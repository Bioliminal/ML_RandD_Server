# Mobile App → Server Wiring Fixes — Handover Brief (2026-04-16)

**Audience:** Kelsi (mobile owner) or a Claude Code helping her. Aaron's authoring this from the server side; changes land in `bioliminal-mobile-application`.
**Goal:** three concrete fixes so the phone app can actually talk to the demo server for the 2026-04-20 bicep curl demo. Without them, the phone will upload successfully but the report fetch will fail silently.
**Scope boundary:** client wiring only. No UI redesign, no consent flow, no sEMG upload — those are separate, tracked in gitlab.

---

## The three fixes

All three are in `bioliminal-mobile-application`.

### Fix 1 — Make the server base URL configurable

**File:** `lib/core/services/bioliminal_client.dart:9`

Today:
```dart
this.baseUrl = 'https://api.bioliminal.ai', // Placeholder
```

That URL doesn't resolve. The demo server will live behind a Cloudflare tunnel on a hostname Aaron will post on gitlab `ML_RandD_Server#11` once the tunnel is up.

**Recommended change:** read from `--dart-define` at build time. One line change:

```dart
this.baseUrl = const String.fromEnvironment(
  'SERVER_URL',
  defaultValue: 'http://localhost:8000',
),
```

Build / run with:
```
flutter run --dart-define=SERVER_URL=https://<tunnel-hostname>
```

**Why not a settings screen:** demo in 4 days. One string, one build flag. Ship it.

### Fix 2 — Correct the report endpoint path

**File:** `lib/core/services/bioliminal_client.dart:50`

Today:
```dart
final url = Uri.parse('$baseUrl/reports/$sessionId');
```

The server serves the report at `GET /sessions/{sessionId}/report`, not `/reports/{sessionId}`. Mobile will 404 today.

**Change to:**
```dart
final url = Uri.parse('$baseUrl/sessions/$sessionId/report');
```

### Fix 3 — Align the `Report` deserializer with what the server actually returns

**File:** `lib/domain/models.dart` — the `Report`, `Finding`, `Compensation`, `Citation` classes starting around line 328.

Today the mobile `Report.fromJson` expects this shape:
```json
{"findings": [...], "practitioner_points": [...], "pdf_url": "..."}
```

The server actually returns (see `software/server/src/auralink/report/schemas.py`):
```json
{
  "metadata": {"session_id": "...", "movement": "...", "captured_at_ms": 0},
  "movement_section": {
    "movement": "bicep_curl",
    "quality_report": {...},
    "chain_observations": [],
    "angle_series": {...},
    "normalized_angle_series": {...},
    "rep_boundaries": null,
    "per_rep_metrics": null,
    "within_movement_trend": null,
    "lift_result": {...},
    "skeleton_result": {...},
    "phase_boundaries": null,
    "movement_temporal_summary": null
  },
  "overall_narrative": "",
  "temporal_section": null,
  "cross_movement_section": null
}
```

**These are incompatible shapes.** `Report.fromJson(data)` will throw on any real response.

**For the demo, pick the cheap path:** rewrite mobile's `Report` to match the server's actual shape. The mobile app currently has no code reading `findings` / `practitioner_points` (those were scaffolded for a post-demo 4-movement flow that hasn't shipped), so rewriting the deserializer is a contained change. Minimum viable:

```dart
class Report {
  const Report({
    required this.sessionId,
    required this.movement,
    required this.chainObservations,
    required this.narrative,
  });

  final String sessionId;
  final String movement;
  final List<String> chainObservations;
  final String narrative;

  factory Report.fromJson(Map<String, dynamic> json) {
    final meta = json['metadata'] as Map<String, dynamic>;
    final movementSection = json['movement_section'] as Map<String, dynamic>;
    final rawObservations =
        (movementSection['chain_observations'] as List<dynamic>? ?? const []);
    return Report(
      sessionId: meta['session_id'] as String,
      movement: meta['movement'] as String,
      // Chain observations come back as full objects; keep just the display text.
      // Refine this once ML_RandD_Server#12 finalizes the observation schema.
      chainObservations: rawObservations
          .map((e) => (e as Map<String, dynamic>)['summary'] as String? ?? e.toString())
          .toList(),
      narrative: json['overall_narrative'] as String? ?? '',
    );
  }
}
```

Existing consumers of `Report.findings` / `Report.practitionerPoints` will break — audit `lib/features/report/` and either adapt the UI to the new shape or stub the old fields to empty lists for now. For the demo, a minimal report UI is fine: "Session complete — <narrative>" + a bulleted list of chainObservations.

`chainObservations` will be **empty** until ML_RandD_Server#12 lands (the bicep curl rule YAML). Wire the UI to render gracefully when the list is empty — don't block the report on non-empty rules.

### Optional follow-up (not demo-blocking)

- If/when we want a richer demo report, the server has a stub `SessionReport` (matrix §8.3 shape: `session_id`, `reps`, `total_reps`, `chain_observations`, `narrative`) in `software/server/src/auralink/api/schemas.py`. It's not yet wired to any route. Wiring would require a new endpoint like `GET /sessions/{id}/report/summary` and moving per-rep metrics into the pipeline — out of scope for demo unless #12 decides it's needed.

## What's explicitly OUT of scope

- Consent UI — tracked separately; sessions without sEMG need no consent block.
- sEMG upload wiring — blocked on `ML_RandD_Server#13` (schema decision) + BLE + signal-chain tasks.
- Authentication — demo has none.
- Retries / offline queueing beyond what's already in the upload flow.

## Acceptance — the phone app is demo-ready for server wiring when

- [ ] `flutter run --dart-define=SERVER_URL=https://<tunnel>` starts without compile errors.
- [ ] Capturing a bicep curl session and uploading returns a non-null `session_id`.
- [ ] `fetchReport(sessionId)` returns a non-null `Report` object (`chainObservations` may be empty until #12 lands — that's OK).
- [ ] The report screen renders something — even if it's just "Session complete: <movement>" — instead of crashing or showing a stale placeholder.

## Pointers

- Demo server standup + tunnel URL tracking: gitlab `ML_RandD_Server#11` (the tunnel URL will be posted there as a comment).
- IC-2 schema reference for payload shape: `mobile-handover/interface/models.dart` in the mobile repo (on `docs/ic2-schema-lock-2026-04-16` branch → MR !8 pending review). That package also has `fixtures/sample_bicep_curl_with_emg.json` as a worked example — valid payload, confirmed to round-trip against the server.
- Full schema JSON if the Dart types are confusing: `mobile-handover/schemas/session.schema.json`.

---

*Questions → Aaron. Don't improvise bigger scope; the goal is a green end-to-end demo, not a redesigned mobile architecture.*
