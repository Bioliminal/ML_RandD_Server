# Repo Visibility Cleanup — Dry-Run Manifest (2026-04-18)

**Status:** draft — Aaron's review, not executed yet.
**Goal:** prepare the four public bioliminal repos (`ML_RandD_Server`, `bioliminal-mobile-application`, `esp32-firmware`, `bioliminal`) for outside eyes by moving strategy / ops / session-state docs into a new private repo, without losing anything.

## Current repo visibility (verified 2026-04-18)

| Repo | Visibility |
|---|---|
| `bioliminal/ML_RandD_Server` | **public** |
| `bioliminal/bioliminal-mobile-application` | **public** |
| `bioliminal/esp32-firmware` | **public** |
| `bioliminal/bioliminal` (group README) | **public** |
| `bioliminal/research` | **private** |

## Decisions (from Aaron, 2026-04-18)

1. **New private repo:** `bioliminal-ops` — strategy, internal ops, session state.
2. **Market analysis = strategy** → moves to `bioliminal-ops`, not `research`.
3. **License audits stay public** — engineering-hygiene signal. Decision recorded in the companion gitlab work item.
4. This manifest is dry-run; nothing executes until Aaron approves.

## `bioliminal-ops` proposed structure

```
bioliminal-ops/
├── README.md              # what lives here and why, link to public repos
├── strategy/              # investor-facing / commercial picks / GTM
├── market/                # competitor analysis, pricing, TAM/SAM
├── plans/                 # L1 / L2 implementation plans
├── decisions/             # tradeoff docs that reveal strategy
├── operations/            # internal operational docs (not public-safe)
│   └── comms/             # session handoffs, parallel-session notes, plain-english briefs
└── sessions/              # progress files + per-task summaries
```

Each public repo, after cleanup, keeps only: code, tests, fixtures, research-backed technical docs, engineering decision docs that are safe to expose (license audits, stack matrices, algorithm notes, architecture docs), and code-adjacent runbooks with no strategic content.

---

## Manifest — `RnD_Server` (Aaron owns)

### Keep public (stays in `ML_RandD_Server`)

| Path | Why |
|---|---|
| `docs/research/license-audit-2026-04-11.md` | Per decision 3 — engineering hygiene |
| `docs/research/license-audit-2026-04-11-v2.md` | Per decision 3 — engineering hygiene |
| `docs/research/dtw-library-comparison-2026-04-14.md` | Pure engineering: library tradeoffs, no commercial exposure |
| `docs/research/ncc-implementation-2026-04-14.md` | Algorithm implementation notes — standard engineering |
| `docs/research/pipeline-architecture-decision-2026-04-10.md` | Architecture decision, already marked superseded; no commercial content inside |
| `docs/research/stack-options-matrix-2026-04-11.md` | Stack comparison — academic framing, explicitly says commercial is "not a decision factor" |
| `docs/research/citations-zotero-export.json` | Citation graph — factual |

### Move to `bioliminal-ops/strategy/`

| Current path | New path |
|---|---|
| `docs/research/model-commercial-viability-matrix-2026-04-16.md` | `strategy/model-commercial-viability-matrix-2026-04-16.md` |
| `docs/operations/gtm.md` | `strategy/gtm.md` |
| `docs/operations/BRAINLIFT.pdf` | `strategy/BRAINLIFT.pdf` |
| `docs/operations/Balance Brainlift.pdf` | `strategy/Balance-Brainlift.pdf` |

### Move to `bioliminal-ops/market/`

| Current path | New path |
|---|---|
| `docs/research/market/market-analysis.md` | `market/market-analysis.md` |
| `docs/research/market/market-analysis.pdf` | `market/market-analysis.pdf` |

### Move to `bioliminal-ops/plans/`

