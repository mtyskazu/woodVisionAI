# プロジェクトファイル構成

## 概要
本ドキュメントはwoodVisionAIプロジェクトのファイル構成を定義します。
新機能追加・コード生成時は必ずこの構成に従ってください。

## ディレクトリ構成

```
woodVisionAI/
├── .cursor/
│   ├── instructions.md          # Cursor Agent 指示手順
│   └── mcp.json                 # MCP設定
├── .github/
│   └── ISSUE_TEMPLATE/
│       └── feature_request.md   # 機能リクエストテンプレート
├── src/
│   └── woodvisionai/            # メインパッケージ
│       ├── __init__.py
│       ├── config.py            # システム設定（光学・カメラ・搬送）
│       ├── camera/              # カメラ制御・画像取得
│       │   ├── __init__.py
│       │   ├── ids_camera.py    # IDS Peak SDK ラッパー
│       │   └── capture.py       # キャプチャスレッド
│       ├── inference/           # AI推論（Phase 2）
│       │   └── __init__.py
│       ├── communication/       # PLC通信（Phase 3）
│       │   └── __init__.py
│       ├── transform/           # 座標変換
│       │   └── __init__.py
│       └── gui/                 # PySide6 GUI
│           └── __init__.py
├── tools/
│   ├── __init__.py
│   ├── diagnose.py              # システム診断ツール
│   └── lighting_comparison.py   # 照明条件比較ツール
├── tests/
│   └── __init__.py
├── data/                        # 画像データ（Git管理外）
│   ├── captures/                # キャプチャ画像
│   └── lighting_test/           # 照明テスト画像
├── docs/
│   ├── issues/                  # Issue関連ドキュメント
│   ├── specs/                   # 仕様書
│   └── summaries/               # 実装サマリー（Phase単位の記録）
├── README.md                    # プロジェクト概要
├── STRUCTURE.md                 # 本ドキュメント（ファイル構成）
├── pyproject.toml               # プロジェクト設定・依存関係
└── requirements.txt             # pip依存パッケージ
```

## Cursor Agentへの指示

### 重要ルール
- 新規ファイルは必ず本ドキュメントの構成に従って配置すること
- **既存ファイルは削除しないこと**
- **`.cursor/` ディレクトリは削除しないこと**
- **`.github/` ディレクトリは削除しないこと**
- **`docs/issues/` ディレクトリは削除しないこと**
- **`docs/specs/` ディレクトリは削除しないこと**
- **`docs/summaries/` ディレクトリは削除しないこと**
- 新しいディレクトリが必要な場合は本ドキュメントを更新すること

## 更新履歴
- 2026-03-09: docs/summaries/ を追加（実装サマリーの追跡用）
- 2026-03-09: Phase 1 ソースコード構成を追加（camera, config, tools）
- 2026-03-09: 初期構成を記載
