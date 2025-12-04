import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# 画像を読み込み
img_path = "target_form.png"
img = cv2.imread(img_path)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

print(f"画像サイズ: {img.shape}")

# HSV色空間に変換して色の範囲を検出
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 複数の色範囲を定義して検出
# 青色系
blue_lower = np.array([100, 50, 50])
blue_upper = np.array([130, 255, 255])
blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)

# 水色/シアン系
cyan_lower = np.array([80, 50, 50])
cyan_upper = np.array([100, 255, 255])
cyan_mask = cv2.inRange(hsv, cyan_lower, cyan_upper)

# 緑色系
green_lower = np.array([40, 50, 50])
green_upper = np.array([80, 255, 255])
green_mask = cv2.inRange(hsv, green_lower, green_upper)

# 黄色系
yellow_lower = np.array([20, 50, 50])
yellow_upper = np.array([40, 255, 255])
yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)

# 赤色系（2範囲）
red_lower1 = np.array([0, 50, 50])
red_upper1 = np.array([10, 255, 255])
red_lower2 = np.array([170, 50, 50])
red_upper2 = np.array([180, 255, 255])
red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
red_mask = cv2.bitwise_or(red_mask1, red_mask2)

# すべてのマスクを統合
combined_mask = cv2.bitwise_or(blue_mask, cyan_mask)
combined_mask = cv2.bitwise_or(combined_mask, green_mask)
combined_mask = cv2.bitwise_or(combined_mask, yellow_mask)
combined_mask = cv2.bitwise_or(combined_mask, red_mask)

# 輪郭を検出
contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 面積でフィルタリング（小さすぎる輪郭を除外）
min_area = 1000
filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

print(f"検出された輪郭数: {len(filtered_contours)}")

# 検出結果を描画
result_img = img_rgb.copy()
cv2.drawContours(result_img, filtered_contours, -1, (255, 0, 0), 3)

# 各輪郭の情報を表示
for i, cnt in enumerate(sorted(filtered_contours, key=cv2.contourArea, reverse=True)[:10]):
    area = cv2.contourArea(cnt)
    x, y, w, h = cv2.boundingRect(cnt)
    print(f"輪郭 {i+1}: 面積={area:.0f}, 位置=({x}, {y}), サイズ=({w}x{h})")

    # バウンディングボックスを描画
    cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(result_img, f"#{i+1}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

# 結果を保存
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

axes[0, 0].imshow(img_rgb)
axes[0, 0].set_title('Original Image')
axes[0, 0].axis('off')

axes[0, 1].imshow(blue_mask, cmap='gray')
axes[0, 1].set_title('Blue Mask')
axes[0, 1].axis('off')

axes[0, 2].imshow(cyan_mask, cmap='gray')
axes[0, 2].set_title('Cyan Mask')
axes[0, 2].axis('off')

axes[1, 0].imshow(green_mask, cmap='gray')
axes[1, 0].set_title('Green Mask')
axes[1, 0].axis('off')

axes[1, 1].imshow(combined_mask, cmap='gray')
axes[1, 1].set_title('Combined Mask')
axes[1, 1].axis('off')

axes[1, 2].imshow(result_img)
axes[1, 2].set_title('Detected Contours')
axes[1, 2].axis('off')

plt.tight_layout()
plt.savefig('form_analysis_result.png', dpi=150, bbox_inches='tight')
print("\n分析結果を form_analysis_result.png に保存しました")

# 最も支配的な色を分析
# マスクされた領域のピクセル数をカウント
color_stats = {
    'blue': np.sum(blue_mask > 0),
    'cyan': np.sum(cyan_mask > 0),
    'green': np.sum(green_mask > 0),
    'yellow': np.sum(yellow_mask > 0),
    'red': np.sum(red_mask > 0)
}

print("\n色別ピクセル数:")
for color, count in sorted(color_stats.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"  {color}: {count} ピクセル")

# 最大の輪郭の色情報を取得
if filtered_contours:
    largest_contour = max(filtered_contours, key=cv2.contourArea)
    mask_largest = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask_largest, [largest_contour], 0, 255, -1)

    # 最大輪郭内の平均色を計算
    mean_color = cv2.mean(img, mask=mask_largest)[:3]
    mean_color_hsv = cv2.cvtColor(np.uint8([[mean_color]]), cv2.COLOR_BGR2HSV)[0][0]

    print(f"\n最大輪郭の平均色 (BGR): {mean_color}")
    print(f"最大輪郭の平均色 (HSV): {mean_color_hsv}")

plt.close()
