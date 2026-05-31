# -*- coding: utf-8 -*-
"""
1989 Quebec / 2003 Halloween / 2024 May / 1859 Carrington 事件参数集

所有时间均为 UTC，来源见各事件尾部注释。
双CME事件: CME-1=清道夫, CME-2=主锤 (最后给出的是主锤/主风暴参数)
"""

from datetime import datetime

EVENTS = {
    "1989_quebec": {
        "name": "1989 Quebec Blackout",
        "g_level": "G5",
        "flare": {
            "class_cme1": "X4.5/3B",
            "class_cme2": "M7.3/2B",
            "time_cme1": datetime(1989, 3, 10, 19, 0, 0),   # X4.5
            "time_cme2": datetime(1989, 3, 12, 22, 0, 0),   # M7.3
            "region": "AR 5395",
            "pos": "S31, L275",
        },
        "cme": {
            "v0_cme1_km_s": 1200,      # 初始速度估计
            "va_cme1_km_s": 550,        # 到达速度 (Cliver 1990)
            "transit_cme1_h": 54.8,     # ~54.8h (22:00 Mar 10 → 01:28 Mar 13)
            "v0_cme2_km_s": 1500,
            "va_cme2_km_s": 960,        # 到达速度 (Nagatsuma 2015)
            "transit_cme2_h": 8.8,      # ~8.8h (or 34h 假设前CME已清路)
            "mass_kg": 5e12,
            "bz_nT": -50,
        },
        "storm": {
            "ssc1": datetime(1989, 3, 13, 1, 28, 0),
            "ssc2": datetime(1989, 3, 13, 7, 47, 0),
            "main_phase_start": datetime(1989, 3, 13, 20, 0, 0),
            "dst_min_nT": -589,
            "dst_min_time": datetime(1989, 3, 14, 2, 0, 0),
            "kp": 9.0,
            "aurora_lat": 30,
            "v_sw_km_s": 960,
            "power_outage_min": 540,    # 9小时
        },
        "double_cme": True,
        "notes": "Boteler 2019: 'first CME cleared a path for the second'",
        "sources": "Nagatsuma 2015, Boteler 2019, Cliver 1990",
    },

    "2003_halloween": {
        "name": "2003 Halloween Storms",
        "g_level": "G5",
        "flare": {
            "class_cme1": "X17.2/4B",
            "class_cme2": "X10.0",
            "time_cme1": datetime(2003, 10, 28, 11, 0, 0),
            "time_cme2": datetime(2003, 10, 29, 20, 37, 0),
            "region": "AR 10486",
            "pos": "S16, L283",
        },
        "cme": {
            "v0_cme1_km_s": 2125,       # LASCO 直接测量
            "va_cme1_km_s": 1800,       # ACE 测量 (减速不大)
            "transit_cme1_h": 19.0,     # LASCO →
            "v0_cme2_km_s": 2020,
            "va_cme2_km_s": 1900,
            "transit_cme2_h": 19.4,
            "mass_kg": 1e13,
            "bz_nT": -50,
        },
        "storm": {
            "ssc1": datetime(2003, 10, 29, 6, 0, 0),
            "ssc2": datetime(2003, 10, 30, 16, 0, 0),
            "dst1_nT": -353,
            "dst1_time": datetime(2003, 10, 29, 23, 0, 0),
            "dst_min_nT": -401,
            "dst_min_time": datetime(2003, 10, 30, 22, 0, 0),
            "kp": 9.0,
            "aurora_lat": 30,
            "v_sw_km_s": 1900,
            "power_outage_min": 60,     # 瑞典1h
        },
        "double_cme": True,
        "notes": "史上最强X级耀斑序列; ACE/SOHO完整记录",
        "sources": "Doherty 2004, Gopalswamy 2005, NOAA/SGD",
    },

    "2024_may": {
        "name": "2024 May Super Storm",
        "g_level": "G5",
        "flare": {
            "class_cme1": "X1.0",
            "class_cme2": "X2.2",
            "class_cme3": "X1.1",
            "time_cme1": datetime(2024, 5, 8, 5, 0, 0),
            "time_cme2": datetime(2024, 5, 9, 9, 0, 0),
            "time_cme3": datetime(2024, 5, 9, 17, 0, 0),
            "region": "AR 3664",
            "pos": "S20, L0 (日面中心)",
        },
        "cme": {
            "v0_cme1_km_s": 1500,       # LASCO
            "va_cme1_km_s": 800,        # DSCOVR
            "transit_cme1_h": 59.5,     # May 8 05:00 → May 10 16:30
            "v0_cme2_km_s": 2100,
            "va_cme2_km_s": 1000,
            "transit_cme2_h": 32.0,     # May 9 09:00 → May 10 17:00
            "v0_cme3_km_s": 1300,
            "va_cme3_km_s": 900,
            "transit_cme3_h": 30.0,     # May 9 17:00 → May 10 23:00
            "mass_kg": 3e12,
            "bz_nT": -30,
        },
        "storm": {
            "ssc1": datetime(2024, 5, 10, 16, 30, 0),
            "ssc2": datetime(2024, 5, 10, 17, 0, 0),
            "dst_min_nT": -412,
            "dst_min_time": datetime(2024, 5, 11, 2, 0, 0),
            "kp": 9.0,
            "aurora_lat": 25,
            "v_sw_km_s": 1000,
            "power_outage_min": 0,
        },
        "double_cme": True,
        "notes": "与1989同机制: CME-2(2100km/s)追上CME-1(1500km/s)叠加",
        "sources": "NOAA SWPC real-time, DSCOVR, SOHO LASCO",
    },

    "1859_carrington": {
        "name": "1859 Carrington Event",
        "g_level": "G5+ (超G5)",
        "flare": {
            "class": "X45±5 (估算)",
            "time": datetime(1859, 9, 1, 11, 15, 0),
            "region": "AR 1490 (现代编号)",
            "pos": "N20, L146",
        },
        "cme": {
            "v0_km_s": 2800,
            "va_km_s": 2360,            # Tsurutani 2003
            "transit_h": 17.6,          # 11:15→05:00
            "mass_kg": 1e13,
            "bz_nT": -80,
        },
        "storm": {
            "ssc": datetime(1859, 9, 2, 5, 0, 0),  # ±30min
            "dst_min_nT": -1600,
            "dst_min_time": datetime(1859, 9, 2, 8, 30, 0),
            "kp": 9.5,
            "aurora_lat": 20,
            "v_sw_km_s": 2360,
            "power_outage_min": 0,
        },
        "double_cme": True,
        "notes": "轨道反推: 耀斑在日面东侧边缘~74°; 到达±30min",
        "sources": "Tsurutani 2003, Cliver 2005, Smart & Shea 2005",
    },

    "2000_bastille": {
        "name": "2000 Bastille Day Storm",
        "g_level": "G5",
        "flare": {"class": "X5.7/3B", "time": datetime(2000,7,14,10,3,0), "region": "AR 9077", "pos": "N22,W05"},
        "cme": {"v0_km_s": 1674, "va_km_s": 1000, "transit_h": 28.5, "mass_kg": 1e13, "bz_nT": -50},
        "storm": {"dst_min_nT": -300, "kp": 9.0, "v_sw_km_s": 1000},
        "notes": "Cycle 23 first G5; ACE/SOHO/GOES full record",
    },
    "2001_april": {
        "name": "2001 April X14 Storm",
        "g_level": "G5",
        "flare": {"class": "X14/2B", "time": datetime(2001,4,21,1,41,0), "region": "AR 9415"},
        "cme": {"v0_km_s": 2100, "va_km_s": 1400, "transit_h": 21.0, "mass_kg": 8e12, "bz_nT": -40},
        "storm": {"dst_min_nT": -271, "kp": 9.0, "v_sw_km_s": 1400},
    },
    "2015_patrick": {
        "name": "2015 St Patrick Day Storm",
        "g_level": "G4",
        "flare": {"class": "C9.1", "time": datetime(2015,3,15,2,0,0), "region": "AR 2297"},
        "cme": {"v0_km_s": 850, "va_km_s": 700, "transit_h": 45.0, "mass_kg": 3e12, "bz_nT": -25},
        "storm": {"dst_min_nT": -223, "kp": 8.0, "v_sw_km_s": 700},
        "notes": "Cycle 24 strongest; sustained Bz 6h",
    },
    "2017_september": {
        "name": "2017 Sep X9.3 Storm",
        "g_level": "G4",
        "flare": {"class": "X9.3/2B", "time": datetime(2017,9,6,14,36,0), "region": "AR 12673"},
        "cme": {"v0_km_s": 1400, "va_km_s": 800, "transit_h": 33.0, "mass_kg": 5e12, "bz_nT": -20},
        "storm": {"dst_min_nT": -124, "kp": 8.0, "v_sw_km_s": 800},
        "notes": "Cy24 largest flare but Bz southward <2h",
    },
    "1972_august": {
        "name": "1972 Aug Fastest CME",
        "g_level": "G5",
        "flare": {"class": "X-class", "time": datetime(1972,8,4,6,0,0), "region": "AR 11976/11979"},
        "cme": {"v0_km_s": 10000, "va_km_s": 2500, "transit_h": 14.6, "mass_kg": 1e13, "bz_nT": -30},
        "storm": {"dst_min_nT": -168, "kp": 9.0, "v_sw_km_s": 2000},
        "notes": "Fastest solar transit ever recorded 14.6h; IMP-5/6 + Pioneer 9",
    },
}


def get_event(name):
    """按名称获取事件 (支持简写)"""
    for key, data in EVENTS.items():
        if name.lower() in key.lower() or name.lower() in data["name"].lower():
            return data
    return None


def list_events():
    """列出所有事件"""
    for key, data in EVENTS.items():
        cme = data["cme"]
        storm = data["storm"]
        print(f"  {key:25s} | Dst={storm['dst_min_nT']:5d} | "
              f"v={cme.get('va_km_s', cme.get('va_cme2_km_s', 0)):4d} km/s | "
              f"Bz={cme['bz_nT']:3d} nT | {data['g_level']:5s}")


# --- 兼容性别名 (供 carrington/__init__.py 导入) ---
EVENT_PARAMS = EVENTS
get_event_params = get_event

