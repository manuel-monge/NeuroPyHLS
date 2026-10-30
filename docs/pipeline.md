# Pipeline

```
Python kernel ──► analyse ──► profile ──► port ──► HLS C++ ──► Bambu / Vitis HLS ──► Verilog
                                                     │                                 │
                                                     └──── verify: Python vs C sim vs RTL sim
```

| Stage | Command | What it does | Package |
|---|---|---|---|
| Analyse | `neuropyhls analyse` | Parses the kernel and finds its loops, operations, library calls and state | `frontend`, `passes` |
| Profile | `neuropyhls profile` | Runs the Python kernel on recordings to measure value ranges and operation counts, which set the fixed-point formats | `passes` |
| Port | `neuropyhls port` | Lowers the IR to synthesizable HLS C++ with fixed-point types and writes the HLS tool's build scripts | `ir`, `passes`, `backends` |
| Synthesize | (inside `port`) | Runs Bambu or Vitis HLS as an external tool, producing Verilog | `backends` |
| Verify | `neuropyhls verify` | Compares Python, C simulation and RTL simulation (Verilator) on golden vectors, and accepts the kernel if it meets its error/SNR threshold | `verify` |

The flow stops at Verilog for now. Logic synthesis and place-and-route for FPGA and ASIC come later.
