import requests
import json
from tqdm import tqdm
import psycopg2

# config.jsonから設定を読み込む
config_path = 'config.json'
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# 使用するUser-Agentを指定
user_agent = config["iPhone"]  # 必要に応じて他のUser-Agentに変更可能

# HTTPリクエストにUser-Agentを追加するためのヘッダー
headers = {
    'User-Agent': user_agent
}

# データベース接続情報
db_config = {
    'dbname': 'website_data',
    'user': 'postgres',
    'password': 'asomura',
    'host': 'localhost'
}

def check_server_status(url):
    http_status = False
    https_status = False

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            if url.startswith("http://"):
                http_status = True
            elif url.startswith("https://"):
                https_status = True
    except requests.RequestException:
        pass

    return http_status, https_status

def url_exists_in_db(url, conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM website_data WHERE url = %s LIMIT 1", (url,))
        return cursor.fetchone() is not None

def main(file_path, output_path):
    with open(file_path, 'r') as file:
        urls = file.readlines()

    urls = [url.strip() for url in urls]

    results = []
    conn = psycopg2.connect(**db_config)

    for url in tqdm(urls, desc="Checking URLs", unit="url"):
        if not url_exists_in_db(url, conn):
            http_status, https_status = check_server_status(url)
            if http_status or https_status:
                results.append((url, http_status, https_status))

    conn.close()

    with open(output_path, 'w') as output_file:
        for url, http_status, https_status in results:
            output_file.write(f"{url}\n")

    for url, http_status, https_status in results:
        print(f"URL: {url}")
        print(f"  HTTP: {'Running' if http_status else 'Not Running'}")
        print(f"  HTTPS: {'Running' if https_status else 'Not Running'}")
        print()

if __name__ == "__main__":
    input_file_path = 'urls.txt'  # URL一覧が記載されたテキストファイルのパスを指定
    output_file_path = 'active_urls.txt'  # 稼働中のURLを保存するファイルのパスを指定
    main(input_file_path, output_file_path)
