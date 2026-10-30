"""Recordings listed in ``examples/datasets.toml``, downloaded to ``data/`` with SHA-256 checks."""

import hashlib
import shutil
import tomllib
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Dataset:
    name: str
    url: str
    sha256: str
    filename: str
    license: str
    note: str = ""


def load_datasets(path: Path) -> list[Dataset]:
    """Read the ``[[dataset]]`` entries of a datasets manifest."""
    with path.open("rb") as f:
        doc = tomllib.load(f)
    return [Dataset(**entry) for entry in doc.get("dataset", [])]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_dataset(ds: Dataset, dest_root: Path) -> Path:
    """Download ``ds`` into ``dest_root/<name>/<filename>`` unless a verified copy exists."""
    dest = dest_root / ds.name / ds.filename
    if dest.exists() and sha256_of(dest) == ds.sha256:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(ds.url) as resp, tmp.open("wb") as out:
        shutil.copyfileobj(resp, out)
    digest = sha256_of(tmp)
    if digest != ds.sha256:
        tmp.unlink()
        raise ValueError(f"{ds.name}: checksum mismatch (expected {ds.sha256}, got {digest})")
    tmp.replace(dest)
    return dest
