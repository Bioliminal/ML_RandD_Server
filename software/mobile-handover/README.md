# BioLiminal Mobile Hand-off Package

Everything the Flutter teammate (or their Claude Code) needs to ship the phone
client. Matches the server contract at `software/server/src/auralink/api/schemas.py`.
The contract is mostly the same across the demo and the post-demo 4-movement
product — where a demo-specific detail applies, it is flagged inline.

**Contents of this directory**

```
software/mobile-handover/
├── README.md                          ← you are here
├── interface/
│   ├── models.dart                    ← data classes mirroring the server schema
│   ├── pose_detector.dart             ← abstract pose-model interface
│   └── mediapipe_pose_detector.dart   ← reference implementation skeleton
├── schemas/
│   └── session.schema.json            ← JSON Schema exported from pydantic
├── fixtures/
│   ├── sample_valid_session.json            ← pose-only, overhead_squat (5 frames)
│   └── sample_bicep_curl_with_emg.json      ← pose + emg + consent worked example
├── model/
│   ├── DOWNLOAD.md                    ← where to get pose_landmarker_full.task
│   └── blazepose_landmark_order.md    ← canonical 33-landmark index table
└── tools/
    ├── export_schemas.py              ← regenerate session.schema.json
    └── post_sample.sh                 ← smoke-test upload against a running server
```

---

## 🎯 Demo context (2026-04-20 bicep curl)

The 2026-04-20 demo target is a **single bicep curl**, one 10-rep set. The
IC-2 contract is otherwise unchanged — the payload shape, the endpoints, and
the Dart dataclasses are the same as for the post-demo 4-movement product.
What's demo-specific:

- **`metadata.movement` = `"bicep_curl"`.** Added to `MovementType` alongside
  the four post-demo movements.
- **Demo server URL:** `https://bioliminal-demo.aaroncarney.me` (Cloudflare tunnel
  to the demo Windows workstation). Build with `--dart-define=SERVER_URL=https://bioliminal-demo.aaroncarney.me`.
- **Report content is sparse until `#12` lands.** `chain_observations` will
  come back empty for bicep curl until the rule YAML ships. Render gracefully.
- **sEMG in the payload is still pending `#13`.** Schema supports it; whether
  the demo upload carries `emg` depends on the `#13` decision and hardware
  readiness. Pose-only bicep curl sessions work end-to-end today.

---

## The contract in one paragraph

Capture bicep-curl (demo) or overhead-squat / single-leg-squat / push-up /
rollup (post-demo) video at **30 fps target, 25 fps floor**. Run MediaPipe
BlazePose Full on-device.
Convert every frame to a `PoseFrame` (33 landmarks, canonical BlazePose order,
visibility + presence in `[0,1]`). Bundle the frames into a `SessionPayload`
with metadata (movement, device, `"mediapipe_blazepose_full"`, measured fps,
UTC timestamp) and `POST` it as JSON to `https://<server>/sessions`. Optional
`emg: list[sEMGSample]` may be included — if so, `consent: ConsentMetadata`
is **required** (server returns 422 otherwise). Server responds with
`{session_id, frames_received}`. Fetch the analysis later via
`GET /sessions/{id}/report` (shape is the `Report` model in
`software/server/src/auralink/report/schemas.py`).

That's the whole protocol. Everything else in this package exists to make that
paragraph easy to implement.

---

## Step-by-step integration

### 1. Download the model (once)

```
cd model
open DOWNLOAD.md        # contains the Google CDN URL + expected SHA-256
```

Drop `pose_landmarker_full.task` into your Flutter project's
`assets/models/` directory and register it in `pubspec.yaml`:

```yaml
flutter:
  assets:
    - assets/models/pose_landmarker_full.task
```

### 2. Copy the Dart contract files

Copy all three files from `interface/` into your Flutter project:

- `lib/models/auralink_session.dart`  ← from `models.dart`
- `lib/pose/pose_detector.dart`       ← from `pose_detector.dart`
- `lib/pose/mediapipe_pose_detector.dart` ← from `mediapipe_pose_detector.dart`

Rename the imports to match your project layout. The classes are plain Dart —
no freezed, no codegen step. If you want freezed/json_serializable later,
swap them in behind the same interface without changing callers.

`models.dart` also ships `SEMGSample`, `SEMGEncoding`, `ConsentMetadata`,
`ConsentJurisdiction`, `RepScore`, and `SessionReport` so you don't have to
hand-author them later.

### 3. Pick a MediaPipe binding and wire `initialize()` / `detect()`

Three options, listed in order of expected effort (lowest first):

1. **`google_mlkit_pose_detection`** (ML Kit). Easiest. Returns the 33
   BlazePose landmarks in canonical order. Ship this unless you hit a blocker.
