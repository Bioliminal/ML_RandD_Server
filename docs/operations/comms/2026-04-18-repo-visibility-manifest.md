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
3. **License audits:** v2 stays public (engineering-hygiene signal). v1 is deleted — git history is the reference.
4. **Other superseded docs are deleted outright** (not archived) — rely on git history. See the "Delete outright" section.
5. **`stack-options-matrix-2026-04-11.md` moves to ops** (reversed from initial proposal) — it will be kept updated going forward rather than frozen in place.
6. **Document header convention** added. Every `.md` under `docs/` gets a minimal status/date/owner header. Convention documented in the group repo at `bioliminal/bioliminal/CONVENTIONS.md`.
7. **Retrofit order:** headers added in each public repo *before* the migration, so authorship provenance survives the non-history-preserving move.
8. This manifest is dry-run; nothing executes until Aaron approves.

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

### Delete outright (git history is the reference)

| Path | Why |
|---|---|
| `docs/research/license-audit-2026-04-11.md` | Superseded by v2; no need to carry a frozen v1 |
| `docs/research/pipeline-architecture-decision-2026-04-10.md` | ⚠️ STALE / DISPUTED header already present; superseded by model-commercial-viability-matrix |
| `docs/operations/comms/research-integration-report.md` | 🪦 ARCHIVED header already present (2026-04-16) |
| `docs/operations/comms/research-integration-report.pdf` | Companion to the md above |
| `docs/research/sensing/catalog.md` | Pre-2026-04-15-migration tracking file; says itself that content has moved to `research` repo |
| `docs/research/sensing/research-gaps.md` | Pre-migration audit against an old session's HTML; obsolete |
| `docs/research/sensing/2506.html` | Archived web page from old research session |
| `docs/research/sensing/2602.html` | Archived web page from old research session |
| `docs/research/sensing/best-pose-estimation-models.html` | Archived web page from old research session |
| `docs/research/sensing/unity-isdk-body-pose-detection.html` | Archived web page from old research session |

### Keep public (stays in `ML_RandD_Server`)

| Path | Why |
|---|---|
| `docs/research/license-audit-2026-04-11-v2.md` | Per decision 3 — engineering hygiene |
| `docs/research/dtw-library-comparison-2026-04-14.md` | Pure engineering: library tradeoffs, no commercial exposure |
| `docs/research/ncc-implementation-2026-04-14.md` | Algorithm implementation notes — standard engineering |
| `docs/research/citations-zotero-export.json` | Citation graph — factual |

### Move to `bioliminal-ops/strategy/`

| Current path | New path |
|---|---|
| `docs/research/model-commercial-viability-matrix-2026-04-16.md` | `strategy/model-commercial-viability-matrix-2026-04-16.md` |
| `docs/research/stack-options-matrix-2026-04-11.md` | `strategy/stack-options-matrix.md` (renamed — will be kept updated) |
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

## Document header convention

Every `.md` under `docs/` (and top-level ones like `README.md`, `CLAUDE.md`) gets a minimal header placed between the H1 title and the body:

```markdown
# <Title>

**Status:** current | superseded | draft
**Created:** YYYY-MM-DD
**Updated:** YYYY-MM-DD
**Owner:** <gitlab-handle>
```

Rules:

- Dated filenames (`YYYY-MM-DD-slug.md`) stay the primary signal for point-in-time docs; `Created` should match the filename date.
- Evergreen docs (`README.md`, `CLAUDE.md`, placement-rules docs) need only `**Updated:**` + `**Owner:**`; drop `Status` and `Created`.
- **No `Supersedes:` / `Superseded by:` fields.** When a doc is superseded, delete it. Git history is the reference.
- `Status: superseded` should almost never appear post-cleanup — only for docs deliberately retained as citable historical references (rare; none currently).
- `Status: draft` is for work-in-progress docs that shouldn't be cited yet.

### Canonical convention location

The convention lives at `bioliminal/bioliminal/CONVENTIONS.md` (group repo). Each public repo's `CLAUDE.md` adds a one-line pointer so any Claude session landing in any repo picks it up on first load:

```
**Documentation conventions:** see https://gitlab.com/bioliminal/bioliminal/-/blob/main/CONVENTIONS.md — follow the header schema for every doc under `docs/`.
```

`CONVENTIONS.md` also carries the canonical git-author → gitlab-handle mapping so the retrofit script and future authors use the same handles:

