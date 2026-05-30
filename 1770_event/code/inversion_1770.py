#!/usr/bin/env python3
"""
1770 Inversion Model — 1770年极端磁暴事件反演

基于 U(1) 太阳模型 + Carrington Dst 模型，对1770年事件进行贝叶斯反演：
  观测值（已知） → 反演 CME/太阳风参数（未知）

观测约束 (1770-09-10~19):
  - Dst ≈ -1100 nT          (Kataoka 2017)
  - 最南极光 18.8° MLAT      (Hayakawa 2017)
  - 黑子面积 6000 millionths   (Hayakawa 2017)
  - 持续 ~9夜                (Hayakawa 2017)
  - 耀斑能量 ~10^34 erg      (Shibata 2013 缩放)

反演参数（待求）:
  - v_cme:  CME 速度 [km/s]
  - m_cme:  CME 质量 [g]
  - bz_imc: ICME 南向 Bz [nT]（绝对值）
  - v_sw:   太阳风速度 [km/s]
  - p_dyn:  太阳风动压 [nPa]
  - n_cme:  多次CME次数 [整数, 1-5]

方法:
  1. 参数空间采样 (Latin Hypercube / MCMC)
  2. 正向模型: CME参数 → 太阳风参数 → Dst剖面 (Carrington DstModelV2)
  3. 似然函数: 模拟Dst与观测约束的匹配程度
  4. 后验: 返回参数分布

参考:
  - U1SolarModel:        projects/u1-solar-modeling/code/u1_solar_model.py
  - DstEvolutionModelV2: projects/carrington-space-engine/carrington/dst_model_v2.py
  - Hayakawa+2017 ApJL 850 L31
  - Kataoka+Iwahashi 2017 Space Weather 15, 1314
  - Ebihara+2017 Space Weather 15, 1373
"""

import sys
import os
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple

# ===== 路径设置（导入依赖模型）=====
# inversion_1770.py 位于 projects/1770-inversion-model/code/
# MATH_SCIENCE = workspace-math-science 根目录
CODE_DIR = os.path.dirname(os.path.abspath(__file__))
# 从 code/ 向上3层: code/ -> 1770-inversion-model/ -> projects/ -> workspace-math-science/
MATH_SCIENCE = os.path.abspath(os.path.join(CODE_DIR, '..', '..', '..'))

# 调试：打印实际路径
print('[DEBUG] CODE_DIR  =', CODE_DIR)
print('[DEBUG] MATH_SCIENCE =', MATH_SCIENCE)
print('[DEBUG] U1 target =', os.path.join(MATH_SCIENCE, 'projects', 'u1-solar-modeling', 'code'))


def _try_import_u1():
    """尝试导入 U1SolarModel，返回 (success, model_or_None)"""
    # 方法1: 加入 u1-solar-modeling/code 目录
    p1 = os.path.join(MATH_SCIENCE, 'projects', 'u1-solar-modeling', 'code')
    if os.path.exists(p1):
        if p1 not in sys.path:
            sys.path.insert(0, p1)
        try:
            from u1_solar_model import U1SolarModel
            m = U1SolarModel()
            print(f'[U1] loaded from {p1}')
            return True, m
        except Exception as e:
            print(f'[U1] import from {p1} failed: {e}')
    # 方法2: 直接导入（如果已安装或在 path 中）
    try:
        from u1_solar_model import U1SolarModel
        m = U1SolarModel()
        print('[U1] loaded from existing sys.path')
        return True, m
    except Exception:
        pass
    print('[U1] NOT loaded — U1 prior will be disabled')
    return False, None


def _try_import_carrington():
    """尝试导入 DstEvolutionModelV2，返回 success"""
    p1 = os.path.join(MATH_SCIENCE, 'projects', 'carrington-space-engine')
    if os.path.exists(p1):
        if p1 not in sys.path:
            sys.path.insert(0, p1)
        try:
            from carrington.dst_model_v2 import DstEvolutionModelV2
            print(f'[Carrington] loaded from {p1}')
            return True
        except Exception as e:
            print(f'[Carrington] import from {p1} failed: {e}')
    print('[Carrington] NOT loaded — will use analytic approximation')
    return False


