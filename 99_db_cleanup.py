import os
import psycopg2
import logging
import json
import config  # config.py を参照

"""
このプログラムは、データベース内のレコードを削除します。
削除条件:
- データベースに記録されている画像ファイル(screenshot_iphone, screenshot_android, screenshot_chrome)のいずれかが
  /home/asomura/waseda/nextstep/images ディレクトリに存在しない場合、そのレコードを削除します。
- 削除されたレコードの詳細は deleted_records.log に記録されます。

構成ファイル:
- config.py: データベース接続設定を定義
- config.json: ベースフォルダのパスやその他の設定情報を含む
"""

# config.jsonの設定を読み込む関数
def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# config.jsonから設定値を読み込み
config_json = load_config('config.json')  # config.jsonが同じディレクトリにある前提
base_path = config_json['basefolder']  # 画像ファイルが保存されているフォルダ
db_config = config_json['database']  # データベース設定

# ログ設定
logging.basicConfig(filename='deleted_records.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# データベース接続設定
def connect_db():
    return psycopg2.connect(
        host=db_config['host'],
        database=db_config['dbname'],
        user=db_config['user'],
        password=db_config['password']
    )

# 画像ファイルのパスを確認する関数
def file_exists(base_path, filename):
    if filename:
        return os.path.isfile(os.path.join(base_path, filename))
    return False

# メイン処理
def main():
    conn = connect_db()
    cur = conn.cursor()

    # データベースから画像ファイル名を取得するクエリ
    select_query = """
    SELECT id, screenshot_iphone, screenshot_android, screenshot_chrome
    FROM public.website_data;
    """
    cur.execute(select_query)
    
    rows = cur.fetchall()
    
    for row in rows:
        record_id, screenshot_iphone, screenshot_android, screenshot_chrome = row
        
        # 画像ファイルが存在するか確認
        iphone_exists = file_exists(base_path, screenshot_iphone)
        android_exists = file_exists(base_path, screenshot_android)
        chrome_exists = file_exists(base_path, screenshot_chrome)
        
        # どれかの画像が存在しない場合、レコードを削除
        if not iphone_exists or not android_exists or not chrome_exists:
            delete_query = "DELETE FROM public.website_data WHERE id = %s"
            cur.execute(delete_query, (record_id,))
            conn.commit()

            # 削除されたレコードの情報をログに記録
            logging.info(f"Deleted record id: {record_id}, "
                         f"screenshot_iphone: {screenshot_iphone}, "
                         f"screenshot_android: {screenshot_android}, "
                         f"screenshot_chrome: {screenshot_chrome}")

    # 接続を閉じる
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
