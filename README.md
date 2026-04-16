# BioLiminal Capstone

AI-powered movement screening + sEMG compression garment for injury prevention. Gauntlet AI capstone project.

**Two-layer system:**
1. Free phone-camera app (MediaPipe pose estimation + fascial chain reasoning)
2. Premium sEMG garment with haptic cueing for real-time muscle activation feedback

## Structure

| Directory | Purpose |
|-----------|---------|
| `hardware/` | Specs, sensor research, cueing research, form factor evaluation |
| `hardware/bom/` | Buy lists, component database (CSV), MVP decisions |
| `software/` | Application code, tests, config (server lives in `software/server/`) |
| `software/mobile-handover/` | Contract package for the Flutter teammate — Dart interface, JSON schema, sample fixture, MediaPipe model fetch |
| `ml/` | Datasets, experiments, models, training, evaluation |
| `docs/operations/` | High-level project framing — BrainLifts, GTM, mission, vision |
| `docs/operations/comms/` | Communications artifacts — team summaries, session notes, technical context for teammates |
| `docs/research/` | Per-paper research, deep reads, synthesis docs, model/framework recommendations |
| `docs/research/{biomechanics,sensing,market}/` | Research subfolders by domain |
| `docs/plans/` | L1 epoch plans, L2 tactical plans |
| `docs/decisions/` | Cross-domain tradeoff decisions |
| `docs/sessions/` | Session handover context, plan reviews, progress snapshots |
| `tools/` | Build scripts, CI helpers |

See `CLAUDE.md` for the full file-placement rules and tiebreakers between directories.

## Key Documents

| Document | What |
|----------|------|
| `docs/operations/BRAINLIFT.pdf` | Cognitive design + SPOVs |
| `docs/operations/gtm.md` | Go-to-market plan |
| `docs/operations/comms/research-integration-report.md` | Authoritative technical context for the sensing/ML layer |
| `docs/research/pipeline-architecture-decision-2026-04-10.md` | Authoritative pipeline + stack engineering decision |
| `docs/research/license-audit-2026-04-11.md` / `-v2` | ML model/dataset license audit |
| `docs/research/stack-options-matrix-2026-04-11.md` | Pose/biomech stack selection matrix |
| `docs/research/dtw-library-comparison-2026-04-14.md` | DTW library selection |
| `docs/research/ncc-implementation-2026-04-14.md` | NCC algorithm implementation notes |
| `docs/research/market/market-analysis.md` | Competitive landscape + TAM/SAM/SOM |
| `docs/decisions/decisions.md` | HW/SW/ML tradeoff log |
| `hardware/bom/final-buy-list-with-local.md` | Current buy list ($745 budget) |
| `hardware/bom/component-database.csv` | Consolidated equipment database |
| `software/mobile-handover/README.md` | Phone teammate's integration guide |

## Quick Start

```bash
just --list        # See available tasks
```
