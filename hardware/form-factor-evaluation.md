# Form Factor Evaluation: Torso sEMG Wearable for Weightlifting Coaching

**Date:** 2026-04-08
**Context:** 10-day rapid prototyping phase. Wearable must capture sEMG from torso muscles (pecs, lats, traps, erector spinae, delts, serratus anterior), deliver vibrotactile cueing, and remain compatible with phone-based MediaPipe pose estimation (which needs visible joint landmarks at shoulders, elbows, hips).

---

## What Research Labs Actually Use

### Gold Standard: Wireless Sensor Pods on Adhesive Electrodes

The dominant research setup for multi-channel torso EMG during exercise is:

- **Delsys Trigno wireless sensors** attached to disposable Ag/AgCl adhesive electrodes placed per SENIAM guidelines. Each sensor has a built-in triaxial accelerometer. The system supports up to 32 simultaneous channels at 40m wireless range with 7+ hour battery life. Sensors use dry parallel-bar electrode contacts adhered directly to skin.
- **REFA multi-channel amplifiers** (TMS International) with 84+ monopolar channels using 2mm recessed sintered Ag/AgCl disc electrodes filled with conductive gel, attached with double-sided tape.
- **Standard skin prep protocol:** shave, abrade with sandpaper/NuPrep, clean with isopropyl alcohol.
- **Electrode spacing:** 2cm center-to-center (SENIAM) or 3.5cm for bipolar pairs in weightlifting studies.
- **Wire management:** cables taped to body, strain-relieved at electrode sites, routed to avoid joint crossings.

### Key Research Protocol Details for Weightlifting

From published deadlift/squat EMG studies:
- Erector spinae electrodes: 2cm lateral to spinous process at L1
- Electrodes placed along muscle fiber direction, on muscle belly
- Reference electrodes on bony prominences (iliac crest, clavicle)
- Movement artifact highest frequencies: 32Hz (walking), 40Hz (jumping) -- compound lifts likely 20-35Hz range

### Movement Artifact Mitigation

- Taping adapter units and cabling to the body minimizes cable-sway artifacts
- Passive electrode wires should be as short as possible
- Sponge/hydrogel electrodes with buffer layers reduce skin-electrode motion
- High-pass filtering at 20Hz removes most movement artifact but may also remove some low-frequency EMG content

---

## What Consumer/Startup Products Used (and Why They Failed)

### Athos ($50M raised, failed)
- **Form factor:** Full compression suit (shirt + shorts), like a slim wetsuit, no undergarments allowed
- **Failure reasons:**
  - Non-breathable: terrible sweat experience during exercise
  - $600 per set -- high price for niche market
  - Direct skin contact meant returns "had to be burned" -- destroyed unit economics
  - Extremely limited addressable market (serious lifters only)
  - Weak demand, extended backorders indicating poor traction
- **Lesson:** Compression garment EMG works technically but fails on comfort, cost, and market fit

### Myontec (M-Body)
- **Form factor:** EMG shorts/tights for lower body
- **Status:** Still operating but niche -- primarily Nordic sports research market
- **Lesson:** Survived by staying small and research-focused, not trying to be consumer mass-market

### Enflux
- **Form factor:** Full-body smart clothing (motion capture focus, not pure EMG)
- **Status:** Raised only $120K (2016), appears dormant
- **Lesson:** Full-body smart clothing is extremely hard to manufacture and sell

### Common Failure Pattern
All garment-based EMG products struggle with: (1) electrode contact consistency across body types, (2) washability degrading conductive textiles, (3) fixed electrode positions that can't accommodate anatomical variation, (4) high per-unit cost with hygiene concerns preventing resale/returns.

---

## Ohiri et al. 2022: E-Textile Modular sEMG Suit

**Paper:** "E-textile based modular sEMG suit for large area level of effort analysis" (Scientific Reports, June 2022)

### Key Findings
- **Signal quality:** Comparable to adhesive electrodes *when textile is slightly damp* (from sweat or pre-moistening). Dry textile impedance is ~5x higher than gel electrodes; impedance drops to near-gel levels when hydrated.
- **Fabrication:** Laser cutting + heat-press lamination (290F, 23 sec per step). No specialized garment manufacturing needed. Achievable in a standard research lab.
- **Channels:** 16-channel Intan RHD2216 amplifier chip
- **Muscles tested:** Biceps/triceps, quadriceps/hamstring, gastrocnemius/tibialis anterior (limbs only -- torso not validated)
- **Modularity:** Circuit boards are removable via flex PCB connectors, BUT electrode positions are fixed at fabrication time. Cannot be repositioned without remaking the garment.
- **Durability:** Acceptable through 100 don/doff cycles. Machine washing caused 120% impedance increase after 10 washes.
- **Sweat:** Actually beneficial -- natural sweat during exercise maintains electrode hydration, eliminating gel dry-out problems.

