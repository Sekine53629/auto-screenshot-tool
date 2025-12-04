#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
様々な検出設定をテストして最適なパラメータを見つける
"""

import sys
import io
# Windows環境での文字化け対策
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import cv2
import numpy as np

img_path = 'C:/Users/imao3/Downloads/screenshot/screenshot_0001_20251205_002905.png'
img = cv2.imread(img_path)

if img is None:
    print(f"画像を読み込めませんでした: {img_path}")
    exit(1)

print(f'画像サイズ: {img.shape}')
print('=' * 80)

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 様々な設定をテスト
configs = [
    ('現在の設定', (110, 40, 180), (125, 255, 255), 50000, 500000, (3.0, 7.0)),
    ('面積を下げた設定', (110, 40, 180), (125, 255, 255), 30000, 500000, (3.0, 7.0)),
    ('さらに面積を下げる', (110, 40, 180), (125, 255, 255), 20000, 500000, (3.0, 7.0)),
    ('色範囲を広げる', (100, 30, 180), (130, 255, 255), 30000, 500000, (3.0, 7.0)),
    ('アスペクト比を緩和', (110, 40, 180), (125, 255, 255), 30000, 500000, (1.0, 10.0)),
    ('全て緩和', (100, 30, 180), (130, 255, 255), 25000, 500000, (1.0, 10.0)),
]

for name, hsv_lower, hsv_upper, min_area, max_area, aspect_range in configs:
    hsv_lower_arr = np.array(hsv_lower)
    hsv_upper_arr = np.array(hsv_upper)
    mask = cv2.inRange(hsv, hsv_lower_arr, hsv_upper_arr)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        if max_area and area > max_area:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h if h > 0 else 0
        if not (aspect_range[0] <= aspect_ratio <= aspect_range[1]):
            continue

        # HSV平均値を取得
        mask_single = np.zeros(img.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask_single, [contour], 0, 255, -1)
        mean_hsv = cv2.mean(hsv, mask=mask_single)[:3]

        detected.append({
            'area': area,
            'aspect': aspect_ratio,
            'size': (w, h),
            'pos': (x, y),
            'hsv': mean_hsv
        })

    print(f'\n【{name}】')
    print(f'  HSV範囲: H={hsv_lower[0]}-{hsv_upper[0]}, S={hsv_lower[1]}-{hsv_upper[1]}, V={hsv_lower[2]}-{hsv_upper[2]}')
    print(f'  面積範囲: {min_area:,} ~ {max_area:,} px')
    print(f'  アスペクト比: {aspect_range[0]} ~ {aspect_range[1]}')
    print(f'  ✓ 検出数: {len(detected)}個')

    if detected:
        for i, d in enumerate(detected, 1):
            print(f'    [{i}] 面積={d["area"]:,.0f}px, アスペクト比={d["aspect"]:.2f}')
            print(f'        サイズ={d["size"][0]}x{d["size"][1]}px, 位置=({d["pos"][0]}, {d["pos"][1]})')
            print(f'        平均HSV: H={d["hsv"][0]:.1f}, S={d["hsv"][1]:.1f}, V={d["hsv"][2]:.1f}')
    else:
        print('    ✗ フォームが検出されませんでした')

print('\n' + '=' * 80)
print('結論と推奨設定')
print('=' * 80)
