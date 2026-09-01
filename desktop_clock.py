# -*- coding: utf-8 -*-
"""
桌面时钟 Desktop Clock v1.1
可运行于 Windows 10/11 的悬浮桌面时钟：
  · 经典表盘，仅显示时针 + 分针（无秒针，分针平滑走动）
  · 左键按住拖动位置；右下角区域拖拽调整大小（或用菜单/设置滑块）
  · 支持透明度调节、窗口置顶、锁定位置
  · 可创建多个时钟，每个时钟可独立设置国家/时区
  · 数字时间支持 12 小时制(AM/PM)与 24 小时制切换
  · 启动时自动检查窗口是否在屏幕内，避免换机/改分辨率后时钟跑到屏幕外
  · 配置自动保存：优先保存在程序目录（便携），否则 %APPDATA%\\DesktopClock

运行方式：
  python desktop_clock.py            正常启动
  python desktop_clock.py --selftest 自检模式（截图各时钟后退出，用于验证）
"""

import json
import math
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

import tkinter as tk
from tkinter import ttk, colorchooser
from tkinter import font as tkfont

APP_NAME = "桌面时钟"
VERSION = "1.1"

MIN_SIZE = 90
MAX_SIZE = 500
LABEL_H = 58          # 底部文字条高度（数字时间 + 时区两行）

# ---------------------------------------------------------------------------
# 主题配色
# ---------------------------------------------------------------------------
THEMES = {
    "light": {
        "bg": "#ffffff", "face": "#fcfcfc", "border": "#4a4a4a",
        "tick": "#c9c9c9", "tick_major": "#666666",
        "hand_h": "#202020", "hand_m": "#202020",
        "center": "#d33", "text": "#1f1f1f", "label": "#8a8a8a",
        "grip": "#b8b8b8",
    },
    "dark": {
        "bg": "#1a1a1a", "face": "#232323", "border": "#5c5c5c",
        "tick": "#5f5f5f", "tick_major": "#c0c0c0",
        "hand_h": "#f2f2f2", "hand_m": "#f2f2f2",
        "center": "#ff5a5a", "text": "#eeeeee", "label": "#8f8f8f",
        "grip": "#5f5f5f",
    },
}

# 常用国家/城市 -> IANA 时区
COMMON_ZONES = [
    ("中国 · 北京/上海", "Asia/Shanghai"),
    ("中国 · 香港", "Asia/Hong_Kong"),
    ("中国 · 澳门", "Asia/Macau"),
    ("中国 · 台北", "Asia/Taipei"),
    ("日本 · 东京", "Asia/Tokyo"),
    ("韩国 · 首尔", "Asia/Seoul"),
    ("新加坡", "Asia/Singapore"),
    ("马来西亚 · 吉隆坡", "Asia/Kuala_Lumpur"),
    ("泰国 · 曼谷", "Asia/Bangkok"),
    ("越南 · 河内", "Asia/Ho_Chi_Minh"),
    ("菲律宾 · 马尼拉", "Asia/Manila"),
    ("印度 · 新德里", "Asia/Kolkata"),
    ("印度尼西亚 · 雅加达", "Asia/Jakarta"),
    ("澳大利亚 · 悉尼", "Australia/Sydney"),
    ("澳大利亚 · 珀斯", "Australia/Perth"),
    ("新西兰 · 奥克兰", "Pacific/Auckland"),
    ("俄罗斯 · 莫斯科", "Europe/Moscow"),
    ("英国 · 伦敦", "Europe/London"),
    ("法国 · 巴黎", "Europe/Paris"),
    ("德国 · 柏林", "Europe/Berlin"),
    ("意大利 · 罗马", "Europe/Rome"),
    ("西班牙 · 马德里", "Europe/Madrid"),
    ("荷兰 · 阿姆斯特丹", "Europe/Amsterdam"),
    ("瑞士 · 苏黎世", "Europe/Zurich"),
    ("瑞典 · 斯德哥尔摩", "Europe/Stockholm"),
    ("希腊 · 雅典", "Europe/Athens"),
    ("葡萄牙 · 里斯本", "Europe/Lisbon"),
    ("土耳其 · 伊斯坦布尔", "Europe/Istanbul"),
    ("阿联酋 · 迪拜", "Asia/Dubai"),
    ("沙特阿拉伯 · 利雅得", "Asia/Riyadh"),
    ("以色列 · 特拉维夫", "Asia/Jerusalem"),
    ("南非 · 约翰内斯堡", "Africa/Johannesburg"),
    ("埃及 · 开罗", "Africa/Cairo"),
    ("肯尼亚 · 内罗毕", "Africa/Nairobi"),
    ("美国 · 纽约", "America/New_York"),
    ("美国 · 洛杉矶", "America/Los_Angeles"),
    ("美国 · 芝加哥", "America/Chicago"),
    ("美国 · 丹佛", "America/Denver"),
    ("加拿大 · 多伦多", "America/Toronto"),
    ("加拿大 · 温哥华", "America/Vancouver"),
    ("墨西哥 · 墨西哥城", "America/Mexico_City"),
    ("巴西 · 圣保罗", "America/Sao_Paulo"),
    ("阿根廷 · 布宜诺斯艾利斯", "America/Buenos_Aires"),
    ("智利 · 圣地亚哥", "America/Santiago"),
    ("哥伦比亚 · 波哥大", "America/Bogota"),
]

