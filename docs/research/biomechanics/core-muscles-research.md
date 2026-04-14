# Core Musculature Research: Abdominal Muscles in Alignment, Stability, and sEMG Feasibility

**Date:** 2026-04-08
**Purpose:** Primary-source evidence review for MVP sensor map decisions (currently 8ch: erector spinae, upper trap, pec, lat). Should external obliques move to Tier 1? Should rectus abdominis be added?

---

## 1. McGill's Core Stability Model: Co-Contraction, Not Isolation

**Key source:** McGill SM. *Low Back Disorders: Evidence-Based Prevention and Rehabilitation.* Human Kinetics, 2002 (2nd ed. 2007).

**Core findings:**

- McGill's model rejects isolating any single muscle for spinal stability. He demonstrates that ALL trunk muscles -- rectus abdominis, external obliques, internal obliques, transversus abdominis, erector spinae, quadratus lumborum -- must co-contract to create a "superstiffness" that exceeds the sum of individual muscle contributions.
- **Abdominal bracing** (co-contracting all trunk muscles) produces significantly greater spinal stiffness than **abdominal hollowing** (isolating TrA). This directly challenges Pilates-derived "draw-in" cuing in loaded contexts.
- The **McGill Big 3** exercises each target different trunk muscle groups:
  - **Curl-up:** rectus abdominis + obliques (anterior stability)
  - **Side plank:** obliques + quadratus lumborum (lateral stability / anti-lateral-flexion)
  - **Bird-dog:** erector spinae + glutes (posterior chain + anti-extension)
- McGill's model implies that monitoring only the posterior chain (erector spinae) gives an incomplete picture of trunk stability. The obliques and rectus abdominis are co-equal partners in the stability system.

**Relevance to hardware:** If we only measure erector spinae, we are measuring half the stability equation. External obliques are the most accessible anterior/lateral trunk stabilizer for sEMG.

---

## 2. Transversus Abdominis: Anticipatory Activation and sEMG Limitations

**Key sources:**
- Hodges PW, Richardson CA. "Inefficient muscular stabilization of the lumbar spine associated with low back pain." *Spine.* 1996;21(22):2640-50.
- Hodges PW, Richardson CA. "Feedforward contraction of transversus abdominis is not influenced by the direction of arm movement." *Experimental Brain Research.* 1997;114:362-370.

**Core findings:**

- In healthy subjects, TrA fires **before** any limb movement as an anticipatory postural adjustment -- independent of movement direction. This is a feedforward mechanism, not reactive.
- In chronic low back pain patients, TrA activation is **delayed**, arriving after the perturbation rather than before it.
- The original Hodges & Richardson studies used **fine-wire (intramuscular) EMG**, not surface EMG, because TrA is a deep muscle lying beneath internal oblique.

**Can surface EMG measure TrA?**

- Marshall PW, Murphy BA. "The validity and reliability of surface EMG to assess the neuromuscular response of the abdominal muscles to rapid limb movement." *Journal of Electromyography and Kinesiology.* 2003;13(6):525-536.
- Marshall & Murphy found that a surface electrode placed inferior-medially (near ASIS) captures a **combined TrA/IO signal**. Cross-correlation analysis showed this signal "accurately demonstrates the functional activity" of TrA/IO with acceptable reliability.
- **However:** You cannot separate TrA from internal oblique with surface EMG. The signal is a composite.

**Relevance to hardware:** TrA is not independently measurable with sEMG. A TrA/IO composite site is possible but adds complexity. This is a Tier 3 consideration, not MVP.

---

## 3. Obliques in Anti-Rotation and Anti-Lateral-Flexion

**Key sources:**
- Saeterbakken AH et al. "Core Muscle Activity during Physical Fitness Exercises: A Systematic Review." *International Journal of Environmental Research and Public Health.* 2020;17(12):4306.
- Stokes IAF et al. "Differential control of abdominal muscles during multi-directional support-surface translations in man." *Experimental Brain Research.* 2008;187:603-611.
- PMC article on sprint hurdler oblique asymmetry (PMC8851117).

**Core findings:**

- External obliques show **high activation** during free-weight exercises, particularly unilateral movements (Bulgarian squats, single-arm carries, Pallof press variations).
- The obliques function as the primary **anti-rotation** and **anti-lateral-flexion** stabilizers. During a squat or deadlift, if the bar shifts or the lifter lists to one side, the contralateral oblique fires to resist the deviation.
- **Asymmetry matters:** Research on athletes shows that oblique asymmetry correlates with injury risk and low back pain. In chronic LBP patients, external oblique activation is abnormally high while internal oblique activation is reduced -- indicating a compensatory pattern.
- During loaded trunk rotation, individuals with LBP show excessive spinal extension coupled with rotation, suggesting the obliques are failing to control the movement.

**Relevance to hardware:** External obliques are the primary muscles resisting the exact compensations we want to detect -- lateral shift during squats, rotational drift during deadlifts. Bilateral external oblique monitoring would directly reveal left-right asymmetry in real time.

---

## 4. Pilates Literature: Deep vs. Superficial Core

**Key sources:**
- Critchley DJ et al. "Comparison of deep and superficial abdominal muscle activity between experienced Pilates and resistance exercise instructors and controls during stabilization exercise." *Journal of Bodywork and Movement Therapies.* 2015;19(3):485-492. (PMC4492427)
- Herrington L, Davies R. "The influence of Pilates training on the ability to contract the transversus abdominis muscle using the pressure biofeedback unit." *Journal of Bodywork and Movement Therapies.* 2005;9(1):52-57.
- Endleman I, Critchley DJ. "Transversus abdominis and obliquus internus activity during Pilates exercises: measurement with ultrasound scanning." *Archives of Physical Medicine and Rehabilitation.* 2008;89(11):2205-12.

