# Session 4 Hardware Decision Handover — 2026-04-08

> For teammates making the final hardware purchasing decisions tonight.
> Read this first, then the supporting docs for details.

---

## What's Decided (research-backed, not changing)

1. **Torso-first is justified.** Fascial chains converge at trunk (Wilke 2016), trunk co-activation is prerequisite for compound lifts (McGill), trunk deficits predict knee injury with 91% sensitivity (Zazulak & Hewett 2007). Erector spinae is a torso muscle — no conflict with Rajat's priority.
   → See `torso-justification.md`

2. **10-channel MVP muscle map:**
   - Erector spinae L/R (injury prevention — stop signal)
   - Upper trapezius L/R (compensation detection)
   - Pectoralis major L/R (mind-muscle, bench press)
   - Latissimus dorsi L/R (mind-muscle, rows)
   - External obliques L/R (core stability, rotational asymmetry)
   → See `critical-muscles.md`, `core-muscles-research.md`

3. **Form factor: Hybrid Option D.** Adhesive electrodes on bare skin (days 1-3) for placement validation, then strap harness at confirmed positions (days 4-7), integration testing (days 8-10). Compression shirt is post-validation.
   → See `form-factor-evaluation.md`

4. **Active electrode architecture is mandatory.** Amplifier must be at the electrode site on the body (<5cm lead wire). Cannot run long analog wires to a central breadboard — signal will drown in noise. Digital output (SPI from ADS1292R/ADS1299) is immune to wire length.
   → See `signal-chain-analysis.md`

5. **ESP32's 12-bit ADC is NOT sufficient.** Need external ADC: 16-bit minimum, 24-bit preferred. ESP32 is MCU + BLE radio only.
   → See `signal-chain-analysis.md`

---

## What Teammates Need to Decide TONIGHT

### Decision 1: Which sensor acquisition architecture?

Five viable options. Ranked by signal quality:

#### Option A: Cerelog ESP-EEG ($362 shipped) ⭐ RECOMMENDED

- 8ch ADS1299 + ESP32-S3 on one board. Research-grade. No preamp needed.
- 24-bit, 110 dB CMRR, <1 µVpp noise, 16 kSPS
- **Only 1 unit left at $350 launch price.** Check cerelog.com NOW.
- Need +2ch for obliques (AD8232 $14 or later ADS1292R)
- USB-only for now (no BLE wireless yet)
- **Budget: $362 sensors. Leaves $338 for everything else.**

#### Option B: AD8232 fast-start ($34) + Cerelog ($362) when arrives

- 3x AD8232 from Amazon ($8 ea) + ESP32 ($10) = $34, arrives tomorrow
- Placement testing days 1-3 with budget hardware
- Cerelog arrives ~1 week for research-grade testing
- **Budget: $396 sensors. Leaves $304 for everything else.**

#### Option C: AD8232 x10 + ADS1115 x10 — all-budget ($110)

- Everything from Amazon, arrives tomorrow
- 80 dB CMRR (below spec), 860 SPS (below spec)
- Good enough for placement testing and gross activation. NOT for MDF fatigue analysis.
- **Budget: $110 sensors. Leaves $590 for everything else.**

#### Option D: BioAmp x10 + ADS1292R x5 ($435)

- BioAmp at ~$31/unit (not $8 as previously assumed), ships from India 1-2 weeks
- ADS1292R currently out of stock at main supplier (ProtoCentral)
- Unpublished CMRR on BioAmp — may not meet spec
- **Budget: $445 sensors. Leaves $255 for everything else. Tight.**

#### Option E: Olimex from DigiKey x10 ($233)

- $23.35/board, 11 in stock, ships today from DigiKey
- Arduino shield form factor — bulky, bench use only
- **Budget: $243 sensors. Leaves $457 for everything else.**

### Decision 2: Do we still include TSA (squeeze cueing) in MVP?

If we go with Option A or B, the sensor cost is $350-400. Original buy list had ~$50 in TSA components (N20 motors, Dyneema, PTFE, DRV8833, INA219). This still fits within budget.

**If budget is tight:** Go vibe-only for cueing (coin motors are $14 for 20). TSA is the "nice to have" — vibrotactile answers "does cueing change behavior?" just as well for an initial test.

### Decision 3: Do we order textile electrode materials?

~$32 for conductive fabric + snaps + conductive thread. Enables a weekend garment prototype alongside the harness build. Low cost, high optionality.

**Recommendation:** Yes, order it. It's cheap insurance.

### Decision 4: How to split across cards?

Depends on Option chosen. Rough split for **Option B** (recommended):

