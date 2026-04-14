# Research Notes: Strive Competitor Analysis & Textile Electrode Feasibility

**Date:** 2026-04-08

---

## Section 1: Strive (strive.tech) Competitor Analysis

### Product Overview

Strive sells the **STRIVE Elite** platform -- EMG sensor-lined compression shorts paired with a Bluetooth-enabled pod that connects to an iOS app. The system is currently on its 4th-generation hardware design (the pod has been significantly miniaturized over iterations).

- **Form factor:** Compression shorts with embedded EMG sensors + removable Bluetooth pod with accelerometer
- **Muscles covered:** Quadriceps, hamstrings, and glutes (3 muscle groups per leg, both legs)
- **Data captured:** Muscle exertion amplitude and frequency, muscle distribution across 3 groups, left/right symmetry, movement intensity (via accelerometer)
- **Channel count:** Not publicly disclosed. Based on covering 3 bilateral muscle groups, likely 6 EMG channels minimum (one per muscle group per leg), possibly more for redundancy

### Target Market

- **Primary:** Professional and collegiate sports teams (NFL, NBA, NCAA, EPL, MLS)
- **Current adoption:** 215+ pro and collegiate teams including Baltimore Ravens, Kansas City Chiefs, Manchester City FC, University of Kentucky basketball
- **Expanding into:** US Military (existing Air Force partnership), physical therapy clinics, heavy industry
- **NOT consumer-facing** -- this is a B2B enterprise/team product

### Pricing

- Not publicly listed (enterprise sales model, "contact us" pricing page)
- From their crowdfunding/investor materials: customer acquisition cost ~$3,500 per team, lifetime value ~$75,000 per team
- This implies annual team subscriptions likely in the $10K-25K range (hardware + software platform)

### Technology

- **Electrodes:** Embedded in compression garment (likely textile/conductive fabric electrodes sewn into the shorts -- they describe the sensors as "lined" into the shorts)
- **Wireless:** Bluetooth to iOS
- **Pod:** Contains accelerometer + Bluetooth radio + presumably the ADC/MCU for EMG signal conditioning
- **MCU/chipset:** Not publicly disclosed
- **Software:** iOS app with team dashboard, muscle exertion/distribution/symmetry analytics

### Funding

- $6M Series A led by Future Communities Capital
- Notable investors: NFL rusher Jonathan Taylor, Heisman winner Troy Smith
- Founded by Nikola Mrvaljevic, based in Bothell, WA

### Comparison to Our Project (Torso sEMG Vest + Vibrotactile/TSA Cueing + Phone CV)

| Dimension | Strive | Our Project |
|---|---|---|
| **Body region** | Lower body only (legs/glutes) | Torso (back, core, shoulders) |
| **Form factor** | Compression shorts | Compression vest |
| **Feedback** | Software dashboard only (post-hoc or coach-mediated) | Real-time vibrotactile + TSA cueing (haptic) |
| **Computer vision** | None | Phone CV for form analysis |
| **Target user** | Pro teams with dedicated staff | Individual athletes / broader market |
| **Autonomy** | Requires coach/trainer to interpret data | Agentic -- system provides direct cueing |
| **Electrode approach** | Textile (integrated into garment) | TBD (adhesive for MVP, textile for production) |

### What We Can Learn From Strive

1. **Textile electrode integration works at scale** -- they ship garments with embedded sensors to 215+ teams, proving the approach is production-viable
2. **Compression garment as the platform** -- using existing athletic compression wear as the substrate is smart; athletes already wear it
3. **Minimize the pod** -- their 4th-gen design philosophy is "make it disappear." The athlete should forget they're wearing it
4. **Start with pro sports** -- high willingness to pay, tolerance for imperfect UX, strong word-of-mouth
5. **Muscle symmetry as a key metric** -- left/right comparison is compelling for injury prevention

### What They're Missing (Our Advantages)

1. **No real-time haptic feedback** -- Strive is observe-and-review, not coach-in-the-moment. Our vibrotactile/TSA cueing closes the loop
2. **No computer vision** -- they rely purely on EMG; we combine EMG with phone CV for richer form analysis
3. **Lower body only** -- no torso coverage for deadlifts, rows, overhead press, posture
4. **Coach-dependent** -- their model requires a trained practitioner to interpret data. Our agentic approach works for solo athletes
5. **No consumer play** -- their enterprise model leaves the individual athlete market open

