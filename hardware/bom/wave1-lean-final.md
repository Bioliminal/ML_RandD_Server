# BioLiminal Wave 1 — Lean Build

**Goal:** "Do things function at all?" — 4 channels, ESP32 ADC, overnight where possible.

| | |
|---|---|
| **Budget** | $745 total across 5 cards |
| **Wave 1 target** | ~$267 |
| **Reserve for Wave 2** | ~$478 |
| **Ship to** | Austin, TX |
| **Cards** | Rajiv $215.52 · Rajat $200 · Kelsi $80 · Aaron $100 · Leo $150 |

---

## Wave 1 Strategy

Only buy what you need to answer Day 1–3 questions: Can we see muscle activation through these electrodes? Does L/R asymmetry show up? Can we localize a vibe on the torso?

Everything else (ADS1292R, Cerelog, textile prototype, TSA) moves to Wave 2 after you have data. This cuts spending from ~$638 to ~$267 and preserves budget for the right sensor upgrade.

---

## 1. Sensor Signal Chain — 4 Channels (~$79)

INA128 amplifies the sEMG signal at the electrode. ESP32's 12-bit ADC digitizes it — garbage for spectral analysis, but enough to see "muscle on/off" and validate placements. Wave 2 adds ADS1292R or Cerelog for real resolution.

### INA128PA (DIP-8) — Instrumentation Amplifier

| | |
|---|---|
| **What it is** | Precision instrumentation amplifier. 120 dB CMRR, gain 1–10,000×, 200 kHz bandwidth at G=100, 700 µA quiescent current. DIP-8 package for breadboard prototyping. |
| **Purpose** | Preamp at electrode site. Amplifies 10 µV–10 mV sEMG signal before wire noise corrupts it. One per muscle channel. |
| **Qty** | 5 (4 channels + 1 spare) |
| **Unit price** | $8.22 |
| **Total** | $41.10 |
| **Source** | DigiKey — part # INA128PA-ND |
| **Link** | https://www.digikey.com/en/products/detail/texas-instruments/INA128PA/300996 |
| **Stock** | ✅ VERIFIED — 4,506 units in stock, genuine Texas Instruments |
| **Shipping** | 2-day ground from Minnesota. Overnight available for ~$15 extra. |
| **Card** | Rajat |

> **Why only 5?** You need 4 channels (erector spinae L/R + upper trap L/R) plus 1 spare. Once the circuit works, order 7 more from DigiKey — arrives in 2 days. Saves $58 vs buying all 12 now.

> **Why not a cheaper alternative?** The AD620 (Analog Devices) is the main competitor — but it's $16.29/ea at DigiKey and the DIP version (AD620ANZ) is OUT OF STOCK. The INA128PA at $8.22 is already the cheapest legitimate instrumentation amp that meets sEMG specs (>100 dB CMRR). Do NOT buy $15 Amazon 10-packs — likely counterfeit.

### ESP32-S3 DevKitC-1 (N16R8) — Microcontroller

| | |
|---|---|
| **What it is** | Dual-core 240 MHz microcontroller with BLE 5.0, WiFi, 16MB flash, 8MB PSRAM. |
| **Purpose** | Brain of the wearable. Reads INA128 analog output via its 12-bit ADC for Wave 1 (gross activation only). Streams to phone via BLE. NOT used as the final ADC — Wave 2 adds external 24-bit ADC. |
| **Qty** | 2 (1 primary + 1 spare) |
| **Unit price** | ~$10 |
| **Total** | ~$20 |
| **Source** | Amazon — multiple sellers |
| **Link** | https://www.amazon.com/s?k=ESP32-S3+DevKitC+N16R8 |
| **Stock** | ✅ VERIFIED — commodity part, widely available |
| **Shipping** | Next-day Prime to Austin |
| **Card** | Rajiv |

### 1% Metal Film Resistor Kit + Ceramic Capacitor Kit

| | |
|---|---|
| **What it is** | Assorted precision resistors (1/4W, 1% tolerance) + assorted ceramic capacitors for filter design. |
| **Purpose** | Resistors: set INA128 gain via Rg (G = 1 + 50kΩ/Rg). For G≈500, Rg ≈ 100Ω. Capacitors: build 20–500 Hz bandpass filter on each INA128 output. High-pass at 20 Hz removes movement artifact. Low-pass at 500 Hz removes noise above sEMG content. Having assorted values means you can tune per-muscle without reordering. |
| **Qty** | 1 kit each |
| **Total** | ~$18 ($8 resistors + $10 caps) |
| **Source** | Amazon |
| **Links** | Resistors: https://www.amazon.com/s?k=1%25+metal+film+resistor+assortment / Caps: https://www.amazon.com/s?k=ceramic+capacitor+assortment+kit |
| **Stock** | ✅ Commodity — widely available |
| **Shipping** | Next-day Prime to Austin |
| **Card** | Rajiv |

