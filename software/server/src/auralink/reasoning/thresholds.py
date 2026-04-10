"""Joint angle thresholds for chain reasoning.

v1 uses a single default population. Body-type adjustment (hypermobile,
female, youth) arrives in a follow-on plan that fills in the conditional
table. See research-integration-report.md section 5.4.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThresholdSet:
    knee_valgus_concern: float  # degrees
    knee_valgus_flag: float
    hip_drop_concern: float
    hip_drop_flag: float


# Placeholder values — calibrate from research before shipping.
# Sources: Hewett 2005 (10 degree valgus = 2.5x ACL risk)
DEFAULT_THRESHOLDS = ThresholdSet(
    knee_valgus_concern=8.0,
    knee_valgus_flag=12.0,
    hip_drop_concern=5.0,
    hip_drop_flag=10.0,
)
