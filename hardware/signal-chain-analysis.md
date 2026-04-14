# sEMG Signal Chain Analysis — Wiring, ADC, and Sensor Spec Verification

**Date:** 2026-04-08
**Context:** Teammate flagged wiring as critical. This doc verifies our hardware choices against research-grade sEMG requirements.

---

## 1. Target Specs (from teammate's research + SENIAM + literature)

| Parameter | Requirement | Why It Matters |
|---|---|---|
| Sampling rate | 1000-2000 Hz min (4000 Hz ideal) | Nyquist: sEMG content up to 500 Hz. MDF fatigue analysis needs full spectrum. |
| Input impedance | >100 MΩ (higher = better) | Minimize distortion from electrode-skin impedance (~5-50 kΩ wet, ~500 kΩ dry) |
| CMRR | >100 dB | Reject 60 Hz powerline noise + motion artifacts |
| Bandwidth | 20-500 Hz bandpass | Full sEMG content. 20 Hz high-pass removes movement artifact. |
| ADC resolution | 16-bit minimum, 24-bit preferred | Dynamic range for small + large activations without clipping |
| Noise floor | <1 µV RMS (input-referred) | Weak signals from small/deep muscles (serratus, lower trap) disappear in noise |
| Gain | 500-10,000× adjustable | sEMG signal is 10 µV - 10 mV; ADC input is 0-3.3V |
| Inter-electrode distance | 20 mm center-to-center | SENIAM standard for bipolar config |
| Electrode type | Ag/AgCl pre-gelled disposable | Gold standard for signal consistency |

---

## 2. THE CRITICAL WIRING ISSUE: Active vs Passive Electrodes

Your teammate is right — this is the single most important hardware design decision.

### The Problem

sEMG signals at the electrode are **10 µV to 10 mV** with source impedance of **5-500 kΩ**. This is a tiny, high-impedance signal. Any wire between the electrode and the amplifier acts as a **noise antenna**:

- Unshielded wires pick up 60 Hz powerline interference
- Cable movement generates motion artifacts (triboelectric effect)
- Longer wires = more noise pickup = worse SNR
- The signal-to-noise ratio degrades **proportionally with wire length** before amplification

### The Solution: Active Electrodes

**Place the amplifier AT the electrode site.** This is called an "active electrode."

| | Passive Electrode (wire → distant amp) | Active Electrode (amp at electrode) |
|---|---|---|
| Wire carries | Raw µV signal (high impedance) | Amplified V signal (low impedance ~10Ω) |
| Noise pickup | **Severe** — wire is antenna for µV signal | **Minimal** — amplified signal overwhelms noise |
| Motion artifact | **High** — cable movement adds µV-level noise | **Low** — low output impedance rejects cable motion |
| Max practical wire length | **~10-15 cm** before SNR degrades significantly | **Meters** — post-amplification signal is robust |
| CMRR at amplifier | Degraded by cable imbalance | Full CMRR — differential amp right at electrodes |

**Source:** Delsys tutorial on sEMG detection; [Wearable Active Electrode for sEMG (PMC7416295)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7416295/) — achieved 96 dB CMRR, 49 dB SNR with dry active electrodes.

### What This Means For Our Design

**Every sEMG channel needs the amplifier board PHYSICALLY AT the electrode site on the body.** You cannot run 30cm wires from torso electrodes to a central breadboard — the signal will be buried in noise.

Practical options:
1. **BioAmp EXG Pill at each electrode site** — it's 25.4 x 10mm, designed for this. Mount on harness pod directly over electrode. Run amplified analog signal back to central MCU via shielded wire.
2. **ADS1292R/ADS1299 at each electrode pair** — these are full AFE+ADC in one chip. Digital output (SPI) is completely immune to wire noise. Can run SPI bus over meters.
3. **AD8232 modules at each site** — cheap ($5-10) but needs filter modification for EMG bandwidth (stock config is 0.5-40 Hz for ECG, not 20-500 Hz for EMG)

---

## 3. How Our Sensor Options Stack Up

### BioAmp EXG Pill

