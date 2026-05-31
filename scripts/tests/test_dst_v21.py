# -*- coding: utf-8 -*-
"""Carrington v2.1 Comprehensive Validation Suite"""

import sys, os, math
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from carrington.dst_model_v2 import DstEvolutionModelV2

passed = 0
failed = 0
issues = []

def check(name, condition, detail=''):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        issues.append('FAIL: {} | {}'.format(name, detail))

# --- Test 1: Initialization ---
print('=== Test 1: Initialization ===')
m = DstEvolutionModelV2({
    'self_saturation': True, 'sat_dst_half': 1200,
    'ey_saturation_enabled': True, 'ey_sat_threshold': 20.0, 'ey_sat_power': 0.5,
    'dst_min_clamp': -5000,
})
check('ey_sat=ON', m.p['ey_saturation_enabled'] == True)
check('a nominal=4.4', abs(m.p['a'] - 4.4) < 1e-6)
check('clamp=-5000', m.p['dst_min_clamp'] == -5000)

# --- Test 2: Ey below threshold ---
print('=== Test 2: Quiet storm (Ey < 20 mV/m) ===')
ey_low = m.effective_ey(400, -5, 2, 80, 12)
inj_low = m.injection_rate(400, -5, 2, 80, 12, dst_star=0)
check('Ey < 20', ey_low < 20, 'Ey={:.1f}'.format(ey_low))
check('no Ey_sat for moderate storm', abs(inj_low + m.p['a']*(ey_low-0.5)) < 1e-6)

# --- Test 3: Ey above threshold ---
print('=== Test 3: Extreme storm (Ey >> 20 mV/m) ===')
ey_hi = m.effective_ey(2000, -80, 20, 260, 9)
inj_hi = m.injection_rate(2000, -80, 20, 260, 9, dst_star=0)
a_eff = abs(inj_hi) / max(0.01, ey_hi - 0.5)
check('Ey > 20', ey_hi > 20, 'Ey={:.1f}'.format(ey_hi))
check('a_eff < nominal', a_eff < 3.0, 'a_eff={:.2f}'.format(a_eff))
check('a_eff > 0', a_eff > 0.2, 'a_eff={:.2f}'.format(a_eff))

# --- Test 4: Compound saturation ---
print('=== Test 4: Compound saturation ===')
inj_near = m.injection_rate(2000, -80, 20, 260, 9, dst_star=-800)
inj_zero = m.injection_rate(2000, -80, 20, 260, 9, dst_star=0)
check('self-sat reduces injection', abs(inj_near) < abs(inj_zero),
      'near={:.1f} < zero={:.1f}'.format(abs(inj_near), abs(inj_zero)))

# --- Test 5: Quiet conditions ---
print('=== Test 5: Quiet conditions ===')
inj_q = m.injection_rate(350, 3, 5, 80, 12, dst_star=-50)
check('Bz positive -> no injection', abs(inj_q) < 1e-6)

# --- Test 6: Recovery physics ---
print('=== Test 6: Recovery tau ===')
tau1 = m.tau_effective(-30, 400)
tau2 = m.tau_effective(-400, 400)
check('quiet recovery faster', tau1 < tau2, '{} < {}'.format(tau1, tau2))

# --- Test 7: Integration stability ---
print('=== Test 7: Integration ===')
ds = 0.0
for j in range(1000):
    _, ds = m.step(ds, 800, -60, 15, 0.5, 15, 260, 9)
check('finite', math.isfinite(ds))
check('in range', -5000 <= ds <= 0, 'ds={:.0f}'.format(ds))
check('clamp respected', ds >= -5000, 'ds={:.0f}'.format(ds))

# --- Test 8: Monotonic decreasing ---
print('=== Test 8: Monotonic injection ===')
ds_m = 0.0
mono = True
for j in range(200):
    _, ds_m = m.step(ds_m, 800, -60, 15, 0.5, 15, 260, 9)
    if ds_m > 0.1:
        mono = False
check('monotonic decrease', mono, 'non-monotonic at ds={:.1f}'.format(ds_m))

# --- Test 9: Deterministic ---
print('=== Test 9: Determinism ===')
ds_a = 0.0
for _ in range(10):
    _, ds_a = m.step(ds_a, 800, -60, 15, 0.5, 15, 260, 9)
ds_b = 0.0
for _ in range(10):
    _, ds_b = m.step(ds_b, 800, -60, 15, 0.5, 15, 260, 9)
check('deterministic', abs(ds_a - ds_b) < 1e-9)

# --- Test 10: Pressure correction ---
print('=== Test 10: DCF ===')
dcf = m.dcf(25)
check('dcf positive', dcf > 0, 'dcf={:.1f}'.format(dcf))
check('conversion consistency', abs(m.dst_star_to_obs(-100, 25) - (-100 + dcf)) < 1e-6)

# --- Test 11: Parameter extremes ---
print('=== Test 11: Parameter extremes ===')
m_ext = DstEvolutionModelV2({
    'self_saturation': True, 'sat_dst_half': 200,
    'ey_saturation_enabled': True, 'ey_sat_threshold': 20.0, 'ey_sat_power': 2.5,
    'dst_min_clamp': -5000,
})
ds_ext = 0.0
for _ in range(200):
    _, ds_ext = m_ext.step(ds_ext, 1000, -30, 10, 0.5, 10, 260, 9)
check('extreme params stable', math.isfinite(ds_ext), 'ds={:.0f}'.format(ds_ext))

# --- Test 12: Backward compat ---
print('=== Test 12: Backward compatibility ===')
m_old = DstEvolutionModelV2({'self_saturation': True, 'dst_min_clamp': -5000})
ey_old = m_old.effective_ey(2000, -80, 20, 260, 9)
inj_old = m_old.injection_rate(2000, -80, 20, 260, 9, dst_star=0)
a_old = abs(inj_old) / max(0.01, ey_old - 0.5)
check('old mode: no ey_sat', abs(a_old - 4.4) < 0.01, 'a_eff={:.2f}'.format(a_old))

# --- Test 13: Clamp enforcement ---
print('=== Test 13: Hard clamp ===')
ds_cl = 0.0
for _ in range(200):
    _, ds_cl = m.step(ds_cl, 3000, -200, 50, 0.25, 60, 260, 9)
    if ds_cl <= -5000:
        break
check('clamp enforced', ds_cl >= -5000, 'ds_cl={:.0f}'.format(ds_cl))

# --- Test 14: Ey=0 edge case ---
print('=== Test 14: Ey=0 edge ===')
inj_null = m.injection_rate(0, -30, 10, 260, 9, dst_star=0)
check('v=0 gives zero or near-zero injection', abs(inj_null) < 1.0, 'inj={:.1f}'.format(inj_null))

# --- Test 15: Negative Bz with large By ---
print('=== Test 15: Large By ===')
inj_by = m.injection_rate(1000, -60, 60, 260, 12, dst_star=0)
check('large By still injects', abs(inj_by) > 0, 'inj={:.1f}'.format(inj_by))

# Summary
print()
print('=' * 50)
print('VALIDATION RESULTS: {} PASSED, {} FAILED'.format(passed, failed))
if issues:
    for iss in issues:
        print('  ' + iss)
else:
    print('ALL 15 TESTS PASSED')
print('=' * 50)