import argparse
import hashlib
import json
import random
import re
import struct
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from segmented_expert_atlas import extract_terms, extract_text_shards, normalize_text, unique_terms


GENERATOR_VERSION = "deterministic-v0"
ANSWER_COUNT = 4
MAX_FIELD_BYTES = 0xFFFF
QUIZ_STOP_TERMS = {
    "about", "above", "across", "after", "again", "against", "also", "although", "among",
    "actually", "approach", "because", "before", "being", "below", "between",
    "cannot", "chapter", "clear", "could", "detecting", "during",
    "each", "either", "enough", "every", "example", "fact", "follows", "given", "however", "into",
    "itself", "later", "lemma", "less", "line", "many", "more", "most", "must", "only", "other",
    "part", "proof", "prove", "rather", "section", "second", "should", "since",
    "some", "statement", "still", "such", "than", "that", "their", "then", "there",
    "therefore", "these", "third", "this", "those", "through", "using", "where",
    "were", "whether", "which", "while", "with", "within", "without", "would",
}
GENERIC_SENTENCE_STARTS = (
    "as mentioned",
    "for example",
    "the literature references",
    "more formally",
    "proof ",
    "the following",
    "we therefore address",
)
MOJIBAKE_MARKERS = ("â", "Â", "Å", "Ë", "ï", "î", "�", "\x7f", "/TAB")


@dataclass(frozen=True)
class QuizClaim:
    source: str
    shard_index: int
    sentence_index: int
    text: str
    anchor: str
    concepts: list[str]


@dataclass(frozen=True)
class QuizItem:
    id: str
    question: str
    answers: list[str]
    correctIndex: int
    source: str
    shardIndex: int
    sentenceIndex: int
    anchor: str
    concepts: list[str]
    difficulty: str
    generator: str
    generatedAt: str
    supportText: str


def build_quiz_deck(source_path: Path, limit: int = 25) -> list[QuizItem]:
    claims = extract_claims(source_path)
    if len(claims) < ANSWER_COUNT:
        raise ValueError(f"Need at least {ANSWER_COUNT} usable claims; found {len(claims)} in {source_path}.")

    items: list[QuizItem] = []
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for claim in claims:
        distractors = choose_distractors(claim, claims)
        if len(distractors) < ANSWER_COUNT - 1:
            continue
        item = build_item(claim, distractors[: ANSWER_COUNT - 1], generated_at)
        validate_item(item)
        items.append(item)
        if len(items) >= limit:
            break

    if not items:
        raise ValueError(f"No valid quiz items could be generated from {source_path}.")
    return items


def extract_claims(source_path: Path) -> list[QuizClaim]:
    claims: list[QuizClaim] = []
    seen_answers: set[str] = set()

    for shard_index, shard in enumerate(extract_text_shards(source_path)):
        for sentence_index, sentence in enumerate(split_sentences(shard)):
            cleaned = clean_answer(sentence)
            if not is_usable_sentence(cleaned):
                continue
            concepts = extract_claim_concepts(cleaned)
            if not concepts:
                continue
            key = normalize_answer(cleaned)
            if key in seen_answers:
                continue
            seen_answers.add(key)
            claims.append(QuizClaim(
                source=source_path.name,
                shard_index=shard_index,
                sentence_index=sentence_index,
                text=cleaned,
                anchor=concepts[0],
                concepts=concepts,
            ))

    claims.sort(key=lambda claim: (
        -claim_quality(claim),
        claim.source,
        claim.shard_index,
        claim.sentence_index,
        claim.anchor,
    ))
    return claims


def split_sentences(text: str) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    if len(parts) == 1:
        parts = re.split(r"\s{2,}|(?=\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4}:)", text)
    return [part.strip(" \t\r\n-") for part in parts if part.strip()]