_success_u1, _u1_model = _try_import_u1()
HAS_U1 = _success_u1

HAS_CARR = _try_import_carrington()


# ===== 1770 观测约束（常量）=====
OBSERVATIONS_1770 = {
    # 注意: 1770年无科学观测记录，所有数值均为现代论文推估
    # 误差应包含 epistemic uncertainty（系统误差）
    'dst_est': -1100.0,       # nT, Kataoka 2017 (推估值)
    'dst_err': 300.0,         # nT, 扩大: 推估误差 + 方法不确定性
    'aurora_mlat_min': 18.8,  # 最南观测 MLAT (°)
    'aurora_mlat_err': 3.0,   # °, 扩大: 历史记录位置误差 + GUFM1模型误差
    'sunspot_area': 6000.0,   # millionths of hemisphere
    'sunspot_err': 1500.0,    # 扩大
    'duration_nights': 9,      # 极光持续夜数
    'flare_energy_erg': 1e34, # ~10^34 erg (Shibata 2013 缩放)
    'year': 1770.7,           # 事件年份（年中）
    'epistemic_note': '所有观测均为历史文献推估，非实测。Kataoka方法系统误差未量化。',
}


@dataclass
class CMEParams:
    """CME/ICME 参数（反演目标）"""
    v_cme: float       # CME 速度 [km/s]
    bz_imc: float      # ICME Bz 强度（南向，正值）[nT]
    v_sw: float        # 太阳风速度 [km/s]
    p_dyn: float       # 太阳风动压 [nPa]
    m_cme: float       # CME 质量 [g]
    n_cme: int = 1    # 多次CME次数
    tau_main: float = 6.0  # 主相持续时间 [h]

    def to_dict(self) -> dict:
        return {
            'v_cme': self.v_cme,
            'bz_imc': self.bz_imc,
            'v_sw': self.v_sw,
            'p_dyn': self.p_dyn,
            'm_cme': self.m_cme,
            'n_cme': self.n_cme,
            'tau_main': self.tau_main,
        }


@dataclass
class InversionConfig:
    """反演配置"""
    n_samples: int = 5000          # MCMC/采样样本数
    burn_in: int = 1000            # burn-in 样本数
    method: str = 'mcmc'          # 'mcmc' | 'lhs' | 'grid'
    prior_bounds: dict = field(default_factory=lambda: {
        'v_cme': (1500, 3500),    # km/s
        'bz_imc': (30, 150),       # nT
        'v_sw': (800, 2500),       # km/s
        'p_dyn': (5.0, 50.0),     # nPa
        'm_cme': (1e15, 5e16),    # g
        'n_cme': (1, 5),           # 整数
        'tau_main': (3.0, 18.0),  # h
    })
    use_u1_prior: bool = True      # 使用 U(1) 相位作为先验
    use_carrington_forward: bool = True  # 使用 Carrington 正向模型


