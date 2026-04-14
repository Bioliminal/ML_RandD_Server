# Torso Vest Hardware Spec — Snapshot 2026-04-08 18:30

> Distilled from `hardware-configurations.html` (Session 3). This is an agent-friendly, content-dense capture of all design decisions, specifications, and rationale. The HTML file contains SVG diagrams and interactive tabs not reproduced here.

---

## 1. Form Factor Decision: Adjustable Strap-Harness (MVP)

**Decision (Session 3, 2026-04-08):** Adjustable strap-harness, NOT compression shirt, for MVP.

**Architecture:**
- Shoulder Y-harness (trap/delt pod zones)
- Chest band with adjustable buckle (pec pod zones)
- Ribcage band with adjustable buckle (lat/serratus pod zones)
- Optional waist band (core/oblique pod zones)
- All straps have velcro/snap zones for modular pod mounting
- Bare skin visible between straps for CV (MediaPipe) landmark tracking

**Why harness over shirt:**
- CV needs bare skin visible for joint keypoint detection (shoulders, elbows, hips)
- Adjustable buckles fit wide range of torso sizes without XS–XXL garment SKUs
- Pods are relocatable for iteration — critical during 10-day testing phase
- Electronics fully removable for washing

**Why not shirt (for now):**
- Fixed electrode positions can't adjust for anatomy during R&D
- Size-specific garments increase cost and reduce iteration speed
- Occludes torso skin, degrading CV accuracy
- Compression shirt is the *consumer product* form factor (post-MVP)

**Pivot from prior sessions:** Sessions 1-2 specified a compression arm sleeve for bicep curl MVP. Session 3 converted to torso vest per product direction (Lawson: torso is where most value lies for imbalance correction). The bicep curl → torso exercise pivot is NOT yet backed by primary literature — this is a Session 4 research task.

---

## 2. Target Muscle Groups & Channel Allocation

### Torso Spatial Resolution Constraints
| Body Region | Two-Point Discrimination | Distinguishable Cue Zones | Source |
|---|---|---|---|
| Chest (pecs) | 40–50mm | 2–3 per side | General TPD literature, extrapolated from hardware-handover.md torso range |
| Upper back (traps/rhomboids) | 50–60mm | 2 per side | Same |
| Lats | 40–55mm | 2–3 per side | Same |
| Delts (shoulder cap) | 35–45mm | 2–3 | Same |
| Core (obliques/rectus) | 40–55mm | 2 per side | Same |

**Note:** The per-region breakdown (chest 40-50mm, lats 40-55mm, etc.) is finer granularity than what's documented in hardware-handover.md, which only provides "Torso/back: 40-60mm" as a single range. See research-gaps.md for details.

### MVP Muscle Coverage (4 groups, 8 channels)
| Muscle Group | sEMG Channels | TSA Zones | Vibe Zones | Priority |
|---|---|---|---|---|
| Pecs (L/R) | 2 per side (4 total) | 1 per side | 1 per side | MVP |
| Lats (L/R) | 1–2 per side (2–4 total) | 1 per side | 1 per side | MVP |
| Upper Traps (L/R) | 1 per side (2 total) | — | 1 per side | MVP |
| Anterior Delts (L/R) | 1 per side (2 total) | — | 1 per side | MVP |

### Post-MVP Expansion
| Muscle Group | Channels | Priority |
|---|---|---|
| Mid Traps / Rhomboids | 1 per side (2) | Post-MVP |
| Posterior Delts | 1 per side (2) | Post-MVP |
| Core / Obliques | 1 per side (2) | Post-MVP |
| Lower Trap | 1 per side (2) | V2 |
| Serratus Anterior | 1 per side (2) | V2 |

### Athos Reference
Athos compression shirt uses ~14 EMG channels covering pecs, delts, lats, traps, biceps, triceps. **This channel count is referenced in the HTML but is NOT cited from a primary source — see research-gaps.md.**

---

## 3. Dual-Modality Cueing Architecture

**Core design decision:** Each cue zone supports BOTH a vibrotactile motor and a TSA contact pad, wired in parallel. Software selects which modality fires per cue event.

