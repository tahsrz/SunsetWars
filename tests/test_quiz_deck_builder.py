import json
import struct
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "builder"))

from build_quiz_deck import build_quiz_deck, write_jsonl, write_quizbin  # noqa: E402


class QuizDeckBuilderTest(unittest.TestCase):
    def test_builds_jsonl_and_android_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sample.tah"
            source.write_text("\0".join(sample_shards()), encoding="utf-8")

            items = build_quiz_deck(source, limit=4)
            self.assertEqual(len(items), 4)
            for item in items:
                self.assertEqual(len(item.answers), 4)
                self.assertIn(item.correctIndex, range(4))
                self.assertEqual(item.answers[item.correctIndex], item.supportText)

            jsonl_path = root / "sample.jsonl"
            binary_path = root / "sample.quizbin"
            write_jsonl(items, jsonl_path)
            write_quizbin(items, binary_path)

            rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 4)
            parsed = parse_quizbin(binary_path.read_bytes())
            self.assertEqual(len(parsed), 4)
            self.assertEqual(parsed[0]["question"], rows[0]["question"])
            self.assertEqual(parsed[0]["answers"], rows[0]["answers"])
            self.assertEqual(parsed[0]["correctIndex"], rows[0]["correctIndex"])


def parse_quizbin(data: bytes) -> list[dict]:
    offset = 0
    rows = []
    while offset < len(data):
        question, offset = read_field(data, offset)
        answers = []
        for _ in range(4):
            answer, offset = read_field(data, offset)
            answers.append(answer)
        correct_index = data[offset]
        offset += 1
        rows.append({"question": question, "answers": answers, "correctIndex": correct_index})
    return rows


def read_field(data: bytes, offset: int) -> tuple[str, int]:
    length = struct.unpack_from("<H", data, offset)[0]
    offset += 2
    value = data[offset:offset + length].decode("utf-8")
    return value, offset + length


def sample_shards() -> list[str]:
    return [
        (
            "Merge sort divides an input sequence into smaller pieces before combining sorted results into one ordered output. "
            "Binary search repeatedly halves a sorted search range so that each comparison removes many remaining candidates. "
            "Dynamic programming stores overlapping subproblem results so later computations can reuse earlier work. "
            "A greedy algorithm makes a locally best choice at each step and depends on a proof that those choices remain globally valid."
        ),
        (
            "Hash tables use a hash function to map keys into buckets where values can usually be found quickly. "
            "Breadth first search explores vertices by increasing distance from the starting vertex in an unweighted graph. "
            "Depth first search follows one path deeply before backing up to try alternative edges. "
            "Dijkstra's algorithm maintains tentative shortest distances and repeatedly settles the closest unsettled vertex."
        ),
    ]


if __name__ == "__main__":
    unittest.main()
