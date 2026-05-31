# -*- coding: utf-8 -*-
"""Dst指数演化模型 v2.0 — 升级版

核心方程:
  dDst*/dt = F(Ey_eff) - Dst*/tau(Dst*, v_sw)

升级 v2.0:
  1. Russell-McPherron偶极倾角修正
  2. 双时间尺度tau恢复
  3. 动压校正分离 (Dst*) 
  4. 注入饱和 (可选, 默认关闭)

参考:
  Burton+1975, O'Brien+McPherron 2000, 
  Russell-McPherron 1973, Shue+1998
"""

import math

# v2.0 升级参数
DST_PARAMS_V2 = {
    # --- Burton基础参数 ---
    "a": 4.4,                  # nT/(mV/m)/h
    "e_threshold": 0.5,        # mV/m, 注入阈值
    
    # --- 动压校正 ---
    "b": 15.8,                 # nT/nPa^(1/2)
    "c": 20.0,                 # nT
    
    # --- 双时间尺度tau (经验优化) ---
    "tau_fast": 1.5,           # h, 恢复初期 (快衰减)
    "tau_slow": 8.0,           # h, 恢复后期 (慢衰减)
    "tau_transition": -100,    # nT, tau过渡中点
    
    # --- 偶极倾角 (默认开启) ---
    "tilt_enabled": True,
    
    # --- 注入饱和 (默认关闭, 1859年数据不支持明显饱和) ---
    "saturation_enabled": False,
    "sat_ey_limit": 50,        # mV/m, 远高于典型风暴值
    
    # --- 自洽饱和: Dst越负, 注入效率递减 ---
    # 物理: 强环电流改变粒子漂移路径, 降低进一步注入
    "self_saturation": True,
    "sat_dst_half": 1200,     # nT, 注入减半时的Dst* (绝对值)
    "sat_steepness": 600,     # nT, 过渡宽度
    
    # --- Ey极盖电位饱和 (Siscoe-Hill, v2.1) ---
    "ey_saturation_enabled": True,   # 默认启用：极端事件需要
    "ey_sat_threshold": 20.0,        # mV/m, 饱和阈值
    "ey_sat_power": 0.5,             # 幂律衰减指数
    
    # --- 安全 ---
    "dst_min_clamp": -5000,
}


