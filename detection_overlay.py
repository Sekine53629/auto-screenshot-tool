#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検出枠オーバーレイ - 検出されたフォームの周りに枠を表示
"""

import cv2
import numpy as np
from mss import mss
import threading
import time


class DetectionOverlay:
    """画面上に検出枠を表示するオーバーレイ"""

    def __init__(self, color_detecting=(0, 255, 0), color_ready=(0, 0, 255), thickness=4):
        """
        Args:
            color_detecting: 検出中の枠の色 (BGR) デフォルト: 黄緑
            color_ready: 撮影準備完了の枠の色 (BGR) デフォルト: 赤
            thickness: 枠の太さ
        """
        self.color_detecting = color_detecting
        self.color_ready = color_ready
        self.thickness = thickness

        # 表示中の枠情報
        self.detected_forms = []
        self.is_ready_to_capture = False
        self.is_running = False
        self.overlay_thread = None
        self.window_name = "Detection Overlay"

    def start(self):
        """オーバーレイ表示を開始"""
        if self.is_running:
            return

        self.is_running = True
        self.overlay_thread = threading.Thread(target=self._run_overlay, daemon=True)
        self.overlay_thread.start()

    def stop(self):
        """オーバーレイ表示を停止"""
        self.is_running = False
        if self.overlay_thread:
            self.overlay_thread.join(timeout=1)
        cv2.destroyAllWindows()

    def update(self, detected_forms, is_ready_to_capture=False):
        """
        検出情報を更新

        Args:
            detected_forms: 検出されたフォーム情報のリスト
            is_ready_to_capture: 撮影準備完了フラグ
        """
        self.detected_forms = detected_forms
        self.is_ready_to_capture = is_ready_to_capture

    def _run_overlay(self):
        """オーバーレイを描画するスレッド"""
        # ウィンドウを作成
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_TOPMOST, 1)

        with mss() as sct:
            monitor = sct.monitors[1]  # メインモニター

            while self.is_running:
                # 画面をキャプチャ
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                # 検出された枠を描画
                if self.detected_forms:
                    color = self.color_ready if self.is_ready_to_capture else self.color_detecting

                    for form in self.detected_forms:
                        bbox = form['bbox']
                        x, y, w, h = bbox

                        # 枠を描画
                        cv2.rectangle(img, (x, y), (x + w, y + h), color, self.thickness)

                        # 情報テキストを描画
                        area = form['area']
                        aspect_ratio = form['aspect_ratio']
                        text = f"Area: {area:.0f}px | Ratio: {aspect_ratio:.2f}"

                        # テキスト背景
                        (text_width, text_height), _ = cv2.getTextSize(
                            text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                        )
                        cv2.rectangle(
                            img,
                            (x, y - text_height - 10),
                            (x + text_width + 10, y),
                            color,
                            -1
                        )

                        # テキスト
                        cv2.putText(
                            img,
                            text,
                            (x + 5, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 255),
                            2
                        )

                        # 撮影準備完了の場合は中央に大きく表示
                        if self.is_ready_to_capture:
                            center_text = "READY TO CAPTURE"
                            (ct_width, ct_height), _ = cv2.getTextSize(
                                center_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 4
                            )
                            center_x = (img.shape[1] - ct_width) // 2
                            center_y = (img.shape[0] + ct_height) // 2

                            # 背景
                            cv2.rectangle(
                                img,
                                (center_x - 20, center_y - ct_height - 20),
                                (center_x + ct_width + 20, center_y + 20),
                                self.color_ready,
                                -1
                            )

                            # テキスト
                            cv2.putText(
                                img,
                                center_text,
                                (center_x, center_y),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                2,
                                (255, 255, 255),
                                4
                            )

                # 透明度を調整（元の画面を透けさせる）
                # 実際には完全に透明にはできないので、枠だけを描画した透明画像を作成
                overlay = np.zeros_like(img)

                if self.detected_forms:
                    color = self.color_ready if self.is_ready_to_capture else self.color_detecting

                    for form in self.detected_forms:
                        bbox = form['bbox']
                        x, y, w, h = bbox
                        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, self.thickness)

                        # テキスト情報
                        area = form['area']
                        aspect_ratio = form['aspect_ratio']
                        text = f"Area: {area:.0f}px | Ratio: {aspect_ratio:.2f}"

                        (text_width, text_height), _ = cv2.getTextSize(
                            text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                        )
                        cv2.rectangle(
                            overlay,
                            (x, y - text_height - 10),
                            (x + text_width + 10, y),
                            color,
                            -1
                        )
                        cv2.putText(
                            overlay,
                            text,
                            (x + 5, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 255),
                            2
                        )

                # 黒背景に枠だけを表示
                cv2.imshow(self.window_name, overlay)

                # ESCキーで終了
                if cv2.waitKey(50) & 0xFF == 27:
                    self.is_running = False
                    break

        cv2.destroyAllWindows()


# テスト用
if __name__ == "__main__":
    overlay = DetectionOverlay()
    overlay.start()

    # テスト：枠を表示
    test_forms = [
        {
            'bbox': (100, 100, 300, 200),
            'area': 60000,
            'aspect_ratio': 1.5
        }
    ]

    for i in range(100):
        is_ready = (i % 10) >= 7  # 7秒後に赤く変わる
        overlay.update(test_forms, is_ready_to_capture=is_ready)
        time.sleep(0.5)

    overlay.stop()
    print("テスト終了")