def clean_answer(text: str) -> str:
    text = normalize_text(text)
    text = repair_mojibake(text)
    replacements = {
        "â€”": "-",
        "â€“": "-",
        "â€": "-",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "ï¬": "fi",
        "ï¬‚": "fl",
        "ï¬€": "ff",
        "NUL": "",
        "/TAB": " ",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", " ", text)
    text = re.sub(r"([A-Za-z])- ([A-Za-z])", r"\1\2", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def repair_mojibake(text: str) -> str:
    try:
        repaired = text.encode("cp1252").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text
    if mojibake_count(repaired) < mojibake_count(text):
        return repaired
    return text


def mojibake_count(text: str) -> int:
    return sum(text.count(marker) for marker in MOJIBAKE_MARKERS)


def is_usable_sentence(text: str) -> bool:
    if not (60 <= len(text) <= 260):
        return False
    if any(marker in text for marker in MOJIBAKE_MARKERS):
        return False
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]*", text)
    if len(words) < 9:
        return False
    lower = text.lower()
    if lower.startswith(GENERIC_SENTENCE_STARTS):
        return False
    if re.match(r"^\d+(?:\.\d+)+\s+", text):
        return False
    if re.search(r"\b[A-Z][A-Za-z ]+\|\s*\d+\b", text):
        return False
    if re.search(r"\b(prove|show|describe)\s+that\b", lower):
        return False
    if any(marker in lower for marker in (" contents ", " bibliography ", " index ", " figure ", " table ")):
        return False
    if sum(ch.isalpha() for ch in text) / max(1, len(text)) < 0.55:
        return False
    if len(re.findall(r"\d", text)) > len(text) * 0.18:
        return False
    return True


def extract_claim_concepts(text: str) -> list[str]:
    words = content_words(text)
    bigrams = [f"{words[index]} {words[index + 1]}" for index in range(len(words) - 1)]
    terms = [
        term for term in unique_terms([*bigrams, *words, *extract_terms(text)])
        if len(term) >= 4
        and not term.isdigit()
        and not re.search(r"\b(chapter|section|page|figure|table)\b", term)
        and not all(part in QUIZ_STOP_TERMS for part in term.split())
    ]
    bigrams = [term for term in terms if " " in term and len(term) <= 42]
    unigrams = [term for term in terms if " " not in term and len(term) <= 24 and term not in QUIZ_STOP_TERMS]
    return unique_terms([*bigrams, *unigrams])[:8]


def content_words(text: str) -> list[str]:
    return [
        word for word in re.findall(r"[a-z][a-z0-9-]+", text.lower())
        if len(word) >= 4 and word not in QUIZ_STOP_TERMS and not word.isdigit()
    ]


def claim_quality(claim: QuizClaim) -> float:
    text = claim.text
    concept_hits = sum(1 for concept in claim.concepts if concept in text.lower())
    connector_hits = len(re.findall(r"\b(because|therefore|however|although|requires|enables|prevents|depends|allows|means)\b", text, re.I))
    length_score = 1.0 - abs(len(text) - 150) / 150
    return concept_hits * 2.0 + connector_hits * 1.5 + max(0.0, length_score)


def choose_distractors(claim: QuizClaim, claims: list[QuizClaim]) -> list[QuizClaim]:
    candidates = [
        candidate for candidate in claims
        if candidate != claim
        and candidate.anchor != claim.anchor
        and normalize_answer(candidate.text) != normalize_answer(claim.text)
        and concept_overlap(candidate, claim) <= 0.25
    ]
    candidates.sort(key=lambda candidate: (
        abs(len(candidate.text) - len(claim.text)),
        stable_int(f"{claim.anchor}|{candidate.anchor}|{candidate.text}"),
    ))
    return candidates


def concept_overlap(left: QuizClaim, right: QuizClaim) -> float:
    left_terms = set(left.concepts)
    right_terms = set(right.concepts)
    if not left_terms or not right_terms:
        return 0.0
    return len(left_terms & right_terms) / len(left_terms | right_terms)


def build_item(claim: QuizClaim, distractors: list[QuizClaim], generated_at: str) -> QuizItem:
    answers = [claim.text, *(distractor.text for distractor in distractors)]
    seed = stable_int(f"{claim.source}:{claim.shard_index}:{claim.sentence_index}:{claim.anchor}")
    rng = random.Random(seed)
    order = list(range(ANSWER_COUNT))
    rng.shuffle(order)
    shuffled = [answers[index] for index in order]
    correct_index = order.index(0)
    item_id = hashlib.sha1(f"{claim.source}:{claim.shard_index}:{claim.sentence_index}:{claim.text}".encode("utf-8")).hexdigest()[:16]

    return QuizItem(
        id=item_id,
        question=f'Which statement is most directly associated with "{claim.anchor}" in {claim.source}?',
        answers=shuffled,
        correctIndex=correct_index,
        source=claim.source,
        shardIndex=claim.shard_index,
        sentenceIndex=claim.sentence_index,
        anchor=claim.anchor,
        concepts=claim.concepts,
        difficulty=infer_difficulty(claim),
        generator=GENERATOR_VERSION,
        generatedAt=generated_at,
        supportText=claim.text,
    )


def infer_difficulty(claim: QuizClaim) -> str:
    lower = claim.text.lower()
    if any(term in lower for term in ("however", "although", "whereas", "rather than", "compared")):
        return "contrast"
    if any(term in lower for term in ("because", "therefore", "requires", "depends", "allows", "enables")):
        return "understanding"
    return "recall"


def validate_item(item: QuizItem) -> None:
    if len(item.answers) != ANSWER_COUNT:
        raise ValueError(f"{item.id}: expected exactly {ANSWER_COUNT} answers.")
    if item.correctIndex not in range(ANSWER_COUNT):
        raise ValueError(f"{item.id}: correctIndex must be 0..3.")
    if item.answers[item.correctIndex] != item.supportText:
        raise ValueError(f"{item.id}: correct answer must match supportText.")
    if len({normalize_answer(answer) for answer in item.answers}) != ANSWER_COUNT:
        raise ValueError(f"{item.id}: answers must be semantically unique.")
    for label, value in [("question", item.question), *[(f"answer {index}", answer) for index, answer in enumerate(item.answers)]]:
        encoded = value.encode("utf-8")
        if not encoded:
            raise ValueError(f"{item.id}: {label} is empty.")
        if len(encoded) > MAX_FIELD_BYTES:
            raise ValueError(f"{item.id}: {label} exceeds {MAX_FIELD_BYTES} bytes.")


def normalize_answer(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def stable_int(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:16], 16)


def write_jsonl(items: Iterable[QuizItem], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for item in items:
            validate_item(item)
            handle.write(json.dumps(asdict(item), ensure_ascii=False, separators=(",", ":")) + "\n")


def write_quizbin(items: Iterable[QuizItem], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = bytearray()
    for item in items:
        validate_item(item)
        write_field(payload, item.question)
        for answer in item.answers:
            write_field(payload, answer)
        payload.append(item.correctIndex)
    output_path.write_bytes(bytes(payload))


def write_field(payload: bytearray, value: str) -> None:
    encoded = value.encode("utf-8")
    if len(encoded) > MAX_FIELD_BYTES:
        raise ValueError(f"Field exceeds {MAX_FIELD_BYTES} bytes.")
    payload.extend(struct.pack("<H", len(encoded)))
    payload.extend(encoded)


def default_output_base(source_path: Path) -> Path:
    return Path("workbench") / "quiz_decks" / source_path.stem


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a deterministic quiz deck from a TAH cartridge.")
    parser.add_argument("source", type=Path, help="Input .tah cartridge path.")
    parser.add_argument("--jsonl", type=Path, help="Output authoring JSONL path.")
    parser.add_argument("--binary", type=Path, help="Output Android .quizbin path.")
    parser.add_argument("--limit", type=int, default=25, help="Maximum number of quiz items.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.limit <= 0:
        raise ValueError("--limit must be positive.")

    source_path = args.source
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    base = default_output_base(source_path)
    jsonl_path = args.jsonl or base.with_suffix(".jsonl")
    binary_path = args.binary or base.with_suffix(".quizbin")

    items = build_quiz_deck(source_path, limit=args.limit)
    write_jsonl(items, jsonl_path)
    write_quizbin(items, binary_path)

    summary = {
        "source": str(source_path),
        "items": len(items),
        "jsonl": str(jsonl_path),
        "binary": str(binary_path),
        "generator": GENERATOR_VERSION,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
