import os
import sys
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
import subprocess
import json
import config

# ロックファイルのパス
lock_file = '/tmp/00-kesagatame.lock'

# ロックファイルを作成して、同時実行を防止する関数
def check_lock_file():
    if os.path.exists(lock_file):
        print("Another instance is running. Exiting.")
        sys.exit()  # プログラム終了
    else:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))  # 現在のプロセスIDを記録

# ロックファイルを削除する関数
def remove_lock_file():
    if os.path.exists(lock_file):
        os.remove(lock_file)

# データベース接続情報をロード
db_config = config.load_db_config()

# URL一覧が記録されたテキストファイルのパス
url_list_file = 'kesagatame.txt'

# URLがすでに登録されているかを確認する関数
def is_url_registered(cursor, normalized_url):
    query = "SELECT 1 FROM website_data WHERE url = %s"
    cursor.execute(query, (normalized_url,))
    return cursor.fetchone() is not None

# URL一覧を読み込みデータベースに挿入する関数
def insert_url_data(url_list_file):
    # テキストファイルをオープンして読み込み
    with open(url_list_file, 'r') as f:
        urls = f.readlines()

    # データベースに接続
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    for url in urls:
        url = url.strip()  # 改行を削除
        if not url:
            continue  # 空行は無視

        normalized_url = normalize_url(url)
        domain = extract_domain_from_url(normalized_url)

        # URLがすでに登録されているか確認
        if is_url_registered(cursor, normalized_url):
            print(f"URL already registered: {normalized_url}")
            continue  # 登録済みの場合、スキップ

        # 固定値
        phish_from = "kesagatame"
        phish_id = None
        phish_detail_url = None
        phish_ip_address = None
        cidr_block = None
        verified = False
        online_status = False
        target = None

        # データベースに挿入
        sql_query = """INSERT INTO website_data (status, last_update, phish_from, url, phish_id, phish_detail_url, phish_ip_address, cidr_block, verified, online_status, target, domain)
                       VALUES (0, now(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (domain) DO NOTHING"""

        values = (
            sanitize(phish_from),
            sanitize(normalized_url),
            sanitize(phish_id),
            sanitize(phish_detail_url),
            sanitize(phish_ip_address),
            sanitize(cidr_block),
            sanitize(verified),
            sanitize(online_status),
            sanitize(target),
            sanitize(domain)
        )
        
        cursor.execute(sql_query, values)
        # データベースにコミット
        conn.commit()

        # 各スクリプトを実行
        scripts = [
            "01_domain_status.py",
            "02_whois.py",
            "03_dig_data.py",
            "04_ip_info.py",
            "05_whois_ip.py",
            "06_fetch_html/main.py"
        ]
    
        for script in scripts:
            try:
                subprocess.run(["python", script], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while running {script}: {e}")

    # データベース接続をクローズ
    cursor.close()
    conn.close()

# サニタイズ関数
def sanitize(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, sql.Literal):
        return str(value)
    return value

# URLを正規化する関数
def normalize_url(url):
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme.lower() if parsed_url.scheme else 'http'
    netloc = parsed_url.netloc.lower()
    path = parsed_url.path
    params = parsed_url.params
    query = parsed_url.query
    fragment = parsed_url.fragment
    normalized_url = f"{scheme}://{netloc}{path}"
    if params:
        normalized_url += f";{params}"
    if query:
        normalized_url += f"?{query}"
    if fragment:
        normalized_url += f"#{fragment}"
    return normalized_url

# URLからドメインを抽出する関数
def extract_domain_from_url(url):
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc

# メイン関数
if __name__ == "__main__":
    try:
        check_lock_file()  # ロックファイルのチェック
        insert_url_data(url_list_file)  # データ挿入
    finally:
        remove_lock_file()  # ロックファイルの削除