**SENSOR SUBTOTAL: ~$79**

---

## 2. Electrodes & Skin Prep (~$69)

Needed for ANY sensor architecture. Signal quality depends more on skin prep and electrode contact than on any other single factor.

### Ag/AgCl Snap Electrodes (100-pack)

| | |
|---|---|
| **What it is** | Silver/silver-chloride pre-gelled disposable electrode pads with standard snap connector. |
| **Purpose** | Gold-standard skin-to-sensor interface. Low impedance, consistent signal. Snap connector mates with standard electrode cables. You'll burn through ~30/day during placement testing. |
| **Qty** | 3 packs (300 total) |
| **Unit price** | ~$8 |
| **Total** | ~$24 |
| **Source** | Amazon |
| **Link** | https://www.amazon.com/s?k=Ag+AgCl+snap+electrodes+100+pack+ECG |
| **Shipping** | Next-day Prime |
| **Card** | Kelsi |

### Ten20 Conductive Paste (4 oz)

| | |
|---|---|
| **What it is** | Thick conductive electrode paste. Industry standard for sEMG research. |
| **Purpose** | Lowers electrode-skin impedance. Applied under electrode pad for better signal, especially on hairy or dry skin. |
| **Qty** | 1 |
| **Total** | ~$12 |
| **Source** | Amazon |
| **Link** | https://www.amazon.com/s?k=Ten20+conductive+paste |
| **Shipping** | Next-day Prime |
| **Card** | Kelsi |

### NuPrep Skin Prep Gel (4 oz)

| | |
|---|---|
| **What it is** | Mildly abrasive skin prep gel. |
| **Purpose** | Removes dead skin cells and oils at electrode site. Reduces skin impedance from ~50 kΩ to ~5 kΩ. Used before applying electrode. |
| **Qty** | 1 |
| **Total** | ~$8 |
| **Source** | Amazon |
| **Link** | https://www.amazon.com/s?k=NuPrep+skin+prep+gel |
| **Shipping** | Next-day Prime |
| **Card** | Kelsi |

### Tape, Coban Wrap, Razors, Alcohol, Skin Markers

| | |
|---|---|
| **What it is** | 3M Transpore medical tape, Coban self-adhering wrap, disposable razors, 70% isopropyl alcohol, surgical skin markers. |
| **Purpose** | Wire management on skin, electrode site hair removal, skin cleaning, marking validated electrode positions for reproducibility across sessions. |
| **Total** | ~$25 |
| **Source** | **CVS / HEB (same-day local pickup)** — check pharmacy first, faster and cheaper than Amazon for these. Amazon backup: https://www.amazon.com/s?k=3M+Transpore+tape |
| **Card** | Kelsi |

**CONSUMABLES SUBTOTAL: ~$69**

---

## 3. Cueing, Power, Wiring & Harness (~$119)

All commodity parts from Amazon with next-day delivery.

### ERM Coin Vibe Motors 10mm (10-pack × 2)

| | |
|---|---|
| **What it is** | Eccentric rotating mass vibration motors, 3V, 10mm diameter. |
| **Purpose** | Haptic cueing actuators. One per muscle zone. Buzz pattern tells user which muscle to activate or relax. 20 motors = 10 zones + 10 spares for failures. Also tests two-point discrimination localization on torso. |
| **Qty** | 2 packs (20 total) |
| **Total** | ~$14 |
| **Link** | https://www.amazon.com/s?k=coin+vibration+motor+10mm+10+pack |
| **Card** | Rajiv |

### 1200mAh LiPo 3.7V × 3 + TP4056 USB-C Charger × 3

| | |
|---|---|
| **What it is** | Lithium polymer rechargeable batteries (JST-PH 2.0 connector) + single-cell charge controllers with overcharge protection. |
| **Purpose** | Powers vest electronics. ESP32 + INA128s + vibe motors. ~2–3 hours runtime. Extras for hot-swapping during long test sessions. |
| **Total** | ~$20 ($15 batteries + $5 chargers) |
| **Links** | LiPo: https://www.amazon.com/s?k=1200mAh+LiPo+3.7V+JST+PH / TP4056: https://www.amazon.com/s?k=TP4056+USB-C+charger+module |
| **Card** | Aaron |

### 30AWG Silicone Wire Kit + Shielded Cable 4-conductor (5m)

