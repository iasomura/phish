import logging
import psycopg2
from psycopg2 import OperationalError
import requests
import config

# ログの設定
logging.basicConfig(filename='ip_info_update.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

"""
IPアドレスの情報を外部APIから取得し、データベースを更新しつつ、処理結果をログに記録し統計情報を出力する。
"""

db_config = config.load_db_config()

def update_ip_info():
    conn = None
    updated_count = 0
    error_count = 0
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        # IPアドレスの形式確認と更新
        cur.execute(r"""
            UPDATE website_data 
            SET ip_address = NULL
            WHERE ip_address !~ '^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        """)
        logging.info(f"Invalid IP addresses set to NULL: {cur.rowcount}")

        # 処理対象のレコードを取得
        cur.execute(r"""
            SELECT id, ip_address 
            FROM website_data
            WHERE ip_address IS NOT NULL
            AND status = 3
        """)
        rows = cur.fetchall()
        total_rows = len(rows)
        logging.info(f"Total rows to process: {total_rows}")

        for id, ip_address in rows:
            try:
                url = f"http://ip-api.com/json/{ip_address}"
                response = requests.get(url).json()

                if response["status"] == "success":
                    ip_info = str(response)
                    org = response["org"]
                    isp = response["isp"]
                    country = response["country"]

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
                    updated_count += 1
                    logging.info(f"Updated IP info for ID {id}")
                else:
                    logging.warning(f"Failed to get info for IP {ip_address}")
                    error_count += 1

            except requests.RequestException as e:
                logging.error(f"Request error for IP {ip_address}: {e}")
                cur.execute("UPDATE website_data SET status = 99 WHERE id = %s", (id,))
                conn.commit()
                error_count += 1
            except KeyError as e:
                logging.error(f"Key error in response for IP {ip_address}: {e}")
                error_count += 1

    except OperationalError as e:
        logging.error(f"Database error: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()
            logging.info("Database connection closed")

    return updated_count, error_count, total_rows

if __name__ == "__main__":
    updated, errors, total = update_ip_info()
    print(f"処理が完了しました。")
    print(f"総レコード数: {total}")
    print(f"更新成功: {updated}")
    print(f"エラー: {errors}")
    logging.info(f"Process completed. Total: {total}, Updated: {updated}, Errors: {errors}")
