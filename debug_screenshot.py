#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スクリーンショットをデバッグして検出条件を確認
"""

import sys
import io
# Windows環境での文字化け対策
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import cv2
import numpy as np

if len(sys.argv) < 2:
    print("使い方: python debug_screenshot.py <画像ファイルパス>")
    sys.exit(1)

img_path = sys.argv[1]
# Windowsの日本語パス対応
try:
    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
except Exception as e:
    print(f"画像読み込みエラー: {e}")
    img = None

if img is None:
    print(f"画像を読み込めませんでした: {img_path}")
    sys.exit(1)

print(f"画像サイズ: {img.shape}")

# HSV変換
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 現在の設定
hsv_lower = np.array([100, 30, 180])
hsv_upper = np.array([130, 70, 255])

# マスク作成
mask = cv2.inRange(hsv, hsv_lower, hsv_upper)

# 輪郭検出
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print(f"\n=== 現在の設定 ===")
print(f"HSV下限: {hsv_lower}")
print(f"HSV上限: {hsv_upper}")
print(f"最小面積: 25,000 ピクセル")
print(f"アスペクト比範囲: 0.8 〜 6.0")

print(f"\n=== 検出結果 ===")
print(f"色にマッチしたピクセル数: {cv2.countNonZero(mask):,}")
print(f"検出された輪郭数: {len(contours)}")

# 条件を満たす輪郭を検索（フォーム内容の変化に対応した設定）
min_area = 25000
aspect_ratio_range = (0.8, 6.0)

matched_contours = []
large_contours = []
for i, contour in enumerate(contours):
    area = cv2.contourArea(contour)
    if area < 1000:  # 小さすぎる輪郭はスキップ
        continue

    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = w / h if h > 0 else 0

    matches_area = area >= min_area
    matches_ratio = aspect_ratio_range[0] <= aspect_ratio <= aspect_ratio_range[1]

    # 大きな輪郭は全て記録
    if area >= 10000:
        large_contours.append((i, area, x, y, w, h, aspect_ratio, matches_area, matches_ratio))

    # 条件を満たす輪郭を記録
    if matches_area and matches_ratio:
        matched_contours.append(contour)

# 大きな輪郭を面積順にソートして表示
large_contours.sort(key=lambda x: x[1], reverse=True)
print(f"\n大きな輪郭（面積10,000ピクセル以上）:")
for idx, area, x, y, w, h, aspect_ratio, matches_area, matches_ratio in large_contours[:20]:
    print(f"\n輪郭 {idx+1}:")
    print(f"  面積: {area:,.0f} px {'✓' if matches_area else '✗ (条件未満)'}")
    print(f"  位置: ({x}, {y})")
    print(f"  サイズ: {w}x{h}")
    print(f"  アスペクト比: {aspect_ratio:.2f} {'✓' if matches_ratio else '✗ (範囲外)'}")
    if matches_area and matches_ratio:
        print(f"  → ✓✓ 条件を満たしています！")

print(f"\n=== 最終結果 ===")
print(f"条件を満たす輪郭: {len(matched_contours)}個")

if len(matched_contours) == 0:
    print("\n⚠ フォームが検出されませんでした")
    print("\n推奨される調整:")

    # 最大の輪郭を確認
    if contours:
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        x, y, w, h = cv2.boundingRect(largest)
        aspect_ratio = w / h if h > 0 else 0

        print(f"\n最大の輪郭:")
        print(f"  面積: {area:,.0f} px")
        print(f"  アスペクト比: {aspect_ratio:.2f}")

        if area < min_area:
            print(f"\n→ min_area を {int(area * 0.8):,} に下げることを推奨")

        if not (aspect_ratio_range[0] <= aspect_ratio <= aspect_ratio_range[1]):
            new_lower = max(0.5, aspect_ratio - 0.3)
            new_upper = aspect_ratio + 0.3
            print(f"→ aspect_ratio_range を ({new_lower:.1f}, {new_upper:.1f}) に変更することを推奨")

    if cv2.countNonZero(mask) < 1000:
        print("\n→ 色範囲が狭すぎる可能性があります")
        print("→ HSV範囲を広げることを推奨:")
        print(f"   target_color_hsv_range=[({hsv_lower[0]-10}, {hsv_lower[1]-20}, {hsv_lower[2]-30}), ({hsv_upper[0]+10}, {hsv_upper[1]+30}, {hsv_upper[2]})]")

else:
    print("\n✓ フォームが正常に検出されました！")

# デバッグ画像を保存
debug_img = img.copy()
if matched_contours:
    cv2.drawContours(debug_img, matched_contours, -1, (0, 255, 0), 3)
    for cnt in matched_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 0, 255), 2)

cv2.imwrite("debug_result.png", debug_img)
cv2.imwrite("debug_mask.png", mask)
print(f"\nデバッグ画像を保存しました:")
print(f"  - debug_result.png (輪郭表示)")
print(f"  - debug_mask.png (マスク)")
