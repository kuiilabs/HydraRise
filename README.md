# HydraRise

> 程序员健康提醒助手（Hydration + Posture + Micro-break）

HydraRise 是一个基于 **Python 3.10+** 和 **tkinter** 的桌面健康提醒工具，面向长时间编程/办公人群，帮助你建立稳定的喝水、起身活动和微休息节奏。

## ✨ 核心特点

- **分层架构清晰**：
  - 数据层：`ConfigManager` / `DailyRecord`
  - 引擎层：`ReminderEngine`
  - UI 层：`HydraRiseApp`
- **智能提醒策略**：支持饮水、久坐、微休息、综合提醒（同一时刻合并弹窗）。
- **工作时段控制**：仅在预设工作时段内提醒，并自动避免“时段即将结束”场景。
- **免打扰机制**：支持“本时段静默”与 “snooze 延后提醒”。
- **每日健康可视化**：展示饮水进度、久坐时长、风险等级、BMI 与推荐饮水量。
- **本地持久化**：配置与每日记录以 JSON 方式落盘，零依赖数据库。

## 🧱 项目结构

```text
HydraRise/
├── hydrarise.py      # 主程序（数据层/引擎层/UI 层）
├── README.md
└── LICENSE
```

## 🚀 快速开始

### 1) 环境要求

- Python >= 3.10
- 操作系统：Windows / macOS / Linux（需支持 tkinter）

### 2) 运行

```bash
python hydrarise.py
```

如果你在服务器/容器环境（无图形界面）验证逻辑，可运行：

```bash
python hydrarise.py --dry-run
```

首次运行会自动生成：

- `config.json`：用户配置
- `daily_record.json`：当日健康记录

## ⚙️ 主要功能说明

- **饮水提醒**：按配置间隔触发，支持记录喝水、延后提醒、时段静默。
- **久坐提醒**：检测连续坐姿时长，达到阈值后提醒起身活动。
- **微休息提醒**：以轻提醒方式更新状态栏，避免频繁打断。
- **风险评估**：根据当前连续久坐时长给出低/中/高风险。

## 🏗️ 架构设计

### 数据层
- `ConfigManager`：配置读取、更新与持久化。
- `DailyRecord`：每日数据（喝水量、久坐、微休息等）维护。

### 引擎层
- `ReminderEngine`：无状态提醒判断逻辑，便于单元测试与扩展。

### UI 层
- `HydraRiseApp`：界面渲染、用户交互、状态刷新与调度。

## 🧪 开发与质量

建议在本地执行：

```bash
python -m py_compile hydrarise.py
python -m unittest discover -s tests
```

如需进一步工程化，可增加：

- 单元测试（`pytest`）
- 静态检查（`ruff` / `mypy`）
- CI（GitHub Actions）

## 🗺️ Roadmap

- [ ] 拆分为 `src/` 多模块结构
- [ ] 增加单元测试覆盖提醒引擎核心逻辑
- [ ] 增加托盘运行与系统通知
- [ ] 增加多语言支持（中文 / English）
- [ ] 提供可配置的工作日程编辑器

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/xxx`
3. 提交修改：`git commit -m "feat: ..."`
4. 推送分支并发起 Pull Request

欢迎提交 issue、需求建议和 PR。

## 📄 License

本项目采用仓库中的 `LICENSE`。