### Relevance to Our Project
- Confirms textile electrodes are viable for exercise EMG
- Fabrication method (laser cut + heat press) is accessible for rapid prototyping
- BUT fixed electrode positions are a major limitation for our placement-validation phase
- Torso muscles were NOT tested in this study

---

## Dry vs. Wet Electrode Signal Quality During Exercise

| Factor | Wet Gel (Ag/AgCl Adhesive) | Dry Textile |
|---|---|---|
| Initial impedance | Low (~5 kOhm) | High (~50-500 kOhm) |
| Impedance after sweating | Degrades (gel dilution, adhesive weakening) | Improves (sweat acts as electrolyte) |
| Motion artifact | Moderate (adhesive helps) | Higher initially, improves with sweat |
| Long-term stability | Degrades (gel dries out in 1-2hr) | Stable if garment maintains pressure |
| Skin prep needed | Yes (shave, abrade, alcohol) | Minimal (moistening helps) |
| Repositioning | Easy (peel and re-stick, new electrode) | Requires garment modification |

**Bottom line for 10-day prototype:** Adhesive electrodes give better signal quality out of the box with zero garment fabrication, but degrade during extended sessions. Textile electrodes require garment integration but improve with sweat during exercise.

---

## MediaPipe Pose Estimation Compatibility

MediaPipe Pose infers 33 3D body landmarks from RGB video. It does NOT require bare skin -- it is trained on clothed subjects and handles clothing variation. However:

- **Tight-fitting clothing** (compression shirts) works well -- landmarks are inferred from body contour
- **Loose/bulky wearables** with visible pods, straps, or cables may confuse landmark detection, especially at shoulders and hips
- **Wires crossing joints** may create visual artifacts that degrade tracking
- **Best case for CV:** minimal coverage at shoulder, elbow, and hip joints

**Practical implication:** All form factors can work with MediaPipe, but straps/wires crossing shoulder and hip joints should be minimized. A compression shirt may actually be slightly better than shirtless-with-tape for CV, since it provides a clean silhouette without dangling wires.

---

## Vibrotactile Haptic Harness Research

A directly relevant 2024 paper presents a **modular toolkit for rapid prototyping of wearable vibrotactile haptic harnesses** (arxiv 2409.04579):

- Uses 3D-printed joints, laser-cut Tyvek/EVA foam tiles, elastic/nylon straps, and magnetic clasps
- Actuators attach via magnetic rings embedded in tiles or screw into grid positions
- Parametric CAD models allow rapid customization
- Quick don/doff via magnetic clasps
- Designed for body-mounted vibrotactile feedback -- directly applicable to our cueing system

**This design pattern is highly relevant for Option A (strap harness) and could be adapted to hold both EMG sensor pods and vibrotactile motors.**

---

## Form Factor Scoring Matrix

Scale: 1 (worst) to 5 (best)

| Criterion | A: Strap Harness | B: Compression Shirt | C: Shirtless + Adhesive | D: Hybrid (C then A/B) |
|---|---|---|---|---|
| **1. Iteration speed** (change electrode positions) | 4 - snap pods to new strap positions | 2 - must re-sew/re-laminate pockets | 5 - peel off, stick on new spot in 30sec | 5 (days 1-3) / 4 (days 4-10) |
| **2. Electrode contact quality** (sweat, dynamic movement) | 3 - pressure-dependent, may shift during lifts | 4 - compression maintains contact, improves with sweat | 4 - adhesive + skin prep = reliable, but degrades over session | 4-5 |
| **3. CV compatibility** (MediaPipe joint visibility) | 4 - bare skin between straps, but straps near shoulders may occlude | 3 - full torso coverage, works but less ideal for shoulder/hip landmarks | 5 - bare skin everywhere, only small electrodes and taped wires | 5 then 4 |
| **4. Build time to first test** | 3 - need to source/sew straps, print snap mounts (2-3 days) | 2 - need shirt + electrode fabrication + wiring (3-5 days) | 5 - order electrodes + tape, test same day | 5 then 3 |
| **5. Micro-adjustability during session** | 4 - slide pods along straps, re-velcro | 1 - positions fixed until garment reworked | 5 - peel and re-place in seconds | 5 then 4 |
| **TOTAL** | **18** | **12** | **24** | **23-24** |

