# Carrington Space Engine — Core Package
"""A pluggable space weather engine calibrated by the 1859 Carrington event."""

__version__ = "1.0.0"

# Lazy / fault-tolerant imports — 任何子模块缺失都不阻断整个包加载
# 使用方（如 inversion_1770.py）只用到 DstEvolutionModelV2，
# 其他组件可选。

_import_errors = []

def _safe_import(module, names, package=None):
    """尝试导入，失败则记录并返回 None"""
    global _import_errors
    try:
        from importlib import import_module
        mod = import_module(f".{module}", __package__)
        results = []
        for name in names:
            if hasattr(mod, name):
                results.append(getattr(mod, name))
            else:
                _import_errors.append(f"{module}: missing {name}")
                results.append(None)
        return tuple(results) if len(names) > 1 else results[0]
    except Exception as e:
        _import_errors.append(f"{module}: {e}")
        return (None,) * len(names) if len(names) > 1 else None


# 核心：DstEvolutionModelV2（必须成功，否则整个包无意义）
try:
    from .dst_model_v2 import DstEvolutionModelV2
    from .dst_model_v2 import DST_PARAMS_V2
except Exception as e:
    _import_errors.append(f"dst_model_v2: {e}")
    DstEvolutionModelV2 = None
    DST_PARAMS_V2 = None

# 兼容层：dst_model.py 可能不存在，用 dst_model_v2 代替
DstV2 = DstEvolutionModelV2

# 可选组件（失败不影响核心功能）
EVENT_PARAMS, get_event_params = _safe_import(
    "event_params", ["EVENT_PARAMS", "get_event_params"]
)
if EVENT_PARAMS is None:
    # 尝试用 EVENTS 兼容
    try:
        from .event_params import EVENTS
        EVENT_PARAMS = EVENTS
    except Exception:
        pass

CrossCalibrator = _safe_import("cross_calibrate", ["CrossCalibrator"])
if CrossCalibrator is None:
    # 尝试用 InterEventCalibrator 兼容
    try:
        from .cross_calibrate import InterEventCalibrator
        CrossCalibrator = InterEventCalibrator
    except Exception:
        pass

CMEPropagation = _safe_import("cme_propagation", ["CMEPropagation"])
if CMEPropagation is None:
    try:
        from .cme_propagation import CMETransitModel
        CMEPropagation = CMETransitModel
    except Exception:
        pass

# earth_environ 子包（全部可选）
DipoleTilt = None
PressureCorrection = None
Atmosphere = None
PluggableEngine = None

try:
    from .earth_environ.dipole_tilt import DipoleTilt
except Exception as e:
    _import_errors.append(f"dipole_tilt: {e}")

try:
    from .earth_environ.pressure_correction import PressureCorrection
except Exception as e:
    _import_errors.append(f"pressure_correction: {e}")

try:
    from .earth_environ.atmosphere import SimpleAtmosphere as Atmosphere
except Exception as e:
    _import_errors.append(f"atmosphere: {e}")

try:
    from .earth_environ.pluggable_engine import PluggableEngine
except Exception as e:
    _import_errors.append(f"pluggable_engine: {e}")

# 导出列表
__all__ = [
    "DstEvolutionModelV2",
    "DstV2",
    "EVENT_PARAMS",
    "get_event_params",
    "CrossCalibrator",
    "CMEPropagation",
    "DipoleTilt",
    "PressureCorrection",
    "Atmosphere",
    "PluggableEngine",
]

# 启动时报错摘要（仅打印警告，不崩溃）
if _import_errors:
    import sys
    print(f"[Carrington] {len(_import_errors)} sub-module(s) failed to import:", file=sys.stderr)
    for _err in _import_errors[:5]:
        print(f"  [warn] {_err}", file=sys.stderr)
    if len(_import_errors) > 5:
        print(f"  [... and {len(_import_errors)-5} more]", file=sys.stderr)
