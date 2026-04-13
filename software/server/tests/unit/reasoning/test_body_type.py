from auralink.reasoning.body_type import BodyTypeProfile, Sex


def test_default_profile():
    profile = BodyTypeProfile()
    assert profile.sex == Sex.UNSPECIFIED
    assert profile.hypermobile is False
    assert profile.age_range == "adult"
