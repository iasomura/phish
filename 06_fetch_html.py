import asyncio
import psycopg2
import json
import os
import logging
import aiohttp
from pyppeteer import launch
from datetime import datetime
import hashlib
import time
import base64

# 設定ファイルの読み込み
config_file = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

# データベース接続情報の設定
db_host = config['database']['host']
db_name = config['database']['name']
db_user = config['database']['user']
db_password = config['database']['password']

# ユーザーエージェントの設定
user_agents = {
    'Chrome': config['Chrome'],
    'Android': config['Android'],
    'iPhone': config['iPhone']
}

# スクリーンショットの保存先フォルダ
basefolder = config['basefolder']
if not os.path.exists(basefolder):
    os.makedirs(basefolder)

# mhtmlの保存先フォルダ
basefolder_mhtml = config['basefolder_mhtml']
if not os.path.exists(basefolder_mhtml):
    os.makedirs(basefolder_mhtml)

# リダイレクトの最大回数
MAX_REDIRECTS = 10

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ログファイルの設定
log_file = 'process_website.log'
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file),
                        logging.StreamHandler()
                    ])

async def execute_sql(sql, *params):
    conn = None
    try:
        # データベースに接続
        conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error while executing SQL: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logging.debug("Database connection closed")

# ウェブサイトを処理するメインの関数
async def process_website(destination, semaphore, progress_tracker):
    website_id, domain, url, url_pc_site, url_mobile_site = destination
    logging.info(f"Processing website: {domain}")

    # 取得するURLを決定
    target_url = url or url_pc_site or f"https://{domain}"
    mobile_target_url = url_mobile_site or url or f"http://{domain}"

    async with semaphore:
        # 各ユーザーエージェントごとにMHTMLコンテンツを取得
        mhtml_content_pc = await fetch_website_as_mhtml(target_url, user_agents['Chrome'], website_id)
        mhtml_content_iphone = await fetch_website_as_mhtml(target_url, user_agents['iPhone'], website_id)
        mhtml_content_android = await fetch_website_as_mhtml(target_url, user_agents['Android'], website_id)
        #time.sleep(10)
        
        # デバッグ情報をログ出力
        logging.debug(f"MHTML Content PC: {mhtml_content_pc}")
        logging.debug(f"MHTML Content iPhone: {mhtml_content_iphone}")
        logging.debug(f"MHTML Content Android: {mhtml_content_android}")

#    if mhtml_content_pc or mhtml_content_iphone or mhtml_content_android:
#        sql = """
#        UPDATE website_data SET 
#            mhtml_pc_site = %s, 
#            mhtml_mobile_site_iphone = %s, 
#            mhtml_mobile_site_android = %s, 
#            status = 6, last_update = NOW() 
#        WHERE id = %s
#        """
#        try:
#            await execute_sql(sql, psycopg2.Binary(mhtml_content_pc),
#                              psycopg2.Binary(mhtml_content_iphone),
#                              psycopg2.Binary(mhtml_content_android),
#                              website_id)
#            logging.info(f"Updated website_data for {website_id} with status 6")
#        except Exception as e:
#            logging.error(f"Failed to update website_data for {website_id}: {e}")

        now = datetime.now()
        filename_prefix = f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}_{domain}_{website_id}_{hashlib.md5(url.encode()).hexdigest()}"
        screenshot_iphone = f"{filename_prefix}_iphone.png"
        screenshot_android = f"{filename_prefix}_android.png"
        screenshot_chrome = f"{filename_prefix}_chrome.png"

        screenshot_iphone_success = await capture_screenshot(target_url, user_agents['iPhone'], os.path.join(basefolder, screenshot_iphone))
        screenshot_android_success = await capture_screenshot(target_url, user_agents['Android'], os.path.join(basefolder, screenshot_android))
        screenshot_chrome_success = await capture_screenshot(target_url, user_agents['Chrome'], os.path.join(basefolder, screenshot_chrome))

        screenshot_availability = screenshot_iphone_success and screenshot_android_success and screenshot_chrome_success
        sql = """
        UPDATE website_data SET 
            screenshot_availability = %s, 
            screenshot_iphone = %s, 
            screenshot_android = %s, 
            screenshot_chrome = %s 
        WHERE id = %s
        """
        try:
            await execute_sql(sql, screenshot_availability, 
                              screenshot_iphone if screenshot_iphone_success else None, 
                              screenshot_android if screenshot_android_success else None, 
                              screenshot_chrome if screenshot_chrome_success else None, 
                              website_id)
            logging.info(f"Updated website_data for {website_id} with screenshots")
        except Exception as e:
            logging.error(f"Failed to update website_data for {website_id} with screenshots: {e}")
        else:
            try:
                await execute_sql("UPDATE website_data SET status = 98 WHERE id = %s", website_id)
                logging.info(f"Updated website_data for {website_id} with status 98")
            except Exception as e:
                logging.error(f"Failed to update website_data for {website_id} with status 98: {e}")

                progress_tracker['completed'] += 1
                logging.info(f"Progress: {progress_tracker['completed']}/{progress_tracker['total']} websites processed.")

