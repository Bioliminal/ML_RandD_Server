# Research Gaps & Unfounded Claims — Audit 2026-04-08

> Gap analysis between `hardware-configurations.html` (Session 3) and the backing .md research files. Every claim in the HTML evaluated for source support.

---

## A. HTML Claims NOT Backed by Any .md File

### A1. Torso-Specific Spatial Resolution (Session 3 new content)
- **Claim:** Chest TPD 40-50mm, upper back 50-60mm, lats 40-55mm, delts 35-45mm, core 40-55mm
- **Source status:** hardware-handover.md provides only "Torso/back: 40-60mm" as a single range. The per-region breakdown is extrapolated, not sourced.
- **Action needed:** Find primary TPD studies that break out chest, back, lats, delts separately. Weinstein 1968 two-point discrimination norms may have this granularity.

### A2. Athos Channel Count
- **Claim:** "Athos compression shirt uses ~14 EMG channels covering pecs, delts, lats, traps, biceps, triceps"
- **Source status:** Not cited in any .md file. Referenced in wearable_emg_cv_research.md descriptively but without specific channel count.
- **Action needed:** Verify from Athos product documentation or the 2018 validation study referenced in wearable_emg_cv_research.md.

### A3. TSA Force Ranges Per Tier
- **Claim:** SG90 servo "1-3N", GA12-N20 "5-15N", Pololu 25D "10-50N"
- **Source status:** Engineering estimates. No .md file provides force measurements. Not from datasheets in the research docs.
- **Action needed:** Verify against motor datasheets. Force depends on string diameter, twist ratio, and lever arm — calculate from published stall torque specs.

### A4. BioAmp Physical Dimensions
- **Claim:** "25.4 x 10mm, <2g"
- **Source status:** Not in any .md file. Likely from Upside Down Labs product page.
- **Action needed:** Low priority. Verify on Crowd Supply listing.

### A5. Precision Microdrives 310-103 Specs
- **Claim:** "10mm dia x 3.4mm, ~200Hz, 0.8G amplitude, 75mA"
- **Source status:** Not in research docs. From vendor datasheet.
- **Action needed:** Low priority. Verify on Precision Microdrives website.

### A6. Sourcing Tab (entire)
- **Claim:** Micro Center Austin address, Mouser overnight to Austin, Pololu from Las Vegas, etc.
- **Source status:** Contextual information, not research-backed. Reasonable but unverified.
- **Action needed:** Verify stock availability on vendor websites before ordering.

### A7. Specialist Questions Q6-Q12
- All torso-specific questions (strap-harness vs compression, scapular movement, washability, 8+ch muxing, dual-modality wiring) are new open questions — not documented in prior research. Valid questions but no prior analysis exists.

---

## B. Research Content NOT Reflected in HTML

### B1. CRITICAL — Safety Constraints (from hardware-engineering-specs.md)
- **Missing:** Circumferential pressure limits (continuous <30 mmHg, venous occlusion >40-60 mmHg, arterial >180-200 mmHg)
- **Missing:** Fail-open design requirement (TSA must freewheel on power loss)
- **Missing:** IEC 60601-1 electrical safety limits (10μA DC leakage)
- **Missing:** Electrode biocompatibility (Ag/AgCl irritation 10-20% after 24hrs, nickel sensitization 10-15%, ISO 10993)
- **Impact:** Specialist handover is incomplete without safety constraints.
- **Now captured in:** torso-vest-spec.md Section 8.

### B2. CRITICAL — FDA Regulatory Strategy (from hardware-engineering-specs.md)
- **Missing:** General wellness exempt vs Class II medical device distinction
- **Missing:** mTrigger cautionary tale (same tech, Class II due to rehab framing)
- **Missing:** Claim framing discipline ("training tool" vs "reduces injury")
- **Impact:** Product claim language directly affects regulatory burden.
- **Now captured in:** torso-vest-spec.md Section 8.

### B3. HIGH — Prior Art Not Referenced
- **Muscle Minder** (UBC SPIN Lab, Karon MacLean): n=6, TSA shirt prototype, pre-rep > continuous cueing. Only directly comparable prior art for TSA-based lifting cueing. Not cited in HTML.
- **mTrigger** ($449 commercial product): single-channel sEMG biofeedback for clinical rehab. Validated, FDA Class II. Shows market demand.
- **Impact:** Specialist and teammates need to know what's been tried before.

### B4. HIGH — Phone-as-Hub Feasibility Risks (from hardware-engineering-specs.md + kelsi-hybrid-spec.md)
- **Missing:** BLE data rate analysis (14ch x 500Hz x 2 bytes = 14 kB/s, ~50-70% of BLE 4.2 throughput)
- **Missing:** Risk of CV frame drops causing BLE interval misses
- **Missing:** Mitigation strategy (buffer on MCU, batch transmit)
- **Missing:** Minimum phone spec (~2022+)
- **Now captured in:** torso-vest-spec.md Section 7.

