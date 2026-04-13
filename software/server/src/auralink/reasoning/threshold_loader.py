from pathlib import Path

import yaml

from auralink.reasoning.body_type import BodyTypeProfile
from auralink.reasoning.config_schemas import (
    BodyTypeAdjustmentsConfig,
    ThresholdSetConfig,
)

_DEFAULT_PATH = Path(__file__).resolve().parents[3] / "config" / "thresholds" / "default.yaml"
_ADJUSTMENTS_PATH = Path(__file__).resolve().parents[3] / "config" / "thresholds" / "body_type_adjustments.yaml"


def load_default_thresholds(path: Path | None = None) -> ThresholdSetConfig:
    p = path or _DEFAULT_PATH
    raw = yaml.safe_load(p.read_text())
    return ThresholdSetConfig.model_validate(raw)


def load_body_type_adjustments(path: Path | None = None) -> BodyTypeAdjustmentsConfig:
    p = path or _ADJUSTMENTS_PATH
    raw = yaml.safe_load(p.read_text())
    return BodyTypeAdjustmentsConfig.model_validate(raw)


def adjust_for_body_type(
    base: ThresholdSetConfig,
    profile: BodyTypeProfile,
    adjustments: BodyTypeAdjustmentsConfig,
) -> ThresholdSetConfig:
    merged = base.model_dump()
    for adj in adjustments.adjustments:
        if adj.applies_to_sex and profile.sex.value not in adj.applies_to_sex:
            continue
        if adj.applies_to_hypermobile is not None and adj.applies_to_hypermobile != profile.hypermobile:
            continue
        if adj.applies_to_age_range and profile.age_range not in adj.applies_to_age_range:
            continue
        merged.update(adj.threshold_overrides)
    return ThresholdSetConfig.model_validate(merged)
