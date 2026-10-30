# Code databases

Relational databases of reference Python repositories, built by static analysis (the code is never imported or run). For every algorithm they record which functions it reaches, which library APIs and Python primitives it uses, and how deep in the call graph each one appears. This shows what a port will have to support.

| Repository | Commit | Algorithms | Explorer |
|---|---|---|---|
| SpikeInterface | `e1edb1a` | 178 | [Open the algorithm explorer](spikeinterface-explorer.html) |

## Tables

- **Entities:** `algorithms`, `functions`, `classes`, `modules`, `libraries`, `library_api`, `primitives`.
- **Links:** `calls`, `imports`, `function_library_api`, `function_primitives`, `function_methods`, `algorithm_functions`, `algorithm_relations`.
- **`global_dataset`:** one row per (algorithm, element), with `min_depth`, `n_uses` and `n_via_functions`.

The tools and their full documentation are in `tools/code_db/` in the repository.

## Rebuild

```bash
uv run neuropyhls fetch-sources spikeinterface
python3 -I tools/code_db/build_code_db.py external/spikeinterface spikeinterface out/code-db/spikeinterface --commit e1edb1a0e9d4c9701110e6a0d0538631e1dc0f2f
python3 -I tools/code_db/build_explorer.py out/code-db/spikeinterface/spikeinterface_code.sqlite tools/code_db/explorer_template.html docs/code-db/spikeinterface-explorer.html
```
