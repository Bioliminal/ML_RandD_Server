from typing import Protocol

from auralink.pipeline.artifacts import PerRepMetrics
from auralink.reasoning.body_type import BodyTypeProfile
from auralink.reasoning.config_schemas import (
    BodyTypeAdjustmentsConfig,
    RuleConfig,
    ThresholdSetConfig,
)
from auralink.reasoning.observations import ChainObservation, ObservationSeverity
from auralink.reasoning.threshold_loader import adjust_for_body_type


class ChainReasoner(Protocol):
    def reason(
        self,
        per_rep_metrics: PerRepMetrics | None,
        movement: str,
        body_type: BodyTypeProfile | None = None,
    ) -> list[ChainObservation]: ...


def _aggregate(values: list[float], aggregation: str) -> float:
    if not values:
        return 0.0
    if aggregation == "max":
        return max(values)
    if aggregation == "min":
        return min(values)
    if aggregation == "mean":
        return sum(values) / len(values)
    raise ValueError(f"unknown aggregation: {aggregation}")


def _extract_metric(metrics: PerRepMetrics, metric_key: str) -> list[float]:
    return [getattr(rep, metric_key) for rep in metrics.reps]


class RuleBasedChainReasoner:
    def __init__(
        self,
        rules: list[RuleConfig],
        base_thresholds: ThresholdSetConfig,
        adjustments: BodyTypeAdjustmentsConfig,
    ) -> None:
        self._rules = rules
        self._base = base_thresholds
        self._adjustments = adjustments

    def reason(
        self,
        per_rep_metrics: PerRepMetrics | None,
        movement: str,
        body_type: BodyTypeProfile | None = None,
    ) -> list[ChainObservation]:
        if per_rep_metrics is None:
            return []
        thresholds = self._base
        if body_type is not None:
            thresholds = adjust_for_body_type(self._base, body_type, self._adjustments)
        threshold_dict = thresholds.model_dump()
        observations: list[ChainObservation] = []
        for rule in self._rules:
            if movement not in rule.applies_to_movements:
                continue
            values = _extract_metric(per_rep_metrics, rule.metric_key)
            if not values:
                continue
            aggregated = _aggregate(values, rule.aggregation)
            concern = threshold_dict.get(rule.threshold_concern_ref)
            flag = threshold_dict.get(rule.threshold_flag_ref)
            if concern is None or flag is None:
                continue
            severity: ObservationSeverity | None = None
            if aggregated >= flag:
                severity = ObservationSeverity.FLAG
            elif aggregated >= concern:
                severity = ObservationSeverity.CONCERN
            if severity is None:
                continue
            narrative = rule.narrative_template.format(value=aggregated)
            observations.append(
                ChainObservation(
                    chain=rule.chain,
                    severity=severity,
                    confidence=rule.confidence,
                    trigger_rule=rule.rule_id,
                    involved_joints=rule.involved_joints,
                    evidence={rule.metric_key: aggregated},
                    narrative=narrative,
                )
            )
        return observations
