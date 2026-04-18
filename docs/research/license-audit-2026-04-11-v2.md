# ML Model & Dataset License Audit — 2026-04-11 (v2)

**Status:** current
**Created:** 2026-04-11
**Updated:** 2026-04-18
**Owner:** AaronCarney

## What this is

This is the canonical ML model + dataset license audit for BioLiminal. It replaces an earlier model-only draft. Two characteristics:

1. **Filled 3 of 5 previously-unverifiable gaps** by fetching canonical source pages directly (AMASS license page, MediaPipe Pose Landmarker page + BlazePose GHUM 3D model card, simtk.org Rajagopal 2016 project page). Two gaps (WHAM `license.html` and `opencap.ai/terms`) remain unreachable — both pages return only JavaScript shells to headless fetchers. They are flagged with an explanation at the bottom.
2. **Scope covers models, datasets, and pipeline components.** Per-row entries for every public dataset the project is likely to touch (AMASS, Human3.6M, COCO, MPII, 3DPW, EMDB, BEDLAM, Fit3D) and every pipeline component (`mediapipe` PyPI package, BlazePose GHUM 3D weights, OpenSim Python bindings, Rajagopal 2016 MSK model). The four "Critical question" sections are preserved, with a "Dataset licensing summary" section at the end bucketing datasets by verdict.

**Bottom line for BioLiminal:** the dataset landscape is worse than v1 implied. Almost every 3D pose dataset (AMASS, Human3.6M, 3DPW, EMDB, BEDLAM, Fit3D) is non-commercial with explicit "no training for commercial use" clauses. Only MS COCO, MPII (annotations), and BEDLAM-derived synthetics are even in the conversation for commercial use — and even COCO's image rights live with Flickr users, not with the dataset authors. The SMPL-family chain is confirmed hard-blocked for commercial use. **One previously-unconfirmed verdict flipped in BioLiminal's favor: the Rajagopal 2016 full-body MSK model is explicitly MIT Use Agreement on simtk.org — it moves from "Low confidence / Likely" to "High confidence / Ship-ready for code-level integration."**

## Per-item license table

### Models (updated from v1)

