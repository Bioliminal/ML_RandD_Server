# Critical Muscle Map for sEMG Torso Vest

> Prioritized sensor placement guide for a weightlifting coaching vest using sEMG to detect fatigue, compensation, and L/R asymmetry.
>
> Compiled 2026-04-08 from SENIAM guidelines, EMG research, and TPD/wearability constraints.

---

## Table of Contents

1. [Background: Key Measurement Principles](#background)
2. [Two-Point Discrimination & Vibrotactile Constraints](#tpd)
3. [Tier 1 -- Must-Have MVP](#tier-1)
4. [Tier 2 -- Nice-to-Have (High Value)](#tier-2)
5. [Tier 3 -- V2 / Future Expansion](#tier-3)
6. [MVP Sensor Map Summary](#mvp-sensor-map)
7. [References](#references)

---

<a id="background"></a>
## 1. Background: Key Measurement Principles

| Signal | What It Detects | Method |
|---|---|---|
| **MDF shift** (median frequency decline) | Local muscle fatigue | Spectral analysis; MDF decreases linearly with fatigue depth (De Luca 1997; Gonzalez-Izal et al. 2012) |
| **Compensation timing** | Early-firing synergists stealing load from prime movers | Onset latency comparison between channels (e.g., upper trap fires before lower trap during overhead press) |
| **L/R asymmetry ratio** | Bilateral imbalance | Symmetry index; >15% asymmetry is a common clinical flag (Impellizzeri et al. 2007) |
| **Co-activation level** | Excessive bracing / spinal loading | Ratio of agonist-to-antagonist amplitude; excessive co-contraction increases compressive spinal load (Marras & Granata 1997) |
| **Mind-muscle activation** | Internal focus engagement | Amplitude increase at submaximal loads (<60% 1RM) confirms attentional engagement (Calatayud et al. 2016; Schoenfeld & Contreras 2016) |

---

<a id="tpd"></a>
## 2. Two-Point Discrimination & Vibrotactile Constraints

TPD determines minimum spacing for vibrotactile actuators (feedback) co-located with sEMG electrodes. Note: sEMG electrode spacing follows SENIAM (20 mm inter-electrode), but actuator spacing must respect tactile acuity.

| Body Region | Static TPD (mm) | Vibrotactile Threshold (mm) | Source |
|---|---|---|---|
| Fingertips | 1--2 | -- | Weinstein 1968 |
| Chest (anterior) | 30--40 | ~20--30 | Weinstein 1968; Van Erp 2005 |
| Upper back (scapular) | 30--40 | ~20--30 | Weinstein 1968; Eskildsen et al. 1969 |
| Lower back (lumbar) | 35--45 | ~30 | Weinstein 1968 |
| Lateral torso | 30--40 | ~20 | Van Erp 2005 |
| Shoulder / deltoid | ~40 | ~30 | Weinstein 1968 |

**Design implication:** Vibrotactile actuators on the torso need minimum 20--30 mm spacing. sEMG electrode pairs (20 mm IED per SENIAM) fit comfortably within these constraints. Co-locating an actuator with each sensor channel is feasible.

---

<a id="tier-1"></a>
## 3. Tier 1 -- Must-Have MVP (8 channels, 4 bilateral pairs)

These muscles provide the highest injury-prevention and coaching value per channel. Each is measured bilaterally (L/R pair).

---

### 3.1 Erector Spinae -- Lumbar (L/R)

| Attribute | Detail |
|---|---|
| **Why it matters** | **Injury prevention (primary).** Fatigue of lumbar erectors during deadlifts/squats causes increased lumbar flexion and up to 36% greater bending moment, directly increasing disc injury risk (Potvin & Norman 1993; Dolan & Adams 1998). MDF shift in erector spinae is the single most validated real-time fatigue signal in sEMG literature. |
| **sEMG signal** | MDF shift (fatigue), L/R asymmetry ratio, co-activation with abdominals |
| **SENIAM placement** | **Longissimus at L1:** 2 cm lateral to L1 spinous process, electrodes oriented cranio-caudally along fiber direction. **Iliocostalis at L2:** at the level of L2, medial to the line from posterior superior iliac spine to lowest point of lateral rib border. IED = 20 mm. |
| **Placement considerations** | Large flat surface, minimal curvature. Low crosstalk risk (wide muscle). Motion artifact moderate during heavy lifts -- use active electrodes with short leads. ECG artifact minimal (distance from heart). |
| **Priority justification** | Strongest evidence base for injury prevention. Fatigue here = stop the set. Non-negotiable for MVP. |

---

### 3.2 Upper Trapezius (L/R)

| Attribute | Detail |
|---|---|
| **Why it matters** | **Compensation detection.** The most common compensator in untrained lifters: overactive upper trap substitutes for weak lower trap and serratus anterior during overhead pressing, rowing, and even bench press (Cools et al. 2007). UT:LT ratio >3.15 is associated with subacromial impingement (Cools et al. 2004). Also critical for shrug detection -- an involuntary shrug during lateral raises or overhead press signals fatigue or excessive load. |
| **sEMG signal** | Compensation timing (early onset relative to prime movers), UT:LT activation ratio, L/R asymmetry |
| **SENIAM placement** | 50% on the line from acromion to C7 spinous process. Electrodes oriented along the line from acromion to C7. IED = 20 mm. Note: some researchers argue this captures middle fibers; for upper fibers specifically, place slightly more lateral toward acromion. |
| **Placement considerations** | Relatively flat surface at this landmark. Moderate motion artifact during dynamic lifts. Low crosstalk risk (well-isolated superficial muscle on upper shoulder). Vest strap/collar region provides good electrode contact. |
| **Priority justification** | Extremely high compensation detection value. Easy to instrument on a vest collar. Strong research base. |

---

### 3.3 Pectoralis Major -- Sternal Head (L/R)

| Attribute | Detail |
|---|---|
| **Why it matters** | **Prime mover for bench press; mind-muscle connection target; pec-delt balance.** The sternal head produces the majority of force during flat bench press. Internal focus on pecs increases pec EMG by ~6% at loads <60% 1RM (Calatayud et al. 2016). Monitoring pec:anterior delt ratio reveals whether the pec is the primary driver or whether the anterior delt is compensating (common in untrained lifters with poor retraction). L/R pec asymmetry is readily detectable and actionable. |
| **sEMG signal** | Amplitude (mind-muscle feedback), pec:delt activation ratio, L/R asymmetry, fatigue MDF shift |
| **Electrode placement** | On the sternocostal head: midway between sternoclavicular joint and anterior axillary line, at the level of the 4th intercostal space, oriented mediolaterally along fiber direction. IED = 20 mm. (Not in SENIAM; placement per Cram & Kasman 1998 and Rodriquez-Ridao et al. 2020.) |
| **Placement considerations** | **ECG artifact is the primary concern**, especially on left pec. Mitigation: high-pass filter at 20 Hz, adaptive ECG template subtraction. Moderate curvature on lateral chest. Crosstalk with anterior deltoid possible if electrode placed too superiorly -- keep below clavicle line. Chest hair may require shaving or dry electrode design. |
| **Priority justification** | Bench press is the most popular gym exercise. Pec activation feedback has strong mind-muscle research support. L/R asymmetry is immediately actionable. Worth tolerating ECG artifact challenges. |

---

### 3.4 Latissimus Dorsi (L/R)

| Attribute | Detail |
|---|---|
| **Why it matters** | **Prime mover for rows and pull-downs; often undertrained in beginners.** Weak lats lead to upper trap and bicep compensation during pulling movements. L/R lat asymmetry is common and directly detectable. Mind-muscle connection to lats is notoriously difficult for beginners -- EMG biofeedback has high coaching value here. |
| **sEMG signal** | Amplitude (mind-muscle / activation confirmation), L/R asymmetry, fatigue MDF shift, lat:upper trap ratio during rows |
| **Electrode placement** | Approximately 4 cm below the inferior angle of the scapula, over the muscle belly, oriented obliquely along fiber direction (inferomedial to superolateral). IED = 20 mm. (Not in SENIAM; per Cram & Kasman 1998, Lehman et al. 2004.) |
| **Placement considerations** | Large flat muscle belly on mid-back. Low curvature. Minimal crosstalk (well-separated from erector spinae at this location). Moderate motion artifact during dynamic rows. Vest panel sits naturally over this region. |
| **Priority justification** | High coaching value for beginners. Easy placement on vest back panel. Completes the push-pull pair with pec major. |

---

<a id="tier-2"></a>
## 4. Tier 2 -- Nice-to-Have (4 additional channels, 2 bilateral pairs)

These add significant value for shoulder health and core stability but can be deferred if channel count is limited.

---

### 4.1 Lower Trapezius (L/R)

| Attribute | Detail |
|---|---|
| **Why it matters** | **Critical scapular stabilizer, often inhibited.** The UT:LT ratio is a primary indicator of scapular dyskinesis and impingement risk (Cools et al. 2007). Lower trap weakness is one of the most common findings in shoulder pain populations. Monitoring LT activation during overhead press and rows can detect inhibition before injury develops. |
| **sEMG signal** | Activation amplitude (is it firing at all?), UT:LT ratio, onset timing relative to upper trap |
| **SENIAM placement** | 2/3 on the line from the trigonum spinae scapulae to the T8 spinous process, at an oblique angle (inferolaterally directed). IED = 20 mm. |
| **Placement considerations** | Moderate curvature over the scapular region. Risk of crosstalk with middle trapezius and infraspinatus -- precise placement is critical. Scapular movement during arm elevation shifts skin relative to muscle, increasing motion artifact. |
| **Priority justification** | Extremely high clinical value for shoulder health. The UT:LT ratio is arguably the single best scapular health metric. Deferred from MVP only because of placement difficulty on a garment (scapular movement). |

---

### 4.2 External Obliques (L/R)

| Attribute | Detail |
|---|---|
| **Why it matters** | **Rotational stability and anti-rotation.** During compound lifts (squats, deadlifts, overhead press), the obliques provide critical anti-rotation and anti-lateral-flexion stability. Asymmetric oblique activation during bilateral lifts reveals rotational compensation. Co-activation with erector spinae indicates trunk bracing strategy -- excessive bracing increases spinal compressive load (Marras & Granata 1997). |
| **sEMG signal** | L/R asymmetry (rotational compensation), co-activation ratio with erector spinae, activation amplitude during bracing |
| **SENIAM placement** | Midway between the anterior superior iliac spine (ASIS) and the lowest point of the rib cage, electrodes oriented along the line from the opposite rib cage to the ASIS (approximately 45-degree oblique). IED = 20 mm. |
| **Placement considerations** | Moderate curvature on lateral torso. Crosstalk with internal oblique and rectus abdominis is a concern -- oblique electrode angle helps discriminate. Breathing artifact at rest but less significant during loaded lifting. Vest side panel accommodates this placement naturally. |
| **Priority justification** | High value for core stability monitoring and rotational asymmetry detection. Pairs well with erector spinae for complete trunk assessment. |

---

<a id="tier-3"></a>
## 5. Tier 3 -- V2 / Future Expansion

These muscles have real value but face practical challenges (crosstalk, placement difficulty, garment design complexity) that make them better suited for a future hardware revision.

---

### 5.1 Middle Trapezius / Rhomboids

| Attribute | Detail |
|---|---|
| **Why it matters** | Scapular retraction during rows. Postural muscle -- weak mid-trap/rhomboids correlate with forward shoulder posture. Important for row form assessment. |
| **sEMG signal** | Activation amplitude during rows, onset timing |
| **SENIAM placement** | 50% on the line from the medial border of the scapula (at the level of the scapular spine) to the T3 spinous process. Oriented horizontally. IED = 20 mm. |
| **V2 rationale** | Crosstalk with lower trap and rhomboids is high (muscles overlap anatomically). Scapular movement creates significant electrode-muscle displacement. Value is partially captured by lat dorsi and lower trap channels. |

---

### 5.2 Serratus Anterior

| Attribute | Detail |
|---|---|
| **Why it matters** | Scapular protraction and upward rotation. Key for overhead pressing safety. Inhibition leads to scapular winging and impingement. Decreased neural drive in serratus anterior is detectable via sEMG in scapular dyskinesis populations (PMC 2024). |
| **sEMG signal** | Activation amplitude, serratus:upper trap ratio |
| **Electrode placement** | 7th intercostal space, anterior to latissimus dorsi, below the axilla. At the level of the inferior scapular angle. Electrodes oriented along the rib (horizontally). IED = 20 mm. (Per Cram & Kasman 1998; validated by recent sensor placement study, Barbero et al. 2022.) |
| **V2 rationale** | Placement is in the axillary region -- difficult to maintain electrode contact on a garment during dynamic movement. High crosstalk risk with latissimus dorsi and pectoralis major. Sweat pooling in this region. Very high value muscle but garment engineering is the bottleneck. |

---

### 5.3 Anterior Deltoid

| Attribute | Detail |
|---|---|
| **Why it matters** | Pressing synergist. Often compensates for weak pec during bench press (increased anterior delt activation when pec fatigues). Monitoring pec:anterior delt ratio would be ideal for bench press coaching. |
| **sEMG signal** | Pec:delt ratio, fatigue MDF shift during pressing |
| **SENIAM placement** | One finger width distal and anterior to the acromion, oriented along the line from acromion to thumb. IED = 20 mm. |
| **V2 rationale** | The deltoid is on the arm/shoulder cap, not the torso -- requires a sleeve or shoulder strap extension. Crosstalk with clavicular pec head. Value is partially inferred from pec major channel (if pec amplitude drops while the bar keeps moving, delt compensation is implied). |

---

### 5.4 Posterior Deltoid

| Attribute | Detail |
|---|---|
| **Why it matters** | Pulling synergist, often underdeveloped. Rear delt activation during rows and face pulls is a coaching target. |
| **sEMG signal** | Activation amplitude, L/R asymmetry |
| **SENIAM placement** | Approximately 2 cm below the lateral border of the scapular spine, over the posterior deltoid belly. Oriented along the line from acromion to elbow. IED = 20 mm. |
| **V2 rationale** | Same garment challenge as anterior delt (shoulder cap, not torso). Also partially inferred from lat dorsi activation patterns. Lower priority overall. |

---

### 5.5 Rectus Abdominis

| Attribute | Detail |
|---|---|
| **Why it matters** | Spinal flexion prevention during deadlifts/squats. Part of the trunk bracing system. |
| **sEMG signal** | Co-activation with erector spinae, bracing amplitude |
| **Electrode placement** | 3 cm lateral to the umbilicus, over the muscle belly, oriented vertically (cranio-caudally). IED = 20 mm. |
| **V2 rationale** | Anterior torso placement competes with pec sensors for vest real estate. Breathing artifact is significant. Co-activation information is partially captured by external oblique sensors. Lower incremental value. |

---

### 5.6 Erector Spinae -- Thoracic

| Attribute | Detail |
|---|---|
| **Why it matters** | Upper back extension and postural stability. Fatigue correlates with thoracic rounding during squats. Adds resolution to the lumbar erector spinae channels. |
| **sEMG signal** | MDF shift (fatigue), activation amplitude |
| **Electrode placement** | 2 cm lateral to T9 spinous process, oriented cranio-caudally. IED = 20 mm. |
| **V2 rationale** | Moderate incremental value over lumbar ES. Adds 2 more channels. Better suited for expanded V2 vest with more channel budget. |

---

<a id="mvp-sensor-map"></a>
## 6. MVP Sensor Map

### Channel Budget: 8 sEMG channels (4 bilateral pairs)

```
                    POSTERIOR VIEW                          ANTERIOR VIEW

              [UT-L]            [UT-R]              
     Upper Trap L/R -- Ch 1,2                       
     (C7-acromion midpoint)                         
                                                     [PEC-L]      [PEC-R]
                                                    Pec Major L/R -- Ch 5,6
              [LD-L]            [LD-R]              (sternal head, 4th ICS)
     Lat Dorsi L/R -- Ch 3,4                        
     (4 cm below scap. inf. angle)                  
                                                    
                                                    
              [ES-L]            [ES-R]              
     Erector Spinae L/R -- Ch 7,8                   
     (2 cm lateral to L1)                           
```

### MVP Channel Allocation & Rationale

| Ch | Muscle | Side | Primary Signal | Key Coaching Use |
|---|---|---|---|---|
| 1 | Upper Trapezius | L | Compensation timing, UT:LT ratio* | Shrug detection, overhead press form |
| 2 | Upper Trapezius | R | Compensation timing, L/R asymmetry | Bilateral balance during rows/presses |
| 3 | Latissimus Dorsi | L | Amplitude, mind-muscle | Lat engagement during rows/pull-downs |
| 4 | Latissimus Dorsi | R | Amplitude, L/R asymmetry | Bilateral balance, fatigue detection |
| 5 | Pectoralis Major | L | Amplitude, pec:delt ratio** | Mind-muscle bench press coaching |
| 6 | Pectoralis Major | R | Amplitude, L/R asymmetry | Bilateral balance, fatigue detection |
| 7 | Erector Spinae (L1) | L | MDF shift (fatigue) | **STOP signal** -- fatigue = injury risk |
| 8 | Erector Spinae (L1) | R | MDF shift, L/R asymmetry | Bilateral balance, spinal load monitoring |

*\*UT:LT ratio requires Tier 2 lower trap channels for full computation; MVP can still detect absolute UT overactivation and shrug events.*

*\*\*Pec:delt ratio is approximate without dedicated anterior delt channel; inferred from pec amplitude drop during pressing.*

### What the MVP Covers

| Coaching Capability | Muscles Used | Detection Method |
|---|---|---|
| **Fatigue-based set termination** | Erector spinae L/R | MDF spectral shift >15% from baseline |
| **Shrug / upper trap compensation** | Upper trap L/R | Amplitude spike above threshold during non-shrug exercises |
| **Bench press mind-muscle coaching** | Pec major L/R | Real-time amplitude biofeedback at <60% 1RM |
| **Row / pull engagement confirmation** | Lat dorsi L/R | Amplitude confirmation (lat firing vs. not) |
| **L/R bilateral asymmetry (all exercises)** | All 4 pairs | Symmetry index; alert if >15% difference |
| **Compensation pattern detection** | Upper trap vs. lat dorsi | Relative timing and amplitude during rows |

### Upgrade Path

| Expansion | Channels Added | New Capability |
|---|---|---|
| **+Tier 2a: Lower Trap L/R** | +2 (10 total) | Full UT:LT ratio, scapular health metric |
| **+Tier 2b: External Oblique L/R** | +2 (12 total) | Rotational asymmetry, trunk bracing analysis, complete spinal co-contraction model |
| **V2 Full Suite** | +4--6 (16--18 total) | Serratus anterior, mid-trap, thoracic ES, anterior/posterior deltoid |

---

<a id="references"></a>
## 7. References

### SENIAM & Electrode Placement
- Hermens HJ, Freriks B, Disselhorst-Klug C, Rau G. Development of recommendations for SEMG sensors and sensor placement procedures. *J Electromyogr Kinesiol.* 2000;10(5):361-374. [PubMed](https://pubmed.ncbi.nlm.nih.gov/11018445/)
- SENIAM Project. Sensor location recommendations. [seniam.org](http://seniam.org/sensor_location.htm)
- Cram JR, Kasman GS. *Introduction to Surface Electromyography.* Aspen Publishers; 1998.
- Barbero M et al. Serratus anterior sEMG -- sensor placement and test position for normalization. *Med Eng Phys.* 2022. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1350453322000169)

### Fatigue & Injury Prevention
- Marras WS, Granata KP. The development of an EMG-assisted model to assess spine loading during whole-body free-dynamic lifting. *J Electromyogr Kinesiol.* 1997;7(4):259-268.
- Dolan P, Adams MA. Repetitive lifting tasks fatigue the back muscles and increase the bending moment acting on the lumbar spine. *J Biomech.* 1998;31(8):713-721. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0021929098000864)
- Potvin JR, Norman RW. Quantification of erector spinae muscle fatigue during prolonged dynamic lifting tasks. *Eur J Appl Physiol.* 1993;67(6):554-562. [Springer](https://link.springer.com/article/10.1007/BF00241654)
- De Luca CJ. The use of surface electromyography in biomechanics. *J Appl Biomech.* 1997;13(2):135-163.

### Mind-Muscle Connection
- Schoenfeld BJ, Vigotsky A, Contreras B, et al. Differential effects of attentional focus strategies during long-term resistance training. *Eur J Sport Sci.* 2018;18(5):705-712. [PubMed](https://pubmed.ncbi.nlm.nih.gov/29533715/)
- Calatayud J, Vinstrup J, Jakobsen MD, et al. Importance of mind-muscle connection during progressive resistance training. *Eur J Appl Physiol.* 2016;116(3):527-533. [PubMed](https://pubmed.ncbi.nlm.nih.gov/26700744/)
- Calatayud J, Vinstrup J, Jakobsen MD, et al. Mind-muscle connection training principle: influence of muscle strength and training experience during a pushing movement. *Eur J Appl Physiol.* 2017;117(7):1445-1452.

### Scapular Health & Compensation
- Cools AM, Witvrouw EE, Declercq GA, et al. Scapular muscle recruitment patterns: trapezius muscle latency with and without impingement symptoms. *Am J Sports Med.* 2003;31(4):542-549.
- Cools AM, Dewitte V, Lanszweert F, et al. Rehabilitation of scapular muscle balance. *Am J Sports Med.* 2007;35(10):1744-1751.
- Rodriguez-Ridao D, Antequera-Vique JA, Martin-Fuentes I, Muyor JM. Effect of five bench inclinations on the electromyographic activity of the pectoralis major, anterior deltoid, and triceps brachii. *Int J Environ Res Public Health.* 2020;17(19):7339. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7579505/)

### Two-Point Discrimination & Tactile Acuity
- Weinstein S. Intensive and extensive aspects of tactile sensitivity as a function of body part, sex, and laterality. In: Kenshalo DR, ed. *The Skin Senses.* Thomas; 1968:195-222.
- Van Erp JBF. Vibrotactile spatial acuity on the torso: effects of location and timing parameters. *Proc First Joint Eurohaptics Conf.* 2005.
- Eskildsen P, Morris A, Collins CC, Bach-y-Rita P. Simultaneous and successive cutaneous two-point thresholds for vibration. *Psychon Sci.* 1969;14(4):146-147.

### Asymmetry Detection
- Impellizzeri FM, Rampinini E, Maffiuletti N, Marcora SM. A vertical jump force test for assessing bilateral strength asymmetry in athletes. *Med Sci Sports Exerc.* 2007;39(11):2044-2050.
- Bishop C, Turner A, Read P. Effects of inter-limb asymmetries on physical and sports performance: a systematic review. *J Sports Sci.* 2018;36(10):1135-1144. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8488821/)

### Crosstalk & Signal Quality
- Farina D, Merletti R, Enoka RM. The extraction of neural strategies from the surface EMG: an update. *J Appl Physiol.* 2014;117(11):1215-1230.
- De Luca CJ, Gilmore LD, Kuber M, Thongpanja S. Filtering the surface EMG signal: Movement artifact and baseline noise contamination. *J Biomech.* 2010;43(8):1573-1579.

### Wearable sEMG Systems
- Orucu S, et al. Design and validation of multichannel wireless wearable sEMG system for real-time training performance monitoring. *J Healthc Eng.* 2019. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6754969/)
- Gong S, et al. A flexible wireless sEMG system for wearable muscle strength and fatigue monitoring in real time. *Adv Electron Mater.* 2023. [Wiley](https://advanced.onlinelibrary.wiley.com/doi/full/10.1002/aelm.202200916)
