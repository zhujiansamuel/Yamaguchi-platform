# Metabase データ可視化ツール セットアップガイド

## 概要

Metabase は、Data Platform のデータを可視化・分析するためのオープンソースBI（Business Intelligence）ツールです。

### 選定理由

| 比較項目 | Metabase | Superset |
|---------|----------|----------|
| 自托管難易度 | ⭐⭐⭐⭐⭐ 非常に簡単 | ⭐⭐⭐ やや複雑 |
| 表示柔軟性 | ⭐⭐⭐ 中程度 | ⭐⭐⭐⭐⭐ 非常に高い |
| 学習コスト | 低い（非技術者も使用可能） | 高い（SQL知識必要） |
| リソース消費 | 低い（512MB RAM〜） | 高い（2GB RAM〜） |
| Docker展開 | 単一コンテナ | 複数サービス必要 |

**結論**: 自托管の簡便さとリソース効率を重視し、Metabase を採用

## クイックスタート

### 1. 環境変数の設定

`.env` ファイルに以下を追加（オプション）：

```bash
# Metabase専用データベース名（デフォルト: metabase）
METABASE_DB_NAME=metabase
```

### 2. サービスの起動

```bash
# 開発環境
docker compose up -d metabase

# 本番環境
docker compose -f docker-compose.prod.yml up -d metabase
```

### 3. 初期セットアップ

1. ブラウザで `http://localhost:3000` にアクセス
2. 初回起動時はセットアップウィザードが表示されます
3. 管理者アカウントを作成
4. Data Platform のデータベースを接続

## データベース接続設定

### Data Platform PostgreSQL への接続

Metabase セットアップウィザードまたは管理画面で以下を設定：

| 設定項目 | 値 |
|---------|-----|
| Database type | PostgreSQL |
| Host | `postgres` (Docker内部ネットワーク) |
| Port | `5432` |
| Database name | `data_platform` |
| Username | `${DB_USER}` (環境変数と同じ) |
| Password | `${DB_PASSWORD}` (環境変数と同じ) |

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Metabase   │    │   Django     │    │   Celery     │  │
│  │   :3000      │    │   :8000      │    │   Workers    │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             ▼                               │
│                    ┌──────────────┐                         │
│                    │  PostgreSQL  │                         │
│                    │   :5432      │                         │
│                    │              │                         │
│                    │ ┌──────────┐ │                         │
│                    │ │data_platf│ │  ← アプリケーションデータ │
│                    │ └──────────┘ │                         │
│                    │ ┌──────────┐ │                         │
│                    │ │ metabase │ │  ← Metabase設定データ    │
│                    │ └──────────┘ │                         │
│                    └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 推奨ダッシュボード

Data Platform のデータモデルに基づく推奨ダッシュボード：

### 1. 在庫管理ダッシュボード
- **テーブル**: `data_aggregation_inventory`, `data_aggregation_iphone`, `data_aggregation_ipad`
- **指標**:
  - 総在庫数（ソース別）
  - IMEI別在庫状況
  - ソフト削除されていないアクティブ在庫

### 2. 購買分析ダッシュボード
- **テーブル**: `data_aggregation_purchasing`
- **指標**:
  - 注文状況の推移
  - 仕入先別集計
  - コンフリクト発生状況

### 3. 決済追跡ダッシュボード
- **テーブル**: `data_aggregation_giftcard*`, `data_aggregation_debitcard*`, `data_aggregation_creditcard*`
- **指標**:
  - 支払い方法別集計
  - ギフトカード残高推移
  - 決済履歴

### 4. EC サイト分析
- **テーブル**: `data_aggregation_ecsite`
- **指標**:
  - サイト別注文数
  - 売上推移
  - 注文ステータス分布

### 5. メール処理状況
- **テーブル**: `data_aggregation_mail*`
- **指標**:
  - 受信メール数推移
  - ラベル別分類
  - 処理済み/未処理状況

## 運用管理

### ヘルスチェック

```bash
# Metabase の稼働状況確認
curl http://localhost:3000/api/health

# Docker コンテナ状態
docker compose ps metabase
```

### ログ確認

```bash
# ログをリアルタイム表示
docker compose logs -f metabase

# 直近100行のログ
docker compose logs --tail=100 metabase
```

### バックアップ

Metabase の設定（ダッシュボード、質問、ユーザーなど）は PostgreSQL の `metabase` データベースに保存されます。

```bash
# Metabase 設定のバックアップ
docker compose exec postgres pg_dump -U ${DB_USER} metabase > metabase_backup.sql

# リストア
cat metabase_backup.sql | docker compose exec -T postgres psql -U ${DB_USER} metabase
```

### リソース設定

#### 開発環境（docker-compose.yml）
```yaml
JAVA_OPTS: "-Xmx512m -Xms256m"
```

#### 本番環境（docker-compose.prod.yml）
```yaml
JAVA_OPTS: "-Xmx1g -Xms512m"
```

大量のデータを扱う場合は、必要に応じてメモリを増加してください。

## トラブルシューティング

### 起動に時間がかかる

初回起動時は Metabase が内部データベースを初期化するため、2-3分かかることがあります。ヘルスチェックの `start_period: 120s` で対応しています。

### データベースに接続できない

1. PostgreSQL コンテナが起動しているか確認
2. ネットワーク設定（`data_platform_internal`）を確認
3. 認証情報（DB_USER, DB_PASSWORD）を確認

### メモリ不足

`JAVA_OPTS` の `-Xmx` 値を増加してください：

```yaml
JAVA_OPTS: "-Xmx2g -Xms1g"
```

## 参考リンク

- [Metabase 公式ドキュメント](https://www.metabase.com/docs/latest/)
- [Metabase Docker 展開ガイド](https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker)
- [PostgreSQL 接続設定](https://www.metabase.com/docs/latest/databases/connections/postgresql)
