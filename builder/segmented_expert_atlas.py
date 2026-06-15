import json
import math
import os
import re
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from cityhash import city_hash64, get_memoria_indices, normalize


EXPERT_ATLAS_MAGIC = 0x21584145  # EAX!
EXPERT_ATLAS_VERSION = 1
HEADER_SIZE = 128
SEGMENT_SIZE = 128
ENTRY_SIZE = 160
BLOOM_BITS = 448
BLOOM_BYTES = 56
BLOOM_HASHES = 4


STOP_TERMS = {
    "this", "that", "from", "into", "onto", "their", "there", "with", "without",
    "about", "above", "below", "general", "common", "rules", "shall", "will",
    "have", "been", "were", "where", "when", "which", "what", "then", "than",
}


@dataclass
class ExpertInput:
    title: str
    source: str
    text: str
    expert_id: int
    domain_mask: int
    region_id: int = 0
    relevance: float = 0.75
    trust: float = 0.8
    recency: float = 0.5
    keywords: list[str] = field(default_factory=list)


@dataclass
class ExpertMeta:
    expert_id: int
    title: str
    source: str
    key: int
    payload_offset: int
    payload_length: int
    domain_mask: int
    region_id: int
    complexity: float
    density: float
    vitality: float
    relevance: float
    trust: float
    recency: float
    bloom: bytes
    keyword_hash: int
    concept_hash: int
    concepts: list[str]
    link_offset: int = 0
    link_count: int = 0


class SegmentedExpertAtlas:
    def __init__(self, segment_size: int = 16, max_experts: int = 400):
        self.segment_size = max(4, int(segment_size))
        self.max_experts = max(1, int(max_experts))
        self.inputs: list[ExpertInput] = []

    def add_expert(self, expert: ExpertInput) -> None:
        if normalize_text(expert.text):
            self.inputs.append(expert)

    def forge(self) -> tuple[bytes, bytes]:
        payloads: list[bytes] = []
        metas: list[ExpertMeta] = []
        payload_offset = 0
        plans = [
            (expert, segment_by_concept_anchors(expert.text, expert.keywords))
            for expert in self.inputs
        ]

        depth = 0
        while len(metas) < self.max_experts:
            selected = 0
            for expert, segments in plans:
                if len(metas) >= self.max_experts:
                    break
                if depth >= len(segments):
                    continue
                segment = segments[depth]
                payload = segment["text"].encode("utf-8") + b"\0"
                meta = self._build_meta(
                    expert=expert,
                    segment=segment,
                    segment_index=depth,
                    segment_count=len(segments),
                    payload_offset=payload_offset,
                    payload_length=len(payload),
                )
                metas.append(meta)
                payloads.append(payload)
                payload_offset += len(payload)
                selected += 1
            if selected == 0:
                break
            depth += 1

        metas.sort(key=lambda meta: (meta.key, meta.expert_id))
        link_table = build_recursive_concept_links(metas)
        segment_table = build_segment_table(metas, self.segment_size)
        expert_table = build_expert_table(metas)
        title_table = json.dumps([
            {
                "expertId": meta.expert_id,
                "title": meta.title,
                "source": meta.source,
                "concepts": meta.concepts,
            }
            for meta in metas
        ], separators=(",", ":")).encode("utf-8")

        segment_offset = HEADER_SIZE
        expert_offset = segment_offset + len(segment_table)
        link_offset = expert_offset + len(expert_table)
        title_offset = link_offset + len(link_table)

        header = bytearray(HEADER_SIZE)
        struct.pack_into("<I H", header, 0, EXPERT_ATLAS_MAGIC, EXPERT_ATLAS_VERSION)
        struct.pack_into("<I I I", header, 8, len(metas), math.ceil(len(metas) / self.segment_size), self.segment_size)
        struct.pack_into("<Q Q Q I", header, 24, segment_offset, expert_offset, title_offset, len(title_table))
        struct.pack_into("<Q I", header, 56, link_offset, len(link_table))

        return (
            bytes(header) + segment_table + expert_table + link_table + title_table,
            b"".join(payloads),
        )

    def _build_meta(
        self,
        expert: ExpertInput,
        segment: dict,
        segment_index: int,
        segment_count: int,
        payload_offset: int,
        payload_length: int,
    ) -> ExpertMeta:
        concepts = segment["concepts"]
        terms = unique_terms([*expert.keywords, *concepts, expert.title, expert.source, *extract_terms(segment["text"])[:32]])
        density = semantic_density(segment["text"], concepts)
        vitality = semantic_vitality(segment["text"], concepts)
        complexity = density
        route_key = build_route_key(expert.domain_mask, expert.region_id, complexity, expert.relevance, expert.trust, expert.recency)
        title = f"{expert.title} / {segment['anchor']}" if segment_count > 1 else expert.title
        return ExpertMeta(
            expert_id=expert.expert_id * 1000 + segment_index,
            title=title,
            source=expert.source,
            key=route_key,
            payload_offset=payload_offset,
            payload_length=payload_length,
            domain_mask=expert.domain_mask,
            region_id=expert.region_id,
            complexity=complexity,
            density=density,
            vitality=vitality,
            relevance=clamp01(expert.relevance),
            trust=clamp01(expert.trust),
            recency=clamp01(expert.recency),
            bloom=build_bloom(terms),
            keyword_hash=hash_text(terms[0] if terms else expert.title),
            concept_hash=hash_text("|".join(concepts) or segment["anchor"] or expert.title),
            concepts=concepts,
        )


