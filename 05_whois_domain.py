import os
import psycopg2
import subprocess
import shlex
import datetime
import ipaddress
import signal

# タイムアウト例外
class CommandTimeout(Exception):
    pass

# タイムアウトハンドラ
def timeout_handler(signum, frame):
    raise CommandTimeout("Command timed out")

# タイムアウト付きでコマンドを実行する関数
def run_command_with_timeout(cmd, timeout=30):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    try:
        result = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        signal.alarm(0)  # タイムアウトをリセット
        return result.stdout
    except CommandTimeout:
        return b'TIMEOUT'
    except subprocess.CalledProcessError as e:
        return b'ERROR'
    finally:
        signal.alarm(0)  # タイムアウトをリセット

# データベース接続情報
db_host = 'localhost'
db_name = 'website_data'
db_user = 'postgres'
db_password = 'asomura'

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
        whois_output = run_command_with_timeout(cmd)

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

        # statusの設定
        if whois_output_decoded == 'TIMEOUT':
            status = 98  # タイムアウトの場合
        elif whois_output_decoded == 'ERROR':
            status = 99  # エラーの場合
        else:
            status = 5   # 正常な場合

        # whois_ipカラムにWHOIS情報を挿入
        cur.execute(update_query, (current_time, status, whois_output_decoded, record_id))
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