| | |
|---|---|
| **What it is** | Flexible thin-gauge hookup wire (6 colors) + 4-wire cable with metal braid shield. |
| **Purpose** | Wire kit: general wiring between boards, power distribution, vibe motor connections. Shielded cable: carries amplified analog signal from INA128 to ESP32 ADC pin. Shield rejects 60 Hz powerline noise and gym equipment EMI. |
| **Qty** | 1 wire kit + 1 shielded cable spool |
| **Total** | ~$16 |
| **Links** | Wire: https://www.amazon.com/s?k=30AWG+silicone+wire+kit / Shielded: https://www.amazon.com/s?k=shielded+cable+4+conductor+30AWG |
| **Card** | Rajiv |

### Mini Breadboards (400-point) × 4 + Jumper Wire Kit

| | |
|---|---|
| **What it is** | Solderless prototyping boards + pre-made hookup wires with pin headers (M-M, M-F, F-F). |
| **Purpose** | Rapid circuit iteration. Mount INA128 DIP chips, passive filter components. Swap wiring without soldering during placement testing phase. Male-to-female jumpers connect ESP32 dev board pins to breadboard. |
| **Total** | ~$17 ($10 breadboards + $7 jumpers) |
| **Links** | Breadboard: https://www.amazon.com/s?k=mini+breadboard+400+point / Jumpers: https://www.amazon.com/s?k=jumper+wire+kit+male+female |
| **Card** | Aaron |

### Harness Materials (Elastic + Buckles, Velcro, Neoprene, Snaps)

| | |
|---|---|
| **What it is** | 1" elastic webbing with side-release buckles (10-pack), adhesive Velcro hook+loop (1" × 5yd), 2mm neoprene fabric (12"×24"), snap button kit (press studs, 100pc). |
| **Purpose** | Physical harness that holds sensors and motors against the body during lifts. Elastic straps = chest/waist/shoulder bands. Velcro = repositionable pod mounting. Neoprene = padding + friction. Snaps = electrode-to-pod quick-connect. |
| **Total** | ~$32 |
| **Link** | https://www.amazon.com/s?k=elastic+webbing+1+inch+buckles (+ search for other items individually) |
| **Card** | Rajiv + Aaron + Leo (split across cards) |

### Compression Shirts (M + L)

| | |
|---|---|
| **What it is** | Tight-fitting athletic undershirts. |
| **Purpose** | Base garment for eventual textile prototype. Also needed for testing: does MediaPipe still track joints when harness is worn over/under a shirt? |
| **Qty** | 2 |
| **Total** | ~$20 |
| **Link** | https://www.amazon.com/s?k=mens+compression+shirt+athletic |
| **Card** | Aaron |

**SUPPORT SUBTOTAL: ~$119**

---

## Deferred to Wave 2 (NOT ordering tonight)

These items are important but not needed until Day 4+. Deferring saves ~$170+ and lets you pick the right sensor upgrade based on data.

| Component | Why Deferred | Est. Cost | When to Order |
|---|---|---|---|
| **ADS1292R breakout × 5** (or Cerelog ESP-EEG) | Need placement data first. ProtoCentral ~$30/ea → $150. Cerelog → $362. Decision after Day 3 data. | $150–362 | Day 3–4 |
| **INA128PA × 7 more** | Only need 5 for Wave 1. Order the rest once circuit is confirmed working. DigiKey 2-day delivery. | ~$58 | Day 2–3 |
| **Conductive Fabric, Snap Connectors, Conductive Thread** | Textile garment prototype. Can't sew until electrode positions are confirmed (Day 5+). | ~$32 | Day 5+ |
| **TSA Components** (DRV8833, N20 motors, Dyneema, PTFE, INA219, hall sensors) | Squeeze cueing is secondary to signal validation. Vibrotactile-only for Wave 1. | ~$37 | Day 5+ |

**Check tonight but don't order:**
- ProtoCentral ADS1292R price in USD: https://protocentral.com/product/ads1292r-ecg-respiration-breakout-kit/
- Cerelog ESP-EEG stock: https://www.cerelog.com/
- Mouser BioAmp EXG Pill (BIOAMPEXGP-01) US warehouse stock: https://www.mouser.com

---

## Budget Summary

| | Amount |
|---|---|
| **Wave 1 spend** | ~$267 |
| **Total budget** | $745 |
| **Reserve for Wave 2** | ~$478 |

$478 reserve is enough for Cerelog ($362) OR ADS1292R + 7 more INA128s + textile + TSA. The data from Days 1–3 tells you which path to take.

---

## Card Split — Wave 1

