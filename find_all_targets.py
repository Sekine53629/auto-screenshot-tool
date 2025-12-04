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

print('=' * 80)
print('全ての青緑系候補を探索（面積100px以上）')
print('=' * 80)
print(f'画像サイズ: {img.shape}\n')

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 青紫系の検出（薄め）
hsv_lower = np.array([100, 20, 180])  # 青紫、彩度低め（薄い色）
hsv_upper = np.array([140, 100, 255])  # 範囲広め
mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print(f'検出された輪郭数: {len(contours)}\n')

all_candidates = []
for contour in contours:
    area = cv2.contourArea(contour)
    if area < 100:  # 100px以上
        continue
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = w / h if h > 0 else 0

    # HSV平均値
    mask_single = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask_single, [contour], 0, 255, -1)
    mean_hsv = cv2.mean(hsv, mask=mask_single)[:3]
    mean_bgr = cv2.mean(img, mask=mask_single)[:3]

    all_candidates.append({
        'area': area,
        'aspect': aspect_ratio,
        'size': (w, h),
        'pos': (x, y),
        'hsv': mean_hsv,
        'bgr': mean_bgr
    })

# 面積順にソート
all_candidates.sort(key=lambda x: x['area'], reverse=True)

print(f'【青紫色（H:100-140, S:20-100, V≥180）の全候補】\n')

for i, c in enumerate(all_candidates[:20], 1):  # 上位20個
    print(f"候補{i}:")
    print(f"  面積: {c['area']:,.0f} px")
    print(f"  サイズ: {c['size'][0]} x {c['size'][1]} px")
    print(f"  アスペクト比: {c['aspect']:.2f}")
    print(f"  位置: x={c['pos'][0]}, y={c['pos'][1]} (右上からの距離: {2304-c['pos'][0]}px)")
    print(f"  平均HSV: H={c['hsv'][0]:.1f}, S={c['hsv'][1]:.1f}, V={c['hsv'][2]:.1f}")
    print(f"  平均BGR: {tuple(int(x) for x in c['bgr'])}")
    print()

if not all_candidates:
    print('青緑色の候補が1つも見つかりませんでした。')
    print('フォームは別の色かもしれません。')
