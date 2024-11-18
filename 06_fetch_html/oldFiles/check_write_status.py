import psycopg2
from psycopg2 import sql
import json

# config.jsonを読み込んでデータベース設定を取得
def load_config():
    with open("config.json", "r") as config_file:
        return json.load(config_file)

# データベースに接続する関数
def connect_to_db(config):
    try:
        connection = psycopg2.connect(
            host=config["database"]["host"],
            database=config["database"]["name"],
            user=config["database"]["user"],
            password=config["database"]["password"]
        )
        return connection
    except Exception as e:
        print(f"データベース接続エラー: {e}")
        return None

# website_dataテーブルから特定のwebsite_idに基づいてレコードを確認する関数
def check_write_status(website_id):
    config = load_config()
    connection = connect_to_db(config)
    
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # website_dataテーブルの指定IDのレコードを取得
            query = sql.SQL("""
            SELECT https_certificate_all, https_certificate_issuer, screenshot_availability, 
                   mhtml_pc_site, status 
            FROM website_data 
            WHERE id = %s
            """)
            cursor.execute(query, (website_id,))
            result = cursor.fetchone()
            
            if result:
                columns = ['https_certificate_all', 'https_certificate_issuer', 'screenshot_availability', 'mhtml_pc_site', 'status']
                record = dict(zip(columns, result))

                # 各カラムが正しく書き込まれているか確認
                if any(value is None for key, value in record.items() if key != 'status'):
                    print(f"書き込みが不完全: {record}")
                    return False
                return True
            else:
                print(f"website_dataにID {website_id}のレコードが存在しません。")
                return False
    except Exception as e:
        print(f"クエリ実行エラー: {e}")
        return False
    finally:
        connection.close()
