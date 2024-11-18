import json
import os

def load_db_config(config_file="config.json"):
    """
    config.jsonからデータベース接続情報をロードする関数

    Args:
        config_file (str, optional): configファイルのパス. Defaults to "config.json".
    """
    try:
        # 実行ファイルのディレクトリを基準にconfigファイルのパスを構築
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config['database']
    
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        # 設定ファイルが存在しない場合やJSON形式が不正な場合のデフォルト設定
        return {
            'host': 'localhost',
            'database': 'website_data',
            'user': 'postgres',
            'password': 'asomura',
            'port': '5432'
        }
