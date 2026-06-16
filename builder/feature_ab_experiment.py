import argparse
import json
import re
import time
from pathlib import Path

from ollama_codex_bridge import (
    DEFAULT_OLLAMA_HOST,
    build_codex_prompt,
    build_query_plan,
    choose_relevant_sources,
    query_expert_atlas,
    query_relevant_cartridges,
)


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_DIR = ROOT / "workbench" / "feature_experiments"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create paired baseline and TAH-assisted Codex briefs for one feature experiment."
    )
    parser.add_argument("feature", help="Feature or improvement to build in both experiment arms.")
    parser.add_argument("--model", help="Ollama model to use for TAH query planning.")
    parser.add_argument("--ollama-host", default=None)
    parser.add_argument("--atlas-top-n", type=int, default=8)
    parser.add_argument("--source-top-n", type=int, default=4)
    parser.add_argument("--max-sources", type=int, default=8)
    parser.add_argument("--max-context-chars", type=int, default=18000)
    args = parser.parse_args()

    started = time.perf_counter()
    experiment_path = make_experiment_dir(args.feature)

    baseline_prompt = build_baseline_prompt(args.feature)
    (experiment_path / "baseline_prompt.md").write_text(baseline_prompt, encoding="utf-8")

    retrieval_started = time.perf_counter()
    plan = build_query_plan(args.feature, args.ollama_host or DEFAULT_OLLAMA_HOST, args.model)
    atlas_hits, atlas_diagnostics = query_expert_atlas(plan, args.atlas_top_n)
    source_names = choose_relevant_sources(atlas_hits, args.max_sources)
    shard_hits = query_relevant_cartridges(plan, source_names, args.source_top_n)
    retrieval_ms = round((time.perf_counter() - retrieval_started) * 1000, 2)

    tah_prompt = build_codex_prompt(
        plan=plan,
        atlas_hits=atlas_hits,
        atlas_diagnostics=atlas_diagnostics,
        shard_hits=shard_hits,
        max_context_chars=args.max_context_chars,
    )
    (experiment_path / "tah_prompt.md").write_text(tah_prompt, encoding="utf-8")

    comparison = build_comparison_sheet(args.feature, source_names, atlas_hits, shard_hits, retrieval_ms)
    (experiment_path / "comparison.md").write_text(comparison, encoding="utf-8")

    manifest = {
        "feature": args.feature,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "experimentPath": str(experiment_path),
        "retrievalMs": retrieval_ms,
        "tokens": plan.tokens,
        "concepts": plan.concepts,
        "ollamaModel": plan.model,
        "fallbackReason": plan.fallback_reason,
        "sources": source_names,
        "atlasResults": len(atlas_hits),
        "shardResults": len(shard_hits),
        "files": {
            "baselinePrompt": str(experiment_path / "baseline_prompt.md"),
            "tahPrompt": str(experiment_path / "tah_prompt.md"),
            "comparison": str(experiment_path / "comparison.md"),
        },
        "totalMs": round((time.perf_counter() - started) * 1000, 2),
    }
    (experiment_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


def make_experiment_dir(feature: str) -> Path:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", feature.lower()).strip("-")[:60] or "feature"
    path = EXPERIMENT_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}-{slug}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def build_baseline_prompt(feature: str) -> str:
    return "\n".join([
        "You are Codex working inside the SunsetWars repository.",
        "This is the BASELINE arm of a feature experiment.",
        "Do not run builder/ollama_codex_bridge.py or read workbench/codex_handoffs/latest.md for this arm.",
        "Use ordinary repository inspection, local tests, and implementation judgment only.",
        "",
        f"FEATURE SPEC: {feature}",
        "",
        "TASK:",
        "Implement the feature with the smallest reasonable change set.",
        "Record what files you inspected, what files you changed, and what verification you ran.",
        "Avoid unrelated refactors.",
    ])


def build_comparison_sheet(feature: str, sources: list[str], atlas_hits: list, shard_hits: list, retrieval_ms: float) -> str:
    source_lines = "\n".join(f"  - {source}" for source in sources) or "  - No TAH sources selected"
    return "\n".join([
        f"# Feature A/B Experiment: {feature}",
        "",
        "## Arms",
        "- Baseline: implement from normal repo inspection only.",
        "- TAH-assisted: implement from `tah_prompt.md`, using retrieved cartridge context as priority ground truth.",
        "",
        "## Generated Files",
        "- `baseline_prompt.md`",
        "- `tah_prompt.md`",
        "- `manifest.json`",
        "",
        "## TAH Retrieval Snapshot",
        f"- Retrieval time: {retrieval_ms} ms",
        f"- Atlas results: {len(atlas_hits)}",
        f"- Shard results: {len(shard_hits)}",
        "- Sources:",
        source_lines,
        "",
        "## How To Run The Experiment",
        "1. Start from a clean branch or worktree.",
        "2. Give Codex `baseline_prompt.md` and implement the baseline arm.",
        "3. Save the diff summary, test output, time spent, and any blockers below.",
        "4. Reset or switch to another clean branch/worktree.",
        "5. Give Codex `tah_prompt.md` and implement the TAH-assisted arm.",
        "6. Compare both arms using the scorecard below.",
        "",
        "## Scorecard",
        "| Metric | Baseline | TAH-assisted | Notes |",
        "| --- | --- | --- | --- |",
        "| Time to first viable patch |  |  |  |",
        "| Files inspected |  |  |  |",
        "| Files changed |  |  |  |",
        "| Tests passing |  |  |  |",
        "| Defects found in review |  |  |  |",
        "| Repo-specific concepts used |  |  |  |",
        "| Unnecessary context read |  |  |  |",
        "| Final confidence |  |  |  |",
        "",
        "## Baseline Notes",
        "",
        "## TAH-Assisted Notes",
        "",
        "## Decision",
        "",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
