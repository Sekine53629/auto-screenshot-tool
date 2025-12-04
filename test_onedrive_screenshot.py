#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import cv2
import numpy as np

# OneDriveのスクリーンショットを分析
img_path = 'temp_test.png'
img = cv2.imread(img_path)

if img is None:
    print(f"画像を読み込めませんでした: {img_path}")
    exit(1)

print('=' * 80)
print('OneDriveスクリーンショットの詳細分析')
print('=' * 80)
print(f'画像サイズ: {img.shape}\n')

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 幅広い範囲で検出して全ての候補を見る
hsv_lower = np.array([100, 30, 180])
hsv_upper = np.array([130, 255, 255])
mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print('【全ての検出候補】（面積1000px以上）')
all_candidates = []
for contour in contours:
    area = cv2.contourArea(contour)
    if area < 1000:
        continue
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = w / h if h > 0 else 0

    # HSV平均値
    mask_single = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask_single, [contour], 0, 255, -1)
    mean_hsv = cv2.mean(hsv, mask=mask_single)[:3]

    all_candidates.append({
        'area': area,
        'aspect': aspect_ratio,
        'size': (w, h),
        'pos': (x, y),
        'hsv': mean_hsv
    })

# 面積順にソート
all_candidates.sort(key=lambda x: x['area'], reverse=True)

for i, c in enumerate(all_candidates[:10], 1):  # 上位10個
    print(f"\n候補{i}:")
    print(f"  面積: {c['area']:,.0f} px")
    print(f"  サイズ: {c['size'][0]} x {c['size'][1]} px")
    print(f"  アスペクト比: {c['aspect']:.2f}")
    print(f"  位置: ({c['pos'][0]}, {c['pos'][1]})")
    print(f"  平均HSV: H={c['hsv'][0]:.1f}, S={c['hsv'][1]:.1f}, V={c['hsv'][2]:.1f}")

    # 現在の設定で検出されるか判定
    checks = []
    checks.append(('面積 ≥ 40000', c['area'] >= 40000))
    checks.append(('面積 ≤ 200000', c['area'] <= 200000))
    checks.append(('アスペクト比 ≥ 4.0', c['aspect'] >= 4.0))
    checks.append(('アスペクト比 ≤ 6.5', c['aspect'] <= 6.5))
    checks.append(('H: 110-125', 110 <= c['hsv'][0] <= 125))
    checks.append(('S: 40-255', c['hsv'][1] >= 40))

    passed = all(check[1] for check in checks)

    print(f"  判定:")
    for check_name, result in checks:
        status = '✓' if result else '✗'
        print(f"    {status} {check_name}")

    if passed:
        print(f"  → 現在の設定で検出されます")
    else:
        print(f"  → 現在の設定では検出されません")

print('\n' + '=' * 80)
print('推奨される設定変更')
print('=' * 80)

# ターゲットと思われる候補を特定（青緑色で横長）
targets = [c for c in all_candidates if 110 <= c['hsv'][0] <= 125 and c['hsv'][1] >= 40 and c['aspect'] >= 3.0]

if targets:
    print(f"\n青緑色の横長候補: {len(targets)}個")
    target = targets[0]  # 最大のもの
    print(f"\nターゲット候補:")
    print(f"  面積: {target['area']:,.0f} px")
    print(f"  アスペクト比: {target['aspect']:.2f}")

    # 推奨設定
    recommended_min_area = int(target['area'] * 0.8)
    recommended_max_area = int(target['area'] * 3.0)
    recommended_min_aspect = max(3.0, target['aspect'] - 2.0)
    recommended_max_aspect = target['aspect'] + 2.0

    print(f"\n推奨設定:")
    print(f"  min_area={recommended_min_area:,}  # {target['area']:,.0f}pxの80%")
    print(f"  max_area={recommended_max_area:,}  # {target['area']:,.0f}pxの300%")
    print(f"  aspect_ratio_range=({recommended_min_aspect:.1f}, {recommended_max_aspect:.1f})")
else:
    print("\n青緑色の横長候補が見つかりませんでした")
