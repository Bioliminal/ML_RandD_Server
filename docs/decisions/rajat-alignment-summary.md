# Rajat's Research — Alignment Summary 2026-04-08

> Distilled from `Rajat/hardware-alignment-injury-prevention.html` and `Rajat/complete-research-document.md`. Agent-friendly capture of Rajat's injury prevention research, component evaluations, and divergences from the torso vest spec.

---

## 1. Core Architecture (ALIGNED)

Both sides independently converged on:
- **Camera (MediaPipe) + sEMG + vibrotactile cueing** — same stack
- **Phone as BLE hub** — same architecture
- **BioAmp EXG Pill** — same MVP sEMG sensor pick
- **ESP32-S3** — same MCU
- **Disposable Ag/AgCl electrodes** — same
- **IMU explicitly excluded** — both sides independently. Camera outperforms IMU for frontal-plane kinematics (Chia 2021: RMSE 3-10° vs 7-15°). IMU magnetometers corrupted by gym equipment.
- **FDA general wellness framing** — "training tool, not diagnostic"

**8 of 12 components fully aligned.**

---

## 2. Four Divergences

### Divergence 1: Body Region
| | Rajat | Rajiv (HTML) |
|---|---|---|
| **Focus** | Lower body + back (erector spinae, quads) | Upper torso (pecs, lats, traps, delts) |
| **Justification** | Highest injury incidence: lumbar 12.9-48%, knee 11-21% (Keogh & Winwood 2017, Bonilla 2022) | Lawson's recommendation: torso is where most value for imbalance correction. More muscle groups to differentiate. Best demo practicality |
| **Strongest argument** | People actually get hurt here. Spinal loading invisible to camera (Marras & Granata 1997: 30-40% from co-contraction) | Structural integration / fascial chain correction. More compelling demo narrative |
| **Bridge proposal** | Push-ups: validates torso EMG (pecs, delts, core) while measuring erector spinae compensation. Zero equipment needed. Squats/deadlifts via leg sleeves in v2 | TBD — needs primary source backing for "torso > extremities" claim |

### Divergence 2: Form Factor
| | Rajat | Rajiv (HTML) |
|---|---|---|
| **Consumer** | Compression shirt (Ohiri 2022: comparable signal quality; lower failure rates than straps; normal gym appearance; setup <2 min) | Compression shirt (post-MVP) |
| **R&D** | Accepts strap-harness for prototype iteration | Strap-harness (MVP) |
| **Status** | **Aligned on sequence:** harness for R&D, shirt for consumer |

### Divergence 3: TSA Squeeze
| | Rajat | Rajiv (HTML) |
|---|---|---|
| **Position** | Not in current plan. Vibration-only for MVP | Central to design. 2 zones in MVP vest |
| **Rajat's argument** | If MVP question is "does detection + basic cueing change behavior?" — vibration-only answers faster and cheaper | If question is "can we replicate a trainer's hand?" — TSA needed |
| **Rajat's recommendation** | Include TSA at 1-2 zones alongside vibration-only zones for A/B testing. Partner has spec'd the build. Let data decide |

### Divergence 4: Channel Count
| | Rajat | Rajiv (HTML) |
|---|---|---|
| **MVP** | 4 channels ($121): L/R erector spinae + VL/VM quad | 8 channels ($220): pecs, lats, traps, delts |
| **Rajat's reasoning** | Answers tighter validation questions: can we get clean signal? Does fatigue precede breakdown? Does VL/VM divergence precede valgus? | More muscle groups = richer data, more impressive demo |
| **Rajat's recommendation** | Order 2x MyoWare NOW (Amazon, tomorrow). Order 10x BioAmp simultaneously (Mouser, 3-5 days). Test with 2 channels while BioAmp ships. Don't wait |

---

## 3. Key Research Citations (Not In Our .md Files)

