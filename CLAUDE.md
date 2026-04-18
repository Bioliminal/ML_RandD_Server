# RnD_Server — ML & Analysis Server

**Updated:** 2026-04-18
**Owner:** AaronCarney

Project-wide context (team, pipeline architecture, constraints, GitLab label taxonomy) lives in the parent `CLAUDE.md` at `projects/bioliminal/CLAUDE.md`. This file covers repo-specific file organization and conventions.

**Documentation conventions:** see https://gitlab.com/bioliminal/bioliminal/-/blob/main/CONVENTIONS.md — header schema (`Status` / `Created` / `Updated` / `Owner`), git-author → gitlab-handle mapping, and the delete-over-archive rule for superseded content. Follow the header schema for every new doc under `docs/`.

## Compliance & Privacy Posture

**Not HIPAA.** Binding regimes: WA MHMDA (opt-in, $7,500/violation, private right of action), FTC HBNR (~$53k/violation), GDPR Art 9 in EU (no wellness exception). IL BIPA HB 2984 pending would add neural data. **sEMG is functionally biometric — 90–97% re-id from 0.8s of 4-channel data.** Schema changes that touch sEMG, session consent, or retention must treat these as load-bearing constraints, not compliance theater.

**Full analysis (always read, do not restate from memory):** `projects/bioliminal/research/synthesis/deep-read-semg-privacy-regulation-2026-04-15.md`. Parent hub: `projects/bioliminal/CLAUDE.md` § "Compliance & Privacy Posture".

## File Organization

### Placement Rules

Files go where their **primary purpose** lives. This repo is public; internal strategy/ops/session content lives in the private `bioliminal-ops` repo, and literature content lives in the private `research` repo.

| If the file is primarily about... | It goes in... |
|---|---|
| A physical component, sensor, actuator, or form factor | `hardware/` in this repo |
| Buying, sourcing, or pricing components | `hardware/bom/` in this repo |
| Engineering decisions safe for public view: license audits, algorithm implementation notes, library comparisons | `docs/research/` in this repo |
| Training scripts, model configs, dataset processing | `ml/` in this repo |
| Application code, UI, API | `software/` in this repo |
| Mobile/server contract handoffs (Dart interfaces, JSON schemas, fixtures) | `operations/handover/mobile/` in `bioliminal-ops` |
| Build tooling, CI, Docker, scripts | `tools/` in this repo |
| Literature: papers, synopses, synthesis docs, deep reads | [`research`](https://gitlab.com/bioliminal/research) repo (private) |
| Strategy: commercial viability, GTM, investor-facing framing, L1/L2 plans, cross-domain decisions | [`bioliminal-ops`](https://gitlab.com/bioliminal/bioliminal-ops) repo (private) |
| Competitors, market sizing, pricing, regulatory strategy | `market/` in `bioliminal-ops` |
| Cross-team internal comms, session handoffs, progress files | `operations/comms/` or `sessions/` in `bioliminal-ops` |

**`hardware/bom/` vs `hardware/`** — BOMs, shopping lists, and pricing docs go in `bom/`. Specs, evaluation docs, and architecture decisions stay in `hardware/`.

**Mobile handover lives in ops, not here.** `software/server/` holds the running FastAPI service. The **contract** the Flutter teammate consumes (Dart interface, exported JSON schemas, sample payload, MediaPipe fetch instructions, smoke-test script) lives at `bioliminal-ops/operations/handover/mobile/` so both teams pull from a single cross-team coordination source. When the server pydantic schema changes, regenerate via `bioliminal-ops/operations/handover/mobile/tools/export_schemas.py` (auto-finds this repo as a sibling) and update `interface/models.dart` to match. The Flutter app itself lives in its own repo.

### Equipment Database

`hardware/bom/component-database.csv` is the single source of truth for all components. Columns: `component_name, quantity, unit_price, total_price, vendor, category, status, source_document`. When adding new components, update this CSV — don't just add them to a markdown file.

Status values: `current` (latest buy list), `superseded` (replaced by newer choice), `alternative` (valid option not selected).

