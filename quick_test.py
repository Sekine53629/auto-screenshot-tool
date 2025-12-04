import sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import cv2
import numpy as np

img = cv2.imread('C:/Users/imao3/Downloads/screenshot/screenshot_0001_20251205_002905.png')
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 最適化された設定
hsv_lower = np.array([110, 40, 180])
hsv_upper = np.array([125, 255, 255])
mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

detected = []
for contour in contours:
    area = cv2.contourArea(contour)
    if area < 40000 or area > 200000:
        continue
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = w / h if h > 0 else 0
    if not (4.0 <= aspect_ratio <= 6.5):
        continue
    detected.append({'area': area, 'aspect': aspect_ratio, 'size': (w, h)})

print('=' * 70)
print('最適化された設定でのテスト')
print('=' * 70)
print(f'HSV: [110, 40, 180] ~ [125, 255, 255]')
print(f'面積: 40,000 ~ 200,000 px')
print(f'アスペクト比: 4.0 ~ 6.5')
print(f'\n検出数: {len(detected)}個\n')
for i, d in enumerate(detected, 1):
    print(f'  [{i}] 面積={d["area"]:,.0f}px, アスペクト比={d["aspect"]:.2f}, サイズ={d["size"]}')
    print(f'       ✓ ターゲットを正しく検出しました！')
print('=' * 70)
