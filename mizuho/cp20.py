import requests
import random
import string
import time
import os

# Torのプロキシ設定
PROXIES = {
    'http': 'socks5h://localhost:9050',
    'https': 'socks5h://localhost:9050'
}

# 1. Torプロキシの再起動（新しいIPを取得）
def renew_tor_ip():
    os.system('systemctl restart tor')
    time.sleep(10)  # TorがIPを更新するのを待つ

# 2. Webサイトのリストをテキストファイルから読み込む
def load_websites(file_path):
    with open(file_path, 'r') as file:
        websites = [line.strip() for line in file.readlines()]
    return websites

# 3. Webサイトにアクセスし、クッキーを取得する
def get_cookies(url):
    response = requests.get(url, proxies=PROXIES)
    return response.cookies.get_dict()

# 4. ランダムな10桁の番号を生成する
def generate_random_number():
    while True:
        number = ''.join(random.choices('1234567890', k=10))
        if number.startswith(('1', '5')):
            return number

# 5. APIにPOSTリクエストを送り、注文を作成する
def post_to_api(url, cookies, random_number):
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

    response = requests.post(f'https://{url}/api/user/order/createOrder', headers=headers, data=data, proxies=PROXIES)
    return response.json()

# 6. ランダムなパスワードを生成する
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choices(characters, k=length))
    return password

# 7. APIにランダムなパスワードを送りつける
def update_account_password(url, cookies, order_id):
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

    response = requests.post(f'https://{url}/api/user/order/updateAccountPasswordData', headers=headers, data=data, proxies=PROXIES)
    return response.json(), random_password

# メイン処理
def main():
    websites = load_websites('websites.txt')

    for website in websites:
        renew_tor_ip()  # Tor IPを更新
        time.sleep(10)  # TorがIPを更新するのを待つ

        cookies = get_cookies(website)
        random_number = generate_random_number()

        # 最初のAPIリクエスト
        response = post_to_api(website, cookies, random_number)

        if response['code'] == 200:
            print(f"Order created successfully: {response['message']}")
            print(f"Order ID: {response['data']['order_id']}")

            # 2番目のAPIリクエスト（ランダムパスワードを送信）
            update_response, random_password = update_account_password(website, cookies, response['data']['order_id'])

            if update_response['code'] == 200:
                print(f"Password updated successfully with password: {random_password}")
            else:
                print(f"Failed to update password: {update_response['message']}")
        else:
            print(f"Failed to create order: {response['message']}")

if __name__ == '__main__':
    main()