class ForwardModel:
    """正向模型: CME参数 → Dst剖面"""

    def __init__(self, use_carrington=True):
        self.use_carrington = use_carrington and HAS_CARR
        if self.use_carrington:
            from carrington.dst_model_v2 import DstEvolutionModelV2
            self.dst_model = DstEvolutionModelV2()

    def simulate_dst(self, params: CMEParams) -> Dict:
        if self.use_carrington:
            return self._simulate_carrington(params)
        else:
            return self._simulate_analytic(params)

    def _simulate_carrington(self, params: CMEParams) -> Dict:
        """使用 Carrington DstModelV2 正向模拟"""
        model = self.dst_model

        v_sw = params.v_sw
        bz = -params.bz_imc  # 南向为负
        by = params.bz_imc * 0.3

        bz_eff = bz * (1.0 + 0.3 * (params.n_cme - 1))

        event = {
            'v_sw': v_sw,
            'bz': bz_eff,
            'by': by,
            'main_h': params.tau_main,
            'p_dyn': params.p_dyn,
            'doy': 260,
            'ut_hour': 9,
            'bz_persist': 0.7,
        }

        dst_star = 0.0
        dst_history = []
        dt = 0.25
        n_steps = int((params.tau_main + 12) / dt)

        for i in range(n_steps):
            t = i * dt
            if t < params.tau_main:
                bz_t = bz_eff
            else:
                decay = math.exp(-(t - params.tau_main) / 6.0)
                bz_t = bz_eff * decay * 0.5

            ddt, dst_next = model.step(
                dst_star, v_sw, bz_t, by, dt,
                event['p_dyn'], event['doy'], event['ut_hour']
            )
            dst_star = dst_next
            dst_history.append(dst_star)
            if dst_star < -2000:
                break

        dst_min = min(dst_history) if dst_history else -50.0

        aurora_mlat = 50.0 + 32.0 * (dst_min / 1100.0)
        aurora_mlat = max(10.0, min(60.0, aurora_mlat))

        return {
            'dst_min': dst_min,
            'dst_profile': dst_history[:100],
            'aurora_mlat': aurora_mlat,
            't_peak': params.tau_main * 0.7,
            'method': 'carrington_dst_v2',
        }

    def _simulate_analytic(self, params: CMEParams) -> Dict:
        """解析近似（无 Carrington 模型时使用）

        改进 Burton 公式 + 环电流自洽饱和效应:

        自洽饱和 (O'Brien & McPherron 2000):
          sat_factor = 1 / (1 + |Dst*| / Dst_half),  Dst_half = 1200 nT

        解析解（隐式方程的二次求根）:
          K = a * (Ey - e0) * tau * N_factor * p_factor
          y = |Dst_min|,  满足  y = K / (1 + y/D)
          →  y² + D·y - K·D = 0
          →  y = (-D + sqrt(D² + 4·D·K)) / 2
        """
        ey = params.v_sw * params.bz_imc / 1000.0
        if ey <= 0.5:
            dst_min = -50.0
            sat_factor = 1.0
        else:
            n_factor = 1.0 + 0.5 * max(0, params.n_cme - 1)
            tau = 8.0 if ey > 30 else 4.0
            p_factor = 1.0 + 0.02 * params.p_dyn

            a = 4.4
            D = 1200.0
            K = a * (ey - 0.5) * tau * n_factor * p_factor

            disc = D * D + 4.0 * D * K
            if disc < 0:
                y = 50.0
            else:
                y = (-D + math.sqrt(disc)) / 2.0

            dst_min = -max(0.0, y)
            dst_min = max(-5000, min(-50.0, dst_min))
            sat_factor = 1.0 / (1.0 + max(0, -dst_min) / D)

        aurora_mlat = 50.0 + 32.0 * (dst_min / 1100.0)
        aurora_mlat = max(10.0, min(60.0, aurora_mlat))

        return {
            'dst_min': dst_min,
            'dst_profile': [],
            'aurora_mlat': aurora_mlat,
            't_peak': params.tau_main * 0.7,
            'method': 'analytic_saturated',
            'sat_factor': sat_factor,
        }


class Likelihood:
    """似然函数: 模拟结果 vs 1770观测"""

    def __init__(self, observations: dict = OBSERVATIONS_1770):
        self.obs = observations

    def log_likelihood(self, sim: Dict) -> float:
        ll = 0.0

        dst_sim = sim.get('dst_min', -50.0)
        dst_obs = self.obs['dst_est']
        dst_err = self.obs['dst_err']
        ll += -0.5 * ((dst_sim - dst_obs) / dst_err) ** 2

        aurora_sim = sim.get('aurora_mlat', 40.0)
        aurora_obs = self.obs['aurora_mlat_min']
        aurora_err = self.obs['aurora_mlat_err']
        ll += -0.5 * ((aurora_sim - aurora_obs) / aurora_err) ** 2

        return ll

    def likelihood(self, sim: Dict) -> float:
        return math.exp(self.log_likelihood(sim))