| Card | Limit | Wave 1 Items | Spend | Remaining |
|---|---|---|---|---|
| **Rajat** | $200 | INA128PA × 5 from DigiKey | ~$41 | ~$159 |
| **Rajiv** | $215.52 | ESP32 × 2, resistor kit, cap kit, vibes × 2, wire kit, shielded cable, elastic, velcro | ~$80 | ~$135 |
| **Kelsi** | $80 | All electrodes & skin prep consumables | ~$69 | ~$11 |
| **Aaron** | $100 | LiPo × 3, TP4056 × 3, breadboards × 4, jumpers, snap buttons, compression shirts × 2 | ~$57 | ~$43 |
| **Leo** | $150 | Neoprene fabric, harness buckle share | ~$20 | ~$130 |
| **TOTAL** | **$745** | | **~$267** | **~$478** |

---

## Order Checklist — Tonight (Tue Apr 8)

- [ ] **Rajat:** Order 5× INA128PA from DigiKey → https://www.digikey.com/en/products/detail/texas-instruments/INA128PA/300996 — $41.10 + shipping. Select fastest ground (arrives Thu/Fri) or overnight if <$15 extra.
- [ ] **Rajiv:** Amazon cart — ESP32-S3 × 2, resistor kit, cap kit, coin vibes × 2, wire kit, shielded cable, elastic webbing, velcro. ~$80 total, next-day Prime.
- [ ] **Kelsi:** Amazon cart — Ag/AgCl electrodes × 3, Ten20, NuPrep. Then hit CVS/HEB tomorrow morning for tape, razors, alcohol, markers. ~$69 total.
- [ ] **Aaron:** Amazon cart — LiPo × 3, TP4056 × 3, breadboards × 4, jumper wires, snap buttons, compression shirts × 2. ~$57 total.
- [ ] **Leo:** Amazon cart — Neoprene fabric, harness buckle share. ~$20. Save the remaining $130 for Wave 2 — Leo is the biggest Wave 2 contributor.
- [ ] **Anyone:** Check ProtoCentral ADS1292R price in USD + Cerelog ESP-EEG stock. Report to group chat. This is Wave 2 intel, not an order tonight.
- [ ] **Tomorrow AM:** Send cold emails to UT KHE Neuromuscular Lab, ReNeu Lab, Neptune Lab for Delsys EMG bench time.
- [ ] **Tomorrow AM:** Complete Texas Inventionworks 3D printer + soldering training → https://inventionworks.engr.utexas.edu/

---

## Free Resources — Don't Buy These

| Item | Where | Savings |
|---|---|---|
| Soldering stations + solder | Texas Inventionworks (EER Building) + Rajat's own iron | ~$25 |
| 3D printing (PETG, PLA, resin) | TIW DFAB Lab or Hello Maker (Welch Hall) — free filament for UT students | ~$20 |
| Sewing machines | TIW DFAB Lab or Hello Maker | ~$15 |
| Oscilloscope + bench power supply | TIW Electronics Lab 1 | ~$200+ avoided |
| Heat shrink, hand tools | TIW The Garage checkout | ~$25 |
| **Total avoided** | | **~$285+** |

---

## Verified Links Summary

All links verified April 8, 2026 via web search.

| Component | Link | Verification |
|---|---|---|
| INA128PA (DigiKey) | https://www.digikey.com/en/products/detail/texas-instruments/INA128PA/300996 | ✅ $8.22/ea, 4,506 in stock, genuine TI, part # INA128PA-ND |
| ADS1292R breakout (Amazon, Senzooe) | https://www.amazon.com/Senzooe-ADS1292-ADS1292R-Board-Module/dp/B0CB7SLD84 | ⚠️ WAVE 2 — verified at $54.70, ships from China (2–4 weeks), 3rd party seller |
| ADS1292R breakout (ProtoCentral) | https://protocentral.com/product/ads1292r-ecg-respiration-breakout-kit/ | ⚠️ WAVE 2 — price unverified (site renders dynamically), ships from India 5–10 days |
| Cerelog ESP-EEG | https://www.cerelog.com/ | ⚠️ WAVE 2 — $349.99 confirmed, limited stock, ships from US |
| Texas Inventionworks | https://inventionworks.engr.utexas.edu/ | ✅ Free for UT students, Mon–Fri 10am–6pm, EER Building |
| Hello Maker Studio | https://sites.utexas.edu/cnsmakerspace/ | ✅ Free for UT students, Welch Hall |

Amazon links (electrodes, ESP32, vibes, wire, etc.) are search queries — pick the listing with Prime next-day delivery to Austin, TX. Prices are approximate and should be confirmed at checkout.
