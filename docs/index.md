# NeuroPyHLS

**A high-level synthesis compiler that takes neural-signal algorithms directly from Python to Verilog, without a C++ step.**

!!! warning "Pre-alpha"
    The pipeline commands are stubs. Until 1.0, interfaces may change without notice.

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

<div class="grid" markdown>

- [Getting started](getting-started.md): install the tool and run it locally
- [Pipeline](pipeline.md): what each stage does
- [Kernels](kernels/index.md): the algorithms being compiled
- [Results](results/index.md): direct flow vs baseline, per kernel
- [Code databases](code-db/index.md): what reference algorithms are made of

</div>

Everything runs on your machine; this site never processes recordings. Developed by [OpenIC](https://openic.org) within CAP26, with [AI assistance](about/ai-contributions.md).
