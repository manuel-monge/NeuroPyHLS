"""NeuroPyHLS: high-level synthesis of neural-signal algorithms directly from Python to Verilog."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("neuropyhls")
except PackageNotFoundError:  # running from a source tree without installation
    __version__ = "0.0.0"

__all__ = ["__version__"]
