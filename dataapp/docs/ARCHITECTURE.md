# Data Consolidation Platform - アーキテクチャ設計

## システム概要

複数の外部ソースからデータを取得し、統一的なプラットフォームに集約するシステムです。

## 技術スタック

| 技術 | バージョン | 用途 |
|------|----------|------|
| Python | 3.11+ (推奨: 3.12) | プログラミング言語 |
| Django | 5.2+ | Webフレームワーク |
| Django REST Framework | 3.15+ | REST API |
| PostgreSQL | 16 | データベース |
| Redis | 7 | メッセージブローカー |
| Celery | 5.4+ | 非同期タスク処理 |
| Gunicorn | 21.2+ | WSGIサーバー (本番) |
| Docker | Latest | コンテナ化 |

## アーキテクチャ図

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Consolidation Platform              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐              ┌──────────────────┐     │
│  │  Django Web App  │              │   PostgreSQL     │     │
│  │   (REST API)     │◄────────────►│    Database      │     │
│  │  Port: 8000      │              │   Port: 5432     │     │
│  └──────────────────┘              └──────────────────┘     │
│           │                                                   │
│           │                                                   │
│  ┌────────┴─────────┐              ┌──────────────────┐     │
│  │                  │              │     Redis        │     │
│  │    Celery Beat   │◄────────────►│   Port: 6379     │     │
│  │   (Scheduler)    │              │                  │     │
│  └──────────────────┘              │  ┌─────────────┐ │     │
│                                     │  │   DB 0      │ │     │
│  ┌──────────────────┐              │  │ Aggregation │ │     │
│  │ Celery Worker    │◄─────────────┤  └─────────────┘ │     │
│  │ Data Aggregation │              │                  │     │
│  │ Queue: agg_queue │              │  ┌─────────────┐ │     │
│  └──────────────────┘              │  │   DB 1      │ │     │
│                                     │  │ Acquisition │ │     │
│  ┌──────────────────┐              │  └─────────────┘ │     │
│  │ Celery Worker    │◄─────────────┤                  │     │
│  │ Data Acquisition │              └──────────────────┘     │
│  │ Queue: acq_queue │                                       │
│  └──────────────────┘                                       │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────┐                                       │
│  │ External Sources │                                       │
│  │ (API, DB, Files) │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

## アプリケーション構成

### 1. Data Acquisition (データ取得)

**責務**: 外部ソースからデータを取得する

**コンポーネント**:
- `DataSource` モデル: 外部データソース情報
- `AcquiredData` モデル: 取得した生データ
- `AcquisitionTask` モデル: タスク実行履歴
- Celery Worker (Redis DB 1)
- Queue: `acquisition_queue`

**タスク例**:
- API エンドポイントからのデータ取得
- 外部データベースからのデータ抽出
- ファイルの読み込みと解析
- WebSocket からのリアルタイムデータ受信

### 2. Data Aggregation (データ集約)

**責務**: 取得したデータを集約・加工する

**コンポーネント**:
- `AggregationSource` モデル: 集約ソース情報
- `AggregatedData` モデル: 集約済みデータ
- `AggregationTask` モデル: タスク実行履歴
- Celery Worker (Redis DB 0)
- Queue: `aggregation_queue`

**タスク例**:
- 複数ソースからのデータ統合
- データの正規化・クレンジング
- 集計・分析処理
- レポート生成

## データフロー

```
┌─────────────────┐
│ External Source │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Acquisition Task    │ (Redis DB 1)
│ - fetch_data()      │
│ - validate()        │
│ - store_raw_data()  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ AcquiredData Model  │ (PostgreSQL)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Aggregation Task    │ (Redis DB 0)
│ - combine_data()    │
│ - transform()       │
│ - aggregate()       │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ AggregatedData Model│ (PostgreSQL)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ REST API Response   │
└─────────────────────┘
```

## Celery ワーカーの分離戦略

### なぜ分離するのか？

1. **リソース管理**: 各アプリのタスクが独立したリソースを使用
2. **障害隔離**: 一方のワーカーが停止しても他方は動作継続
3. **スケーラビリティ**: 負荷に応じて各ワーカーを個別にスケール
4. **優先度管理**: タスクタイプごとに優先度を設定可能

### 設定詳細

