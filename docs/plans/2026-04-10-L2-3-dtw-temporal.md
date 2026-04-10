# L2 Plan 3 — DTW + Temporal Analysis (Stub)

**Status:** Stub — flesh out with `writing-plans` before execution.
**Parent:** `2026-04-10-analysis-pipeline-epoch.md`
**Depends on:** Plan 1 (pipeline framework), Plan 2 (report schema), Plan 4 (synthetic fixtures + reference rep library)

## Goal

Add the research-backed per-rep and cross-movement temporal analysis from Scientific Reports 2025 (DOI: 10.1038/s41598-025-29062-7). Align each rep against a reference rep via Dynamic Time Warping, compute Normalized Cross-Correlation for similarity scoring, detect within-movement trends (fatigue, compensation drift), and aggregate across the 4-movement protocol to surface cross-movement patterns (fatigue carryover, emergent compensations).

Adds a `POST /protocols` endpoint for multi-session aggregation and extends the `Report` with temporal and cross-movement sections.

## File Tree Delta

```
software/server/src/auralink/
├── temporal/
│   ├── __init__.py            # NEW
│   ├── dtw.py                 # NEW — DTW alignment over 1D angle series
│   ├── ncc.py                 # NEW — Normalized Cross-Correlation
│   ├── reference_reps.py      # NEW — reference rep library + loader
│   ├── comparison.py          # NEW — per-rep comparison (rep vs reference)
│   └── trend.py               # NEW — within-movement + cross-movement trend detection
├── pipeline/stages/
│   ├── rep_comparison.py      # NEW — DTW + NCC stage (per movement)
│   └── cross_movement_trend.py  # NEW — cross-movement aggregation stage
├── protocol/
│   ├── __init__.py            # NEW
│   ├── schemas.py             # NEW — Protocol pydantic (4-movement session bundle)
│   └── aggregator.py          # NEW — combines multiple session reports into a protocol report
├── api/routes/protocols.py    # NEW — POST /protocols
└── report/schemas.py          # MODIFIED — add temporal + cross-movement sections

software/server/config/reference_reps/
├── overhead_squat.json        # NEW — synthetic reference rep
├── single_leg_squat.json      # NEW
└── push_up.json               # NEW

tests/
├── unit/temporal/             # NEW — DTW, NCC, trend tests
├── unit/protocol/             # NEW — aggregator tests
└── integration/test_protocol_endpoint.py  # NEW — 4 sessions → protocol report
```

## Schemas (rough)

- **`ReferenceRep`** — reference angle series for a single rep, per movement type
- **`RepComparison`** — per-rep DTW alignment path, NCC score, deviation signals
- **`MovementTemporalSummary`** — within-movement trend metrics (ROM drift, velocity drift, compensation growth)
- **`ProtocolReport`** — aggregates per-movement reports + cross-movement metrics (fatigue carryover, emergent compensations)
- **`CrossMovementMetric`** — change in a signal from movement N to movement M

## Task List

1. DTW implementation (wrapping `tslearn.metrics.dtw` or `fastdtw`; pick during library check)
2. NCC implementation (numpy-native, no external dep)
3. `ReferenceRep` schema + loader (JSON config files)
4. Synthetic reference reps for overhead_squat, single_leg_squat, push_up
5. Per-rep comparison module (`rep vs reference → RepComparison`)
6. Rep comparison stage (wraps per-rep comparison, consumes Plan 1 artifacts)
7. Within-movement trend module (monotonic change detection over rep comparisons)
8. Cross-movement aggregator (combines per-movement trends into protocol-level signals)
9. Cross-movement trend stage
10. `Protocol` + `ProtocolReport` pydantic schemas
11. Protocol aggregator (combines session reports; invoked by protocol endpoint)
12. `POST /protocols` endpoint (accepts a list of session IDs, runs aggregation, returns `ProtocolReport`)
13. Extend `Report` schema with temporal + cross-movement sections
14. Update Plan 2's report assembler to include temporal outputs
15. Integration test: 4 synthetic fixtures → `POST /protocols` → protocol report with cross-movement fatigue signal
16. Final validation

## Dependencies

- Plan 1 completed (angle time-series + per-rep metrics artifacts available)
- Plan 2 completed (`Report` model exists + rule-based reasoning runs)
- One external library: either `tslearn` or `fastdtw` (TBD during library check; lean `fastdtw` for smaller footprint)

## Exit Criteria

- ~15-20 new tests.
- DTW alignment on synthetic reps produces expected similarity scores (NCC > 0.95 for identical reps, NCC < 0.7 for a rep with 30% ROM reduction).
- Within-movement trend detects a fatigue signal in a 5-rep fixture where each rep progressively loses 10% ROM.
- Cross-movement aggregation detects fatigue carryover in a 4-session fixture where the last session has reduced ROM vs the first.
- `POST /protocols` endpoint returns a valid `ProtocolReport`.
- Reference rep loader accepts JSON from `config/reference_reps/`.
- All previous tests still pass.

## Deferred to L3

- DTW library choice (`tslearn` vs `fastdtw` vs `dtw-python`) — decide during library check.
- Exact NCC similarity thresholds for trend detection — tune during implementation.
- Reference rep format (single canonical rep vs distribution with variance bounds) — decide during implementation.
- Whether protocol report narrative is templated like Plan 2 or generated differently.

## Notes for writing-plans

- This is the only plan in the epoch that adds a runtime dependency. Justify the choice in the plan doc and confirm via `context7` during library check.
- DTW has multiple API conventions (cost matrix vs warp path vs distance-only). Pick one and document.
- Synthetic reference reps must be realistic enough that real reps would actually compare well. Generate them from the same synthetic fixture generator as Plan 4 — don't invent separate hand-tuned shapes.
- The protocol endpoint is a new API surface. Consider rate limiting / auth hooks but defer implementation to Plan 5 or a follow-on.