---

## Detailed Option Analysis

### Option A: Adjustable Strap Harness
**Pros:**
- Reusable across sessions without new electrodes
- Can integrate both EMG pods and vibrotactile motors on same strap infrastructure
- Modular haptic harness research (2024 paper) provides proven design pattern
- Good CV compatibility (bare skin between straps)

**Cons:**
- 2-3 day build time before first test
- Strap tension affects electrode contact quality -- hard to get consistent pressure across all torso muscles
- Pec and lat muscles require different strap routing than erector spinae
- Compound lift bar paths (bench press bar on chest, squat bar on traps) may conflict with strap placement

**Risk:** Straps shift during heavy compound lifts, especially during bench press (chest compression) and barbell rows (back contraction changes torso circumference).

### Option B: Compression Shirt
**Pros:**
- Ohiri et al. 2022 confirms textile electrode signal quality comparable to adhesive
- Sweat actually improves contact during exercise
- Clean, professional appearance
- 16-channel amplifier proven in literature

**Cons:**
- Electrode positions fixed at fabrication -- devastating for a placement-validation phase
- 3-5 day build time minimum
- Torso muscles NOT validated in Ohiri study (only limbs tested)
- Athos/Enflux/Myontec failure pattern: comfort, washability, sizing across users
- MediaPipe may have slightly harder time with shoulder/hip landmarks under full shirt

**Risk:** You spend 5 days building a shirt, discover electrode positions are wrong, and have to rebuild.

### Option C: Shirtless + Adhesive Electrodes
**Pros:**
- Fastest path to data (order electrodes, test day 1)
- Maximum placement flexibility -- try 20 different positions in one session
- Gold standard signal quality with proper skin prep
- Perfect CV compatibility (bare skin everywhere)
- This is literally what every EMG research lab uses for initial studies

**Cons:**
- Wire management is tedious and fragile during dynamic lifts
- Adhesive weakens with sweat over 30-60 min sessions
- Electrodes are consumable (cost per session)
- Not a viable product form factor -- prototype only
- Looks "lab experiment," not "product demo"

**Risk:** Wires catch on barbells/bench during compound lifts. Electrode adhesion fails mid-set.

### Option D: Modular Hybrid (C -> A or B)
**Pros:**
- Captures the best of both worlds: fast validation then stable platform
- Days 1-3 with adhesive electrodes answer "where should electrodes go?" before committing
- Days 4-10 build the right thing with confirmed positions
- Minimizes wasted fabrication time

**Cons:**
- Requires planning two build phases
- Day 3-4 transition creates a "dead day" for building

**Risk:** If placement validation takes longer than 3 days, the build phase gets compressed.

---

## Wire Management Approaches for Option C

Based on research protocols:
1. **Pre-amplified electrodes** (like Delsys Trigno sensors) eliminate long wire runs -- signal is digitized at the electrode. Most effective but expensive ($200+/sensor).
2. **Short lead wires** to a body-mounted amplifier board (e.g., OpenBCI Cyton/Ganglion strapped to waist). Keep leads under 15cm.
3. **Tape leads flat** against skin using medical tape (Tegaderm or Transpore), creating strain relief loops near electrodes.
4. **Route wires away from joints** -- run along torso midline, not across shoulders or hips.
5. **Elastic band overwrap** -- after placing electrodes and routing wires, wrap a light elastic bandage (Coban) over the wire runs for additional security during dynamic movement.

---

## Recommendation

### Phase 1: Testing / Placement Validation (Days 1-10)

**Use Option D (Hybrid): Start with Option C, transition to Option A.**

**Days 1-3: Shirtless + Adhesive Electrodes (Option C)**
- Order: Ag/AgCl snap electrodes (100-pack), medical tape, conductive gel, skin prep supplies
- Goal: Validate electrode positions for each target muscle during each compound lift
- Test protocol: Record sEMG during bench, squat, deadlift, row, push-up
- Mark optimal positions with skin-safe marker
- Document which positions give clean signal vs. movement artifact
- Also test vibrotactile motor positions (tape ERM motors to skin)
- This is the research-standard approach and maximizes learning per day