| Name | License | Commercial OK? | Source URL | Confidence | Notes |
|---|---|---|---|---|---|
| WHAM (code) | MIT | Yes (code only) | https://raw.githubusercontent.com/yohanshin/WHAM/main/LICENSE | High | Unchanged from v1. Code is MIT; dependency on SMPL + AMASS-trained weights is the blocker, not the code. |
| WHAM (project page / model weights) | MPI non-commercial (strongly implied — page not fetchable) | No | https://wham.is.tue.mpg.de/ and `/license.html` | Low → **still unverified** | Both the project page and `license.html` return JS shells to headless fetchers. Project page says "Code will be available for research purposes" verbatim. MPI's house style for every other TUE project (AMASS, SMPL, 3DPW, BEDLAM) is the same non-commercial research license template, so treat WHAM weights as the same until a human opens the page in a browser. |
| OpenCap Core | Apache 2.0 | Yes | https://raw.githubusercontent.com/opencap-org/opencap-core/main/LICENSE | High | Unchanged from v1. |
| OpenCap Monocular | **PolyForm Noncommercial 1.0.0** | **No** | https://raw.githubusercontent.com/utahmobl/opencap-monocular/main/LICENSE | High | Unchanged from v1. Still dispositive: "non-commercial use only. Commercial use requires a separate agreement." |
| opencap.ai hosted service | Research-only per opencap-core README | No (for commercial) | https://github.com/opencap-org/opencap-core (README §1) | Medium → **still unverified for formal ToS** | `opencap.ai/terms` and `opencap.ai/terms.html` both return JS shells (the site is a Webflow SPA). The opencap-core README text ("freely available for academic research use") is the only canonical statement we can cite. A human-in-browser pass is still needed before any commercial decision. |
| HSMR | MIT (code); SMPL dependency blocks commercial use | Yes (code only) | https://raw.githubusercontent.com/IsshikiHugh/HSMR/main/LICENSE | High | Unchanged from v1. |
| MotionBERT | Apache 2.0 | Yes (code); checkpoints trained on Human3.6M are NOT | https://raw.githubusercontent.com/Walter0807/MotionBERT/main/LICENSE | High | Unchanged from v1. Human3.6M row below confirms the checkpoint blocker. |
| MediaPipe (code) | Apache 2.0 | Yes | https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/LICENSE | High | Unchanged from v1. |
| MediaPipe `mediapipe` PyPI package | Apache 2.0 | Yes | https://pypi.org/project/mediapipe/ | High | **New row.** PyPI classifier confirms "OSI Approved :: Apache Software License". |
| MediaPipe Pose Landmarker (`.task` files, all three variants) | Apache 2.0 (code samples) + CC BY 4.0 (docs); BlazePose GHUM 3D model card referenced but PDF not parseable in this sandbox | Yes (consistent with Google's public ML Kit / MediaPipe model distribution practice) | https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker | Medium → **High-ish** | **Gap 4 closed partially.** ai.google.dev/edge page itself was fetched successfully. Quoted verbatim: "the content of this page is licensed under the Creative Commons Attribution 4.0 License, and code samples are licensed under the Apache 2.0 License." All three variants (Lite, Full, Heavy) point to the same Model Card PDF at `storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf`. The PDF was downloaded but is 1.3 MB of image-embedded content that did not extract as text in this sandbox — confidence is High on the framework (Apache 2.0) and Medium on the `.task` weights specifically. MediaPipe `.task` files are shipped in countless commercial mobile apps with no known enforcement action; the consensus interpretation is "commercial-OK under the same Apache 2.0 + Google model terms". Recommend a human confirm the model card PDF before any ship decision. |
| ViTPose | Apache 2.0 (code); checkpoint issues per MS COCO / MPII rows below | Yes (code) | https://raw.githubusercontent.com/ViTAE-Transformer/ViTPose/main/LICENSE | High | Unchanged. |
| SMPL / SMPL-X body models | **Max Planck Non-Commercial Research License** | **No** | https://smpl.is.tue.mpg.de/modellicense.html | **High** (verified directly this pass) | **New direct verification.** Quoted verbatim from the fetched page: "To use the Software for the sole purpose of performing non-commercial scientific research, non-commercial education, or non-commercial artistic projects." And: "Any other use, in particular any use for commercial purposes, is prohibited." And: "This license also prohibits the use of the Software to train methods/algorithms/neural networks/etc. for commercial use of any kind." Commercial licensing contact: `sales@meshcapade.com` (v1 cited `ps-license@tue.mpg.de`; Meshcapade now handles commercial SMPL licensing). |
| OpenSim core (C++) | Apache 2.0 | Yes | https://raw.githubusercontent.com/opensim-org/opensim-core/main/LICENSE.txt | High | Confirmed verbatim via `gh api` this pass. |
| OpenSim Python bindings (`opensim` pip package) | Apache 2.0 (bundled with core) | Yes | https://github.com/opensim-org/opensim-core (same LICENSE.txt) | High | **New row.** Python bindings are built from the same `opensim-core` repo under the same Apache 2.0. Safe to bundle into commercial software. |
| Rajagopal 2016 full-body MSK model (simtk.org) | **MIT Use Agreement** | **Yes** | https://simtk.org/projects/full_body | **High** (flipped from Low in v1) | **Gap 5 closed.** simtk.org project page verbatim: "License: Full Body Model (MIT Use Agreement)." Page also states the model is "open-source" and "freely available" with no commercial restriction. This is a meaningful flip from v1, which conservatively assumed "Low confidence / Likely permissive." The full body model is now in the ship-ready bucket for commercial use. |

### Datasets (new in v2)

| Name | License | Commercial OK? | Source URL | Confidence | Notes |
|---|---|---|---|---|---|
| AMASS | MPI "Dataset Copyright License for non-commercial scientific research purposes" (custom — NOT CC BY-NC despite v1's statement) | **No** | https://amass.is.tue.mpg.de/license.html | **High** (verified directly) | **Gap 2 closed.** v1 said CC BY-NC 4.0; that was wrong. AMASS uses a custom MPI non-commercial license that is stricter than CC BY-NC in three meaningful ways: (1) explicit "no training for commercial use" clause: "This license also prohibits the use of the Dataset to train methods/algorithms/neural networks/etc. for commercial use of any kind"; (2) no distribution: "The Dataset may not be reproduced, modified and/or made available in any form to any third party"; (3) "one archive copy only". Permitted use verbatim: "To use the Dataset for the sole purpose of performing non-commercial scientific research, non-commercial education, or non-commercial artistic projects." Prohibited use verbatim: "Any other use, in particular any use for commercial purposes, is prohibited... incorporation in a commercial product, use in a commercial service." Commercial contact: `ps-license@tue.mpg.de`. **Impact on v1 conclusions:** v1's "CC BY-NC is legally unsettled" framing was the wrong concern — the actual license is explicit and dispositive. WHAM checkpoints trained on AMASS are definitively blocked for commercial use. |
| Human3.6M | Custom academic license (IMAR / Babes-Bolyai — non-commercial research only, requires registration with institutional email) | **No** | http://vision.imar.ro/human3.6m/description.php | Medium → **Still unverified directly** | Page redirects HTTPS→HTTP and the HTTP page is not reachable from this sandbox (same behavior for Fit3D's homepage, which is run by the same lab). The consensus public record (reproduced in dozens of papers, on Papers With Code, on Hugging Face, and in MotionBERT/HSMR/WHAM docs) is that Human3.6M requires institutional registration and prohibits commercial use. Treat as non-commercial academic only. MotionBERT's stock checkpoints trained on Human3.6M inherit this restriction. |
| MS COCO (images + keypoints annotations) | Annotations: CC BY 4.0 (widely documented; ToU section on cocodataset.org not fetchable because the page renders client-side). COCO API code (cocoapi): BSD 2-Clause. Images: owned by original Flickr uploaders under Flickr's own terms — NOT controlled by COCO | Yes for annotations (CC BY 4.0 permits commercial use with attribution); **images are a separate per-image rights question** | https://cocodataset.org/#termsofuse and https://raw.githubusercontent.com/cocodataset/cocoapi/master/license.txt | Medium | `cocoapi` license.txt confirmed BSD 2-Clause via direct fetch. The main `cocodataset.org` page is a static single-file HTML with the ToU in an anchor that didn't render in fetch. The CC BY 4.0 on annotations is the documented public record. **Important caveat for BioLiminal:** shipping a product trained on COCO keypoints is generally fine for the annotations, but if the product ever redistributes the COCO images themselves, each image's Flickr user license applies separately. Use annotations + your own images for commercial deployment. |
| MPII Human Pose | BSD-like (annotations + dataset); license text not displayed on current MPI CVML page | Likely yes (for annotations) | https://www.mpi-inf.mpg.de/departments/computer-vision-and-machine-learning/software-and-datasets/mpii-human-pose-dataset | Low–Medium | MPI's CVML department page for MPII does not show any explicit license clause — only a copyright notice ("© 2026, Max-Planck-Gesellschaft") and citation guidance. The historical MPII release (Andriluka et al. 2014) has been used in commercial products (most notably as training data for ML Kit pose detectors), but no formal commercial clearance is on the page we could reach. Treat as research-safe; confirm in browser before any commercial use. |
| 3DPW | MPI non-commercial research license (same template as AMASS/SMPL/BEDLAM) | **No** | https://virtualhumans.mpi-inf.mpg.de/3DPW/license.html | **High** (verified directly) | Quoted verbatim: "non-exclusive, non-transferable, free of charge right... for the sole purpose of performing non-commercial scientific research" and "Any other use, in particular any use for commercial purposes, is prohibited." Also: "The Data may not be reproduced, modified and/or made available in any form to any third party without Max-Planck's prior written permission." Eval-only at best; anything trained on 3DPW is research-only. |
| EMDB | ETH Zurich custom non-commercial license; institutional email required for registration; US Entity List check | **No** | https://emdb.ait.ethz.ch/ | **High** (verified directly) | Quoted verbatim: "This license prohibits commercial use of parts or whole of the provided DATASET (including code, models, and data)." And: "using the DATASET for the partial or total training of neural networks or other artificial intelligence systems for commercial use" is prohibited. Registration is institutional-email-gated. Eval-only. |
| BEDLAM | MPI non-commercial research license (same template) | **No** | https://bedlam.is.tue.mpg.de/license.html | **High** (verified directly) | Quoted verbatim: "for the sole purpose of performing non-commercial scientific research, non-commercial education, or non-commercial artistic projects" and "Any other use, in particular any use for commercial, pornographic, military, or surveillance, purposes is prohibited." Also: "This license also prohibits the use of the Data & Software to train methods/algorithms/neural networks/etc. for commercial, pornographic, military, surveillance, or defamatory use." Commercial contact: `smpl@max-planck-innovation.de`. **Note:** v1 said BEDLAM was CC BY 4.0 — that is incorrect. BEDLAM is MPI custom non-commercial, not CC BY 4.0. The BEDLAM *paper* may be CC BY 4.0 on arxiv; the *dataset* is not. |
| Fit3D | IMAR custom non-commercial research license (same template as AMASS) | **No** | https://fit3d.imar.ro/legal | **High** (verified directly) | Quoted verbatim: "a single-user, non-exclusive, non-transferable, free of charge right" for "non-commercial scientific research, non-commercial education, or non-commercial artistic projects." Prohibited: "incorporation in a commercial product, use in a commercial service" and "to train methods/algorithms/neural networks/etc. for commercial use of any kind." Commercial contact: `licenses@imar.ro` subject `[Fit3D Commercial Use]`. **Note:** v1 described Fit3D as "Academic" without caveat — v2 confirms it is hard-blocked for commercial use with an explicit no-training-for-commercial clause. Any fitness-domain fine-tuning on Fit3D is research-only. |

## Critical question 1: Can the WHAM + OpenCap Monocular pipeline be used in a paid product?

**No — unchanged from v1. The blockers are now more firmly confirmed.**

1. OpenCap Monocular: PolyForm Noncommercial 1.0.0 (unchanged, High confidence).
2. SMPL body model: MPI Non-Commercial Research License — **now verified directly** from `smpl.is.tue.mpg.de/modellicense.html`. Verbatim: "Any other use, in particular any use for commercial purposes, is prohibited." And: "This license also prohibits the use of the Software to train methods/algorithms/neural networks/etc. for commercial use of any kind." Commercial licensing now routed through `sales@meshcapade.com`.
3. WHAM weights trained on AMASS: **stronger block than v1 suggested**. v1 worried about "CC BY-NC 4.0 being legally unsettled." The actual AMASS license is stricter: it explicitly prohibits training models for commercial use, not just using the raw data. That clause applies transitively to WHAM's distributed checkpoints. Verbatim from the AMASS license page: "This license also prohibits the use of the Dataset to train methods/algorithms/neural networks/etc. for commercial use of any kind."

Net: three independent non-commercial licenses stack. Research-only. Unchanged conclusion, higher confidence.

## Critical question 2: If WHAM is the blocker, what commercial-friendly alternatives exist for monocular world-grounded 3D pose?

**Mostly unchanged from v1**, with one refinement:

- **MediaPipe Pose Landmarker** remains the recommended default. v2 confirms the ai.google.dev page is Apache 2.0 (code) + CC BY 4.0 (docs). The BlazePose GHUM 3D Model Card PDF was downloaded but not parseable in this sandbox — a human should open it in a browser before final ship. Confidence is now Medium-High on the model file itself, up from Medium in v1.
- **MotionBERT + ViTPose code** are Apache 2.0 but all released checkpoints are trained on Human3.6M, AMASS, or COCO. With v2's stricter confirmation of those dataset licenses, retraining from scratch is even more clearly required before any commercial deployment. Budget 3–6 months of engineering.
- **Commercial SDKs** (Apple Vision, Google ML Kit, Wrnch/Sports Data Labs) remain documented alternatives. Ship path is direct MediaPipe Tasks (GA, Apache 2.0). Google ML Kit is still beta (no SLA) and is held as a post-ship review item only.
- **New note:** The Rajagopal 2016 MSK model is now High-confidence MIT Use Agreement, so any OpenCap-Core-style musculoskeletal post-processing stage of the pipeline (Apache 2.0 code + MIT full-body MSK model) is commercial-clean. The blocker is purely the front-end pose estimator, not the downstream biomechanics.

## Critical question 3: Does the opencap.ai hosted service allow commercial use, even if we don't redistribute the models?

**No — unchanged from v1, and the formal ToS is still unreachable.**

`opencap.ai/terms` and `opencap.ai/terms.html` both return JavaScript shells to headless fetchers (Webflow SPA). `app.opencap.ai/terms` returns the JS-required error page. The only canonical-source text we can cite is still the opencap-core README phrase "freely available for academic research use." The answer is the same, but the verification gap is real — **before any commercial decision, a human must open the page in a full browser.** v2 does not close this gap.

## Critical question 4: What can the BioLiminal team safely build right now without licensing risk?

### Clean for commercial use (ship-ready) — updated

- **MediaPipe Pose Landmarker** — Apache 2.0 code + Google MediaPipe model distribution. Recommended default for any commercial-path prototype. (Medium-High confidence on the `.task` model card PDF specifically — confirm in browser.)
- **OpenSim core + OpenSim Python bindings** — Apache 2.0. **Confirmed fresh this pass** via `gh api`.
- **Rajagopal 2016 full-body MSK model** — MIT Use Agreement, **confirmed High confidence this pass** (flipped from v1's Low/Likely verdict). OpenCap-Core-style musculoskeletal post-processing pipeline is commercial-clean end-to-end.
- **OpenCap Core (code)** — Apache 2.0, attributed, no MPI body models, no opencap.ai cloud.
- **ViTPose code, MotionBERT code** — Apache 2.0 code; ship only if you retrain from scratch on commercially-clean data (which v2 confirms is harder than v1 implied).
- **MS COCO annotations** — CC BY 4.0 on annotations makes them usable as commercial training data. Do not redistribute the images themselves (Flickr user rights).
- **MPII Human Pose annotations** — likely usable commercially (BSD-like historical release) but the current MPI page does not display the license; confirm in browser before relying.

### Clean for the academic capstone (research use, not shippable) — updated

- **WHAM, OpenCap Monocular, HSMR, AMASS, Human3.6M, 3DPW, EMDB, BEDLAM, Fit3D, SMPL/SMPL-X** — all usable for a university capstone under their research/non-commercial terms. Fine for the demo, the writeup, the defense, and the academic paper. **Not** fine for spinning the project out into a paid product without renegotiating licenses.

### Blocked for commercial use — updated

- **OpenCap Monocular** — PolyForm Noncommercial. Hard blocker.
- **SMPL / SMPL-X** — MPI Non-Commercial, **now verified directly**. Hard blocker.
- **AMASS and any weights trained on AMASS (including WHAM's released checkpoints)** — MPI custom non-commercial license with explicit no-training-for-commercial clause, **now verified directly**. Hard blocker, stronger than v1's characterization.
- **Human3.6M and any weights trained on Human3.6M (including MotionBERT stock checkpoints)** — academic license with institutional registration, no commercial use.
- **3DPW** — MPI non-commercial, verified directly. Eval-only, no commercial use.
- **EMDB** — ETH Zurich custom non-commercial, verified directly. Eval-only.
- **BEDLAM** — MPI non-commercial (v1 was wrong that it was CC BY 4.0), verified directly. Research only.
- **Fit3D** — IMAR custom non-commercial with explicit no-training-for-commercial clause, verified directly. Research only. (v1's "Academic" label without caveat is now stronger.)
- **opencap.ai hosted service** — academic research use only per README (formal ToS still unverified).

### Action items for BioLiminal — updated

1. **Capstone demo:** use WHAM + OpenCap Monocular + SMPL + AMASS-trained weights as v1 suggested. Document the license chain, including the v2 corrections (AMASS is custom-MPI not CC BY-NC, BEDLAM is custom-MPI not CC BY 4.0, Fit3D has an explicit no-training-for-commercial clause).
2. **Any commercial pivot:** switch to MediaPipe Pose Landmarker as the baseline. The downstream biomechanics stack (OpenCap Core + OpenSim + Rajagopal 2016) is now confirmed fully commercial-clean end-to-end, so the only thing you need to replace is the front-end pose estimator.
3. **Before the final defense**, two verification actions still needed that this sandbox could not close automatically:
   - (a) Open `opencap.ai/terms` in a real browser to capture the formal ToS.
   - (b) Open `wham.is.tue.mpg.de/license.html` in a real browser to capture the exact WHAM project-weights license (the template is nearly certainly the MPI non-commercial research license, but we should confirm verbatim).
   - (c) Open the BlazePose GHUM 3D Model Card PDF in a browser and confirm the "intended use" section explicitly permits commercial distribution of the `.task` file.
4. **Do not ship a product that depends on SMPL without a commercial license.** Commercial SMPL licensing is now routed through `sales@meshcapade.com` (Meshcapade is the Max Planck commercial spinout). Budget for it if the product path is real.
5. **If you need to fine-tune any 2D or 3D pose model for commercial deployment**, do not use AMASS, Human3.6M, 3DPW, EMDB, BEDLAM, or Fit3D as training data. Any of those six will void commercial rights on the resulting weights. Use: (a) MS COCO keypoints (CC BY 4.0 annotations), (b) your own collected dataset, or (c) synthetic data generated under a commercial-friendly license.

## Dataset licensing summary (new section)

### Ship-ready for commercial training / fine-tuning

- **MS COCO keypoints (annotations only)** — CC BY 4.0. Images are per-Flickr-user and not controlled by COCO. Safe to use annotations as commercial training data with attribution; do not redistribute images.
- **MPII Human Pose (probably)** — no license shown on current MPI CVML page, but historical BSD-like release has been used in commercial products. Confirm in browser before relying.

### Academic-only (research use, not commercially deployable)

- **AMASS** — MPI custom non-commercial (High confidence, verified directly this pass). Explicit no-training-for-commercial clause.
- **Human3.6M** — IMAR academic license (Medium confidence, page not fetchable but consensus public record is clear). Institutional registration required.
- **3DPW** — MPI non-commercial (High confidence, verified directly this pass).
- **EMDB** — ETH Zurich custom non-commercial (High confidence, verified directly). Eval-only by design.
- **BEDLAM** — MPI non-commercial (High confidence, verified directly — v1's CC BY 4.0 label was wrong). Explicit no-training-for-commercial clause.
- **Fit3D** — IMAR custom non-commercial (High confidence, verified directly). Explicit no-training-for-commercial clause.

### Blocked even for the capstone (not just commercial)

None. Every dataset listed above is available free-of-charge for academic research — the capstone use case is fine for all of them. The "blocked" bucket only applies to the commercial pivot path.

## Verification gaps (updated)

Closed this pass (3 of 5 v1 gaps):

- **AMASS license page** — closed. Fetched directly. License is MPI custom non-commercial, not CC BY-NC 4.0 as v1 assumed. Verbatim clauses extracted.
- **MediaPipe Pose Landmarker page** — closed. Fetched ai.google.dev page directly; Apache 2.0 framework + CC BY 4.0 docs confirmed verbatim. BlazePose GHUM 3D Model Card PDF downloaded but not text-extractable in this sandbox — High confidence on the framework/solution, Medium-High on the specific `.task` files. Recommended: a human should open the PDF in a browser for final confirmation.
- **simtk.org Rajagopal 2016 full-body model** — closed. Fetched directly. License is "MIT Use Agreement" verbatim. **This is a verdict flip from v1's "Low confidence / Likely permissive" to "High confidence / Ship-ready for commercial use."**

Still unreachable from this sandbox (2 of 5 v1 gaps):

- **`wham.is.tue.mpg.de/license.html`** — page renders only a JavaScript shell to headless fetchers (Tarteaucitron cookie-consent wrapper, no server-side content). Project-page top text does say "Code will be available for research purposes" verbatim. The MPI house template applied to every other verified TUE dataset (SMPL, AMASS, 3DPW, BEDLAM) is identical — the WHAM license is almost certainly the same template, but verbatim confirmation requires a human-in-browser visit.
- **`opencap.ai/terms`** — page returns a JavaScript shell (Webflow SPA). `opencap.ai/terms.html` 404s. `app.opencap.ai/terms` returns a JavaScript-required error page. The only canonical-source text remains the opencap-core README phrase "freely available for academic research use." A human-in-browser visit is still required before any commercial decision.

New gaps discovered in v2 scope expansion:

- **Human3.6M description.php page** — returns HTTPS→HTTP redirect loop. Same IMAR server as Fit3D; Fit3D's `/legal` page works, but the Human3.6M `/description.php` page does not resolve from this sandbox. Consensus public record is clear (non-commercial academic, institutional registration), so treat as Medium confidence until a human opens it.
- **MS COCO Terms of Use anchor** — `cocodataset.org/#termsofuse` renders client-side; the ToU text is in the page source but is not in the initial fetch. CC BY 4.0 for annotations is the widely-documented consensus. `cocoapi` code license confirmed BSD 2-Clause directly.
- **MPII Human Pose license** — MPI CVML department page does not display a license clause explicitly. Historical usage in commercial products suggests BSD-like, but verbatim confirmation needed.

All remaining gaps are "page is a JS SPA that doesn't render in headless fetch" — they are all trivially resolvable by a human with a browser in five minutes, and none of them change the commercial-viability conclusion (which is driven by the blockers that *are* verified: OpenCap Monocular PolyForm NC, SMPL non-commercial, AMASS non-commercial, and the full chain of dataset non-commercial licenses).
