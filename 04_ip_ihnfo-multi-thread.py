import threading
import requests
from datetime import datetime
import psycopg2
import time
import re

# データベース接続情報
DB_HOST = 'localhost'
DB_NAME = 'website_data'
DB_USER = 'postgres'
DB_PASSWORD = 'asomura'

# APIエンドポイント
API_ENDPOINT = 'http://ip-api.com/json/'

# スレッド数
THREAD_COUNT = 20

# データベース接続
conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
cursor = conn.cursor()

def is_valid_ip(ip):
    # IPアドレスの正規表現パターン (修正版)
    ip_pattern = r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
    return re.match(ip_pattern, ip) is not None

def fetch_ip_data(ip):
    try:
        if not is_valid_ip(ip):
            #print(f"Invalid IP address format: {ip}")
            print(f"Efetching data for IP {ip}")
            return None

        response = requests.get(API_ENDPOINT + ip)
        data = response.json()

        if data['status'] == 'success':
            return data

    except Exception as e:
        print(f"Error fetching data for IP {ip}: {str(e)}")
        return None

def update_database(ip, data):
    try:
        if data:
            cursor.execute(
                """
                UPDATE website_data
                SET ip_info = %s,
                    ip_retrieval_date = NOW(),
                    ip_organization = %s,
                    hosting_provider = %s,
                    ip_location = %s
                WHERE ip_address = %s
                """,
                (str(data), data.get('org', ''), data.get('isp', ''), data.get('country', ''), ip)
            )

            if cursor.rowcount > 0:
                print(f"Updated data for IP {ip} with info: {data}")
            else:
                cursor.execute(
                    """
                    UPDATE website_data
                    SET ip_retrieval_date = NOW()
                    WHERE ip_address = %s
                    """,
                    (ip,)
                )
        conn.commit()

    except Exception as e:
        print(f"Error updating database for IP {ip}: {str(e)}")
        conn.rollback()

# データベースからip_infoカラムがNULLのレコードを取得
def get_null_ip_info_records():
    try:
        cursor.execute("SELECT ip_address FROM website_data WHERE ip_info IS NULL")
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Error fetching IP addresses from database: {str(e)}")
        return []

# マルチスレッドでデータ取得とデータベース更新を実行
def process_ips():
    ip_addresses = get_null_ip_info_records()
    threads = []

    for ip in ip_addresses:
        thread = threading.Thread(target=update_database, args=(ip, fetch_ip_data(ip)))
        threads.append(thread)

    # スレッドの開始
    for thread in threads:
        thread.start()

    # 全てのスレッドの終了を待つ (動的な待機時間)
    while threads:
        threads = [t for t in threads if t.is_alive()]
        #time.sleep(0.1)

if __name__ == "__main__":
    process_ips()
    
    # データベース接続をクローズ
    cursor.close()
    conn.close()
