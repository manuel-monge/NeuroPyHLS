"""Direct backend: lower the IR straight to Verilog, with no C++ step (the project's main goal).

Planned stages: scheduling (assign operations to clock cycles), binding (share functional units
and registers), control generation (FSM), and Verilog emission of the datapath and controller.
"""
