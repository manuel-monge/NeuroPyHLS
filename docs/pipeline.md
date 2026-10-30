# Pipeline

NeuroPyHLS compiles a Python kernel to Verilog through two flows that share their front half.

- **Direct:** IR → Verilog with no C++ step. This is the compiler the project is building.
- **Baseline:** IR → HLS C++ → Bambu or Vitis HLS → Verilog. This established route is used to test the direct flow and compare against it.

```
                                           ┌─► direct:   schedule ─► bind ─► FSM/datapath ─► Verilog (A)
Python kernel ─► analyse ─► profile ─► IR ─┤
                                           └─► baseline: HLS C++ ─► Bambu / Vitis HLS ─────► Verilog (B)

verify:   Python  vs  RTL sim (A)  vs  C sim + RTL sim (B)        compare:  A vs B
```

## Shared stages

| Stage | Command | What it does | Package |
|---|---|---|---|
| Analyse | `neuropyhls analyse` | Parses the kernel and finds its loops, operations, library calls and state | `frontend`, `passes` |
| Profile | `neuropyhls profile` | Runs the Python kernel on recordings to measure value ranges and operation counts, which set the fixed-point formats | `passes` |
| Lower | (inside `port`) | Builds the IR: a dataflow graph with fixed-point types | `ir`, `passes` |

## Direct flow: `neuropyhls port --flow direct` (default)

| Stage | What it does |
|---|---|
| Scheduling | Assigns each operation to a clock cycle under latency and resource constraints, and pipelines loops to a target initiation interval |
| Binding | Maps operations to shared functional units (multipliers, adders) and values to registers |
| Control | Generates the finite-state machine that sequences the datapath |
| Emission | Writes synthesizable Verilog for the datapath and controller, with a standard streaming interface |

All of this lives in `backends/direct/`.

## Baseline flow: `neuropyhls port --flow bambu` or `--flow vitis`

| Stage | What it does |
|---|---|
| C++ generation | Writes HLS C++ with fixed-point types, plus the HLS tool's build script |
| HLS | Runs Bambu or Vitis HLS as an external program, producing Verilog |

This lives in `backends/bambu/` and `backends/vitis/`.

## Verification and comparison

| Command | What it does |
|---|---|
| `neuropyhls verify --flow …` | Runs a flow's Verilog in RTL simulation (Verilator), and the baseline's C++ in C simulation, on the golden vectors. The flow passes if it meets the kernel's error/SNR threshold against Python |
| `neuropyhls compare` | Reports the direct flow next to the baseline flows for each kernel: accuracy, latency, initiation interval, resources (LUT/FF/DSP or area) and maximum clock |

Both flows stop at Verilog for now. Logic synthesis and place-and-route for FPGA and ASIC come later.