ZONE_LABEL = {tz: name for name, tz in COMMON_ZONES}
ZONE_LIST = [f"{name}  [{tz}]" for name, tz in COMMON_ZONES]


def friendly_label(tz):
    return ZONE_LABEL.get(tz, tz)


def utc_offset_str(tz):
    try:
        off = datetime.now(ZoneInfo(tz)).utcoffset()
        total = int(off.total_seconds())
        sign = "+" if total >= 0 else "-"
        total = abs(total)
        return f"UTC{sign}{total // 3600}:{(total % 3600) // 60:02d}"
    except Exception:
        return ""


def enable_dpi_awareness():
    """让 tkinter 坐标与物理像素一致，避免高 DPI 下窗口偏移/模糊。"""
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def screen_work_rects():
    """返回所有显示器的屏幕区域（物理像素）[(l,t,r,b),...]；失败返回 None。"""
    try:
        import ctypes
        from ctypes import wintypes

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        rects = []
        enum_cb = ctypes.WINFUNCTYPE(
            ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.POINTER(RECT), ctypes.c_void_p)

        def _cb(_hmon, _hdc, lprc, _data):
            r = lprc.contents
            rects.append((r.left, r.top, r.right, r.bottom))
            return 1

        ctypes.windll.user32.EnumDisplayMonitors(0, 0, enum_cb(_cb), 0)
        return rects if rects else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 路径与配置
