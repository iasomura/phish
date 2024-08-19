import requests
import random
import string
import time
import os
import sys

# Torのプロキシ設定
PROXIES = {
    'http': 'socks5h://localhost:9050',
    'https': 'socks5h://localhost:9050'
}

# 1. Torプロキシの再起動（新しいIPを取得）
def renew_tor_ip(use_proxy):
    if use_proxy:
        print("Renewing Tor IP...")
        os.system('sudo systemctl restart tor')
        time.sleep(10)  # TorがIPを更新するのを待つ

# 2. Webサイトのリストをテキストファイルから読み込む
def load_websites(file_path):
    with open(file_path, 'r') as file:
        websites = [line.strip() for line in file.readlines()]
    return websites

# 3. Webサイトにアクセスし、クッキーを取得する
def get_cookies(url, use_proxy):
    access_url = f"https://{url}/servlet/LOGBNK0000000B.do"
    print(f"Accessing {access_url} to get cookies...")
    
    if use_proxy:
        response = requests.get(access_url, proxies=PROXIES)
    else:
        response = requests.get(access_url)
    
    print(f"Cookies received: {response.cookies.get_dict()}")
    return response.cookies.get_dict()

# 4. ランダムな10桁の番号を生成する
def generate_random_number():
    while True:
        number = ''.join(random.choices('1234567890', k=10))
        if number.startswith(('1', '5')):
            print(f"Generated random number: {number}")
            return number

# 5. APIにPOSTリクエストを送り、注文を作成する
def post_to_api(url, cookies, random_number, use_proxy):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Mobile/15E148 Snapchat/10.77.5.59 (like Safari/604.1)',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': '; '.join([f'{key}={value}' for key, value in cookies.items()]),
        'Referer': f'https://{url}',
        'Origin': f'https://{url}'
    }

    data = {
        'order_id': '',
        'order_username': random_number
    }

    print(f"Posting data to https://{url}/api/user/order/createOrder with data: {data}")
    
    if use_proxy:
        response = requests.post(f'https://{url}/api/user/order/createOrder', headers=headers, data=data, proxies=PROXIES)
    else:
        response = requests.post(f'https://{url}/api/user/order/createOrder', headers=headers, data=data)
    
    print(f"Response received: {response.json()}")
    return response.json()

# 6. ランダムなパスワードを生成する
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choices(characters, k=length))
    return password

# 7. APIにランダムなパスワードを送りつける
def update_account_password(url, cookies, order_id, use_proxy):
    random_password = generate_random_password()

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Mobile/15E148 Snapchat/10.77.5.59 (like Safari/604.1)',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': '; '.join([f'{key}={value}' for key, value in cookies.items()]),
        'Referer': f'https://{url}',
        'Origin': f'https://{url}'
    }

    data = {
        'order_id': order_id,
        'order_password': random_password
    }

    print(f"Updating password for order ID {order_id} with new password: {random_password}")
    
    if use_proxy:
        response = requests.post(f'https://{url}/api/user/order/updateAccountPasswordData', headers=headers, data=data, proxies=PROXIES)
    else:
        response = requests.post(f'https://{url}/api/user/order/updateAccountPasswordData', headers=headers, data=data)
    
    print(f"Password update response received: {response.json()}")
    return response.json(), random_password

# メイン処理
def main():
    # コマンドライン引数からPOST回数とプロキシの使用設定を取得
    if len(sys.argv) < 2:
        print("Usage: python script.py <number_of_posts> [use_proxy (on/off)]")
        sys.exit(1)

    num_posts = int(sys.argv[1])
    use_proxy = sys.argv[2].lower() == 'on' if len(sys.argv) > 2 else False

    websites = load_websites('websites.txt')

    for i in range(num_posts):
        print(f"\n--- Iteration {i+1}/{num_posts} ---")
        renew_tor_ip(use_proxy)  # Tor IPを更新
        time.sleep(10)  # TorがIPを更新するのを待つ

        for website in websites:
            cookies = get_cookies(website, use_proxy)
            random_number = generate_random_number()

            # 最初のAPIリクエスト
            response = post_to_api(website, cookies, random_number, use_proxy)

            if response['code'] == 200:
                print(f"Order created successfully: {response['message']}")
                print(f"Order ID: {response['data']['order_id']}")

                # 2番目のAPIリクエスト（ランダムパスワードを送信）
                update_response, random_password = update_account_password(website, cookies, response['data']['order_id'], use_proxy)

                if update_response['code'] == 200:
                    print(f"Password updated successfully with password: {random_password}")
                    time.sleep(120)  # とりあえず休んでおく

                else:
                    print(f"Failed to update password: {update_response['message']}")
            else:
                print(f"Failed to create order: {response['message']}")

if __name__ == '__main__':
    main()
