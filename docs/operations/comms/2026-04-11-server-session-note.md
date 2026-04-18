# Note for the parallel server-coding session

**Status:** current
**Created:** 2026-04-11
**Updated:** 2026-04-15
**Owner:** AaronCarney

**Date:** 2026-04-11
**From:** the research/planning session.
**To:** whoever is currently coding the BioLiminal server (probably executing
L2 Plan 1 / Plan 4 / Plan 2 via `parallel-plan-executor`).

You don't need to change what you're building. This note tells you what *I*
just did that touches the server contract, so you can absorb it without
re-reading three research documents.

---

## TL;DR for you

1. **The server pydantic schema at `software/server/src/auralink/api/schemas.py`
   is now also the contract for the Flutter mobile app.** Don't change shapes
   without flagging it. If you must change a field, regenerate the JSON schema
   in the mobile-handover package (instructions below).
2. **A new `software/mobile-handover/` directory exists.** It mirrors the server
   schema in Dart classes for the phone teammate. Treat it as read-only output —
   it's regenerated, not hand-edited, when the schema changes.
3. **The full ML model story is changing**, but in a way that *does not affect
   you in this session*. Plan 4's `Lifter` / `SkeletonFitter` / `PhaseSegmenter`
   protocols are unchanged. What plugs into them later is changing. Build the
   stubs as written.
4. **One small future change to Plan 2:** the body-type intake task should be
   downgraded from "questionnaire" to "auto-populate from `SkeletonFitter`
   output." Don't act on this yet — I'll edit Plan 2 explicitly. If you reach
   that task before I update the plan, pause and ping the user.

---

## What's in `software/mobile-handover/`

```
software/mobile-handover/
├── README.md                         ← integration guide for the phone teammate
├── interface/
│   ├── models.dart                   ← Dart classes mirroring the pydantic schema
│   ├── pose_detector.dart            ← abstract pose-model interface
│   └── mediapipe_pose_detector.dart  ← reference impl skeleton (TODOs only)
├── schemas/
│   └── session.schema.json           ← JSON Schema exported from pydantic
├── fixtures/
│   └── sample_valid_session.json     ← known-valid 5-frame overhead-squat payload
├── model/
│   ├── DOWNLOAD.md                   ← MediaPipe model fetch instructions
│   └── blazepose_landmark_order.md   ← canonical 33-landmark index table
└── tools/
    ├── export_schemas.py             ← regenerates session.schema.json from pydantic
    └── post_sample.sh                ← smoke-test: POSTs the fixture to a running server
```

The Dart classes in `interface/models.dart` are 1:1 with `Session`, `Frame`,
`Landmark`, `SessionMetadata`, `SessionCreateResponse` from
`software/server/src/auralink/api/schemas.py`. Field names use Dart camelCase
(`frameRate`, `timestampMs`) but `toJson` writes the snake_case wire format
(`frame_rate`, `timestamp_ms`) so the network payload matches pydantic exactly.

The fixture in `fixtures/sample_valid_session.json` was generated with the
*current* pydantic models (`Session.model_validate` round-trips it cleanly —
verified). It's an overhead squat, 5 frames, 33 landmarks each, in canonical
BlazePose order. If your changes ever cause the fixture to fail validation,
that's a contract break and the phone teammate needs to know immediately.

---

## What this means for your in-flight work

### If you're currently on Plan 1 or Plan 4

Carry on. You're not affected. The protocols stay the same, the shapes you're
building tests against are the shapes the phone is going to send.

### If you're currently on Plan 2 (chain reasoning + report assembly)

Two things to know:

1. **`BodyTypeProfile` task should not ship a questionnaire.** Per a team
   decision dated 2026-04-10, the body type profile gets auto-populated from the
   `SkeletonFitter` output (SKEL `β` shape vector → height/build buckets),
   not from a user-facing form. **If you reach this task, pause and check with
   the user before implementing.** I'll be updating Plan 2 to reflect this in
   a separate edit, but I haven't touched it yet at the time of this note.
2. **Every rule in `config/rules/*.yaml` should have an `evidence:` block.**
   New requirement from the deep-read of the Sahrmann/Joyce/Van Dillen
   biomechanics literature. The block should look like:
   ```yaml
   evidence:
     level: 2b   # or "1", "3", "5" — Oxford CEBM level of evidence
     citation: "Harris-Hayes 2018, JOSPT 48(4):316–324"
     mechanism: "hip adduction reduction correlated with MHHS improvement (r=−0.67, p<.01)"
   ```
   This is what the report assembler uses to back the narrative claims with a
   defensible source. The schema for `RuleConfig` should require these three
   fields. If you've already drafted a rule schema without them, add them.

### If you're currently on Plan 3 or Plan 5

Carry on. Not affected.

---

## Regenerating the JSON schema after a server schema change

If you (or anyone) changes `software/server/src/auralink/api/schemas.py`, the
mobile-handover JSON schema needs to refresh. From the repo root:

```bash
software/server/.venv/bin/python software/mobile-handover/tools/export_schemas.py
```

This rewrites `software/mobile-handover/schemas/session.schema.json` from the
live pydantic models. The Dart classes in `interface/models.dart` are
hand-written, not codegen — they need a corresponding manual edit. The
mobile-handover README documents this drift-detection process for the phone
teammate.

A simple drift smoke-test (paste into a terminal):

```bash
software/server/.venv/bin/python -c "
import json, sys
sys.path.insert(0, 'software/server/src')
from auralink.api.schemas import Session
data = json.load(open('software/mobile-handover/fixtures/sample_valid_session.json'))
print('OK' if Session.model_validate(data) else 'FAIL')
"
```

If that prints `OK`, the fixture still matches the schema. If it prints
anything else, the fixture is stale — regenerate it the same way it was
created (see `software/mobile-handover/tools/` for the pattern).

---

## What I'm NOT touching

So you don't waste time double-checking:

- I am not editing `software/server/src/**`. The code is the source of truth;
  the mobile package mirrors it.
- I am not editing `pipeline/`, `analysis/`, `reasoning/`, `pose/`, or any
  L2-plan-owned modules.
- I am not editing the L2 plan files yet (the questionnaire-removal edit to
  Plan 2 will happen in a follow-up pass and will be obvious in `git diff`).
- I am not touching tests.

---

## Document trail (for if you want the long version)

- `docs/research/pipeline-architecture-decision-2026-04-10.md` — the
  authoritative engineering-decision doc; supersedes `research-integration-report.md`
  pipeline section.
- `research/synthesis/deep-read-sensing-2026-04-10.md` (sibling research repo) — per-paper notes on the 8
  ML/vision papers.
- `research/synthesis/deep-read-biomech-2026-04-10.md` (sibling research repo) — per-paper notes on the 9
  biomechanics papers + the MSI cherry-pick verdict.
- `docs/operations/comms/2026-04-11-plan-changes-plain-english.md` — plain-English summary
  for the team.
- `docs/operations/comms/research-integration-report.md` — the original 2026-04-09 report with
  a revision pointer at the top.
- `software/mobile-handover/README.md` — the phone teammate's entry point.

---

*If anything in this note conflicts with what's in the repo, the repo wins
and I should be told. If anything in here is unclear, ping the user — both of
us are in the same conversation thread.*