class DstEvolutionModelV2:
    """Dst指数演化模型 v2.0"""
    
    def __init__(self, params=None):
        self.p = {**DST_PARAMS_V2, **(params or {})}
        self._dipole_tilt = None
        self._pressure = None
        
    def inject_components(self, dipole_tilt, pressure):
        self._dipole_tilt = dipole_tilt
        self._pressure = pressure
    
    # ===== 1. 偶极倾角 =====
    
    def effective_ey(self, v_km_s, bz_nT, by_nT=5, doy=80, ut_hour=12):
        ey_raw = -v_km_s * bz_nT / 1000.0
        if ey_raw <= 0:
            return 0.0
        
        if self.p["tilt_enabled"]:
            if self._dipole_tilt is not None:
                eta = self._dipole_tilt.coupling_efficiency(bz_nT, by_nT)
                return ey_raw * eta
            
            # 内置简化版
            lam = (doy - 80) * 360.0 / 365.25
            seasonal = abs(math.sin(math.radians(lam)))
            sign = -1 if bz_nT * (by_nT or 5) < 0 else 0.5
            eta = 1.0 + seasonal * sign * 0.6
            eta = max(0.4, min(1.6, eta))
            return ey_raw * eta
        
        return ey_raw
    
    # ===== 2. 动压校正 =====
    
    def dcf(self, p_dyn_nPa):
        """磁层顶电流 [nT]"""
        if p_dyn_nPa <= 0:
            return -self.p["c"]
        return self.p["b"] * math.sqrt(p_dyn_nPa) - self.p["c"]
    
    def dst_star_to_obs(self, dst_star, p_dyn_nPa):
        """Dst* -> 观测Dst"""
        return dst_star + self.dcf(p_dyn_nPa)
    
    def obs_to_dst_star(self, dst_obs, p_dyn_nPa):
        """观测Dst -> Dst*"""
        return dst_obs - self.dcf(p_dyn_nPa)
    
    # ===== 3. 双时间尺度tau =====
    
    def tau_effective(self, dst_star, v_sw_km_s=400):
        """有效tau [h]
        
        物理: Dst*越负(环电流越强) -> 高能粒子比例高 -> 衰减慢(tau~8h)
              Dst*近零(环电流弱) -> 损失快(tau~1.5h)
              太阳风快 -> 对流增强 -> tau略减
        """
        # 平滑过渡: Dst*=-100时half-slow, Dst*=-400时fully-slow
        dst_norm = max(-500, min(0, dst_star))
        w_slow = 1.0 / (1.0 + math.exp((dst_norm - self.p["tau_transition"]) / 60))
        
        tau = self.p["tau_fast"] * (1 - w_slow) + self.p["tau_slow"] * w_slow
        
        # 太阳风速度修正 (弱)
        v_factor = 1.0 + 0.02 * ((v_sw_km_s - 400) / 100)
        v_factor = max(0.7, min(1.5, v_factor))
        
        return max(0.5, tau / v_factor)
    
    # ===== 4. 注入 =====
    
    def injection_rate(self, v_km_s, bz_nT, by_nT=5, doy=80, ut_hour=12, dst_star=0):
        """环电流注入率 [nT/h] (含自洽饱和 + 极盖电位饱和 v2.1)"""
        ey = self.effective_ey(v_km_s, bz_nT, by_nT, doy, ut_hour)
        
        if ey <= self.p["e_threshold"]:
            return 0.0
        
        # v2.1: 极盖电位饱和 — 极端Ey时耦合效率下降 (Siscoe-Hill)
        if self.p.get("ey_saturation_enabled", False) and ey > self.p.get("ey_sat_threshold", 20.0):
            a_eff = self.p["a"] * (self.p["ey_sat_threshold"] / ey) ** self.p.get("ey_sat_power", 0.5)
        else:
            a_eff = self.p["a"]
        
        injection = -a_eff * (ey - self.p["e_threshold"])
        
        # 自洽饱和: 强环电流改变粒子漂移路径, 降低注入
        if self.p["self_saturation"]:
            dst_abs = max(0, -dst_star)
            sat_factor = 1.0 / (1.0 + dst_abs / self.p["sat_dst_half"])
            injection *= sat_factor
        
        # 外源Ey饱和 (旧版, 默认关闭)
        if self.p["saturation_enabled"] and ey > self.p["sat_ey_limit"]:
            excess = ey - self.p["sat_ey_limit"]
            sat_factor = 1.0 / (1.0 + excess / 50.0)
            injection *= sat_factor
            
        return injection
    
    def decay_rate(self, dst_star, v_sw_km_s=400):
        tau = self.tau_effective(dst_star, v_sw_km_s)
        return dst_star / tau if tau > 0 else 0
    
    # ===== 5. 单步演化 =====
    
    def step(self, dst_star, v_km_s, bz_nT, by_nT=5,
             dt_h=0.5, p_dyn_nPa=2.0, doy=80, ut_hour=12,
             v_sw_km_s=None):
        if v_sw_km_s is None:
            v_sw_km_s = v_km_s
        
        finj = self.injection_rate(v_km_s, bz_nT, by_nT, doy, ut_hour, dst_star)
        fdec = self.decay_rate(dst_star, v_sw_km_s)
        ddt = finj - fdec
        
        dst_star_next = max(dst_star + ddt * dt_h, self.p["dst_min_clamp"])
        return ddt, dst_star_next
    
    # ===== 6. 完整风暴剖面 =====
    
    def simulate_profile(self, event_params, dt_h=0.25):
        """从参数dict生成完整Dst剖面
        
        event_params:
          v_sw: 太阳风速度 (km/s)
          bz:   Bz峰值 (nT)
          by:   By (nT)
          main_h: 主相持续 (h)
          p_dyn: 动压 (nPa)
          doy, ut_hour: 时间
          bz_persist: Bz持续系数 (0-1)
        """
        # 参数验证
        if not isinstance(event_params, dict):
            raise TypeError(f'event_params must be dict, got {type(event_params).__name__}')
        dt_h = max(0.01, min(24.0, float(dt_h)))
        
        p = event_params
        v = float(p.get('v_sw', 800))
        if v < 100 or v > 10000:
            v = 800.0  # 不合理速度回落默认值
        bz = float(p.get('bz', -30))
        by = float(p.get('by', 5))
        main_h = float(p.get('main_h', 6))
        p_dyn = float(p.get('p_dyn', 2.0))
        doy = int(p.get('doy', 80))
        ut = float(p.get('ut_hour', 12))
        persist = float(p.get('bz_persist', 0.7))
        
        dst_star = 0
        profile = []
        
        # 主相
        n_main = int(main_h / dt_h)
        bz_eff = bz * (0.5 + 0.5 * persist)
        
        for i in range(n_main):
            ramp = min(1.0, i / max(1, n_main * 0.3))
            bz_t = bz_eff * ramp
            ddt, dst_star = self.step(dst_star, v, bz_t, by, dt_h, p_dyn, doy, ut, v)
            profile.append({
                't_h': i * dt_h, 'dst_star': round(dst_star, 1),
                'dst_obs': round(self.dst_star_to_obs(dst_star, p_dyn), 1),
                'bz': round(bz_t, 1), 'tau': round(self.tau_effective(dst_star, v), 2),
            })
        
        dst_min = min(dst_star, 0)
        
        # 恢复相
        n_rec = int(24 / dt_h)
        for i in range(n_rec):
            bz_t = 2  # 近零Bz
            v_rec = v * 0.6
            ddt, dst_star = self.step(dst_star, v_rec, bz_t, by, dt_h, p_dyn*0.5, doy, ut+0.1*i, v_rec)
            profile.append({
                't_h': (n_main + i) * dt_h, 'dst_star': round(dst_star, 1),
                'dst_obs': round(self.dst_star_to_obs(dst_star, p_dyn*0.5), 1),
                'bz': round(bz_t, 1), 'tau': round(self.tau_effective(dst_star, v_rec), 2),
            })
        
        return {'profile': profile, 'dst_min': round(dst_min, 1), 'dst_obs_min': round(self.dst_star_to_obs(dst_min, p_dyn), 1)}
    
    def summary(self, v=800, bz=-50, by=5, doy=80, ut=12):
        ey_raw = -v * bz / 1000
        ey_eff = self.effective_ey(v, bz, by, doy, ut)
        return {
            'ey_raw_mv_m': round(ey_raw, 1),
            'ey_eff_mv_m': round(ey_eff, 1),
            'tilt_factor': round(ey_eff / max(0.01, ey_raw), 2),
            'tau_fast_h': self.p['tau_fast'],
            'tau_slow_h': self.p['tau_slow'],
            'saturation': self.p['saturation_enabled'],
        }
