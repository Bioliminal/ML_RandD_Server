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
- **Stack:** Python 3.11+, FastAPI, pydantic v2, numpy, pytest, ruff, black, uv — the scaffold stack. No new runtime dependencies unless explicitly justified in the L2 plan. **Plan 3 is the known exception to this rule**: it adds a DTW library (`fastdtw` or `tslearn`, decided via library check during Plan 3's `writing-plans` pass). This is the only sanctioned runtime dependency added in this epoch.
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

This epoch is composed of 5 L2 plans. **Execution order: 1 → 4 → 2 → 3 → 5.** Plan 4 runs second so that Plans 2 and 3 can write their tests against the real synthetic fixture generator from the start rather than hand-building divergent test data. Plans 2-5 all depend only on Plan 1 structurally; the sequencing below optimizes for TDD data reuse and product-story coherence.

| Order | # | Plan | File | Depends On | Status |
|-------|---|------|------|------------|--------|
| 1st | 1 | Pipeline Framework + Core Analysis Stages | `2026-04-10-L2-1-pipeline-framework.md` | Scaffold | Stub |
| 2nd | 4 | ML Interfaces + Fixture Harness | `2026-04-10-L2-4-ml-interfaces.md` | Plan 1 | Stub |
| 3rd | 2 | Chain Reasoning v1 + Report Assembly | `2026-04-10-L2-2-chain-reasoning.md` | Plan 1, Plan 4 fixtures | Stub |
| 4th | 3 | DTW + Temporal Analysis | `2026-04-10-L2-3-dtw-temporal.md` | Plan 1, Plan 2, Plan 4 fixtures | Stub |
| 5th | 5 | Operations + Observability | `2026-04-10-L2-5-operations.md` | Plan 1 | Stub |

Rationale for the 1 → 4 → 2 → 3 → 5 ordering:

- **Plan 1 first** — nothing runs without the stage framework.
- **Plan 4 second** — ships the synthetic fixture generator and ML protocols. **Plan 4 owns BOTH session-fixture generation AND reference-rep generation** via a single shared module (`tests/fixtures/synthetic/generator.py`) exposing two entry points: `generate_session()` (for end-to-end pipeline tests) and `generate_reference_rep()` (consumed by Plan 3). Plans 2 and 3 consume these fixtures as their primary test data; neither plan builds its own generator, avoiding drift between hand-built test data.
- **Plan 2 third** — once fixtures exist, chain reasoning can TDD against realistic compensation signals (e.g., the overhead-squat valgus variant from Plan 4).
- **Plan 3 fourth** — extends Plan 2's report schema and depends on Plan 4's reference rep library.
- **Plan 5 last** — operations hardening is the final production layer; doesn't affect the earlier logic but benefits from having the full pipeline in place to observe.

Each L2 stub is a starting point only. Before execution, the chosen plan is fleshed out with full TDD-step detail via the `writing-plans` skill and then reviewed via `plan-review`.

## Out of Scope (Follow-on Epochs)

- **MotionBERT integration** — 2D→3D lifting with real model. Needs PyTorch dep, model checkpoint, inference budget decision.
- **HSMR / SKEL integration** — biomechanical skeleton fitting. Needs GPU inference endpoint.
- **GCN chain reasoning** — needs labeled training data.
- **Real rollup phase segmentation** — blocked on research gap §7.3.
- **Population-specific threshold validation** — blocked on research gap §7.6; Plan 2 uses the Hewett 2005 defaults only. Plan 2 ships the body-type adjustment *mechanism* with placeholder lookup data; the deferred item is the empirical *validation* of the adjustment values. The mechanism can be rerun against validated thresholds once they exist.
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
- FastAPI `BackgroundTasks` proves inadequate for pipeline runtime (background thread starvation under load, shared event-loop issues, etc.) — Plan 5 may need to adopt TaskIQ or Celery instead.
- Async context propagation of correlation IDs breaks tests — Python `contextvars` combined with `BackgroundTasks` has sharp edges that may force a rework of Plan 5's correlation ID design.

## Completion Signal

Epoch is done when:

1. All 5 L2 plans have been executed and merged.
2. End-to-end integration test: POST a synthetic overhead_squat fixture → GET the report → assert the report contains expected rule-based flags, per-rep metrics, and trend output.
3. ML integration points are in place and tested with no-op implementations.
4. Golden-capture fixture pipeline is ready (Flutter can drop files, tests pick them up automatically).
5. `finishing-a-development-branch` runs and the epoch branch merges to main.
6. Decision document updated at `docs/decisions/` summarizing architectural choices made during the epoch.
