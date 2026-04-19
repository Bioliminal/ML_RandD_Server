"""Fascial chain definitions — SBL, BFL, FFL.

Per the research integration report section 2.5, chains are modeled as
graph paths over the skeleton. Only the three chains with strong
anatomical evidence (Wilke 2016, Kalichman 2025) are included.
"""

from dataclasses import dataclass
from enum import StrEnum


class ChainName(StrEnum):
    SBL = "superficial_back_line"
    BFL = "back_functional_line"
    FFL = "front_functional_line"
    UPPER_LIMB_LOCAL = "upper_limb_local"


@dataclass(frozen=True)
class ChainDefinition:
    name: ChainName
    description: str
    anatomical_path: list[str]


CHAIN_DEFINITIONS: dict[ChainName, ChainDefinition] = {
    ChainName.SBL: ChainDefinition(
        name=ChainName.SBL,
        description="Plantar fascia through calves, hamstrings, erector spinae, to skull base.",
        anatomical_path=[
            "plantar_fascia",
            "gastrocnemius",
            "hamstrings",
            "sacrotuberous_ligament",
            "erector_spinae",
            "epicranial_fascia",
        ],
    ),
    ChainName.BFL: ChainDefinition(
        name=ChainName.BFL,
        description=(
            "Latissimus dorsi through thoracolumbar fascia to contralateral gluteus maximus."
        ),
        anatomical_path=[
            "latissimus_dorsi",
            "thoracolumbar_fascia",
            "contralateral_gluteus_maximus",
            "vastus_lateralis",
        ],
    ),
    ChainName.FFL: ChainDefinition(
        name=ChainName.FFL,
        description="Pectoralis major through rectus abdominis to contralateral adductors.",
        anatomical_path=[
            "pectoralis_major",
            "rectus_abdominis",
            "contralateral_adductor_longus",
        ],
    ),
}
