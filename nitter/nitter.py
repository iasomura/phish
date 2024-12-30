# main.py
import logging
from logging.handlers import RotatingFileHandler
import feedparser
import schedule
import time
import re
import requests
from requests.exceptions import RequestException
import os
import json
from datetime import datetime
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
import config
import socket
import socks

class RSSMonitor:
    def __init__(self, feed_config):
        self.feed_url = feed_config['url']
        self.feed_name = feed_config['name']
        
        # ディレクトリの作成
        os.makedirs(config.LOG_DIR, exist_ok=True)
        
        # ファイルパスの設定
        self.latest_feed_file = os.path.join(config.LOG_DIR, f"latest_feed_{self.feed_name}.json")
        
        # データベース設定の読み込み
        self.db_config = config.load_db_config()

        # Tor設定の適用
        if hasattr(config, 'USE_TOR') and config.USE_TOR:
            self.setup_tor()

    def setup_tor(self):
        """Tor接続の設定"""
        socks.set_default_proxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
        socket.socket = socks.socksocket
        logging.info("Tor proxy configuration applied")

    def restart_tor(self):
        """Torを再起動する"""
        try:
            # Torサービスを再起動
            os.system('sudo systemctl restart tor')
            # 再起動完了まで待機
            time.sleep(10)  
            logging.info("Tor service restarted successfully")
            
            # 新しいIPアドレスの確認
            session = self.get_session()
            try:
                response = session.get('https://check.torproject.org/')
                if 'Congratulations' in response.text:
                    logging.info("Successfully connected to Tor with new IP")
                    return True
            except Exception as e:
                logging.error(f"Failed to verify new Tor connection: {e}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to restart Tor: {e}")
            return False

    def check_rss_with_new_ip(self):
        """Torを再起動してから RSS チェックを実行"""
        if hasattr(config, 'USE_TOR') and config.USE_TOR:
            if not self.restart_tor():
                logging.error("Skipping RSS check due to Tor restart failure")
                return
        
        self.check_rss()

    def get_session(self):
        """リクエストセッションを取得"""
        session = requests.Session()
        if hasattr(config, 'USE_TOR') and config.USE_TOR:
            session.proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }
        return session

    def check_tor_connection(self):
        """Tor接続のテスト"""
        try:
            session = self.get_session()
            response = session.get('https://check.torproject.org/')
            return 'Congratulations' in response.text
        except Exception as e:
            logging.error(f"Tor connection test failed: {e}")
            return False

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

    def extract_domain_from_url(self, url):
        """URLからドメインを抽出する"""
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc

    def is_url_registered(self, cursor, normalized_url):
        """URLがすでに登録されているかを確認"""
        query = "SELECT 1 FROM website_data WHERE url = %s"
        cursor.execute(query, (normalized_url,))
        return cursor.fetchone() is not None

    def insert_url_to_db(self, url):
        """URLをデータベースに挿入"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            normalized_url = self.normalize_url(url)
            domain = self.extract_domain_from_url(normalized_url)

            # URLが既に登録されているか確認
            if self.is_url_registered(cursor, normalized_url):
                logging.info(f"{self.feed_name}: URL already registered: {normalized_url}")
                return

            # 固定値の設定
            phish_from = self.feed_name
            sql_query = """
                INSERT INTO website_data 
                (status, last_update, phish_from, url, phish_id, phish_detail_url, 
                phish_ip_address, cidr_block, verified, online_status, target, domain)
                VALUES (0, now(), %s, %s, NULL, NULL, NULL, NULL, FALSE, FALSE, NULL, %s)
                ON CONFLICT (domain) DO NOTHING
            """

            cursor.execute(sql_query, (phish_from, normalized_url, domain))
            conn.commit()
            logging.info(f"{self.feed_name}: Inserted URL to database: {normalized_url}")

            # 関連スクリプトの実行
            self.run_analysis_scripts()

        except psycopg2.Error as e:
            logging.error(f"{self.feed_name}: Database error: {e}")
        finally:
            if 'conn' in locals():
                cursor.close()
                conn.close()

    def run_analysis_scripts(self):
        """分析スクリプトを実行"""
        # スクリプトのある親ディレクトリのパスを取得
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        scripts = [
            "01_domain_status.py",
            "02_whois.py",
            "03_dig_data.py",
            "04_ip_info.py",
            "05_whois_ip.py",
            "06_fetch_html/main.py"
        ]
        
        for script in scripts:
            try:
                script_path = os.path.join(parent_dir, script)
                os.system(f"python {script_path}")
                logging.info(f"{self.feed_name}: Executed {script}")
            except Exception as e:
                logging.error(f"{self.feed_name}: Error running {script}: {e}")

    def defang_to_url(self, defanged_url):
        """デファングされたURLを元の形式に戻す"""
        return defanged_url.replace("hxxp", "http").replace("[.]", ".").replace("[:]", ":").replace("<br", "").replace("</p>", "")
    
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
            session = self.get_session()
            
            # Tor使用時は接続テスト
            if hasattr(config, 'USE_TOR') and config.USE_TOR:
                if not self.check_tor_connection():
                    logging.error("Tor connection test failed. Skipping RSS check.")
                    return

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br'
            }
            
            response = session.get(self.feed_url, headers=headers, timeout=30)
            
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

        except requests.exceptions.ProxyError as e:
            logging.error(f"{self.feed_name}: Torプロキシ接続エラー: {e}")
        except RequestException as e:
            logging.error(f"{self.feed_name}: ネットワークエラー: {e}")
        except Exception as e:
            logging.error(f"{self.feed_name}: 予期せぬエラー: {e}")

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
    monitors = [RSSMonitor(feed_config) for feed_config in config.RSS_FEEDS]
    
    # スケジュール設定
    for monitor in monitors:
        schedule.every(10).minutes.do(monitor.check_rss_with_new_ip)
        logging.info(f"{monitor.feed_name}: 監視を開始します...")
    
    # メインループ
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにスケジュールをチェック
        except KeyboardInterrupt:
            logging.info("プログラムを終了します...")
            break
        except Exception as e:
            logging.error(f"スケジュール実行中のエラー: {e}")
            time.sleep(60)  # エラー時は1分待機してから再試行

if __name__ == "__main__":
    main()