### B5. MEDIUM — Mechanoreceptor Education
- **Missing:** Pacinian (FA-II, vibration 50-300Hz, habituates in 5-15s), Meissner (FA-I, flutter 10-50Hz), Merkel (SA-I, sustained pressure), Ruffini (SA-II, skin stretch)
- **Impact:** The hybrid cueing rationale depends on understanding receptor adaptation rates. HTML mentions them in passing but doesn't explain.

### B6. MEDIUM — Motor Unit Physiology Detail
- **Missing:** Motor unit territories 5-10mm cross-sectional zones
- **Missing:** Wakahara 2013 (regional activation predicts regional hypertrophy in triceps)
- **Missing:** Biceps vs brachioradialis distinction rationale (between-muscle > within-muscle)
- **Impact:** Less critical for torso vest but relevant for future arm expansion.

### B7. LOW — Kelsi Hybrid Architecture Detail
- **Missing:** Three operating modes (Kelsi-only, Rajiv-only, Hybrid)
- **Missing:** Shared fascial chain knowledge base
- **Impact:** Not directly relevant to hardware spec but important for product architecture context.

---

## C. Major Inconsistencies

### C1. MVP Exercise: Biceps → Torso (UNEXPLAINED PIVOT)
- **Session 2 decision (2026-04-07):** Bicep curl with dumbbell. Documented in mvp-build-decisions.md with detailed rationale table.
- **Session 3 HTML:** Assumes torso exercises (bench press, row, push-up) without explaining why the bicep decision was superseded.
- **What's needed:** Primary source backing for "torso is where the most value lies" (Lawson's recommendation). This is a Session 4 research task.

### C2. Form Factor: Arm Sleeve → Torso Harness (UNEXPLAINED PIVOT)
- **Session 2 decision:** Compression arm sleeve with velcro pods. Documented in mvp-build-decisions.md.
- **Session 3 HTML:** Presents strap-harness vest as if established, without explaining the pivot.
- **What's needed:** The conversation context (CV needs bare skin, sizing flexibility, iteration speed) is the rationale. Now documented in torso-vest-spec.md Section 1.

### C3. Rajat vs Rajiv: Body Region Disagreement
- **Rajat's research:** Lower body + back (erector spinae, quads). Strongest injury prevention case — lumbar injuries 12.9-48%, knee 11-21%.
- **Rajiv's HTML:** Upper torso (pecs, lats, traps, delts). Best demo practicality, Lawson's structural integration recommendation.
- **Bridge proposal (Rajat's doc):** Push-ups as MVP exercise — validates torso EMG hardware (pecs, delts, core) while measuring erector spinae/core compensation patterns. Squats via leg sleeves in v2.
- **What's needed:** Session 4 must reconcile body region with research backing.

---

## D. Claims From Rajat's Research NOT Yet In Our Spec

### D1. New Citations (Strong Evidence)
- Hakariya et al. 2023: Skilled athletes use 3-4 muscle synergies vs 5-6 in unskilled. Temporal coordination is critical.
- Bakhshinejad et al. 2025: Systematic review — fatigue causes lumbar flexion in deadlifts, forward lean in squats, bar path changes in bench.
- Parakkat 2004: Novices show higher co-activation than experts → higher spinal loading at same weight.
- Toon 2023: Why Athos/Enflux/Myontec failed — signal quality during dynamic exercise, washability, "so what" problem. Setup time >2 min loses users.
- Ohiri et al. 2022: Compression shirt sEMG signal quality comparable to adhesive electrodes.

### D2. Key Arguments to Incorporate
- **Temporal warning window (2-5 reps):** Core value prop. EMG fatigue precedes visible breakdown. Must validate empirically.
- **Spinal loading invisible to camera:** 30-40% of actual load from co-contraction. Marras & Granata 1997. Strongest argument for EMG necessity.
- **Fading algorithm required:** van Dijk 2006, Lauber & Keller 2014. Product must fade cueing (100% → 33%) to build motor independence. Otherwise creates dependent user.
- **Never display "safety score":** Risk compensation / Peltzman effect concern.
- **Setup time <2 min:** Toon 2023 — adoption killer for consumer EMG products.

### D3. Rajat's 4-Channel Placement (Alternative to Our 8-Channel)
- L/R erector spinae + VL/VM quad = $121 total
- Validates: clean sEMG signal quality, fatigue-before-breakdown claim, VL/VM ratio divergence, haptic behavior change
- More focused than 8-channel torso vest, answers tighter validation questions
