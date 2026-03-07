#!/usr/bin/env bash
# ============================================================
# Yamaguchi Dashboard — 環境変数設定スクリプト
# 使い方: パスワード部分を実際の値に書き換えてから実行
#   chmod +x setup-env.sh
#   source setup-env.sh
# または docker-compose 用の .env ファイルを生成:
#   ./setup-env.sh --dotenv
# ============================================================

# ---------- 既存設定 ----------
export DATAAPP_API_URL="http://host.docker.internal:8000"
export DATAAPP_SERVICE_TOKEN=""
export WEBAPP_API_URL="http://host.docker.internal:8001"
export WEBAPP_SERVICE_TOKEN=""
export FETCH_INTERVAL_S=30
export FETCH_TIMEOUT_S=10
export TIME_WINDOW_DAYS=2

# ---------- メール設定 ----------
export XSERVER_MAIL_HOST="sv16698.xserver.jp"

# ★★★ 以下のパスワードを実際の値に書き換えてください ★★★
export MAIL_ACCOUNTS='[
  {"key":"contact",  "address":"contact@mobile-zone.jp",              "password":"CHANGE_ME"},
  {"key":"error",    "address":"error@automation.mobile-zone.jp",     "password":"CHANGE_ME"},
  {"key":"info",     "address":"info@automation.mobile-zone.jp",      "password":"CHANGE_ME"},
  {"key":"no-reply", "address":"no-reply@mobile-zone.jp",            "password":"CHANGE_ME"}
]'

# ---------- .env ファイル生成モード ----------
if [ "$1" = "--dotenv" ]; then
  ENV_FILE="$(dirname "$0")/.env"
  cat > "$ENV_FILE" <<DOTENV
DATAAPP_API_URL=${DATAAPP_API_URL}
DATAAPP_SERVICE_TOKEN=${DATAAPP_SERVICE_TOKEN}
WEBAPP_API_URL=${WEBAPP_API_URL}
WEBAPP_SERVICE_TOKEN=${WEBAPP_SERVICE_TOKEN}
FETCH_INTERVAL_S=${FETCH_INTERVAL_S}
FETCH_TIMEOUT_S=${FETCH_TIMEOUT_S}
TIME_WINDOW_DAYS=${TIME_WINDOW_DAYS}
XSERVER_MAIL_HOST=${XSERVER_MAIL_HOST}
MAIL_ACCOUNTS=${MAIL_ACCOUNTS}
DOTENV
  echo "Generated: ${ENV_FILE}"
  echo "※ docker-compose up で自動的に読み込まれます"
fi
