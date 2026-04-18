# BlazePose Landmark Reference (Server)

Internal reference for the BlazePose 33-landmark ordering assumed by the BioLiminal server's analysis pipeline. The canonical model interface contract is `custom_model_contract.md` (owned by the Flutter team). This doc is the server's view of the landmark schema.

## Canonical Spec — BlazePose 33 Landmarks

### Input
- **Shape:** `[1, 256, 256, 3]` float32 for `BlazePose Full`, `[1, 192, 192, 3]` for `BlazePose Lite`
- **Normalization:** `pixel / 255.0` → range `[0, 1]`
- **Color order:** RGB, not BGR

### Output
- **Landmarks tensor:** shape `[1, 195]` flattened, reshapes to `[1, 39, 5]`
  - 39 landmarks (33 body + 6 auxiliary)
  - 5 values per landmark: `[x, y, z, visibility, presence]`
- **Pose presence flag:** scalar, sigmoid'd, `≥0.5` = person detected
- **Segmentation mask:** optional, ignored downstream
- **Heatmaps:** intermediate, ignored downstream

### Coordinate Space
- `x`, `y`: input pixel coordinates (`[0, 256]` Full, `[0, 192]` Lite). **Not normalized** to `[0, 1]` at model output — Flutter app rescales to `[0, 1]` before sending to server.
- `z`: depth relative to hip midpoint in the same pixel units. Not meters.

### Visibility & Presence
- **Already sigmoid'd** in model output, range `[0, 1]`. Do not apply sigmoid again.
- `visibility` = landmark is in-frame and unoccluded
- `presence` = landmark is detected at all

### Landmark Ordering
Landmarks 0-32 follow the canonical BlazePose body ordering:

| Index | Name |
|-------|------|
| 0 | nose |
| 1 | left_eye_inner |
| 2 | left_eye |
| 3 | left_eye_outer |
| 4 | right_eye_inner |
| 5 | right_eye |
| 6 | right_eye_outer |
| 7 | left_ear |
| 8 | right_ear |
| 9 | mouth_left |
| 10 | mouth_right |
| 11 | left_shoulder |
| 12 | right_shoulder |
| 13 | left_elbow |
| 14 | right_elbow |
| 15 | left_wrist |
| 16 | right_wrist |
| 17 | left_pinky |
| 18 | right_pinky |
| 19 | left_index |
| 20 | right_index |
| 21 | left_thumb |
| 22 | right_thumb |
| 23 | left_hip |
| 24 | right_hip |
| 25 | left_knee |
| 26 | right_knee |
| 27 | left_ankle |
| 28 | right_ankle |
| 29 | left_heel |
| 30 | right_heel |
| 31 | left_foot_index |
| 32 | right_foot_index |

Landmarks 33-38 are auxiliary (used internally by BlazePose for next-frame ROI prediction). They are ignored by BioLiminal.

Reference: https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/pose.md

## Server-Side Contract

The server consumes JSON sessions matching the pydantic schema in `bioliminal.api.schemas.Session`:

```json
{
  "metadata": {
    "movement": "overhead_squat",
    "device": "Pixel 8",
    "model": "mediapipe_blazepose_full",
    "frame_rate": 30.0,
    "captured_at": "2026-04-09T14:32:00Z"
  },
  "frames": [
    {
      "timestamp_ms": 0,
      "landmarks": [
        {"x": 0.52, "y": 0.31, "z": -0.08, "visibility": 0.98, "presence": 0.99}
      ]
    }
  ]
}
```

Landmark coordinates are normalized to `[0, 1]` before sending to the server. The Flutter app is responsible for rescaling from model pixel-space to `[0, 1]` frame-space.

## If a Custom Model Is Introduced

The canonical Flutter-side model interface contract is `custom_model_contract.md` (owned by the Flutter team). If a custom .tflite model is introduced, that doc specifies the 8-question spec and mapping-layer requirements. This server-side doc only documents what the server assumes at the schema level: BlazePose 33-landmark ordering, normalized coordinates, sigmoid'd visibility and presence.

## Why This Matters

Every downstream reference in BioLiminal — joint angle math, chain reasoning, threshold tables, test fixtures, research paper citations — assumes BlazePose 33-landmark ordering. Deviating creates permanent tax on every future integration.
