#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
複数のスクリーンショットからフォーム形状を統計分析
"""

import cv2
import numpy as np
import sys

# 最新の複数のスクリーンショットを分析
files = [
    'C:/Users/imao3/Downloads/screenshot/screenshot_0001_20251205_002905.png',
    'C:/Users/imao3/Downloads/screenshot/screenshot_0002_20251205_003151.png',
    'C:/Users/imao3/Downloads/screenshot/screenshot_0003_20251205_003216.png',
    'C:/Users/imao3/Downloads/screenshot/screenshot_0004_20251205_003232.png',
    'C:/Users/imao3/Downloads/screenshot/screenshot_0005_20251205_003250.png',
    'C:/Users/imao3/Downloads/screenshot/screenshot_0006_20251205_003315.png'
]

print('=' * 80)
print('複数のスクリーンショットからフォーム形状を分析')
print('=' * 80)

all_forms = []

for img_path in files:
    try:
        img = cv2.imread(img_path)
        if img is None:
            print(f"読み込めませんでした: {img_path}")
            continue

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 青緑系の色範囲で検出
        hsv_lower = np.array([100, 30, 180])
        hsv_upper = np.array([130, 70, 255])
        mask = cv2.inRange(hsv, hsv_lower, hsv_upper)

        # 輪郭を検出
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 面積でフィルタリング
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 10000:  # 小さい輪郭は無視
                continue

            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0

            # HSV平均値も取得
            mask_single = np.zeros(img.shape[:2], dtype=np.uint8)
            cv2.drawContours(mask_single, [contour], 0, 255, -1)
            mean_hsv = cv2.mean(hsv, mask=mask_single)[:3]

            # フォーム情報を記録
            all_forms.append({
                'file': img_path.split('/')[-1],
                'area': area,
                'width': w,
                'height': h,
                'aspect_ratio': aspect_ratio,
                'x': x,
                'y': y,
                'mean_h': mean_hsv[0],
                'mean_s': mean_hsv[1],
                'mean_v': mean_hsv[2]
            })

    except Exception as e:
        print(f'エラー ({img_path}): {e}')
        continue

# 統計情報を計算
if all_forms:
    print(f'\n検出されたフォーム数: {len(all_forms)}')
    print('\n' + '=' * 80)
    print('個別フォーム詳細:')
    print('=' * 80)

    for i, form in enumerate(all_forms, 1):
        print(f"\n[{i}] {form['file']}")
        print(f"  位置: ({form['x']}, {form['y']})")
        print(f"  サイズ: {form['width']} x {form['height']} px")
        print(f"  面積: {form['area']:,.0f} px")
        print(f"  アスペクト比: {form['aspect_ratio']:.2f}")
        print(f"  平均HSV: H={form['mean_h']:.1f}, S={form['mean_s']:.1f}, V={form['mean_v']:.1f}")

    # 統計サマリー
    areas = [f['area'] for f in all_forms]
    widths = [f['width'] for f in all_forms]
    heights = [f['height'] for f in all_forms]
    ratios = [f['aspect_ratio'] for f in all_forms]
    h_values = [f['mean_h'] for f in all_forms]
    s_values = [f['mean_s'] for f in all_forms]
    v_values = [f['mean_v'] for f in all_forms]

    print('\n' + '=' * 80)
    print('統計サマリー:')
    print('=' * 80)
    print(f"\n面積:")
    print(f"  最小: {min(areas):,.0f} px")
    print(f"  最大: {max(areas):,.0f} px")
    print(f"  平均: {np.mean(areas):,.0f} px")
    print(f"  中央値: {np.median(areas):,.0f} px")
    print(f"  標準偏差: {np.std(areas):,.0f} px")

    print(f"\nアスペクト比 (幅/高さ):")
    print(f"  最小: {min(ratios):.2f}")
    print(f"  最大: {max(ratios):.2f}")
    print(f"  平均: {np.mean(ratios):.2f}")
    print(f"  中央値: {np.median(ratios):.2f}")
    print(f"  標準偏差: {np.std(ratios):.2f}")

    print(f"\n幅:")
    print(f"  最小: {min(widths)} px")
    print(f"  最大: {max(widths)} px")
    print(f"  平均: {np.mean(widths):.0f} px")

    print(f"\n高さ:")
    print(f"  最小: {min(heights)} px")
    print(f"  最大: {max(heights)} px")
    print(f"  平均: {np.mean(heights):.0f} px")

    print(f"\nHSV色範囲:")
    print(f"  H: {min(h_values):.1f} 〜 {max(h_values):.1f} (平均: {np.mean(h_values):.1f})")
    print(f"  S: {min(s_values):.1f} 〜 {max(s_values):.1f} (平均: {np.mean(s_values):.1f})")
    print(f"  V: {min(v_values):.1f} 〜 {max(v_values):.1f} (平均: {np.mean(v_values):.1f})")

    # 推奨設定を提案
    print('\n' + '=' * 80)
    print('推奨設定:')
    print('=' * 80)

    recommended_min_area = int(min(areas) * 0.9)  # 最小値の90%
    recommended_max_ratio = max(ratios) * 1.15  # 最大値の115%
    recommended_min_ratio = min(ratios) * 0.85  # 最小値の85%

    # HSV範囲の推奨値（平均±標準偏差の1.5倍）
    h_min = max(0, int(min(h_values) - 5))
    h_max = min(180, int(max(h_values) + 5))
    s_min = max(0, int(min(s_values) - 10))
    s_max = min(255, int(max(s_values) + 10))
    v_min = max(0, int(min(v_values) - 20))
    v_max = 255

    print(f"\n# 推奨パラメータ（実測値ベース）")
    print(f"target_color_hsv_range=[({h_min}, {s_min}, {v_min}), ({h_max}, {s_max}, {v_max})]")
    print(f"min_area={recommended_min_area:,}")
    print(f"aspect_ratio_range=({recommended_min_ratio:.2f}, {recommended_max_ratio:.2f})")

    print(f"\n# より厳格な設定（誤検出を最小化）")
    strict_min_area = int(np.median(areas) * 0.8)
    strict_min_ratio = np.median(ratios) * 0.9
    strict_max_ratio = np.median(ratios) * 1.1
    print(f"min_area={strict_min_area:,}")
    print(f"aspect_ratio_range=({strict_min_ratio:.2f}, {strict_max_ratio:.2f})")

else:
    print('フォームが検出されませんでした')
