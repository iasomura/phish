import logging
from pyppeteer import launch
from database import execute_sql
import psycopg2
import asyncio


# Torのプロキシ設定
#TOR_PROXY = 'socks5://127.0.0.1:9050'
TOR_PROXY = 'http://localhost:8888'


async def fetch_website_as_mhtml(url, user_agent, website_id):
    """
    指定されたURLのウェブサイトをMHTML形式で取得する
    
    :param url: 取得対象のURL
    :param user_agent: 使用するユーザーエージェント
    :param website_id: ウェブサイトのID
    :return: 取得したURL（成功時）またはNone（失敗時）
    """
    browser = None
    try:
        # プロキシを使用せずにブラウザを起動
        browser = await launch(headless=True, args=['--no-sandbox'])
        # Torプロキシを使用するようにブラウザを設定
        #browser = await launch(headless=True, args=[
        #    '--no-sandbox',
        #    f'--proxy-server={TOR_PROXY}'
        #])
        page = await browser.newPage()
        await page.setUserAgent(user_agent)
        
        # プロキシ認証が必要な場合は以下のコメントを解除して設定してください
        # await page.authenticate({'username': 'your_username', 'password': 'your_password'})
        
        await page.goto(url, {'waitUntil': 'networkidle2'})
        # 10秒間待機
        await asyncio.sleep(10)
        cdp = await page._client.send('Page.captureSnapshot', {'format': 'mhtml'})
        mhtml_content = cdp['data']
        if mhtml_content:
            logging.info("Successfully fetched MHTML content")
            mhtml_content_bytes = mhtml_content.encode('utf-8')
            await update_mhtml_content(website_id, user_agent, mhtml_content_bytes)
        else:
            logging.warning("No MHTML content fetched")
        return url
    except Exception as e:
        logging.error(f"Failed to fetch MHTML content: {e}")
        return None
    finally:
        if browser:
            await browser.close()

async def update_mhtml_content(website_id, user_agent, mhtml_content_bytes):
    """
    取得したMHTMLコンテンツをデータベースに保存する
    
    :param website_id: ウェブサイトのID
    :param user_agent: 使用したユーザーエージェント
    :param mhtml_content_bytes: MHTMLコンテンツ（バイト列）
    """
    from config import USER_AGENTS
    
    if user_agent == USER_AGENTS['Chrome']:
        sql = "UPDATE website_data SET mhtml_pc_site = %s, status = 6, last_update = NOW() WHERE id = %s"
    elif user_agent == USER_AGENTS['iPhone']:
        sql = "UPDATE website_data SET mhtml_mobile_site_iphone = %s, status = 6, last_update = NOW() WHERE id = %s"
    elif user_agent == USER_AGENTS['Android']:
        sql = "UPDATE website_data SET mhtml_mobile_site_android = %s, status = 6, last_update = NOW() WHERE id = %s"
    else:
        logging.error(f"Unknown user agent: {user_agent}")
        return
    try:
        await execute_sql(sql, psycopg2.Binary(mhtml_content_bytes), website_id)
        logging.info(f"Updated website_data for {website_id} with status 6")
    except Exception as e:
        logging.error(f"Failed to update website_data for {website_id}: {e}")