| Current path | New path |
|---|---|
| `docs/plans/2026-04-09-server-scaffold.md` | `plans/2026-04-09-server-scaffold.md` |
| `docs/plans/2026-04-10-analysis-pipeline-epoch.md` | `plans/2026-04-10-analysis-pipeline-epoch.md` |
| `docs/plans/2026-04-10-L2-1-pipeline-framework.md` | `plans/2026-04-10-L2-1-pipeline-framework.md` |
| `docs/plans/2026-04-10-L2-2-chain-reasoning.md` | `plans/2026-04-10-L2-2-chain-reasoning.md` |
| `docs/plans/2026-04-10-L2-3-dtw-temporal.md` | `plans/2026-04-10-L2-3-dtw-temporal.md` |
| `docs/plans/2026-04-10-L2-4-ml-interfaces.md` | `plans/2026-04-10-L2-4-ml-interfaces.md` |
| `docs/plans/2026-04-10-L2-5-operations.md` | `plans/2026-04-10-L2-5-operations.md` |

### Move to `bioliminal-ops/decisions/`

| Current path | New path |
|---|---|
| `docs/decisions/decisions.md` | `decisions/decisions.md` |
| `docs/decisions/rajat-alignment-summary.md` | `decisions/rajat-alignment-summary.md` |
| `docs/file-inventory.md` | `decisions/file-inventory.md` |

### Move to `bioliminal-ops/operations/comms/`

| Current path | New path |
|---|---|
| `docs/operations/comms/2026-04-11-plan-changes-plain-english.md` | `operations/comms/2026-04-11-plan-changes-plain-english.md` |
| `docs/operations/comms/2026-04-11-server-session-note.md` | `operations/comms/2026-04-11-server-session-note.md` |
| `docs/operations/comms/2026-04-16-demo-server-standup.md` | `operations/comms/2026-04-16-demo-server-standup.md` |
| `docs/operations/comms/2026-04-16-mobile-app-server-wiring-fixes.md` | `operations/comms/2026-04-16-mobile-app-server-wiring-fixes.md` |
| `docs/operations/comms/2026-04-16-model-lockdown-plain-english.md` | `operations/comms/2026-04-16-model-lockdown-plain-english.md` |
| `docs/operations/comms/2026-04-18-cloudflare-tunnel-setup.md` | `operations/comms/2026-04-18-cloudflare-tunnel-setup.md` |
| `docs/operations/comms/2026-04-18-repo-visibility-manifest.md` | `operations/comms/2026-04-18-repo-visibility-manifest.md` (this file) |
| `docs/operations/comms/research-integration-report.md` | `operations/comms/research-integration-report.md` (already has stale-warning header) |
| `docs/operations/comms/research-integration-report.pdf` | `operations/comms/research-integration-report.pdf` |

### Move to `bioliminal-ops/sessions/`

Entire `docs/sessions/` subtree — progress files, plan reviews, and all `summaries/task-*.md` (~70 files). These are internal work tracking with no value for outside readers.

| Current path | New path |
|---|---|
| `docs/sessions/plan-review-L2-1-pipeline-framework-architectural.md` | `sessions/plan-review-L2-1-pipeline-framework-architectural.md` |
| `docs/sessions/plan-review-L2-1-pipeline-framework-structural.md` | `sessions/plan-review-L2-1-pipeline-framework-structural.md` |
| `docs/sessions/progress-bioliminal-p4-wave-c.md` | `sessions/progress-bioliminal-p4-wave-c.md` |
| `docs/sessions/progress-main-20260412-143123-3a220b-adf38416.md` | `sessions/progress-main-20260412-143123-3a220b-adf38416.md` |
| `docs/sessions/summaries/*.md` (~70 files) | `sessions/summaries/*.md` |

### Move to `research/` repo (existing private)

These are literature/synthesis files that should have landed in the `research` repo per the 3-repo boundary rule. They're in `RnD_Server` as residue from before the 2026-04-15 research-split migration.

| Current path | New path |
|---|---|
| `docs/research/biomechanics/*` (7 files) | `biomechanics/` in `research` repo — **verify no duplicates first** |
| `docs/research/sensing/*` (4 files) | `sensing/` in `research` repo — **verify no duplicates first** |

