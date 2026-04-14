# Final Buy List — 2026-04-08 (v2)

> Synthesized from Tracks 1-4 + core muscle research + textile electrode feasibility.
> Budget: ~$700 across 4 Ramp cards. Time-priority: sensors are the bottleneck.
> Ordering tonight (Tue Apr 8). All ETAs assume order placed by 11pm CT.

---

## Design Decisions Driving This List

1. **Muscle targets (10ch MVP):** Erector spinae L/R, upper trap L/R, pec major L/R, lat dorsi L/R, **external obliques L/R**
2. **Form factor:** Option D Hybrid — adhesive electrodes (days 1-3) → strap harness (days 4-7) → integration (days 8-10). Textile garment prototype in parallel on days 5-7.
3. **Sensor strategy:** 3x MyoWare NOW (Amazon next-day) for immediate testing while 10x BioAmp EXG Pill ships from Crowd Supply (5-7 days). Don't wait.
4. **Hedging:** Order for 10+ channels. Budget covers injury-prevention + hypertrophy + alignment use cases.

---

## Table 1: Order NOW — Amazon Same-Day / Next-Day

| Item | Qty | Price | Card | ETA | Use Case |
|---|---|---|---|---|---|
| | | | | | |
| **-- sEMG Sensors --** | | | | | |
| MyoWare 2.0 Muscle Sensor (DEV-21265) | 3 | $114 | Rajat | **Wed Apr 9** | Immediate 3ch testing: erector spinae + oblique + trap |
| | | | | | |
| **-- MCU --** | | | | | |
| ESP32-S3 DevKitC-1 (N16R8) | 2 | $20 | Rajiv | **Wed Apr 9** | Vest MCU + spare |
| | | | | | |
| **-- Electrodes & Skin Prep --** | | | | | |
| Ag/AgCl snap electrodes 100-pack | 3 | $24 | Kelsi | **Wed Apr 9** | 300 electrodes for 10-day placement testing |
| Ten20 conductive paste 4oz | 1 | $12 | Kelsi | **Wed Apr 9** | Electrode-skin interface |
| NuPrep skin prep gel 4oz | 1 | $8 | Kelsi | **Wed Apr 9** | Abrasive prep for low impedance |
| 3M Transpore medical tape 1" x2 | 1 | $5 | Kelsi | **Wed Apr 9** | Wire management on skin |
| Coban self-adhering wrap 2" | 2 | $6 | Kelsi | **Wed Apr 9** | Overwrap for wire runs during lifts |
| Disposable razors 10-pack | 1 | $5 | Kelsi | **Wed Apr 9** | Electrode site hair removal |
| Isopropyl alcohol 70% 16oz | 1 | $3 | Kelsi | **Wed Apr 9** | Skin cleaning |
| Skin-safe marker (surgical) | 2 | $6 | Kelsi | **Wed Apr 9** | Mark validated electrode positions |
| | | | | | |
| **-- Cueing (Vibrotactile) --** | | | | | |
| ERM coin vibe motors 10mm, 10-pack | 2 | $14 | Rajiv | **Wed Apr 9** | 20 motors — cueing zones + spares |
| | | | | | |
| **-- Power --** | | | | | |
| 1200mAh LiPo 3.7V (JST-PH 2.0) | 3 | $15 | Aaron | **Wed Apr 9** | Vest power + spares |
| TP4056 USB-C LiPo charger module | 3 | $4 | Aaron | **Wed Apr 9** | Charging |
| | | | | | |
| **-- Wiring --** | | | | | |
| 30AWG silicone wire kit (6 colors) | 1 | $8 | Rajiv | **Wed Apr 9** | Signal wiring |
| Shielded cable 4-conductor 30AWG 5m | 1 | $8 | Rajiv | **Wed Apr 9** | sEMG signal runs (low noise) |
| Mini breadboard 400-point | 4 | $10 | Aaron | **Wed Apr 9** | Prototyping |
| Jumper wire kit (M-M, M-F, F-F) | 1 | $7 | Aaron | **Wed Apr 9** | Prototyping |
| | | | | | |
| **-- Harness Build (days 4-7) --** | | | | | |
| Elastic webbing 1" + buckles 10-pack | 1 | $12 | Rajiv | **Wed Apr 9** | Harness straps |
| Velcro adhesive hook+loop 1" x 5yd | 1 | $6 | Rajiv | **Wed Apr 9** | Pod mounting on straps |
| Neoprene fabric 2mm 12"x24" | 1 | $8 | Rajiv | **Wed Apr 9** | Strap padding, pod backing |
| Snap button kit (press studs, 100pc) | 1 | $6 | Aaron | **Wed Apr 9** | Electrode-to-pod connections |
| | | | | | |
| **-- Textile Garment Prototype --** | | | | | |
| Compression shirts (athletic, M+L) | 2 | $20 | Aaron | **Wed Apr 9** | Base garment for textile electrode prototype |
| Adafruit woven conductive fabric 20x20cm | 2 | $10 | Rajiv | **Wed Apr 9** | Textile electrode patches (~12+ electrodes) |
| 12mm snap connector kit | 1 | $10 | Aaron | **Wed Apr 9** | Snap-connect textile electrodes to wires |
| Conductive thread (silver-coated, 50ft) | 1 | $12 | Rajiv | **Thu Apr 10** | Traces between electrode patches (2-day) |
| | | | | | |
| **Amazon Subtotal** | | **~$353** | | | |

