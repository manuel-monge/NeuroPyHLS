# CLI reference

```text
neuropyhls [--version] <command> ...

  analyse KERNEL         inspect a Python kernel: structure, operations, libraries
  profile KERNEL         measure value ranges and operation counts on recordings
  port KERNEL            lower the kernel to HLS C++ for a backend (bambu, vitis)
  verify KERNEL          compare Python, C simulation, and RTL simulation outputs
  fetch-sources [NAME…]  clone pinned external repositories      (--manifest, --dest)
  fetch [NAME…]          download recordings and check SHA-256    (--manifest, --dest)
```

`analyse`, `profile`, `port` and `verify` are not implemented yet; they exit with code 2.
