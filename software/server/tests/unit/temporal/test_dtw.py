import pytest

from bioliminal.temporal.dtw import DTWResult, run_dtw


def test_identical_sequences_have_zero_distance_and_diagonal_path():
    seq = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = run_dtw(seq, seq)
    assert isinstance(result, DTWResult)
    assert result.distance == pytest.approx(0.0, abs=1e-9)
    # identical signals align on the main diagonal. Use set equality rather
    # than list equality so the assertion survives dtaidistance version bumps
    # that may reorder the path list (e.g., start→end vs end→start).
    assert set(result.path) == {(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)}
    # extra sanity: every (i, j) step should satisfy i == j for identical seqs
    assert all(i == j for i, j in result.path)


def test_shifted_signal_has_nondiagonal_path():
    a = [0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0]
    b = [0.0, 0.0, 1.0, 2.0, 3.0, 2.0, 1.0]  # same shape, shifted by one
    result = run_dtw(a, b)
    assert result.distance >= 0.0
    # at least one path step deviates from the main diagonal
    assert any(i != j for i, j in result.path)


def test_window_is_populated_from_sequence_length():
    a = [0.0] * 40
    b = [0.0] * 30
    result = run_dtw(a, b, radius_fraction=0.1)
    # max length is 40, 10% = 4
    assert result.window == 4


def test_different_length_sequences_align():
    a = [0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0]
    b = [0.0, 2.0, 3.0, 2.0, 0.0]  # shorter but similar arc
    result = run_dtw(a, b)
    assert result.distance >= 0.0
    # path must terminate at (last_a, last_b)
    assert result.path[-1] == (len(a) - 1, len(b) - 1)
