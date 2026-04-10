# AuraLink Server — Analysis Pipeline Epoch (L1)

**Status:** Planning
**Created:** 2026-04-10
**Parent:** docs/research-integration-report.md (architectural context)
**Predecessor:** docs/plans/2026-04-09-server-scaffold.md (completed)

## Epoch Goal

Take the committed scaffold (session ingest → joint angles → rep segmentation primitives) and build it into a working end-to-end analysis pipeline. By epoch completion, a captured session POSTed to `/sessions` produces a structured report via `GET /sessions/{id}/report`, containing:

- Rule-based chain reasoning over SBL, BFL, FFL
- Per-rep temporal metrics (ROM, velocity profile, compensation angles) per the Scientific Reports 2025 methodology
- Within-movement and cross-movement trend analysis
- Quality gate decisions for invalid sessions
- Integration hooks for MotionBERT, HSMR, and GCN chain reasoning behind already-defined interfaces

The key design property: when ML models are ready, landing them is a config swap, not a rewrite.

## Success Criteria

- A captured overhead-squat session (MLKit JSON shape per `api.schemas.Session`) produces a full structured report via two API calls (`POST /sessions`, `GET /sessions/{id}/report`), no manual wiring.
- Rule-based chain reasoning flags knee valgus, hip drop, and trunk lean per the default threshold table (Hewett 2005 baseline); threshold values live in config, not code.
- Per-rep metrics and within-movement trends match the Scientific Reports 2025 pipeline structure (angle time-series → DTW alignment → NCC similarity → trend metrics).
- A 4-movement protocol aggregates into cross-movement metrics (fatigue carryover, emergent compensations).
- ML integration stages (`Lifter`, `SkeletonFitter`, GCN `ChainReasoner`) exist as no-op identity functions behind protocols — landing real models later swaps the implementation only.
- Quality gates reject sessions with bad frame rate, insufficient visibility, short duration, or missing landmarks — with structured error responses.
- Synthetic fixtures cover all four movement types end-to-end; loader is ready to consume Flutter golden captures as they arrive.
- Structured logs with correlation IDs + per-stage timing + pipeline run status tracking.

## Constraints

- **No real ML model integration in this epoch.** MotionBERT, HSMR, GCN all land in a follow-on epoch once model checkpoints, PyTorch dependencies, and compute-budget decisions are settled. Interfaces ship, implementations stay no-op.
- **Wellness positioning** — report language follows Capstone CLAUDE.md rules (no "diagnosis", "dysfunction", "drivers of pain"; use "movement patterns", "body connections").
- **Chain scope: SBL, BFL, FFL only.** Spiral, Lateral, and SFL chains excluded per the research integration report §6.2.
- **Rollup movement is interface-only.** The `PhaseSegmenter` protocol plugs in, but the real phase-segmentation implementation is deferred (research gap §7.3).
- **Stack:** Python 3.11+, FastAPI, pydantic v2, numpy, pytest, ruff, black, uv — the scaffold stack. No new runtime dependencies unless explicitly justified in the L2 plan.
- **TDD throughout.** Every L2 plan executes via `parallel-plan-executor` (sequential-in-main-tree) with `task-executor` per task.
- **Every L2 plan gets `plan-review` before execution.**
- **Thresholds, rules, reference reps live in config files**, not code. Tuning without redeployment is a baked-in property.

## Modularity Principles

Every L2 plan in this epoch must honor the following (violations are grounds for rejection in plan-review):

1. **Stages are pure functions.** `(ArtifactIn) -> ArtifactOut`. No direct stage-to-stage coupling — composition is the orchestrator's job.
2. **Protocols before implementations.** `Stage`, `ChainReasoner`, `Lifter`, `SkeletonFitter`, `PhaseSegmenter`, `ModelLoader` — all defined as `typing.Protocol` types with at least one concrete impl and one trivial impl (no-op or identity) for testing.
3. **Artifacts are pydantic models.** Every stage boundary is serializable, validated, and independently testable.
4. **Movement-type dispatch via strategy pattern.** The orchestrator picks stages based on `MovementType`; adding a new movement registers its stage list without touching existing code.
5. **Config-driven behavior.** Thresholds, rules, reference reps, pipeline compositions — all loaded from YAML/JSON at startup, never hard-coded.
6. **Single responsibility per module.** A stage module contains one stage plus its tests. A reasoning rule set lives in one file. No god-modules.
7. **No circular imports.** Pipeline depends on artifacts and stages; stages depend on schemas and utilities; nothing depends back on pipeline.
8. **Boundary validation.** Quality gates at the session ingest boundary; pydantic validation at every stage boundary. Internal code trusts its inputs.

