# -*- coding: utf-8 -*-
"""生成程序图标 clock.ico（与打包所用的图标一致）。

GitHub 文本推送不支持二进制文件，故图标不直接入库；
运行本脚本即可在项目根目录重新生成 clock.ico。

用法：
    pip install pillow
    python icon_gen.py
"""
import math
import os

from PIL import Image, ImageDraw

S = 256
CX = CY = S // 2
R = S // 2 - 6


def _draw(img):
    d = ImageDraw.Draw(img)
    # 表盘底（白底 + 灰描边）
    d.ellipse([CX - R, CY - R, CX + R, CY + R],
              fill=(255, 255, 255, 255), outline=(40, 40, 40, 255), width=4)
    # 60 个刻度
    for i in range(60):
        a = math.radians(i * 6)
        sx, sy = math.sin(a), -math.cos(a)
        outer = (CX + (R - 8) * sx, CY + (R - 8) * sy)
        if i % 5 == 0:
            inner = (CX + (R - 24) * sx, CY + (R - 24) * sy)
            d.line([inner, outer], fill=(30, 30, 30, 255), width=4)
        else:
            inner = (CX + (R - 14) * sx, CY + (R - 14) * sy)
            d.line([inner, outer], fill=(130, 130, 130, 255), width=2)
    # 时针（约 10 点）与分针（约 2 点）
    def hand(deg, length, width, color):
        a = math.radians(deg)
        sx, sy = math.sin(a), -math.cos(a)
        tip = (CX + length * sx, CY + length * sy)
        back = (CX - length * 0.18 * sx, CY + length * 0.18 * sy)
        d.line([back, tip], fill=color, width=width)
    hand(300, R * 0.52, 16, (35, 35, 35, 255))   # 时针
    hand(60, R * 0.80, 10, (35, 35, 35, 255))    # 分针
    # 中心红点
    cr = R * 0.075
    d.ellipse([CX - cr, CY - cr, CX + cr, CY + cr], fill=(230, 60, 60, 255))
    return img


def main():
    img = _draw(Image.new("RGBA", (S, S), (0, 0, 0, 0)))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clock.ico")
    img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("clock.ico generated ->", out)


if __name__ == "__main__":
    main()
