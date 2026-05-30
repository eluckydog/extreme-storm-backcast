# -*- coding: utf-8 -*-
"""
CME 传播模型 — 日球层运动学

模型:
  - 阻力减速: d(v)/dr = -α * (v - v_sw) / r² (Gopalswamy 2001)
  - 激波到达时间: t = ∫ dr/v(r) 从 Sun 到 1 AU
  - 减速参数 α 可调, 用各事件观测值校准

输入: 初始速度 v0, 太阳风速 v_sw (默认 400 km/s)
输出: 到达速度 v_arrival, 传播时间, 减速因子
"""

import math


class CMETransitModel:
    """CME 日球层传播模型
    
    使用 Gopalswamy 阻力减速模型:
      d(v)/dr = -α * (v - v_sw) / r²
      
    其中 α = 减速参数 (可调), v_sw = 太阳风速度
    r 从 R_sun 到 1 AU (归一化)
    """

    def __init__(self, v_sw_km_s=400.0):
        self.v_sw = v_sw_km_s
        self.r_sun_au = 0.00465    # 1 R_sun in AU
        self.r_earth_au = 1.0       # 1 AU

    def propagate_numeric(self, v0_km_s, alpha=0.5, n_steps=1000):
        """数值积分 CME 从日表到地球的传播
        
        参数:
          v0_km_s: CME 初始速度 (km/s)
          alpha:   减速参数 (0 = 无减速, ~1 = 强减速)
          n_steps: 积分步数
          
        返回:
          dict: {v_arrival, transit_hours, speed_at_r, r_at_step}
        """
        r_step = (self.r_earth_au - self.r_sun_au) / n_steps
        v = v0_km_s
        t = 0.0  # 总时间 (s)
        traj = {"r": [], "v": []}

        for i in range(n_steps):
            r = self.r_sun_au + i * r_step
            if v > self.v_sw:
                dv = -alpha * (v - self.v_sw) / (r * 1e3) * r_step
                # r 归一化 ~1, 所以除 1e3 控制减速量级
            else:
                dv = 0.0

            v += dv * (r_step / (v / (self.r_earth_au * 1.5e8 / 86400)))  # 时间修正
            # 简化: dt = dr / v (单位一致化)
            dt_s = r_step * 1.5e8 / v  # r_step[AU] -> dr[m] -> dt = dr/v [s]
            t += dt_s

            if i % (n_steps // 10) == 0:
                traj["r"].append(r)
                traj["v"].append(v)

        transit_h = t / 3600.0
        return {
            "v_arrival_km_s": v,
            "transit_hours": transit_h,
            "trajectory": traj,
        }

    def propagate_analytic(self, v0_km_s, alpha=0.5):
        """解析近似: CME 到达速度 (Gopalswamy 2001 经验公式)
        
        v_arrival ≈ v_sw + (v0 - v_sw) / (1 + α * (v0 - v_sw) * ln(r_e/r_s))
        
        这个更稳定, 推荐用于批量校准
        """
        dv = v0_km_s - self.v_sw
        if dv <= 0:
            return v0_km_s

        ln_ratio = math.log(self.r_earth_au / self.r_sun_au)
        v_arrival = self.v_sw + dv / (1 + alpha * dv * ln_ratio * 1e-4)

        # 传播时间: 积分 ≈ distance / average_speed
        avg_v = (v0_km_s + v_arrival) / 2
        distance_m = (self.r_earth_au - self.r_sun_au) * 1.495978707e11
        transit_h = distance_m / (avg_v * 1000) / 3600

        return {
            "v0_km_s": v0_km_s,
            "v_arrival_km_s": v_arrival,
            "transit_hours": transit_h,
            "alpha": alpha,
            "v_sw_km_s": self.v_sw,
        }

    def calibrate_alpha(self, v0_km_s, v_arrival_obs, v_sw=400.0):
        """从观测的 v0 和 v_arrival 反推最优 alpha
        
        用二分法找到使 v_model ≈ v_obs 的 alpha
        """
        lo, hi = 0.0, 20.0
        for _ in range(50):
            mid = (lo + hi) / 2
            res = self.propagate_analytic(v0_km_s, mid)
            err = res["v_arrival_km_s"] - v_arrival_obs
            if abs(err) < 0.1:
                break
            if err > 0:
                lo = mid
            else:
                hi = mid
        return {
            "alpha_optimal": mid,
            "v0_km_s": v0_km_s,
            "v_arrival_model": res["v_arrival_km_s"],
            "v_arrival_obs": v_arrival_obs,
            "transit_hours": res["transit_hours"],
        }

    def drag_parameter(self, v0_km_s, transit_h_obs):
        """从传播时间反推等效阻力参数"""
        v_arr = self.propagate_analytic(v0_km_s, 1.0)
        # 归一化偏差
        ratio = transit_h_obs / v_arr["transit_hours"]
        return ratio

    @staticmethod
    def classify_speed(v_km_s):
        """速度分级"""
        if v_km_s >= 2000:
            return "极端快"
        elif v_km_s >= 1500:
            return "非常快"
        elif v_km_s >= 1000:
            return "快速"
        elif v_km_s >= 500:
            return "中速"
        else:
            return "慢速"


class ICMEShockModel:
    """ICME 激波参数模型
    
    给定 CME 速度, 估算激波压缩比和下游参数
    """

    def __init__(self):
        self.gamma = 5.0 / 3.0  # 绝热指数 (单原子等离子体)

    def shock_compression(self, v_cme_km_s, v_sw=400.0, cs=50.0):
        """Rankine-Hugoniot 激波压缩比
        
        M_A = (v_cme - v_sw) / v_A  (Alfvén Mach 数)
        """
        v_shock = v_cme_km_s - v_sw
        if v_shock <= 0:
            return {"compression": 1.0, "mach": 0}

        # 典型 Alfvén 速度 ~50 km/s (日球层1AU)
        v_a = 50.0 if v_sw < 500 else 40.0
        m_a = v_shock / v_a

        # 垂直激波压缩比 (RH 关系)
        r = (self.gamma + 1) * m_a**2 / ((self.gamma - 1) * m_a**2 + 2)
        r = max(1.0, min(r, 4.0))  # 非相对论激波压缩比 ≤4

        b_enhance = r  # 磁场按激波压缩比增强

        return {
            "mach_alfven": round(m_a, 1),
            "compression_ratio": round(r, 3),
            "b_field_enhancement": round(b_enhance, 2),
            "v_shock_frame": round(v_shock, 1),
        }
