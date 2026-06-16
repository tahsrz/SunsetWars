import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from segmented_expert_atlas import SegmentedExpertAtlasQuery, domain_mask_for_label


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATLAS_BASE = ROOT / "cartridges" / "expert_atlas" / "segmented_expert_atlas"


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the segmented expert atlas without invoking Ollama or Codex.")
    parser.add_argument("query", help="Search text.")
    parser.add_argument("--atlas", default=str(DEFAULT_ATLAS_BASE), help="Atlas base path without .hat/.tah suffix.")
    parser.add_argument("--domain", help="Optional domain label used to build the route mask.")
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--max-segments", type=int, default=8)
    parser.add_argument("--text-chars", type=int, default=420)
    parser.add_argument("--full", action="store_true", help="Print full result payloads.")
    args = parser.parse_args()

    atlas = SegmentedExpertAtlasQuery(args.atlas)
    result = atlas.search(
        args.query,
        domain_mask=domain_mask_for_label(args.domain or args.query),
        top_n=args.top_n,
        max_segments=args.max_segments,
    )

    print(json.dumps({
        "query": args.query,
        "diagnostics": result["diagnostics"],
        "results": [
            {
                "expertId": row["expertId"],
                "title": row["title"],
                "source": row["source"],
                "score": round(row["score"], 3),
                "density": round(row["density"], 3),
                "vitality": round(row["vitality"], 3),
                "concepts": row["concepts"][:8],
                "links": row["links"][:5],
                "text": row["text"] if args.full else row["text"][:args.text_chars],
            }
            for row in result["results"]
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
