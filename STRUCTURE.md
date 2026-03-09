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
├── docs/
│   ├── issues/                  # Issue関連ドキュメント
│   └── specs/                   # 仕様書
├── README.md                    # プロジェクト概要
└── STRUCTURE.md                 # 本ドキュメント（ファイル構成）
```

## Cursor Agentへの指示

### 重要ルール
- 新規ファイルは必ず本ドキュメントの構成に従って配置すること
- **既存ファイルは削除しないこと**
- **`.cursor/` ディレクトリは削除しないこと**
- **`docs/issues/` ディレクトリは削除しないこと**
- **`docs/specs/` ディレクトリは削除しないこと**
- 新しいディレクトリが必要な場合は本ドキュメントを更新すること

## 更新履歴
- 2026-03-09: 初期構成を記載
