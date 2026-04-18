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

Files go where their **primary purpose** lives. When a file could belong in multiple places, use these tiebreakers:

| If the file is primarily about... | It goes in... | Even if it also touches... |
|---|---|---|
| A physical component, sensor, actuator, or form factor | `hardware/` | Software that reads it, ML that processes its signal |
| Buying, sourcing, or pricing components | `hardware/bom/` | Research that justified the purchase |
| Fascial chains, anatomy, injury epidemiology, movement science | `docs/research/biomechanics/` | Sensors that measure it, ML that models it |
| sEMG signal quality, pose estimation accuracy, CV performance | `docs/research/sensing/` | Hardware specs, biomechanics context |
| Competitors, market sizing, regulatory/FDA, business models | `docs/research/market/` | Product direction, pricing |
| Per-paper deep reads, model/framework recommendations, citation lists | `docs/research/` (root) | Cross-cutting research synthesis |
| **High-level project framing**: BrainLifts, GTM, mission, vision, SPOVs | `docs/operations/` | Research backing them |
| **Communications & cross-team handoffs**: plain-English summaries, session notes between Aaron / teammates / parallel coding sessions, shareable technical reports for the team | `docs/operations/comms/` | Whatever they're communicating about |
| Implementation plans (L1 epochs, L2 tactical) | `docs/plans/` | Research and decisions they consume |
| Session handover, context dumps, plan reviews between work sessions | `docs/sessions/` | Everything — these are snapshots, not primary sources |
| Tradeoff decisions that span HW+SW+ML | `docs/decisions/` | Individual domain details |
| Training scripts, model configs, dataset processing | `ml/` | Hardware that collects the data |
| Application code, UI, API | `software/` | ML models it calls, hardware it reads |
| Mobile/server contract handoffs (Dart interfaces, JSON schemas, fixtures) | `software/mobile-handover/` | Implementation details inside `software/server/` |
| Build tooling, CI, Docker, scripts | `tools/` | Any domain it automates |

### Research Subdirectory Tiebreakers

Within `docs/research/`:
- `biomechanics/` — The body. Fascial chains, muscle anatomy, injury mechanisms, clinical thresholds, movement patterns. If it cites Wilke, McGill, Hewett, Schleip, or discusses force transmission → biomechanics.
- `sensing/` — The measurement. sEMG signal chains, MediaPipe accuracy, sensor validation, gap analysis of what's measurable vs claimed. If it's about whether we *can* detect something → sensing.
- `market/` — The business. Competitors, TAM/SAM, FDA/regulatory, pricing, practitioner counts. If it's about who else does this or whether we can sell it → market.
- Root (`docs/research/`) — Engineering-decision artifacts: license audits, stack-options matrices, library comparisons, algorithm implementation notes, and model/framework recommendation docs.

**`docs/operations/` vs `docs/research/`** — operations is about *what we're building and why*; research is about *what the science says*.
- If it frames the product (BrainLift, SPOVs, GTM, mission) → `docs/operations/`
- If it cites papers and synthesizes evidence → `docs/research/`
- Example: `gtm.md` is in `docs/operations/` because it's a product strategy document, even though it cites market research.
- Example: `pipeline-architecture-decision-2026-04-10.md` is in `docs/research/` because it's an engineering decision grounded in paper findings — it drives implementation choices for the sensing/ML layer.

**`docs/operations/` vs `docs/operations/comms/`** — operations holds living strategy/framing docs that the team owns over time; `comms/` holds the artifacts produced *for* communicating between humans (or between Aaron and parallel coding sessions).
- Living, owned by the team, updated as the project evolves → `docs/operations/` (root)
- Dated, write-once, communication artifact → `docs/operations/comms/`
- Examples in `docs/operations/`: `BRAINLIFT.pdf`, `Balance Brainlift.pdf`, `gtm.md`.
- Examples in `docs/operations/comms/`: `research-integration-report.md` (technical context for teammates), `2026-04-11-plan-changes-plain-english.md` (Slack-paste team summary), `2026-04-11-server-session-note.md` (handoff to parallel coding session).
- Naming convention for `comms/`: dated files (`YYYY-MM-DD-<slug>.md`) for snapshots; undated for evergreen team-context docs that get revised in place.

**`hardware/bom/` vs `hardware/`** — BOMs, shopping lists, and pricing docs go in `bom/`. Specs, evaluation docs, and architecture decisions stay in `hardware/`.

**`software/mobile-handover/` vs `software/server/`** — `software/server/` holds the running FastAPI service. `software/mobile-handover/` holds the **contract** that the Flutter teammate's app needs to satisfy: Dart data classes mirroring the pydantic schema, an exported JSON schema, a sample valid payload, the MediaPipe model fetch instructions, and a smoke-test script. The mobile-handover package is treated as derived output — when the server pydantic schema changes, regenerate via `software/mobile-handover/tools/export_schemas.py` and update `interface/models.dart` to match. Do not put running mobile code there; the Flutter app lives in its own repo.

### Equipment Database

`hardware/bom/component-database.csv` is the single source of truth for all components. Columns: `component_name, quantity, unit_price, total_price, vendor, category, status, source_document`. When adding new components, update this CSV — don't just add them to a markdown file.

Status values: `current` (latest buy list), `superseded` (replaced by newer choice), `alternative` (valid option not selected).

