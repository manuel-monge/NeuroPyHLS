# Getting started

## Install

You need [uv](https://docs.astral.sh/uv/) and Git.

```bash
git clone https://github.com/openic-org/NeuroPyHLS.git
cd NeuroPyHLS
uv sync
uv run neuropyhls --help
```

For the hardware steps, also install [Bambu](https://panda.dei.polimi.it/) and [Verilator](https://www.veripool.org/verilator/), and put both on your `PATH`. Vitis HLS is optional.

## Reference code and recordings

```bash
uv run neuropyhls fetch-sources   # clone pinned reference repos (examples/sources.toml) into external/
uv run neuropyhls fetch           # download recordings (examples/datasets.toml) into data/, checking SHA-256
```

## Run the tests

```bash
uv run pytest -m unit    # fast, no external tools
uv run pytest -m bambu   # needs Bambu and Verilator
```
