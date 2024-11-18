import re
import subprocess
import psycopg2
from psycopg2 import sql
import logging
from urllib.parse import urlparse
import config

"""
このプログラムは、指定されたウェブサイトのドメイン情報（Aレコード、MXレコード、NSレコード、IPアドレス）を
DNSクエリを使って取得し、その結果をデータベースに更新するものです。
"""

# ログの設定
logging.basicConfig(filename='03_error.log', level=logging.ERROR, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def execute_command(command):
    """
    コマンドを実行し、出力を返すヘルパー関数
    """
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    return output.decode("utf-8")

def is_valid_ip(ip):
    """
    IPアドレスの形式をチェックする関数
    """
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return re.match(pattern, ip)

def get_ip_from_nslookup(output):
    """
    nslookupの出力からIPアドレスを抽出する関数
    """
    non_auth_ip = None
    auth_ip = None
    for line in output.splitlines():
        if "Non-authoritative answer" in line:
            non_auth_ip = True
        if "Address:" in line:
            ip = line.split("Address:")[1].strip()
            if is_valid_ip(ip):
                if non_auth_ip:
                    return ip  # Non-authoritative answerのIPを優先して返す
                auth_ip = ip  # Non-authoritative answerがない場合のIPを保存
    return auth_ip

def extract_domain_from_url(url):
    """
    URLからドメインを抽出する関数
    """
    parsed_url = urlparse(url)
    return parsed_url.hostname

def check_dns_records(dig_info_A, dig_info_NS, domain):
    """
    DNSレコードの有効性をチェックする関数
    """
    if len(dig_info_A) <= 1:
        raise ValueError(f"Aレコードが不足しています: domain={domain}, A={len(dig_info_A)}")
    if len(dig_info_NS) <= 1:
        raise ValueError(f"NSレコードが不足しています: domain={domain}, NS={len(dig_info_NS)}")

def update_website_data(connection):
    """
    ウェブサイトデータを更新する関数
    """
    cursor = connection.cursor()
    try:
        # 条件に基づいてウェブサイトデータを取得
        cursor.execute("""
            SELECT id, url 
            FROM website_data 
            WHERE domain_status = 'NOERROR' 
                AND dig_info_A IS NULL 
                AND status = 2
        """)
        websites = cursor.fetchall()
        total_websites = len(websites)
        processed_websites = 0

        for website in websites:
            website_id, url = website
            domain = extract_domain_from_url(url)
            try:
                # nslookupを使用してAレコードとIPアドレスを取得
                nslookup_output = execute_command(f"nslookup {domain}")
                dig_info_A = nslookup_output
                ip_address = get_ip_from_nslookup(nslookup_output)

                # IPアドレスが取得できない場合は例外を発生
                if not ip_address:
                    raise ValueError(f"IPアドレスが取得できませんでした: {domain}")

                # TTLの値を取得
                dig_info_TTL_A = None
                if ip_address:
                    dig_output = execute_command(f"dig +noall +answer {domain} A")
                    ttl_values = [int(line.split()[1]) for line in dig_output.split('\n') if line.strip()]
                    if ttl_values:
                        dig_info_TTL_A = min(ttl_values)

                # MXレコードを取得（存在しない場合は特別な文字列を設定）
                dig_info_MX = execute_command(f"dig +noall +answer {domain} MX")
                if not dig_info_MX.strip():
                    dig_info_MX = "No MX Record"

                # NSレコードを取得
                dig_info_NS = execute_command(f"dig +noall +answer {domain} NS")

                # AレコードとNSレコードの必須チェック
                check_dns_records(dig_info_A, dig_info_NS, domain)

                # データベースを更新
                cursor.execute("""
                    UPDATE website_data 
                    SET last_update = now(), 
                        status = 3, 
                        dig_info_A = %s, 
                        dig_info_TTL_A = %s, 
                        dig_info_MX = %s, 
                        dig_info_NS = %s, 
                        ip_address = %s 
                    WHERE id = %s
                """, (dig_info_A, dig_info_TTL_A, dig_info_MX, dig_info_NS, ip_address, website_id))

                connection.commit()
                
                # 処理進捗を表示
                processed_websites += 1
                print(f"進捗: {processed_websites}/{total_websites}", end="\r")
                
                # 更新されたデータを確認し表示
                check_and_display_website_data(cursor, website_id)

            except Exception as e:
                # エラーが発生した場合はステータスを99に更新
                cursor.execute("""
                    UPDATE website_data 
                    SET last_update = now(), 
                        status = 9903 
                    WHERE id = %s
                """, (website_id,))
                connection.commit()
                
                # エラーログを記録
                logging.error(f"エラーが発生しました (website_id={website_id}): %s", e)
                print(f"エラーが発生しました (website_id={website_id}):", e)

        print("\nウェブサイトデータが正常に更新されました。")

    except Exception as e:
        print("エラーが発生しました:", e)
        logging.error("予期せぬエラーが発生しました: %s", e)

    finally:
        cursor.close()
        connection.close()

def check_and_display_website_data(cursor, website_id):
    """
    指定されたwebsite_idのデータを確認し、表示する関数
    """
    try:
        query = sql.SQL("""
            SELECT dig_info_A, dig_info_TTL_A, dig_info_MX, dig_info_NS, ip_address
            FROM website_data
            WHERE id = {}
        """).format(sql.Literal(website_id))

        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            dig_info_A, dig_info_TTL_A, dig_info_MX, dig_info_NS, ip_address = result
            print(f"\nWebsite ID: {website_id}")
            print(f"dig_info_A: {dig_info_A}")
            print(f"dig_info_TTL_A: {dig_info_TTL_A}")
            print(f"dig_info_MX: {dig_info_MX}")
            print(f"dig_info_NS: {dig_info_NS}")
            print(f"ip_address: {ip_address}")
        else:
            print(f"\nデータが見つかりません。(Website ID: {website_id})")
    
    except Exception as e:
        print(f"データの確認中にエラーが発生しました: {e}")
        logging.error(f"データ確認エラー (website_id={website_id}): %s", e)

if __name__ == "__main__":
    try:
        # PostgreSQLデータベースに接続
        db_config = config.load_db_config()
        connection = psycopg2.connect(**db_config)
        update_website_data(connection)
    except psycopg2.Error as e:
        logging.error("データベース接続エラー: %s", e)
        print("データベース接続エラー:", e)
