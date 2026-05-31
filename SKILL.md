---
name: extreme-storm-backcast
description: "Dual-model extreme geomagnetic storm backcasting system. Combines U(1) Solar Model v4.0 (phase-based risk assessment with dual-window architecture, 72.7% hit rate on 11 historical events) and Carrington Space Engine v2.1 (self-consistent Dst evolution with Ey polar cap potential saturation). Trigger keywords: extreme geomagnetic storm, backcast, retrodiction, 1770, Carrington, Dst, U(1) phase, U1 solar, solar cycle, ring current, Ey saturation, Siscoe-Hill, polar cap potential, MCMC inversion, space weather."
license: MIT
version: "1.0.0"
---
# Extreme Storm Backcast System

Dual-model extreme geomagnetic storm backcasting: U(1) Solar Model v4.0 + Carrington Space Engine v2.1.

## Quick Start

Clone into your OpenClaw skills directory:
```bash
git clone https://github.com/eluckydog/extreme-storm-backcast.git ~/.qclaw/skills/extreme-storm-backcast
```

Then in any OpenClaw session, say: **"分析 1770 年极端地磁暴"** and the skill auto-loads.

## What This Skill Does

### U(1) Solar Model v4.0
- Phase-based solar activity risk assessment
- Dual-window architecture: W1 (sunspot peak, 142.9°±60°) + W2 (storm peak, 222.0°±45°)
- 72.7% hit rate on 11 historical extreme events
- Validated on 334,123 flare events (1986-2020, 3 solar cycles)

### Carrington Space Engine v2.1
- Self-consistent Dst evolution model
- Ey polar cap potential saturation (Siscoe-Hill, 200 kV cap)
- Forward simulation from solar wind parameters
- MCMC parameter inversion for unknown historical events

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/u1_solar_model_v4.py` | U(1) phase-based solar activity model |
| `scripts/carrington/dst_model_v2.py` | Dst evolution with Ey saturation |
| `scripts/inversion_1770.py` | MCMC parameter inversion for 1770 event |
| `scripts/simulate_1770_v4.py` | Joint U(1) + Carrington forward simulation |

## References

- `references/audit-report_2026-05-28.md` — Third-party audit (门生, 红队, 工程)

## Model Versions

| Model | Version | Key Feature |
|-------|---------|-------------|
| U(1) Solar | v4.0 | Dual-window (72.7% hit rate) |
| Carrington Dst | v2.1 | Ey polar cap saturation (Siscoe-Hill) |
| 1770 Inversion | v1.0 | MCMC with 3 observational constraints |

## Key Findings

- Storm phase distribution is bimodal (CME + CIR/SIR drivers)
- 1770 event: Dst ≈ -884 nT (forward), MCMC inversion Dst ≈ -1001 nT
- Ey saturation is essential for modeling Dst < -750 nT events
- Single-window hit rate ceiling: 45-55% (physics-limited)

## Verification

- 23/23 test suite passed (`scripts/tests/test_dst_v21.py`)
- Triple audit: 门下省 (K3) + 专业红队 (T3-A) + 工程化AI (B+)
- GitHub: https://github.com/eluckydog/extreme-storm-backcast
