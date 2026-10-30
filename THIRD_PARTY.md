# Third-party software and code

## External tools (not included, linked, or redistributed)

NeuroPyHLS runs these as separate programs that users install themselves. Their licences do not extend to NeuroPyHLS or to the output it generates.

| Tool | Licence | Use |
|---|---|---|
| [Bambu (PandA)](https://panda.dei.polimi.it/) | GPL-3.0 | Primary HLS backend: C++ → Verilog |
| [AMD Vitis HLS](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vitis/vitis-hls.html) | Proprietary (AMD) | Secondary HLS backend |
| [Verilator](https://www.veripool.org/verilator/) | LGPL-3.0 / Artistic-2.0 | RTL simulation |
| [cocotb](https://www.cocotb.org/) | BSD-3-Clause | Python testbenches for RTL (optional `rtl` dependency group) |

## Reference repositories (cloned into `external/`, not committed)

These are listed in `examples/sources.toml`.

| Repository | Licence | Use |
|---|---|---|
| [SpikeInterface](https://github.com/SpikeInterface/spikeinterface) | MIT | Reference implementations, golden vectors, code-db input |

## Code ported into this repository

When code is ported or adapted from a permissively licensed source, add a row and keep the original copyright notice in the file header.

| File in this repo | Source (repo, commit, file) | Licence | Notes |
|---|---|---|---|
| none yet | | | |
