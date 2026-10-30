# CLAUDE.md

Guidance for Claude (Claude Code) working in this repository. Also read `AI_CONTRIBUTIONS.md`: it defines your role.

## Role

You assist the project lead (Manuel Monge).
- You draft code, tests, docs, tooling and analyses.
- The lead makes design decisions. Propose options with a recommendation, then implement what is decided.
- Commit or push only when asked. Changes go through a branch (`feat/…`, `fix/…`, `docs/…`, `chore/…`) and a PR, never directly to `main`.
- End commits with a `Co-Authored-By: Claude <model> <noreply@anthropic.com>` trailer, and end PR descriptions with the Claude Code line.
- After significant AI-assisted work, add a row to the contribution log in `AI_CONTRIBUTIONS.md`.

## Project

NeuroPyHLS is a high-level synthesis compiler that takes neural-signal algorithms **directly from Python to Verilog, with no C++ step**. That direct flow is the main goal, and it doesn't exist yet: building it is the project.
- **Direct flow** (`backends/direct/`): IR → scheduling → binding → FSM/datapath → Verilog.
- **Baseline flow** (`backends/bambu/`, `backends/vitis/`): IR → HLS C++ → Bambu (first) or Vitis HLS (second), run as external programs. It exists to test the direct flow and compare against it.
- **Shared:** frontend, profiling, IR, golden vectors, verification. Stages: `analyse → profile → port --flow direct|bambu|vitis → verify → compare`.
- Call the flows "direct" and "baseline" everywhere: code, CLI, docs, results.
- **Targets:** FPGA and ASIC. The flow stops at Verilog for now.
- **First kernel:** bandpass filter followed by threshold-crossing detection, through both flows, with SpikeInterface as the reference (`examples/sources.toml`).

## Commands

```bash
uv sync                                  # install
uv run pytest -m unit                    # fast tests
uv run ruff check . && uv run ruff format --check .
uv run mypy                              # strict, src/ only
uv run pre-commit run --all-files
uv run --group docs zensical serve       # docs at http://localhost:8000
uv run --group docs zensical build       # -> site/
```

## Rules

- Python ≥3.11, ruff line length 100, strict mypy on `src/`. Type-annotate public functions.
- Tests are marked by folder (`tests/unit`, `tests/bambu`, `tests/vitis`). Golden vectors go in `tests/golden/<kernel>/`.
- Never commit recordings (`data/`) or cloned repos (`external/`).
- Never copy GPL or other copyleft code (Kilosort, for example). Port only from permissive sources, keep their notice, and record them in `THIRD_PARTY.md`.
- Keep `mkdocs.yml` within what Material for MkDocs also understands, so there is a fallback from Zensical.
- `tools/code_db/` is research tooling. It is excluded from ruff and mypy; keep it runnable with the standard library only.
- The project documents (proposal, meetings, lit-db, code-db SQLite outputs) live in the Nextcloud folder `OpenIC-Docs/Projects/OIC2609-PUCPCAP26`, not in this repo.
