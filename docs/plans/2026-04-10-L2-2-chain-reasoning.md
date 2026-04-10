# L2 Plan 2 — Chain Reasoning v1 + Report Assembly (Stub)

**Status:** Stub — flesh out with `writing-plans` before execution.
**Parent:** `2026-04-10-analysis-pipeline-epoch.md`
**Depends on:** Plan 1 (Pipeline Framework + Core Analysis Stages), Plan 4 (synthetic fixture generator for TDD test data)

## Goal

Turn the raw pipeline artifact bundle from Plan 1 into a human-readable structured report. Implement the first-version rule-based chain reasoner operating over `PerRepMetrics` + `WithinMovementTrend`, applying the threshold table to SBL, BFL, and FFL chains. Emit `ChainObservation` per flagged pattern. Assemble the final `Report` pydantic model and serve it via `GET /sessions/{id}/report` (replacing Plan 1's raw artifact response).

This plan delivers the free-tier product value end-to-end: capture a session, receive a chain-reasoned report.

## File Tree Delta

```
software/server/src/auralink/
├── reasoning/
│   ├── engine.py              # NEW — ChainReasoner protocol + base
│   ├── rule_engine.py         # NEW — RuleBasedChainReasoner (v1)
│   ├── observations.py        # NEW — ChainObservation pydantic schema
│   ├── body_type.py           # NEW — questionnaire intake + adjustment lookup
│   └── rules/
│       ├── __init__.py        # NEW
│       ├── sbl.py             # NEW — Superficial Back Line rules
│       ├── bfl.py             # NEW — Back Functional Line rules
│       └── ffl.py             # NEW — Front Functional Line rules
├── report/
│   ├── __init__.py            # NEW
│   ├── schemas.py             # NEW — Report pydantic model
│   └── assembler.py           # NEW — Report assembler stage
├── pipeline/stages/
│   ├── chain_reasoning.py     # NEW — wraps ChainReasoner as a Stage
│   └── report_assembly.py     # NEW — wraps report.assembler as a Stage
└── api/routes/reports.py      # MODIFIED — returns Report not raw artifacts

software/server/config/
├── thresholds/
│   ├── default.yaml           # NEW — Hewett 2005 baseline table
│   └── body_type_adjustments.yaml  # NEW — population lookup (placeholder)
└── rules/
    ├── sbl.yaml               # NEW — SBL rule definitions
    ├── bfl.yaml               # NEW — BFL rule definitions
    └── ffl.yaml               # NEW — FFL rule definitions

tests/
├── unit/reasoning/            # NEW — rule set unit tests
├── unit/report/               # NEW — assembler tests
└── integration/test_full_report.py  # NEW — fixture → full report with ChainObservations
```

## Schemas (rough)

- **`ChainObservation`** — `chain: ChainName`, `severity: Literal["info", "concern", "flag"]`, `confidence: float`, `trigger_rule: str`, `involved_joints: list[str]`, `evidence: dict[str, float]`, `narrative: str`
- **`BodyTypeProfile`** — intake questionnaire fields (sex, hypermobility flag, age range, etc.)
- **`Report`** — session metadata + quality report + per-movement sections (metrics + trend + chain observations) + top-level narrative
- **Rule config (YAML)** — structured declarative rules: `threshold`, `applies_to_movement`, `metric_key`, `chain`, `severity_mapping`

## Task List

1. `ChainObservation` schema
2. `BodyTypeProfile` schema + questionnaire intake
3. Threshold config loader (YAML → pydantic `ThresholdSet`)
4. Rule config loader (YAML → runtime rule objects)
5. `ChainReasoner` protocol
6. `RuleBasedChainReasoner` base implementation (rule evaluation engine)
7. SBL rule set (YAML + code binding: knee valgus, hamstring tightness proxies)
8. BFL rule set (lat / glute coupling signals)
9. FFL rule set (pec / adductor coupling signals)
10. Body-type adjustment lookup (modifies thresholds based on profile)
11. Chain reasoning stage (wraps `RuleBasedChainReasoner`)
12. `Report` pydantic model **with named extension slots**: `temporal_section: TemporalSection | None = None` and `cross_movement_section: CrossMovementSection | None = None`. Stub `TemporalSection` and `CrossMovementSection` as empty pydantic models in `report/schemas.py` (placeholder shapes). Plan 3 swaps in real schemas for these stubs — Plan 3 **populates** these slots and does **not** restructure the `Report`. This decouples Plan 2 and Plan 3 ownership of the report schema.
13. Report assembler module
14. Report assembly stage
15. Wire both new stages into the orchestrator (after Plan 1's stages)
16. Update `GET /sessions/{id}/report` to return the `Report` model
17. Integration test: overhead_squat fixture with injected valgus → Report contains SBL `ChainObservation` flagging knee valgus
18. Final validation

## Dependencies

- Plan 1 must be complete (orchestrator, per-rep metrics, within-movement trend artifacts all exist).
- Default thresholds come from Hewett 2005 — already placeholder values in `reasoning.thresholds.DEFAULT_THRESHOLDS`, to be moved into YAML config.

## Exit Criteria

- ~20 new tests.
- Synthetic overhead_squat fixture with a 12° knee valgus angle produces a `ChainObservation` for SBL with severity ≥ `concern`.
- A fixture with zero compensation produces zero observations but still returns a valid `Report`.
- Report language matches the Capstone CLAUDE.md wellness-positioning rules (no forbidden terms).
- Threshold + rule configs are loaded from YAML at startup; changing a threshold does not require code changes.
- Body-type profile optionally passed with the session; if present, the threshold table adjusts accordingly.

## Deferred to L3

- Exact severity thresholds (info vs concern vs flag) — pick pragmatic defaults during implementation.
- Rule format details (YAML schema shape) — iterate during implementation.
- Whether `BodyTypeProfile` arrives in the session metadata or as a separate endpoint (leaning metadata to keep the API surface small).

## Notes for writing-plans

- This plan introduces YAML as a new file format. Verify pydantic-yaml (`pyyaml` is already transitive — confirm during library check).
- Rule evaluation should be fully deterministic and independently testable per rule. Avoid rule-engine framework overhead — plain Python conditionals in a loop is the right level of simplicity for v1.
- The `ChainReasoner` protocol must accept the artifact bundle from Plan 1 — define the exact input shape during `writing-plans` after Plan 1 execution settles the artifact schemas.
- Narrative text generation is stage-scope, not LLM — template strings per rule. LLM narrative comes in a separate plan if ever.