| Card | Limit | Items | Est. |
|---|---|---|---|
| **Rajat** (~$300) | Cerelog ESP-EEG ($350+$12) | **Over limit by $62** — need to split | |
| | OR: Rajat pays $300, Rajiv pays $62 of Cerelog | | |
| **Rajiv** ($215.52) | AD8232 x5 ($40) + electrodes/skin prep ($50) + harness materials ($40) + textile materials ($32) + Cerelog overflow ($62) | ~$224 — **$9 over** | |
| **Kelsi** (~$80) | Consumables: electrodes, tape, NuPrep, razors, alcohol, markers | ~$69 | |
| **Aaron** (~$100) | Vibes ($14) + LiPo ($15) + breadboards ($10) + jumpers ($7) + compression shirts ($20) + TSA motors/parts if included ($30) | ~$96 | |

**Card limits are tight for the Cerelog option.** May need creative splitting or one person fronting cost and getting reimbursed.

---

## Teammate's sEMG Spec Requirements (verified)

These came from a teammate's research. All are correct per literature:

| Parameter | Requirement | Source/Verification |
|---|---|---|
| Sampling rate | 1000-2000 Hz min, 4000 Hz ideal | Nyquist for 500 Hz sEMG content ✓ |
| Input impedance | >100 MΩ | Minimize electrode-skin impedance distortion ✓ |
| CMRR | >100 dB | SENIAM recommends >96 dB; 100 dB is conservative ✓ |
| Bandwidth | 20-500 Hz bandpass | Standard sEMG range ✓ |
| ADC resolution | 16-bit min, 24-bit preferred | Dynamic range for small activations ✓ |
| Noise floor | <1 µV RMS input-referred | Required for weak/deep muscles ✓ |
| Gain | 500-10,000× adjustable | sEMG is 10 µV-10 mV ✓ |
| IED | 20mm center-to-center | SENIAM bipolar standard ✓ |
| Electrode type | Ag/AgCl pre-gelled disposable | Gold standard ✓ |

**Which options meet these specs:**
- **ADS1299 (Cerelog, OpenBCI):** Meets ALL ✓
- **ADS1292R:** Meets all except gain (PGA max 12×, may need external preamp) ⚠️
- **BioAmp EXG Pill:** Input impedance ✓, rest UNPUBLISHED ⚠️
- **AD8232:** CMRR 80 dB ✗, bandwidth needs mods ⚠️, gain 514× with mods ⚠️
- **ESP32 internal ADC:** Fails on resolution, noise, linearity ✗✗✗

---

## Competitor Context

**Strive** (strive.tech): $6M raised, 215+ pro/college teams (NFL, NBA, EPL). EMG compression shorts, lower body only. $10-25K/year per team. No real-time cueing, no CV, coach-dependent. Validates the garment+EMG market. We differentiate with torso, real-time haptic cueing, phone CV, and consumer-accessible pricing.
→ See `strive-analysis-textile-electrodes.md`

---

## Files in This Session (read order for teammates)

| # | File | What It Contains | Priority |
|---|---|---|---|
| 1 | **hardware-decision-handover.md** | THIS FILE — start here | 🔴 Read first |
| 2 | **sensor-sourcing-reality.md** | Verified prices/stock for every sensor option | 🔴 Read before ordering |
| 3 | **signal-chain-analysis.md** | Why wiring matters, active electrodes, ADC requirements | 🔴 Critical for architecture |
| 4 | **buy-list-final.md** | ⚠️ STALE — written before signal chain findings. Use as reference for non-sensor items (harness, consumables, cueing) only | 🟡 Reference only |
| 5 | **critical-muscles.md** | Which muscles, why, SENIAM placement, priority tiers | 🟡 For electrode placement |
| 6 | **torso-justification.md** | Primary source evidence for torso-first | 🟢 Background |
| 7 | **core-muscles-research.md** | Why obliques are Tier 1 | 🟢 Background |
| 8 | **form-factor-evaluation.md** | Strap vs shirt vs adhesive vs hybrid | 🟢 Background |
| 9 | **strive-analysis-textile-electrodes.md** | Competitor + textile electrode DIY feasibility | 🟢 Background |
| 10 | **torso-vest-spec.md** | Session 3 spec snapshot (partially superseded) | 🟢 Context |
| 11 | **research-gaps.md** | Audit of unfounded claims (many now resolved) | 🟢 Context |
| 12 | **rajat-alignment-summary.md** | Rajat divergences (now reconciled) | 🟢 Context |

---

## Key Action Items for Tonight

- [ ] **Check Cerelog stock** at cerelog.com — only 1 unit was left at $350
- [ ] **Check Mouser** for BIOAMPEXGP-01 — if US warehouse stock, overnight to Austin
- [ ] **Check Amazon** for AD8232 modules — verify next-day delivery to Austin
- [ ] **Decide architecture** (Options A-E above)
- [ ] **Split card assignments** based on chosen option
- [ ] **Order immediately** — every day of shipping delay is a day of lost testing
- [ ] **Order consumables regardless** — Ag/AgCl electrodes, skin prep, tape, elastic straps. These are needed for ANY option.