### Card Split — Amazon

| Card | Limit | Items | Subtotal |
|---|---|---|---|
| **Rajiv** | $215.52 | ESP32 x2, vibes x2, wire, shielded cable, elastic, velcro, neoprene, conductive fabric x2, conductive thread | ~$108 |
| **Rajat** | ~$300 | MyoWare 2.0 x3 | ~$114 |
| **Kelsi** | ~$80 | Electrodes x3, Ten20, NuPrep, tape, Coban, razors, alcohol, markers | ~$69 |
| **Aaron** | ~$100 | LiPo x3, TP4056 x3, breadboards, jumpers, snaps (press + 12mm), compression shirts | ~$62 |

---

## Table 2: Order NOW — Mouser / Crowd Supply (2-7 day delivery)

| Item | Qty | Price | Source | ETA | Use Case |
|---|---|---|---|---|---|
| | | | | | |
| **-- sEMG Sensors (main build) --** | | | | | |
| BioAmp EXG Pill (Upside Down Labs) | 10 | $80 | Crowd Supply | **Mon-Wed Apr 14-16** | 10ch MVP. $8/ch. Ships from Portland OR, ground to Austin ~5-7 biz days |
| | | | | | |
| **-- Muxing --** | | | | | |
| CD4051BE 8:1 analog mux | 4 | $3 | Mouser | **Thu Apr 10** | Mux 10 BioAmp channels → ESP32 ADC. Overnight ground from Mansfield |
| | | | | | |
| **-- Cueing (TSA) --** | | | | | |
| DRV8833 dual H-bridge driver | 4 | $8 | Mouser | **Thu Apr 10** | TSA motor + vibe motor control |
| N20 gearmotor 6V 100RPM | 4 | $12 | Mouser | **Thu Apr 10** | TSA squeeze actuators (2 active + 2 spare) |
| INA219 current sensor breakout | 2 | $4 | Mouser | **Thu Apr 10** | TSA force proxy via motor current |
| SS49E linear hall sensor | 4 | $4 | Mouser | **Thu Apr 10** | TSA position feedback |
| | | | | | |
| **-- TSA Mechanical --** | | | | | |
| Dyneema braided line 50lb 25m | 1 | $8 | Amazon 2-day | **Thu Apr 10** | TSA string |
| PTFE tubing 1.5mm ID, 5m | 1 | $5 | Amazon 2-day | **Thu Apr 10** | TSA Bowden-style routing channels |
| | | | | | |
| **Wave 2 Subtotal** | | **~$124** | | | |

### Card Split — Mouser/Crowd Supply

| Card | Items | Subtotal |
|---|---|---|
| **Rajat** (~$186 remaining) | BioAmp x10 ($80) + Mouser order ($31) + Dyneema + PTFE ($13) | ~$124 |

---

## Table 3: Order AFTER First Test Results (Days 4-6)

*Hold budget in reserve. Only order if testing reveals specific gaps.*

