import re
import subprocess
import psycopg2
from psycopg2 import sql
import logging
from urllib.parse import urlparse
import config



"""
このプログラムは、指定されたウェブサイトのドメイン情報（Aレコード、MXレコード、NSレコード、IPアドレス）をDNSクエリを使って取得し、その結果をデータベースに更新するものです。
"""

# ログの設定
logging.basicConfig(filename='03_error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')



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


def update_website_data(connection):
    """
    ウェブサイトデータを更新し、データの長さを確認する関数
    """
    cursor = connection.cursor()
    try:
        # 条件に基づいてウェブサイトデータを取得
        cursor.execute("SELECT id, url FROM website_data WHERE domain_status = 'NOERROR' AND dig_info_A IS NULL AND status = 2")
        websites = cursor.fetchall()
        total_websites = len(websites)
        processed_websites = 0

        for website in websites:
            website_id, url = website
            domain = extract_domain_from_url(url)
            try:
                # nslookupを使用してAレコードを調べ、結果をdig_info_A TEXTに格納する
                nslookup_output = execute_command(f"nslookup {domain}")
                dig_info_A = nslookup_output
                ip_address = get_ip_from_nslookup(nslookup_output)

                # IPアドレスが取得できない場合は例外を発生させる
                if not ip_address:
                    raise ValueError(f"IPアドレスが取得できませんでした: {domain}")

                # TTLの値を取得してdig_info_TTL_Aに格納する
                dig_info_TTL_A = None
                if ip_address:
                    dig_output = execute_command(f"dig +noall +answer {domain} A")
                    ttl_values = [int(line.split()[1]) for line in dig_output.split('\n') if line.strip()]
                    if ttl_values:
                        dig_info_TTL_A = min(ttl_values)

                # MXレコードを調べ、結果をdig_info_MX TEXTに格納する
                dig_info_MX = execute_command(f"dig +noall +answer {domain} MX")

                # NSレコードを調べ、結果をdig_info_NS TEXTに格納する
                dig_info_NS = execute_command(f"dig +noall +answer {domain} NS")

                # データの長さをチェック
                if (len(dig_info_A) <= 1 or len(dig_info_MX) <= 1 or len(dig_info_NS) <= 1):
                    raise ValueError(f"データが1バイト以下です: domain={domain}, A={len(dig_info_A)}, MX={len(dig_info_MX)}, NS={len(dig_info_NS)}")

                # データベースを更新する
                cursor.execute("UPDATE website_data SET last_update = now(), status = 3, dig_info_A = %s, dig_info_TTL_A = %s, dig_info_MX = %s, dig_info_NS = %s, ip_address = %s WHERE id = %s",
                               (dig_info_A, dig_info_TTL_A, dig_info_MX, dig_info_NS, ip_address, website_id))

                connection.commit()
                # 処理進捗を表示
                processed_websites += 1
                print(f"進捗: {processed_websites}/{total_websites}", end="\r")
                # 更新されたデータを確認し表示
                check_and_display_website_data(cursor, website_id)

            except Exception as e:
                # エラーが発生した場合はロールバック
                cursor.execute("UPDATE website_data SET last_update = now(), status = 99 WHERE id = %s",
                               (website_id,))

                connection.commit()
                # エラーログを記録
                logging.error(f"エラーが発生しました (website_id={website_id}): %s", e)
                print(f"エラーが発生しました (website_id={website_id}):", e)

        
                
        print("\nウェブサイトデータが正常に更新されました。")

    except Exception as e:
        print("エラーが発生しました:", e)

    finally:
        # カーソルとコネクションをクローズ
        cursor.close()
        connection.close()


        
def check_and_display_website_data(cursor, website_id):
    """
    指定されたwebsite_idのデータを確認し、表示する関数
    """
    try:
        # SQLクエリを準備
        query = sql.SQL("""
        SELECT dig_info_A, dig_info_TTL_A, dig_info_MX, dig_info_NS, ip_address
        FROM website_data
        WHERE id = {}
        """).format(sql.Literal(website_id))

        # クエリを実行
        cursor.execute(query)

        # 結果を取得
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


if __name__ == "__main__":
    # PostgreSQLデータベースに接続
    try:
        db_config = config.load_db_config()
        connection = psycopg2.connect(**db_config)
        #connection = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        update_website_data(connection)
    except psycopg2.Error as e:
        # データベースエラーをログに記録
        logging.error("データベースエラー: %s", e)
        print("データベースエラー:", e)