2. **Direct MediaPipe Tasks plugin** (if a maintained Flutter binding exists
   when you start). More flexible — lets you swap `.task` files without
   changing app code. Worth the effort if you want to A/B test model variants.
3. **Platform channels straight to the native MediaPipe Tasks API**
   (Android + iOS). Maximum control, maximum work. Don't do this unless
   option 2 turns out to be a dead end.

Whichever you pick, the reference skeleton in
`interface/mediapipe_pose_detector.dart` marks the two methods that need real
bodies: `initialize()` and `detect()`. Every other class in the package
already works as-is.

### 4. Capture + upload

Rough flow in Dart (not copy-paste; structure only):

```dart
final detector = MediaPipePoseDetector();
await detector.initialize();

final frames = <PoseFrame>[];
await for (final image in cameraController.imageStream) {
  final frame = await detector.detect(
    imageBytes: image.bytes,
    width: image.width,
    height: image.height,
    rotationDegrees: image.rotation,
    timestampMs: image.timestampMs,
  );
  if (frame != null) frames.add(frame);
}
await detector.dispose();

final payload = SessionPayload(
  metadata: SessionMetadata(
    movement: MovementType.bicepCurl, // or overheadSquat / etc post-demo
    device: await _deviceModel(),
    model: detector.modelId,
    frameRate: measuredFps,
  ),
  frames: frames,
  // emg + consent optional — see section below
);

final response = await http.post(
  Uri.parse('$serverBase/sessions'),
  headers: {'content-type': 'application/json'},
  body: jsonEncode(payload.toJson()),
);
```

`SessionPayload.toJson()` output matches `sample_valid_session.json` (pose
only) or `sample_bicep_curl_with_emg.json` (pose + emg + consent). If the
server accepts those fixtures, it'll accept your payload.

### 5. Smoke-test before touching UI

With the server running locally (or reachable through the demo tunnel):

```
cd tools
./post_sample.sh http://localhost:8000
```

You should see a `201 Created` response with a `session_id`. If you don't,
the fixture or your server is broken — fix before writing Flutter code.

`post_sample.sh` uses the pose-only fixture by default. For a pose + emg +
consent smoke test, curl the other fixture directly:

```
curl -sS -X POST -H 'content-type: application/json' \
  --data-binary @fixtures/sample_bicep_curl_with_emg.json \
  http://localhost:8000/sessions
```

---

## sEMG + consent

The schema has optional `emg: list[sEMGSample]` plus a required-when-emg
`consent: ConsentMetadata` block. The server rejects any session with `emg`
but no `consent` (HTTP 422).

Rationale: sEMG is biometrically re-identifiable at 90–97% from 0.8 s of
4-channel data — functionally a biometric identifier. Privacy regimes that
apply: Washington MHMDA (opt-in + private right of action), FTC HBNR, GDPR
Article 9. See the parent project CLAUDE.md § "Compliance & Privacy Posture"
for the full summary and
`research/synthesis/deep-read-semg-privacy-regulation-2026-04-15.md` for the
deep analysis.

### `SEMGSample` fields

- `channel: int` — 0 = biceps belly, 1 = brachioradialis for the demo.
- `timestamp_ms: int` — MCU-clock timestamp; reconcile with `PoseFrame.timestampMs`
  via the IC-1 clock-sync handshake.
- `value: double` — raw mV, normalized [0,1], or extracted-feature value.
- `encoding: SEMGEncoding` — `raw_mv` / `normalized_0_1` / `feature_rms` /
  `feature_mdf`. On-device feature extraction (RMS/MDF) is the de-identification
  strategy of record for privacy-conscious deployments. Encoding defaults to
  `normalized_0_1`.

### `ConsentMetadata` fields (required when `emg` is present)

- `consentVersion: String` — hash or semver of the specific policy text the
  user agreed to.
- `consentJurisdiction: ConsentJurisdiction` — `US-WA` / `US-other` / `EU` /
  `other`. Drives which downstream retention / deletion rules the server
  applies.
- `consentTimestamp: DateTime` — opt-in moment.
- `dataRetentionDays: int?` — null means "retain per server default policy
  for this jurisdiction."

For sessions without `emg`, consent is not required at this layer — pose data
is not "consumer health data" under MHMDA's definition.

---

## Known mobile-side wiring issues

Three issues in the current mobile app code that need fixing before the
phone can talk to the server successfully. The server is correct; these
are all client-side bugs.

### 1. `bioliminal_client.dart` baseUrl is a placeholder

Currently hardcoded to `https://api.bioliminal.ai`. Replace with a
build-time define:

```dart
static const String _baseUrl = String.fromEnvironment(
  'SERVER_URL',
  defaultValue: 'http://localhost:8000',
);
```

