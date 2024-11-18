#!/bin/bash

# データベース接続情報
DB_NAME="website_data"
DB_USER="postgres"
DB_HOST="localhost"

# カラム名を取得
COLUMNS=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT string_agg(column_name, ',') FROM information_schema.columns WHERE table_name = 'website_data' AND column_name LIKE '%https_certificate%';")

# データを抽出してCSVに出力
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "COPY (SELECT $COLUMNS FROM website_data) TO STDOUT WITH CSV HEADER" > output.csv

echo "データが output.csv に出力されました。"
