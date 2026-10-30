"""Error metrics used to accept or reject a ported kernel against its Python reference."""

import numpy as np
from numpy.typing import ArrayLike


def _pair(reference: ArrayLike, test: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    ref = np.asarray(reference, dtype=np.float64)
    out = np.asarray(test, dtype=np.float64)
    if ref.shape != out.shape:
        raise ValueError(f"shape mismatch: reference {ref.shape} vs test {out.shape}")
    return ref, out


def max_abs_error(reference: ArrayLike, test: ArrayLike) -> float:
    """Largest absolute difference between the reference and the test output."""
    ref, out = _pair(reference, test)
    return float(np.max(np.abs(ref - out))) if ref.size else 0.0


def snr_db(reference: ArrayLike, test: ArrayLike) -> float:
    """Signal-to-error ratio in dB, treating ``test - reference`` as noise.

    Returns ``inf`` when the outputs are identical.
    """
    ref, out = _pair(reference, test)
    noise = float(np.sum((out - ref) ** 2))
    if noise == 0.0:
        return float("inf")
    return float(10.0 * np.log10(float(np.sum(ref**2)) / noise))
