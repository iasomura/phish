import requests
import random
import string
from urllib.parse import urlparse

# Torプロキシの設定
use_tor_proxy = False  # Torプロキシを使用する場合はTrue、使用しない場合はFalseに設定
proxies = {
    'http': 'socks5h://localhost:9050',
    'https': 'socks5h://localhost:9050'
} if use_tor_proxy else None

def generate_session_id():
    """32文字のランダムな文字列を生成する"""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(32))

def generate_random_values():
    print("Step 2: Generating random values...")
    # val1: 3桁のランダムな数字
    val1 = str(random.randint(100, 999))
    
    # val2: 4861811に似せたランダムな数字（同じ桁数の範囲内）
    val2_base = 4861811
    val2 = str(random.randint(val2_base - 10000, val2_base + 10000))
    
    # val3: 8から12桁のランダムなパスワード
    val3_length = random.randint(8, 12)
    val3 = ''.join(random.choices(string.ascii_letters + string.digits, k=val3_length))
    
    print(f"Random values generated - Val1: {val1}, Val2: {val2}, Val3: {val3}")
    return val1, val2, val3

def send_post_request(url, val1, val2, val3):
    print("Step 3: Sending POST request...")
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
print("Step 0: Reading URL from url.txt...")
with open('url.txt', 'r') as file:
    url = file.read().strip()

print(f"URL read: {url}")

# ランダムな値を生成
val1, val2, val3 = generate_random_values()

# POSTリクエストを送信
response = send_post_request(url, val1, val2, val3)
if response:
    print('Status Code:', response.status_code)
    print('Response Text:', response.text)
else:
    print("Failed to send POST request. Exiting...")
