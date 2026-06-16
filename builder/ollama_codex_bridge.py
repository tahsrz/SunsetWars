import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.append(str(Path(__file__).resolve().parent))

from memoria_query import MemoriaQuery
from segmented_expert_atlas import (
    SegmentedExpertAtlasQuery,
    domain_mask_for_label,
    extract_terms,
)


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGE_DIR = ROOT / "cartridges"
ATLAS_BASE = CARTRIDGE_DIR / "expert_atlas" / "segmented_expert_atlas"
HANDOFF_DIR = ROOT / "workbench" / "codex_handoffs"
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL_PREFERENCE = ("phi4-mini", "smollm2", "gemma4")


@dataclass
class QueryPlan:
    query: str
    tokens: list[str]
    concepts: list[str]
    intent: str
    model: str | None = None
    fallback_reason: str | None = None


@dataclass
class RetrievedShard:
    source: str
    title: str
    text: str
    score: float
    offset: int | None = None
    length: int | None = None
    concepts: list[str] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tokenize a query with Ollama, retrieve relevant TAH shards, and hand off to Codex CLI."
    )
    parser.add_argument("query", help="Question or task to route through the TAH library.")
    parser.add_argument("--model", help="Ollama model to use for query tokenization.")
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST))
    parser.add_argument("--atlas-top-n", type=int, default=8)
    parser.add_argument("--source-top-n", type=int, default=4)
    parser.add_argument("--max-sources", type=int, default=8)
    parser.add_argument("--max-context-chars", type=int, default=18000)
    parser.add_argument("--no-codex", action="store_true", help="Write the handoff prompt but do not invoke Codex.")
    parser.add_argument("--codex-path", default=find_codex_cli_path())
    parser.add_argument("--codex-approval", default="on-request")
    parser.add_argument("--codex-sandbox", default="workspace-write")
    parser.add_argument("--print-prompt", action="store_true")
    args = parser.parse_args()

    plan = build_query_plan(args.query, args.ollama_host, args.model)
    atlas_hits, atlas_diagnostics = query_expert_atlas(plan, args.atlas_top_n)
    source_names = choose_relevant_sources(atlas_hits, args.max_sources)
    shard_hits = query_relevant_cartridges(plan, source_names, args.source_top_n)
    prompt = build_codex_prompt(
        plan=plan,
        atlas_hits=atlas_hits,
        atlas_diagnostics=atlas_diagnostics,
        shard_hits=shard_hits,
        max_context_chars=args.max_context_chars,
    )
    prompt_path = write_handoff(prompt, plan)

    report = {
        "query": plan.query,
        "tokens": plan.tokens,
        "concepts": plan.concepts,
        "ollamaModel": plan.model,
        "fallbackReason": plan.fallback_reason,
        "sources": source_names,
        "atlasResults": len(atlas_hits),
        "shardResults": len(shard_hits),
        "handoffPath": str(prompt_path),
    }
    print(json.dumps(report, indent=2))

    if args.print_prompt:
        print("\n--- CODEX HANDOFF PROMPT ---")
        print(prompt)

    if args.no_codex:
        return 0

    return run_codex(prompt, args.codex_path, args.codex_approval, args.codex_sandbox)


def build_query_plan(query: str, ollama_host: str, model: str | None) -> QueryPlan:
    chosen_model = model or choose_ollama_model()
    if chosen_model:
        try:
            response = call_ollama(
                ollama_host,
                chosen_model,
                [
                    "Extract retrieval metadata for a local binary TAH knowledge search.",
                    "Return only JSON with keys: tokens, concepts, intent.",
                    "tokens: 6-16 lowercase search tokens or bigrams.",
                    "concepts: 3-10 durable concept labels.",
                    "intent: one short phrase.",
                    f"Query: {query}",
                ],
            )
            parsed = parse_json_object(response)
            tokens = clean_terms(parsed.get("tokens", []))
            concepts = clean_terms(parsed.get("concepts", []))
            intent = str(parsed.get("intent", "")).strip()[:160] or query
            if tokens or concepts:
                return QueryPlan(query, tokens or fallback_terms(query), concepts or tokens[:8], intent, chosen_model)
        except Exception as exc:
            return fallback_query_plan(query, f"ollama failed: {exc}", chosen_model)
    return fallback_query_plan(query, "no ollama model found", chosen_model)


def fallback_query_plan(query: str, reason: str, model: str | None = None) -> QueryPlan:
    terms = fallback_terms(query)
    return QueryPlan(
        query=query,
        tokens=terms[:16],
        concepts=terms[:10],
        intent=query[:160],
        model=model,
        fallback_reason=reason,
    )


def fallback_terms(query: str) -> list[str]:
    return extract_terms(query)[:16] or [part.lower() for part in query.split() if len(part) > 2][:16]


