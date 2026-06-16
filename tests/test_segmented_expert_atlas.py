import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "builder"))

from segmented_expert_atlas import (  # noqa: E402
    SegmentedExpertAtlasQuery,
    build_atlas_from_cartridges,
    domain_mask_for_label,
)


class SegmentedExpertAtlasTest(unittest.TestCase):
    def test_builds_bootstrap_and_cartridge_experts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cartridges = root / "cartridges"
            cartridges.mkdir()
            (cartridges / "architecture.tah").write_text(
                "\0".join([
                    "Architecture cache hierarchy uses memory ordering, branch prediction, and pipeline routing.",
                    "SIMD vector lanes improve processor throughput when data alignment is predictable.",
                ]),
                encoding="utf-8",
            )
            (cartridges / "dallas_safety_intel.tah").write_text(
                "Dallas safety incident response uses community reports, location context, and priority routing.",
                encoding="utf-8",
            )

            output_base = cartridges / "expert_atlas" / "segmented_expert_atlas"
            manifest = build_atlas_from_cartridges(root, output_base, max_experts=24, segment_size=4)
            self.assertGreaterEqual(manifest["expertCount"], 6)

            atlas = SegmentedExpertAtlasQuery(output_base)
            feature = atlas.search(
                "semantic expert atlas retrieval feature",
                domain_mask=domain_mask_for_label("semantic expert atlas retrieval feature"),
                top_n=2,
                max_segments=4,
            )
            self.assertGreaterEqual(len(feature["results"]), 1)
            self.assertEqual(feature["results"][0]["source"], "expert_atlas.bootstrap")
            self.assertGreater(feature["results"][0]["vitality"], 0)
            self.assertGreater(len(feature["results"][0]["links"]), 0)

            architecture = atlas.search(
                "cache memory architecture",
                domain_mask=domain_mask_for_label("architecture cache cpu"),
                top_n=2,
                max_segments=4,
            )
            self.assertGreaterEqual(len(architecture["results"]), 1)
            self.assertIn("architecture.tah", {row["source"] for row in architecture["results"]})
            self.assertLessEqual(
                architecture["diagnostics"]["payloadReads"],
                max(4, architecture["diagnostics"]["candidateExperts"]),
            )


if __name__ == "__main__":
    unittest.main()
