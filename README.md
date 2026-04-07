<div align="center">

# 💧 HydraRise

**程序员健康提醒助手**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-94E2D5?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-A6ADC8?style=flat-square)]()
[![Stars](https://img.shields.io/github/stars/Quell-sun/drink-warning?style=flat-square&color=FAB387)](https://github.com/Quell-sun/drink-warning/stargazers)

*在专注 coding 的同时，守护你的身体。*

</div>

---

## ✨ 特性一览

| 功能 | 说明 |
|------|------|
| 💧 **饮水提醒** | 按自定义间隔弹出提醒，结合体重自动计算每日饮水目标（体重 × 35 ml） |
| 🪑 **久坐提醒** | 持续坐超过设定时间后弹窗，支持一键记录活动、延后或静默 |
| ⚡ **微休息提示** | 每隔指定分钟在状态栏轻提醒，眼睛、肩颈、手腕一起照顾 |
| 🔀 **智能合并提醒** | 饮水与久坐同时到期时自动合并为一条提醒，减少打扰 |
| 📊 **BMI 计算** | 填写身高体重后实时计算 BMI 并给出分类说明 |
| 🕐 **工作时段感知** | 内置工作日时段表，非工作时间自动静默，不打扰休息 |
| 🎨 **暗黑 UI** | 极简暗黑风格，长时间使用不伤眼 |
| 💾 **本地持久化** | 配置与今日记录自动保存为 JSON，原子写入防止数据损坏 |

---

## 📸 界面预览

> *主窗口（1180 × 850）极简暗黑风格*

```
┌─────────────────────────────────────────────────────────┐
│  HydraRise                              程序员健康提醒助手│
├────────────────────┬────────────────────────────────────┤
│  基础信息          │  饮水设置      久坐设置             │
│  BMI / 饮水健康   │  今日健康进度                       │
│                    │  统计与操作 [记录] [重置] [退出]    │
├────────────────────┴────────────────────────────────────┤
│  状态：工作中 | 久坐：12 分 | 下次饮水：14:30 | 已饮水：500 ml │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python **3.10+**
- tkinter（Python 标准库，通常已内置；Linux 用户见下方说明）

### 安装

```bash
# 克隆仓库
git clone https://github.com/Quell-sun/drink-warning.git
cd drink-warning

# （可选）创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

> **Linux 用户**：如果 tkinter 缺失，请先安装：
> ```bash
> # Ubuntu / Debian
> sudo apt install python3-tk
> # Arch
> sudo pacman -S tk
> ```

### 运行

```bash
python main.py
```

首次运行会在同目录自动生成 `config.json` 和 `daily_record.json`。

---

## ⚙️ 配置说明

所有配置均可在 UI 中实时修改并保存，也可直接编辑 `config.json`：

```jsonc
{
  "weight_kg": 65,                    // 体重（kg），用于计算饮水目标
  "height_cm": 172,                   // 身高（cm），用于 BMI 计算
  "drink_remind_interval_min": 45,    // 饮水提醒间隔（分钟，最小 10）
  "drink_amount_ml": 250,             // 每次记录饮水量（ml）
  "sound_enabled": true,              // 弹窗时是否响铃
  "lunch_break_enabled": true,        // 午休免打扰
  "off_work_quiet_enabled": true,     // 下班后免打扰
  "enable_sit_reminder": true,        // 启用久坐提醒
  "sit_remind_interval_min": 30,      // 久坐提醒阈值（分钟，最小 10）
  "enable_micro_break": true,         // 启用微休息提示
  "micro_break_interval_min": 20      // 微休息间隔（分钟，最小 5）
}
```

### 工作时段

HydraRise 内置了默认工作时段，仅在此期间触发弹窗提醒：

| 星期 | 时段 |
|------|------|
| 周一、周二、周四 | 09:00–12:00 / 14:00–17:30 / 19:00–20:30 |
| 周三、周五 | 09:00–12:00 / 14:00–17:30 |
| 周六、周日 | 全天静默 |

> 如需自定义，修改 `main.py` 中 `ReminderEngine._PERIODS` 字典即可。

---

## 🏗️ 项目架构

```
drink-warning/
├── main.py              # 全部源码（单文件应用）
├── config.json          # 用户配置（自动生成）
├── daily_record.json    # 今日记录（自动生成，每日重置）
├── LICENSE
└── README.md
```

### 分层设计

```
┌──────────────────────────────────────────────────────┐
│  UI 层        HydraRiseApp (tkinter)                 │
│               弹窗 / 状态栏 / 进度显示               │
├──────────────────────────────────────────────────────┤
│  引擎层       ReminderEngine                         │
│               无状态纯函数逻辑，便于单元测试          │
├──────────────────────────────────────────────────────┤
│  数据层       ConfigManager  /  DailyRecord          │
│               JSON 持久化，原子写入                   │
└──────────────────────────────────────────────────────┘
```

---

## 🎮 使用说明

### 弹窗操作

**饮水提醒弹窗**

| 按钮 | 效果 |
|------|------|
| 我已喝水 | 记录本次饮水并重置提醒计时器 |
| 10分钟后提醒 | 延后提醒 10 分钟 |
| 本时段静默 | 当前工作时段不再弹窗 |
| 关闭 | 5 分钟后再次提醒 |

**久坐提醒弹窗**

| 按钮 | 效果 |
|------|------|
| 我已活动 | 记录活动并重置久坐计时器 |
| 1分钟后提醒 | 延后 1 分钟（适合"马上就起来"） |
| 10分钟后提醒 | 延后 10 分钟 |
| 本时段静默 | 当前工作时段不再弹窗 |

**综合提醒**：当饮水和久坐同时到期（相差 ≤5 分钟），自动合并为单一弹窗，一次操作两件事。

### 状态栏

底部状态栏每 30 秒刷新一次，显示：
- 当前工作状态 / 下一时段时间
- 当前久坐时长
- 下次饮水提醒时间
- 今日已饮水量
- 微休息次数

---

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！

```bash
# Fork 后克隆你的仓库
git clone https://github.com/<your-username>/drink-warning.git
cd drink-warning

# 新建分支
git checkout -b feat/your-feature

# 提交修改
git add .
git commit -m "feat: 添加 xxx 功能"
git push origin feat/your-feature

# 在 GitHub 上创建 Pull Request
```

### 贡献方向

- 🌍 多语言支持（英文界面）
- 🔔 系统原生通知（Windows Toast / macOS Notification Center）
- 📈 历史数据统计图表
- 🎵 自定义提醒音效
- 🪟 系统托盘图标支持

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源，欢迎自由使用和修改。

---

<div align="center">

Made with ❤️ for developers who forget to take care of themselves.

**[⭐ 给项目点个 Star](https://github.com/Quell-sun/drink-warning)** · **[🐛 提交 Issue](https://github.com/Quell-sun/drink-warning/issues)** · **[🔀 提交 PR](https://github.com/Quell-sun/drink-warning/pulls)**

</div>
