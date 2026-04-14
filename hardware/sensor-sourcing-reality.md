# Sensor Sourcing Reality Check — 2026-04-08

> Verified pricing and availability as of tonight (Tue Apr 8).
> Prior specs assumed BioAmp at $8/unit and MyoWare at $38/unit. Both are wrong.

---

## MyoWare 2.0 — DISCONTINUED

| Source | Price | Status | Link |
|---|---|---|---|
| SparkFun | $36.51-$42.95 | **Backordered / retired from catalog** | [sparkfun.com](https://www.sparkfun.com/myoware-2-muscle-sensor.html) |
| Adafruit | $43.50 | **"No longer stocked"** | [adafruit.com](https://www.adafruit.com/product/6423) |
| The Pi Hut | — | **Discontinued** | [thepihut.com](https://thepihut.com/products/myoware-2-0-muscle-sensor) |
| Amazon | ~$38-43 | **May have 3rd-party stock — unverified** | Search "MyoWare 2.0" |

**Bottom line:** MyoWare 2.0 is end-of-life. Cannot rely on it for the project.

---

## BioAmp EXG Pill — Available but ~$31/unit (not $8)

The $8 figure in prior specs was an old campaign/crowdfunding price. Actual retail:

| Source | Config | Price | $/unit | Stock | Ship Time to Austin |
|---|---|---|---|---|---|
| Tindie | 8-pack | $249 | $31.13 | 6 left | India → US, **1-2 weeks** |
| Tindie | 2-pack | $69 | $34.50 | In stock | India → US, **1-2 weeks** |
| Upside Down Labs store | Single | ₹2,599 (~$31) | ~$31 | In stock | India → DHL Express, **5-7 days** |
| Mouser (BIOAMPEXGP-01) | 2-pack kit | ~$30-35 est. | ~$15-18? | 126 units (India warehouse) | **Unknown — may be US or India stock** |
| Crowd Supply | 2-pack | $69 | $34.50 | Campaign ended, may still sell | Portland OR → ground, **5-7 biz days** |

**Key issue:** BioAmp's CMRR and noise floor are unpublished. The TL074 op-amp is general-purpose, not precision instrumentation grade. May not meet the >100 dB CMRR / <1 µV RMS noise requirements for MDF fatigue analysis.

**Mouser note:** The Mouser listing shows stock but the product page wouldn't load during this session. Mouser ships overnight from Mansfield TX if it's US warehouse stock. **Teammates should check mouser.com directly for BIOAMPEXGP-01 pricing and warehouse location.**

---

## DigiKey Options — In-Stock, Fast Ship

| Sensor | DigiKey Part | Price | Stock | Channels | Notes |
|---|---|---|---|---|---|
| **Olimex SHIELD-EKG-EMG** | SHIELD-EKG-EMG | ~$23.35 | **11 in stock** | 1 per board | Arduino shield — bulky, bench use only, not wearable |
| **DFRobot SEN0240** (Gravity EMG) | SEN0240 | $18.57 (Arrow) / $49.50 (DFRobot) | In stock | 1 per board | OYMotion analog EMG sensor, single-channel |
| **SparkFun SEN-13723** | SEN-13723 | ~$25 | Listed | 1 per board | Medical EMG eval board |

**These are all single-channel, relatively bulky boards.** Not ideal for on-body active electrode mounting but usable for bench testing.

---

## AD8232 — Cheapest, Fastest, Needs Mods

| Source | Price | ETA | Stock |
|---|---|---|---|
| Amazon (generic Chinese modules) | **$5-10 each** | **Next-day** | Abundant |
| SparkFun (SEN-12650) | ~$20 | 2-3 days | Listed |

**Specs:**
- Input impedance: 10 GΩ ✓
- CMRR: 80 dB — **below 100 dB requirement** ✗
- Stock bandwidth: 0.5-40 Hz (ECG) — **must modify filters for 20-500 Hz EMG**
- Gain: ~100 stock, ~514 with mods (documented in Electronics 2023 paper)
- Can be modified for EMG with component swaps on highpass/lowpass filters

**Verdict:** Cheap fast-start for placement testing. Not endgame for fatigue analysis.

---

## ADS1292R — Research-Grade ADC (2ch)

| Source | Price | Stock | Notes |
|---|---|---|---|
| ProtoCentral breakout | ₹3,945 (~$47) | **OUT OF STOCK** | Tindie listing may still have units |
| SparkFun | Need to verify | — | May carry compatible breakout |
| Generic breakout boards | $15-30 | Varies | Search Amazon/AliExpress |

**Specs:** 24-bit, 2ch, 105 dB CMRR, 8 kSPS, SPI output. Meets all specs. PGA gain 1-12× (may need external preamp for full sEMG range). Five boards for 10 channels.

---

## ADS1299 — Research-Grade 8ch (Best Single-Board Option)

| Board | Price | Stock | Channels | Ships From |
|---|---|---|---|---|
| **Cerelog ESP-EEG** | **$349.99** (+$12 ship) | **1 unit left** (batch 2) | 8 | US |
| **OpenBCI Cyton** | **$1,249** | 80 in stock | 8 | US |
| AliExpress ADS1299 module | ~$100-200 | Varies | 8 | China (2-4 weeks — OUT) |
| eBay ADS1299 module | ~$470 | Limited | 8 | Varies |
| TI ADS1299EEGFE-PDK eval | ~$500+ | TI store | 8 | US |
| HackEEG (Crowd Supply) | ~$200-400 est. | Unknown | 8 | US |

**ADS1299 specs:** 24-bit, 110 dB CMRR, <1 µVpp noise at PGA=24, 16 kSPS, built-in PGA (no separate preamp needed for sEMG). SPI digital output = immune to wire noise.

**Cerelog is the standout:** ESP32-S3 built in, ADS1299, $350, ships from US. Open source. BrainFlow compatible. BUT: USB-only (no BLE wireless yet), and only 1 unit left at launch price.

---

## ESP32 Internal ADC — NOT Sufficient

| Spec | ESP32 ADC | Requirement | Gap |
|---|---|---|---|
| Resolution | 12-bit (9 effective) | 16-bit min | **7 bits short** |
| Linearity | Non-linear | Linear | **Requires calibration** |
| Noise | ~2-4 mV | <1 µV RMS input-referred | **Orders of magnitude worse** |

**Implication:** ESP32 works as MCU + BLE radio, but CANNOT be used as the sEMG ADC. Must use external ADC (ADS1292R, ADS1299, or at minimum ADS1115).
