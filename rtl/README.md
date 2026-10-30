# Hand-written RTL

Verilog that is written by hand rather than generated: top-level wrappers, interface adapters, and testbench helpers.

- Generated Verilog is not committed. It is rebuilt from the HLS C++ by `neuropyhls port`.
- Lint and format with [Verible](https://github.com/chipsalliance/verible). The pre-commit hooks run it when it is installed.
- Simulate with Verilator. Python testbenches use cocotb (`uv sync --group rtl`).
