# Extreme Storm Backcast

> A dual-model system that backcasts historical extreme geomagnetic storms using U(1) solar phase theory and self-consistent ring current physics.

## Core Insight

Two independently developed models — the **U(1) Solar Model** (phase-based risk assessment) and the **Carrington Space Engine** (forward Dst simulation with self-consistent saturation) — are linked together to backcast the 1770 Great East Asian Storm and other extreme events. The combined system achieves 72.7% hit rate on 11 historical extreme storms.

## Story (Three Chapters)

### Chapter 1: U(1) Solar Phase → Risk Windows
The Sun's magnetic activity follows a circular phase φ(t) with period ~11 years. Extreme flares cluster at φ ≈ 142.9° (sunspot maximum), while geomagnetic storms form a dual-peak distribution: a CME-driven peak at W1 (142.9° ± 60°) and a CIR/SIR-driven Gnevyshev peak at W2 (222.0° ± 45°). Combined hit rate: 8/11 events (72.7%).

### Chapter 2: Carrington Dst → Self-Consistent Saturation
The Dst evolution model incorporates Ey polar cap potential saturation (Siscoe-Hill model) to resolve unphysical over-injection under extreme solar wind conditions (Ey >> 20 mV/m). A power-law decay in coupling efficiency (a_eff) enables physically motivated extrapolation to events beyond the calibration range.

### Chapter 3: 1770 Event → Joint Backcast
For the 1770.9 Great East Asian Storm (Dst ≈ −1100 ± 300 nT, MLAT 18.8°):
- **U(1) v4 phase**: 185.7° → W1 HIGH risk (0.650)
- **Carrington v2.1 forward**: Dst = −884 nT (2× Carrington scenario)
- **Carrington v2.1 MCMC inversion**: Dst = −1001 nT, Bz = 112 nT (87% acceptance)
- **Observational constraints**: Sunspot area ~6000 msh, flare energy ~10³⁴ erg, MLAT ~18.8° → all consistent

## Repository Structure

```
extreme-storm-backcast/
├── README.md                  # You are here
├── u1_model/                  # U(1) Solar Model v4.0
│   ├── u1_solar_model_v4.py   # Core model (dual-window, Poisson, MCMC)
│   └── tests/                 # Test suite
├── carrington/                # Carrington Space Engine v2.1
│   ├── carrington/            # Core package
│   │   ├── __init__.py
│   │   └── dst_model_v2.py    # Dst evolution with Ey saturation
│   └── tests/                 # Test suite (23 validations)
├── 1770_event/                # 1770 Great East Asian Storm
│   ├── code/
│   │   ├── inversion_1770.py  # MCMC inversion with U(1) priors
│   │   └── simulate_1770_v4.py # Forward simulation
│   └── data/                  # Observational constraints
├── joint_pipeline/            # U1 → Carrington → Inversion pipeline
├── audits/                    # Three-level audit report
└── examples/                  # Demo notebooks
```

## Installation

```bash
pip install numpy scipy matplotlib
```

## Quick Start

```python
# 1. Evaluate U(1) risk for any date
from u1_model.u1_solar_model_v4 import U1SolarModel
model = U1SolarModel()
risk = model.evaluate_risk(1770.9)  # → W1, HIGH, 0.650

# 2. Forward simulate Dst
from carrington.dst_model_v2 import DstEvolutionModelV2
dst_model = DstEvolutionModelV2(ey_saturation_enabled=True)
result = dst_model.simulate(v_cme=2500, Bz_ICME=-100, n_cme=5)

# 3. Run full backcast pipeline
python joint_pipeline/run_joint_backcast.py --event 1770.9
```

## Related Repositories

- [**u1-solar-modeling**](https://github.com/eluckydog/u1-solar-modeling) — U(1) solar phase model with 35 years of flare data
- [**Carrington-Space-Engine**](https://github.com/eluckydog/Carrington-Space-Engine) — Self-consistent ring current Dst model

## Physics References

- **U(1) Solar Phase**: von Mises circular statistics, Poisson peak-over-threshold modeling
- **Ring Current**: Burton-McPherron-Russell Dst equation with self-consistent energy balance
- **Saturation**: Siscoe-Hill polar cap potential saturation (Φ_PC ≤ 200 kV)
- **1770 Event**: Kataoka & Hayakawa 2017 (Dst estimate), Hayakawa 2017 (sunspot/MSAS), Shibata 2013 (flare energy)

## License

MIT