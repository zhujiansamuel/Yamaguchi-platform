# Data Consolidation Platform

データ集約プラットフォーム - 複数のソースからデータを収集・集約するシステム

## 🏗️ アーキテクチャ

このプロジェクトは以下の技術スタックで構築されています：

- **Python 3.11**
- **Django 5.2+**
- **Django REST Framework** - REST API
- **PostgreSQL** - データベース
- **Redis** - Celeryブローカー/バックエンド
- **Celery** - 非同期タスク処理

### アプリ構成

プロジェクトは以下のDjangoアプリで構成されています：

1. **core** - 共通ユーティリティ/履歴管理

2. **data_acquisition** - データ取得アプリ
   - 外部ソースからデータを取得
   - Redis DB 1を使用
   - 独立したCelery Worker (`acquisition_queue`)

3. **data_aggregation** - データ集約アプリ
   - 取得したデータを集約・処理
   - Redis DB 0を使用
   - 独立したCelery Worker (`aggregation_queue`)

## 📁 プロジェクト構造

```
Data-consolidation/
├── apps/
│   ├── core/                  # 共通ユーティリティ/履歴管理
│   │   ├── history.py
│   │   └── apps.py
│   ├── data_acquisition/      # データ取得アプリ
│   │   ├── celery.py         # Celery設定 (Redis DB 1)
│   │   ├── tasks.py          # Celeryタスク
│   │   ├── models.py         # データモデル
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   └── data_aggregation/      # データ集約アプリ
│       ├── celery.py         # Celery設定 (Redis DB 0)
│       ├── tasks.py          # Celeryタスク
│       ├── models.py         # データモデル
│       ├── views.py
│       ├── serializers.py
│       └── urls.py
├── config/
│   ├── settings/
│   │   ├── base.py           # 基本設定
│   │   ├── development.py    # 開発環境設定
│   │   └── production.py     # 本番環境設定
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py             # Celery Beat設定
├── docker-compose.yml         # 開発環境用
├── docker-compose.prod.yml    # 本番環境用
├── Dockerfile
├── requirements.txt
└── requirements-prod.txt
```

## 🚀 開発環境セットアップ (Mac)

### 1. 環境変数の設定

```bash
cp .env.example .env
# 必要に応じて .env を編集
```

### 2. PostgreSQLとRedisを起動 (Docker)

```bash
docker-compose up -d
```

### 3. Pythonパッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. データベースマイグレーション

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. スーパーユーザーの作成

```bash
python manage.py createsuperuser
```

### 6. サービスの起動

#### Django開発サーバー
```bash
python manage.py runserver
```

#### Celery Worker - Data Acquisition
```bash
celery -A apps.data_acquisition.celery worker -Q acquisition_queue -n acquisition_worker@%h --loglevel=info
```

#### Celery Worker - Data Aggregation
```bash
celery -A apps.data_aggregation.celery worker -Q aggregation_queue -n aggregation_worker@%h --loglevel=info
```

#### Celery Beat (スケジューラー)
```bash
celery -A config beat --loglevel=info
```

## 🐳 本番環境デプロイ (Ubuntu Server - Docker)

### 1. 環境変数の設定

```bash
cp .env.example .env
# 本番環境用に .env を編集
# - SECRET_KEY を変更
# - DEBUG=False
# - ALLOWED_HOSTS を設定
# - データベース認証情報を設定
```

### 2. 全サービスを起動

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. マイグレーション実行

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### サービスの確認

```bash
# ログの確認
docker-compose -f docker-compose.prod.yml logs -f

# 特定サービスのログ
docker-compose -f docker-compose.prod.yml logs -f celery_aggregation
docker-compose -f docker-compose.prod.yml logs -f celery_acquisition
```

## 📡 API エンドポイント

### APIドキュメント
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- OpenAPI Schema: http://localhost:8000/api/schema/

### アプリエンドポイント
- Data Acquisition API: http://localhost:8000/api/acquisition/
- Data Aggregation API: http://localhost:8000/api/aggregation/

### 管理画面
- Django Admin: http://localhost:8000/admin/

## 🔧 開発ガイド

### Celeryタスクの作成

#### Data Acquisition タスク
```python
# apps/data_acquisition/tasks.py
from .celery import app

@app.task(name='apps.data_acquisition.tasks.my_task')
def my_task(param):
    # タスクロジックをここに実装
    return {"status": "completed"}
```

#### Data Aggregation タスク
```python
# apps/data_aggregation/tasks.py
from .celery import app

@app.task(name='apps.data_aggregation.tasks.my_task')
def my_task(param):
    # タスクロジックをここに実装
    return {"status": "completed"}
```

### タスクの実行

```python
# Django shellまたはビューから
from apps.data_acquisition.tasks import fetch_data_from_source
result = fetch_data_from_source.delay(config)
```

## 🧪 テスト

```bash
# 全テストを実行
python manage.py test

# 特定アプリのテスト
python manage.py test apps.data_acquisition
python manage.py test apps.data_aggregation
```

## 📊 データモデル

### Data Acquisition
- `DataSource` - 外部データソース
- `AcquiredData` - 取得した生データ
- `AcquisitionTask` - タスク実行履歴

### Data Aggregation
- `AggregationSource` - 集約ソース
- `AggregatedData` - 集約済みデータ
- `AggregationTask` - タスク実行履歴

## 🛠️ トラブルシューティング

### Celery Workerが起動しない
- Redisが起動しているか確認: `docker ps`
- Redis接続設定を確認: `.env`ファイル

### データベース接続エラー
- PostgreSQLが起動しているか確認: `docker ps`
- データベース認証情報を確認: `.env`ファイル

### マイグレーションエラー
```bash
# マイグレーションをリセット
python manage.py migrate --fake-initial
```

## 📝 ライセンス

このプロジェクトは開発中です。

## 👥 貢献

詳細な実装は今後追加予定です。