class SegmentedExpertAtlasQuery:
    def __init__(self, base_path: str | Path):
        base = str(base_path).replace(".hat", "").replace(".tah", "")
        self.hat_path = Path(f"{base}.hat")
        self.tah_path = Path(f"{base}.tah")
        self.hat = self.hat_path.read_bytes()
        self.tah = self.tah_path.read_bytes()
        if struct.unpack_from("<I", self.hat, 0)[0] != EXPERT_ATLAS_MAGIC:
            raise ValueError(f"Invalid expert atlas: {self.hat_path}")
        self.expert_count = struct.unpack_from("<I", self.hat, 8)[0]
        self.segment_count = struct.unpack_from("<I", self.hat, 12)[0]
        self.segment_size = struct.unpack_from("<I", self.hat, 16)[0]
        self.segment_offset = struct.unpack_from("<Q", self.hat, 24)[0]
        self.expert_offset = struct.unpack_from("<Q", self.hat, 32)[0]
        self.title_offset = struct.unpack_from("<Q", self.hat, 40)[0]
        self.title_length = struct.unpack_from("<I", self.hat, 48)[0]
        self.link_offset = struct.unpack_from("<Q", self.hat, 56)[0]
        self.link_length = struct.unpack_from("<I", self.hat, 64)[0]
        rows = json.loads(self.hat[self.title_offset:self.title_offset + self.title_length].decode("utf-8"))
        self.labels = {row["expertId"]: row for row in rows}

    def search(self, query: str, domain_mask: int | None = None, top_n: int = 5, max_segments: int = 8) -> dict:
        terms = extract_terms(query)[:12]
        query_concepts = extract_concepts(query)
        mask = domain_mask or domain_mask_for_label(query)
        target_complexity = query_complexity_target(query, query_concepts)
        key = build_route_key(mask, 0, target_complexity, 0.6, 0.5, 0.5)
        route_info = self._find_route_segment(key)
        route = route_info["index"]
        fallback_used = False
        candidates: list[tuple[float, int, ExpertMeta]] = []
        visited = 0
        visited_indices: set[int] = set()
        rejected = 0
        rejected_by_reason: dict[str, int] = {}
        lower = route
        upper = route + 1

        def scan_segment(index: int) -> None:
            nonlocal rejected
            segment = self._read_segment(index)
            reason = segment_rejection_reason(segment, mask, terms, target_complexity)
            if reason:
                rejected += 1
                rejected_by_reason[reason] = rejected_by_reason.get(reason, 0) + 1
                return
            for local_index in range(segment["count"]):
                expert_index = segment["start"] + local_index
                meta = self._read_expert(expert_index)
                if meta.domain_mask & mask == 0:
                    continue
                label = self.labels.get(meta.expert_id, {})
                label_terms = extract_terms(" ".join([
                    label.get("title", ""),
                    label.get("source", ""),
                    " ".join(label.get("concepts", [])),
                ]))
                if terms and not any(bloom_contains(meta.bloom, term) or term in label_terms for term in terms):
                    continue
                score = meta.relevance * 40 + meta.trust * 25 + meta.vitality * 12 + meta.density * 10
                score += sum(1 for term in terms if bloom_contains(meta.bloom, term) or term in label_terms) * 8
                candidates.append((score, expert_index, meta))

        while (lower >= 0 or upper < self.segment_count) and visited < max_segments:
            choose_lower = lower >= 0 and (
                upper >= self.segment_count
                or segment_distance(self._read_segment(lower), key) <= segment_distance(self._read_segment(upper), key)
            )
            index = lower if choose_lower else upper
            lower -= 1 if choose_lower else 0
            upper += 0 if choose_lower else 1
            if index in visited_indices:
                continue
            visited_indices.add(index)
            visited += 1
            scan_segment(index)

        if not candidates and visited < self.segment_count:
            fallback_used = True
            for index in range(self.segment_count):
                if index in visited_indices:
                    continue
                visited_indices.add(index)
                visited += 1
                scan_segment(index)

        results = []
        payload_reads = 0
        for score, _expert_index, meta in sorted(candidates, reverse=True, key=lambda row: row[0])[: max(top_n * 4, top_n)]:
            text = self.tah[meta.payload_offset:meta.payload_offset + meta.payload_length].decode("utf-8", errors="ignore").rstrip("\0").strip()
            payload_reads += 1
            label = self.labels.get(meta.expert_id, {})
            haystack = " ".join([
                text,
                label.get("title", ""),
                label.get("source", ""),
                " ".join(label.get("concepts", [])),
            ]).lower()
            if terms and not any(term in haystack for term in terms):
                continue
            results.append({
                "expertId": meta.expert_id,
                "title": label.get("title", f"Expert {meta.expert_id}"),
                "source": label.get("source", meta.source),
                "score": score,
                "density": meta.density,
                "vitality": meta.vitality,
                "concepts": label.get("concepts", []),
                "links": self._read_links(meta),
                "text": text,
            })
            if len(results) >= top_n:
                break

        return {
            "results": results,
            "diagnostics": {
                "totalSegments": self.segment_count,
                "visitedSegments": visited,
                "rejectedSegments": rejected,
                "candidateExperts": len(candidates),
                "payloadReads": payload_reads,
                "routeIndex": route,
                "routeKey": key,
                "targetComplexity": target_complexity,
                "binaryTrace": route_info["trace"],
                "discardedLowerSegments": route_info["discardedLower"],
                "discardedUpperSegments": route_info["discardedUpper"],
                "rejectedByReason": rejected_by_reason,
                "fallbackUsed": fallback_used,
            },
        }

    def _find_route_segment(self, key: int) -> dict:
        low, high, best = 0, self.segment_count - 1, 0
        trace: list[dict] = []
        discarded_lower = 0
        discarded_upper = 0
        while low <= high:
            mid = (low + high) // 2
            segment = self._read_segment(mid)
            best = mid
            if key < segment["keyMin"]:
                discarded = high - mid + 1
                discarded_upper += discarded
                trace.append({
                    "mid": mid,
                    "keyMin": segment["keyMin"],
                    "keyMax": segment["keyMax"],
                    "decision": "target-lower",
                    "discardedSegments": discarded,
                })
                high = mid - 1
            elif key > segment["keyMax"]:
                discarded = mid - low + 1
                discarded_lower += discarded
                trace.append({
                    "mid": mid,
                    "keyMin": segment["keyMin"],
                    "keyMax": segment["keyMax"],
                    "decision": "target-higher",
                    "discardedSegments": discarded,
                })
                low = mid + 1
            else:
                trace.append({
                    "mid": mid,
                    "keyMin": segment["keyMin"],
                    "keyMax": segment["keyMax"],
                    "decision": "match",
                    "discardedSegments": 0,
                })
                return {
                    "index": mid,
                    "trace": trace,
                    "discardedLower": discarded_lower,
                    "discardedUpper": discarded_upper,
                }
        return {
            "index": max(0, min(best, self.segment_count - 1)),
            "trace": trace,
            "discardedLower": discarded_lower,
            "discardedUpper": discarded_upper,
        }

    def _read_segment(self, index: int) -> dict:
        offset = self.segment_offset + index * SEGMENT_SIZE
        key_min, key_max, start, count, domain_mask_union = struct.unpack_from("<Q Q I I Q", self.hat, offset)
        min_complexity, max_complexity, max_relevance, max_trust, max_recency, max_vitality = struct.unpack_from("<f f f f f f", self.hat, offset + 32)
        return {
            "keyMin": key_min,
            "keyMax": key_max,
            "start": start,
            "count": count,
            "domainMaskUnion": domain_mask_union,
            "minComplexity": min_complexity,
            "maxComplexity": max_complexity,
            "maxRelevance": max_relevance,
            "maxTrust": max_trust,
            "maxRecency": max_recency,
            "maxVitality": max_vitality,
            "bloom": self.hat[offset + 56:offset + 56 + BLOOM_BYTES],
        }

    def _read_expert(self, index: int) -> ExpertMeta:
        offset = self.expert_offset + index * ENTRY_SIZE
        expert_id = struct.unpack_from("<I", self.hat, offset)[0]
        domain_mask, key, payload_offset = struct.unpack_from("<Q Q Q", self.hat, offset + 8)
        payload_length = struct.unpack_from("<I", self.hat, offset + 32)[0]
        complexity, relevance, trust, recency, vitality, density = struct.unpack_from("<f f f f f f", self.hat, offset + 36)
        region_id, link_count, link_offset = struct.unpack_from("<H H I", self.hat, offset + 60)
        bloom = self.hat[offset + 72:offset + 72 + BLOOM_BYTES]
        keyword_hash, concept_hash = struct.unpack_from("<Q Q", self.hat, offset + 128)
        return ExpertMeta(expert_id, "", "", key, payload_offset, payload_length, domain_mask, region_id, complexity, density, vitality, relevance, trust, recency, bloom, keyword_hash, concept_hash, [], link_offset, link_count)

    def _read_links(self, meta: ExpertMeta) -> list[dict]:
        start = self.link_offset + meta.link_offset
        end = start + meta.link_count * 4
        if end > self.link_offset + self.link_length:
            return []
        indices = list(struct.unpack_from(f"<{meta.link_count}I", self.hat, start)) if meta.link_count else []
        links = []
        for index in indices:
            if index >= self.expert_count:
                continue
            linked = self._read_expert(index)
            label = self.labels.get(linked.expert_id, {})
            links.append({
                "expertId": linked.expert_id,
                "title": label.get("title", f"Expert {linked.expert_id}"),
                "source": label.get("source", linked.source),
                "concepts": label.get("concepts", []),
            })
        return links


