import asyncio
import asyncpg
import psycopg2
import json
import os
import logging
import aiohttp
from pyppeteer import launch
from datetime import datetime
import hashlib

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

# 非同期でSQLを実行する関数
async def execute_sql(sql, *params):
    conn = None
    try:
        # データベースに接続
        logging.debug("Connecting to database...")
        conn = await asyncpg.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        logging.debug("Connected to database. Executing SQL...")
        # SQLクエリを実行
        await conn.execute(sql, *params)
        logging.debug("SQL executed.")
        logging.info(f"{datetime.now().isoformat()} - Executed SQL: {sql} with params: {params}")
    except Exception as error:
        # エラーログを記録
        logging.error(f"{datetime.now().isoformat()} - Database Error: {str(error)}")
    finally:
        # データベース接続を閉じる
        if conn:
            await conn.close()
            logging.debug("Connection closed.")
        logging.debug("Exiting execute_sql")

# ウェブサイトのHTMLコンテンツをMHTML形式で取得する関数
async def fetch_website_as_mhtml(url, user_agent):
    browser = None
    try:
        # Pyppeteerでブラウザを起動
        browser = await launch(headless=True, args=['--no-sandbox'])
        page = await browser.newPage()
        # ユーザーエージェントを設定
        await page.setUserAgent(user_agent)
        # 指定されたURLに移動
        await page.goto(url)
        # MHTML形式でページを保存
        response = await page._client.send('Page.captureSnapshot', {'format': 'mhtml'})
        mhtml_content = response.get('data')  # 'data'キーの値を取得
        # MHTMLコンテンツをバイナリに変換（UTF-8エンコードは不要）
        mhtml_content = mhtml_content.encode('utf-8')

        return mhtml_content
    except Exception as e:
        logging.error(f"Failed to fetch MHTML content: {e}")
        return None
    finally:
        # ブラウザを閉じる
        if browser:
            await browser.close()


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

# ウェブサイトを処理するメインの関数
async def process_website(destination, semaphore, progress_tracker):
    website_id, domain, url, url_pc_site, url_mobile_site = destination
    logging.info(f"Processing website: {domain}")

    # 取得するURLを決定
    target_url = url or url_pc_site or f"https://{domain}"
    mobile_target_url = url_mobile_site or url or f"http://{domain}"

    async with semaphore:
        # 各ユーザーエージェントごとにMHTMLコンテンツを取得
        mhtml_content_pc = await fetch_website_as_mhtml(target_url, user_agents['Chrome'])
        mhtml_content_iphone = await fetch_website_as_mhtml(target_url, user_agents['iPhone'])
        mhtml_content_android = await fetch_website_as_mhtml(target_url, user_agents['Android'])

    # MHTMLコンテンツが取得できた場合
    if mhtml_content_pc or mhtml_content_iphone or mhtml_content_android:
        sql = """
        UPDATE website_data SET 
            mhtml_pc_site = $1, 
            mhtml_mobile_site_iphone = $2, 
            mhtml_mobile_site_android = $3, 
            status = 6, last_update = NOW() 
        WHERE id = $4
        """
        #await execute_sql(sql, psycopg2.Binary(mhtml_content_pc, mhtml_content_iphone, mhtml_content_android, website_id))
        await execute_sql(sql,psycopg2.Binary(mhtml_content_pc),
                          psycopg2.Binary(mhtml_content_iphone),
                          psycopg2.Binary(mhtml_content_android),
                          website_id)

        # 現在の日時とハッシュ値を使ってファイル名を生成
        now = datetime.now()
        filename_prefix = f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}_{domain}_{website_id}_{hashlib.md5(url.encode()).hexdigest()}"
        screenshot_iphone = f"{filename_prefix}_iphone.png"
        screenshot_android = f"{filename_prefix}_android.png"
        screenshot_chrome = f"{filename_prefix}_chrome.png"

        # 各デバイスごとにスクリーンショットを取得
        screenshot_iphone_success = await capture_screenshot(target_url, user_agents['iPhone'], os.path.join(basefolder, screenshot_iphone))
        screenshot_android_success = await capture_screenshot(target_url, user_agents['Android'], os.path.join(basefolder, screenshot_android))
        screenshot_chrome_success = await capture_screenshot(target_url, user_agents['Chrome'], os.path.join(basefolder, screenshot_chrome))

        # スクリーンショットが全て成功したかどうかを確認
        screenshot_availability = screenshot_iphone_success and screenshot_android_success and screenshot_chrome_success
        sql = """
        UPDATE website_data SET 
            screenshot_availability = $1, 
            screenshot_iphone = $2, 
            screenshot_android = $3, 
            screenshot_chrome = $4 
        WHERE id = $5
        """
        await execute_sql(sql, screenshot_availability, screenshot_iphone if screenshot_iphone_success else None, screenshot_android if screenshot_android_success else None, screenshot_chrome if screenshot_chrome_success else None, website_id)


    else:
        # MHTMLコンテンツが取得できなかった場合、ステータスを98に更新
        await execute_sql("UPDATE website_data SET status = 98 WHERE id = $1", website_id)
    
    # 進捗を更新
    progress_tracker['completed'] += 1
    print(f"Progress: {progress_tracker['completed']}/{progress_tracker['total']} websites processed.")
    print(mhtml_content_pc)

# メイン関数
async def main():
    # セマフォを設定して同時実行数を制限
    semaphore = asyncio.Semaphore(5)

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

