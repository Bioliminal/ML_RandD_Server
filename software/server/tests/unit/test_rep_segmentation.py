import numpy as np

from auralink.analysis.rep_segmentation import segment_reps


def test_segment_reps_single_rep():
    descent = np.linspace(180, 90, 15)
    ascent = np.linspace(90, 180, 15)
    angles = np.concatenate([descent, ascent])
    boundaries = segment_reps(angles.tolist(), min_amplitude=30.0)
    assert len(boundaries) == 1
    rep = boundaries[0]
    assert rep.start_index == 0
    assert rep.end_index == 29
    assert rep.bottom_index == 14


def test_segment_reps_multiple_reps():
    rep_angles = np.concatenate(
        [
            np.linspace(180, 90, 10),
            np.linspace(90, 180, 10),
        ]
    )
    angles = np.tile(rep_angles, 3)
    boundaries = segment_reps(angles.tolist(), min_amplitude=30.0)
    assert len(boundaries) == 3


def test_segment_reps_ignores_noise():
    angles = [180.0 + 2.0 * np.sin(i * 0.5) for i in range(50)]
    boundaries = segment_reps(angles, min_amplitude=30.0)
    assert len(boundaries) == 0


def test_rep_boundary_indices_are_valid():
    descent = np.linspace(180, 90, 15)
    ascent = np.linspace(90, 180, 15)
    angles = np.concatenate([descent, ascent])
    boundaries = segment_reps(angles.tolist(), min_amplitude=30.0)
    for rep in boundaries:
        assert rep.start_index < rep.bottom_index < rep.end_index