| Item | Qty | Price | Source | ETA (if ordered day 4) | Trigger Condition |
|---|---|---|---|---|---|
| ADS1292R breakout (2ch, 24-bit) | 2 | $50 | SparkFun | **Mon Apr 14** | BioAmp too noisy for MDF spectral analysis |
| DRV2605L + LRA haptic driver | 4 | $32 | SparkFun | **Mon Apr 14** | ERM coin vibes can't be localized on torso |
| Precision Microdrives 310-103 LRA | 6 | $30 | Precision Microdrives | **Wed Apr 16** | Need tighter frequency control for cueing |
| Pololu 25D metal gearmotor + encoder | 2 | $50 | Pololu (Las Vegas) | **Mon Apr 14** | N20 TSA squeeze force insufficient (need >15N) |
| nRF52840 DK | 1 | $40 | Mouser | **Mon Apr 14** | ESP32 BLE throughput can't sustain 10ch x 500Hz |
| LessEMF A321 silver Lycra fabric | 1 | $35 | LessEMF | **Wed-Fri Apr 16-18** | Want higher-quality textile electrodes for demo garment |
| 3D printer filament PETG 1kg | 1 | $20 | Micro Center | **Same day** | Pod housings for harness build |
| | | | | | |
| **Wave 3 Subtotal (max)** | | **~$257** | | | |

### Wave 3 Card Assignment

| Card | Remaining Budget | Available For |
|---|---|---|
| **Rajiv** | ~$108 | ADS1292R ($50) + DRV2605L ($32) + PETG ($20) = $102 |
| **Rajat** | ~$62 | Precision Microdrives ($30) + LessEMF ($35)... over by $3. Move LessEMF to Rajiv |
| **Rajiv revised** | ~$108 | ADS1292R ($50) + LessEMF ($35) = $85. DRV2605L to Rajat |
| **Rajat revised** | ~$62 | DRV2605L ($32) + Precision Microdrives ($30) = $62 |
| **Kelsi** | ~$11 | Consumable restock (electrodes, tape) |
| **Aaron** | ~$38 | nRF52840 ($40)... $2 over. Move PETG ($20) to Rajiv, nRF to Aaron at $38 budget |

**Final Wave 3 card plan:**

| Card | Wave 3 Items | Wave 3 Spend | Grand Total | Under Limit? |
|---|---|---|---|---|
| **Rajiv** | ADS1292R ($50) + LessEMF ($35) + PETG ($20) | $105 | $213 | Yes ($2.52 margin) |
| **Rajat** | DRV2605L ($32) + Precision Microdrives ($30) | $62 | $300 | At limit |
| **Kelsi** | Consumable restock | $11 | $80 | At limit |
| **Aaron** | nRF52840 ($40) | $38* | $100 | At limit |

*nRF52840 DK may be $35-40; pick the SKU that fits.

---

## Budget Summary

| Wave | Spend | Status |
|---|---|---|
| Wave 1: Amazon (tonight) | ~$353 | Order tonight |
| Wave 2: Mouser/Crowd Supply (tonight) | ~$124 | Order tonight |
| **Day 0 total commit** | **~$477** | |
| Wave 3: After testing (days 4-6) | up to ~$222 | Hold — conditional |
| **Grand total if all waves** | **~$699** | Within $700 budget |

### Per-Card Grand Totals

| Card | Limit | W1 | W2 | W3 (max) | Total | Margin |
|---|---|---|---|---|---|---|
| Rajiv | $215.52 | $108 | $0 | $105 | $213 | $2.52 |
| Rajat | ~$300 | $114 | $124 | $62 | $300 | $0 |
| Kelsi | ~$80 | $69 | $0 | $11 | $80 | $0 |
| Aaron | ~$100 | $62 | $0 | $38 | $100 | $0 |

---

## Arrival Timeline

```
Tue Apr  8  TONIGHT: Place all Wave 1 + Wave 2 orders

Wed Apr  9  ████████████████████ Amazon next-day arrives
            MyoWare x3, ESP32 x2, electrodes x300, skin prep,
            vibe motors x20, LiPo x3, breadboards, wire,
            harness materials, conductive fabric, compression shirts
            → START adhesive electrode placement testing

Thu Apr 10  ████████████ Mouser overnight + Amazon 2-day arrives
            CD4051 mux x4, DRV8833 x4, N20 motors x4,
            INA219 x2, hall sensors x4, Dyneema, PTFE,
            conductive thread
            → START TSA prototyping, mux circuit build

Fri Apr 11  (build day — no new arrivals expected)
            → Continue placement validation, begin harness layout

Sat Apr 12  (build day)
            → Harness build with confirmed positions

Sun Apr 13  (build day)
            → Textile garment prototype (sew conductive fabric into shirt)

Mon Apr 14  ████████ BioAmp EXG Pills MAY arrive (optimistic)
            → If arrived: build 10ch mux circuit
            → DECISION POINT: Wave 3 needed?

Tue Apr 15  (integration day)

Wed Apr 16  ████ BioAmp arrival (conservative estimate)
            → 10ch build if not already started
            
Thu Apr 17  (full system testing)

Fri Apr 18  (demo prep)
```