| Git author | GitLab handle |
|---|---|
| Aaron Carney | `AaronCarney` |
| Kelsi Andrews | `kelsi.andrews` |
| Rajat Arora | `rajat19981` |
| Rajiv Nelakanti | `rajivn` |

### Retrofit script (runs per-repo)

One ~60-line script, once per public repo, applied **before** migration so authorship provenance survives the non-history-preserving move:

```python
for md in repo.glob("docs/**/*.md"):
    if "**Status:**" in md.read_text(): continue            # already has header
    created = git_first_commit_date(md)                     # git log --diff-filter=A --follow --format=%as | tail -1
    updated = git_latest_commit_date(md)                    # git log -1 --format=%as
    owner   = handle_map[git_primary_author(md)]            # git log --format=%an | sort | uniq -c | sort -rn | head -1
    inject_header(md, created, updated, owner, status="current")
```

After migration, the script runs once more inside `bioliminal-ops` — a no-op for migrated files (headers already present) and a safety net for any net-new docs.

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

1. **Gitlab work item created** — `ML_RandD_Server#16` tracks this cleanup.
2. **Aaron reviews this manifest**, redlines any reclassifications, approves.
3. **Write `bioliminal/bioliminal/CONVENTIONS.md`** — header schema + git-author → handle mapping. Commit to group repo.
4. **Delete superseded docs** in each public repo (per "Delete outright" sections). Commit: `chore: remove superseded docs — git history is the reference`.
5. **Run retrofit script** in each public repo, adding headers populated from git log. Commit: `docs: add status/date/owner headers per conventions`. This must happen **before** migration so authorship provenance survives the non-history-preserving move.
6. **Update each public repo's `CLAUDE.md`** with a one-line pointer to `CONVENTIONS.md`. Commit per repo.
7. **Create `bioliminal/bioliminal-ops` private gitlab repo** with the proposed directory structure.
8. **Seed `bioliminal-ops/README.md`** explaining: what lives here, why, pointers back to public repos, access model.
9. **Move Aaron's RnD_Server docs** using `git mv` locally, commit in `RnD_Server` (removes from public), then add in `bioliminal-ops` with a fresh commit referencing the original path in the commit message. Preserves history via message cross-reference; does **not** use `git subtree` or history-splitting.
10. **Mirror the research-repo-bound `biomechanics/` and `sensing/` subtrees** only after cross-checking duplicates against the `research` repo.
11. **Run retrofit script inside `bioliminal-ops`** as a safety net — no-op for migrated files (already headered), populates any net-new docs.
12. **Post a gitlab note per-teammate** (Kelsi, Rajat, Rajiv) summarizing what needs to move out of their repos, with the relevant subsection of this manifest linked.
13. **Add `.gitignore` baseline** to each public repo in the same commit that removes the moved docs.
14. **Post-migration sweep:** grep each public repo for obvious leakage patterns (`BRAINLIFT`, `GTM`, `investor`, `pricing`, `confidential`, `TODO-private`) and fix anything that surfaces.
15. **Verify** by cloning each public repo fresh and spot-checking nothing strategic remains.

## Out of scope for this migration

- Changing existing repo visibility (keep public repos public, private private).
- Rewriting git history to erase moved files from public history. Decision: leave history intact — git commit messages already reference these docs, and rewriting public history is expensive and breaks anyone who cloned. If a specific file is considered retroactively sensitive, handle it individually via `git filter-repo`.
- Migrating the comcam-ml / olorin-white / other non-bioliminal workstreams — this manifest is bioliminal-only.
- Setting up CI/lint rules in the public repos — separate concern.

## Open questions for Aaron

1. `docs/file-inventory.md` — stale since the 2026-04-15 research-split migration. Move to `bioliminal-ops/decisions/` as a historical snapshot, or delete outright per decision 4?
2. Do you want Kelsi/Rajat to migrate their docs themselves (each opens MRs against their repo + the new `bioliminal-ops`), or do you want to do it all yourself across repos? Affects timing of the cleanup vs. demo week.
3. GitHub mirror: `RnD_Server` also pushes to `github.com/AaronCarney/capstone-fascia`. If that mirror is public, it needs the same treatment. In scope for this cleanup, or separate follow-up?

## Resolved (previously open)

- `research-integration-report.md` + `.pdf` → **delete** (resolved by decision 4).
- Stack options matrix → **move to ops** as a living doc (resolved by decision 5).
- License audit v1 → **delete** (resolved by decision 3).
