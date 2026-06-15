import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from segmented_expert_atlas import SegmentedExpertAtlasQuery, build_atlas_from_cartridges, domain_mask_for_label


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_BASE = ROOT / "cartridges" / "expert_atlas" / "segmented_expert_atlas"


def main() -> None:
    max_experts = int(os.environ.get("EXPERT_ATLAS_MAX_EXPERTS", "400"))
    segment_size = int(os.environ.get("EXPERT_ATLAS_SEGMENT_SIZE", "16"))

    manifest = build_atlas_from_cartridges(
        root=ROOT,
        output_base=OUTPUT_BASE,
        max_experts=max_experts,
        segment_size=segment_size,
    )

    print(json.dumps({
        "hatPath": str(OUTPUT_BASE.with_suffix(".hat")),
        "tahPath": str(OUTPUT_BASE.with_suffix(".tah")),
        "manifestPath": str(OUTPUT_BASE.with_suffix(".manifest.json")),
        **manifest,
    }, indent=2))

    query = SegmentedExpertAtlasQuery(OUTPUT_BASE)
    smoke = query.search(
        "architecture",
        domain_mask=domain_mask_for_label("architecture cache cpu"),
        top_n=2,
        max_segments=8,
    )
    print("\nSMOKE:")
    print(json.dumps({
        "diagnostics": smoke["diagnostics"],
        "results": [
            {
                "title": row["title"],
                "source": row["source"],
                "density": round(row["density"], 3),
                "vitality": round(row["vitality"], 3),
                "concepts": row["concepts"][:5],
                "linkCount": len(row["links"]),
            }
            for row in smoke["results"]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