# ウェブサイトのスクリーンショットを取得する関数
async def capture_screenshot(url, user_agent, filename, timeout=180):
    try:
        # Pyppeteerでブラウザを起動
        browser = await launch(headless=True, args=['--no-sandbox'])
        page = await browser.newPage()
        # ユーザーエージェントを設定
        await page.setUserAgent(user_agent)
        # 指定されたURLに移動
        await asyncio.wait_for(page.goto(url), timeout=timeout)
        # ページ全体のスクリーンショットを取得
        await asyncio.wait_for(page.screenshot({'path': filename, 'fullPage': True}), timeout=timeout)
        logging.info(f"Full page screenshot saved to {filename}")
        return True
    except asyncio.TimeoutError:
        logging.error(f"Timeout while capturing full page screenshot for {url}")
        return False
    except Exception as e:
        logging.error(f"Failed to capture full page screenshot: {e}")
        return False
    finally:
        # ブラウザを閉じる
        if browser:
            await browser.close()

# ウェブサイトのHTMLコンテンツをMHTML形式で取得する関数
async def fetch_website_as_mhtml(url, user_agent, website_id):
    browser = None
    try:
        # Pyppeteerでブラウザを起動
        browser = await launch(headless=True, args=['--no-sandbox'])
        page = await browser.newPage()
        # ユーザーエージェントを設定
        await page.setUserAgent(user_agent)
        # 指定されたURLに移動
        await page.goto(url, {'waitUntil': 'networkidle2'})
        # MHTML形式でページを保存
        cdp = await page._client.send('Page.captureSnapshot', {'format': 'mhtml'})
        mhtml_content = cdp['data']
        if mhtml_content:
            print(mhtml_content)
            logging.info("Successfully fetched MHTML content")
            mhtml_content_bytes = mhtml_content.encode('utf-8')  # strをbytesに変換

            if user_agent == user_agents['Chrome']:
                sql = """
                UPDATE website_data SET 
                mhtml_pc_site = %s, 
                status = 6, last_update = NOW() 
                WHERE id = %s
                """
                try:
                    await execute_sql(sql, psycopg2.Binary(mhtml_content_bytes), website_id)
                    logging.info(f"Updated website_data for {website_id} with status 6")
                except Exception as e:
                    logging.error(f"Failed to update website_data for {website_id}: {e}")

            elif user_agent == user_agents['iPhone']:
                sql = """
                UPDATE website_data SET 
                mhtml_mobile_site_iphone = %s, 
                status = 6, last_update = NOW() 
                WHERE id = %s
                """
                try:
                    await execute_sql(sql, psycopg2.Binary(mhtml_content_bytes), website_id)
                    logging.info(f"Updated website_data for {website_id} with status 6")
                except Exception as e:
                    logging.error(f"Failed to update website_data for {website_id}: {e}")

            elif user_agent == user_agents['Android']:
                sql = """
                UPDATE website_data SET 
                mhtml_mobile_site_android = %s, 
                status = 6, last_update = NOW() 
                WHERE id = %s
                """
                try:
                    await execute_sql(sql, psycopg2.Binary(mhtml_content_bytes), website_id)
                    logging.info(f"Updated website_data for {website_id} with status 6")
                except Exception as e:
                    logging.error(f"Failed to update website_data for {website_id}: {e}")

        else:
            logging.warning("No MHTML content fetched")
        return url
    except Exception as e:
        logging.error(f"Failed to fetch MHTML content: {e}")
        return None
    finally:
        # ブラウザを閉じる
        if browser:
            await browser.close()


# メイン関数
async def main():
    # セマフォを設定して同時実行数を制限
    semaphore = asyncio.Semaphore(6)

    # データベースに接続して処理対象のウェブサイト情報を取得
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
    cur = conn.cursor()
    cur.execute("SELECT id, domain, url, url_pc_site, url_mobile_site FROM website_data WHERE status = 5 AND (url IS NOT NULL OR url_pc_site IS NOT NULL OR (domain IS NOT NULL AND ip_address IS NOT NULL))")
    destinations = cur.fetchall()
    cur.close()
    conn.close()

    # 進捗管理用の変数を初期化
    progress_tracker = {'total': len(destinations), 'completed': 0}

    # 各ウェブサイトの処理タスクを作成
    tasks = [process_website(destination, semaphore, progress_tracker) for destination in destinations]

    # タスクを実行
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
