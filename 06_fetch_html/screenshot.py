import asyncio
import logging
from pyppeteer import launch

# Torのプロキシ設定
#TOR_PROXY = 'socks5://127.0.0.1:9050'
TOR_PROXY = 'http://localhost:8888'


async def capture_screenshot(url, user_agent, filename, timeout=180):
    """
    指定されたURLのスクリーンショットをTor経由で取得する
    
    :param url: スクリーンショットを取得するURL
    :param user_agent: 使用するユーザーエージェント
    :param filename: スクリーンショットの保存先ファイル名
    :param timeout: タイムアウト時間（秒）
    :return: スクリーンショットの取得に成功したかどうか（boolean）
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
        
        #await asyncio.wait_for(page.goto(url), timeout=timeout)
        await asyncio.wait_for(page.goto(url, {'waitUntil': 'networkidle2'}), timeout=timeout)
        # 10秒間待機
        await asyncio.sleep(10)
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
        if browser:
            await browser.close()

# 使用例
async def main():
    url = "https://example.com"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    filename = "screenshot.png"
    
    success = await capture_screenshot(url, user_agent, filename)
    if success:
        print("Screenshot captured successfully.")
    else:
        print("Failed to capture screenshot.")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
