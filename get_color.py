#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
マウスカーソル位置の色を取得するツール
"""

import pyautogui
import time

print("=" * 60)
print("色取得ツール")
print("=" * 60)
print("使い方:")
print("1. 動画を開いて、検出したい色（紫の背景など）にマウスを合わせる")
print("2. このウィンドウに戻って Enter を押す")
print("=" * 60)

input("\n準備ができたら Enter を押してください...")

print("\n5秒後にカーソル位置の色を取得します...")
print("今のうちにマウスを目的の色の上に移動してください！")

for i in range(5, 0, -1):
    print(f"{i}...", end=" ", flush=True)
    time.sleep(1)

print("\n\n取得中...\n")

x, y = pyautogui.position()
screenshot = pyautogui.screenshot()
rgb = screenshot.getpixel((x, y))
bgr = (rgb[2], rgb[1], rgb[0])  # RGB -> BGR

print("=" * 60)
print(f"カーソル位置: ({x}, {y})")
print(f"RGB値: {rgb}")
print(f"BGR値: {bgr}")
print("=" * 60)
print("\n以下のコードを auto_screenshot.py に使用してください:\n")
print(f"target_color_bgr={bgr},")
print(f"color_tolerance=30,")
print("=" * 60)