**Days 4-7: Build Strap Harness (Option A) with confirmed positions**
- Use modular haptic harness design pattern (3D-printed snap mounts, elastic straps, magnetic clasps)
- Strap layout: chest band + waist band + shoulder Y-harness + optional lateral straps for lats/serratus
- Mount sensor pods at validated positions using velcro/snap attachments
- Integrate vibrotactile motors into same strap infrastructure
- Route wires through strap channels

**Days 8-10: Integration Testing**
- Test full system (EMG + vibrotactile + CV pipeline) with harness
- Validate signal quality matches adhesive baseline from days 1-3
- Iterate on strap tension and pod mounting
- Test with MediaPipe to confirm joint landmark detection with harness on

### Phase 2: Demo / Product Phase (Post-Validation)

**Build toward Option B (Compression Shirt) with validated electrode positions.**

Once electrode positions are confirmed and the signal processing pipeline is proven:
- Use Ohiri et al. fabrication method (laser cut + heat press conductive textile electrodes)
- Integrate into athletic compression shirt with pre-routed conductive traces
- Embed vibrotactile motors in fabric
- Target 16-channel Intan amplifier or equivalent
- Design for the 2-3 body sizes that cover your demo audience

**Rationale for shirt in product phase:**
- Professional appearance for demos
- Sweat actually improves contact (good for real workouts)
- Reproducible donning -- no fidgeting with straps
- Clean silhouette works well with MediaPipe

**Do NOT build the shirt during the prototyping phase.** The Athos lesson is clear: fixed electrode positions in a garment are only viable after exhaustive placement validation.

---

## Bill of Materials: Days 1-3 (Option C Quick Start)

| Item | Est. Cost | Source |
|---|---|---|
| Ag/AgCl snap electrodes (100-pack) | $15 | Amazon/DigiKey |
| Conductive electrode gel (Ten20) | $12 | Amazon |
| Medical tape (Transpore 3M) | $5 | Pharmacy |
| Skin prep (NuPrep abrasive gel) | $8 | Amazon |
| Disposable razors | $5 | Pharmacy |
| Isopropyl alcohol 70% | $3 | Pharmacy |
| Elastic bandage wrap (Coban) | $5 | Pharmacy |
| Skin-safe marker | $3 | Pharmacy |
| **Total** | **~$56** | |

(Assumes EMG amplifier board and vibrotactile motors already sourced separately.)

---

## Sources

- [Ohiri et al. 2022 - E-textile based modular sEMG suit](https://pmc.ncbi.nlm.nih.gov/articles/PMC9187645/)
- [Modular Toolkit for Rapid Prototyping of Wearable Vibrotactile Haptic Harness (2024)](https://arxiv.org/abs/2409.04579v1)
- [The Failure of Athos Wearable Technology](https://www.kennethhurley.com/blog/the-failure-of-athos-wearable-technology)
- [Delsys Trigno Wireless EMG System](https://delsys.com/trigno/)
- [EMG activity in deadlift exercise - systematic review](https://pmc.ncbi.nlm.nih.gov/articles/PMC7046193/)
- [Kinematic and EMG Activity Changes during Back Squat](https://pmc.ncbi.nlm.nih.gov/articles/PMC5435978/)
- [Surface EMG Analysis of Three Squat Exercises](https://pmc.ncbi.nlm.nih.gov/articles/PMC6714362/)
- [Comparison of Signal Processing Methods for Reducing Motion Artifacts in HD-EMG](https://pmc.ncbi.nlm.nih.gov/articles/PMC8974705/)
- [Wearable EMG Measurement Device Using Polyurethane Foam for Motion Artifact Suppression](https://www.mdpi.com/1424-8220/24/10/2985)
- [Recent Advances in Textile Electrodes for Wearable Biopotential Signal Monitoring](https://pmc.ncbi.nlm.nih.gov/articles/PMC10377545/)
- [Vibrotactile feedback as a tool to improve motor learning - systematic review](https://pmc.ncbi.nlm.nih.gov/articles/PMC5530110/)
- [JMIR - Vibrotactile Feedback Strategies for Trunk-Stabilizing Exercises](https://formative.jmir.org/2025/1/e62903)
- [Smart Garment for sEMG Monitoring (2026)](https://link.springer.com/article/10.1007/s12221-026-01395-8)
- [3D Printed EMG Sensing Systems (2023)](https://advanced.onlinelibrary.wiley.com/doi/10.1002/adsr.202300003)
- [High-Density EMG for Gesture-Based Control](https://www.nature.com/articles/s44182-025-00018-3)