# ---------------------------------------------------------------------------
def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def config_path():
    d = app_dir()
    try:
        probe = os.path.join(d, ".write_probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("")
        os.remove(probe)
        return os.path.join(d, "desktop_clock_config.json")
    except Exception:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        folder = os.path.join(base, "DesktopClock")
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception:
            pass
        return os.path.join(folder, "desktop_clock_config.json")


def default_clock(x, y):
    return {
        "x": x, "y": y, "size": 170, "alpha": 0.92,
        "tz": "Asia/Shanghai", "locked": False, "topmost": True,
        "theme": "light", "show_digital": True, "hour12": True,
        "hand_h_color": None, "hand_m_color": None,
    }


# ---------------------------------------------------------------------------
# 表盘窗口
# ---------------------------------------------------------------------------
class ClockFace(tk.Toplevel):
    def __init__(self, app, cfg):
        super().__init__(app.root)
        self.app = app
        self.cfg = cfg
        self._drag_off = None
        self._resizing = False
        self.overrideredirect(True)          # 无边框悬浮窗
        self.attributes("-topmost", bool(cfg["topmost"]))
        self._apply_alpha()
        self.configure(bg=self.c("bg"))

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        # 交互
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_menu)
        self.canvas.bind("<Double-Button-1>", self._on_double)

        self._build_menu()
        self.apply_geometry()
        self._clamp_to_screen()              # 防止窗口在屏幕外
        self.draw_static()
        self._loop()

    # ---- 颜色 ----
    def c(self, key):
        th = THEMES.get(self.cfg.get("theme", "light"), THEMES["light"])
        if key == "hand_h" and self.cfg.get("hand_h_color"):
            return self.cfg["hand_h_color"]
        if key == "hand_m" and self.cfg.get("hand_m_color"):
            return self.cfg["hand_m_color"]
        return th.get(key, th["text"])

    # ---- 几何 ----
    @property
    def size(self):
        return self.cfg["size"]

    def w(self):
        return self.size

    def h(self):
        return self.size + LABEL_H

    def apply_geometry(self):
        self.geometry(f"{self.w()}x{self.h()}+{self.cfg['x']}+{self.cfg['y']}")
        self.canvas.config(width=self.w(), height=self.h(), bg=self.c("bg"))

    def set_size(self, s):
        s = int(max(MIN_SIZE, min(MAX_SIZE, s)))
        self.cfg["size"] = s
        self.apply_geometry()
        self.draw_static()
        self._save()

    def set_alpha(self, v):
        self.cfg["alpha"] = max(0.15, min(1.0, float(v)))
        self._apply_alpha()
        self._save()

    def _apply_alpha(self):
        try:
            self.attributes("-alpha", float(self.cfg["alpha"]))
        except Exception:
            pass

    def move_to(self, x, y):
        self.cfg["x"], self.cfg["y"] = int(x), int(y)
        self.geometry(f"+{self.cfg['x']}+{self.cfg['y']}")
        self._save()

    # ---- 屏幕外归位 ----
    def _clamp_to_screen(self):
        """若窗口与任何显示器都不相交，则将其拉回主屏幕内。
        解决把 exe 拷到另一台电脑（分辨率/多屏/缩放不同）后时钟跑到屏幕外的问题。"""
        try:
            w, h = self.w(), self.h()
            x, y = int(self.cfg.get("x", 0)), int(self.cfg.get("y", 0))
            rects = screen_work_rects()
            if rects:
                for (l, t, r, b) in rects:
                    if not (x + w < l or x > r or y + h < t or y > b):
                        return  # 与某块屏幕相交，保留原位置
                l, t, r, b = rects[0]
                nx = min(max(x, l + 12), max(l, r - w - 12))
                ny = min(max(y, t + 12), max(t, b - h - 12))
                self.cfg["x"], self.cfg["y"] = nx, ny
                self.geometry(f"{w}x{h}+{nx}+{ny}")
            else:
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                if x + w < 0 or x > sw or y + h < 0 or y > sh:
                    nx = max(0, min(x, max(0, sw - w - 40)))
                    ny = max(0, min(y, max(0, sh - h - 60)))
                    self.cfg["x"], self.cfg["y"] = nx, ny
                    self.geometry(f"{w}x{h}+{nx}+{ny}")
        except Exception:
            pass

    def center_on_screen(self):
        """把时钟移到主屏幕中央（用于手动找回丢失的窗口）。"""
        try:
            self.update_idletasks()
            w, h = self.w(), self.h()
            rects = screen_work_rects()
            if rects:
                l, t, r, b = rects[0]
                x = l + (r - l - w) // 2
                y = t + (b - t - h) // 2
            else:
                x = max(0, (self.winfo_screenwidth() - w) // 2)
                y = max(0, (self.winfo_screenheight() - h) // 2)
            self.cfg["x"], self.cfg["y"] = int(x), int(y)
            self.geometry(f"{w}x{h}+{x}+{y}")
            self.lift()
            self._save()
        except Exception:
            pass

    # ---- 绘制 ----
    def draw_static(self):
        cv = self.canvas
        cv.delete("all")
        cx = self.size / 2.0
        cy = self.size / 2.0
        R = self.size / 2.0 - 10

        # 表盘
        cv.create_oval(cx - R, cy - R, cx + R, cy + R,
                       fill=self.c("face"), outline=self.c("border"), width=2)

        # 刻度：60 个分钟小刻度 + 12 个整点大刻度
        for i in range(60):
            a = math.radians(i * 6 - 90)
            major = (i % 5 == 0)
            r1 = R - (self.size * 0.10 if major else self.size * 0.045)
            x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
            x2, y2 = cx + R * math.cos(a), cy + R * math.sin(a)
            cv.create_line(x1, y1, x2, y2,
                           fill=self.c("tick_major") if major else self.c("tick"),
                           width=2 if major else 1)

        # 时针 / 分针（多边形，稍后每帧更新坐标）
        self.hour_item = cv.create_polygon(0, 0, 0, 0, 0, 0, fill=self.c("hand_h"))
        self.min_item = cv.create_polygon(0, 0, 0, 0, 0, 0, fill=self.c("hand_m"))

        # 中心轴
        cr = max(3, self.size * 0.035)
        cv.create_oval(cx - cr, cy - cr, cx + cr, cy + cr,
                       fill=self.c("center"), outline=self.c("center"))

        # 底部文字：数字时间（含 AM/PM）+ 时区，分两行避免重叠
        ty = self.size + 14
        self.dig_item = cv.create_text(cx, ty, text="--:--",
                                       fill=self.c("text"), font=("Segoe UI", self._dig_font(), "bold"))
        ly = self.size + 46
        self.lab_item = cv.create_text(cx, ly, text="",
                                       fill=self.c("label"), font=("Microsoft YaHei UI", self._lab_font()))

        self.update_hands()

    def _dig_font(self):
        # 负号为像素字号，不受 DPI 缩放影响，尺寸可预测
        return max(-16, min(-int(self.size * 0.12), -24))

    def _lab_font(self):
        return max(-11, min(-int(self.size * 0.075), -14))

    def _fit_label(self, text, font_size):
        """按表盘实际宽度用字体测量截断时区文字，避免溢出窗口。"""
        limit = self.size - 16
        if limit <= 0:
            return text
        cache = getattr(self, "_fit_fonts", None)
        if cache is None:
            cache = self._fit_fonts = {}
        f = cache.get(font_size)
        if f is None:
            f = tkfont.Font(family="Microsoft YaHei UI", size=font_size)
            cache[font_size] = f
        if f.measure(text) <= limit:
            return text
        out = ""
        for ch in text:
            if f.measure(out + ch + "…") > limit:
                break
            out += ch
        return out + "…"

    @staticmethod
    def _hand_pts(cx, cy, length, width, angle):
        """返回时针/分针的四边形顶点（角度以 12 点为 0，顺时针）。"""
        dx, dy = math.sin(angle), -math.cos(angle)
        px, py = math.cos(angle), math.sin(angle)
        tail = -length * 0.20
        bx, by = cx + dx * tail, cy + dy * tail
        return [bx + px * width / 2, by + py * width / 2,
                cx + dx * length, cy + dy * length,
                bx - px * width / 2, by - py * width / 2]

    def update_hands(self):
        try:
            tz = ZoneInfo(self.cfg["tz"])
            now = datetime.now(tz)
        except Exception:
            tz = ZoneInfo("Asia/Shanghai")
            now = datetime.now(tz)
        # 测试钩子：DESKTOP_CLOCK_FREEZE=HH:MM 冻结时间（仅用于验证指针角度）
        _freeze = os.environ.get("DESKTOP_CLOCK_FREEZE")
        if _freeze and ":" in _freeze:
            try:
                fh, fm = _freeze.split(":")
                now = now.replace(hour=int(fh), minute=int(fm), second=0, microsecond=0)
            except Exception:
                pass
        s = now.second
        m = now.minute
        h = now.hour % 12
        minute_frac = m + s / 60.0
        hour_frac = h + minute_frac / 60.0

        cx = self.size / 2.0
        cy = self.size / 2.0
        R = self.size / 2.0 - 10

        len_h = R * 0.52
        len_m = R * 0.78
        w_h = max(3, self.size * 0.045)
        w_m = max(2, self.size * 0.032)

        a_h = math.radians(hour_frac * 30)
        a_m = math.radians(minute_frac * 6)
        self.canvas.coords(self.hour_item, *self._hand_pts(cx, cy, len_h, w_h, a_h))
        self.canvas.coords(self.min_item, *self._hand_pts(cx, cy, len_m, w_m, a_m))

        if self.cfg.get("show_digital", True):
            if self.cfg.get("hour12", True):
                hh = now.hour % 12 or 12
                ampm = "AM" if now.hour < 12 else "PM"
                self.canvas.itemconfig(self.dig_item, text=f"{hh}:{now.minute:02d} {ampm}")
            else:
                self.canvas.itemconfig(self.dig_item, text=f"{now.hour:02d}:{now.minute:02d}")
        else:
            self.canvas.itemconfig(self.dig_item, text="")
        self.canvas.itemconfig(
            self.lab_item,
            text=self._fit_label(
                f"{friendly_label(self.cfg['tz'])} {utc_offset_str(self.cfg['tz'])}",
                self._lab_font()))

    def _loop(self):
        self.update_hands()
        self.after(250, self._loop)

    # ---- 交互 ----
    def _in_grip(self, x, y):
        return x >= self.w() - 34 and y >= self.h() - 34

    def _on_press(self, e):
        self._resizing = self._in_grip(e.x, e.y)
        if self.cfg.get("locked"):
            self._resizing = False
            return
        self._drag_off = (e.x_root - self.winfo_x(), e.y_root - self.winfo_y())
        self.canvas.config(cursor="sizing" if self._resizing else "fleur")

    def _on_motion(self, e):
        if self.cfg.get("locked"):
            return
        if self._resizing:
            nw = max(MIN_SIZE, e.x_root - self.winfo_x())
            self.set_size(nw)
        elif self._drag_off is not None:
            self.move_to(e.x_root - self._drag_off[0], e.y_root - self._drag_off[1])

    def _on_release(self, _e):
        self._drag_off = None
        self._resizing = False
        self.canvas.config(cursor="")

    def _on_double(self, _e):
        self.open_settings()

    # ---- 右键菜单 ----
    def _build_menu(self):
        self.menu = tk.Menu(self, tearoff=0)

    def _on_menu(self, e):
        menu = tk.Menu(self, tearoff=0)

        menu.add_command(label="设置...", command=self.open_settings)

        alpha_menu = tk.Menu(menu, tearoff=0)
        for p in (0.3, 0.5, 0.7, 0.85, 1.0):
            alpha_menu.add_command(
                label=f"{int(p * 100)}%", command=lambda v=p: self.set_alpha(v))
        menu.add_cascade(label="透明度", menu=alpha_menu)

        size_menu = tk.Menu(menu, tearoff=0)
        for s, name in ((110, "小"), (150, "中"), (190, "大"), (240, "更大")):
            size_menu.add_command(label=f"{name} ({s})", command=lambda v=s: self.set_size(v))
        menu.add_cascade(label="表盘大小", menu=size_menu)

        theme_menu = tk.Menu(menu, tearoff=0)
        theme_menu.add_command(label="浅色", command=lambda: self.set_theme("light"))
        theme_menu.add_command(label="深色", command=lambda: self.set_theme("dark"))
        menu.add_cascade(label="主题", menu=theme_menu)

        menu.add_separator()
        menu.add_command(label="锁定位置", command=self.toggle_lock)
        menu.add_command(label="窗口置顶", command=self.toggle_topmost)
        menu.add_command(label="显示数字时间", command=self.toggle_digital)
        menu.add_separator()
        menu.add_command(label="移至屏幕中央", command=self.center_on_screen)
        menu.add_separator()
        menu.add_command(label="添加一个时钟", command=self.app.add_clock)
        menu.add_command(label="删除此时钟", command=self.remove_self)
        menu.add_separator()
        menu.add_command(label="退出全部时钟", command=self.app.quit_all)
        menu.tk_popup(e.x_root, e.y_root)
        menu.grab_release()

    def toggle_lock(self):
        self.cfg["locked"] = not self.cfg.get("locked", False)
        self._save()

    def toggle_topmost(self):
        self.cfg["topmost"] = not self.cfg.get("topmost", True)
        self.attributes("-topmost", self.cfg["topmost"])
        self._save()

    def toggle_digital(self):
        self.cfg["show_digital"] = not self.cfg.get("show_digital", True)
        self.update_hands()
        self._save()

    def set_theme(self, th):
        self.cfg["theme"] = th
        self.configure(bg=self.c("bg"))
        self.apply_geometry()
        self.draw_static()
        self._save()

    # ---- 设置 ----
    def open_settings(self):
        SettingsDialog(self.app, self)

    def remove_self(self):
        self.app.remove_clock(self)

    def _save(self):
        self.app.save_config()

    def destroy_me(self):
        try:
            self.canvas.delete("all")
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 设置对话框
# ---------------------------------------------------------------------------
class SettingsDialog(tk.Toplevel):
    def __init__(self, app, clock):
        super().__init__(app.root)
        self.app = app
        self.clock = clock
        self.cfg = clock.cfg
        self.title(f"时钟设置 - {friendly_label(self.cfg['tz'])}")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._build()
        # 主窗口 withdraw 后，必须显式布局、定位到时钟旁边并置顶聚焦，否则不显示
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 380)
        h = self.winfo_reqheight()
        cw = clock.winfo_width()
        ch = clock.winfo_height()
        cx = clock.winfo_rootx() + cw // 2
        cy = clock.winfo_rooty() + ch // 2
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, min(int(cx - w // 2), max(0, sw - w - 40)))
        y = max(0, min(int(cy - h // 2), max(0, sh - h - 60)))
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_force()
        self.after(80, self._keep_focus)

    def _keep_focus(self):
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _build(self):
        pad = {"padx": 12, "pady": 5}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        # 时区
        ttk.Label(frm, text="国家 / 城市时区：").grid(row=0, column=0, sticky="w", **pad)
        self.tz_cb = ttk.Combobox(frm, values=ZONE_LIST, state="readonly", width=38)
        self.tz_cb.grid(row=0, column=1, columnspan=2, sticky="we", **pad)
        self.tz_cb.bind("<<ComboboxSelected>>", self._on_zone_selected)
        for i, (name, tz) in enumerate(COMMON_ZONES):
            if tz == self.cfg["tz"]:
                self.tz_cb.current(i)
                break

        ttk.Label(frm, text="自定义时区(IANA)：").grid(row=1, column=0, sticky="w", **pad)
        self.tz_entry = ttk.Entry(frm, width=28)
        self.tz_entry.grid(row=1, column=1, sticky="we", **pad)
        self.tz_entry.insert(0, self.cfg["tz"])
        ttk.Button(frm, text="应用", command=self._apply_custom_zone).grid(row=1, column=2, **pad)
        ttk.Label(frm, text="当前：%s  %s" % (self.cfg["tz"], utc_offset_str(self.cfg["tz"])),
                  foreground="#888").grid(row=2, column=1, columnspan=2, sticky="w", padx=12)

        ttk.Separator(frm).grid(row=3, column=0, columnspan=3, sticky="we", pady=8)

        # 透明度
        ttk.Label(frm, text="透明度：").grid(row=4, column=0, sticky="w", **pad)
        self.alpha_var = tk.IntVar(value=int(round(self.cfg["alpha"] * 100)))
        ttk.Scale(frm, from_=20, to=100, variable=self.alpha_var,
                  command=self._on_alpha).grid(row=4, column=1, sticky="we", **pad)
        ttk.Label(frm, textvariable=self.alpha_var, width=4).grid(row=4, column=2, **pad)

        # 大小
        ttk.Label(frm, text="表盘大小：").grid(row=5, column=0, sticky="w", **pad)
        self.size_var = tk.IntVar(value=self.cfg["size"])
        ttk.Scale(frm, from_=MIN_SIZE, to=MAX_SIZE, variable=self.size_var,
                  command=self._on_size).grid(row=5, column=1, sticky="we", **pad)
        ttk.Label(frm, textvariable=self.size_var, width=4).grid(row=5, column=2, **pad)

        ttk.Separator(frm).grid(row=6, column=0, columnspan=3, sticky="we", pady=8)

        # 选项
        self.lock_var = tk.BooleanVar(value=bool(self.cfg.get("locked")))
        self.top_var = tk.BooleanVar(value=bool(self.cfg.get("topmost", True)))
        self.dig_var = tk.BooleanVar(value=bool(self.cfg.get("show_digital", True)))
        self.h12_var = tk.BooleanVar(value=bool(self.cfg.get("hour12", True)))
        ttk.Checkbutton(frm, text="锁定位置（不可拖动/缩放）", variable=self.lock_var,
                        command=self._on_lock).grid(row=7, column=1, sticky="w", **pad)
        ttk.Checkbutton(frm, text="窗口置顶", variable=self.top_var,
                        command=self._on_top).grid(row=8, column=1, sticky="w", **pad)
        disp = ttk.Frame(frm)
        disp.grid(row=9, column=1, sticky="w", padx=12, pady=2)
        ttk.Checkbutton(disp, text="显示数字时间", variable=self.dig_var,
                        command=self._on_digital).pack(side="left")
        ttk.Checkbutton(disp, text="AM/PM 12小时制", variable=self.h12_var,
                        command=self._on_hour12).pack(side="left", padx=10)

        ttk.Label(frm, text="主题：").grid(row=10, column=0, sticky="w", **pad)
        self.theme_var = tk.StringVar(value=self.cfg.get("theme", "light"))
        tt = ttk.Frame(frm)
        tt.grid(row=10, column=1, columnspan=2, sticky="w", padx=12)
        ttk.Radiobutton(tt, text="浅色", value="light", variable=self.theme_var,
                        command=self._on_theme).pack(side="left")
        ttk.Radiobutton(tt, text="深色", value="dark", variable=self.theme_var,
                        command=self._on_theme).pack(side="left", padx=8)

        ttk.Label(frm, text="指针颜色：").grid(row=11, column=0, sticky="w", **pad)
        hcol = ttk.Frame(frm)
        hcol.grid(row=11, column=1, columnspan=2, sticky="w", padx=12)
        ttk.Button(hcol, text="时针", width=8, command=lambda: self._pick_color("hand_h_color")).pack(side="left")
        ttk.Button(hcol, text="分针", width=8, command=lambda: self._pick_color("hand_m_color")).pack(side="left", padx=6)
        ttk.Button(hcol, text="恢复默认", command=self._reset_colors).pack(side="left")

        ttk.Separator(frm).grid(row=12, column=0, columnspan=3, sticky="we", pady=8)

        bottom = ttk.Frame(frm)
        bottom.grid(row=13, column=0, columnspan=3, sticky="e", pady=4)
        ttk.Button(bottom, text="删除此时钟", command=self.clock.remove_self).pack(side="left", padx=6)
        ttk.Button(bottom, text="关闭", command=self.destroy).pack(side="left")

    def _on_zone_selected(self, _e):
        idx = self.tz_cb.current()
        if idx >= 0 and idx < len(COMMON_ZONES):
            tz = COMMON_ZONES[idx][1]
            self._set_zone(tz)

    def _apply_custom_zone(self):
        tz = self.tz_entry.get().strip()
        if not tz:
            return
        try:
            ZoneInfo(tz)
        except Exception:
            import tkinter.messagebox as mb
            mb.showerror("时区无效", f"无法识别时区：{tz}\n请输入有效的 IANA 时区，例如 Asia/Tokyo", parent=self)
            return
        self._set_zone(tz)

    def _set_zone(self, tz):
        self.cfg["tz"] = tz
        self.tz_entry.delete(0, "end")
        self.tz_entry.insert(0, tz)
        self.clock.update_hands()
        self.clock._save()
        self.title(f"时钟设置 - {friendly_label(tz)}")

    def _on_alpha(self, _v):
        self.clock.set_alpha(self.alpha_var.get() / 100.0)

    def _on_size(self, _v):
        self.clock.set_size(self.size_var.get())

    def _on_lock(self):
        self.cfg["locked"] = self.lock_var.get()
        self.clock._save()

    def _on_top(self):
        self.cfg["topmost"] = self.top_var.get()
        self.clock.attributes("-topmost", self.top_var.get())
        self.clock._save()

    def _on_digital(self):
        self.cfg["show_digital"] = self.dig_var.get()
        self.clock.update_hands()
        self.clock._save()

    def _on_hour12(self):
        self.cfg["hour12"] = self.h12_var.get()
        self.clock.update_hands()
        self.clock._save()

    def _on_theme(self):
        self.clock.set_theme(self.theme_var.get())

    def _pick_color(self, key):
        rgb, hx = colorchooser.askcolor(color=self.cfg.get(key) or "#202020", parent=self)
        if hx:
            self.cfg[key] = hx
            self.clock.draw_static()
            self.clock._save()

    def _reset_colors(self):
        self.cfg["hand_h_color"] = None
        self.cfg["hand_m_color"] = None
        self.clock.draw_static()
        self.clock._save()


# ---------------------------------------------------------------------------
# 主应用
# ---------------------------------------------------------------------------
class DesktopClockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()          # 隐藏主窗口，只有悬浮表盘
        self.root.title(APP_NAME)
        self.clocks = []
        self._cfg_file = config_path()
        self._load_config()

    # ---- 配置 ----
    def _load_config(self):
        data = {}
        try:
            with open(self._cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        self.settings = data.get("settings", {})
        self.clocks_cfg = data.get("clocks", []) or []

    def save_config(self):
        data = {
            "settings": self.settings,
            "clocks": [dict(c) for c in self.clocks_cfg],
        }
        try:
            with open(self._cfg_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ---- 时钟管理 ----
    def start(self):
        if not self.clocks_cfg:
            self._seed_default()
        for cfg in self.clocks_cfg:
            c = ClockFace(self, cfg)
            self.clocks.append(c)
        for c in self.clocks:
            try:
                ZoneInfo(c.cfg["tz"])
            except Exception:
                c.cfg["tz"] = "Asia/Shanghai"
                c.update_hands()
        # 确保所有窗口已映射并可见（配合启动时屏幕外归位）
        try:
            self.root.update_idletasks()
            for c in self.clocks:
                if not c.winfo_viewable():
                    c.deiconify()
                    c.lift()
        except Exception:
            pass
        self.save_config()

    def _seed_default(self):
        import random
        base_x = 60 + random.randint(0, 20)
        base_y = 60 + random.randint(0, 20)
        self.clocks_cfg.append(default_clock(base_x, base_y))

    def add_clock(self):
        ref = self.clocks[-1].cfg if self.clocks else default_clock(100, 100)
        cfg = dict(ref)
        cfg["x"] = int(ref.get("x", 100)) + 40
        cfg["y"] = int(ref.get("y", 100)) + 40
        zones = [c.cfg["tz"] for c in self.clocks]
        for _tz in ("Asia/Tokyo", "America/New_York", "Europe/London", "Asia/Singapore"):
            if _tz not in zones:
                cfg["tz"] = _tz
                break
        self.clocks_cfg.append(cfg)
        c = ClockFace(self, cfg)
        self.clocks.append(c)
        self.save_config()
        return c

    def remove_clock(self, clock):
        if len(self.clocks) <= 1:
            import tkinter.messagebox as mb
            mb.showinfo(APP_NAME, "至少保留一个时钟。\n如需退出，请选择“退出全部时钟”。", parent=clock)
            return
        clock.destroy_me()
        if clock in self.clocks:
            self.clocks.remove(clock)
        if clock.cfg in self.clocks_cfg:
            self.clocks_cfg.remove(clock.cfg)
        self.save_config()

    def quit_all(self):
        self.save_config()
        for c in self.clocks:
            try:
                c.destroy_me()
            except Exception:
                pass
        self.root.destroy()

    def run(self):
        self.start()
        self.root.protocol("WM_DELETE_WINDOW", self.quit_all)
        self.root.mainloop()

    # ---- 自检模式：截图后退出（用于验证） ----
    def run_selftest(self, outdir):
        self.start()
        self.root.update()
        self.root.update_idletasks()
        report = []
        try:
            from PIL import ImageGrab
            import time as _t
            _t.sleep(0.6)
            for i, c in enumerate(self.clocks):
                self.root.update()
                hc = c.canvas.coords(c.hour_item)
                mc = c.canvas.coords(c.min_item)
                _cx = c.size / 2.0

                def _face(pts):
                    dx, dy = pts[2] - _cx, pts[3] - _cx
                    a = (math.degrees(math.atan2(dy, dx)) + 360) % 360
                    return (a + 90) % 360

                line = f"SELFTEST hands: tz={c.cfg['tz']} " \
                       f"hour={_face(hc):.0f}deg min={_face(mc):.0f}deg"
                print(line)
                report.append(line)
                _db = c.canvas.bbox(c.dig_item)
                _lb = c.canvas.bbox(c.lab_item)
                _dig_text = c.canvas.itemcget(c.dig_item, "text")
                _lab_text = c.canvas.itemcget(c.lab_item, "text")
                _ov = not (_db is None or _lb is None or _db[3] < _lb[1] or _lb[3] < _db[1])
                line = f"SELFTEST text: dig='{_dig_text}' lab='{_lab_text}' " \
                       f"dig_bbox={_db} lab_bbox={_lb} overlap={_ov}"
                print(line)
                report.append(line)
                line = f"SELFTEST pos: tz={c.cfg['tz']} pos=({c.winfo_x()},{c.winfo_y()}) " \
                       f"viewable={c.winfo_viewable()}"
                print(line)
                report.append(line)
                x = c.winfo_rootx()
                y = c.winfo_rooty()
                w = c.winfo_width()
                h = c.winfo_height()
                img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                path = os.path.join(outdir, f"clock_{i}_{c.cfg['tz'].replace('/', '_')}.png")
                img.save(path)
                line2 = f"SELFTEST saved: {path}  (size={c.size}, alpha={c.cfg['alpha']}, tz={c.cfg['tz']})"
                print(line2)
                report.append(line2)
        except Exception as e:
            line = f"SELFTEST capture error: {e}"
            print(line)
            report.append(line)
            line = "SELFTEST rendered windows: " + str(
                [(c.cfg['tz'], c.winfo_width(), c.winfo_height()) for c in self.clocks])
            print(line)
            report.append(line)
        try:
            with open(os.path.join(outdir, "report.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(report))
        except Exception:
            pass
        # 设置对话框可见性检查（验证 -- 修复对话框不显示的 bug）
        try:
            c = self.clocks[0]
            c.open_settings()
            for _ in range(12):
                self.root.update()
            dlg = [w for w in self.root.winfo_children() if isinstance(w, SettingsDialog)]
            if dlg:
                d = dlg[0]
                line = f"SELFTEST settings-dialog: viewable={d.winfo_viewable()} mapped={d.winfo_ismapped()} geo={d.winfo_geometry()}"
                print(line)
                try:
                    with open(os.path.join(outdir, "report.txt"), "a", encoding="utf-8") as f:
                        f.write("\n" + line)
                except Exception:
                    pass
                d.destroy()
        except Exception as e:
            print("SELFTEST settings-dialog error:", e)
        self.quit_all()
        print("SELFTEST DONE")


# ---------------------------------------------------------------------------
def make_icon(path):
    """用 Pillow 生成一个简单表盘图标（可选）。"""
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return False
    sizes = [256, 64, 48, 32, 16]
    imgs = []
    for s in sizes:
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        m = s * 0.04
        d.ellipse([m, m, s - m, s - m], fill=(37, 99, 235, 255), outline=(255, 255, 255, 255), width=max(1, s // 24))
        cx = cy = s / 2
        R = s / 2 - m - 2
        for i in range(12):
            a = math.radians(i * 30 - 90)
            r1 = R * (0.78 if i % 3 else 0.62)
            x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
            x2, y2 = cx + R * math.cos(a), cy + R * math.sin(a)
            d.line([x1, y1, x2, y2], fill=(255, 255, 255, 255), width=max(1, s // 40))
        d.line([cx, cy, cx + R * 0.45, cy], fill=(255, 255, 255, 255), width=max(1, s // 28))
        d.line([cx, cy, cx, cy - R * 0.7], fill=(255, 255, 255, 255), width=max(1, s // 32))
        d.ellipse([cx - R * 0.09, cy - R * 0.09, cx + R * 0.09, cy + R * 0.09],
                  fill=(255, 255, 255, 255))
        imgs.append(im)
    imgs[0].save(path, format="ICO", sizes=[(s, s) for s in sizes], append_images=imgs[1:])
    return True


def main():
    enable_dpi_awareness()
    if "--selftest" in sys.argv:
        outdir = os.path.join(app_dir(), "selftest_out")
        os.makedirs(outdir, exist_ok=True)
        app = DesktopClockApp()
        app.run_selftest(outdir)
        return
    app = DesktopClockApp()
    app.run()


if __name__ == "__main__":
    main()
