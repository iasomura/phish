import os
import psycopg2
import json

# config.jsonを読み込む関数
def load_config(file_path):
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config

# 設定ファイルのパス
config_path = 'config.json'

# 設定を読み込む
config = load_config(config_path)
db_config = config['database']
basefolder = config['basefolder']

# データベースに接続
conn = psycopg2.connect(
    host=db_config['host'],
    database=db_config['name'],
    user=db_config['user'],
    password=db_config['password']
)
cur = conn.cursor()

# データベースから画像ファイル名を取得するクエリ
select_query = """
SELECT screenshot_iphone, screenshot_android, screenshot_chrome
FROM public.website_data
WHERE screenshot_iphone IS NOT NULL
   OR screenshot_android IS NOT NULL
   OR screenshot_chrome IS NOT NULL;
"""
cur.execute(select_query)

# データベースに存在する画像ファイル名をセットに格納
existing_files = set()
rows = cur.fetchall()
for row in rows:
    screenshot_iphone, screenshot_android, screenshot_chrome = row
    if screenshot_iphone:
        existing_files.add(screenshot_iphone)
    if screenshot_android:
        existing_files.add(screenshot_android)
    if screenshot_chrome:
        existing_files.add(screenshot_chrome)

# basefolder内の画像ファイルをチェック
for filename in os.listdir(basefolder):
    file_path = os.path.join(basefolder, filename)
    if os.path.isfile(file_path):
        # ファイルがデータベースに存在しない場合は削除
        if filename not in existing_files:
            os.remove(file_path)
            print(f"Deleted: {file_path}")

# 接続を閉じる
cur.close()
conn.close()
