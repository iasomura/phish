import psycopg2
import logging
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
import asyncpg

async def execute_sql(sql, *params):
    """
    SQLクエリを実行する非同期関数
    
    :param sql: 実行するSQLクエリ
    :param params: SQLクエリのパラメータ
    """
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute(sql, params)
        # ログにSQL文を出力
        #logging.debug(f"Executing SQL: {sql} with params: {params}")
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error while executing SQL: {error}")
        raise
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logging.debug("Database connection closed")
            
def get_websites_to_process():
    """
    処理対象のウェブサイト情報をデータベースから取得する
    
    :return: 処理対象のウェブサイト情報のリスト
    """
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cur = conn.cursor()
    cur.execute("SELECT id, domain, url, url_pc_site, url_mobile_site FROM website_data WHERE status = 5 AND (url IS NOT NULL OR url_pc_site IS NOT NULL OR (domain IS NOT NULL AND ip_address IS NOT NULL))")
    destinations = cur.fetchall()
    cur.close()
    conn.close()
    return destinations
