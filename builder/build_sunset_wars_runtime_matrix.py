import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from memoria_builder import MemoriaBuilder, OzrielSegmenter


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "specs" / "sunset_wars_runtime_magic_matrix.md"
OUTPUT_BASE = ROOT / "cartridges" / "sunset_wars_runtime_matrix"


RUNTIME_SHARDS = [
    {
        "title": "Sunset Wars Runtime Magic Matrix",
        "text": (
            "Sunset Wars maps prompt-style slot aggregation into a fixed four-slot "
            "runtime spell matrix. Slots are Core, Trajectory, Modifier A, and "
            "Modifier B. The editor can keep rich MagicModule records, but combat "
            "receives a compact CompiledSpellPayload for hot-swapping."
        ),
        "relevance": 1.0,
    },
    {
        "title": "Compiled Spell Payload Contract",
        "text": (
            "CompiledSpellPayload version 1 contains moduleIds, complexity, flags, "
            "baseDamage, speedMultiplier, projectileCount, aoeRadius, statusEffectIds, "
            "and vfxIndices. The compiler rejects loadouts above maxTokenCapacity and "
            "uses engine table indices instead of rich runtime objects."
        ),
        "relevance": 1.0,
    },
    {
        "title": "Zustand Magic Matrix Boundary",
        "text": (
            "Zustand owns inventory, equipped slots, drag-and-drop interactions, overload "
            "warnings, and compiled preview state. It should not be the combat runtime. "
            "Gameplay handlers consume only the compiled payload."
        ),
        "relevance": 0.9,
    },
    {
        "title": "UE5 Magic Payload Bridge",
        "text": (
            "UE5 mirrors the compiled spell as FSunsetCompiledSpellPayload with primitive "
            "fields and integer arrays. Projectile, damage, status, Niagara, and shader "
            "systems resolve behavior through flags and table indices."
        ),
        "relevance": 0.95,
    },
]


def build() -> None:
    if not SPEC_PATH.exists():
        raise FileNotFoundError(f"Missing source spec: {SPEC_PATH}")

    builder = MemoriaBuilder(expected_elements=800)

    spec_text = SPEC_PATH.read_text(encoding="utf-8")
    for index, shard in enumerate(OzrielSegmenter.segment(spec_text, max_shard_size=1000)):
        builder.add_text_shard(
            text=shard,
            url=f"local://specs/sunset_wars_runtime_magic_matrix.md#{index}",
            location="USA_TX",
            relevance=0.9,
        )

    for shard in RUNTIME_SHARDS:
        builder.add_text_shard(
            text=f"{shard['title']}\n\n{shard['text']}",
            url="local://sunset_wars/runtime_magic_matrix",
            location="USA_TX",
            relevance=shard["relevance"],
        )

    os.makedirs(OUTPUT_BASE.parent, exist_ok=True)
    builder.save(str(OUTPUT_BASE))


if __name__ == "__main__":
    build()