class Prior:
    """先验分布（含 U(1) 相位先验）"""

    def __init__(self, bounds: dict, use_u1=True):
        self.bounds = bounds
        self.use_u1 = use_u1 and HAS_U1
        if self.use_u1:
            try:
                self.u1_model = _u1_model
                self.obs_year = OBSERVATIONS_1770['year']
                self.phi_1770 = self.u1_model.phase(self.obs_year)
                self.prob_1770 = self.u1_model.flare_probability(phase=self.phi_1770)
                phi_deg = math.degrees(self.phi_1770)
                mu_deg = self.u1_model.PHASE_LAG_DEG
                print(f'[Prior] U1 prior enabled: phi(1770)={self.phi_1770:.3f} rad '
                      f'({phi_deg:.1f}°), peak at {mu_deg:.1f}°, '
                      f'flare_prob={self.prob_1770:.3f}')
                self._print_u1_diagnostic()
            except Exception as e:
                self.use_u1 = False
                print(f'[Prior] U1 prior disabled: {e}')

    def _print_u1_diagnostic(self):
        """打印 1770 年 U(1) 相位的物理解释 — 太阳发生了什么？"""
        phi = self.phi_1770
        mu = self.u1_model.MU
        lag_deg = self.u1_model.PHASE_LAG_DEG

        diff = abs(phi - mu)
        if diff > math.pi:
            diff = 2.0 * math.pi - diff
        diff_deg = math.degrees(diff)

        prob = self.u1_model.flare_probability(phase=phi)
        rate = self.u1_model.flare_rate(phase=phi)

        print()
        print('  [U1 Diagnostic] 1770 年太阳发生了什么？')
        print(f'    U(1) 相位 phi = {phi:.3f} rad = {math.degrees(phi):.1f}°')
        print(f'    耀斑峰值相位 mu = {mu:.3f} rad = {lag_deg:.1f}°')
        print(f'    相位差 = {diff_deg:.1f}° '
              f'（{"在峰值附近" if diff_deg < 10 else ("接近峰值" if diff_deg < 30 else "离开峰值")}）')
        print(f'    耀斑概率 = {prob:.3f}  （0=极小，1=极大）')
        print(f'    预期耀斑率 = {rate:.0f} events/10°-bin/cycle')

        if diff_deg < 15:
            print('    >> 结论: 1770 年太阳处于 U(1) 活动峰值期附近！')
            print('             极端磁暴发生在最活跃的相位窗口内。')
        elif diff_deg < 45:
            print('    >> 结论: 1770 年太阳处于活动高期，但非峰值。')
        else:
            print('    >> 结论: 1770 年太阳不在活动高期，极端事件较意外。')
        print()

    def log_prior(self, params: CMEParams) -> float:
        ll = 0.0
        b = self.bounds

        p = params.to_dict()
        for key, (lo, hi) in b.items():
            if key == 'n_cme':
                continue
            val = p.get(key, (lo + hi) / 2)
            if val < lo or val > hi:
                return -math.inf

        if params.n_cme < b['n_cme'][0] or params.n_cme > b['n_cme'][1]:
            return -math.inf

        # U(1) 相位先验: 1770 年应在高活动期
        if self.use_u1:
            try:
                prob = self.u1_model.flare_probability(phase=self.phi_1770)
                if prob < 0.2:
                    ll += -5.0  # 强惩罚：1770年不可能是低活动期
                elif prob < 0.5:
                    ll += -1.0  # 弱惩罚
            except Exception:
                pass

        return ll

    def sample_prior(self) -> CMEParams:
        b = self.bounds
        v_cme = np.random.uniform(*b['v_cme'])
        bz_imc = np.random.uniform(*b['bz_imc'])
        v_sw = np.random.uniform(*b['v_sw'])
        p_dyn = np.random.uniform(*b['p_dyn'])
        m_cme = 10 ** np.random.uniform(math.log10(b['m_cme'][0]), math.log10(b['m_cme'][1]))
        n_cme = np.random.randint(b['n_cme'][0], b['n_cme'][1] + 1)
        tau_main = np.random.uniform(*b['tau_main'])
        return CMEParams(v_cme, bz_imc, v_sw, p_dyn, m_cme, n_cme, tau_main)


