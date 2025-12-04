#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
オーバーレイGUI - 常に最前面に表示されるステータスウィンドウ
"""

import tkinter as tk
from tkinter import ttk
import threading


class OverlayGUI:
    """画面上に常に表示される半透明ステータスウィンドウ"""

    def __init__(self, on_pause_callback=None, on_stop_callback=None, on_cancel_callback=None):
        """
        Args:
            on_pause_callback: 一時停止/再開ボタンが押されたときのコールバック
            on_stop_callback: 停止ボタンが押されたときのコールバック
            on_cancel_callback: キャンセルボタンが押されたときのコールバック
        """
        self.on_pause_callback = on_pause_callback
        self.on_stop_callback = on_stop_callback
        self.on_cancel_callback = on_cancel_callback
        self.is_paused = False
        self.root = None
        self.thread = None

        # 状態表示用の変数（Noneで初期化、GUI起動後に設定）
        self.state_text = None
        self.counter_text = None
        self.info_text = None
        self.cancel_button = None

        # 色定義
        self.colors = {
            'waiting': '#4CAF50',      # 緑 - 待機中
            'detecting': '#FFC107',    # 黄 - 検出中
            'captured': '#2196F3',     # 青 - 撮影完了
            'cooldown': '#9E9E9E',     # グレー - クールダウン
            'paused': '#FF5722'        # 赤 - 一時停止
        }
        self.current_color = self.colors['waiting']

    def start(self):
        """GUIを別スレッドで起動"""
        self.thread = threading.Thread(target=self._run_gui, daemon=True)
        self.thread.start()
        # スレッドが起動してGUIが初期化されるまで待機
        import time
        max_wait = 2.0  # 最大2秒待つ
        elapsed = 0
        while self.root is None and elapsed < max_wait:
            time.sleep(0.1)
            elapsed += 0.1

    def _run_gui(self):
        """GUI本体を実行"""
        try:
            self.root = tk.Tk()
            self.root.title("Auto Screenshot")

            # ウィンドウ設定
            window_width = 320
            window_height = 180

            # 画面右上に配置
            screen_width = self.root.winfo_screenwidth()
            x_position = screen_width - window_width - 20
            y_position = 20

            self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

            # 常に最前面に表示
            self.root.attributes('-topmost', True)

            # 半透明設定（0.0〜1.0）
            self.root.attributes('-alpha', 0.9)

            # ウィンドウを閉じるボタンを無効化
            self.root.protocol("WM_DELETE_WINDOW", self._on_close_attempt)

            # スタイル設定
            style = ttk.Style()
            style.theme_use('clam')
        except Exception as e:
            print(f"GUI初期化エラー: {e}")
            self.root = None
            return

        # StringVar を GUI スレッドで初期化
        self.state_text = tk.StringVar(value="初期化中...")
        self.counter_text = tk.StringVar(value="撮影枚数: 0")
        self.info_text = tk.StringVar(value="")

        # メインフレーム
        main_frame = tk.Frame(self.root, bg='#263238', padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # タイトル
        title_label = tk.Label(
            main_frame,
            text="🎥 Auto Screenshot",
            font=('Arial', 14, 'bold'),
            bg='#263238',
            fg='white'
        )
        title_label.pack(pady=(0, 10))

        # 状態インジケーター
        self.status_canvas = tk.Canvas(
            main_frame,
            width=280,
            height=30,
            bg='#263238',
            highlightthickness=0
        )
        self.status_canvas.pack(pady=(0, 5))

        self.status_indicator = self.status_canvas.create_rectangle(
            10, 5, 270, 25,
            fill=self.current_color,
            outline='white',
            width=2
        )

        self.status_text_item = self.status_canvas.create_text(
            140, 15,
            text="待機中",
            font=('Arial', 10, 'bold'),
            fill='white'
        )

        # 撮影枚数
        counter_label = tk.Label(
            main_frame,
            textvariable=self.counter_text,
            font=('Arial', 11),
            bg='#263238',
            fg='#B0BEC5'
        )
        counter_label.pack(pady=(5, 5))

        # 詳細情報
        info_label = tk.Label(
            main_frame,
            textvariable=self.info_text,
            font=('Arial', 9),
            bg='#263238',
            fg='#78909C'
        )
        info_label.pack(pady=(0, 10))

        # ボタンフレーム
        button_frame = tk.Frame(main_frame, bg='#263238')
        button_frame.pack(pady=(5, 0))

        # 一時停止/再開ボタン
        self.pause_button = tk.Button(
            button_frame,
            text="⏸ 一時停止",
            font=('Arial', 9),
            bg='#FFC107',
            fg='black',
            activebackground='#FFD54F',
            relief=tk.RAISED,
            bd=2,
            padx=10,
            pady=5,
            command=self._on_pause_clicked
        )
        self.pause_button.pack(side=tk.LEFT, padx=3)

        # キャンセルボタン（初期は非表示）
        self.cancel_button = tk.Button(
            button_frame,
            text="✕ キャンセル",
            font=('Arial', 9, 'bold'),
            bg='#FF9800',
            fg='white',
            activebackground='#FFB74D',
            relief=tk.RAISED,
            bd=2,
            padx=10,
            pady=5,
            command=self._on_cancel_clicked
        )
        # 初期は非表示
        # self.cancel_button.pack(side=tk.LEFT, padx=3)

        # 停止ボタン
        stop_button = tk.Button(
            button_frame,
            text="⏹ 停止",
            font=('Arial', 9),
            bg='#F44336',
            fg='white',
            activebackground='#E57373',
            relief=tk.RAISED,
            bd=2,
            padx=10,
            pady=5,
            command=self._on_stop_clicked
        )
        stop_button.pack(side=tk.LEFT, padx=3)

        # GUIループ開始
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"GUI実行エラー: {e}")

    def update_state(self, state, info=""):
        """
        状態を更新

        Args:
            state: 状態名 ('waiting', 'detecting', 'captured', 'cooldown', 'paused')
            info: 追加情報（残り時間など）
        """
        if not self.root:
            return

        state_names = {
            'waiting': '待機中',
            'detecting': '検出中',
            'captured': '撮影完了',
            'cooldown': 'クールダウン',
            'paused': '一時停止'
        }

        state_display = state_names.get(state, state)
        self.state_text.set(state_display)

        # 色を更新
        color = self.colors.get(state, self.colors['waiting'])

        try:
            self.status_canvas.itemconfig(self.status_indicator, fill=color)
            self.status_canvas.itemconfig(self.status_text_item, text=state_display)
            self.info_text.set(info)

            # 検出中のみキャンセルボタンを表示
            if state == 'detecting' and self.cancel_button:
                self.cancel_button.pack(side=tk.LEFT, padx=3, before=self.pause_button.master.winfo_children()[-1])
            elif self.cancel_button:
                self.cancel_button.pack_forget()

        except:
            pass

    def update_counter(self, count):
        """撮影枚数を更新"""
        if not self.root:
            return
        self.counter_text.set(f"撮影枚数: {count}")

    def flash_capture(self):
        """撮影時に画面をフラッシュ"""
        if not self.root:
            return

        def flash():
            try:
                # 白くフラッシュ
                self.status_canvas.itemconfig(self.status_indicator, fill='white')
                self.root.after(100, lambda: self.status_canvas.itemconfig(
                    self.status_indicator, fill=self.colors['captured']
                ))
            except:
                pass

        self.root.after(0, flash)

    def _on_pause_clicked(self):
        """一時停止/再開ボタンがクリックされた"""
        self.is_paused = not self.is_paused

        if self.is_paused:
            self.pause_button.config(text="▶ 再開", bg='#4CAF50')
            self.update_state('paused', '一時停止中')
        else:
            self.pause_button.config(text="⏸ 一時停止", bg='#FFC107')

        if self.on_pause_callback:
            self.on_pause_callback(self.is_paused)

    def _on_cancel_clicked(self):
        """キャンセルボタンがクリックされた"""
        if self.on_cancel_callback:
            self.on_cancel_callback()
        self.info_text.set("撮影をキャンセルしました")

    def _on_stop_clicked(self):
        """停止ボタンがクリックされた"""
        if self.on_stop_callback:
            self.on_stop_callback()

        if self.root:
            self.root.quit()
            self.root.destroy()

    def _on_close_attempt(self):
        """ウィンドウを閉じようとした時"""
        # 閉じるボタンでは閉じず、停止ボタンを使わせる
        self.info_text.set("停止するには「停止」ボタンを押してください")

    def destroy(self):
        """GUIを破棄"""
        if self.root:
            self.root.quit()
            self.root.destroy()


# テスト用
if __name__ == "__main__":
    import random

    def on_pause(is_paused):
        print(f"一時停止: {is_paused}")

    def on_stop():
        print("停止しました")

    gui = OverlayGUI(on_pause_callback=on_pause, on_stop_callback=on_stop)
    gui.start()

    # テスト：状態を変化させる
    states = ['waiting', 'detecting', 'captured', 'cooldown']
    counter = 0

    time.sleep(1)

    for i in range(100):
        state = random.choice(states)
        info = f"テスト {i+1}"

        if state == 'detecting':
            info = f"撮影まであと {random.randint(1, 5)}秒"
        elif state == 'cooldown':
            info = f"クールダウン {random.randint(1, 3)}秒"

        gui.update_state(state, info)

        if state == 'captured':
            counter += 1
            gui.update_counter(counter)
            gui.flash_capture()

        time.sleep(2)

    print("テスト終了")