**CAUTION:** the `research` repo already has `biomechanics/` and `sensing/` at its root. Cross-check every file to avoid overwrite or duplicate. Likely safer to inspect, then delete duplicates from `RnD_Server` rather than move.

---

## Manifest — `bioliminal-mobile-application` (Kelsi owns, Aaron flags)

Aaron doesn't own this repo; flag these to Kelsi for her decision. The proposed destinations mirror the RnD_Server logic.

### Move to `bioliminal-ops/strategy/`

| Current path | Proposed |
|---|---|
| `gtm.md` (repo root) | `strategy/gtm-mobile.md` |
| `gtm.pdf` | `strategy/gtm-mobile.pdf` |
| `brainlift-gemini.pdf` | `strategy/brainlift-gemini.pdf` |
| `brainlifts/` (whole dir) | `strategy/brainlifts-mobile/` |

### Move to `bioliminal-ops/operations/`

| Current path | Proposed |
|---|---|
| `AUDIT.md` / `AUDIT-GEMINI.md` / `AUDIT-PREMIUM.md` | `operations/audits/` |
| `MODIFICATION_DESIGN.md` / `MODIFICATION_IMPLEMENTATION.md` | `operations/modifications/` |
| `GEMINI.md` | `operations/ai-agent-instructions.md` (if it's agent config) |

### Move to `bioliminal-ops/sessions/` (Aaron's per-person docs)

| Current path | Proposed |
|---|---|
| `docs/aaron's docs/2026-04-11-plan-changes-plain-english.md` | `sessions/aaron/` |
| `docs/aaron's docs/stack-options-matrix-2026-04-11.md` | delete — duplicate of `RnD_Server/docs/research/stack-options-matrix-2026-04-11.md` |

### Move to `research/` repo

| Current path | Proposed |
|---|---|
| `docs/rajiv's docs/01-cueing-rajiv.md` | `research/cueing/` or wherever Rajiv's cueing notes live now |
| `docs/rajat's docs/complete-research-document.md` | `research/hardware/` or the appropriate subdir |
| `docs/rajat's docs/hardware-cueing-research.md` | `research/cueing/` |
| `docs/rajat's docs/hardware-alignment-injury-prevention.html` | `research/hardware/` |

### Move to `esp32-firmware` repo (hardware content in the wrong repo)

Per 3-repo boundary, these don't belong in mobile. Rajat's call on destination.

| Current path | Rationale |
|---|---|
| `docs/rajat's docs/hardware-configurations.html` | Hardware config |
| `docs/rajat's docs/sensor-purchase-plan.html` / `.md` / `.pdf` | Component sourcing — should be `esp32-firmware/hardware/bom/` |
| `docs/rajat's docs/final-buy-list-with-local.md` | BOM |
| `docs/rajat's docs/buy-list-2026-04-09_1.pdf` | BOM |
| `docs/rajat's docs/shopping-list-researched_1.html` | BOM |
| `docs/rajat's docs/hardware-engineering-specs.md` | Hardware specs |
| `docs/rajat's docs/hardware-build-4ch-injury-prevention.html` | Build doc |
| `docs/rajat's docs/Actuation_Options_Spec_v2.pdf` | Hardware spec |
| `docs/rajat's docs/mvp-build-decisions.md` | Hardware decisions |
| `docs/rajat's docs/wave1-lean-final.html` | Hardware build |
| `docs/rajat's docs/ESP32_MyoWare_Setup_Guide.pdf` | Hardware setup |

### Move to `bioliminal-ops/operations/` (private — PII)

| Current path | Why private |
|---|---|
| `docs/rajat's docs/SALESORDER_EMAIL98549680.pdf` | Personal billing info — PII. **Must be private even if Rajat doesn't care about the rest.** |

### Mobile repo gitignore additions

| Pattern | Reason |
|---|---|
| `docs/demo videos/` | Large binaries, keep out of git (or use Git LFS) |
| `.env`, `.env.*` | Secrets |
| `*.keystore`, `*.jks` | Signing keys |
| `google-services.json` | Firebase config with keys (**verify before removing — may be required**) |
| `android/key.properties` | Signing config |
| `build/`, `.gradle/` | Build output |
| `.dart_tool/`, `.flutter-plugins*` | Flutter local state |

---

## Manifest — `esp32-firmware` (Rajat owns, Aaron flags)

Flag to Rajat. Aaron hasn't inspected this repo — Rajat should apply the same categorization logic: strategy/ops/sessions → `bioliminal-ops`, research → `research`, keep hardware docs + code public.

Standard gitignore additions Rajat should confirm:
- `build/`, `.pio/`, `.vscode/` (PlatformIO / ESP-IDF outputs)
- `*.bin`, `*.elf`, `*.map` (firmware artifacts)
- `secrets.h`, `wifi_credentials.h` (any hardcoded credentials)
- `.env`

---

## Manifest — `bioliminal` (group README repo)

Single `README.md`. Keep public as-is. No private content.

---

## Public repos — gitignore baseline (post-cleanup)

Each public repo needs a proper `.gitignore`. Shared baseline:

```gitignore
# Secrets
.env
.env.*
!.env.example
*.pem
*.key
*.crt
credentials.json

# Local state
.DS_Store
Thumbs.db
.vscode/
.idea/
*.swp
```

Per-repo additions are in the sections above.

---

## Execution plan (not yet executed)

1. **Create the gitlab work item** tracking this cleanup (see below).
2. **Aaron reviews this manifest**, redlines any reclassifications, approves.
3. **Create `bioliminal/bioliminal-ops` private gitlab repo** with the proposed directory structure.
4. **Seed `bioliminal-ops` README.md** explaining: what lives here, why, pointers back to public repos, access model.
5. **Move Aaron's RnD_Server docs** using `git mv` locally, commit in `RnD_Server` (removes from public), then add in `bioliminal-ops` with a fresh commit referencing the original path in the commit message. Preserves history via message cross-reference; does **not** use `git subtree` or history-splitting (too invasive for a mid-demo-week cleanup).
6. **Mirror the research-repo-bound `biomechanics/` and `sensing/` subtrees** only after cross-checking duplicates.
7. **Post a gitlab note per-teammate** (Kelsi, Rajat, Rajiv) summarizing what needs to move out of their repos, with the relevant subsection of this manifest linked.
8. **Add `.gitignore` baseline** to each public repo in the same commit that removes the moved docs.
9. **Post-migration sweep:** grep each public repo for obvious leakage patterns (`BRAINLIFT`, `GTM`, `investor`, `pricing`, `confidential`, `TODO-private`) and fix anything that surfaces.
10. **Verify** by cloning each public repo fresh and spot-checking nothing strategic remains.

## Out of scope for this migration

- Changing existing repo visibility (keep public repos public, private private).
- Rewriting git history to erase moved files from public history. Decision: leave history intact — git commit messages already reference these docs, and rewriting public history is expensive and breaks anyone who cloned. If a specific file is considered retroactively sensitive, handle it individually via `git filter-repo`.
- Migrating the comcam-ml / olorin-white / other non-bioliminal workstreams — this manifest is bioliminal-only.
- Setting up CI/lint rules in the public repos — separate concern.

## Open questions for Aaron

1. `docs/operations/comms/research-integration-report.md` has a stale-warning header. Move to `bioliminal-ops` or just delete since it's superseded?
2. Stack options matrix explicitly says "academic license only, commercial is not a decision factor" — is that statement still something you want public, given the post-demo commercial pivot? (Current proposal: keep public, since it's accurate for the prototype phase.)
3. `docs/file-inventory.md` — stale since the 2026-04-15 research-split migration. Move to `bioliminal-ops/decisions/` as a historical snapshot, or delete?
4. Do you want Kelsi/Rajat to migrate their docs themselves (each opens MRs against their repo + the new `bioliminal-ops`), or do you want to do it all yourself across repos? Affects timing of the cleanup vs. demo week.
