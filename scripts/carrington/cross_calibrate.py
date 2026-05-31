# -*- coding: utf-8 -*-
"""
跨事件交叉校准 — 用统一物理模型拟合三个现代事件

工作流:
  1. CME传播模型校准: 用观测的v0/v_arrival反推阻力参数α
  2. Dst注入效率校准: 用v_sw/Bz和观测Dst反推注入参数
  3. 事件间一致性检查: 同一α是否适用于所有事件
  4. 偏差分析: 模型预测 vs 观测, 系统误差方向

统一校准指标:
  - CME传播: α的最优值及其方差
  - Dst模型: 注入系数a的跨事件一致性
  - 残差: 模型Dst_min vs 实测Dst_min
"""

from .event_params import EVENTS, list_events
from .cme_propagation import CMETransitModel
from .dst_model import DstEvolutionModel, DstProfile


class EventFitter:
    """单个事件的参数拟合"""

    def __init__(self, event_name, event_data):
        self.name = event_name
        self.data = event_data

    def fit_cme_propagation(self, v_sw=400):
        """拟合CME传播: 从v0和v_arrival反推α"""
        model = CMETransitModel(v_sw)
        cme = self.data["cme"]

        # 双CME事件用主锤参数
        v0 = cme.get("v0_cme2_km_s", cme.get("v0_km_s"))
        va = cme.get("va_cme2_km_s", cme.get("va_km_s"))

        if v0 and va:
            return model.calibrate_alpha(v0, va, v_sw)
        return None

    def compute_verify_params(self):
        """计算验证参数"""
        storm = self.data["storm"]
        cme = self.data["cme"]

        # 1. 传播时间 vs 速度的关系
        v_avg = (cme.get("va_cme2_km_s", cme.get("va_km_s", 1000)) +
                 cme.get("v0_cme2_km_s", cme.get("v0_km_s", 1500))) / 2
        transit_h = cme.get("transit_cme2_h", cme.get("transit_h", 20))

        # 2. Dst / vBz 效率
        v = storm.get("v_sw_km_s", 500)
        bz = cme.get("bz_nT", -30)
        ey = -v * bz / 1000  # mV/m
        dst_min = storm["dst_min_nT"]

        return {
            "v_avg_km_s": round(v_avg, 0),
            "transit_h": transit_h,
            "ey_mv_m": round(ey, 2),
            "dst_per_ey": round(dst_min / ey, 1) if ey != 0 else 0,
            "dst_min_nT": dst_min,
        }

    def estimate_recovery_tau(self):
        """从事件数据估算恢复相时间常数"""
        storm = self.data["storm"]
        # 简单估计: 恢复相 ≈ 4τ
        if "power_outage_min" in storm and storm["power_outage_min"] > 0:
            # 如果停电时长已知, 作为恢复时间下限
            outage_h = storm["power_outage_min"] / 60
            return round(outage_h / 3, 1)
        return 5.0


