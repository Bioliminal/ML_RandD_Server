# BioLiminal Capstone

**Updated:** 2026-04-16
**Owner:** AaronCarney

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
| `docs/research/` | Engineering-decision research safe for public view — license audits, algorithm notes |
| `tools/` | Build scripts, CI helpers |

See `CLAUDE.md` for the full file-placement rules and tiebreakers between directories.

## Key Documents

| Document | What |
|----------|------|
| `docs/research/license-audit-2026-04-11-v2.md` | ML model/dataset license audit (raw facts) |
| `docs/research/dtw-library-comparison-2026-04-14.md` | DTW library selection |
| `docs/research/ncc-implementation-2026-04-14.md` | NCC algorithm implementation notes |
| `hardware/bom/final-buy-list-with-local.md` | Current buy list |
| `hardware/bom/component-database.csv` | Consolidated equipment database |
| `software/mobile-handover/README.md` | Phone teammate's integration guide |

## Quick Start

```bash
just --list        # See available tasks
```
