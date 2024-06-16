import os
import psycopg2
import subprocess
import shlex
import datetime
import ipaddress

# 環境変数からデータベース接続情報を取得
#db_host = os.getenv('DB_HOST', 'localhost')
#db_name = os.getenv('DB_NAME', 'website_data')
#db_user = os.getenv('DB_USER', 'postgres')
#db_password = os.getenv('DB_PASSWORD', '')

conn = psycopg2.connect("host=localhost dbname=website_data user=postgres password=asomura")
# データベース接続情報
db_host = 'localhost'
db_name = 'website_data'
db_user = 'postgres'
db_password = 'asomura'
#conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
cur = conn.cursor()

conn = None
cur = None

try:
    # PostgreSQLへの接続を確立
    conn_params = {
        "host": db_host,
        "database": db_name,
        "user": db_user,
        "password": db_password
    }
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    # SQLクエリを定義
    sql_query = """
        SELECT id, ip_address
        FROM website_data
        WHERE status = 4
    """

    # SQLクエリを実行
    cur.execute(sql_query)
    results = cur.fetchall()

    total_records = len(results)
    processed_records = 0

    # 各IPアドレスに対してWHOISを実行し、データベースに挿入
    for row in results:
        record_id, ip_address = row

        # IPアドレスの形式を検証
        try:
            ip = ipaddress.ip_address(ip_address)
        except ValueError as e:
            print(f"無効なIPアドレス {ip_address}: {e}")
            continue

        cmd = f"whois {ip}"
        try:
            whois_result = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            whois_output = whois_result.stdout
        except subprocess.CalledProcessError as e:
            print(f"レコード {record_id} のWHOIS情報の取得中にエラーが発生しました:", e)
            whois_output = b'ERROR'

        # WHOISの出力をデコード
        whois_output_decoded = whois_output.decode('utf-8', errors='ignore')

        # whois_ipカラムに挿入するためのSQLクエリを定義
        update_query = """
            UPDATE website_data
            SET
            last_update = %s,
            status = %s,
            whois_ip = %s
            WHERE id = %s
        """
        # 現在の日時を取得
        current_time = datetime.datetime.now()
        # whois_ipカラムにWHOIS情報を挿入
        cur.execute(update_query, (current_time, 5 if whois_output_decoded != 'ERROR' else 99, whois_output_decoded, record_id))
        conn.commit()

        processed_records += 1
        print(f"処理済み: {processed_records}/{total_records}")

except psycopg2.Error as e:
    print("データベースエラー:", e)
finally:
    # カーソルと接続をクローズ
    if cur:
        cur.close()
    if conn:
        conn.close()