class InversionEngine:
    """1770 反演引擎（MCMC采样）"""

    def __init__(self, config: InversionConfig = InversionConfig()):
        self.config = config
        self.forward = ForwardModel(use_carrington=config.use_carrington_forward)
        self.likelihood = Likelihood()
        self.prior = Prior(config.prior_bounds, use_u1=config.use_u1_prior)
        self.samples: List[CMEParams] = []
        self.log_probs: List[float] = []

    def run_mcmc(self, n_samples: int = None, burn_in: int = None):
        n_samples = n_samples or self.config.n_samples
        burn_in = burn_in or self.config.burn_in

        samples = []
        log_probs = []

        current = CMEParams(
            v_cme=2500.0,
            bz_imc=80.0,
            v_sw=2000.0,
            p_dyn=20.0,
            m_cme=1e16,
            n_cme=3,
            tau_main=8.0,
        )
        sim = self.forward.simulate_dst(current)
        current_ll = self.likelihood.log_likelihood(sim)
        current_lp = self.prior.log_prior(current)
        current_log_post = current_ll + current_lp

        n_accept = 0
        total = n_samples + burn_in

        for i in range(total):
            proposed = self._perturb(current)

            sim_p = self.forward.simulate_dst(proposed)
            lp = self.likelihood.log_likelihood(sim_p)
            pp = self.prior.log_prior(proposed)
            proposed_log_post = lp + pp

            log_alpha = proposed_log_post - current_log_post
            if log_alpha > 0 or np.log(np.random.rand()) < log_alpha:
                current = proposed
                current_ll = lp
                current_lp = pp
                current_log_post = proposed_log_post
                if i >= burn_in:
                    n_accept += 1

            if i >= burn_in:
                samples.append(current)
                log_probs.append(current_log_post)

            if (i + 1) % 1000 == 0:
                acc_rate = n_accept / max(1, (i + 1 - burn_in))
                print(f"  MCMC step {i+1}/{total}, accept_rate={acc_rate:.2f}")

        self.samples = samples
        self.log_probs = log_probs
        print(f"MCMC 完成: {len(samples)} 样本, 接受率={n_accept/max(1, n_samples):.2f}")
        return samples, log_probs

    def _perturb(self, p: CMEParams, scale: float = 0.1) -> CMEParams:
        b = self.config.prior_bounds

        def _clip(val, lo, hi):
            return max(lo, min(hi, val))

        v_cme = _clip(np.random.normal(p.v_cme, scale * p.v_cme), *b['v_cme'])
        bz_imc = _clip(np.random.normal(p.bz_imc, scale * p.bz_imc), *b['bz_imc'])
        v_sw = _clip(np.random.normal(p.v_sw, scale * p.v_sw), *b['v_sw'])
        p_dyn = _clip(np.random.normal(p.p_dyn, scale * p.p_dyn), *b['p_dyn'])

        log_m = math.log10(p.m_cme)
        log_m_range = (math.log10(b['m_cme'][1]) - math.log10(b['m_cme'][0])) * scale
        m_cme = 10 ** _clip(np.random.normal(log_m, log_m_range),
                                   math.log10(b['m_cme'][0]),
                                   math.log10(b['m_cme'][1]))

        n_cme = p.n_cme
        if np.random.rand() < 0.3:
            n_cme = _clip(n_cme + np.random.randint(-1, 2), *b['n_cme'])

        tau_main = _clip(np.random.normal(p.tau_main, scale * p.tau_main), *b['tau_main'])

        return CMEParams(v_cme, bz_imc, v_sw, p_dyn, m_cme, int(n_cme), tau_main)

    def summarize(self) -> Dict:
        if not self.samples:
            return {'error': 'no samples'}

        v_cme = [s.v_cme for s in self.samples]
        bz_imc = [s.bz_imc for s in self.samples]
        v_sw = [s.v_sw for s in self.samples]
        p_dyn = [s.p_dyn for s in self.samples]
        m_cme = [s.m_cme for s in self.samples]
        n_cme = [s.n_cme for s in self.samples]

        def _stats(arr):
            return {
                'mean': float(np.mean(arr)),
                'median': float(np.median(arr)),
                'std': float(np.std(arr)),
                'ci_5': float(np.percentile(arr, 5)),
                'ci_95': float(np.percentile(arr, 95)),
            }

        return {
            'n_samples': len(self.samples),
            'v_cme_km_s': _stats(v_cme),
            'bz_imc_nT': _stats(bz_imc),
            'v_sw_km_s': _stats(v_sw),
            'p_dyn_nPa': _stats(p_dyn),
            'm_cme_g': _stats(m_cme),
            'n_cme': {
                'mean': float(np.mean(n_cme)),
                'mode': float(max(set(n_cme), key=n_cme.count)),
            },
            'log_prob_mean': float(np.mean(self.log_probs)),
        }

    def best_fit(self) -> Optional[CMEParams]:
        if not self.samples:
            return None
        idx = int(np.argmax(self.log_probs))
        return self.samples[idx]