| Spec | BioAmp EXG Pill | Requirement | Meets? |
|---|---|---|---|
| Input impedance | 10^12 Ω (1 TΩ) | >100 MΩ | **YES** ✓ |
| Channels | 1 per board | — | OK (need 10 boards) |
| Gain | Configurable via R6 resistor | 500-10,000× | **YES** ✓ (requires component selection) |
| Bandwidth | Configurable via R12, C5 | 20-500 Hz | **LIKELY** ✓ (requires component selection) |
| CMRR | Not published | >100 dB | **UNKNOWN** ⚠️ |
| Noise floor | Not published | <1 µV RMS | **UNKNOWN** ⚠️ |
| Op-amp | TL074 (quad JFET) | — | Reasonable for prototyping, not research-grade |
| Output | Analog → requires external ADC | — | See ADC section |
| Size | 25.4 x 10mm | — | **Small enough for active electrode mount** ✓ |
| Price | **~$31/unit** (not $8) | — | 10 units = **$310** |

**Verdict:** Good for prototyping. Input impedance is excellent. But CMRR and noise specs are unpublished — may not meet research-grade requirements. The TL074 op-amp is a general-purpose JFET, not a precision instrumentation amp. **Adequate for "can we detect muscle activation?" but may fail for "can we track MDF fatigue shift?"**

### AD8232 (generic Amazon breakout, $5-10)

| Spec | AD8232 (stock ECG config) | AD8232 (modified for EMG) | Requirement |
|---|---|---|---|
| Input impedance | 10 GΩ | 10 GΩ | >100 MΩ → **YES** ✓ |
| Gain | ~100 (ECG) | ~514 (EMG config) | 500-10,000× → **MARGINAL** ⚠️ |
| Bandwidth | 0.5-40 Hz (ECG) | 0.5-500+ Hz (modifiable) | 20-500 Hz → **YES with mods** |
| CMRR | 80 dB typical | 80 dB | >100 dB → **NO** ✗ |
| Noise | ~30 µV RMS (output) | Similar | <1 µV (input) → **NEEDS VERIFICATION** |
| Output | Analog | Analog | External ADC needed |
| Price | **$5-10** | Same + component swap | — |

