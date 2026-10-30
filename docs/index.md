# NeuroPyHLS

**Compile Python neural-signal algorithms to HLS C++ and Verilog, and verify the hardware against the Python reference.**

!!! warning "Pre-alpha"
    The pipeline commands are stubs. Until 1.0, interfaces may change without notice.

NeuroPyHLS has two parts:

- **A compiler-like tool.** A Python algorithm goes in. It is analysed, profiled and ported to HLS C++, and Bambu (or Vitis HLS) turns that into a Verilog kernel, with no hand edits. The targets are FPGA and ASIC.
- **A research environment.** It holds the code databases of reference implementations, the literature database, and the results of each ported kernel.

<div class="grid" markdown>

- [Getting started](getting-started.md): install the tool and run it locally
- [Pipeline](pipeline.md): what each stage does
- [Kernels](kernels/index.md): the algorithms being ported
- [Code databases](code-db/index.md): what reference algorithms are made of

</div>

Everything runs on your machine; this site never processes recordings. Developed by [OpenIC](https://openic.org) within CAP26, with [AI assistance](about/ai-contributions.md).
