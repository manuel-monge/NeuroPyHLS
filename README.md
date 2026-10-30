# NeuroPyHLS

**A high-level synthesis compiler that takes neural-signal algorithms directly from Python to Verilog, without a C++ step.**

[Documentation](https://openic-org.github.io/NeuroPyHLS/) · [Contributing](CONTRIBUTING.md) · [AI contributions](AI_CONTRIBUTIONS.md) · License: Apache-2.0 (code), CC-BY-4.0 (docs)

> **Status: pre-alpha (`0.1.0.dev0`).** The pipeline commands are stubs. Until 1.0, interfaces may change without notice.

NeuroPyHLS has three parts:

1. **A direct Python → Verilog HLS compiler (the main goal).** A neural-signal algorithm written in Python is lowered straight to a Verilog kernel, with no C++ step. NeuroPyHLS does the scheduling, resource binding and control generation itself. This path is under development; building it is what the project is about.
2. **A baseline flow, Python → HLS C++ → Verilog.** The same Python kernel is ported to HLS C++ and synthesized with Bambu (or Vitis HLS). It acts as the reference the direct compiler is tested and compared against: same inputs, same golden vectors, and a side-by-side comparison of accuracy, latency, throughput and resources.
3. **A research environment.** It holds the code databases, the literature database, notebooks and results behind both flows.

Both flows share the frontend, profiling, IR, golden vectors and verification. Only the back half differs, so any difference in results comes from the compiler itself. The targets are FPGA and ASIC; for now both flows stop at Verilog.

```
                                           ┌─► direct:   schedule ─► bind ─► FSM/datapath ─► Verilog (A)
Python kernel ─► analyse ─► profile ─► IR ─┤
                                           └─► baseline: HLS C++ ─► Bambu / Vitis HLS ─────► Verilog (B)

verify:   Python  vs  RTL sim (A)  vs  C sim + RTL sim (B)        compare:  A vs B
```

The first target is a **bandpass filter followed by a threshold-crossing spike detector**, compiled through both flows, with SpikeInterface as the Python reference.

## Quick start

You need [uv](https://docs.astral.sh/uv/) and Git. Verilator is needed for RTL simulation, and Bambu only for the baseline flow.

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
| `src/neuropyhls/` | The package: `frontend/` (Python → IR), `ir/`, `passes/` (analysis, profiling, fixed point), `backends/` (`direct/` → Verilog; baseline `bambu/`, `vitis/` via HLS C++), `verify/`, and the CLI |
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
- **Baseline HLS tools are external.** For the baseline flow, NeuroPyHLS calls Bambu (GPL-3.0) and Vitis HLS (proprietary) as separate programs. It does not include, link or redistribute them; you install them yourself. See [THIRD_PARTY.md](https://github.com/openic-org/NeuroPyHLS/blob/main/THIRD_PARTY.md).
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
