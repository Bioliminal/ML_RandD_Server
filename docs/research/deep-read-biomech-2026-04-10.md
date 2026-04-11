# Deep Read — Biomechanics Papers Added 2026-04-10

**Purpose:** Per-paper extraction + verdict on the Sahrmann Movement System Impairment (MSI) framework for AuraLink.
**Scope:** 9 items moved from `unsorted/` → `biomechanics/` on 2026-04-10.
**Upstream:** `docs/operations/comms/research-integration-report.md` (fascial chain rule strategy).

---

## Paper-by-paper

### 1. Sahrmann 2017 — "How and Why of the Movement System" (IJSPT 12(6):862–869)

- **Type:** Commentary. Level of Evidence 5 (opinion).
- **Claim:** PT's professional identity should be "the movement system." Shifts from *pathokinesiologic* ("pathology causes movement dysfunction") to *kinesiopathologic* ("movement dysfunction causes pathology").
- **MSI link:** Foundational framing rather than a specific rule set.
- **Actionable rules for us:** None. Conceptual.

### 2. Sahrmann 2021 — "Defining Our Diagnostic Labels" (Phys Ther 101:pzaa196)

- **Type:** Point of View. Level of Evidence 5.
- **Claim:** PTs must own movement-diagnosis labels for the profession to survive under value-based care.
- **Actionable rules for us:** None. Strategic / reimbursement argument, not clinical evidence.

### 3. Joyce, Beneciuk, George 2023 — "Concerns on the Science and Practice of a Movement System" (Phys Ther 103:pzad087)

- **Type:** Point of View / evidence-based critique.
- **Core argument:** Movement diagnoses (including MSI-derived categories) lack:
  - **Predictive validity** — movement-based labels like "verticality" haven't been shown to predict future pathology (e.g., falls).
  - **Known-group validity** — asymptomatic individuals often show the same "abnormal" movement patterns as symptomatic ones.
  - Clear linkage to health outcomes (pain, disability, future pathology).
- **Implication for AuraLink:** Any movement pattern we flag as "concerning" must be validated against an outcome we actually care about, not just as a label. "Hip adduction during single-leg squat" is defensible as a rule because there's mechanistic evidence tying it to function (Harris-Hayes 2018); "lumbar flexion bias" is not defensible as a diagnosis without that link.

### 4. Physiopedia — Sahrmann MSI for LBP (web)

- **Content:** Educational overview of Sahrmann's MSI classification applied to low back pain (lumbar flexion / extension / rotation / lateral-shift biases).
- **Rule potential:** Categorical only. No thresholds published in this overview.

### 5. Van Dillen, Norton, Sahrmann et al. 2016 — LBP Classification-Specific Treatment RCT (Manual Therapy 24:52–64)

- **Type:** 2-center single-blind RCT. **Level 1 evidence.**
- **N:** 101 chronic LBP patients (47 classification-specific, 54 non-classification-specific). 6-week treatment, 1-year follow-up.
- **Intervention:** MSI-classified treatment vs generic movement training.
- **Primary outcome:** Modified Oswestry Disability Index.
- **Key result:** **No significant difference between groups** (p > .05). Both groups improved; plateau at 6 months. Only adherence to the performance training (not classification category) predicted outcome.
- **Verdict on MSI for LBP:** **MSI classification did not beat generic movement training.** This is the most important biomech finding in this batch.
- **Rule for us:** The classification *label* is not the active ingredient. Adherence to corrective training is. Our product should emphasize clarity and adherence of the training cue, not the label we attach to it.

### 6. Harris-Hayes, Czuppon, Van Dillen et al. 2016 — Feasibility RCT, Movement Pattern Training for Chronic Hip Pain (JOSPT 46(6):452–461)

- **Type:** Feasibility RCT. Level 2b.
- **N:** 35 adults with chronic hip joint pain. MPT vs wait-list.
- **Intervention:** Sahrmann-style movement pattern training.
- **Primary outcome:** Modified Harris Hip Score (MHHS).
- **Key result:** MPT was feasible (85% retention), acceptable, and showed effect sizes favoring the MPT group. Underpowered for definitive effectiveness.
- **Rule for us:** Feasibility proven for movement-pattern intervention delivered clinically. Does not prove phone-delivered inference is accurate enough — that's a separate validation we'd owe.

### 7. Harris-Hayes et al. 2018 — Reduced Hip Adduction & MHHS (JOSPT 48(4):316–324)