def build_atlas_from_cartridges(root: Path, output_base: Path, max_experts: int = 400, segment_size: int = 16) -> dict:
    atlas = SegmentedExpertAtlas(segment_size=segment_size, max_experts=max_experts)
    cartridges = [
        path for path in sorted((root / "cartridges").glob("**/*.tah"))
        if "expert_atlas" not in path.parts
    ]
    expert_id = 1
    source_inputs: dict[str, int] = {}
    buckets = [
        {"cartridge": cartridge, "shards": list(extract_text_shards(cartridge)), "cursor": 0}
        for cartridge in cartridges
    ]
    buckets = [bucket for bucket in buckets if bucket["shards"]]

    while expert_id <= max_experts and any(bucket["cursor"] < len(bucket["shards"]) for bucket in buckets):
        for bucket in buckets:
            if expert_id > max_experts:
                break
            if bucket["cursor"] >= len(bucket["shards"]):
                continue
            cartridge = bucket["cartridge"]
            shard = bucket["shards"][bucket["cursor"]]
            bucket["cursor"] += 1
            source_index = source_inputs.get(cartridge.name, 0) + 1
            atlas.add_expert(ExpertInput(
                title=f"{cartridge.stem} #{source_index}",
                source=cartridge.name,
                text=shard,
                expert_id=expert_id,
                domain_mask=domain_mask_for_label(f"{cartridge.stem} {shard[:400]}"),
                region_id=infer_region_id(shard),
                relevance=0.82,
                trust=0.88 if cartridge.with_suffix(".hat").exists() else 0.8,
                recency=normalize_recency(cartridge.stat().st_mtime),
                keywords=extract_terms(f"{cartridge.stem} {shard}")[:12],
            ))
            expert_id += 1
            source_inputs[cartridge.name] = source_index

    hat, tah = atlas.forge()
    output_base.parent.mkdir(parents=True, exist_ok=True)
    output_base.with_suffix(".hat").write_bytes(hat)
    output_base.with_suffix(".tah").write_bytes(tah)

    title_offset = struct.unpack_from("<Q", hat, 40)[0]
    title_length = struct.unpack_from("<I", hat, 48)[0]
    labels = json.loads(hat[title_offset:title_offset + title_length].decode("utf-8"))
    source_counts: dict[str, int] = {}
    for row in labels:
        source_counts[row["source"]] = source_counts.get(row["source"], 0) + 1

    manifest = {
        "name": output_base.name,
        "format": "segmented-expert-atlas-v1",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "expertCount": struct.unpack_from("<I", hat, 8)[0],
        "segmentCount": struct.unpack_from("<I", hat, 12)[0],
        "maxExperts": max_experts,
        "sources": [{"name": name, "experts": count} for name, count in sorted(source_counts.items())],
    }
    output_base.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def extract_text_shards(tah_path: Path) -> Iterable[str]:
    hat_path = tah_path.with_suffix(".hat")
    if hat_path.exists():
        try:
            yield from extract_v36_shards(hat_path, tah_path)
            return
        except Exception:
            pass

    raw = tah_path.read_bytes()
    chunks = re.split(rb"\0+", raw)
    for chunk in chunks:
        text = normalize_text(chunk.decode("utf-8", errors="ignore"))
        if len(text) >= 80:
            yield text


