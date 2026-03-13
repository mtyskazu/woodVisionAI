# Phase 1: 撮像・照明環境の確立 — 実装サマリー

**作成日**: 2026-03-09
**最終更新**: 2026-03-09
**ステータス**: カメラ接続・テスト撮像完了（照明比較テスト待ち）

---

## 実装内容

### プロジェクト基盤

| ファイル | 役割 |
|---|---|
| `pyproject.toml` | プロジェクト定義・依存関係・ビルド設定 |
| `requirements.txt` | pip依存パッケージ（IDS SDK・PyTorchのインストール手順付き）|
| `.gitignore` | `data/`・`__pycache__/` 等を除外に追加 |

### ソースコード（`src/woodvisionai/`）

#### `config.py` — システム設定の一元管理

- `CameraConfig`: IDS GV-50C0CP の解像度・露光・トリガー設定
- `OpticsConfig`: WD=240mm, FOV=200×126mm, 分解能0.103mm/pixel
- `ConveyorConfig`: 搬送速度10m/min, 材最大長4000mm
- `SystemConfig`: 全設定の統合（フレーム数計算プロパティ付き）

#### `camera/ids_camera.py` — IDS Peak SDK ラッパー

- コンテキストマネージャによるリソース安全管理（`with IDSCamera.open(config) as cam:`）
- フリーラン / ハードウェアトリガー（エンコーダ同期）両対応
- BayerRG8 → RGB変換、numpy配列としてフレーム返却
- SDK未インストール時の検出とエラーメッセージ

#### `camera/capture.py` — キャプチャスレッド

- `CaptureThread`: デーモンスレッドで連続撮像、`Queue` で後段にフレーム配信
- `CapturedFrame`: フレームID・タイムスタンプ付きデータコンテナ
- CLIエントリーポイント: `woodvisionai-capture` コマンドでテスト撮像

### 検証ツール（`tools/`）

#### `lighting_comparison.py` — 照明比較ツール

- 白色/赤色 × 拡散板有無 の4条件を定量評価
- 評価メトリクス: 輝度, コントラスト(RMS), ハレーション率, SNR, エッジ鮮鋭度(Laplacian)
- CSV出力 + コンソールレポート + 最適条件の推奨表示

### Phase 2・3 準備

- `inference/`, `communication/`, `transform/`, `gui/` のパッケージ骨格を作成済み

---

## ファイル一覧

```
src/woodvisionai/
├── __init__.py
├── config.py
├── camera/
│   ├── __init__.py
│   ├── ids_camera.py
│   └── capture.py
├── inference/__init__.py
├── communication/__init__.py
├── transform/__init__.py
└── gui/__init__.py

tools/
├── __init__.py
└── lighting_comparison.py

tests/
└── __init__.py
```

---

## 環境検証結果（2026-03-09）

### wood_ai Conda 環境

| パッケージ | バージョン | 状態 |
|---|---|---|
| Python | 3.12.12 | OK |
| ids_peak (IDS Peak SDK) | 1.14.0 | OK |
| ids_peak_ipl | 1.17.1 | OK |
| PyTorch | 2.10.0+cu130 | OK |
| CUDA / RTX 4060 Laptop GPU | 8.0 GB VRAM | OK |
| OpenCV | 4.13.0 | OK |
| ultralytics (YOLO) | 8.4.19 | OK |
| PySide6 | 6.10.2 | OK |

### カメラ接続テスト

| 項目 | 値 |
|---|---|
| モデル | IDS GV-50CxCP-C |
| シリアル | 4104520310 |
| インターフェース | GigE Vision (Ethernet) |
| 解像度 | 1920 × 1200 |
| PixelFormat | BayerRG8 |
| 露光時間 | 34422.8 µs |

### テスト撮像結果

| 項目 | 値 |
|---|---|
| 画像サイズ | (1200, 1920, 3) |
| 平均輝度 | 54.8 |
| 輝度標準偏差 | 59.1 |
| 保存先 | `data/captures/test_20260309_173444.png` |

---

## 次のステップ: 照明比較テストの準備

### 必要な準備物

| 準備物 | 用途 | 必須 |
|---|---|---|
| **木材サンプル** | 節・腐れが含まれる実材（コントラスト評価対象） | はい |
| **OPB-X 照明** | 白色（W）/ 赤色（R）の比較 | はい |
| **拡散板 DF80** | 反射抑制効果の確認（透過率80%） | はい |
| **照明コントローラ** | OPPX-6012P2 (12V/60W パラレル2CH) | はい |

### 木材サンプル選定の目安

- **節あり**: 生節（黒〜暗褐色）と死節（抜けかけ）の両方が望ましい
- **腐れあり**: 表面に変色・軟化が見える部分
- **正常部**: 比較基準として必要
- **サイズ**: 幅150mm 前後の材（FOV 200mmでカバーできる範囲）

### 照明比較テストの手順

1. 各条件で同一サンプルを撮像し、以下のフォルダに配置:
   - `data/lighting_test/white_no_diffuser/`
   - `data/lighting_test/white_with_diffuser/`
   - `data/lighting_test/red_no_diffuser/`
   - `data/lighting_test/red_with_diffuser/`
2. `python tools/lighting_comparison.py` で定量評価を実行
3. 評価メトリクス（輝度, コントラスト, ハレーション率, SNR, エッジ鮮鋭度）に基づき照明条件を決定

### Phase 2 への準備（照明確定後）

| 準備 | 内容 | 目安数量 |
|---|---|---|
| **撮像データ収集** | 確定した照明条件で、さまざまな節・腐れの画像を撮影 | 最低 200〜500 枚 |
| **アノテーション環境** | バウンディングボックス付与ツール（Roboflow, CVAT, LabelImg 等） | — |
| **ラベル定義** | クラス: `knot`（節）, `rot`（腐れ） | 2クラス |