### Cueing Protocol
| Cue State | Vibration | TSA Pressure | When |
|---|---|---|---|
| **Correction** | Burst (spatial attention) | Onset (sustained pressure) | Wrong muscle dominant |
| **Reinforcement** | Off (would habituate) | Low sustained (Merkel/Ruffini) | Correct activation, maintain |
| **Fade** | Off | Gradual release | Testing motor independence |

### Why Dual-Modality
- Deshpande (2021): vibrotactile localization 60.7% vs force 54.6% — vibration better for spatial "where" cueing on torso
- Pacinian corpuscles (vibration) habituate in 5-15s — useless for sustained cueing
- Merkel/Ruffini (pressure) don't habituate — sustain signal through entire rep
- Software-switchable lets us A/B test modality effectiveness per muscle group without hardware changes

### MVP Implementation
- Wire both vibe + TSA at 2-4 key zones (pecs, lats)
- App toggles which fires per cue event
- Post-MVP: standardized 4-pin pod connectors (VCC, GND, SDA, SCL) enable physically swappable pods

### TSA on Torso — Distributed Motors
- **Problem:** Torso routing distances (pec to spine: 40-50cm) exceed 30-40cm practical max for PTFE-on-Dyneema string routing
- **Solution:** Distributed motors on straps near target muscle (<15-20cm routes)
- **Constraint:** One motor per independent squeeze zone (multi-string from one motor couples forces)
- **Friction budget:** ~10-30% force loss per 90-degree bend (PTFE-on-Dyneema, mu ~0.04-0.08)

---

## 4. Electrode Skin Contact

**sEMG requires direct skin contact.** Two approaches compatible with modular pods:

1. **MVP (disposable Ag/AgCl):** User applies adhesive electrode on bare skin, puts on harness, pod snaps onto strap over electrode via conductive snap stud. Simple, no fabric modification needed.
2. **Post-MVP (dry electrodes):** Pod has integrated dry electrode protruding through ~25mm fabric window in strap, held against skin by strap compression.

---

## 5. BOM — MVP Vest (Recommended Tier)

| Component | Qty | Part | Price |
|---|---|---|---|
| sEMG | 8ch | BioAmp EXG Pill | $80 |
| Analog mux | 2 | CD4051 8:1 | $2 |
| TSA (pec zones) | 2 | N20 + Dyneema + hall sensor | $50 |
| Vibrotactile | 6 | Precision Microdrives 310-103 | $15 |
| Motor drivers | 2 | DRV8833 | $4 |
| MCU | 1 | ESP32-S3 DevKit | $10 |
| Battery | 1 | 1200mAh LiPo + TP4056 | $10 |
| Electrodes | 100 | Ag/AgCl disposable | $8 |
| Harness | 1 | Adjustable nylon straps + buckles + PTFE | $25 |
| Wiring | — | Shielded 30AWG + snap studs + PCB | $15 |
| **Total** | | | **~$220** |

### Hedging (order extras for iteration)
| Item | Need | Order | Extra Cost |
|---|---|---|---|
| BioAmp EXG Pill | 8 | 10 | +$20 |
| Coin vibe motors | 6 | 20 | +$7 |
| N20 gearmotors | 2 | 4 | +$6 |
| Ag/AgCl electrodes | 50 | 200 | +$12 |
| ESP32-S3 DevKit | 1 | 2 | +$10 |
| Dyneema line | 5m | 25m | +$5 |
| DRV8833 | 2 | 4 | +$4 |
| **Hedge total** | | | **+$64** |

**Total Day 1 spend: ~$330** (MVP + hedging + spares)

### Upgrade Path
- sEMG too noisy on torso? → ADS1292R (+$25/2ch net)
- Vibe cues can't be localized? → LRA + DRV2605L (+$15/zone)
- TSA squeeze too weak? → Pololu 25D + encoder (+$25/zone)
- All working at budget tier? → Don't upgrade. Ship the demo.

---

## 6. Sourcing Strategy (Austin, TX)

**Priority: minimize delivery time. Sensors are the bottleneck.**

### Wave 1 — Order TODAY (arrives tomorrow)
- **Amazon same-day/next-day:** ESP32-S3 (x2), coin vibe motors (10-pack), Ag/AgCl electrodes (100-pack), LiPo batteries, mux breakouts, breadboards, elastic straps, velcro, neoprene
- **Micro Center Austin** (10900 Domain Dr): soldering supplies, breadboards, 3D printer filament
- **Subtotal: ~$115**