### Sources

- [Strive Tech Website](https://strive.tech/)
- [Strive Tech Hardware Design -- Charles Marzette Jr](http://www.marzettedesign.com/strive-tech-hardware)
- [STRIVE Secures $6M -- Fitt Insider](https://insider.fitt.co/strive-secures-6m-to-unlock-athlete-performance-data/)
- [Strive Sense3 Validation Study](https://www.researchgate.net/publication/348193095_Validity_and_Reliability_of_StriveTM_Sense3_for_Muscle_Activity_Monitoring_During_the_Squat_Exercise)
- [Crowdability -- Strive Deal](https://crowdability.com/deals/strive-tech)

---

## Section 2: Textile Electrode Feasibility for Rough Demo Garment

### Overview

Textile electrodes for sEMG are well-established in research and increasingly in commercial products (Strive, Myontec, Athos). For a demo garment, the simplest viable approach is sewing conductive fabric patches into a compression shirt with snap connectors to external EMG hardware.

### DIY Fabrication Methods

#### Method 1: Conductive Fabric Patches + Snap Connectors (Simplest -- Recommended for Demo)

This is the MyoWare-documented approach and the fastest path to a working demo:

1. **Cut** conductive fabric into rectangular electrode patches (~15mm x 45mm for mid-electrode, ~15mm x 50mm for end electrodes)
2. **Sew** patches into a compression shirt/sleeve using zigzag stitch (allows stretch)
3. **Attach** 12mm button snaps through the conductive fabric using a snap kit
4. **Connect** snap leads to EMG front-end (MyoWare, OpenBCI, or custom ADS1299 board)
5. **Wet** the electrode area lightly with water or electrode spray before use (improves skin contact for dry textile electrodes)

**Equipment needed:** Scissors, sewing machine (or hand needle), snap pliers, multimeter for testing

#### Method 2: Ohiri et al. 2022 -- Laser Cut + Heat Press (Better Quality, More Equipment)

From the Johns Hopkins APL paper (Ohiri et al., *Scientific Reports*, 2022):

1. **Laser cut** conductive fabric (silver-plated Lycra, specifically LessEMF A321) into electrode and trace shapes
2. **Heat-press laminate** the cut pieces onto the inside of a compression garment using thermoplastic adhesive film
3. Result: integrated electrodes + conductive traces (no external wiring needed inside the garment)

**Equipment needed:**
- CO2 laser cutter (available at most makerspaces, ~$50-100/session)
- Heat press ($100-300 for a basic one, or use a makerspace)
- Conductive stretch fabric (LessEMF A321 or equivalent)
- Thermoplastic adhesive film (heat-activated bonding)

**Key result from paper:** sEMG signal quality was comparable to conventional adhesive Ag/AgCl electrodes, with improved comfort and reusability. Materials are machine-washable.

#### Method 3: Embroidered Electrodes (Best Durability, Hardest DIY)

Using conductive thread (silver-coated polyamide) embroidered directly into fabric:
- Lock stitch or moss stitch patterns
- Requires computerized embroidery machine for consistency
- Best for production, overkill for a demo

### Signal Quality: Textile vs. Adhesive Ag/AgCl

Research consensus from multiple studies:

| Electrode Type | SNR (dB) | Notes |
|---|---|---|
| Adhesive Ag/AgCl (gold standard) | ~24-35 dB | Single-use, requires gel, excellent contact |
| Stainless steel fabric (SSF) | ~17.7 dB | Durable, lower SNR |
| Silver-coated embroidery | ~13.3 dB | Variable by stitch pattern |
| Optimized embroidered design | ~35.2 dB | On par with Ag/AgCl when well-designed |
| Ohiri et al. e-textile suit | Comparable to Ag/AgCl | Laser-cut silver Lycra, heat-pressed |

**Key findings:**
- Electrode diameter >= 20mm and compression pressure >= 10 mmHg are critical for good signal
- Compression garment naturally provides needed pressure
- Silver-plated fabrics consistently outperform other conductive textiles
- Light moisture (water spray) dramatically improves dry textile electrode performance
- During exercise, sweat naturally provides moisture, improving contact over time

### Material Costs (Textile Electrode Bill of Materials)

#### Conductive Fabric

| Product | Source | Size | Price | Notes |
|---|---|---|---|---|
| Woven Conductive Fabric (Cu/Ni plated polyester) | [Adafruit #1168](https://www.adafruit.com/product/1168) | 20cm x 20cm | **$4.95** | <1 ohm/ft, good for prototyping |
| Knit Conductive Fabric (silver plated) | [Adafruit #1167](https://www.adafruit.com/product/1167) | 20cm x 20cm | **$9.95** | Silver, stretchable, often out of stock |
| Stretch Conductive Fabric (silver-plated Lycra) | [LessEMF A321](https://lessemf.com/product/stretch-conductive-fabric/) | ~12" x 13" | **~$30-40** | Used in Ohiri et al. paper, best for EMG |
| Conductive Fabric (silver) | [Amazon -- Amradield](https://www.amazon.com/Grounding-Conductive-Electrode-Magnetic-Blocking/dp/B07V3VTBWV) | 40" x 59" | **~$20-35** | Large sheet, silver-coated nylon |

#### Conductive Thread

| Product | Source | Length | Price | Notes |
|---|---|---|---|---|
| AGSIS-LITE Silver-Coated Nylon | [Amazon](https://www.amazon.com/AGSIS-LITE-Conductive-Silver-Coated-Textiles-Electronics/dp/B07NF393C9) | 50 ft | **~$10-15** | Good for traces/connections |
| AGSIS-LITE Silver-Coated Nylon | [Amazon](https://www.amazon.com/AGSIS-LITE-Conductive-Silver-Coated-Textiles-Electronics/dp/B07PZ8LM8L) | 1000 ft | **~$40-60** | Bulk option |
| AGSIS High-Conductivity | [Amazon](https://www.amazon.com/AGSIS-Conductive-Silver-Coated-Textiles-Electronics/dp/B01M9FHACB) | 100 ft | **~$15-25** | Higher conductivity variant |

#### Other Components

| Item | Source | Price | Notes |
|---|---|---|---|
| 12mm Button Snap Kit | Amazon | **~$8-12** | For electrode-to-wire connections |
| Compression shirt | Amazon | **~$15-25** | Base garment |
| Electrode spray/gel | Amazon | **~$8-15** | Optional, improves dry electrode contact |

**Total estimated BOM for a demo garment: ~$50-80** (using Adafruit conductive fabric + snaps + compression shirt)

### Minimum Viable Demo Garment: Recommended Approach

**Goal:** Working sEMG garment for demo purposes, built in a weekend

**Recipe:**
1. Buy a tight-fitting compression shirt ($15-25)
2. Buy 2x Adafruit woven conductive fabric squares ($10 total) -- enough for 12+ electrode patches
3. Buy a 12mm snap kit from Amazon ($8-12)
4. Cut conductive fabric into ~20mm diameter circles or ~15mm x 45mm rectangles (3 patches per EMG channel: mid-electrode, two end-electrodes)
5. Zigzag-stitch patches onto inside of compression shirt at target muscle locations
6. Press snaps through each patch
7. Connect snap leads to MyoWare 2.0 sensors or ADS1299-based board
8. Lightly dampen electrode areas before use (or just start exercising -- sweat works)

**What you get:** A reusable, washable demo garment with embedded EMG electrodes that produces signal quality adequate for muscle activation detection. Not clinical-grade, but sufficient for demonstrating the concept and cueing system.

**What to skip for the demo:**
- Laser cutting (requires equipment access)
- Embroidery (requires machine)
- Conductive traces inside the garment (just use external snap-to-wire connections)
- Custom PCB (use off-the-shelf EMG front-end)

### Key References

- [MyoWare Conductive Fabric Electrodes Tutorial](https://myoware.com/project/conductive-fabric-electrodes/)
- [Ohiri et al. 2022 -- E-textile sEMG Suit](https://pubmed.ncbi.nlm.nih.gov/35688946/) (Scientific Reports)
- [Lam et al. 2022 -- Textile Electrode Materials for EMG Smart Garments](https://pmc.ncbi.nlm.nih.gov/articles/PMC8811440/)
- [Embroidered Textile Electrodes for EMG (Sensors, 2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10181695/)
- [Textile Electrode EMG Comparison Using PCA](https://www.mdpi.com/2673-4591/35/1/6)
- [EMG Textile Electrode Optimization -- Size and Pressure](https://pubmed.ncbi.nlm.nih.gov/33086662/)
