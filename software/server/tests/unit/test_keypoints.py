from bioliminal.pose.keypoints import (
    BLAZEPOSE_LANDMARK_COUNT,
    LandmarkIndex,
    landmark_index,
)


def test_landmark_count():
    assert BLAZEPOSE_LANDMARK_COUNT == 33


def test_known_indices():
    assert LandmarkIndex.NOSE == 0
    assert LandmarkIndex.LEFT_HIP == 23
    assert LandmarkIndex.RIGHT_HIP == 24
    assert LandmarkIndex.LEFT_KNEE == 25
    assert LandmarkIndex.RIGHT_KNEE == 26
    assert LandmarkIndex.LEFT_ANKLE == 27
    assert LandmarkIndex.RIGHT_ANKLE == 28


def test_landmark_index_lookup_by_name():
    assert landmark_index("left_hip") == 23
    assert landmark_index("right_knee") == 26
