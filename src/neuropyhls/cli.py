"""Command-line interface: ``neuropyhls <command>``."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from neuropyhls import __version__
from neuropyhls.datasets import fetch_dataset, load_datasets
from neuropyhls.sources import fetch_source, load_sources

PIPELINE = {
    "analyse": "inspect a Python kernel: structure, operations, libraries",
    "profile": "measure value ranges and operation counts on recordings",
    "port": "lower the kernel to HLS C++ for a backend (bambu, vitis)",
    "verify": "compare Python, C simulation, and RTL simulation outputs",
}


def _not_implemented(args: argparse.Namespace) -> int:
    print(f"neuropyhls {args.command}: not implemented yet", file=sys.stderr)
    return 2


def _fetch_sources(args: argparse.Namespace) -> int:
    wanted = set(args.names)
    for src in load_sources(args.manifest):
        if not wanted or src.name in wanted:
            print(f"{src.name} @ {src.commit[:7]} -> {fetch_source(src, args.dest)}")
    return 0


def _fetch(args: argparse.Namespace) -> int:
    wanted = set(args.names)
    for ds in load_datasets(args.manifest):
        if not wanted or ds.name in wanted:
            print(f"{ds.name} -> {fetch_dataset(ds, args.dest)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="neuropyhls", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in PIPELINE.items():
        p = sub.add_parser(name, help=help_text)
        p.add_argument("kernel", type=Path, help="Python file containing the kernel")
        p.set_defaults(func=_not_implemented)

    p = sub.add_parser("fetch-sources", help="clone pinned external repositories")
    p.add_argument("names", nargs="*", help="sources to fetch (default: all)")
    p.add_argument("--manifest", type=Path, default=Path("examples/sources.toml"))
    p.add_argument("--dest", type=Path, default=Path("external"))
    p.set_defaults(func=_fetch_sources)

    p = sub.add_parser("fetch", help="download recordings and check their SHA-256")
    p.add_argument("names", nargs="*", help="datasets to fetch (default: all)")
    p.add_argument("--manifest", type=Path, default=Path("examples/datasets.toml"))
    p.add_argument("--dest", type=Path, default=Path("data"))
    p.set_defaults(func=_fetch)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