**Core findings:**

- Pilates training emphasizes TrA and multifidus ("deep core") over rectus abdominis and external obliques ("superficial core"). This is grounded in the Hodges & Richardson work.
- Experienced Pilates practitioners show significantly **higher co-contraction** of deep and superficial muscles during stability tasks compared to novices.
- The Pilates literature increasingly acknowledges that **both systems matter**: deep core for anticipatory control, superficial core for force production and load transfer.
- Ultrasound (not EMG) is the preferred clinical tool for assessing TrA in Pilates research, confirming that sEMG is not the right modality for deep core.

**Relevance to hardware:** A Pilates-informed user already has good deep core activation. The gap in their training awareness is more likely in the superficial system under load -- exactly what sEMG can measure (external obliques, rectus abdominis).

---

## 5. Surface EMG Feasibility for Abdominal Muscles

**Key sources:**
- Ng JK-F, Kippers V, Richardson CA. "Muscle fibre orientation of abdominal muscles and suggested surface EMG electrode positions." *Electromyography and Clinical Neurophysiology.* 1998;38:51-58.
- Marshall PW, Murphy BA. 2003 (cited above).
- Springer article on sEMG reliability for rectus diastasis assessment (2024).

**What surface EMG CAN measure well:**

| Muscle | sEMG Quality | Electrode Placement | Crosstalk Risk |
|--------|-------------|---------------------|----------------|
| Rectus abdominis | Excellent | 3cm lateral to midline, aligned with fibers | Low (large, superficial) |
| External oblique | Good | Below 8th rib, aligned ~4deg from rib angle | Moderate (skin fold variability) |
| Internal oblique / TrA composite | Fair | Medial to ASIS, horizontal | High (composite signal only) |
| TrA alone | Not feasible | N/A | N/A (too deep) |

**Key validity points:**
- Rectus abdominis is large and superficial -- the cleanest abdominal sEMG signal available.
- External oblique is reliably measurable with proper electrode alignment along fiber direction (Ng et al. 1998).
- The IO/TrA composite site (Marshall & Murphy 2003) is valid for research but adds interpretive complexity inappropriate for a coaching product.
- Crosstalk between RA and EO is manageable with proper inter-electrode distance and alignment.

---

## Hardware Decision Matrix

| Muscle | Stability Role | sEMG Signal Quality | Detects Asymmetry? | Recommendation |
|--------|---------------|---------------------|--------------------|----|
| External oblique | Anti-rotation, anti-lateral-flexion, bracing | Good | Yes (bilateral L/R) | **PROMOTE TO TIER 1** |
| Rectus abdominis | Anti-extension, bracing, force transfer | Excellent | Limited (midline) | **Keep Tier 2** |
| Internal oblique/TrA | Anticipatory stabilization | Fair (composite only) | Possible | Keep Tier 3 |

---

## Recommendation

### Promote external obliques to Tier 1 MVP. Here is why:

1. **McGill's co-contraction model** says you cannot assess trunk stability without the anterior/lateral system. Erector spinae alone is half the picture.
2. **Oblique asymmetry** is directly linked to compensation patterns and injury risk -- this is the exact use case for a coaching wearable.
3. **sEMG signal quality** for external obliques is good with proper electrode placement (Ng et al. 1998).
4. **Bilateral external oblique channels** (2 channels) would give left-right asymmetry detection during squats, deadlifts, and carries -- high coaching value.
5. **Pilates-informed users** already have strong deep core awareness. The external obliques under load are the gap.

### Keep rectus abdominis at Tier 2:

- RA has excellent signal quality but its coaching value is lower. It is a midline muscle -- bilateral monitoring adds less asymmetry information.
- RA activation during squats and deadlifts is relatively low compared to obliques and erector spinae.
- RA becomes important for anti-extension (e.g., overhead press, front squat) -- worth adding in Tier 2 expansion.

### Channel budget impact:

Adding bilateral external obliques = +2 channels, bringing MVP to 10 channels (from 8). This is the single highest-value addition to the sensor map based on the evidence.

---

## Sources

- [McGill Big 3 - Squat University](https://squatuniversity.com/2018/06/21/the-mcgill-big-3-for-core-stability/)
- [Hodges & Richardson 1996 - PubMed](https://pubmed.ncbi.nlm.nih.gov/8961451/)
- [Hodges & Richardson 1997 - PubMed](https://pubmed.ncbi.nlm.nih.gov/9166925/)
- [Marshall & Murphy 2003 - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1050641103000270)
- [Ng, Kippers, Richardson 1998 - PubMed](https://pubmed.ncbi.nlm.nih.gov/9532434/)
- [Core Muscle Activity Systematic Review 2020 - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7345922/)
- [Oblique Asymmetry in Sprint Athletes - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8851117/)
- [Pilates Deep vs Superficial Core - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4492427/)
- [TrA Pilates Ultrasound - PubMed](https://pubmed.ncbi.nlm.nih.gov/18996251/)
- [sEMG Rectus Abdominis and External Oblique - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9505236/)
- [Abdominal Bracing vs Hollowing Review - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11503327/)
- [McGill Low Back Disorders - Google Books](https://books.google.com/books/about/Low_Back_Disorders.html?id=j0R4-fzBwPIC)
- [Oblique Asymmetry and LBP - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4519377/)
- [Trunk Rotation in Chronic LBP - PLOS One](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0186369)
- [Appropriately Placed Surface EMG for Deep Muscles - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/0021929096845477)