def extract_v36_shards(hat_path: Path, tah_path: Path) -> Iterable[str]:
    hat = hat_path.read_bytes()
    tah = tah_path.read_bytes()
    magic = struct.unpack_from("<I", hat, 0)[0]
    if magic not in (0x54414821, 0x48415421):
        return
    k = struct.unpack_from("<B", hat, 6)[0]
    bloom_bits = struct.unpack_from("<Q", hat, 8)[0]
    shard_count = struct.unpack_from("<I", hat, 16)[0]
    index_offset = 64 + (bloom_bits // 8)
    if k <= 0 or index_offset >= len(hat):
        return
    for index in range(shard_count):
        entry_offset = index_offset + index * 80
        if entry_offset + 80 > len(hat):
            break
        tag = struct.unpack_from("<B", hat, entry_offset)[0]
        if tag != 0:
            continue
        payload_offset, payload_length = struct.unpack_from("<Q I", hat, entry_offset + 8)
        text = tah[payload_offset:payload_offset + payload_length].decode("utf-8", errors="ignore").split("\0")[0]
        text = normalize_text(text)
        if len(text) >= 80:
            yield text


def segment_by_concept_anchors(text: str, seeds: list[str] | None = None, max_words: int = 180) -> list[dict]:
    text = normalize_text(text)
    seeds = seeds or []
    if not text:
        return []
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|(?=\b[A-Z][A-Z0-9_ ]{2,}:)", text) if part.strip()] or [text]
    segments: list[dict] = []
    current: list[str] = []
    concepts: set[str] = set()
    anchor = seeds[0].lower() if seeds else "general"

    for sentence in sentences:
        sentence_concepts = extract_concepts(sentence, seeds)
        next_anchor = sentence_concepts[0] if sentence_concepts else anchor
        current_words = len(" ".join(current).split())
        overlap = len(concepts.intersection(sentence_concepts))
        should_split = current and (current_words + len(sentence.split()) > max_words or (sentence_concepts and overlap == 0 and current_words > 45))
        if should_split:
            segments.append(finalize_segment(current, concepts, anchor))
            current, concepts, anchor = [], set(), next_anchor
        current.append(sentence)
        concepts.update(sentence_concepts)
        anchor = anchor or next_anchor

    if current:
        segments.append(finalize_segment(current, concepts, anchor))
    return segments


def finalize_segment(sentences: list[str], concepts: set[str], anchor: str) -> dict:
    text = normalize_text(" ".join(sentences))
    concept_list = list(concepts)[:12] or extract_concepts(text, [anchor])[:12]
    return {"anchor": concept_list[0] if concept_list else anchor, "concepts": concept_list, "text": text}


def extract_concepts(text: str, seeds: list[str] | None = None) -> list[str]:
    candidates = [term for term in extract_terms(text) if is_concept(term)]
    candidates.sort(key=lambda term: concept_weight(term, text), reverse=True)
    return unique_terms([*(seeds or []), *candidates])[:12]


def extract_terms(text: str) -> list[str]:
    words = [word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2 and word not in STOP_TERMS]
    bigrams = [f"{words[index]} {words[index + 1]}" for index in range(len(words) - 1)]
    return unique_terms([*bigrams, *words])


def is_concept(term: str) -> bool:
    return len(term) >= 4 and not term.isdigit() and ((" " in term) or term not in STOP_TERMS)


def concept_weight(term: str, text: str) -> float:
    normalized = text.lower()
    return normalized.count(term) * (2.0 if " " in term else 1.0) + min(2.0, len(term) / 12)


def semantic_density(text: str, concepts: list[str]) -> float:
    words = max(1, len(text.split()))
    term_count = len(extract_terms(text))
    hits = sum(1 for concept in concepts if concept in text.lower())
    return clamp01((term_count / words) * 0.65 + (hits / max(1, len(concepts))) * 0.35)


def semantic_vitality(text: str, concepts: list[str]) -> float:
    density = semantic_density(text, concepts)
    anchor_strength = min(1.0, len(concepts) / 8)
    connective_count = len(re.findall(r"\b(because|therefore|enables|requires|links|drives|prevents|routes|maps|yields)\b", text, re.I))
    return clamp01(density * 0.45 + anchor_strength * 0.25 + min(1.0, connective_count / 4) * 0.15 + min(1.0, len(text.split()) / 80) * 0.15)


def query_complexity_target(query: str, concepts: list[str]) -> float:
    words = query.split()
    if not words:
        return 0.5
    density = semantic_density(query, concepts)
    # Query strings are much shorter than shards, so dampen density toward the middle
    # of the route space instead of letting one-word queries pin to the far edge.
    return clamp01(0.35 + density * 0.4 + min(1.0, len(words) / 18) * 0.25)


def segment_rejection_reason(segment: dict, mask: int, terms: list[str], target_complexity: float) -> str | None:
    if segment["domainMaskUnion"] & mask == 0:
        return "domain"
    if terms and not any(bloom_contains(segment["bloom"], term) for term in terms):
        return "segment-bloom"
    complexity_window = 0.55
    if segment["maxComplexity"] < target_complexity - complexity_window:
        return "complexity-low"
    if segment["minComplexity"] > target_complexity + complexity_window:
        return "complexity-high"
    if segment["maxVitality"] <= 0:
        return "vitality"
    return None


def build_segment_table(metas: list[ExpertMeta], segment_size: int) -> bytes:
    table = bytearray()
    for start in range(0, len(metas), segment_size):
        chunk = metas[start:start + segment_size]
        bloom = bytearray(BLOOM_BYTES)
        domain_union = 0
        for meta in chunk:
            domain_union |= meta.domain_mask
            for index, value in enumerate(meta.bloom):
                bloom[index] |= value
        row = bytearray(SEGMENT_SIZE)
        struct.pack_into(
            "<Q Q I I Q f f f f f f",
            row,
            0,
            chunk[0].key,
            chunk[-1].key,
            start,
            len(chunk),
            domain_union,
            min(meta.complexity for meta in chunk),
            max(meta.complexity for meta in chunk),
            max(meta.relevance for meta in chunk),
            max(meta.trust for meta in chunk),
            max(meta.recency for meta in chunk),
            max(meta.vitality for meta in chunk),
        )
        row[56:56 + BLOOM_BYTES] = bloom
        table.extend(row)
    return bytes(table)


def build_expert_table(metas: list[ExpertMeta]) -> bytes:
    table = bytearray()
    for meta in metas:
        row = bytearray(ENTRY_SIZE)
        struct.pack_into("<I", row, 0, meta.expert_id)
        struct.pack_into("<Q Q Q I", row, 8, meta.domain_mask, meta.key, meta.payload_offset, meta.payload_length)
        struct.pack_into("<f f f f f f", row, 36, meta.complexity, meta.relevance, meta.trust, meta.recency, meta.vitality, meta.density)
        struct.pack_into("<H H I", row, 60, meta.region_id, meta.link_count, meta.link_offset)
        row[72:72 + BLOOM_BYTES] = meta.bloom
        struct.pack_into("<Q Q", row, 128, meta.keyword_hash, meta.concept_hash)
        table.extend(row)
    return bytes(table)


def build_recursive_concept_links(metas: list[ExpertMeta]) -> bytes:
    concept_index: dict[str, list[int]] = {}
    for index, meta in enumerate(metas):
        for concept in meta.concepts:
            concept_index.setdefault(concept, []).append(index)

    out = bytearray()
    for index, meta in enumerate(metas):
        links: dict[int, float] = {}

        def remember(link_index: int, rank: float) -> None:
            if link_index == index or link_index < 0 or link_index >= len(metas):
                return
            links[link_index] = min(rank, links.get(link_index, float("inf")))

        jump = 1
        while jump < len(metas):
            if index - jump >= 0:
                remember(index - jump, 100 + math.log2(jump))
            if index + jump < len(metas):
                remember(index + jump, 100 + math.log2(jump))
            jump *= 2
        for concept in meta.concepts:
            peers = sorted((peer for peer in concept_index.get(concept, []) if peer != index), key=lambda peer: abs(peer - index))
            for peer in peers[:3]:
                remember(peer, abs(peer - index) * 0.01)
        selected = [
            link for link, _rank in sorted(
                links.items(),
                key=lambda item: (item[1], abs(item[0] - index), item[0]),
            )[:24]
        ]
        meta.link_offset = len(out)
        meta.link_count = len(selected)
        for link in selected:
            out.extend(struct.pack("<I", link))
    return bytes(out)


def build_bloom(terms: Iterable[str]) -> bytes:
    bloom = bytearray(BLOOM_BYTES)
    for term in terms:
        for idx in get_memoria_indices(term, BLOOM_BITS, BLOOM_HASHES):
            bloom[idx // 8] |= 1 << (idx % 8)
    return bytes(bloom)


def bloom_contains(bloom: bytes, term: str) -> bool:
    for idx in get_memoria_indices(term, BLOOM_BITS, BLOOM_HASHES):
        if idx // 8 >= len(bloom) or not (bloom[idx // 8] & (1 << (idx % 8))):
            return False
    return True


def build_route_key(domain_mask: int, region_id: int, complexity: float, relevance: float, trust: float, recency: float) -> int:
    buckets = [domain_bucket(domain_mask), region_id & 1023, bucket10(complexity), bucket10(relevance), bucket10(trust), bucket10(recency)]
    key = 0
    for bit in range(9, -1, -1):
        for bucket in buckets:
            key = (key << 1) | ((bucket >> bit) & 1)
    return key


def domain_mask_for_label(label: str) -> int:
    value = label.lower()
    patterns = [
        (r"architecture|cache|cpu|memory|simd|mapreduce|operating|compiler|unix", 0),
        (r"pulse|idx|mls|listing|property|real estate|dallas|tarrant|texas", 1),
        (r"security|zero trust|auth|jwt|crypto|guardian|abidan", 2),
        (r"medical|health|clinical|diagnosis", 3),
        (r"category|scheme|sicp|lisp|lambda", 4),
        (r"visual|three|mapbox|raster|image|video", 5),
        (r"runtime|combat|matrix|spell|unreal|zustand", 7),
    ]
    mask = 0
    for pattern, bit in patterns:
        if re.search(pattern, value):
            mask |= 1 << bit
    return mask or (1 << (hash_text(value or "general") % 32))


def domain_bucket(mask: int) -> int:
    for index in range(64):
        if mask & (1 << index):
            return index & 1023
    return 0


def infer_region_id(text: str) -> int:
    value = text.lower()
    if re.search(r"dallas|tarrant|texas|ntreis", value):
        return 1
    if re.search(r"california|san francisco|los angeles", value):
        return 2
    if re.search(r"japan|tokyo", value):
        return 103
    return 0


def normalize_recency(mtime: float) -> float:
    age_days = max(0.0, (time.time() - mtime) / 86400)
    return clamp01(1 / (1 + age_days / 90))


def segment_distance(segment: dict, key: int) -> int:
    if key < segment["keyMin"]:
        return segment["keyMin"] - key
    if key > segment["keyMax"]:
        return key - segment["keyMax"]
    return 0


def hash_text(value: str) -> int:
    return city_hash64(normalize(value))


def bucket10(value: float) -> int:
    return max(0, min(1023, round(clamp01(value) * 1023)))


def clamp01(value: float) -> float:
    if not math.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, float(value)))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\0", " ")).strip()


def unique_terms(terms: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for term in terms:
        key = normalize_text(term.lower())
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out
