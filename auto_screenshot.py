#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動スクリーンショット撮影プログラム
特定の色の枠を検知して自動的にスクリーンショットを保存します
"""

import sys
import io
# Windows環境での文字化け対策
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import cv2
import numpy as np
from mss import mss
from PIL import Image
import time
import os
from datetime import datetime

class AutoScreenshot:
    # 状態定義
    STATE_WAITING = "waiting"              # フォーム表示を待機中
    STATE_DETECTING = "detecting"          # フォームを検出中（確認期間）
    STATE_CAPTURED = "captured"            # 撮影完了、消失を待機中
    STATE_COOLDOWN = "cooldown"            # 再検出防止のクールダウン中

    def __init__(self,
                 target_color_hsv_range=None,  # HSV色範囲 [(H_min, S_min, V_min), (H_max, S_max, V_max)]
                 min_area=25000,               # 最小面積（ピクセル）
                 max_area=None,                # 最大面積（ピクセル）None=無制限
                 aspect_ratio_range=(0.8, 6.0), # アスペクト比範囲（幅/高さ）
                 detection_time=2.0,           # 検出確認時間（秒）
                 disappear_check_time=1.0,     # 消失確認時間（秒）
                 cooldown_time=3.0,            # クールダウン時間（秒）
                 save_dir="screenshots",
                 capture_region=None,
                 check_interval=0.5):
        """
        Args:
            target_color_hsv_range: 検出する色範囲 [(H_min, S_min, V_min), (H_max, S_max, V_max)]
            min_area: 検出する最小面積（ピクセル）
            max_area: 検出する最大面積（ピクセル）None=無制限
            aspect_ratio_range: 検出する形状のアスペクト比範囲
            detection_time: フォームが表示され続ける時間（秒）を確認してから撮影
            disappear_check_time: フォームが消えたことを確認する時間（秒）
            cooldown_time: 撮影後の再検出防止期間（秒）
            save_dir: 保存先ディレクトリ
            capture_region: キャプチャする領域 {"top": y, "left": x, "width": w, "height": h}
            check_interval: チェック間隔（秒）
        """
        # デフォルトの色範囲（青緑系）
        if target_color_hsv_range is None:
            self.hsv_lower = np.array([100, 30, 180])  # 青緑の下限
            self.hsv_upper = np.array([130, 70, 255])  # 青緑の上限
        else:
            self.hsv_lower = np.array(target_color_hsv_range[0])
            self.hsv_upper = np.array(target_color_hsv_range[1])

        self.min_area = min_area
        self.max_area = max_area
        self.aspect_ratio_range = aspect_ratio_range
        self.detection_time = detection_time
        self.disappear_check_time = disappear_check_time
        self.cooldown_time = cooldown_time
        self.save_dir = save_dir
        self.capture_region = capture_region
        self.check_interval = check_interval

        # 状態管理
        self.state = self.STATE_WAITING
        self.state_start_time = time.time()
        self.screenshot_count = 0
        self.detection_start_time = None
        self.disappear_start_time = None

        # 一時停止フラグ
        self.is_paused = False
        self.stop_requested = False
        self.cancel_capture_requested = False

        # GUI（オプショナル）
        self.gui = None

        # 保存先ディレクトリを作成
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    def detect_target_form(self, image):
        """
        画像内に指定の色と形状のフォームがあるかを検出
        横バー検出方式：フォーム上下の固定バーのみを検出し、中のテキストボックスの影響を受けない

        Args:
            image: numpy配列の画像データ (BGR)

        Returns:
            tuple: (検出されたか, 検出された輪郭情報のリスト, デバッグ情報)
        """
        # HSV色空間に変換
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 色範囲でマスク作成
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)

        # モルフォロジー処理で細い線を除去（オプション）
        # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 輪郭を検出
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 条件に合う輪郭を検索
        detected_forms = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # 面積チェック（最小）
            if area < self.min_area:
                continue

            # 面積チェック（最大）
            if self.max_area is not None and area > self.max_area:
                continue

            # バウンディングボックスを取得
            x, y, w, h = cv2.boundingRect(contour)

            # アスペクト比チェック
            aspect_ratio = w / h if h > 0 else 0
            if not (self.aspect_ratio_range[0] <= aspect_ratio <= self.aspect_ratio_range[1]):
                continue

            # 横バー検出による追加検証
            # ROI内で横方向に広がる青紫バーの存在を確認
            roi_mask = mask[y:y+h, x:x+w]
            y_counts = np.sum(roi_mask > 0, axis=1)
            threshold_width = w * 0.7  # 幅の70%以上が青紫

            # 横バーの検出（連続する行をグループ化）
            horizontal_bars = []
            for row_idx in range(len(y_counts)):
                if y_counts[row_idx] >= threshold_width:
                    horizontal_bars.append(row_idx)

            if not horizontal_bars:
                continue  # 横バーがない場合はスキップ

            # 連続する行をグループ化
            bar_groups = []
            current_group = [horizontal_bars[0]]

            for row_idx in horizontal_bars[1:]:
                if row_idx == current_group[-1] + 1:
                    current_group.append(row_idx)
                else:
                    bar_groups.append(current_group)
                    current_group = [row_idx]
            bar_groups.append(current_group)

            # 高さ10px以上の太いバーのみを抽出
            thick_bars = [group for group in bar_groups if len(group) >= 10]

            # 上下に2つ以上の太いバーがあることを確認（フォームの上下バー）
            if len(thick_bars) < 2:
                continue

            # 上端と下端のバーの位置を確認
            top_bar = thick_bars[0]
            bottom_bar = thick_bars[-1]
            bar_distance = bottom_bar[0] - top_bar[-1]

            # 上下バー間の距離が妥当か（50px以上、フォームの高さとして妥当）
            if bar_distance < 50:
                continue

            # 条件を満たすフォームを記録
            detected_forms.append({
                'contour': contour,
                'area': area,
                'bbox': (x, y, w, h),
                'aspect_ratio': aspect_ratio,
                'bar_count': len(thick_bars),
                'bar_distance': bar_distance
            })

        # デバッグ情報
        debug_info = {
            'total_contours': len(contours),
            'matched_forms': len(detected_forms),
            'color_pixels': cv2.countNonZero(mask)
        }

        is_detected = len(detected_forms) > 0

        return is_detected, detected_forms, debug_info

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
        print(f"[OK] スクリーンショット保存: {filename}")

        # GUIを更新
        if self.gui:
            self.gui.update_counter(self.screenshot_count)
            self.gui.flash_capture()

        # 音を鳴らす（オプション）
        try:
            import winsound
            winsound.Beep(1000, 200)  # 1000Hz, 200ms
        except:
            pass

        return filename

    def change_state(self, new_state, info=""):
        """状態を変更"""
        self.state = new_state
        self.state_start_time = time.time()

        # GUIを更新
        if self.gui:
            self.gui.update_state(new_state, info)

    def on_pause_toggle(self, is_paused):
        """一時停止/再開のコールバック"""
        self.is_paused = is_paused
        if is_paused:
            print("\n[⏸] 一時停止中...")
        else:
            print("\n[▶] 再開しました")

    def on_stop_request(self):
        """停止ボタンが押されたときのコールバック"""
        print("\n[⏹] 停止リクエストを受信")
        self.stop_requested = True

    def on_cancel_request(self):
        """キャンセルボタンが押されたときのコールバック"""
        print("\n[✕] 撮影キャンセルリクエストを受信")
        self.cancel_capture_requested = True

    def run(self, duration=None, use_gui=True):
        """
        自動スクリーンショット撮影を開始（状態遷移ベース）

        Args:
            duration: 実行時間（秒）。Noneの場合は無限に実行
            use_gui: GUIを使用するかどうか
        """
        print("=" * 70)
        print("自動スクリーンショット撮影プログラム（状態遷移型）")
        print("=" * 70)
        print(f"検出色範囲 (HSV): {self.hsv_lower} 〜 {self.hsv_upper}")
        print(f"面積範囲: {self.min_area:,} 〜 {self.max_area:,} ピクセル" if self.max_area else f"最小面積: {self.min_area:,} ピクセル")
        print(f"アスペクト比範囲: {self.aspect_ratio_range}")
        print(f"検出確認時間: {self.detection_time}秒")
        print(f"消失確認時間: {self.disappear_check_time}秒")
        print(f"クールダウン時間: {self.cooldown_time}秒")
        print(f"保存先: {self.save_dir}/")
        print(f"チェック間隔: {self.check_interval}秒")
        print("\n状態遷移:")
        print("  待機中 → 検出中 → 撮影完了 → 消失待機 → クールダウン → 待機中")
        print("\nGUIウィンドウで操作可能" if use_gui else "\nCtrl+C で停止")
        print("=" * 70)

        # GUIを起動
        if use_gui:
            try:
                from overlay_gui import OverlayGUI
                self.gui = OverlayGUI(
                    on_pause_callback=self.on_pause_toggle,
                    on_stop_callback=self.on_stop_request,
                    on_cancel_callback=self.on_cancel_request
                )
                self.gui.start()
                time.sleep(0.5)  # GUI初期化待ち
                print("✓ GUIウィンドウを起動しました")
            except Exception as e:
                print(f"⚠ GUI起動に失敗: {e}")
                print("コンソールモードで続行します")
                self.gui = None

        start_time = time.time()

        try:
            while True:
                # 停止リクエストチェック
                if self.stop_requested:
                    break

                # 実行時間チェック
                if duration and (time.time() - start_time) > duration:
                    break

                # 一時停止中はスキップ
                if self.is_paused:
                    time.sleep(self.check_interval)
                    continue

                # 画面をキャプチャ
                img_pil, img_cv = self.capture_screen()

                # フォームを検出
                is_detected, detected_forms, debug_info = self.detect_target_form(img_cv)
                current_time = time.time()
                timestamp = datetime.now().strftime("%H:%M:%S")

                # 状態別の処理
                if self.state == self.STATE_WAITING:
                    # 待機中：フォームの出現を待つ
                    if is_detected:
                        info = f"{self.detection_time}秒間確認します"
                        self.change_state(self.STATE_DETECTING, info)
                        self.detection_start_time = current_time
                        print(f"\n[{timestamp}] フォーム検出！ {info}")
                    else:
                        info = f"色px: {debug_info['color_pixels']:,} | 輪郭: {debug_info['total_contours']}"
                        if self.gui:
                            self.gui.update_state('waiting', info)
                        print(f"[{timestamp}] [待機中] {info}", end='\r')

                elif self.state == self.STATE_DETECTING:
                    # 検出中：一定時間フォームが表示され続けることを確認
                    elapsed = current_time - self.detection_start_time

                    # キャンセルリクエストをチェック
                    if self.cancel_capture_requested:
                        print(f"\n[{timestamp}] ✕ ユーザーが撮影をキャンセルしました")
                        self.cancel_capture_requested = False
                        self.change_state(self.STATE_WAITING, "")
                    elif is_detected:
                        remaining = self.detection_time - elapsed
                        if remaining > 0:
                            forms_info = f"{len(detected_forms)}個" if detected_forms else "0個"
                            info = f"撮影まであと {remaining:.1f}秒 | フォーム: {forms_info}"
                            if self.gui:
                                self.gui.update_state('detecting', info)
                            print(f"[{timestamp}] [検出中] {info}", end='\r')
                        else:
                            # 撮影実行
                            print(f"\n[{timestamp}] ✓ 撮影実行！")
                            self.save_screenshot(img_pil)
                            self.change_state(self.STATE_CAPTURED, "フォームの消失を待機中")
                            self.disappear_start_time = None
                    else:
                        # 検出が途切れた
                        print(f"\n[{timestamp}] ✗ フォームが消えました（撮影キャンセル）")
                        self.change_state(self.STATE_WAITING, "")

                elif self.state == self.STATE_CAPTURED:
                    # 撮影完了：フォームが消えるのを待つ
                    if not is_detected:
                        # フォームが消え始めた
                        if self.disappear_start_time is None:
                            self.disappear_start_time = current_time
                            print(f"[{timestamp}] フォームが消え始めました。{self.disappear_check_time}秒間確認します...")

                        elapsed_disappear = current_time - self.disappear_start_time
                        remaining = self.disappear_check_time - elapsed_disappear
                        if elapsed_disappear >= self.disappear_check_time:
                            # 完全に消えたことを確認
                            print(f"[{timestamp}] ✓ フォームの消失を確認。クールダウン開始...")
                            self.change_state(self.STATE_COOLDOWN, f"{self.cooldown_time}秒")
                        else:
                            info = f"消失確認中 あと {remaining:.1f}秒"
                            if self.gui:
                                self.gui.update_state('captured', info)
                            print(f"[{timestamp}] [消失確認中] {info}", end='\r')
                    else:
                        # フォームが再び検出された（消失タイマーをリセット）
                        if self.disappear_start_time is not None:
                            print(f"\n[{timestamp}] ⚠ フォームが再検出されました（消失タイマーリセット）")
                        self.disappear_start_time = None
                        forms_info = f"{len(detected_forms)}個" if detected_forms else "0個"
                        info = f"フォーム: {forms_info}"
                        if self.gui:
                            self.gui.update_state('captured', info)
                        print(f"[{timestamp}] [消失待機中] {info}", end='\r')

                elif self.state == self.STATE_COOLDOWN:
                    # クールダウン：再検出を防ぐための待機期間
                    elapsed_cooldown = current_time - self.state_start_time
                    remaining_cooldown = self.cooldown_time - elapsed_cooldown

                    if remaining_cooldown > 0:
                        info = f"あと {remaining_cooldown:.1f}秒"
                        if self.gui:
                            self.gui.update_state('cooldown', info)
                        print(f"[{timestamp}] [クールダウン] {info}", end='\r')
                    else:
                        print(f"\n[{timestamp}] クールダウン終了。次の検出待機に戻ります。")
                        self.change_state(self.STATE_WAITING, "")

                # 待機
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n" + "=" * 70)
            print("停止しました")
            print(f"合計 {self.screenshot_count} 枚のスクリーンショットを保存しました")
            print("=" * 70)
        finally:
            # GUIをクリーンアップ
            if self.gui:
                self.gui.destroy()
                print("GUI終了")


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

    # オプション1: 分析結果に基づいた設定（青緑系のフォーム検出）
    # 実測値: screenshot_0001 - H=117.6, S=57.6, V=195.1, 面積=85,920px, アスペクト比=5.42
    # 重要: 白色領域（H=3-4, S=0-5）と他の要素を除外するため、条件を最適化
    auto_ss = AutoScreenshot(
        target_color_hsv_range=[(110, 40, 180), (125, 255, 255)],  # 青紫色（H=119中心、S≥40で白を除外）
        min_area=30000,              # 最小面積 30,000px（実測39,260pxの約76%、余裕を持たせる）
        max_area=200000,             # 最大面積 200,000px（大きな白領域を除外）
        aspect_ratio_range=(1.0, 2.0),  # アスペクト比 1.0〜2.0（実測1.37を含む、正方形〜やや横長）
        detection_time=2.0,          # 2秒間表示を確認してから撮影
        disappear_check_time=1.5,    # 1.5秒間消失を確認（より確実に）
        cooldown_time=3.0,           # 3秒間のクールダウン
        save_dir="C:/Users/imao3/Downloads/screenshot",
        check_interval=0.5           # 0.5秒ごとにチェック
    )

    # オプション2: カスタム設定例（より厳格な条件）
    # auto_ss = AutoScreenshot(
    #     target_color_hsv_range=[(115, 40, 190), (125, 60, 220)],  # より狭い色範囲
    #     min_area=35000,              # より大きな面積
    #     aspect_ratio_range=(1.3, 1.4),  # より狭いアスペクト比範囲
    #     detection_time=3.0,          # 3秒間表示を確認
    #     disappear_check_time=2.0,    # 2秒間消失を確認
    #     cooldown_time=5.0,           # 5秒間のクールダウン
    #     save_dir="screenshots",
    #     check_interval=0.3
    # )

    # 実行
    auto_ss.run()
