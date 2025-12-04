#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
実際のスクリーンショットで検出テスト
"""
import cv2
from auto_screenshot import AutoScreenshot

# AutoScreenshotインスタンスを作成
auto_ss = AutoScreenshot(
    target_color_hsv_range=[(110, 40, 180), (125, 255, 255)],
    min_area=30000,
    max_area=200000,
    aspect_ratio_range=(1.0, 2.0),
    detection_time=2.0,
    disappear_check_time=1.5,
    cooldown_time=3.0,
    save_dir="C:/Users/imao3/Downloads/screenshot",
    check_interval=0.5
)

# テスト画像を読み込み
test_image = cv2.imread('C:/Users/imao3/Documents/GitHub/auto-screenshot-tool/temp_test.png')

print('=' * 80)
print('実際のスクリーンショットで検出テスト')
print('=' * 80)
print(f'画像サイズ: {test_image.shape}\n')

# 検出実行
is_detected, forms, debug_info = auto_ss.detect_target_form(test_image)

print(f'検出結果: {is_detected}')
print(f'検出されたフォーム数: {len(forms)}')
print(f'デバッグ情報:')
print(f'  総輪郭数: {debug_info["total_contours"]}')
print(f'  マッチしたフォーム: {debug_info["matched_forms"]}')
print(f'  色ピクセル数: {debug_info["color_pixels"]}')

if forms:
    print(f'\nフォーム詳細:')
    for i, form in enumerate(forms, 1):
        x, y, w, h = form['bbox']
        print(f'  フォーム{i}:')
        print(f'    位置: ({x}, {y})')
        print(f'    サイズ: {w} x {h} px')
        print(f'    面積: {form["area"]:.0f} px')
        print(f'    アスペクト比: {form["aspect_ratio"]:.2f}')
        print(f'    バー数: {form["bar_count"]}')
        print(f'    上下バー間距離: {form["bar_distance"]}px')
else:
    print('\nフォームが検出されませんでした')
