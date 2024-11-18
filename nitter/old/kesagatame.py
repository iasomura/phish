import logging
from logging.handlers import RotatingFileHandler
import feedparser
import schedule
import time
import re
import requests
import os
import json
import config

# ログファイルの設定
log_file = config.NITTER_LOG

# ローテーションするログハンドラを設定 (最大ファイルサイズ: 5MB, バックアップ: 5ファイルまで)
handler = RotatingFileHandler(log_file, maxBytes=100 * 1024, backupCount=5)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)

# ルートロガーにハンドラを追加
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

# デファングされたURLを元の形式に戻す
def defang_to_url(defanged_url):
    return defanged_url.replace("hxxp", "http").replace("[.]", ".").replace("[:]", ":").replace("<br", "").replace("</p>", "")

# 最新のguidをロード
def load_latest_feed():
    if os.path.exists(config.LATEST_FEED_FILE):
        with open(config.LATEST_FEED_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logging.warning("JSONファイルが空です。最初の実行として処理します。")
                return None
    return None

# 最新のguidを保存
def save_latest_feed(latest_guid):
    with open(config.LATEST_FEED_FILE, 'w') as f:
        json.dump(latest_guid, f)

# フィード内容の前処理 - 不正なタグや不要な部分を除去
def clean_xml_content(content):
    cleaned_content = re.sub(r'<[^>]*mismatched[^>]*>', '', content)
    return cleaned_content

# 取得したURLをテキストファイルに書き出す関数
def write_urls_to_file(urls, file_path):
    try:
        with open(file_path, 'a') as f:  # 追記モードで開く
            for url in urls:
                f.write(url + '\n')
        logging.info(f"URLをファイルに書き出しました: {file_path}")
    except Exception as e:
        logging.error(f"URLの書き出しエラー: {e}")

# RSSをチェックして更新があればhxxpから始まるURLを取得して元に戻す
def check_rss():
    try:
        # ヘッダーとCookieの設定
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        response = requests.get(config.RSS_FEED_URL, headers=headers)
        
        if response.status_code != 200:
            logging.error(f"RSSフィード取得エラー: ステータスコード {response.status_code}")
            return

        # フィード内容を事前にクリーンアップ
        cleaned_content = clean_xml_content(response.text)

        # RSSフィードを解析
        feed = feedparser.parse(cleaned_content)
        if feed.bozo:
            logging.warning(f"RSS解析エラー: {feed.bozo_exception} - 解析を続行します。")

        latest_guid = load_latest_feed()  # 最新のguidをロード
        new_latest_guid = None
        new_entries = []

        # フィードエントリの解析
        for entry in feed.entries:
            if latest_guid and entry.guid == latest_guid:
                break  # 既に取得済みのエントリに到達したらループを終了

            # 新しいエントリを収集
            new_entries.append(entry)

            # 一番最新のエントリのguidを保存する準備
            if new_latest_guid is None:
                new_latest_guid = entry.guid

        # 新しいエントリをログに出力（差分すべてを処理）
        for entry in reversed(new_entries):  # 新しいものから順に処理
            defanged_urls = re.findall(r'hxxp[s]?://[^\s]+', entry.description)
            if defanged_urls:
                logging.info(f"更新: {entry.title}")
                urls_to_write = []  # 書き込むURLリスト
                for defanged_url in defanged_urls:
                    original_url = defang_to_url(defanged_url)
                    logging.info(f"デファングURL: {defanged_url} -> 元のURL: {original_url}")
                    urls_to_write.append(original_url)  # URLをリストに追加

                # 取得したURLが存在すれば書き出す
                if urls_to_write:
                    write_urls_to_file(urls_to_write, config.URL_OUTPUT_FILE)
                else:
                    logging.info("新しいURLが見つかりませんでした。")

        # 最新のguidを保存
        if new_latest_guid:
            save_latest_feed(new_latest_guid)

    except Exception as e:
        logging.error(f"RSSフィード取得エラー: {e}")
        if response.text:
            logging.error(f"レスポンス内容: {response.text}")

# 1分ごとに実行するスケジュールを設定
schedule.every(1).minutes.do(check_rss)

logging.info("RSSの監視を開始します...")
while True:
    try:
        schedule.run_pending()
        time.sleep(15)
    except Exception as e:
        logging.error(f"スケジュール実行中のエラー: {e}")
