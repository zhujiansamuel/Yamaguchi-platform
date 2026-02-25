#!/bin/bash
set -e

# Create Metabase database if it doesn't exist
# This script runs automatically when PostgreSQL container starts for the first time

METABASE_DB="${METABASE_DB_NAME:-metabase}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create database for Metabase application data
    SELECT 'CREATE DATABASE ${METABASE_DB}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${METABASE_DB}')\gexec

    -- Grant privileges to the main user
    GRANT ALL PRIVILEGES ON DATABASE ${METABASE_DB} TO ${POSTGRES_USER};
EOSQL

echo "Metabase database '${METABASE_DB}' initialized successfully."
