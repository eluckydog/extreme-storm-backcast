"""
轨道计算器物理常数 v1.0 — 集中管理所有物理常数
来源: NIST 2018 / IAU 2012-2015 / NASA Planetary Fact Sheet

使用方式:
    from src.constants import G, AU, M_SUN, ...
"""

# 基础物理常数
G = 6.67430e-11          # m^3 kg^-1 s^-2 (NIST 2018)
AU = 1.495978707e11      # m (IAU 2012)
C = 299792458             # m/s (精确)
M_SUN = 1.9885e30         # kg, 太阳质量 (IAU 2015)
M_EARTH = 5.9722e24       # kg, 地球质量 (NASA)
R_SUN = 6.957e8           # m, 太阳赤道半径 (IAU 2015)
R_EARTH = 6378137.0       # m, 地球赤道半径 (WGS84)

# 时间常数
DAY_S = 86400.0           # s
YEAR_S = 365.256363 * DAY_S  # s, 恒星年 (J2000)
YEAR_S_SIMPLE = 365.25 * DAY_S  # s, 简化年

# 天文学常数
LY = 9.4607304725808e15   # m, 光年
PC = 3.085677581e16       # m, 秒差距
AU_KM = 1.495978707e8     # km
