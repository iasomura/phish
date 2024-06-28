import requests
import random
import string
import subprocess
import time
from requests.exceptions import RequestException, HTTPError, Timeout, TooManyRedirects

# Torプロキシの設定
use_tor_proxy = True  # Torプロキシを使用する場合はTrue、使用しない場合はFalseに設定
tor_proxy_address = 'socks5h://localhost:9050'
proxies = {
    'http': tor_proxy_address,
    'https': tor_proxy_address
} if use_tor_proxy else None

# Torプロキシを再起動する関数
def restart_tor_proxy():
    if use_tor_proxy:
        try:
            subprocess.call(['sudo', 'systemctl', 'restart', 'tor'])
            time.sleep(5)  # Torが再起動するまで待機
        except Exception as e:
            print(f"Error restarting Tor proxy: {e}")

# URLリストを読み込む関数
def read_urls_from_file(filename='url.txt'):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

# GETリクエストでクッキーを取得する関数
def get_initial_cookies(url):
    headers = {
        'Accept-Language': 'ja',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Mobile/15E148 Snapchat/10.77.5.59 (like Safari/604.1)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Encoding': 'gzip, deflate, br',
        'Priority': 'u=0, i'
    }
    
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        response.raise_for_status()
        return response.cookies, response.headers.get('Set-Cookie')
    except (RequestException, HTTPError, Timeout, TooManyRedirects) as e:
        print(f"Error obtaining initial cookies: {e}")
        return None, None

# リダイレクトURLを取得する関数
def get_redirect_location(url, cookies):
    headers = {
        'Accept-Language': 'ja',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Mobile/15E148 Snapchat/10.77.5.59 (like Safari/604.1)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Encoding': 'gzip, deflate, br',
        'Priority': 'u=0, i'
    }

    try:
        response = requests.get(url, headers=headers, cookies=cookies, allow_redirects=False, proxies=proxies, timeout=10)
        response.raise_for_status()
        return response.headers['Location']
    except (RequestException, HTTPError, Timeout, TooManyRedirects) as e:
        print(f"Error obtaining redirect location: {e}")
        return None

# POSTリクエストを送信する関数
def send_post_request(host, redirect_location, cookies):
    url = f"{host}{redirect_location}"
    headers = {
        'Accept-Language': 'ja',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Mobile/15E148 Snapchat/10.77.5.59 (like Safari/604.1)',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': '*/*',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': host,
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': f'{host}/sigin/loginpw.php',
        'Accept-Encoding': 'gzip, deflate, br',
        'Priority': 'u=1, i'
    }
    
    # ランダムなlogin_idとlogin_pwを生成
    login_id = ''.join(random.choices(string.digits, k=8))
    login_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    data = {
        'login_id': login_id,
        'login_pw': login_pw
    }
    
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=data, proxies=proxies, timeout=10)
        response.raise_for_status()
        return response
    except (RequestException, HTTPError, Timeout, TooManyRedirects) as e:
        print(f"Error sending POST request: {e}")
        return None

# 実行
def execute_requests(num_requests):
    urls = read_urls_from_file()
    for i in range(num_requests):
        for url in urls:
            print(f"\nExecuting request {i + 1} for URL: {url}")
            if use_tor_proxy:
                print("Restarting Tor proxy...")
                restart_tor_proxy()
            cookies, initial_cookie = get_initial_cookies(url)
            if not cookies:
                print("Failed to obtain initial cookies. Skipping to next request.")
                continue

            redirect_location = get_redirect_location(url, cookies)
            if redirect_location:
                response = send_post_request(url, redirect_location, cookies)
                if response:
                    print('Status Code:', response.status_code)
                    print('Response Text:', response.text)
                    print('Generated login_id:', response.request.body.split(b'&')[0].decode().split('=')[1])
                    print('Generated login_pw:', response.request.body.split(b'&')[1].decode().split('=')[1])
                    print('Response Headers:', response.headers)
                    print('Response Cookies:', response.cookies)
                else:
                    print("POST request failed.")
            else:
                print("Failed to get redirect location.")

# 任意の回数リクエストを送信
num_requests = 5  # ここに希望する回数を入力
execute_requests(num_requests)
