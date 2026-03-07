# woodVisionAI - フォーム管理アプリケーション

フォームの入力内容を MongoDB に保存し、キャンセルで変更前の状態に戻す Web アプリケーションです。

## 技術スタック

| 層 | 技術 |
|---|---|
| フロントエンド | React.js |
| バックエンド | Node.js / Express.js |
| データベース | MongoDB |

## ディレクトリ構成

```
/project-root
├── /client            # フロントエンド (React)
│   ├── /src
│   │   ├── /components
│   │   │   └── FormComponent.js
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   └── package.json
├── /server            # バックエンド (Express)
│   ├── /models
│   │   └── FormDataModel.js
│   ├── /routes
│   │   └── formRoutes.js
│   ├── server.js
│   └── package.json
└── README.md
```

## セットアップ

### 前提条件

- Node.js 18 以上
- MongoDB が起動していること

### バックエンド

```bash
cd server
npm install
npm run dev
```

サーバーが `http://localhost:5000` で起動します。

環境変数でカスタマイズできます:

| 変数 | デフォルト値 | 説明 |
|---|---|---|
| `PORT` | `5000` | サーバーポート |
| `MONGO_URI` | `mongodb://localhost:27017/woodVisionAI` | MongoDB 接続文字列 |

### フロントエンド

```bash
cd client
npm install
npm start
```

開発サーバーが `http://localhost:3000` で起動します。

## API エンドポイント

### `POST /api/form/save`

フォームデータを保存します。`id` を含めると既存データを更新します。

**リクエストボディ:**
```json
{
  "id": "(任意) 既存データのID",
  "field1": "入力内容1",
  "field2": "入力内容2"
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "_id": "自動生成ID",
    "field1": "入力内容1",
    "field2": "入力内容2",
    "createdAt": "2026-03-07T...",
    "updatedAt": "2026-03-07T..."
  }
}
```

### `GET /api/form/retrieve`

保存済みのフォームデータを取得します。

**クエリパラメータ:**
- `id` (任意): 特定のデータを取得する場合に指定

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "_id": "...",
    "field1": "入力内容1",
    "field2": "入力内容2",
    "createdAt": "...",
    "updatedAt": "..."
  }
}
```