Then build with `--dart-define=SERVER_URL=https://bioliminal-demo.aaroncarney.me`
for the demo.

### 2. `fetchReport` calls the wrong path

Client calls `GET /reports/{id}` → server returns 404.
Server actually serves the report at `GET /sessions/{id}/report`.

Fix in the report fetch:

```dart
// before
final url = Uri.parse('$_baseUrl/reports/$sessionId');
// after
final url = Uri.parse('$_baseUrl/sessions/$sessionId/report');
```

### 3. `Report.fromJson` expects fields that the server doesn't return

Client currently expects `findings[]` and `practitioner_points[]`.
Server actually returns `metadata`, `movement_section`, `overall_narrative`.

The server's response shape (see `software/server/src/auralink/report/schemas.py`
on the server side or re-generate `session.schema.json` in this package):

```json
{
  "metadata": { "session_id": "...", "movement": "bicep_curl", "generated_at": "..." },
  "movement_section": {
    "summary": "...",
    "rep_scores": [ { "rep_index": 0, "quality": "good", "narrative": "..." }, ... ],
    "chain_observations": [ ... ]
  },
  "overall_narrative": "..."
}
```

Update the Dart `Report.fromJson` to map those fields. Until `#12` (rule YAML)
lands, `chain_observations` will be empty — render gracefully.

---

All three must be fixed before the phone can complete a full round-trip
against the demo server. Items 1 and 2 are mechanical; item 3 requires
matching the response schema exactly (the JSON schema in
`schemas/session.schema.json` and the fixtures in `fixtures/` are the
source of truth).

---

## What NOT to build on the phone

Clear scope boundary so we don't duplicate server work:

- ❌ **No chain reasoning, no risk flagging, no MSI classification.** Server
  only. Joyce 2023 and Van Dillen 2016 make clear this has to be centralized
  and auditable.
- ❌ **No onboarding questionnaire.** Team decision 2026-04-10. Body type gets
  auto-derived server-side (post-demo; not in bicep curl path).
- ❌ **No account wall** on the free flow. Low-friction onboarding is the
  whole pitch.
- ❌ **No 3D lifting, no WHAM, no OpenCap Monocular, no HSMR.** Those are all
  server-side — even on capable phones, we don't ship them in the app. For
  bicep curl the server itself doesn't use them either; elbow flexion from
  2D landmarks is sufficient.
- ❌ **No sEMG pairing UI for the demo.** Hardware team owns pairing
  (`esp32-firmware#1` / IC-1). Mobile only needs to know that if a session
  includes `emg`, it must also include `consent` — the app layer is agnostic
  about *how* the samples got there.

What the phone DOES own:

- ✅ Camera capture with framing guidance (real-time skeleton overlay with
  visibility-coloured landmarks — single biggest accuracy lever).
- ✅ Setup validation (progressive requirement checks: lighting, distance,
  full-body-in-frame).
- ✅ MediaPipe on-device inference.
- ✅ Rep counting and live cue text for user feedback during capture.
- ✅ Upload + retry + error UX.
- ✅ Report fetch + render.

---

## Regenerating the JSON schema

If the server-side pydantic models change, refresh the schema:

```
cd tools
./export_schemas.py
```

This writes `schemas/session.schema.json` from the live pydantic models.
Commit the refreshed file. The Dart classes are hand-written — update
`interface/models.dart` to match.

---

## Validation checklist before you consider this done

- [ ] `post_sample.sh` returns 201 against a local server (pose-only
      fixture).
- [ ] Posting `sample_bicep_curl_with_emg.json` returns 201 (pose + emg +
      consent round-trip).
- [ ] Posting an `emg`-bearing session WITHOUT `consent` returns 422 (the
      server enforces this; your client should surface the error cleanly).
- [ ] `SessionPayload.toJson()` round-trips through
      `SessionPayload.fromJson(jsonDecode(payload.toJson()))` byte-for-byte.
- [ ] Every rejected frame (no person detected, < 33 landmarks, bad
      confidence) is dropped silently — the server enforces "exactly 33
      landmarks per frame," partial frames will 422.
- [ ] `metadata.model` is always `"mediapipe_blazepose_full"` for this ship;
      no hardcoded values anywhere else.
- [ ] A 10-second capture produces ~300 frames at the 30 fps target (acceptable
      floor ~250 at 25 fps). Fewer than ~100 means something's wrong with
      capture throughput.
- [ ] Report screen renders gracefully when `chain_observations` is empty
      (expected for bicep curl until `#12` lands).

---

*Maintained alongside `software/server/src/auralink/api/schemas.py`. If you
see drift, the server schema wins — regenerate `session.schema.json` and
update `models.dart` to match.*
