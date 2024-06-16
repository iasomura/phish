import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# iPhone 11のユーザーエージェントを設定
#iphone_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Mobile/15E148 Safari/604.1"
iphone_ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

headers = {"User-Agent": iphone_ua}
#headers = {"User-Agent": chrome_ua}

# Yahoo! JAPANにアクセス
url = "https://sportybetbalanceadderweb100x2023org.weebly.com/"
response = requests.get(url, headers=headers)

# レスポンスが正常か確認
if response.status_code == 200:
    # Chrome WebDriverを起動
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # ヘッドレスモード
    options.add_argument(f"--user-agent={iphone_ua}")  # iPhoneのUAを設定
    driver = webdriver.Chrome(options=options)

    # Yahoo! JAPANを開く
    driver.get(url)

    # ページの高さを取得
    page_height = driver.execute_script("return document.body.scrollHeight")

    # ウィンドウサイズを調整
    driver.set_window_size(600, page_height)  # 高さは取得した値を使用

    # ページ全体をスクロール
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # スクリーンショットを撮る
    driver.save_screenshot("yahoo_jp_full.png")

    # WebDriverを終了
    driver.quit()
else:
    print(f"エラー: ステータスコード {response.status_code}")
