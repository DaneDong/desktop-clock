# 桌面时钟 Desktop Clock

一个可运行于 **Windows 10 / 11** 的悬浮桌面时钟。

经典表盘，只显示时针和分针（无秒针、分针平滑走动）；无边框悬浮、始终置顶；支持多时钟、多时区、透明度、主题、AM/PM 等。

## 功能特性

- 🕐 经典表盘，仅时针 + 分针，分针平滑走动
- 📌 无边框悬浮窗，始终显示在其他窗口之上
- ✋ 左键拖动移动位置，右下角区域调整大小（也可用菜单/设置滑块）
- 🎚 透明度调节（20% - 100%）
- 🌍 **多时钟 + 多时区**：可添加多个时钟，每个时钟独立设置国家/时区（内置 40+ 常用城市，也支持任意 IANA 时区）
- 🕑 数字时间支持 **12 小时制（AM/PM）** 与 24 小时制切换
- 🎨 浅色 / 深色主题，可自定义时针、分针颜色
- 🔒 锁定位置、窗口置顶、显示数字时间开关
- 🛡 启动时自动检测窗口是否在屏幕内：换电脑 / 改分辨率后不会"消失"，右键可一键"移至屏幕中央"
- 💾 配置自动保存、绿色单文件、免安装

## 运行方式

### 方式一：直接使用（推荐）
从 [Releases](../../releases) 下载 `桌面时钟.exe`，双击即可运行。无需安装 Python。

### 方式二：从源码运行
需要 **Python 3.10+**（Windows 上建议安装 `tzdata` 以提供完整时区数据库）：

```bash
pip install tzdata pillow
python desktop_clock.py
```

### 方式三：打包为 exe
```bash
pip install pyinstaller pillow tzdata
python icon_gen.py        # 生成 clock.ico（图标为二进制，不入库，需先执行一次）
pyinstaller DesktopClock.spec --noconfirm
```
生成的可执行文件位于 `dist/` 目录。

## 操作说明

| 操作 | 说明 |
| --- | --- |
| 左键按住表盘拖动 | 移动时钟位置 |
| 拖动右下角区域 | 调整表盘大小 |
| 双击表盘 | 打开设置 |
| 右键表盘 | 功能菜单：设置 / 透明度 / 大小 / 主题 / 锁定 / 置顶 / 移至屏幕中央 / 添加·删除时钟 / 退出 |

## 项目结构

```
desktop_clock/
├── desktop_clock.py        # 主程序（单文件，全部功能）
├── DesktopClock.spec       # PyInstaller 打包配置
├── icon_gen.py             # 生成 clock.ico 图标的脚本
├── 使用说明.txt             # 用户使用手册
├── README.md
└── .gitignore
```

> 注：`clock.ico` 是二进制图标文件，不入库；克隆后先运行 `python icon_gen.py` 生成。

## 依赖

- Python 3.10+（标准库：`tkinter`、`zoneinfo`）
- `tzdata`：Windows 下的 IANA 时区数据（运行必需）
- `Pillow`：仅用于生成图标与自检截图（运行不需要）
- `PyInstaller`：仅用于打包（运行不需要）

## 配置说明

运行时会在 exe 同目录生成 `desktop_clock_config.json`（不可写时改用 `%APPDATA%\DesktopClock`），保存每个时钟的位置、大小、时区等设置；该文件为个人运行数据，已加入 `.gitignore`，不会提交。

## License

MIT
