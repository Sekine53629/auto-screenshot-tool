# Auto Screenshot Tool

特定の色を検出して自動的にスクリーンショットを撮影するPythonプログラムです。

## 概要

このツールは、画面上に特定の色（枠やボックスなど）が表示されたときに自動的にスクリーンショットを撮影します。オンライン講義やプレゼンテーションのスライドを自動保存する際に便利です。

## 機能

- 指定した色（RGB/BGR）を画面から検出
- 検出後、指定時間待機してからスクリーンショットを撮影
- 色が消えた場合は撮影をキャンセル
- 連続撮影の防止（指定間隔を空ける）
- カーソル位置から色を取得するユーティリティツール付き

## 必要なライブラリ

```bash
pip install opencv-python pillow mss numpy pyautogui
```

## ファイル構成

- `auto_screenshot.py` - メインの自動スクリーンショットプログラム
- `get_color.py` - カーソル位置の色を取得するユーティリティ

## 使い方

### 1. 基本的な使用方法

```bash
python auto_screenshot.py
```

デフォルトでは、紫色のボックスを検出して撮影します。

### 2. 検出する色を変更する

#### 方法A: カーソル位置から色を取得

```bash
python get_color.py
```

1. Enterキーを押す
2. 5秒のカウントダウン中に、検出したい色の上にマウスを移動
3. 表示されたBGR値を`auto_screenshot.py`の設定に貼り付ける

#### 方法B: 直接色を指定

`auto_screenshot.py`を編集して、`target_color_bgr`の値を変更：

```python
auto_ss = AutoScreenshot(
    target_color_bgr=(0, 0, 255),  # 赤色 (B, G, R)
    color_tolerance=30,
    save_dir="C:/Users/YourName/Downloads/screenshot",
    check_interval=1.0
)
```

### 3. 設定のカスタマイズ

`auto_screenshot.py`の設定を変更できます：

| パラメータ | 説明 | デフォルト |
|-----------|------|-----------|
| `target_color_bgr` | 検出する色 (B, G, R) | `(182, 137, 136)` |
| `color_tolerance` | 色の許容範囲 | `30` |
| `save_dir` | 保存先ディレクトリ | `"C:/Users/imao3/Downloads/screenshot"` |
| `check_interval` | チェック間隔（秒） | `1.0` |

コード内の定数：
- **検出後の待機時間**: `auto_screenshot.py`の140行目 `elapsed >= 15.0` (15秒)
- **撮影間隔**: `auto_screenshot.py`の142行目 `> 60.0` (60秒)

### 4. 停止方法

`Ctrl + C` でプログラムを停止

## 色の指定例

BGR形式で色を指定します：

| 色 | BGR値 |
|----|-------|
| 赤 | `(0, 0, 255)` |
| 青 | `(255, 0, 0)` |
| 緑 | `(0, 255, 0)` |
| 白 | `(255, 255, 255)` |
| 黒 | `(0, 0, 0)` |
| 紫 | `(150, 100, 120)` |

## 動作フロー

1. 指定した色を検出 → メッセージ表示
2. 指定時間待機（デフォルト15秒）
3. 待機中も色が表示され続けている → スクリーンショット撮影
4. 待機中に色が消えた → 撮影キャンセル
5. 次の検出まで指定間隔（デフォルト60秒）待機

## 保存ファイル

スクリーンショットは以下の形式で保存されます：

```
screenshot_0001_20251116_143025.png
screenshot_0002_20251116_143045.png
...
```

## 注意事項

- Windows環境で開発・テストされています
- パスの指定は `/` (スラッシュ) を使用してください（`\` はエラーになります）
- 検出精度は`color_tolerance`の値で調整できます（大きいほど広範囲の色を検出）

## ライセンス

MIT License

## 作者

Created with Claude Code
