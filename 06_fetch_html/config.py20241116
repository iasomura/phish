import json
import os

def load_config():
    """設定ファイルを読み込む"""
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_file, 'r') as f:
        return json.load(f)

# 設定を読み込む
config = load_config()

# データベース接続情報
DB_HOST = config['database']['host']
DB_NAME = config['database']['name']
DB_USER = config['database']['user']
DB_PASSWORD = config['database']['password']

# ユーザーエージェント設定
USER_AGENTS = {
    'Chrome': config['Chrome'],
    'Android': config['Android'],
    'iPhone': config['iPhone']
}

# フォルダ設定
BASEFOLDER = config['basefolder']
BASEFOLDER_MHTML = config['basefolder_mhtml']

# その他の定数
MAX_REDIRECTS = 10  # リダイレクトの最大回数