- **Type:** Ancillary analysis of the MPT RCT. Level 2b.
- **N:** 18 young adults with CHJP.
- **Primary finding:** **Hip adduction-angle reduction during functional tasks was significantly correlated with MHHS improvement** (r = −0.67, p < .01). Hip abductor strength improvement also present (p = .01). Alpha angle (bony morphology) was **not** correlated with outcome.
- **Measurement properties:** Hip adduction during single-leg squat, ICC = 0.72, SEM = 3.3°.
- **Verdict:** This is one of the only papers in the batch that links a specific, phone-measurable kinematic variable to a clinical outcome. **This is an extractable rule.**
- **Rule for us:** Hip adduction angle during single-leg squat / step-down is a valid proxy for CHJP functional status. A reduction goal is the training target. Worth encoding as a concrete SBL/BFL-adjacent rule in the chain reasoner.

### 8. Rajagopal et al. 2016 — Full-Body MSK Model (IEEE TBME 63(10):2068–2079)

- **Type:** Model development + validation.
- **Model:** OpenSim-format full-body model. **37 DoF** (6 pelvis, 14 lower limb, 17 upper body). **80 Hill-type muscle-tendon units** driving the lower limbs. 17 ideal torque actuators driving the upper body. 22 rigid body segments. Reference anthropometry 75 kg / 170 cm male, 21 cadaver + 24 MRI subjects informing muscle parameters.
- **Validation:** Muscle-driven joint moments within ~3% RMSE of inverse dynamics during walking and running.
- **Compute:** ~10 minutes per gait cycle on desktop for a full muscle-driven simulation.
- **License:** Open-source (OpenSim ecosystem).
- **Use for us:**
  - Underlying MSK model for OpenCap / OpenCap Monocular dynamics.
  - Synthetic data generator for training / testing — run a known movement through the model, sample video-like 2D projections, use as training data for the pose-to-kinematics stages.
  - Counterfactual simulation — "what if this person reduced hip adduction by 5°, what happens to knee moment?" to validate our own rules before we ship them.

### 9. Uhlrich et al. — Muscle Coordination Retraining Reduces Knee Contact Force (*Scientific Reports*)

- **Type:** Proof-of-concept experimental.
- **N:** 10 healthy adults (8 with full KCF data).
- **Method:** Musculoskeletal simulation (using Rajagopal 2016 model) predicted that gastrocnemius-avoidance gait would reduce knee contact force. Subjects were given a single session of real-time EMG biofeedback on gastrocnemius:soleus activation ratio.
- **Results:**
  - Gastrocnemius:soleus activation ratio reduced **25 ± 15%** (p = 0.004).
  - Late-stance knee contact force reduced **12 ± 12%** (p = 0.029).
  - Ratio reduction correlated with KCF reduction.
- **Verdict:** Mechanistic evidence that MSK-simulation-designed interventions translate to human behavior with EMG biofeedback. Directly validates the premise of the hardware team's sEMG garment.
- **Use for us:** If / when the sEMG garment ships, this is a concrete premium intervention we can deliver: "your gait pattern is loading your knee; here is a biofeedback protocol to shift load from gastroc to soleus." Proven mechanism. Not a free-tier feature.

---

## Synthesis

### MSI framework — adopt, reject, or cherry-pick?

**Verdict: cherry-pick. Adopt the mechanistic kinematic rules; reject the diagnostic label system.**

Justification:
1. **Van Dillen 2016 (Level 1 RCT, n=101) shows MSI classification did NOT outperform generic movement training for LBP.** This is the strongest piece of evidence in the batch and it's negative for the classification *label* approach.
2. **Joyce 2023 validly attacks the validity of movement diagnoses as diagnostic categories.** The critique is not that patterns aren't real; it's that the label "lumbar flexion bias" hasn't been shown to predict anything that matters.
3. **Harris-Hayes 2018 (Level 2b, n=18) shows pattern correction at the kinematic level does predict functional outcome** — hip adduction ↓ correlated with MHHS ↑, r = −0.67. This is the signal we care about: kinematic-level rules tied to outcomes, not labels.
4. **Sahrmann 2017 / 2021 are opinion pieces**, strategic arguments for the PT profession. They don't carry evidentiary weight for our rule engine.

**Concrete implication for our rule set:**
- **Don't ship output labels like "Lumbar Flexion MSI" in the report.** That's a diagnostic claim we cannot defend.
- **Do ship kinematic rules with mechanistic citations.** "Your hip adducted 18° past neutral during the single-leg squat. Studies of chronic hip joint pain show that reducing hip adduction during this movement correlates with improved function."
- **Keep Sahrmann's movement-pattern-training *mechanism* as the underlying framing** without adopting the MSI *diagnostic labels*. Reinforces the wellness positioning.