def demo_inversion():
    """演示: 对1770事件进行反演"""
    print("=" * 60)
    print("1770 Inversion Model -- 1770年极端磁暴反演演示")
    print("=" * 60)
    print()
    print("[注意] 1770年无科学观测记录，所有约束均为现代论文推估值。")
    print("        观测误差已扩大以反映 epistemic uncertainty。")
    print()

    # 检查依赖
    print(f"U(1) 模型: {'已加载' if HAS_U1 else '未找到（使用默认先验）'}")
    print(f"Carrington Dst 模型: {'已加载' if HAS_CARR else '未找到（使用解析近似）'}")
    print()

    # 观测约束
    print("观测约束（1770年9月）:")
    for k, v in OBSERVATIONS_1770.items():
        print(f"  {k}: {v}")
    print()

    # 运行反演
    config = InversionConfig(
        n_samples=3000,
        burn_in=500,
        method='mcmc',
        use_u1_prior=HAS_U1,
        use_carrington_forward=HAS_CARR,
    )

    engine = InversionEngine(config)
    print(f"开始 MCMC 采样 ({config.n_samples} 样本, burn-in {config.burn_in})...")
    engine.run_mcmc()

    # 输出结果
    print()
    print("=" * 60)
    print("反演结果（后验统计量）")
    print("=" * 60)

    summary = engine.summarize()
    for key in ['v_cme_km_s', 'bz_imc_nT', 'v_sw_km_s', 'p_dyn_nPa', 'm_cme_g', 'n_cme']:
        stats = summary.get(key, {})
        label = {
            'v_cme_km_s': 'CME 速度 [km/s]',
            'bz_imc_nT': 'ICME Bz [nT]',
            'v_sw_km_s': '太阳风速度 [km/s]',
            'p_dyn_nPa': '动压 [nPa]',
            'm_cme_g': 'CME 质量 [g]',
            'n_cme': '多次CME次数',
        }.get(key, key)

        if key == 'n_cme':
            print(f"  {label}: 均值={stats.get('mean', '?'):.1f}, "
                  f"众数={int(stats.get('mode', 0))}")
        elif 'mean' in stats:
            print(f"  {label}:")
            print(f"    均值={stats['mean']:.1f}, 中位数={stats['median']:.1f}, "
                  f"std={stats['std']:.1f}")
            print(f"    95% CI: [{stats['ci_5']:.1f}, {stats['ci_95']:.1f}]")
        else:
            print(f"  {label}: {stats}")

    # 最佳拟合
    best = engine.best_fit()
    if best:
        print()
        print("最佳拟合参数:")
        sim = engine.forward.simulate_dst(best)
        print(f"  Dst_min (模拟) = {sim['dst_min']:.0f} nT, "
              f"观测 = {OBSERVATIONS_1770['dst_est']:.0f} nT")
        print(f"  极光南界 (模拟) = {sim['aurora_mlat']:.1f}°, "
              f"观测 = {OBSERVATIONS_1770['aurora_mlat_min']:.1f}°")

    print()
    return summary


if __name__ == '__main__':
    np.random.seed(1770)
    summary = demo_inversion()
