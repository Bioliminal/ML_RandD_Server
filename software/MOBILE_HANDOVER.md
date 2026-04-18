# Mobile Handover — Moved

The mobile handover package used to live at `software/mobile-handover/` in
this repo. It has moved to the ops repo so both server and mobile teams
pull from a single coordination source rather than having RnD_Server
mirror manually into the Flutter repo.

**New location:** `bioliminal-ops/operations/handover/mobile/`

- Contract docs + README: `operations/handover/mobile/README.md`
- Per-stage phone-vs-server ownership + adaptive sketch:
  `operations/handover/mobile/what-runs-where.md`
- JSON schemas (session + report): `operations/handover/mobile/schemas/`
- Dart interface files + fixtures: `operations/handover/mobile/interface/`,
  `.../fixtures/`
- Schema export tool (runs against live pydantic models in this repo):
  `operations/handover/mobile/tools/export_schemas.py`

When the server pydantic models change, regenerate:

```bash
cd ../bioliminal-ops/operations/handover/mobile/tools
python export_schemas.py   # auto-finds RnD_Server as a sibling checkout
```

The mobile team owns pulling the updated handover into their own repo.
