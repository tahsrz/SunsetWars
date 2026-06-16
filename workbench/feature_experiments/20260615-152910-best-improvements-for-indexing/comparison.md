# Feature A/B Experiment: Best improvements for indexing

## Arms
- Baseline: implement from normal repo inspection only.
- TAH-assisted: implement from `tah_prompt.md`, using retrieved cartridge context as priority ground truth.

## Generated Files
- `baseline_prompt.md`
- `tah_prompt.md`
- `manifest.json`

## TAH Retrieval Snapshot
- Retrieval time: 3993.01 ms
- Atlas results: 4
- Shard results: 20
- Sources:
- sunset_wars.tah
- sunset_wars_runtime_matrix.tah
- deepLearning.tah
- algorithms.tah
- dataDesign.tah

## How To Run The Experiment
1. Start from a clean branch or worktree.
2. Give Codex `baseline_prompt.md` and implement the baseline arm.
3. Save the diff summary, test output, time spent, and any blockers below.
4. Reset or switch to another clean branch/worktree.
5. Give Codex `tah_prompt.md` and implement the TAH-assisted arm.
6. Compare both arms using the scorecard below.

## Scorecard
| Metric | Baseline | TAH-assisted | Notes |
| --- | --- | --- | --- |
| Time to first viable patch |  |  |  |
| Files inspected |  |  |  |
| Files changed |  |  |  |
| Tests passing |  |  |  |
| Defects found in review |  |  |  |
| Repo-specific concepts used |  |  |  |
| Unnecessary context read |  |  |  |
| Final confidence |  |  |  |

## Baseline Notes

## TAH-Assisted Notes

## Decision
