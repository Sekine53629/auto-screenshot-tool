#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import cv2
import numpy as np

img = cv2.imread('C:/Users/imao3/Documents/GitHub/auto-screenshot-tool/temp_test.png')
roi = img[140:313, 2041:2278]  # フォーム領域を切り出し
hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

# 青紫のマスク
mask_purple = cv2.inRange(hsv_roi, np.array([110, 40, 180]), np.array([125, 255, 255]))

# Y座標ごとの青紫ピクセル数をカウント
y_counts = np.sum(mask_purple > 0, axis=1)

# 横バーの検出（幅の80%以上が青紫）
threshold_width = roi.shape[1] * 0.8
horizontal_bars = []

for y in range(len(y_counts)):
    if y_counts[y] >= threshold_width:
        horizontal_bars.append(y)

print(f'フォーム内の青紫横バー（幅の80%以上）:')
print(f'総行数: {len(horizontal_bars)}')

# 連続する行をグループ化
if horizontal_bars:
    groups = []
    current_group = [horizontal_bars[0]]

    for y in horizontal_bars[1:]:
        if y == current_group[-1] + 1:
            current_group.append(y)
        else:
            groups.append(current_group)
            current_group = [y]
    groups.append(current_group)

    print(f'\n横バーのグループ数: {len(groups)}')
    for i, group in enumerate(groups, 1):
        y_start = group[0]
        y_end = group[-1]
        height = len(group)
        print(f'  バー{i}: Y={y_start}〜{y_end}, 高さ={height}px')

# 可視化
output = roi.copy()
for y in horizontal_bars:
    cv2.line(output, (0, y), (roi.shape[1]-1, y), (0, 255, 0), 1)

cv2.imwrite('C:/Users/imao3/Documents/GitHub/auto-screenshot-tool/purple_bars_visualization.png', output)
print(f'\n可視化結果を保存: purple_bars_visualization.png')
