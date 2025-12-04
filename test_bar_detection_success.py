#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
横バー検出ロジックのテスト
"""
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import cv2
import numpy as np

# テスト画像
img = cv2.imread('C:/Users/imao3/Documents/GitHub/auto-screenshot-tool/success_example.png')

print('=' * 80)
print('横バー検出テスト')
print('=' * 80)

# HSV変換
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 青紫マスク
hsv_lower = np.array([110, 40, 180])
hsv_upper = np.array([125, 255, 255])
mask = cv2.inRange(hsv, hsv_lower, hsv_upper)

# 輪郭検出
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print(f'検出された輪郭数: {len(contours)}\n')

# 設定
min_area = 30000
max_area = 200000
aspect_ratio_range = (1.0, 2.0)

for i, contour in enumerate(contours, 1):
    area = cv2.contourArea(contour)

    if area < min_area:
        continue

    if max_area is not None and area > max_area:
        continue

    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = w / h if h > 0 else 0

    if not (aspect_ratio_range[0] <= aspect_ratio <= aspect_ratio_range[1]):
        continue

    print(f'候補{i}:')
    print(f'  位置: ({x}, {y})')
    print(f'  サイズ: {w} x {h} px')
    print(f'  面積: {area:.0f} px')
    print(f'  アスペクト比: {aspect_ratio:.2f}')

    # 横バー検出
    roi_mask = mask[y:y+h, x:x+w]
    y_counts = np.sum(roi_mask > 0, axis=1)
    threshold_width = w * 0.7

    horizontal_bars = []
    for row_idx in range(len(y_counts)):
        if y_counts[row_idx] >= threshold_width:
            horizontal_bars.append(row_idx)

    if not horizontal_bars:
        print('  → 横バーなし、スキップ')
        continue

    # グループ化
    bar_groups = []
    current_group = [horizontal_bars[0]]

    for row_idx in horizontal_bars[1:]:
        if row_idx == current_group[-1] + 1:
            current_group.append(row_idx)
        else:
            bar_groups.append(current_group)
            current_group = [row_idx]
    bar_groups.append(current_group)

    # 太いバー抽出
    thick_bars = [group for group in bar_groups if len(group) >= 10]

    print(f'  横バーグループ数: {len(bar_groups)}')
    print(f'  太いバー数（≥10px）: {len(thick_bars)}')

    for j, bar in enumerate(thick_bars, 1):
        print(f'    バー{j}: Y={bar[0]}〜{bar[-1]}, 高さ={len(bar)}px')

    if len(thick_bars) < 2:
        print('  → 太いバーが2つ未満、スキップ')
        continue

    top_bar = thick_bars[0]
    bottom_bar = thick_bars[-1]
    bar_distance = bottom_bar[0] - top_bar[-1]

    print(f'  上下バー間距離: {bar_distance}px')

    if bar_distance < 50:
        print('  → バー間距離が50px未満、スキップ')
        continue

    print('  ✓ 検出成功！')
    print(f'  バー数: {len(thick_bars)}, 上下距離: {bar_distance}px')
