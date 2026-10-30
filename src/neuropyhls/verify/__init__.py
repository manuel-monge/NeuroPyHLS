"""Verification: compare Python, C simulation, and RTL simulation outputs on golden vectors."""

from neuropyhls.verify.metrics import max_abs_error, snr_db

__all__ = ["max_abs_error", "snr_db"]