def call_ollama(host: str, model: str, prompt_parts: list[str]) -> str:
    payload = json.dumps({
        "model": model,
        "prompt": "\n".join(prompt_parts),
        "stream": False,
        "options": {
            "temperature": 0.05,
            "num_predict": 500,
        },
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("response", "")


def parse_json_object(value: str) -> dict:
    stripped = value.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", stripped, flags=re.I)
    candidate = fenced.group(1).strip() if fenced else stripped
    first = candidate.find("{")
    last = candidate.rfind("}")
    if first == -1 or last <= first:
        raise ValueError("Ollama response did not contain a JSON object")
    return json.loads(candidate[first:last + 1])


def clean_terms(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        term = re.sub(r"\s+", " ", str(value).lower()).strip()
        term = re.sub(r"[^a-z0-9 #+_.-]+", "", term).strip()
        if len(term) < 3 or term in seen:
            continue
        seen.add(term)
        cleaned.append(term)
    return cleaned


def choose_ollama_model() -> str | None:
    configured = os.environ.get("TAH_OLLAMA_MODEL") or os.environ.get("NEWS_OLLAMA_MODEL")
    if configured:
        return configured
    manifest_root = Path(os.environ.get(
        "OLLAMA_LIBRARY_MANIFESTS",
        str(Path.home() / ".ollama" / "models" / "manifests" / "registry.ollama.ai" / "library"),
    ))
    if not manifest_root.exists():
        return None
    models: list[str] = []
    for family in manifest_root.iterdir():
        if not family.is_dir():
            continue
        for tag in family.iterdir():
            if tag.is_file():
                models.append(f"{family.name}:{tag.name}")
    for preferred in DEFAULT_MODEL_PREFERENCE:
        match = next((model for model in models if model.startswith(f"{preferred}:")), None)
        if match:
            return match
    return models[0] if models else None


def query_expert_atlas(plan: QueryPlan, top_n: int) -> tuple[list[RetrievedShard], dict]:
    if not ATLAS_BASE.with_suffix(".hat").exists():
        return [], {"error": f"missing atlas: {ATLAS_BASE.with_suffix('.hat')}"}
    atlas = SegmentedExpertAtlasQuery(ATLAS_BASE)
    search_text = " ".join([plan.query, *plan.tokens, *plan.concepts])
    result = atlas.search(
        search_text,
        domain_mask=domain_mask_for_label(search_text),
        top_n=top_n,
        max_segments=10,
    )
    hits = [
        RetrievedShard(
            source=row["source"],
            title=row["title"],
            text=row["text"],
            score=float(row["score"]),
            concepts=row.get("concepts", []),
            links=row.get("links", []),
        )
        for row in result["results"]
    ]
    return hits, result["diagnostics"]


def choose_relevant_sources(atlas_hits: list[RetrievedShard], max_sources: int) -> list[str]:
    sources: list[str] = []
    seen: set[str] = set()

    def add(source: str) -> None:
        if source and source not in seen and (CARTRIDGE_DIR / source).exists():
            seen.add(source)
            sources.append(source)

    for hit in atlas_hits:
        add(hit.source)
    for hit in atlas_hits:
        for link in hit.links[:4]:
            add(str(link.get("source", "")))
        if len(sources) >= max_sources:
            break
    return sources[:max_sources]


def query_relevant_cartridges(plan: QueryPlan, source_names: list[str], top_n: int) -> list[RetrievedShard]:
    hits: list[RetrievedShard] = []
    query_text = " ".join([plan.query, *plan.tokens, *plan.concepts])
    for source_name in source_names:
        tah_path = CARTRIDGE_DIR / source_name
        if tah_path.with_suffix(".hat").exists():
            hits.extend(query_memoria_cartridge(tah_path, query_text, top_n))
        else:
            hits.extend(query_raw_tah(tah_path, plan, top_n))
    return sorted(hits, key=lambda hit: hit.score, reverse=True)


def query_memoria_cartridge(tah_path: Path, query_text: str, top_n: int) -> list[RetrievedShard]:
    try:
        q = MemoriaQuery(tah_path)
        matches = q.get_matches(query_text, top_n=top_n)
        q.close()
    except Exception:
        return []
    return [
        RetrievedShard(
            source=tah_path.name,
            title=f"{tah_path.stem} #{match['index']}",
            text=match["data"],
            score=float(match["score"]),
            offset=match.get("offset"),
            length=match.get("length"),
            concepts=[],
            links=[{"index": link} for link in match.get("links", [])],
        )
        for match in matches
    ]


def query_raw_tah(tah_path: Path, plan: QueryPlan, top_n: int) -> list[RetrievedShard]:
    terms = [*plan.tokens, *plan.concepts]
    scored: list[RetrievedShard] = []
    try:
        raw = tah_path.read_bytes()
    except Exception:
        return []

    cursor = 0
    for index, chunk in enumerate(re.split(rb"\0+", raw)):
        chunk_start = raw.find(chunk, cursor)
        if chunk_start < 0:
            chunk_start = cursor
        cursor = chunk_start + len(chunk) + 1
        text = re.sub(r"\s+", " ", chunk.decode("utf-8", errors="ignore")).strip()
        if len(text) < 80:
            continue
        haystack = text.lower()
        score = sum(8.0 for term in terms if term in haystack)
        score += sum(2.0 for part in plan.query.lower().split() if len(part) > 2 and part in haystack)
        if score <= 0:
            continue
        scored.append(RetrievedShard(
            source=tah_path.name,
            title=f"{tah_path.stem} raw #{index}",
            text=text,
            score=score,
            offset=chunk_start,
            length=len(chunk),
            concepts=extract_terms(text)[:8],
        ))
    return sorted(scored, key=lambda hit: hit.score, reverse=True)[:top_n]


def build_codex_prompt(
    plan: QueryPlan,
    atlas_hits: list[RetrievedShard],
    atlas_diagnostics: dict,
    shard_hits: list[RetrievedShard],
    max_context_chars: int,
) -> str:
    context_blocks: list[str] = []
    included_hits: list[RetrievedShard] = []
    char_budget = max_context_chars
    for hit in [*atlas_hits, *shard_hits]:
        text = hit.text.strip()
        if not text:
            continue
        excerpt = text[: min(len(text), 2200)]
        block = format_shard(hit, excerpt, include_diagnostics=False)
        if len(block) > char_budget:
            continue
        context_blocks.append(block)
        included_hits.append(hit)
        char_budget -= len(block)
        if char_budget <= 1200:
            break

    metadata = {
        "query": plan.query,
        "tokens": plan.tokens,
        "concepts": plan.concepts,
        "intent": plan.intent,
        "ollamaModel": plan.model,
        "fallbackReason": plan.fallback_reason,
        "atlasDiagnostics": atlas_diagnostics,
        "includedSources": [shard_diagnostics(hit) for hit in included_hits],
    }
    return "\n".join([
        "You are Codex working inside the SunsetWars repository.",
        "This prompt was generated by builder/ollama_codex_bridge.py; the TAH/Memoria retrieval pass has already run.",
        "Do not invoke the bridge again unless the user explicitly asks for a fresh retrieval.",
        "Use the retrieved TAH/Memoria context below as priority ground truth before reading large source files.",
        "Cite cartridge names when the retrieved context materially informs your answer or implementation.",
        "Cache layout: stable instructions and retrieved content come before volatile query tags and route diagnostics.",
        "",
        "RETRIEVED TAH CONTEXT:",
        "\n\n".join(context_blocks) if context_blocks else "No matching TAH context was retrieved.",
        "",
        "USER QUERY:",
        plan.query,
        "",
        "TASK:",
        "Answer or implement the user query using this context, then verify the result in the repo.",
        "",
        "RETRIEVAL METADATA AND SOURCE TAGS:",
        json.dumps(metadata, indent=2),
    ])


def format_shard(hit: RetrievedShard, excerpt: str, include_diagnostics: bool = True) -> str:
    suffix = ""
    if include_diagnostics:
        suffix = f" score={hit.score:.2f}"
        if hit.offset is not None:
            suffix += f" offset={hit.offset} length={hit.length}"
    concepts = ", ".join(hit.concepts[:8])
    return "\n".join([
        f"[{hit.source}] {hit.title}{suffix}",
        f"concepts: {concepts}" if concepts else "concepts: n/a",
        excerpt,
    ])


def shard_diagnostics(hit: RetrievedShard) -> dict:
    return {
        "source": hit.source,
        "title": hit.title,
        "score": hit.score,
        "offset": hit.offset,
        "length": hit.length,
        "concepts": hit.concepts[:8],
    }


def write_handoff(prompt: str, plan: QueryPlan) -> Path:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", plan.query.lower()).strip("-")[:48] or "query"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = HANDOFF_DIR / f"{stamp}-{slug}.md"
    path.write_text(prompt, encoding="utf-8")
    (HANDOFF_DIR / "latest.md").write_text(prompt, encoding="utf-8")
    return path


def find_codex_cli_path() -> str:
    config_path = Path.home() / ".codex" / "config.toml"
    if config_path.exists():
        match = re.search(r"CODEX_CLI_PATH\s*=\s*'([^']+)'", config_path.read_text(encoding="utf-8", errors="ignore"))
        if match and Path(match.group(1)).exists():
            return match.group(1)
    return "codex"


def run_codex(prompt: str, codex_path: str, approval: str, sandbox: str) -> int:
    command = [
        codex_path,
        "exec",
        "-C",
        str(ROOT),
        "-c",
        f"approval_policy={json.dumps(approval)}",
        "--sandbox",
        sandbox,
        "-",
    ]
    try:
        env = os.environ.copy()
        env["SUNSETWARS_TAH_BRIDGE_ACTIVE"] = "1"
        completed = subprocess.run(command, cwd=ROOT, input=prompt, text=True, env=env)
        return completed.returncode
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Codex launch failed: {exc}", file=sys.stderr)
        print(f"Handoff prompt is still available at {HANDOFF_DIR / 'latest.md'}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