class InterEventCalibrator:
    """跨事件校准器"""

    def __init__(self, events=None):
        self.events = events or ["1989_quebec", "2003_halloween", "2024_may"]
        self.results = {}

    def calibrate_all(self):
        """对所有选定事件执行全参数校准"""
        for key in self.events:
            if key not in EVENTS:
                continue
            event = EVENTS[key]
            fitter = EventFitter(key, event)

            alpha_result = fitter.fit_cme_propagation()
            verify = fitter.compute_verify_params()
            tau = fitter.estimate_recovery_tau()

            self.results[key] = {
                "name": event["name"],
                "alpha_fit": alpha_result,
                "verification": verify,
                "recovery_tau_h": tau,
            }

        # 一致性分析
        self.consistency_analysis()
        return self.results

    def consistency_analysis(self):
        """跨事件一致性分析: 同一物理参数在不同事件间是否一致?"""
        alphas = []
        ey_values = []
        dst_ey_ratios = []
        names = []

        for key, r in self.results.items():
            names.append(r["name"])
            if r.get("alpha_fit"):
                alphas.append(r["alpha_fit"]["alpha_optimal"])
            verify = r["verification"]
            ey_values.append(verify["ey_mv_m"])
            dst_ey_ratios.append(verify["dst_per_ey"])

        self.calibration_summary = {
            "alphas": alphas,
            "ey_values": ey_values,
            "dst_ey_ratios": dst_ey_ratios,
            "alpha_mean": round(sum(alphas) / len(alphas), 3) if alphas else None,
            "alpha_std": round(
                (sum((a - sum(alphas) / len(alphas)) ** 2 for a in alphas)
                 / len(alphas)) ** 0.5, 3
            ) if alphas else None,
        }
        return self.calibration_summary

    def print_summary(self):
        """打印完整的校准报告"""
        if not self.results:
            print("尚未执行校准。请先调用 calibrate_all()。")
            return

        print("=" * 72)
        print("  地磁风暴模型 — 跨事件交叉校准报告")
        print("=" * 72)

        # 1. 事件参数对比
        print("\n  ┌─ 事件参数对比")
        for key, r in self.results.items():
            ev = EVENTS[key]
            storm = ev["storm"]
            cme = ev["cme"]
            flare = ev["flare"]
            print(f"  │")
            print(f"  ├── {r['name']:40s} [{ev['g_level']:>5s}]")
            ver = r["verification"]
            print(f"  │  Dst_min={storm['dst_min_nT']:5d} nT | "
                  f"Bz={cme.get('bz_nT', 0):3d} nT | "
                  f"v_sw={storm.get('v_sw_km_s', 0):4d} km/s | "
                  f"Kp={storm['kp']:.1f}")
            print(f"  │  速度 v0={cme.get('v0_cme2_km_s', cme.get('v0_km_s',0)):.0f} → "
                  f"va={cme.get('va_cme2_km_s', cme.get('va_km_s',0)):.0f} km/s | "
                  f"t_transit={cme.get('transit_cme2_h', cme.get('transit_h',0)):.1f}h")
            if "耀斑" in r["name"] and "flare" in ev:
                pass

        # 2. CME传播模型校准
        print("\n  ┌─ CME 传播模型校准")
        print("  │  (阻力减速模型: d(v)/dr = -α·(v-v_sw)/r²)")
        for key, r in self.results.items():
            af = r.get("alpha_fit")
            if af:
                print(f"  │  {r['name']:30s} α={af['alpha_optimal']:.3f}  "
                      f"v0={af['v0_km_s']:.0f}→v={af['v_arrival_model']:.0f} "
                      f"(obs={af['v_arrival_obs']:.0f}) km/s")

        s = self.calibration_summary
        if s.get("alpha_mean"):
            print(f"  │")
            print(f"  ├── α 跨事件均值: {s['alpha_mean']:.3f} ± {s['alpha_std']:.3f}")

        # 3. Dst 注入效率
        print("\n  ┌─ Dst 注入效率 (Ey = -v·Bz)")
        print(f"  │  {'事件':>25s}  {'Ey(mV/m)':>10s}  {'Dst_min':>8s}  {'Dst/Ey':>8s}")
        for key, r in self.results.items():
            v = r["verification"]
            print(f"  │  {r['name']:>25s}  {v['ey_mv_m']:10.2f}  "
                  f"{v['dst_min_nT']:8d}  {v['dst_per_ey']:8.1f}")

        # 4. 恢复相时间
        print("\n  ┌─ 恢复相时间常数")
        for key, r in self.results.items():
            print(f"  │  {r['name']:30s} τ={r['recovery_tau_h']:.1f}h")

        print("\n  └" + "─" * 33)

    def predict_dst_min(self, v_km_s, bz_nT, t_hours=6.0):
        """用统一模型预测Dst最小"""
        dst = DstEvolutionModel()
        dst_star = 20.0  # 初始 Dst* (平静)
        for _ in range(int(t_hours / 0.25)):
            _, dst_star = dst.step(dst_star, v_km_s, bz_nT, dt_h=0.25)
        return round(dst_star, 1)


def report_all():
    """全量运行+报告"""
    print(f"\n  {'='*60}")
    print(f"  四大事件完整校准报告")
    print(f"  {'='*60}\n")

    list_events()

    calibrator = InterEventCalibrator()
    calibrator.calibrate_all()
    calibrator.print_summary()

    print("\n  Dst 最小预测 (统一模型, 6h主相):")
    for key in EVENTS:
        ev = EVENTS[key]
        v = ev["storm"]["v_sw_km_s"]
        bz = ev["cme"]["bz_nT"]
        pred = calibrator.predict_dst_min(v, bz, 6.0)
        obs = ev["storm"]["dst_min_nT"]
        err = pred - obs
        print(f"  {ev['name']:40s} pred={pred:5.1f} obs={obs:5d} 差={err:+.0f} nT")

    return calibrator


# --- 兼容性别名 (供 carrington/__init__.py 导入) ---
CrossCalibrator = InterEventCalibrator

