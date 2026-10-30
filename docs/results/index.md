# Results

Results compare the **direct** Python → Verilog flow with the **baseline** flows (Bambu and Vitis HLS via HLS C++), kernel by kernel, on the same golden vectors.

| Metric | Meaning |
|---|---|
| SNR / max error | Agreement with the Python reference |
| Detection agreement | For detectors: matched events versus the Python reference |
| Latency, II | Cycles from input to output, and the initiation interval |
| Resources | LUT, FF, DSP and BRAM (FPGA), or cell area (ASIC), once synthesis is added |
| Fmax | Maximum clock frequency, once synthesis is added |

The [summary table](summary.md) is generated from `results/*.json` by `scripts/gen_docs.py`. Each JSON file holds one (kernel, flow) entry.
