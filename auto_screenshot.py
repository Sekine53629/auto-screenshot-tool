#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動スクリーンショット撮影プログラム
特定の色の枠を検知して自動的にスクリーンショットを保存します
"""

import cv2
import numpy as np
from mss import mss
from PIL import Image
import time
import os
from datetime import datetime

class AutoScreenshot:
    def __init__(self,
                 target_color_bgr=(0, 0, 255),  # BGR形式 デフォルトは赤
                 color_tolerance=30,
                 save_dir="screenshots",
                 capture_region=None,  # None=フルスクリーン, またはタプル(x, y, width, height)
                 check_interval=0.5):  # 0.5秒ごとにチェック
        """
        Args:
            target_color_bgr: 検出する色 (B, G, R) 0-255
            color_tolerance: 色の許容範囲
            save_dir: 保存先ディレクトリ
            capture_region: キャプチャする領域 {"top": y, "left": x, "width": w, "height": h}
            check_interval: チェック間隔（秒）
        """
        self.target_color = np.array(target_color_bgr)
        self.color_tolerance = color_tolerance
        self.save_dir = save_dir
        self.capture_region = capture_region
        self.check_interval = check_interval
        self.last_detection_time = 0
        self.screenshot_count = 0
        self.first_detection_time = None  # 最初に検出した時刻

        # 保存先ディレクトリを作成
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    def detect_color_frame(self, image):
        """
        画像内に指定色の枠があるかを検出

        Args:
            image: numpy配列の画像データ (BGR)

        Returns:
            bool: 枠が検出されたらTrue
        """
        # 色範囲を定義
        lower_bound = np.maximum(self.target_color - self.color_tolerance, 0)
        upper_bound = np.minimum(self.target_color + self.color_tolerance, 255)

        # 指定色の範囲内のピクセルをマスク
        mask = cv2.inRange(image, lower_bound, upper_bound)

        # マスク内のピクセル数をカウント
        color_pixels = cv2.countNonZero(mask)

        # 画像の端（枠部分）のみを検査するオプション
        # 画像全体の5%以上が指定色なら検出とみなす（調整可能）
        height, width = image.shape[:2]
        total_pixels = height * width

        # 枠として検出する閾値（全体の0.1%以上）
        threshold = total_pixels * 0.001

        return color_pixels > threshold

    def capture_screen(self):
        """画面をキャプチャして返す"""
        with mss() as sct:
            if self.capture_region:
                monitor = self.capture_region
            else:
                monitor = sct.monitors[1]  # メインモニター

            screenshot = sct.grab(monitor)
            # PIL Imageに変換
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            # OpenCV形式(BGR)に変換
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            return img, img_cv

    def save_screenshot(self, image):
        """スクリーンショットを保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.screenshot_count += 1
        filename = f"{self.save_dir}/screenshot_{self.screenshot_count:04d}_{timestamp}.png"
        image.save(filename)
        print(f"✓ スクリーンショット保存: {filename}")
        return filename

    def run(self, duration=None):
        """
        自動スクリーンショット撮影を開始

        Args:
            duration: 実行時間（秒）。Noneの場合は無限に実行
        """
        print("=" * 60)
        print("自動スクリーンショット撮影プログラム")
        print("=" * 60)
        print(f"検出色 (BGR): {self.target_color}")
        print(f"色許容範囲: ±{self.color_tolerance}")
        print(f"保存先: {self.save_dir}/")
        print(f"チェック間隔: {self.check_interval}秒")
        print("Ctrl+C で停止")
        print("=" * 60)

        start_time = time.time()
        last_detected = False

        try:
            while True:
                # 実行時間チェック
                if duration and (time.time() - start_time) > duration:
                    break

                # 画面をキャプチャ
                img_pil, img_cv = self.capture_screen()

                # 色の枠を検出
                is_detected = self.detect_color_frame(img_cv)
                current_time = time.time()

                # 検出ロジック：検出してから15秒後に撮影
                if is_detected:
                    if not last_detected:
                        # 新しく検出された
                        self.first_detection_time = current_time
                        print(f"検出！ 15秒後に撮影します...")
                    elif self.first_detection_time is not None:
                        # 検出が継続中
                        elapsed = current_time - self.first_detection_time
                        if elapsed >= 15.0:  # 15秒経過
                            # 前回の撮影から60秒以上経過していれば撮影
                            if current_time - self.last_detection_time > 60.0:
                                self.save_screenshot(img_pil)
                                self.last_detection_time = current_time
                            self.first_detection_time = None  # リセット
                else:
                    # 検出されなくなった（撮影前に色が消えた）
                    if self.first_detection_time is not None and last_detected:
                        print(f"✗ 撮影キャンセル（色が消えました）")
                    self.first_detection_time = None

                last_detected = is_detected

                # 待機
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n" + "=" * 60)
            print("停止しました")
            print(f"合計 {self.screenshot_count} 枚のスクリーンショットを保存しました")
            print("=" * 60)


def get_color_at_cursor():
    """
    マウスカーソル位置の色を取得するユーティリティ関数
    """
    import pyautogui

    print("マウスカーソルを目的の色の上に置いて Enter を押してください...")
    input()

    x, y = pyautogui.position()
    screenshot = pyautogui.screenshot()
    rgb = screenshot.getpixel((x, y))
    bgr = (rgb[2], rgb[1], rgb[0])  # RGB -> BGR

    print(f"カーソル位置 ({x}, {y}) の色:")
    print(f"  RGB: {rgb}")
    print(f"  BGR: {bgr}")
    print(f"\n使用するコード:")
    print(f"  target_color_bgr={bgr}")

    return bgr


if __name__ == "__main__":
    # 使用例

    # オプション1: 青いバーを検出（推奨）
    auto_ss = AutoScreenshot(
        target_color_bgr=(182, 137, 136),
        color_tolerance=30,
        save_dir="C:/Users/imao3/Downloads/screenshot",
        check_interval=1.0  # 1秒ごとにチェック（遅くした）
    )

    # オプション2: 紫色のキーワードボックスを検出
    # auto_ss = AutoScreenshot(
    #     target_color_bgr=(150, 100, 120),  # 紫 (BGR)
    #     color_tolerance=35,
    #     save_dir="lecture_screenshots",
    #     check_interval=0.3
    # )

    # オプション2: カーソル位置から色を取得
    # color = get_color_at_cursor()
    # auto_ss = AutoScreenshot(target_color_bgr=color)

    # 実行
    auto_ss.run()