### Critical Path Risk

**BioAmp is the bottleneck.** Crowd Supply ships from Portland OR — ground to Austin TX is 5-7 business days. If ordered tonight (Tue), ships Wed/Thu, arrives **Mon-Wed Apr 14-16**.

**Mitigation:** MyoWare x3 arrives Wed Apr 9. Test with 3 channels (erector spinae + oblique + trap OR pec) on days 1-4 while BioAmp ships. If BioAmp is backordered, order 2 more MyoWare from Amazon ($76, on Rajiv's card with $2.52 margin... too tight. Use Rajat's Wave 3 budget instead).

---

## Updated MVP Channel Map (10 channels)

```
        POSTERIOR VIEW                    ANTERIOR VIEW

          [UT-L]    [UT-R]              
   Upper Trap L/R — Ch 1,2              
                                         [PEC-L]    [PEC-R]
          [LD-L]    [LD-R]              Pec Major L/R — Ch 5,6
   Lat Dorsi L/R — Ch 3,4              
                                         [OBL-L]    [OBL-R]
          [ES-L]    [ES-R]              Ext Oblique L/R — Ch 9,10
   Erector Spinae L/R — Ch 7,8         
```

### Muxing Plan for 10 Channels

- 2x CD4051 (8:1 mux each) → 2 ESP32 ADC pins
- Mux A: Ch 1-8 (UT, LD, PEC, ES)
- Mux B: Ch 9-10 (OBL) + 6 open slots for Tier 2 expansion
- Sample rate: 500Hz per channel → 5kHz aggregate mux switching rate (well within CD4051 spec)

---

## What This Buy List Validates

| Question | Components | Days | Arrival Gate |
|---|---|---|---|
| Clean sEMG from torso during compound lifts? | MyoWare + Ag/AgCl + skin prep | 1-3 | Wed Apr 9 |
| Vibe cue localization on torso? | Coin vibes + TPD protocol | 2-3 | Wed Apr 9 |
| Optimal electrode positions per muscle? | Adhesive electrodes + skin marker | 1-4 | Wed Apr 9 |
| L/R oblique asymmetry detectable? | MyoWare bilateral oblique pair | 1-3 | Wed Apr 9 |
| TSA squeeze feels like "trainer's hand"? | N20 + Dyneema + PTFE at pec zone | 5-7 | Thu Apr 10 |
| 10ch simultaneous acquisition works? | BioAmp x10 + CD4051 mux + ESP32 | 6-8 | Apr 14-16 |
| Textile electrodes viable for demo? | Conductive fabric + compression shirt | 5-7 | Wed Apr 9 |
| MDF fatigue shift precedes form breakdown? | BioAmp + ESP32 + spectral analysis | 6-8 | Apr 14-16 |
| Closed loop: sense → reason → cue? | Full system integration | 8-10 | Apr 14-16 |
| MediaPipe tracks joints with harness on? | Phone + harness | 8-10 | Wed Apr 9 |

---

## Micro Center Austin (10900 Domain Dr) — Optional Same-Day

Worth a trip for soldering supplies if not already owned. Charge to Aaron.

| Item | Price | Need By |
|---|---|---|
| Soldering iron + solder | ~$25 | Day 4 (harness build) |
| Heat shrink tubing assortment | ~$5 | Day 4 |
| 3D printer filament PETG 1kg | ~$20 | Day 5 (pod housings) |

---

## Competitor Context

**Strive** (strive.tech) validates our approach: $6M raised, 215+ pro teams, textile EMG compression shorts. They cover lower body only, no real-time cueing, no CV, coach-dependent. Our advantages: torso coverage, closed-loop haptic cueing, phone CV, works without a coach. Their existence proves the garment + EMG market is real.

---

## Reconciliation with Rajat

Rajat's 4ch spec (erector spinae L/R + quad VL/VM) is a subset. Our 10ch vest includes erector spinae + adds traps, pecs, lats, obliques. Only quads are deferred (leg band V2). Both specs converge on BioAmp, ESP32, Ag/AgCl, coin vibes, adhesive-first testing. The body-region disagreement is resolved: erector spinae IS on the torso, and obliques (Rajat's core stability concern) are now Tier 1.
