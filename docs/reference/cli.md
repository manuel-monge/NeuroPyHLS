# CLI reference

```text
neuropyhls [--version] <command> ...

  analyse KERNEL         inspect a Python kernel: structure, operations, libraries
  profile KERNEL         measure value ranges and operation counts on recordings
  port KERNEL [--flow F] compile the kernel to Verilog; F = direct (default), bambu, vitis
  verify KERNEL [--flow F] check a flow's outputs against the Python reference
  compare KERNEL         compare the direct flow against the baseline flows
  fetch-sources [NAME…]  clone pinned external repositories      (--manifest, --dest)
  fetch [NAME…]          download recordings and check SHA-256    (--manifest, --dest)
```

`--flow direct` is the Python → Verilog compiler the project is building. `bambu` and `vitis` are the baseline flow through HLS C++.

`analyse`, `profile`, `port`, `verify` and `compare` are not implemented yet; they exit with code 2.
