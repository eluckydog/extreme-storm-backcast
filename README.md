# Extreme Storm Backcast

> 一键安装即为 Skill：clone 到 `~/.qclaw/skills/`，说句触发词就能用。

## 安装为 Skill

```bash
git clone https://github.com/eluckydog/extreme-storm-backcast.git ~/.qclaw/skills/extreme-storm-backcast
```

重启 OpenClaw 会话，说以下任意触发词，Skill 自动加载：

> 「分析 1770 年极端地磁暴」「U(1) 相位风险」「Dst 模拟 Carrington」「MCMC 反演」

## 这是什么

两套独立模型联合回溯极端地磁暴：

- **U(1) 太阳模型 v4.0**：相位风险评估，双窗口（W1 黑子峰 + W2 Gnevyshev 磁暴峰），11 个历史事件命中率 **72.7%**
- **Carrington 空间引擎 v2.1**：Dst 环电流演化，Ey 极盖电位饱和（Siscoe-Hill），正向模拟 + MCMC 反演
- **1770 事件联合回测**：U(1) 判定 W1 HIGH → Carrington 正向 Dst=-884 nT → MCMC 反演 Dst=-1001 nT

## 仓库结构 (Skill 格式)

```
extreme-storm-backcast/
├── SKILL.md                        ← Skill 入口（OpenClaw 自动加载）
├── README.md                       ← 本文件
├── scripts/
│   ├── u1_solar_model_v4.py        ← U(1) 太阳模型 v4.0
│   ├── inversion_1770.py           ← 1770 MCMC 反演
│   ├── simulate_1770_v4.py         ← 联合正向模拟
│   ├── carrington/                 ← Carrington 空间引擎
│   │   ├── __init__.py
│   │   └── dst_model_v2.py         ← Dst 演化 (Ey 饱和)
│   └── tests/
│       └── test_dst_v21.py         ← 23 项测试
└── references/
    └── audit-report_2026-05-28.md  ← 三级审计报告
```

## 核心发现

- 磁暴相位呈**双峰分布**：CME 驱动峰 (~150°) + CIR/SIR Gnevyshev 峰 (~222°)
- 单窗口命中率天花板 45-55%（受物理本质限制）
- Ey 极盖电位饱和是模拟 Dst < -750 nT 事件的必要条件
- 1770 事件 U(1) 相位 185.7°（W1），与三条独立观测约束一致

## 验证

- ✅ 23/23 测试通过
- ✅ 三级审计通过（门下省 K3 + 专业红队 T3-A + 工程化AI B+）
- ✅ 334,123 耀斑事件验证（1986-2020，3 个太阳周期）

## 关键文件路径

| 脚本 | 功能 |
|------|------|
| `scripts/u1_solar_model_v4.py` | U(1) 相位模型（双窗口、Poisson、MCMC） |
| `scripts/carrington/dst_model_v2.py` | Dst 演化（Ey 饱和、Siscoe-Hill） |
| `scripts/inversion_1770.py` | 1770 贝叶斯反演（MCMC + U(1) 先验） |
| `scripts/simulate_1770_v4.py` | 联合正向模拟（U1 → Carrington） |

## 关联仓库

- [u1-solar-modeling](https://github.com/eluckydog/u1-solar-modeling) — U(1) 太阳模型 + 35 年耀斑数据
- [Carrington-Space-Engine](https://github.com/eluckydog/Carrington-Space-Engine) — Dst 环电流模型

## 参考文献

- Kataoka & Hayakawa 2017: 1770 年 Dst 推估 ~-1100 nT
- Hayakawa 2017: 太阳黑子面积 ~6000 millionths
- Siscoe-Hill: 极盖电位饱和 (Φ_PC ≤ 200 kV)
- Burton-McPherron-Russell: Dst 环电流方程

## License

MIT
