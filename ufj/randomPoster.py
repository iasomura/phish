import requests
import random
import string
import subprocess
import time
from urllib.parse import urlparse

# Torプロキシの設定
use_tor_proxy = False  # Torプロキシを使用する場合はTrue、使用しない場合はFalseに設定
proxies = {
    'http': 'socks5h://localhost:9050',
    'https': 'socks5h://localhost:9050'
} if use_tor_proxy else None

def restart_tor():
    """Torプロキシを再起動する"""
    print("Restarting Tor proxy...")
    try:
        # Torの再起動コマンド
        subprocess.run(["sudo", "systemctl", "restart", "tor"], check=True)
        # Torが再起動するのを待つ
        time.sleep(5)
        print("Tor proxy restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error restarting Tor proxy: {e}")

def generate_session_id():
    """32文字のランダムな文字列を生成する"""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(32))

def generate_random_values():
    print("Generating random values...")
    # val1: 3桁のランダムな数字
    val1 = str(random.randint(100, 999))
    
    # val2: 4861811に似せたランダムな数字（同じ桁数の範囲内）
    val2_base = 4861811
    val2 = str(random.randint(val2_base - 10000, val2_base + 10000))
    
    # val3: 8から12桁のランダムなパスワード
    val3_length = random.randint(8, 12)
    val3 = ''.join(random.choices(string.ascii_letters + string.digits, k=val3_length))
    
    # val4: 6桁のランダムな数字
    val4 = ''.join(random.choices(string.digits, k=6))
    
    # val5: 090で始まる8桁のランダムな携帯電話番号
    val5 = '090' + ''.join(random.choices(string.digits, k=8))
    
    # val6: ランダムなメールアドレス
    val6_username_length = random.randint(5, 10)
    val6_domain_length = random.randint(3, 7)
    val6_username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=val6_username_length))
    val6_domain = ''.join(random.choices(string.ascii_lowercase, k=val6_domain_length))
    val6 = f"{val6_username}@{val6_domain}.com"
    
    print(f"Random values generated - Val1: {val1}, Val2: {val2}, Val3: {val3}, Val4: {val4}, Val5: {val5}, Val6: {val6}")
    return val1, val2, val3, val4, val5, val6

def send_post_request(url, val1, val2, val3, val4, val5, val6, proxies):
    print(f"Sending POST request to {url} using proxies {proxies}...")
    session_id = generate_session_id()
    parsed_url = urlparse(url)
    host = parsed_url.netloc

    headers = {
        'Host': host,
        'Cookie': f'sessionid={session_id}; msg=true',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Mobile/15E148 Snapchat/10.77.5.59 (like Safari/604.1)',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'application/json, text/plain, */*',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Accept-Language': 'ja',
        'Origin': url,
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': url,
        'Priority': 'u=1, i',
        'Content-Length': '91'
    }

    data = {
        "Origin": "UFJ",
        "Val1": val1,
        "Val2": val2,
        "Val3": val3,
        "Val4": val4,
        "Val5": val5,
        "Val6": val6,
        "Page": "login"
    }

    try:
        response = requests.post(f'{url}/public/submit', headers=headers, json=data, proxies=proxies, verify=False, timeout=10)
        response.raise_for_status()  # HTTPエラーが発生した場合に例外をスロー
        print("POST request sent successfully.")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error sending POST request: {e}")
        return None

# URLをurl.txtから読み込む
print("Reading URLs from url.txt...")
with open('url.txt', 'r') as file:
    urls = file.readlines()

urls = [url.strip() for url in urls if url.strip()]

num_requests = int(input("Enter the number of POST requests to send for each URL: "))

for url in urls:
    print(f"Processing URL: {url}")
    
    for _ in range(num_requests):
        if use_tor_proxy:
            # Torプロキシを再起動
            restart_tor()

        # ランダムな値を生成
        val1, val2, val3, val4, val5, val6 = generate_random_values()

        # POSTリクエストを送信
        response = send_post_request(url, val1, val2, val3, val4, val5, val6, proxies)
        if response:
            print('Status Code:', response.status_code)
            print('Response Text:', response.text)
        else:
            print(f"Failed to send POST request to {url}.")
