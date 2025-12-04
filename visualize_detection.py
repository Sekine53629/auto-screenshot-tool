#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import cv2
import numpy as np

# OneDriveのスクリーンショットを分析
img_path = 'C:/Users/imao3/Documents/GitHub/auto-screenshot-tool/temp_test.png'
img = cv2.imread(img_path)

if img is None:
    print(f"画像を読み込めませんでした: {img_path}")
    exit(1)

print('検出範囲の可視化')
print(f'画像サイズ: {img.shape}')

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 現在の設定
hsv_lower = np.array([110, 40, 180])
hsv_upper = np.array([125, 255, 255])
mask = cv2.inRange(hsv, hsv_lower, hsv_upper)

# 輪郭検出
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 可視化用に元画像をコピー
output = img.copy()

print(f'\n検出された輪郭数: {len(contours)}')

for i, contour in enumerate(contours):
    area = cv2.contourArea(contour)
    if area < 100:
        continue

    x, y, w, h = cv2.boundingRect(contour)
    aspect = w / h if h > 0 else 0

    # HSV平均値
    mask_single = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask_single, [contour], 0, 255, -1)
    mean_hsv = cv2.mean(hsv, mask=mask_single)[:3]

    # 矩形を描画（緑色）
    cv2.rectangle(output, (x, y), (x+w, y+h), (0, 255, 0), 3)

    # テキスト情報
    text = f"#{i+1} {w}x{h} ({area:.0f}px)"
    cv2.putText(output, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    print(f'\n候補{i+1}:')
    print(f'  位置: ({x}, {y})')
    print(f'  サイズ: {w} x {h} px')
    print(f'  面積: {area:.0f} px')
    print(f'  アスペクト比: {aspect:.2f}')
    print(f'  平均HSV: H={mean_hsv[0]:.1f}, S={mean_hsv[1]:.1f}, V={mean_hsv[2]:.1f}')

# 保存
output_path = 'C:/Users/imao3/Documents/GitHub/auto-screenshot-tool/detected_regions.png'
cv2.imwrite(output_path, output)
print(f'\n可視化結果を保存: {output_path}')
