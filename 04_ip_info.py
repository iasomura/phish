import logging
import psycopg2
import re
import requests
from psycopg2 import OperationalError

# ログの設定
log_file = '04_ierror.log'
logging.basicConfig(filename=log_file, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# データベース接続情報
DB_HOST = 'localhost'
DB_NAME = 'website_data'
DB_USER = 'postgres'
DB_PASSWORD = 'asomura'

def update_ip_info():
    try:
        # データベースに接続
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()

        # IPアドレスの形式が正しいかどうかを確認し、形式が正しくない場合はNULLに設定
        cur.execute("""
            UPDATE website_data 
            SET ip_address = NULL
            WHERE ip_address !~ '^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        """)
        print("IPアドレスの形式を確認しました。")

        # IPアドレスが正しい形式で、かつ情報が未取得のレコードを選択して更新
        cur.execute("""
            SELECT id, ip_address 
            FROM website_data
            WHERE ip_address IS NOT NULL
            AND status = 3
        """)
        rows = cur.fetchall()

        total_rows = len(rows)
        processed_rows = 0

        # 各レコードに対して処理を行う
        for row in rows:
            id, ip_address = row
            processed_rows += 1
            print(f"処理中: {processed_rows}/{total_rows}")

            try:
                # ip-api.comからデータを取得
                url = f"http://ip-api.com/json/{ip_address}"
                print(url)
                response = requests.get(url).json()

                # レスポンスが成功の場合、情報を取得しデータベースを更新
                if response["status"] == "success":
                    ip_info = str(response)
                    org = response["org"]
                    isp = response["isp"]
                    country = response["country"]
                    print(isp)
                    print(country)
                    
                    # データを更新
                    update_query = """
                        UPDATE website_data
                        SET last_update = now(),
                            status = 4,
                            ip_info = %s,
                            ip_retrieval_date = now(),
                            ip_organization = %s,
                            hosting_provider = %s,
                            ip_location = %s
                        WHERE id = %s
                    """
                    cur.execute(update_query, (ip_info, org, isp, country, id))
                    conn.commit()

            # リクエストエラーが発生した場合
            except requests.RequestException as e:
                print(f"リクエストエラー: {e}")
                # ステータスを99に変更し、次のレコードに進む
                cur.execute("""
                    UPDATE website_data
                    SET status = 99
                    WHERE id = %s
                """, (id,))
                conn.commit()
                # エラーログをファイルに記録
                logging.error(f"リクエストエラー: {e}")
                continue

            # 必要なキーがレスポンスに含まれていない場合
            except KeyError as e:
                print(f"キーが見つかりません: {e}")
                # 次のレコードに進む
                continue

    # データベースエラーが発生した場合
    except OperationalError as e:
        print(f"データベースエラー: {e}")
        # エラーログをファイルに記録
        logging.error(f"データベースエラー: {e}")

    finally:
        # データベース接続をクローズ
        if conn:
            cur.close()
            conn.close()
            print("データベース接続がクローズされました。")

if __name__ == "__main__":
    # IP情報の更新を実行
    update_ip_info()
    print("処理が完了しました。")
