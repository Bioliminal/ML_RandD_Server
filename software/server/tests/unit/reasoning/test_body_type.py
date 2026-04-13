from auralink.reasoning.body_type import BodyTypeProfile, Sex


def test_default_profile():
    profile = BodyTypeProfile()
    assert profile.sex == Sex.UNSPECIFIED
    assert profile.hypermobile is False
    assert profile.age_range == "adult"


def test_hypermobile_profile():
    profile = BodyTypeProfile(sex=Sex.FEMALE, hypermobile=True, age_range="youth")
    assert profile.sex == Sex.FEMALE
    assert profile.hypermobile is True
    assert profile.age_range == "youth"
