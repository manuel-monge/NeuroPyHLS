# Notebooks

Notebooks are stored as Jupytext **percent-format `.py` files**, in which `# %%` marks a cell. This keeps diffs readable and avoids committing outputs. The `.ipynb` copies are git-ignored.

```bash
uv run jupytext --sync notebooks/*.py   # create or update the paired .ipynb files
```

Open the `.ipynb` in Jupyter or VS Code. On save, Jupytext keeps the `.py` file in sync (configured in `jupytext.toml`). VS Code can also run the `.py` file directly, cell by cell.
