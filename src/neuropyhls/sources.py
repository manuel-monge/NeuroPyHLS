"""Pinned external source repositories (``examples/sources.toml``), cloned into ``external/``."""

import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    commit: str
    license: str
    note: str = ""


def load_sources(path: Path) -> list[Source]:
    """Read the ``[[source]]`` entries of a sources manifest."""
    with path.open("rb") as f:
        doc = tomllib.load(f)
    return [Source(**entry) for entry in doc.get("source", [])]


def fetch_source(src: Source, dest_root: Path) -> Path:
    """Clone ``src`` into ``dest_root/<name>`` (if needed) and check out its pinned commit."""
    dest = dest_root / src.name
    if not (dest / ".git").exists():
        dest_root.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--filter=blob:none", src.url, str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "fetch", "--quiet", "origin", src.commit], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "--quiet", src.commit], check=True)
    return dest
