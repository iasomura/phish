import csv
import requests
from urllib.parse import urlparse, urlunparse

# ファイル名の定義
csv_file = 'top_sites.csv'
output_file = 'normalSite.txt'

# クエリパラメータを除去したURLを保存する関数
def save_url(url):
    with open(output_file, 'a') as f:
        f.write(url + '\n')

# クエリパラメータを削除する関数
def remove_query_params(url):
    parsed_url = urlparse(url)
    clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))  # クエリとフラグメントを空にする
    return clean_url

# CSVファイルを読み込み、URLを抽出してチェックする処理
with open(csv_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    
    for row in reader:
        if len(row) >= 2:
            url = row[1]
            
            if url:  # URLが存在する場合のみ
                try:
                    # クエリパラメータを削除
                    clean_url = remove_query_params(url)
                    
                    # HTTPリクエストを送信
                    response = requests.get(clean_url, timeout=5)  # タイムアウトを5秒に設定
                    if response.status_code == 200:
                        save_url(clean_url)
                        print(f"200 OK: {clean_url}")
                    else:
                        print(f"Non-200 response: {clean_url}, Status code: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed to access {clean_url}: {e}")
