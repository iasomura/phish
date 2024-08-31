#、Majestic Million リストを使用します。これは、ウェブ上で最も人気のある100万ドメインのリストです。
#以下は、Majestic Million リストを使用して上位のサイトを取得し、それらのURLを検証する修正版Pythonスクリプトです：

import csv
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import io

def get_top_domains(limit=30000):
    url = "https://downloads.majestic.com/majestic_million.csv"
    response = requests.get(url)
    csv_content = io.StringIO(response.text)
    csv_reader = csv.reader(csv_content)
    next(csv_reader)  # ヘッダーをスキップ
    return [row[2] for row in csv_reader][:limit]  # Domain列を取得

def validate_url(domain):
    try:
        url = f'https://{domain}'
        response = requests.get(url, timeout=5, allow_redirects=True)
        final_url = response.url
        parsed_url = urlparse(final_url)
        return {
            'domain': domain,
            'final_url': final_url,
            'scheme': parsed_url.scheme,
            'status_code': response.status_code
        }
    except Exception as e:
        return {
            'domain': domain,
            'final_url': '',
            'scheme': '',
            'status_code': str(e)
        }

def main():
    print("Fetching top domains from Majestic Million...")
    domains = get_top_domains()
    
    print("Validating URLs...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(validate_url, domains))
    
    print("Saving results to CSV...")
    with open('top_sites.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['domain', 'final_url', 'scheme', 'status_code']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print("Done!")

if __name__ == "__main__":
    main()
