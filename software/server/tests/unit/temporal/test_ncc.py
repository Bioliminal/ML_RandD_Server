import math

import numpy as np
import pytest

from bioliminal.temporal.ncc import ncc


def test_identical_signals_score_one():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert ncc(x, x) == pytest.approx(1.0, abs=1e-12)


def test_inverse_signal_scores_negative_one():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = -x
    assert ncc(x, y) == pytest.approx(-1.0, abs=1e-12)


def test_zero_variance_signal_returns_nan():
    x = np.array([3.0, 3.0, 3.0, 3.0])
    y = np.array([1.0, 2.0, 3.0, 4.0])
    result = ncc(x, y)
    assert math.isnan(result)


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        ncc(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0]))
