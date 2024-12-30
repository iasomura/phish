# Tor設定
USE_TOR = True  # TorプロキシをON/OFF
TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

# データベース設定
def load_db_config():
    return {
        'host': 'localhost',
        'database': 'website_data',
        'user': 'postgres',
        'password': 'asomura',
        'port': '5432'
    }

# RSSフィード設定
RSS_FEEDS = [
    {
        'name': 'KesaGataMe0',
        'url': 'https://nitter.poast.org/KesaGataMe0/rss'
    },
    {
        'name': 'naomisuzuki_',
        'url': 'https://nitter.poast.org/naomisuzuki_/rss'
    },
    {
        'name': 'harugasumi',
        'url': 'https://nitter.poast.org/harugasumi/rss'
    },
    { 
        'name': 'bubobubo_lover',
        'url': 'https://nitter.poast.org/bubobubo_lover/rss'
    },
    { 
        'name': 'catnap707',
        'url': 'https://nitter.poast.org/catnap707/rss'
    }
    # 必要に応じて他のフィードを追加
]

# ログ設定
LOG_DIR = 'logs'
NITTER_LOG = 'nitter.log'
