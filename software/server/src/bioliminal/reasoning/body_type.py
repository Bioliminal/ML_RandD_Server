from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNSPECIFIED = "unspecified"


class BodyTypeProfile(BaseModel):
    sex: Sex = Sex.UNSPECIFIED
    hypermobile: bool = False
    age_range: Literal["youth", "adult", "senior"] = "adult"
