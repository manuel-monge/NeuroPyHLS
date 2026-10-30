# NeuroPyHLS

**Compile Python neural-signal algorithms to HLS C++ and Verilog, and verify the hardware against the Python reference.**

[Documentation](https://openic-org.github.io/NeuroPyHLS/) · [Contributing](CONTRIBUTING.md) · [AI contributions](AI_CONTRIBUTIONS.md) · License: Apache-2.0 (code), CC-BY-4.0 (docs)

> **Status: pre-alpha (`0.1.0.dev0`).** The pipeline commands are stubs. Until 1.0, interfaces may change without notice.

NeuroPyHLS has two parts:

1. **A compiler-like tool.** A Python algorithm goes in. It is analysed, profiled and ported to HLS C++, and an HLS tool turns that into a Verilog kernel, with no hand edits. The targets are FPGA and ASIC; for now the flow stops at Verilog.
2. **A research environment.** It holds the notebooks, analyses, code databases, results and documentation behind the tool.

```
Python kernel ──► analyse ──► profile ──► port ──► HLS C++ ──► Bambu / Vitis HLS ──► Verilog
                                                     │                                 │
                                                     └──── verify: Python vs C sim vs RTL sim (golden vectors, error/SNR)
```

The first target is a **bandpass filter followed by a threshold-crossing spike detector**, using SpikeInterface as the reference implementation.

## Quick start

You need [uv](https://docs.astral.sh/uv/) and Git. Bambu and Verilator are needed only for the hardware steps.

```bash
git clone https://github.com/openic-org/NeuroPyHLS.git
cd NeuroPyHLS
uv sync                          # creates .venv with the package and the dev tools
uv run neuropyhls --help
uv run neuropyhls fetch-sources  # clones reference repos into external/
uv run pytest -m unit
```

Everything runs locally. The public docs site never processes recordings.

## Repository layout

| Path | Contents |
|---|---|
| `src/neuropyhls/` | The package: `frontend/` (Python → IR), `ir/`, `passes/` (analysis, profiling, fixed point), `backends/` (Bambu, Vitis), `verify/`, and the CLI |
| `tests/` | `unit/`, `bambu/`, `vitis/` (marked automatically by folder) and `golden/` vectors |
| `rtl/` | Hand-written Verilog (wrappers, testbenches) |
| `notebooks/` | Jupytext-paired notebooks, stored as `.py` files |
| `examples/` | `sources.toml` (pinned reference repos) and `datasets.toml` (recordings with checksums) |
| `tools/code_db/` | Static-analysis code databases of reference repos |
| `scripts/` | Generates the docs result pages |
| `docs/` | Documentation site (Zensical) |
| `data/`, `external/` | Downloaded recordings and cloned repos (git-ignored) |

## Licensing: rules for users and collaborators

<!-- --8<-- [start:licensing] -->
- **Code** is under the [Apache License 2.0](https://github.com/openic-org/NeuroPyHLS/blob/main/LICENSE). **Documentation** in `docs/` is under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).
- **Your generated output is yours.** The HLS C++, Verilog and reports that NeuroPyHLS produces from your algorithms belong to you. Our licence places no conditions on them.
- **HLS tools are external.** NeuroPyHLS calls Bambu (GPL-3.0) and Vitis HLS (proprietary) as separate programs. It does not include, link or redistribute them; you install them yourself. See [THIRD_PARTY.md](https://github.com/openic-org/NeuroPyHLS/blob/main/THIRD_PARTY.md).
- **Porting other people's code.** Port only from permissively licensed sources (MIT, BSD, Apache-2.0, and similar). Keep their copyright notice and add an entry to `THIRD_PARTY.md`.
- **Never copy GPL or other copyleft code into this repository**, for example Kilosort. You may read it as a reference for behaviour and write an independent implementation.
- **Contributions** are accepted under the same licences (inbound = outbound). There is no CLA; see [CONTRIBUTING.md](https://github.com/openic-org/NeuroPyHLS/blob/main/CONTRIBUTING.md).
<!-- --8<-- [end:licensing] -->

## AI assistance

This project is developed with help from Claude, an AI assistant by Anthropic, under the direction of the project lead. Humans make the design decisions, review every change, and are the only authors. [AI_CONTRIBUTIONS.md](AI_CONTRIBUTIONS.md) describes what the assistant does and how its work is traced.

## Citing

See [CITATION.cff](CITATION.cff), or use GitHub's "Cite this repository" button.

## Acknowledgements

Developed by [OpenIC](https://openic.org) within the CAP26 project (OIC2609-PUCPCAP26).