## Composition — L2 Plans

This epoch is composed of 5 L2 plans. Default execution order is 1 → 2 → 3 → 4 → 5. Plans 2, 3, 4, 5 all depend only on Plan 1 and can be reshuffled based on team priorities.

| # | Plan | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Pipeline Framework + Core Analysis Stages | `2026-04-10-L2-1-pipeline-framework.md` | Scaffold | Stub |
| 2 | Chain Reasoning v1 + Report Assembly | `2026-04-10-L2-2-chain-reasoning.md` | Plan 1 | Stub |
| 3 | DTW + Temporal Analysis | `2026-04-10-L2-3-dtw-temporal.md` | Plan 1, Plan 2 | Stub |
| 4 | ML Interfaces + Fixture Harness | `2026-04-10-L2-4-ml-interfaces.md` | Plan 1 | Stub |
| 5 | Operations + Observability | `2026-04-10-L2-5-operations.md` | Plan 1 | Stub |

Each L2 stub is a starting point only. Before execution, the chosen plan is fleshed out with full TDD-step detail via the `writing-plans` skill and then reviewed via `plan-review`.

## Out of Scope (Follow-on Epochs)

- **MotionBERT integration** — 2D→3D lifting with real model. Needs PyTorch dep, model checkpoint, inference budget decision.
- **HSMR / SKEL integration** — biomechanical skeleton fitting. Needs GPU inference endpoint.
- **GCN chain reasoning** — needs labeled training data.
- **Real rollup phase segmentation** — blocked on research gap §7.3.
- **Population-specific threshold validation** — blocked on research gap §7.6; Plan 2 uses the Hewett 2005 defaults only.
- **Video Beighton scoring** — post-launch per research report §5.3.
- **Model serving infrastructure** — Replicate vs Modal vs self-hosted decision. Epoch-scope choice, not tactical.
- **Flutter mobile app** — teammate's domain.
- **User authentication, multi-tenant isolation, payment / tier enforcement** — not required for the academic capstone.
- **CI/CD beyond local test runs** — GitHub Actions integration deferred until demo deployment.

## External Dependencies

- **Flutter team** — golden-capture fixtures for overhead_squat, single_leg_squat, push_up (rollup later). Plan 4 consumes them; until they arrive, synthetic fixtures cover the gap.
- **No team decision needed to start Plan 1.** Plans 2, 3, 4, 5 also start without cross-team blockers.

## Backtracking Triggers

If any of these fire during execution, pause and revise this L1 document:

- Scientific Reports 2025 DTW/NCC methodology turns out to require reference rep data we cannot generate synthetically with fidelity (affects Plan 3 viability).
- `PhaseSegmenter` protocol for rollup cannot be defined without knowing the real segmentation shape (affects Plan 4; may need to defer rollup entirely).
- Quality gate thresholds cannot be validated without golden captures (affects Plan 1; may need to gate epoch completion on Flutter fixture delivery).
- Plan 1's stage framework turns out to be over-abstracted for the actual set of stages we need (affects the whole epoch; may need to flatten the design).

## Completion Signal

Epoch is done when:

1. All 5 L2 plans have been executed and merged.
2. End-to-end integration test: POST a synthetic overhead_squat fixture → GET the report → assert the report contains expected rule-based flags, per-rep metrics, and trend output.
3. ML integration points are in place and tested with no-op implementations.
4. Golden-capture fixture pipeline is ready (Flutter can drop files, tests pick them up automatically).
5. `finishing-a-development-branch` runs and the epoch branch merges to main.
6. Decision document updated at `docs/decisions/` summarizing architectural choices made during the epoch.
