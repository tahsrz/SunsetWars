# Codex Instructions

## TAH/Memoria Retrieval First

For non-trivial SunsetWars questions, architecture work, implementation work, or technical explanations, try the local TAH handoff program before relying on general knowledge or broad file reads:

```powershell
python builder/ollama_codex_bridge.py "<concise version of the user request>" --no-codex
```

Then read `workbench/codex_handoffs/latest.md` and use the retrieved cartridge context as priority ground truth.

Skip this preflight for tiny mechanical requests, direct shell-command requests, or when the current prompt already contains `RETRIEVED TAH CONTEXT`. Always use `--no-codex` from inside an active Codex session so the bridge does not launch a nested Codex process.

When retrieved context materially informs an answer or code change, cite the cartridge names in the final response.