### Strong Evidence (New)
| Citation | Key Finding | Relevance |
|---|---|---|
| **Bakhshinejad et al. 2025**, Sports Med - Open | Systematic review: fatigue causes lumbar flexion (deadlift), forward lean (squat), bar path changes (bench) | Direct evidence for fatigue → injury mechanism per exercise |
| **Hakariya et al. 2023**, J Sports Sciences | Skilled athletes: 3-4 muscle synergies. Unskilled: 5-6. Temporal coordination (timing) is critical, not just magnitude | Justifies multi-channel EMG + timing analysis for compensation detection |
| **Parakkat 2004**, Ohio State dissertation | Novices show higher co-activation than experts → higher spinal loading at identical external weight | Strongest argument for EMG in beginners — invisible risk |
| **Toon 2023**, U Derby dissertation | Why Athos/Enflux/Myontec failed: signal quality during dynamic exercise, washability, "so what" problem. Setup >2 min loses users | Critical product design constraints |
| **Ohiri et al. 2022**, Scientific Reports | Compression shirt sEMG signal quality comparable to adhesive electrodes at 15-20 mmHg passive pressure | Validates compression garment form factor |
| **Falk, Aasa & Berglund 2021**, Musc Sci & Practice | PTs cannot visually detect posterior pelvic tilt until >34° | Camera with angle measurement beats trained human observation |
| **Rampichini et al. 2020**, Entropy | MDF (median frequency) shift is most validated fatigue biomarker. RMS amplitude increases reflect recruitment | Establishes fatigue detection mechanism |

### Moderate Evidence (New)
| Citation | Key Finding |
|---|---|
| **Sigrist et al. 2013**, Psychonomic Bull & Rev | Haptic feedback best for force/effort tasks with least guidance dependency. Multimodal > single |
| **Lauber & Keller 2014**, Eur J Sport Sci | Fading schedule (100% → 33%) produces superior retention vs constant feedback |
| **van Dijk 2006**, UTwente dissertation | Three-stage motor learning: cognitive → associative → autonomous. Maps to our Correction → Reinforcement → Fade |
| **Hegi et al. 2023**, Front Sports & Active Living | Exercise adherence predicted more by social support than technical feedback quality |

### Honest Gaps Acknowledged
- **No RCT shows wearable biofeedback reduces lifting injury rates** (Battis 2023). Detection ≠ prevention. This gap = our market opportunity.
- **EMG degrades during dynamic exercise** (Disselhorst-Klug 2020): sweat, movement artifact, subcutaneous fat. Compression + disposable electrodes mitigate, don't solve.
- **Transfer from cueing to independent performance is inconsistent** in literature.
- **Risk compensation (Peltzman effect):** User may trust "smart shirt" and attempt heavier weights. Never display "safety score."

---

## 4. Rajat's Key Design Recommendations

1. **Camera-first, EMG-premium:** Free app for acquisition, garment for engaged users. Addresses "so what" that killed Athos.
2. **Temporal warning window (2-5 reps):** Core value prop. EMG detects fatigue before visible breakdown. Must validate empirically.
3. **Fading algorithm required:** Product must fade cueing (100% → 33% over sessions) to build motor independence. Otherwise creates dependent user.
4. **Setup time <2 minutes:** Non-negotiable for consumer adoption (Toon 2023).
5. **Never display "safety score":** Risk compensation concern.
6. **Spinal loading is the killer argument for EMG:** 30-40% invisible to camera (Marras & Granata 1997). This is why EMG matters — not just muscle activation levels.

---

## 5. Rajat's $121 Prototype BOM

| Component | Qty | Price |
|---|---|---|
| BioAmp EXG Pill | 4 | $40 |
| Ag/AgCl electrodes | 100 | $8 |
| ESP32-S3 DevKitC | 1 | $12 |
| Coin vibe motors | 6 | $6 |
| 800mAh LiPo + TP4056 | 1 | $10 |
| Compression shirt + shorts | 1 | $30 |
| Wiring/build | 1 | $15 |
| **Total** | | **$121** |

**Placement:** L/R erector spinae + VL/VM quad (4 sensor channels, 6 vibe zones including glute med cue-only)

**5 Validation Questions This Prototype Answers:**
1. Can we get clean sEMG from erector spinae and quads during compound lifts through compression fabric?
2. Does EMG fatigue signal actually precede visible form breakdown (2-5 rep claim)?
3. Does VL/VM ratio divergence precede visible knee valgus?
4. Does haptic cueing change beginner behavior on next rep?
5. Will a beginner actually wear this?
