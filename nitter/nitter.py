import logging
from logging.handlers import RotatingFileHandler
import requests
import os
import re
import json
from datetime import datetime
from urllib.parse import urlparse
import config

# Tor用プロキシ設定
PROXIES = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050",
}

class NitterMonitor:
    def __init__(self, feed_config):
        self.feed_url = feed_config['url']
        self.feed_name = feed_config['name']

        # ディレクトリの作成
        os.makedirs(config.LOG_DIR, exist_ok=True)

        # ファイルパスの設定
        self.latest_feed_file = os.path.join(config.LOG_DIR, f"latest_feed_{self.feed_name}.json")

    def normalize_url(self, url):
        """URLを正規化する"""
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme.lower() if parsed_url.scheme else 'http'
        netloc = parsed_url.netloc.lower()
        path = parsed_url.path
        params = parsed_url.params
        query = parsed_url.query
        fragment = parsed_url.fragment
        normalized_url = f"{scheme}://{netloc}{path}"
        if params:
            normalized_url += f";{params}"
        if query:
            normalized_url += f"?{query}"
        if fragment:
            normalized_url += f"#{fragment}"
        return normalized_url

    def defang_to_url(self, defanged_url):
        """デファングされたURLを元の形式に戻す"""
        return defanged_url.replace("hxxp", "http").replace("[.]", ".").replace("[:", ":")

    def load_latest_feed(self):
        """最新のフィードGUIDを読み込む"""
        if os.path.exists(self.latest_feed_file):
            with open(self.latest_feed_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logging.warning(f"{self.feed_name}: JSONファイルが空です。最初の実行として処理します。")
                    return None
        return None

    def save_latest_feed(self, latest_guid):
        """最新のフィードGUIDを保存"""
        with open(self.latest_feed_file, 'w') as f:
            json.dump(latest_guid, f)

    def clean_xml_content(self, content):
        """XMLコンテンツから不正なタグを除去"""
        return re.sub(r'<[^>]*mismatched[^>]*>', '', content)

    def check_rss(self):
        """RSSフィードをチェックして更新を処理"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br'
            }

            # Torプロキシ経由でリクエストを送信
            response = requests.get(self.feed_url, headers=headers, proxies=PROXIES, timeout=30)

            if response.status_code != 200:
                logging.error(f"{self.feed_name}: RSSフィード取得エラー: ステータスコード {response.status_code}")
                return

            cleaned_content = self.clean_xml_content(response.text)
            feed = feedparser.parse(cleaned_content)

            if feed.bozo:
                logging.warning(f"{self.feed_name}: RSS解析警告: {feed.bozo_exception}")

            latest_guid = self.load_latest_feed()
            new_latest_guid = None
            new_entries = []

            for entry in feed.entries:
                if latest_guid and entry.guid == latest_guid:
                    break
                new_entries.append(entry)
                if new_latest_guid is None:
                    new_latest_guid = entry.guid

            for entry in reversed(new_entries):
                defanged_urls = re.findall(r'hxxp[s]?://[^\s]+', entry.description)
                if defanged_urls:
                    logging.info(f"{self.feed_name} 更新: {entry.title}")
                    for defanged_url in defanged_urls:
                        url = self.defang_to_url(defanged_url)
                        self.insert_url_to_db(url)

            if new_latest_guid:
                self.save_latest_feed(new_latest_guid)

        except requests.RequestException as e:
            logging.error(f"{self.feed_name}: ネットワークエラー: {e}")
        except Exception as e:
            logging.error(f"{self.feed_name}: 予期せぬエラー: {e}")

    def insert_url_to_db(self, url):
        """URLをデータベースに挿入（仮実装、具体的なコードはmain.py参照）"""
        logging.info(f"{self.feed_name}: 仮実装 - URLを挿入: {url}")


# ログ設定
def setup_logging():
    """ログ設定をセットアップ"""
    os.makedirs(config.LOG_DIR, exist_ok=True)
    log_file = os.path.join(config.LOG_DIR, config.NITTER_LOG)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=100 * 1024,  # 100KB
        backupCount=5,
        encoding='utf-8'
    )
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def main():
    """メイン処理"""
    setup_logging()

    # 監視インスタンスの作成
    monitors = [NitterMonitor(feed_config) for feed_config in config.NITTER_FEEDS]

    # スケジュール設定
    for monitor in monitors:
        monitor.check_rss()


if __name__ == "__main__":
    main()