### Wave 2 — Order TODAY (arrives 2-3 days)
- **Mouser** (overnight ground from Mansfield TX): 10x BioAmp EXG Pill, DRV8833, INA219, snap buttons
- **Amazon 2-day:** Dyneema, PTFE tubing, N20 gearmotors, compression shirts for testing
- **Subtotal: ~$180**
- **Mouser will-call option:** 3hr drive to Mansfield, same-day pickup. Only if BioAmp is critical path.

### Wave 3 — AFTER initial testing validates
- Precision Microdrives 310-103, Pololu motors, DRV2605L + LRA, nRF52840, ADS1292R
- Don't pre-buy. Budget tier answers most questions first.

**AliExpress is OUT** for anything time-sensitive (2-4 week ship).

---

## 7. Signal Flow Architecture

```
Vest (BLE Peripheral)          Phone (Hub)
┌──────────────────┐          ┌──────────────────┐
│ 8-14ch sEMG      │──BLE──→ │ MediaPipe CV      │
│ via BioAmp+mux   │         │ sEMG envelope     │
│                  │         │ LLM Reasoning     │
│ TSA motors (2-6) │←─BLE──  │ Cue Engine        │
│ Vibe motors (6-8)│         │ Muscle Heatmap    │
│ ESP32-S3 MCU     │         │ L/R Symmetry      │
│ 1200mAh LiPo    │         │ Data Logging      │
└──────────────────┘          └──────────────────┘

Closed loop: Sense → Reason → Cue (~50-200ms)
BLE data rate: 14ch x 500Hz x 2 bytes = 14 kB/s
BLE 4.2 practical throughput: 20-30 kB/s (uses ~50-70%)
Consider 200Hz envelope for reliability margin.
```

**Phone-as-hub feasibility:** Validated in hardware-engineering-specs.md and kelsi-hybrid-spec.md. MediaPipe ~30fps GPU + BLE on separate threads. Feasible on phones from ~2022+. Risk: CV frame drops may cause BLE interval misses. Mitigation: buffer sEMG on MCU, batch transmit.

---

## 8. Safety Constraints (from hardware-engineering-specs.md)

- **Continuous compression:** <30 mmHg (well below 40-60 mmHg venous occlusion threshold)
- **TSA fail-open:** Motor freewheels on power loss → string untwists passively
- **Electrical:** IEC 60601-1 leakage limits (10μA DC normal). sEMG is passive sensing (microvolts) — near-zero risk
- **Electrodes:** Disposable Ag/AgCl for MVP. Irritation in 10-20% after 24+ hrs continuous wear (not an issue for session-based use)
- **FDA positioning:** "Training and educational tool, not diagnostic or therapeutic." General wellness exempt per 2016 policy. Same tech as mTrigger (Class II) but different framing = different regulatory burden.

---

## 9. Key Design Decisions Log

| Decision | Made | Rationale |
|---|---|---|
| Torso vest (not arm sleeve) | Session 3, 2026-04-08 | Lawson: torso is where most value for imbalance correction. **Needs primary source backing (Session 4 task)** |
| Strap-harness (not compression shirt) | Session 3, 2026-04-08 | CV needs bare skin. Adjustable sizing. Iteration speed for R&D. Shirt is post-MVP consumer form. |
| Dual-modality per zone | Session 3, 2026-04-08 | Software-switchable A/B testing. Deshpande supports hybrid. |
| Distributed TSA motors | Session 3, 2026-04-08 | Torso routing distances exceed 30-40cm friction limit. |
| Sensors before cueing | Session 3, 2026-04-08 | Measurements are the bottleneck. Cueing is meaningless without verified signal. |
| Bicep curl as MVP exercise | Session 2, 2026-04-07 | **SUPERSEDED by torso pivot.** New MVP exercise TBD (Session 4). |
| Compression sleeve + velcro pods | Session 2, 2026-04-07 | **SUPERSEDED by strap-harness.** |
| Pre-rep cueing only for MVP | Session 2, 2026-04-07 | Muscle Minder finding: pre-rep > continuous. 400ms TSA onset acceptable. |
| Fail-open TSA design | Session 2, 2026-04-07 | Safety requirement. Motor freewheels on power loss. |
| FDA general wellness framing | Session 2, 2026-04-07 | "Training tool, not diagnostic." Language discipline required. |
