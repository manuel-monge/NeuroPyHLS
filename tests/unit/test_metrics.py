import math

import numpy as np
import pytest

from neuropyhls.verify import max_abs_error, snr_db


def test_identical_outputs() -> None:
    x = np.sin(np.linspace(0, 10, 1000))
    assert max_abs_error(x, x) == 0.0
    assert snr_db(x, x) == math.inf


def test_known_snr() -> None:
    ref = np.ones(100)
    out = ref + 0.1  # noise power 0.01 per sample -> 20 dB
    assert snr_db(ref, out) == pytest.approx(20.0)
    assert max_abs_error(ref, out) == pytest.approx(0.1)


def test_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="shape mismatch"):
        snr_db(np.zeros(3), np.zeros(4))