| アプリ | Redis DB | Queue名 | Worker名 |
|--------|----------|---------|----------|
| Data Acquisition | DB 1 | `acquisition_queue` | `acquisition_worker` |
| Data Aggregation | DB 0 | `aggregation_queue` | `aggregation_worker` |
| Celery Beat | DB 0 | - | - |

### Worker 起動コマンド

```bash
# Data Acquisition Worker
celery -A apps.data_acquisition.celery worker \
  -Q acquisition_queue \
  -n acquisition_worker@%h \
  --loglevel=info

# Data Aggregation Worker
celery -A apps.data_aggregation.celery worker \
  -Q aggregation_queue \
  -n aggregation_worker@%h \
  --loglevel=info

# Celery Beat (スケジューラー)
celery -A config beat --loglevel=info
```

## API エンドポイント設計

### Data Acquisition API

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/acquisition/sources/` | GET, POST | データソース一覧・作成 |
| `/api/acquisition/sources/{id}/` | GET, PUT, DELETE | データソース詳細 |
| `/api/acquisition/data/` | GET | 取得データ一覧 |
| `/api/acquisition/tasks/` | GET | タスク履歴 |

### Data Aggregation API

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/aggregation/sources/` | GET, POST | 集約ソース一覧・作成 |
| `/api/aggregation/sources/{id}/` | GET, PUT, DELETE | 集約ソース詳細 |
| `/api/aggregation/data/` | GET | 集約データ一覧 |
| `/api/aggregation/tasks/` | GET | タスク履歴 |

### API ドキュメント

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`

## データベーススキーマ

### Data Acquisition

#### DataSource
```sql
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    config JSONB DEFAULT '{}',
    fetch_interval INTEGER DEFAULT 3600,
    last_fetched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### AcquiredData
```sql
CREATE TABLE acquired_data (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES data_sources(id),
    raw_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    data_hash VARCHAR(64),
    acquired_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_acquired_data_acquired_at ON acquired_data(acquired_at DESC);
CREATE INDEX idx_acquired_data_source ON acquired_data(source_id, acquired_at DESC);
CREATE INDEX idx_acquired_data_hash ON acquired_data(data_hash);
```

### Data Aggregation

#### AggregationSource
```sql
CREATE TABLE aggregation_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### AggregatedData
```sql
CREATE TABLE aggregated_data (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES aggregation_sources(id),
    data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    aggregated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_aggregated_data_aggregated_at ON aggregated_data(aggregated_at DESC);
CREATE INDEX idx_aggregated_data_source ON aggregated_data(source_id, aggregated_at DESC);
```

## デプロイメント構成

### 開発環境 (Mac)

```yaml
# docker-compose.yml
services:
  - postgres (ポート: 5432)
  - redis (ポート: 6379)

# ローカル実行
- Django runserver
- Celery workers (手動起動)
```

### 本番環境 (Ubuntu Server)

```yaml
# docker-compose.prod.yml
services:
  - postgres
  - redis
  - web (Django + Gunicorn)
  - celery_acquisition (ワーカー)
  - celery_aggregation (ワーカー)
  - celery_beat (スケジューラー)
```

## セキュリティ考慮事項

1. **環境変数**: 機密情報は `.env` で管理
2. **SECRET_KEY**: 本番環境では必ず変更
3. **ALLOWED_HOSTS**: 本番環境で適切に設定
4. **HTTPS**: 本番環境では SSL/TLS を使用
5. **Database**: PostgreSQL の認証情報を適切に管理
6. **CORS**: 必要なオリジンのみ許可

## パフォーマンス最適化

1. **Database Indexing**: 頻繁に検索されるフィールドにインデックス
2. **Celery Worker**: 負荷に応じてワーカー数を調整
3. **Connection Pooling**: PostgreSQL の接続プール設定
4. **Caching**: Redis を使用したキャッシング
5. **Pagination**: API レスポンスのページネーション

## モニタリング

### ログ

- Django: `logs/django.log`
- Celery Acquisition: コンテナログ
- Celery Aggregation: コンテナログ

### メトリクス

- Celery タスク実行状況
- API レスポンスタイム
- データベース接続数
- メモリ使用量

## 今後の拡張予定

- [ ] タスクの優先度管理
- [ ] リトライ戦略の実装
- [ ] Webhook サポート
- [ ] データバリデーション強化
- [ ] メトリクスダッシュボード
- [ ] アラート機能
- [ ] ユーザー認証・権限管理
- [ ] データのバージョン管理
