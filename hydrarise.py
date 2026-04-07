from __future__ import annotations

import json
import logging
import math
import random
import tkinter as tk
from datetime import date, datetime, time, timedelta
from pathlib import Path
from tkinter import messagebox, ttk

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("hydrarise")

# ---------------- Paths ----------------
CONFIG_PATH = Path("config.json")
DAILY_RECORD_PATH = Path("daily_record.json")

# ---------------- Theme ----------------
_C = {
    "bg": "#1E1E2E",
    "fg": "#CDD6F4",
    "sub_fg": "#A6ADC8",
    "card_bg": "#2A2A3C",
    "accent": "#94E2D5",
    "accent_hover": "#A6F3E6",
    "btn_bg": "#313244",
    "border": "#45475A",
    "risk_high": "#F38BA8",
    "risk_mid": "#FAB387",
}

DEFAULT_CONFIG: dict = {
    "weight_kg": 60,
    "height_cm": 170,
    "gender": "",
    "age": "",
    "drink_remind_interval_min": 45,
    "drink_amount_ml": 250,
    "sound_enabled": True,
    "lunch_break_enabled": True,
    "off_work_quiet_enabled": True,
    "micro_break_interval_min": 20,
    "sit_remind_interval_min": 30,
    "sit_activity_duration_min": 3,
    "sit_escalation_interval_min": 60,
    "enable_sit_reminder": True,
    "enable_micro_break": True,
}

_DRINK_MSGS = [
    "该喝点水啦，休息一下会更舒服。",
    "补充一点水分，继续保持好状态。",
    "今天也别忘了规律喝水哦。",
    "忙的时候更容易忘记喝水，现在补一点吧。",
    "喝口水，顺便放松一下肩膀。",
]
_SIT_MSGS = [
    "你已经坐了一会儿了，起来活动 2 分钟吧。",
    "该站起来走走了，接杯水也不错。",
    "久坐太久身体会抗议，起来伸展一下吧。",
    "站起来活动一下，肩颈和腰背会舒服很多。",
    "看代码很投入，也别忘了让身体换个姿势。",
]
_COMBINED_MSGS = [
    "该起来活动一下了，顺便喝点水吧。",
    "你已经坐了一段时间了，建议站起来走走并补充一点水分。",
    "活动一下肩颈，顺便接杯水，状态会更好。",
]
_MICRO_MSGS = [
    "抬头看看远处 20 秒，让眼睛休息一下。",
    "放松一下肩膀和手腕，继续工作会更舒服。",
    "做个短暂微休息，调整一下姿势。",
    "眨眨眼，转转肩，给身体一点小缓冲。",
    "休息 30 秒，也是在保护专注力。",
]

TICK_INTERVAL_MS = 30_000


def _safe_load(path: Path, default: dict) -> dict:
    if not path.exists():
        _safe_save(path, default)
        return dict(default)
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return {**default, **data}
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 %s 失败，使用默认值：%s", path.name, exc)
        _safe_save(path, default)
        return dict(default)