**Verdict:** CMRR of 80 dB is below the 100 dB requirement — will have more powerline noise. Usable for gross activation detection but NOT for fatigue spectral analysis. The filter components CAN be modified for EMG bandwidth (documented in [AD8232 to Biopotentials Sensors, Electronics 2023](https://www.mdpi.com/2079-9292/12/4/833) — gain increased to 514, highpass/lowpass resized). **Budget fast-start option, not endgame.**

### ADS1292R (external AFE+ADC)

| Spec | ADS1292R | Requirement | Meets? |
|---|---|---|---|
| Input impedance | Very high (integrated PGA) | >100 MΩ | **YES** ✓ |
| Channels | 2 per chip | — | 5 chips for 10ch |
| Gain | 1, 2, 3, 4, 6, 8, 12× (PGA) | 500-10,000× | **Needs external preamp** ⚠️ |
| Bandwidth | DC to 8 kHz (configurable) | 20-500 Hz | **YES** ✓ |
| CMRR | 105 dB | >100 dB | **YES** ✓ |
| ADC | 24-bit delta-sigma | 16+ bit | **YES** ✓✓ |
| Noise | 8 µV peak-to-peak (at gain=6) | <1 µV RMS | **Marginal** — needs higher gain or external preamp |
| Sampling | Up to 8 kSPS | 1000-2000 Hz | **YES** ✓ |
| Output | Digital (SPI) | — | **Wire-length immune** ✓✓ |
| Price | **~$25/2ch breakout** | — | 5 boards for 10ch = **$125** |

**Verdict:** Best signal quality option. 24-bit ADC, 105 dB CMRR, digital SPI output (immune to wire noise). Needs external preamp for full gain. **This is the right chip for MDF fatigue tracking.** Available on SparkFun/Mouser.

### ADS1299 (8-channel research-grade)

| Spec | ADS1299 | Requirement | Meets? |
|---|---|---|---|
| Channels | 8 per chip | — | 2 chips for 16ch |
| CMRR | 110 dB | >100 dB | **YES** ✓✓ |
| ADC | 24-bit | 16+ bit | **YES** ✓✓ |
| Noise | 1 µV peak-to-peak (at gain=24) | <1 µV RMS | **YES** ✓ |
| Sampling | Up to 16 kSPS | 1000-2000 Hz | **YES** ✓ |
| Gain | 1, 2, 4, 6, 8, 12, 24× (PGA) | — | Needs external preamp for full range |
| Output | Digital (SPI) | — | **Wire-length immune** ✓✓ |
| Price | **~$50-60 per breakout board** | — | OpenBCI Cyton ($200) uses this |

**Verdict:** Research-grade. This is what Delsys Trigno and OpenBCI use. Expensive but meets every spec. One 8-ch board could cover most of the MVP.

---

## 4. THE ADC PROBLEM: ESP32 Is Not Enough

| ADC | Resolution | Effective Bits | Sampling Rate | Noise Floor | Meets Spec? |
|---|---|---|---|---|---|
| **ESP32 internal** | 12-bit | **~9 effective bits** (non-linear!) | 1 MSPS shared | ~2-4 mV | **NO** ✗ |
| **Arduino UNO R4** | 14-bit | ~12 effective | 500 kSPS | ~1 mV | **Marginal** ⚠️ |
| **ADS1115 (external)** | 16-bit | ~15 effective | 860 SPS max | ~5 µV | **YES but SLOW** ⚠️ |
| **ADS1292R** | 24-bit | ~19 effective | 8 kSPS | ~8 µVpp | **YES** ✓ |
| **ADS1299** | 24-bit | ~22 effective | 16 kSPS | ~1 µVpp | **YES** ✓✓ |

**ESP32's 12-bit ADC is effectively 9-bit due to non-linearity.** This gives you ~512 usable levels across the signal range — enough to see "muscle on vs off" but NOT enough to track spectral frequency shifts (MDF analysis) or detect subtle fatigue onset.

**The fix:** Use ESP32 as MCU/BLE radio but route sEMG signals through an external ADC:
- **Budget:** ADS1115 (16-bit, $3/ch) — slow at 860 SPS, need one per channel = 10 chips. Meets resolution but not sampling rate.
- **Better:** ADS1292R (24-bit, 2ch, ~$25/board) — 5 boards for 10ch. Meets everything.
- **Best:** ADS1299 (24-bit, 8ch, ~$50-60/board) — 2 boards for 16ch. Research-grade.

---

## 5. Revised Signal Chain Architecture

```
WRONG (original plan):
  Electrode → 30cm wire → BioAmp on breadboard → ESP32 12-bit ADC
  Problems: wire noise, 9-bit effective ADC, no CMRR at electrode

RIGHT (active electrode + external ADC):
  Electrode → BioAmp EXG Pill ON BODY (≤5cm wire) → shielded analog wire → ADS1292R → SPI → ESP32
  Or:
  Electrode → ADS1292R ON BODY (integrated preamp+ADC) → SPI digital wire (noise-immune) → ESP32

BEST (digital at electrode):
  Electrode → ADS1299 board on harness → SPI → ESP32
  All analog signal stays within cm of electrode. Digital bus runs to MCU.
```

---

## 6. Impact on Buy List

### What Changes

| Original Plan | Problem | Revised |
|---|---|---|
| BioAmp → ESP32 ADC | 9-bit effective ADC, long analog wires | BioAmp → ADS1292R → ESP32 SPI |
| 30cm analog wires to breadboard | Noise antenna for µV signals | Active electrode: amp at body, <5cm analog lead |
| ESP32 12-bit ADC for all channels | Below 16-bit minimum | External 24-bit ADC (ADS1292R or ADS1299) |
| CD4051 analog mux | Muxing analog signals adds noise, shared ADC | Dedicated ADC per channel pair (ADS1292R = 2ch each) |

### Revised Component Needs

**For 10-channel MVP with research-quality signal:**

| Component | Qty | Est. Price | Source | Role |
|---|---|---|---|---|
| BioAmp EXG Pill (preamp at electrode) | 10 | ~$310 | Tindie/Mouser | Active electrode preamp, mount on body |
| ADS1292R breakout (2ch, 24-bit ADC) | 5 | ~$125 | SparkFun/Mouser | Digitize at body, SPI to ESP32 |
| ESP32-S3 | 1 | $10 | Amazon | MCU + BLE radio only (not ADC) |
| **Sensor subtotal** | | **~$445** | | |

**Budget alternative (adequate for placement testing, not fatigue analysis):**

| Component | Qty | Est. Price | Source | Role |
|---|---|---|---|---|
| AD8232 breakout (preamp at electrode) | 10 | ~$70 | Amazon | Active electrode, needs filter mod |
| ADS1115 (16-bit, 1ch) | 10 | ~$30 | Amazon/Mouser | External ADC (slow but cheap) |
| ESP32-S3 | 1 | $10 | Amazon | MCU + BLE |
| **Budget subtotal** | | **~$110** | | |

**Tiered approach (recommended):**

| Phase | Components | Cost | What It Validates |
|---|---|---|---|
| Days 1-3 | AD8232 x3 + ESP32 ADC (12-bit) | ~$25 | Gross activation detection, placement testing |
| Days 4-7 | BioAmp x10 + ADS1292R x5 | ~$435 | Full 10ch, fatigue MDF analysis, real signal quality |
| If budget tight | Skip BioAmp, use AD8232 x10 + ADS1115 x10 | ~$110 | Adequate for demo, not for fatigue science |

---

## 7. DigiKey Sensor Availability (verified via search)

| Sensor | DigiKey Part | Price | Stock | Notes |
|---|---|---|---|---|
| DFRobot SEN0240 (Analog EMG) | SEN0240 | **$18.57** (Arrow) / **$49.50** (DFRobot) | In stock on DigiKey | OYMotion design, analog output, single-channel |
| Olimex SHIELD-EKG-EMG | SHIELD-EKG-EMG | **~$23.35** | **11 in stock** | Arduino shield, 1-channel, EKG/EMG, good for prototyping |
| SparkFun SEN-13723 | SEN-13723 | ~$25 | Listed on DigiKey | Medical EMG evaluation board |
| BioAmp EXG Pill | BIOAMPEXGP-01 | ~$30-35 (est.) | Listed but price unverifiable | Mouser shows 126 units (India warehouse) |

**Best DigiKey fast-ship option for immediate testing:** Olimex SHIELD-EKG-EMG at $23.35, 11 in stock, ships today. It's single-channel but validates the concept.

---

## 8. Wiring Best Practices Summary

| Rule | Why | Source |
|---|---|---|
| **Amplifier within 5cm of electrode** | Pre-amplification before noise pickup | Delsys, SENIAM, PMC7416295 |
| **Shielded cable for analog runs** | Reject EMI from gym equipment, powerlines | Standard practice |
| **Twist electrode lead pairs** | Minimize loop area → reduce magnetic pickup | [PMC10059683](https://pmc.ncbi.nlm.nih.gov/articles/PMC10059683/) |
| **Keep analog wire runs <15cm** post-amplification | Even amplified analog degrades over distance | Engineering best practice |
| **Digital (SPI/I2C) for long runs** | Immune to analog noise, can run meters | ADS1292R/ADS1299 output |
| **Ground electrode on bony prominence** | Low muscle activity reference point | SENIAM |
| **Use active electrodes, not passive** | 10Ω output impedance rejects cable artifacts | Delsys tutorial |
| **Route wires away from power lines** | Reduce 60Hz coupling | Standard practice |
| **Strain relief at electrode site** | Prevent cable tug from moving electrode | ADInstruments guide |
| **No cable crossing joints** | Joint flexion = cable movement = artifact | SENIAM |

---

## Sources

- [Delsys: Surface EMG Detection and Recording (PDF)](https://www.delsys.com/downloads/TUTORIAL/semg-detection-and-recording.pdf)
- [Cornell: Important Factors in Surface EMG Measurement (PDF)](https://people.ece.cornell.edu/land/courses/ece5030/labs/f2009/EMG_measurement_and_recording.pdf)
- [Wearable Active Electrode for sEMG — PMC7416295](https://pmc.ncbi.nlm.nih.gov/articles/PMC7416295/)
- [Reducing Noise in Single-Channel EMG — PMC10059683](https://pmc.ncbi.nlm.nih.gov/articles/PMC10059683/)
- [AD8232 to Biopotentials Sensors — Electronics 2023](https://www.mdpi.com/2079-9292/12/4/833)
- [Merletti & Muceli 2019: Surface EMG Best Practices — J Electromyogr Kinesiol](https://www.sciencedirect.com/science/article/pii/S1050641119302536)
- [BioAmp EXG Pill Documentation](https://docs.upsidedownlabs.tech/hardware/bioamp/bioamp-exg-pill/index.html)
- [ADS1292R TI Forum: EMG Configuration](https://e2e.ti.com/support/data-converters-group/data-converters/f/data-converters-forum/877586/ads1292r-configure-ads1292r-for-emg-acquisition)
- [Open-Source 8-Ch BCI Board (ESP32 + ADS1299)](https://news.ycombinator.com/item?id=46502051)
- [ADInstruments: Biopotential Electrodes and Lead Wires](https://www.adinstruments.com/products/biopotential-electrodes-and-lead-wires)
