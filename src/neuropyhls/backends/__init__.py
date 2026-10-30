"""Backends that turn the IR into Verilog.

- ``direct``: IR -> Verilog, with no C++ step. This is the compiler NeuroPyHLS is building.
- ``bambu``, ``vitis``: the baseline flow, IR -> HLS C++ -> external HLS tool -> Verilog. It is
  used to test the direct backend and compare against it.
"""

FLOWS = ("direct", "bambu", "vitis")
"""Values accepted by ``neuropyhls port --flow``. ``direct`` is the default."""
