# OceanTrace — 1-Page PRD

**SIH 2026 · Problem Statement #26143 (NTRO) · Team Adamya**

---

## 1. The Problem

When an oil spill happens at sea, satellites can spot the dark patch on the water — but that's only step one. Two much harder questions follow:

- **Where did it actually come from?** By the time it's spotted, the slick has already drifted with the currents — its current position is not its origin.
- **Who's responsible?** No one confesses to a spill. Someone has to manually cross-reference which ships were in the area at the right time — slow, and often too late to matter.

Meanwhile, oil keeps spreading, evidence degrades, and coastal ecosystems and fisheries take the damage.

## 2. Who This Is For

- **Coast guard / maritime enforcement teams** (like NTRO) who need to act fast once a spill is spotted
- **Environmental response agencies** who need to know where the spill is heading next, not just where it is now
- **Investigators** who currently reconstruct vessel movement manually from AIS records after the fact

## 3. Our Solution

OceanTrace is an automated pipeline that:

1. **Detects** the oil spill directly from satellite radar imagery, using a trained AI model
2. **Reconstructs the drift** — simulates ocean currents backward to estimate where and when it started, and forward to predict where it's heading
3. **Cross-references ship traffic** near that estimated origin point and time, ranking the most likely responsible vessels
4. **Shows it all** on one interactive map — the spill, its drift path, and the ranked suspects

## 4. Real User Story

*A satellite passes over the Arabian Sea and captures a radar image. Within minutes, OceanTrace flags a dark patch as a likely oil spill, traces its drift backward to estimate it started 6 hours earlier near a specific point, and cross-references vessel traffic — surfacing one cargo ship that was in exactly the right place at exactly the right time. A response team that would normally spend hours manually piecing this together instead has a ranked starting point in minutes.*

## 5. Existing Solutions — and the Gap

| Existing Approach | What It Does | Where It Falls Short |
|---|---|---|
| Manual satellite image review | Human analysts scan SAR imagery for spills | Slow, doesn't estimate origin or attribute responsibility |
| Spill-detection-only tools/research | Detect and outline the spill shape | Stop there — no drift reconstruction, no vessel attribution |
| Manual AIS investigation | Investigators separately pull vessel records after a spill is confirmed | Disconnected from detection; happens hours/days later, after the trail has gone cold |

**The gap:** every piece of this exists somewhere in isolation. Nobody closes the loop — detection → drift → attribution — as one automated pipeline.

## 6. Our USP

**Existing tools stop at detecting the spill. We close the loop — detection, drift reconstruction, and vessel attribution — as one pipeline, validated end-to-end on real satellite data, not just a synthetic demo.**

## 7. What Makes Us Credible, Not Just Ambitious

- Built on a real trained AI model (not a mock), validated on a real downloaded satellite scene, not only a textbook demo image
- Honest about what's real and what's simulated at every stage — we don't oversell an unfinished piece as more complete than it is
- A working, clickable dashboard exists today — not just slides

## 8. Impact

- **Before:** Manual detection-to-attribution can take hours to days, often after the trail has gone cold
- **After:** An automated first pass in minutes, giving response teams a starting point instead of a blank page

## 9. Future Scope

- Real-time satellite feed ingestion (instead of manual scene download)
- Real AIS data integration (Global Fishing Watch identified as the best lead)
- Spill age estimation (physics-based, already prototyped, not yet wired into the live demo)
- Full-scene scanning instead of a single representative crop