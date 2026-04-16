# ML Models — Reference Copies

Local-only upstream model clones for inspection and future inference work. **Contents of subdirectories are gitignored** (`ml/models/*/` in `.gitignore`); only this README is tracked. Weights, code, and checkpoints live on-disk under each subdir.

Each subdir has a `LOCAL_README.md` (our notes) alongside the upstream `README.md` (the repo's own docs).

## Inventory

| Subdir | Model | Size | License | Role in pipeline | Status |
|---|---|---|---|---|---|
| `mediapipe-blazepose/` | MediaPipe BlazePose (lite/full/heavy) | 44 MB | Apache 2.0 | **Ship** — on-device 2D keypoints | Weights present |
| `movenet-thunder/` | MoveNet Thunder + MoveNet multipose Lightning (TF Lite) | 99 MB | Apache 2.0 | Alternate 2D detector (A/B only) | Weights present |
| `hrnet-small/` | HRNet-small reference implementation | 16 MB | MIT (code); research license (weights) | Deferred upgrade tier | Code only — weights behind manual Google Drive auth |
| `wham/` | WHAM — monocular → world-grounded SMPL 3D pose | 6.1 GB | Max Planck research (non-commercial) | **Prep now** — server-side premium pipeline | Code + all 6 checkpoints present; SMPL body model still gated |
| `opencap-monocular/` | OpenCap Monocular — SMPL pose → OpenSim IK/ID → kinetics | 61 MB | PolyForm Noncommercial 1.0.0 | **Prep now** — server-side premium pipeline | Code only — weights need SimTK/SMPL registrations |
| `hsmr/` | HSMR — SKEL-based human mesh recovery | 17 MB | MIT (code); research (SKEL body model) | Deferred — rollup-only branch, blocked on 4-movement protocol confirmation | Code only — SKEL body model gated |
| `sabo-beighton/` | Sabo 2026 Beighton hypermobility scorer | <1 MB | — | Deferred past v1 | Paper-only; no public code as of 2026-04-15 |

**Total on-disk:** ~6.3 GB

## License registrations still required (human-gated)

Before any of the server-side models can actually run inference end-to-end, the following registrations must be completed manually by a human. None can be automated.

| Registration | URL | Blocks | Who |
|---|---|---|---|
| **SMPL body model** | https://smpl.is.tue.mpg.de/ | WHAM + OpenCap Monocular visualization | Aaron |
| **SMPLify** | https://smplify.is.tue.mpg.de/ | WHAM full demo (`SMPL_NEUTRAL.pkl`) | Aaron |
| **SKEL body model** | https://skel.is.tue.mpg.de/login.php | HSMR inference | Aaron (defer until rollup confirmed) |
| **SimTK OpenCap DUA** | https://simtk.org/projects/opencap | OpenCap public dataset (calibration reference) + hosted endpoint access | Aaron (Action #2 in pipeline decision) |
| **OpenCap hosted endpoint** | https://www.opencap.ai | Test before committing to self-host (pipeline decision §2.1) | Aaron |

After the SMPL registrations, run `bash ml/models/wham/fetch_demo_data.sh` from the WHAM dir — it will prompt for both sets of credentials and fetch the remaining body-model files.

## Decision-doc cross-references

Model choices and rationale are in `docs/research/pipeline-architecture-decision-2026-04-10.md`. Key points:

- **Ship path:** `MediaPipe BlazePose Full → WHAM → OpenCap Monocular → rule reasoner` (§2)
- **Hosted before self-host:** OpenCap Monocular runs against the hosted `opencap.ai` endpoint first; self-hosting is the launch target, not current work (§2.1 + Action #2)
- **HSMR is rollup-only:** blocked on Rajiv confirming whether rollup is in the 4-movement protocol (§2.1 + Action #7)
- **Not adopted:** MotionBERT, TCPFormer, ViTPose, true output-ensembling (§2.1)
- **Deferred past v1:** HRPose, Sabo Beighton, HSMR (conditional on rollup)

## Why the subdirs are gitignored

Upstream model repos are multi-GB, bring their own `.git/` histories, and are reference-only for the BioLiminal team. Committing them would bloat `ML_RandD_Server` to tens of GB and conflate upstream history with ours. The committed surface is this index README only; the actual clones live on-disk for local inspection and can be re-fetched from the URLs below.

## Re-fetching from scratch

If `ml/models/` is wiped and you need to regenerate it:

```bash
# Phone / alternate 2D (Apache 2.0, no registration)
mkdir -p ml/models/mediapipe-blazepose ml/models/movenet-thunder
python3 -c "import urllib.request; urllib.request.urlretrieve('https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task', 'ml/models/mediapipe-blazepose/pose_landmarker_full.task')"
# ... (see each subdir's LOCAL_README.md for the exact URLs)

# WHAM (research license)
git clone --depth=1 https://github.com/yohanshin/WHAM.git ml/models/wham/
# Then: pip install --user gdown && bash ml/models/wham/fetch_demo_data.sh
# (requires SMPL + SMPLify registrations completed)

# OpenCap Monocular
git clone --depth=1 --branch main https://github.com/utahmobl/opencap-monocular ml/models/opencap-monocular/

# HSMR
git clone --depth=1 https://github.com/IsshikiHugh/HSMR ml/models/hsmr/
```

Full per-model instructions in each subdir's `LOCAL_README.md`.
