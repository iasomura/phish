import requests
import asyncio
from pyppeteer import launch

# iPhoneのユーザーエージェント
iphone_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Mobile/15E148 Safari/604.1"
iphone_headers = {"User-Agent": iphone_ua}

# PC版Chromeのユーザーエージェント
chrome_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
chrome_headers = {"User-Agent": chrome_ua}

# 取得するURL
url = "https://dc.watch.impress.co.jp/"

async def get_screenshot(url, headers, filename, width):
    browser = await launch({'headless': True, 'args': ['--user-agent=' + headers["User-Agent"]]})
    page = await browser.newPage()
    await page.setExtraHTTPHeaders(headers)  # 追加: ユーザーエージェントを設定
    await page.goto(url, {'waitUntil': 'networkidle0'})
    
    # ページ全体の高さを取得
    body_height = await page.evaluate("document.body.scrollHeight")
    
    # スクリーンショットの解像度を設定
    await page.setViewport({'width': width, 'height': body_height})
    
    # スクリーンショットを取得
    await page.screenshot({'path': filename, 'fullPage': True})
    
    await browser.close()

async def main():
    # iPhoneのスクリーンショットを取得（横幅は縦向きの解像度）
    await get_screenshot(url, iphone_headers, 'iphone_screenshot.png', 375)

    # PC版Chromeのスクリーンショットを取得（一般的なウェブページの横幅）
    await get_screenshot(url, chrome_headers, 'chrome_screenshot.png', 1280)

# asyncioイベントループを実行
asyncio.get_event_loop().run_until_complete(main())
