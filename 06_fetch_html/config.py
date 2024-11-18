import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """統合設定管理クラス"""
    
    def __init__(self):
        # 環境変数の読み込み
        load_dotenv()
        
        # ベースとなるパスの設定
        self.BASE_DIR = Path(os.getenv('BASE_DIR', '/home/asomura/waseda/nextstep'))
        
        # 各種パスの設定
        self.BASEFOLDER = Path(os.getenv('IMAGES_PATH', str(self.BASE_DIR / 'images')))
        self.BASEFOLDER_MHTML = Path(os.getenv('MHTML_PATH', str(self.BASE_DIR / 'mhtml')))
        
        # データベース設定
        self.DB_CONFIG = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'name': os.getenv('DB_NAME', 'website_data'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'asomura')  # デフォルト値は開発用
        }
        
        # ユーザーエージェント設定
        self.USER_AGENTS = {
            'Chrome': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                     'Chrome/123.0.0.0 Safari/537.36',
            'Android': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/124.0.6367.113 Mobile Safari/537.36',
            'iPhone': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_4_1 like Mac OS X) AppleWebKit/605.1.15 '
                     '(KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1 OPT/4.1.1'
        }
        
        # その他の定数
        self.MAX_REDIRECTS = int(os.getenv('MAX_REDIRECTS', '10'))
        
        # 初期化時にディレクトリを確認・作成
        self.ensure_directories()

    def ensure_directories(self) -> None:
        """必要なディレクトリが存在することを確認し、必要に応じて作成"""
        self.BASEFOLDER.mkdir(parents=True, exist_ok=True)
        self.BASEFOLDER_MHTML.mkdir(parents=True, exist_ok=True)

    def get_db_url(self) -> str:
        """データベースURLを生成（パスワードは隠蔽）"""
        return (f"postgresql://{self.DB_CONFIG['user']}:****@"
                f"{self.DB_CONFIG['host']}/{self.DB_CONFIG['name']}")

    def get_user_agent(self, device: str) -> str:
        """指定されたデバイスのユーザーエージェントを取得"""
        return self.USER_AGENTS.get(device, self.USER_AGENTS['Chrome'])

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で取得（デバッグ用）"""
        return {
            'basefolder': str(self.BASEFOLDER),
            'basefolder_mhtml': str(self.BASEFOLDER_MHTML),
            'database': {
                'host': self.DB_CONFIG['host'],
                'name': self.DB_CONFIG['name'],
                'user': self.DB_CONFIG['user'],
                'password': '****'  # パスワードは隠蔽
            },
            'user_agents': self.USER_AGENTS,
            'max_redirects': self.MAX_REDIRECTS
        }

# シングルトンインスタンスの作成
config = Config()

# 使いやすいように主要な設定値をモジュールレベルで公開
DB_HOST = config.DB_CONFIG['host']
DB_NAME = config.DB_CONFIG['name']
DB_USER = config.DB_CONFIG['user']
DB_PASSWORD = config.DB_CONFIG['password']
BASEFOLDER = config.BASEFOLDER
BASEFOLDER_MHTML = config.BASEFOLDER_MHTML
MAX_REDIRECTS = config.MAX_REDIRECTS
USER_AGENTS = config.USER_AGENTS
