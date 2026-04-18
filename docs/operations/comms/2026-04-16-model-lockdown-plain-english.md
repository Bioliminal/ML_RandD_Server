# Model Stack — Plain English (2026-04-16)

**Status:** current
**Created:** 2026-04-16
**Updated:** 2026-04-16
**Owner:** AaronCarney

**For:** Kelsi, Rajat, Rajiv.
**Why this doc exists:** if anyone asks "what's our stack, and can we actually ship it?" — this is the answer. One page. No jargon.

**Long version:** `docs/research/model-commercial-viability-matrix-2026-04-16.md` (476 lines — only read if you need to defend a specific choice).

---

## The 5 decisions

1. **Phone pose: MediaPipe BlazePose Full.** Apache 2.0 + Google ML Kit terms. Ships commercially as-is. No retrain, no licensing landmine. Same model Google ships in thousands of apps.
2. **Server 3D pose lift: none for the demo.** Bicep curl is a single-plane movement. Elbow flexion from BlazePose's 2D landmarks is enough. We don't call WHAM, MotionBERT, HSMR, or OpenCap Monocular at all.
3. **Server kinetics (angles, rep peaks): our own geometry.** Computed directly from BlazePose landmarks. Our code.
4. **Server reasoner: YAML rule engine.** Our code. This is the product differentiator — the place where our clinical evidence (Harris-Hayes, Hewett, Sahrmann patterns) becomes an observation a user can read.
5. **Server scorer: DTW / normalized cross-correlation.** Classical signal processing. Our code.

Nothing in the demo path depends on a research-only model or a non-commercial dataset. Zero licensing fees to third parties.

---

## What changed vs the 4-10 pipeline decision doc

That doc chained **WHAM → OpenCap Monocular → SMPL → rule engine**. Each of those has a separate commercial blocker (WHAM is non-commercial, OpenCap Monocular needs a license negotiation, SMPL needs Meshcapade). For a single-plane bicep curl demo, we don't need any of them. The 4-10 doc is flagged superseded and belongs to the post-demo conversation, not the 4/20 conversation.

---

## Post-demo upgrade path

When we add movements that genuinely need 3D (rollup spine, asymmetric work), two real options: negotiate commercial licensing with Max Planck / Meshcapade (case-by-case, uncosted), or retrain a MotionBERT-class lifter on proprietary data (~6 months, $70k–$600k). We do not touch either until product metrics earn the investment.

---

## If asked by outsiders ("can you ship this?")

> "Yes. The phone runs a model Google already licenses for commercial use. Everything else — angle computation, rep scoring, chain reasoning — is our own code. We know the licensing landscape of the research-grade alternatives cold and we have a priced path to bring them in if a later movement needs them. Nothing on our shipping stack breaks under a closer look."

That's the honest answer, and it's also the strongest one.

---

*If anything here goes stale, the matrix at `docs/research/model-commercial-viability-matrix-2026-04-16.md` is the source of truth.*