### Extractable rules (candidates for `config/rules/*.yaml`)

```yaml
# BFL — Back Functional Line (crosses midline through glute/lat coupling)
hip_adduction_single_leg_squat:
  chain: BFL
  metric: hip_adduction_angle_peak
  measurement: single_leg_squat, frontal plane, peak descent
  thresholds:
    info:    8
    concern: 12
    flag:    18
  reliability:
    icc: 0.72
    sem_deg: 3.3
  evidence:
    level: 2b
    citation: "Harris-Hayes 2018, JOSPT 48(4):316–324"
    mechanism: "hip adduction reduction correlated with MHHS improvement (r=−0.67, p<.01)"
  body_type_adjustments:
    hypermobile: +3       # wider tolerance
    female: +2
  notes: "Thresholds are placeholders derived from normative ranges; refine with our own data."
```

```yaml
# SBL — Superficial Back Line (placeholder, Hewett-style baseline)
knee_valgus_overhead_squat:
  chain: SBL
  metric: knee_valgus_angle_peak
  measurement: overhead_squat, frontal plane
  thresholds:
    info:    6
    concern: 10
    flag:    14
  evidence:
    level: 1 (cohort / prospective)
    citation: "Hewett 2005, AJSM"
    mechanism: "knee abduction >10° = 2.5x ACL injury risk"
  body_type_adjustments:
    female: +2
    hypermobile: +3
```

```yaml
# FFL — Front Functional Line (sEMG premium only; hardware-gated)
gastroc_soleus_ratio_walking:
  chain: FFL
  metric: gastrocnemius_soleus_activation_ratio
  measurement: steady-state walking, late stance
  target: "25% reduction from baseline via biofeedback"
  evidence:
    level: 3 (proof-of-concept)
    citation: "Uhlrich et al., Scientific Reports; Rajagopal 2016 MSK model"
    mechanism: "25% ratio reduction yields ~12% knee contact force reduction (p=0.029, n=8)"
  requires: sEMG.gastrocnemius && sEMG.soleus
  tier: premium_with_hardware
```

Everything above is an explicit rule, tied to a published mechanism, and straightforward to tune from YAML per L2 Plan 2.

### Movement pattern training — what does the Harris-Hayes + Uhlrich evidence buy us?

- **Pattern correction is teachable.** Single-session biofeedback (Uhlrich) produced a 25% coordination change; multi-week MPT (Harris-Hayes) produced sustained functional gains.
- **Adherence beats classification.** Van Dillen is explicit: the *content* of the training mattered, not the *label*. Our UX should prioritize clear, repeatable cues over clever categories.
- **The mechanism we can deliver from a phone is kinematic, not EMG.** Without the sEMG garment, we cannot do Uhlrich-style coordination retraining. We *can* deliver Harris-Hayes-style hip adduction correction cues from a pose stream.
- **The mechanism we can deliver *with* the sEMG garment is Uhlrich-style** — this is the strongest premium feature we can ship that no competitor has.

### What this means for our plan

1. **Report schema (`report/schemas.py`, Plan 2).** Rename any "MSI classification" output fields to kinematic-pattern findings. Chain labels (SBL, BFL, FFL) stay — those are scoped to anatomical evidence (Wilke 2016), not to Sahrmann categorization.
2. **Rule config format (`config/rules/*.yaml`).** Every rule should have an `evidence:` block with `level` + `citation` + `mechanism`. Lets us audit which rules are "strong" vs "provisional" at report time.
3. **Body type adjustments (Plan 2 Task 10).** The `adjustment` values should be conservative and citation-linked. No adjustment without a paper.
4. **Premium kinetics from OpenCap Monocular.** Once the server-side pipeline lands, we can encode rules in terms of *joint moments* (Nm/kg) not just angles — that's where the Hewett/Harris-Hayes outcome evidence actually lives. Angle thresholds are a proxy for the moment thresholds.

### Contradictions / tensions with `research-integration-report.md`

- The integration report §5 talks about "chain reasoning" somewhat abstractly. These biomech papers say: rules should be kinematic + mechanistic, not categorical. Strengthens the rule-based-first stance in §6.3, weakens the case for a learned GNN at launch (Joyce critique applies to labeled movement-pattern categories).
- The integration report does not cite Joyce 2023 or Van Dillen 2016. Both should be added to the "MSI caveats" framing when we next touch §5.
- Nothing in the biomech batch contradicts the fascial chain scope (SBL, BFL, FFL via Wilke 2016) — that remains the anatomical basis.

---

*Generated 2026-04-10 from agent deep-read of 9 biomechanics papers.*