def _safe_save(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        tmp.replace(path)
    except Exception as exc:  # noqa: BLE001
        logger.error("写入 %s 失败：%s", path.name, exc)
        tmp.unlink(missing_ok=True)
        messagebox.showerror("保存失败", f"无法写入 {path.name}:\n{exc}")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _now() -> datetime:
    return datetime.now()


class ConfigManager:
    def __init__(self):
        self._data = _safe_load(CONFIG_PATH, DEFAULT_CONFIG)

    @property
    def weight_kg(self) -> float:
        return float(self._data.get("weight_kg", 60))

    @property
    def height_cm(self) -> float:
        return float(self._data.get("height_cm", 170))

    @property
    def drink_interval_min(self) -> int:
        return int(self._data.get("drink_remind_interval_min", 45))

    @property
    def drink_amount_ml(self) -> int:
        return int(self._data.get("drink_amount_ml", 250))

    @property
    def sound_enabled(self) -> bool:
        return bool(self._data.get("sound_enabled", True))

    @property
    def micro_interval_min(self) -> int:
        return int(self._data.get("micro_break_interval_min", 20))

    @property
    def sit_interval_min(self) -> int:
        return int(self._data.get("sit_remind_interval_min", 30))

    @property
    def sit_escalation_min(self) -> int:
        return int(self._data.get("sit_escalation_interval_min", 60))

    @property
    def enable_sit(self) -> bool:
        return bool(self._data.get("enable_sit_reminder", True))

    @property
    def enable_micro(self) -> bool:
        return bool(self._data.get("enable_micro_break", True))

    def get_daily_target_ml(self) -> int:
        return max(1500, int(self.weight_kg * 35))

    def update(self, **kwargs) -> None:
        self._data.update(kwargs)
        _safe_save(CONFIG_PATH, self._data)

    def raw(self) -> dict:
        return dict(self._data)


class DailyRecord:
    _DEFAULTS: dict = {
        "consumed_ml": 0,
        "last_drink_time": "",
        "last_drink_remind_time": "",
        "current_period_drink_muted": False,
        "drink_snooze_until": "",
        "last_posture_reset_time": "",
        "sit_break_count": 0,
        "micro_break_count": 0,
        "longest_sit_minutes": 0,
        "current_period_sit_muted": False,
        "sit_snooze_until": "",
        "last_micro_break_hint_time": "",
    }

    def __init__(self):
        today = date.today().isoformat()
        raw = _safe_load(DAILY_RECORD_PATH, {"date": today, **self._DEFAULTS})
        if raw.get("date") != today:
            raw = {"date": today, **self._DEFAULTS}
        if not raw.get("last_posture_reset_time"):
            raw["last_posture_reset_time"] = _fmt_dt(_now())
        self._d = raw
        self.save()

    @property
    def consumed_ml(self) -> int:
        return int(self._d.get("consumed_ml", 0))

    @property
    def sit_break_count(self) -> int:
        return int(self._d.get("sit_break_count", 0))

    @property
    def micro_break_count(self) -> int:
        return int(self._d.get("micro_break_count", 0))

    @property
    def longest_sit_minutes(self) -> int:
        return int(self._d.get("longest_sit_minutes", 0))

    @property
    def drink_muted(self) -> bool:
        return bool(self._d.get("current_period_drink_muted", False))

    @property
    def sit_muted(self) -> bool:
        return bool(self._d.get("current_period_sit_muted", False))

    @property
    def record_date(self) -> str:
        return str(self._d.get("date", ""))

    def last_drink_time(self) -> datetime | None:
        return _parse_dt(self._d.get("last_drink_time"))

    def last_drink_remind_time(self) -> datetime | None:
        return _parse_dt(self._d.get("last_drink_remind_time"))

    def last_posture_reset_time(self) -> datetime | None:
        return _parse_dt(self._d.get("last_posture_reset_time"))

    def last_micro_hint_time(self) -> datetime | None:
        return _parse_dt(self._d.get("last_micro_break_hint_time"))

    def drink_snooze_until(self) -> datetime | None:
        return _parse_dt(self._d.get("drink_snooze_until"))

    def sit_snooze_until(self) -> datetime | None:
        return _parse_dt(self._d.get("sit_snooze_until"))

    def current_sit_minutes(self, now: datetime | None = None) -> int:
        now = now or _now()
        last = self.last_posture_reset_time() or now
        return max(0, int((now - last).total_seconds() // 60))

    def add_drink(self, amount_ml: int, now: datetime) -> None:
        self._d["consumed_ml"] = self.consumed_ml + amount_ml
        self._d["last_drink_time"] = _fmt_dt(now)
        self._d["last_drink_remind_time"] = _fmt_dt(now)
        self._d["drink_snooze_until"] = ""
        self.save()

    def mark_drink_reminded(self, now: datetime) -> None:
        self._d["last_drink_remind_time"] = _fmt_dt(now)
        self.save()

    def snooze_drink(self, minutes: int, now: datetime | None = None) -> None:
        self._d["drink_snooze_until"] = _fmt_dt((now or _now()) + timedelta(minutes=minutes))
        self.save()

    def mute_drink(self) -> None:
        self._d["current_period_drink_muted"] = True
        self.save()

    def add_sit_break(self, now: datetime) -> None:
        cur = self.current_sit_minutes(now)
        self._d["longest_sit_minutes"] = max(self.longest_sit_minutes, cur)
        self._d["sit_break_count"] = self.sit_break_count + 1
        self._d["last_posture_reset_time"] = _fmt_dt(now)
        self._d["sit_snooze_until"] = ""
        self.save()

    def snooze_sit(self, minutes: int, now: datetime | None = None) -> None:
        self._d["sit_snooze_until"] = _fmt_dt((now or _now()) + timedelta(minutes=minutes))
        self.save()

    def mute_sit(self) -> None:
        self._d["current_period_sit_muted"] = True
        self.save()

    def add_micro_break(self, now: datetime) -> None:
        self._d["micro_break_count"] = self.micro_break_count + 1
        self._d["last_micro_break_hint_time"] = _fmt_dt(now)
        self.save()

    def reset_period_flags(self) -> None:
        self._d["current_period_drink_muted"] = False
        self._d["current_period_sit_muted"] = False
        self.save()

    def reset(self) -> None:
        self._d = {
            "date": date.today().isoformat(),
            **self._DEFAULTS,
            "last_posture_reset_time": _fmt_dt(_now()),
        }
        self.save()

    def save(self) -> None:
        _safe_save(DAILY_RECORD_PATH, self._d)


class ReminderEngine:
    _PERIODS: dict[int, list[tuple[time, time]]] = {
        0: [(time(9, 0), time(12, 0)), (time(14, 0), time(17, 30)), (time(19, 0), time(20, 30))],
        1: [(time(9, 0), time(12, 0)), (time(14, 0), time(17, 30)), (time(19, 0), time(20, 30))],
        2: [(time(9, 0), time(12, 0)), (time(14, 0), time(17, 30))],
        3: [(time(9, 0), time(12, 0)), (time(14, 0), time(17, 30)), (time(19, 0), time(20, 30))],
        4: [(time(9, 0), time(12, 0)), (time(14, 0), time(17, 30))],
    }
    _ENDING_SOON_MIN = 15
    _MIN_DRINK_GAP_MIN = 20

    def get_periods(self, d: date) -> list[tuple[datetime, datetime]]:
        return [(datetime.combine(d, s), datetime.combine(d, e)) for s, e in self._PERIODS.get(d.weekday(), [])]

    def current_period(self, now: datetime) -> tuple[datetime, datetime] | None:
        return next(((s, e) for s, e in self.get_periods(now.date()) if s <= now < e), None)

    def next_period(self, now: datetime) -> tuple[datetime, datetime] | None:
        for s, e in self.get_periods(now.date()):
            if now < s:
                return (s, e)
        d = now.date() + timedelta(days=1)
        for _ in range(8):
            periods = self.get_periods(d)
            if periods:
                return periods[0]
            d += timedelta(days=1)
        return None

    def _period_ending_soon(self, now: datetime) -> bool:
        period = self.current_period(now)
        return (not period) or (period[1] - now).total_seconds() < self._ENDING_SOON_MIN * 60

    def _in_active_period(self, now: datetime) -> bool:
        return bool(self.current_period(now)) and not self._period_ending_soon(now)

    def should_drink(self, now: datetime, cfg: ConfigManager, rec: DailyRecord) -> bool:
        if not self._in_active_period(now) or rec.drink_muted or rec.consumed_ml >= cfg.get_daily_target_ml():
            return False
        snooze = rec.drink_snooze_until()
        if snooze and now < snooze:
            return False
        period = self.current_period(now)
        if period and (now - period[0]).total_seconds() < cfg.drink_interval_min * 60:
            return False
        last_drink = rec.last_drink_time()
        if last_drink and (now - last_drink).total_seconds() < self._MIN_DRINK_GAP_MIN * 60:
            return False
        last_remind = rec.last_drink_remind_time()
        return (last_remind is None) or (now - last_remind).total_seconds() >= cfg.drink_interval_min * 60

    def should_sit_break(self, now: datetime, cfg: ConfigManager, rec: DailyRecord) -> bool:
        if not cfg.enable_sit or not self._in_active_period(now) or rec.sit_muted:
            return False
        snooze = rec.sit_snooze_until()
        if snooze and now < snooze:
            return False
        period = self.current_period(now)
        if period and (now - period[0]).total_seconds() < cfg.sit_interval_min * 60:
            return False
        return rec.current_sit_minutes(now) >= cfg.sit_interval_min

    def should_micro_break(self, now: datetime, cfg: ConfigManager, rec: DailyRecord) -> bool:
        if not cfg.enable_micro or not self._in_active_period(now):
            return False
        last_hint = rec.last_micro_hint_time()
        if last_hint and (now - last_hint).total_seconds() < cfg.micro_interval_min * 60:
            return False
        return rec.current_sit_minutes(now) >= cfg.micro_interval_min

    def should_combined(self, now: datetime, cfg: ConfigManager, rec: DailyRecord) -> bool:
        if not self.should_drink(now, cfg, rec) or not self.should_sit_break(now, cfg, rec):
            return False
        last_remind = rec.last_drink_remind_time() or now
        last_reset = rec.last_posture_reset_time() or now
        drink_due = last_remind + timedelta(minutes=cfg.drink_interval_min)
        sit_due = last_reset + timedelta(minutes=cfg.sit_interval_min)
        return abs((drink_due - sit_due).total_seconds()) <= 5 * 60

    def risk_level(self, now: datetime, cfg: ConfigManager, rec: DailyRecord) -> str:
        sit_min = rec.current_sit_minutes(now)
        if sit_min >= cfg.sit_escalation_min:
            return "high"
        if sit_min >= cfg.sit_interval_min:
            return "mid"
        return "low"


class HydraRiseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = ConfigManager()
        self.rec = DailyRecord()
        self.engine = ReminderEngine()

        self.active_popup: tk.Toplevel | None = None
        self._current_period_start: datetime | None = None

        self._setup_window()
        self._setup_style()
        self._build_ui()
        self._populate_inputs()
        self._refresh_health()
        self._refresh_progress()
        self._refresh_status()
        self._schedule_tick()

    def _setup_window(self):
        self.root.title("HydraRise - 程序员健康提醒助手")
        self.root.geometry("1180x850")
        self.root.minsize(1080, 780)
        self.root.configure(bg=_C["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)

    def _on_quit(self):
        self.rec.save()
        self.root.destroy()

    def _setup_style(self):
        s = ttk.Style()
        s.theme_use("clam")
        bg, card = _C["bg"], _C["card_bg"]
        s.configure("TFrame", background=bg)
        s.configure("TLabel", background=bg, foreground=_C["fg"], font=("Roboto", 10))
        s.configure("Title.TLabel", font=("Roboto", 24, "bold"), foreground=_C["accent"], background=bg)
        s.configure("Subtitle.TLabel", font=("Roboto", 12), foreground=_C["sub_fg"], background=bg)
        s.configure("Status.TLabel", font=("Roboto", 10), foreground=_C["sub_fg"], background=bg)

        for prefix, color in (("Section", bg), ("Card", card)):
            s.configure(f"{prefix}.TFrame", background=color)
            s.configure(f"{prefix}.TLabel", background=color, foreground=_C["fg"], font=("Roboto", 10))

        s.configure(
            "Section.TLabelframe",
            background=card,
            foreground=_C["fg"],
            bordercolor=_C["border"],
            borderwidth=1,
            relief="flat",
            font=("Roboto", 11, "bold"),
        )
        s.configure(
            "Section.TLabelframe.Label",
            foreground=_C["accent"],
            background=card,
            font=("Roboto", 11, "bold"),
            padding=(10, 0),
        )
        s.configure("Value.TLabel", font=("Roboto Medium", 14, "bold"), foreground=_C["accent"], background=card)
        s.configure(
            "TEntry",
            fieldbackground=bg,
            foreground=_C["fg"],
            bordercolor=_C["border"],
            borderwidth=1,
            relief="flat",
            padding=5,
        )
        s.map("TEntry", bordercolor=[("focus", _C["accent"])])

        s.configure(
            "TButton",
            font=("Roboto Medium", 10),
            background=_C["btn_bg"],
            foreground=_C["fg"],
            bordercolor=_C["border"],
            borderwidth=1,
            relief="flat",
            padding=(15, 7),
        )
        s.map("TButton", background=[("active", _C["accent"]), ("pressed", _C["border"])], foreground=[("active", _C["bg"])])
        s.configure("Accent.TButton", background=_C["accent"], foreground=_C["bg"], bordercolor=_C["accent"])
        s.map("Accent.TButton", background=[("active", _C["accent_hover"]), ("pressed", _C["border"])], foreground=[("active", _C["bg"])])

        s.configure("TCheckbutton", background=card, foreground=_C["fg"], font=("Roboto", 10))
        s.map("TCheckbutton", foreground=[("active", _C["accent"])], background=[("active", card)])
        s.configure("Horizontal.TProgressbar", background=_C["accent"], troughcolor=bg, bordercolor=_C["border"], borderwidth=1, relief="flat")

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=25)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 20))
        ttk.Label(header, text="HydraRise", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="程序员健康提醒助手", style="Subtitle.TLabel").pack(anchor="w", pady=(5, 0))

        content = ttk.Frame(outer)
        content.pack(fill="both", expand=True)
        left = ttk.Frame(content)
        right = ttk.Frame(content)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        self._build_left(left)
        self._build_right(right)
        self._build_status_bar(outer)

    def _build_left(self, parent):
        base = ttk.LabelFrame(parent, text="基础信息", style="Section.TLabelframe", padding=15)
        base.pack(fill="x", pady=(0, 10))
        bf = ttk.Frame(base, style="Card.TFrame")
        bf.pack(fill="x")

        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.gender_var = tk.StringVar()
        self.age_var = tk.StringVar()

        fields = (("体重 (kg)", self.weight_var), ("身高 (cm)", self.height_var), ("性别", self.gender_var), ("年龄", self.age_var))
        for i, (label, var) in enumerate(fields):
            ttk.Label(bf, text=label, style="Card.TLabel").grid(row=i, column=0, sticky="w", pady=6, padx=(0, 10))
            ttk.Entry(bf, textvariable=var, width=18).grid(row=i, column=1, sticky="w", pady=6)

        ttk.Button(bf, text="保存所有设置", command=self._on_save, style="Accent.TButton").grid(row=len(fields), column=0, columnspan=2, pady=(15, 5), sticky="ew")

        health = ttk.LabelFrame(parent, text="BMI / 饮水健康", style="Section.TLabelframe", padding=15)
        health.pack(fill="x", pady=10)
        hf = ttk.Frame(health, style="Card.TFrame")
        hf.pack(fill="x")

        self.bmi_value = tk.StringVar(value="--")
        self.bmi_class = tk.StringVar(value="--")
        self.bmi_desc = tk.StringVar(value="请填写有效身高体重")
        self.daily_target_var = tk.StringVar(value="--")
        self.daily_cups = tk.StringVar(value="--")

        health_fields = (
            ("BMI", self.bmi_value),
            ("BMI 分类", self.bmi_class),
            ("BMI 说明", self.bmi_desc),
            ("建议每日饮水量", self.daily_target_var),
            ("约合杯数 (250ml/杯)", self.daily_cups),
        )
        for i, (k, v) in enumerate(health_fields):
            ttk.Label(hf, text=k, style="Card.TLabel").grid(row=i, column=0, sticky="w", pady=6, padx=(0, 15))
            ttk.Label(hf, textvariable=v, style="Value.TLabel").grid(row=i, column=1, sticky="w", pady=6)

    def _build_right(self, parent):
        sf = ttk.Frame(parent)
        sf.pack(fill="x", pady=(0, 10))
        ls = ttk.Frame(sf)
        rs = ttk.Frame(sf)
        ls.pack(side="left", fill="both", expand=True, padx=(0, 5))
        rs.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self._build_drink_settings(ls)
        self._build_sit_settings(rs)
        self._build_progress(parent)
        self._build_stats(parent)

    def _build_drink_settings(self, parent):
        drink = ttk.LabelFrame(parent, text="饮水设置", style="Section.TLabelframe", padding=15)
        drink.pack(fill="both", expand=True)
        df = ttk.Frame(drink, style="Card.TFrame")
        df.pack(fill="x")

        self.drink_interval_var = tk.StringVar()
        self.drink_amount_var = tk.StringVar()
        self.sound_enabled_var = tk.BooleanVar()
        self.lunch_quiet_var = tk.BooleanVar()
        self.offwork_quiet_var = tk.BooleanVar()

        ttk.Label(df, text="间隔 (分钟)", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=5, padx=(0, 8))
        ttk.Entry(df, textvariable=self.drink_interval_var, width=8).grid(row=0, column=1, sticky="w")
        ttk.Label(df, text="量 (ml)", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(df, textvariable=self.drink_amount_var, width=8).grid(row=1, column=1, sticky="w")

        cf = ttk.Frame(df, style="Card.TFrame")
        cf.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        for text, var in (("声音提醒", self.sound_enabled_var), ("午休免打扰", self.lunch_quiet_var), ("下班后免打扰", self.offwork_quiet_var)):
            ttk.Checkbutton(cf, text=text, variable=var).pack(anchor="w", pady=3)

    def _build_sit_settings(self, parent):
        sit = ttk.LabelFrame(parent, text="久坐设置", style="Section.TLabelframe", padding=15)
        sit.pack(fill="both", expand=True)
        sf = ttk.Frame(sit, style="Card.TFrame")
        sf.pack(fill="x")

        self.enable_sit_var = tk.BooleanVar()
        self.enable_micro_var = tk.BooleanVar()
        self.micro_interval_var = tk.StringVar()
        self.sit_interval_var = tk.StringVar()

        cf2 = ttk.Frame(sf, style="Card.TFrame")
        cf2.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Checkbutton(cf2, text="启用久坐提醒", variable=self.enable_sit_var).pack(anchor="w", pady=3)
        ttk.Checkbutton(cf2, text="启用微休息", variable=self.enable_micro_var).pack(anchor="w", pady=3)

        ttk.Label(sf, text="连续 (分钟)", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=5, padx=(0, 8))
        ttk.Entry(sf, textvariable=self.sit_interval_var, width=8).grid(row=1, column=1, sticky="w")
        ttk.Label(sf, text="微休息间隔", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(sf, textvariable=self.micro_interval_var, width=8).grid(row=2, column=1, sticky="w")

    def _build_progress(self, parent):
        prog = ttk.LabelFrame(parent, text="今日健康进度", style="Section.TLabelframe", padding=20)
        prog.pack(fill="x", pady=10)
        pf = ttk.Frame(prog, style="Card.TFrame")
        pf.pack(fill="x")

        self.today_target_var = tk.StringVar(value="0 ml")
        self.today_consumed_var = tk.StringVar(value="0 ml")
        self.today_percent_var = tk.StringVar(value="0%")

        ttk.Label(pf, text="今日饮水目标", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 15))
        ttk.Label(pf, textvariable=self.today_target_var, style="Value.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(pf, text="已饮水", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(pf, textvariable=self.today_consumed_var, style="Value.TLabel").grid(row=1, column=1, sticky="w")

        self.progress = ttk.Progressbar(pf, orient="horizontal", mode="determinate", length=350)
        self.progress.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 12))
        ttk.Label(pf, textvariable=self.today_percent_var, style="Value.TLabel").grid(row=2, column=2, sticky="w", padx=(10, 0))

    def _build_stats(self, parent):
        ops = ttk.LabelFrame(parent, text="统计与操作", style="Section.TLabelframe", padding=15)
        ops.pack(fill="both", expand=True, pady=10)
        of = ttk.Frame(ops, style="Card.TFrame")
        of.pack(fill="both", expand=True)

        self.current_sit_var = tk.StringVar(value="0 分钟")
        self.sit_break_count_var = tk.StringVar(value="0")
        self.longest_sit_var = tk.StringVar(value="0 分钟")

        stats = (("当前久坐", self.current_sit_var), ("今日活动次数", self.sit_break_count_var), ("最长久坐", self.longest_sit_var))
        for i, (k, v) in enumerate(stats):
            ttk.Label(of, text=k, style="Card.TLabel").grid(row=i // 2, column=(i % 2) * 2, sticky="w", pady=5, padx=(0, 10))
            ttk.Label(of, textvariable=v, style="Value.TLabel").grid(row=i // 2, column=(i % 2) * 2 + 1, sticky="w", pady=5, padx=(0, 25))

        ttk.Label(of, text="当前风险", style="Card.TLabel").grid(row=1, column=2, sticky="w", pady=5, padx=(0, 10))
        self.risk_label = tk.Label(of, text="低", font=("Roboto Medium", 14, "bold"), fg=_C["fg"], bg=_C["card_bg"])
        self.risk_label.grid(row=1, column=3, sticky="w", pady=5)

        bf = ttk.Frame(of, style="Card.TFrame")
        bf.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(15, 0))
        for text, cmd in (("测试饮水提醒", self._show_drink_popup), ("测试久坐提醒", self._show_sit_popup), ("记录喝水一次", self._record_drink), ("记录活动一次", self._record_sit_break)):
            ttk.Button(bf, text=text, command=cmd).pack(side="left", padx=5)
        ttk.Button(bf, text="退出", command=self._on_quit).pack(side="right", padx=5)
        ttk.Button(bf, text="重置记录", command=self._on_reset).pack(side="right", padx=5)

    def _build_status_bar(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(15, 0))
        ttk.Separator(bar, orient="horizontal").pack(fill="x", pady=(0, 6))
        self.status_var = tk.StringVar(value="当前状态：初始化中")
        ttk.Label(bar, textvariable=self.status_var, style="Status.TLabel").pack(anchor="w")

    def _populate_inputs(self):
        raw = self.cfg.raw()
        self.weight_var.set(str(raw["weight_kg"]))
        self.height_var.set(str(raw["height_cm"]))
        self.gender_var.set(str(raw.get("gender", "")))
        self.age_var.set(str(raw.get("age", "")))
        self.drink_interval_var.set(str(raw["drink_remind_interval_min"]))
        self.drink_amount_var.set(str(raw["drink_amount_ml"]))
        self.sound_enabled_var.set(bool(raw["sound_enabled"]))
        self.lunch_quiet_var.set(bool(raw["lunch_break_enabled"]))
        self.offwork_quiet_var.set(bool(raw["off_work_quiet_enabled"]))
        self.enable_sit_var.set(bool(raw["enable_sit_reminder"]))
        self.enable_micro_var.set(bool(raw["enable_micro_break"]))
        self.micro_interval_var.set(str(raw["micro_break_interval_min"]))
        self.sit_interval_var.set(str(raw["sit_remind_interval_min"]))

    def _validated_updates(self) -> dict:
        return {
            "weight_kg": float(self.weight_var.get()),
            "height_cm": float(self.height_var.get()),
            "gender": self.gender_var.get().strip(),
            "age": self.age_var.get().strip(),
            "drink_remind_interval_min": max(10, int(self.drink_interval_var.get())),
            "drink_amount_ml": max(50, int(self.drink_amount_var.get())),
            "sound_enabled": self.sound_enabled_var.get(),
            "lunch_break_enabled": self.lunch_quiet_var.get(),
            "off_work_quiet_enabled": self.offwork_quiet_var.get(),
            "enable_sit_reminder": self.enable_sit_var.get(),
            "enable_micro_break": self.enable_micro_var.get(),
            "micro_break_interval_min": max(5, int(self.micro_interval_var.get())),
            "sit_remind_interval_min": max(10, int(self.sit_interval_var.get())),
        }

    def _on_save(self):
        try:
            updates = self._validated_updates()
        except ValueError:
            messagebox.showwarning("输入错误", "请检查数值输入，确保体重/身高/间隔为有效数字。")
            return
        self.cfg.update(**updates)
        self._refresh_health()
        self._refresh_progress()
        self._refresh_status("设置已保存")

    def _on_reset(self):
        if messagebox.askyesno("确认重置", "确定要清除今日所有记录吗？此操作不可撤销。"):
            self.rec.reset()
            self._refresh_progress()
            self._refresh_status("今日记录已重置")

    def _create_popup(self, title: str, message: str, buttons: list[tuple[str, callable]]) -> tk.Toplevel | None:
        if self.active_popup and self.active_popup.winfo_exists():
            return None

        pop = tk.Toplevel(self.root)
        self.active_popup = pop
        pop.title(title)
        pop.geometry("480x300")
        pop.resizable(False, False)
        pop.configure(bg=_C["card_bg"])
        pop.transient(self.root)
        pop.grab_set()

        frm = ttk.Frame(pop, padding=25, style="Card.TFrame")
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=title, style="Value.TLabel", font=("Roboto", 18, "bold")).pack(anchor="w")
        ttk.Label(frm, text=message, style="Card.TLabel", wraplength=430, justify="left").pack(anchor="w", pady=(15, 18))

        bf = ttk.Frame(frm, style="Card.TFrame")
        bf.pack(fill="x", pady=(5, 0))
        for i, (text, cmd) in enumerate(buttons):
            ttk.Button(bf, text=text, command=cmd, style="Accent.TButton" if i == 0 else "TButton").grid(
                row=i // 2, column=i % 2, sticky="ew", padx=5, pady=6
            )
        bf.columnconfigure(0, weight=1)
        bf.columnconfigure(1, weight=1)

        pop.protocol("WM_DELETE_WINDOW", self._close_popup)
        if self.cfg.sound_enabled:
            self.root.bell()
        return pop

    def _close_popup(self, status: str | None = None):
        if self.active_popup and self.active_popup.winfo_exists():
            self.active_popup.destroy()
        self.active_popup = None
        if status:
            self._refresh_status(status)

    def _show_drink_popup(self):
        self.rec.mark_drink_reminded(_now())
        self._create_popup(
            "饮水提醒",
            random.choice(_DRINK_MSGS),
            [
                ("我已喝水", lambda: (self._record_drink(), self._close_popup())),
                ("10分钟后提醒", lambda: (self.rec.snooze_drink(10), self._close_popup("饮水提醒已延后 10 分钟"))),
                ("本时段静默", lambda: (self.rec.mute_drink(), self._close_popup("本时段饮水提醒已静默"))),
                ("关闭", lambda: (self.rec.snooze_drink(5), self._close_popup())),
            ],
        )

    def _show_sit_popup(self):
        self._create_popup(
            "久坐提醒",
            random.choice(_SIT_MSGS),
            [
                ("我已活动", lambda: (self._record_sit_break(), self._close_popup())),
                ("1分钟后提醒", lambda: (self.rec.snooze_sit(1), self._close_popup("久坐提醒已延后 1 分钟"))),
                ("10分钟后提醒", lambda: (self.rec.snooze_sit(10), self._close_popup("久坐提醒已延后 10 分钟"))),
                ("本时段静默", lambda: (self.rec.mute_sit(), self._close_popup("本时段久坐提醒已静默"))),
                ("关闭", lambda: (self.rec.snooze_sit(5), self._close_popup())),
            ],
        )

    def _show_combined_popup(self):
        self.rec.mark_drink_reminded(_now())
        self._create_popup(
            "综合健康提醒",
            random.choice(_COMBINED_MSGS),
            [
                ("我已喝水并活动", lambda: (self._record_drink(), self._record_sit_break(), self._close_popup())),
                ("只记录喝水", lambda: (self._record_drink(), self._close_popup())),
                ("只记录活动", lambda: (self._record_sit_break(), self._close_popup())),
                ("10分钟后提醒", lambda: (self.rec.snooze_drink(10), self.rec.snooze_sit(10), self._close_popup("综合提醒已延后 10 分钟"))),
                ("本时段静默", lambda: (self.rec.mute_drink(), self.rec.mute_sit(), self._close_popup("本时段提醒已静默"))),
                ("关闭", lambda: (self.rec.snooze_drink(5), self.rec.snooze_sit(5), self._close_popup())),
            ],
        )

    def _record_drink(self):
        self.rec.add_drink(self.cfg.drink_amount_ml, _now())
        self._refresh_progress()
        self._refresh_status("已记录喝水 💧")

    def _record_sit_break(self):
        self.rec.add_sit_break(_now())
        self._refresh_progress()
        self._refresh_status("已记录站立活动 🏃")

    def _refresh_health(self):
        w, h = self.cfg.weight_kg, self.cfg.height_cm
        if w <= 0 or h <= 0:
            for var in (self.bmi_value, self.bmi_class, self.daily_target_var, self.daily_cups):
                var.set("--")
            self.bmi_desc.set("请填写有效身高体重")
            return

        bmi = w / (h / 100) ** 2
        self.bmi_value.set(f"{bmi:.1f}")

        if bmi < 18.5:
            cls, desc = "偏瘦", "建议增加营养摄入，保持规律作息。"
        elif bmi <= 23.9:
            cls, desc = "正常", "体重状态良好，继续保持。"
        elif bmi <= 27.9:
            cls, desc = "超重", "建议增加活动与饮食管理。"
        else:
            cls, desc = "肥胖", "建议咨询专业人士改善生活方式。"

        target = self.cfg.get_daily_target_ml()
        self.bmi_class.set(cls)
        self.bmi_desc.set(desc)
        self.daily_target_var.set(f"{target} ml")
        self.daily_cups.set(f"约 {math.ceil(target / 250)} 杯")

    def _refresh_progress(self):
        now = _now()
        target = self.cfg.get_daily_target_ml()
        consumed = self.rec.consumed_ml
        percent = 0 if target <= 0 else min(100, int(consumed / target * 100))

        self.today_target_var.set(f"{target} ml")
        self.today_consumed_var.set(f"{consumed} ml")
        self.today_percent_var.set(f"{percent}%")
        self.progress["value"] = percent

        sit_min = self.rec.current_sit_minutes(now)
        self.current_sit_var.set(f"{sit_min} 分钟")
        self.sit_break_count_var.set(str(self.rec.sit_break_count))
        self.longest_sit_var.set(f"{self.rec.longest_sit_minutes} 分钟")

        risk = self.engine.risk_level(now, self.cfg, self.rec)
        text, color = {"high": ("高 (!!!)", _C["risk_high"]), "mid": ("中 (!)", _C["risk_mid"]), "low": ("低", _C["fg"])}[risk]
        self.risk_label.config(text=text, fg=color)

    def _refresh_status(self, extra: str | None = None):
        if extra:
            self.status_var.set(f"当前状态：{extra}")
            return

        now = _now()
        period = self.engine.current_period(now)
        if period:
            state = "工作中"
        elif now.weekday() >= 5:
            state = "周末"
        else:
            nxt = self.engine.next_period(now)
            state = f"休息中（下一时段 {nxt[0].strftime('%H:%M')}）" if nxt else "休息中"

        last_remind = self.rec.last_drink_remind_time() or now
        next_drink = last_remind + timedelta(minutes=self.cfg.drink_interval_min)
        sit_min = self.rec.current_sit_minutes(now)

        self.status_var.set(
            f"状态：{state} | 久坐：{sit_min} 分 | 下次饮水：{next_drink.strftime('%H:%M')} | 已饮水：{self.rec.consumed_ml} ml | 微休息：{self.rec.micro_break_count} 次"
        )

    def _schedule_tick(self):
        try:
            self._tick()
        except Exception as exc:  # noqa: BLE001
            logger.exception("tick 异常：%s", exc)
        finally:
            self.root.after(TICK_INTERVAL_MS, self._schedule_tick)

    def _tick(self):
        if self.rec.record_date != date.today().isoformat():
            self.rec.reset()
            logger.info("跨日重置完成")

        now = _now()
        period = self.engine.current_period(now)

        if period:
            if self._current_period_start != period[0]:
                self._current_period_start = period[0]
                self.rec.reset_period_flags()
                logger.info("进入新工作时段 %s", period[0].strftime("%H:%M"))
        else:
            self._current_period_start = None

        if not (self.active_popup and self.active_popup.winfo_exists()):
            if self.engine.should_combined(now, self.cfg, self.rec):
                self._show_combined_popup()
            elif self.engine.should_drink(now, self.cfg, self.rec):
                self._show_drink_popup()
            elif self.engine.should_sit_break(now, self.cfg, self.rec):
                self._show_sit_popup()

        if self.engine.should_micro_break(now, self.cfg, self.rec):
            self.rec.add_micro_break(now)
            self._refresh_status(random.choice(_MICRO_MSGS))

        self._refresh_progress()
        self._refresh_status()


def main():
    root = tk.Tk()
    HydraRiseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
