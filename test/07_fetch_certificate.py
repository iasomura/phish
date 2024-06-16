import os
import psycopg2
import requests
from requests.exceptions import RequestException
import json
from datetime import datetime
import time
import logging
import ssl
import OpenSSL.crypto
import subprocess


# ログの設定
log_file = os.path.join(os.path.dirname(__file__), 'error.log')
logging.basicConfig(filename=log_file, level=logging.ERROR)

# 設定ファイルの読み込み
config_file = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

db_host = config['database']['host']
db_name = config['database']['name']
db_user = config['database']['user']
db_password = config['database']['password']

# ユーザーエージェントの設定
user_agents = {
    'Chrome': config['Chrome'],
    'Android': config['Android'],
    'iPhone': config['iPhone']
}

# リダイレクトの最大追跡回数
MAX_REDIRECTS = 10

# ウェブサイトデータの取得関数
def get_website_data(user_agent):
    try:
        conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        cur = conn.cursor()

        cur.execute("SELECT id, domain,url, url_pc_site, url_mobile_site FROM website_data WHERE status = 5 AND (url IS NOT NULL OR url_pc_site IS NOT NULL OR (domain IS NOT NULL AND ip_address IS NOT NULL))")
        destinations = cur.fetchall()

        for destination in destinations:
            website_id, domain, url, url_pc_site, url_mobile_site = destination

            # URLの選定ロジック (Chrome)
            if url is not None:
                target_url = url
            elif url_pc_site is not None:
                target_url = url_pc_site
            else:
                target_url = f"https://{domain}"
                
            # URLの選定ロジック (Android または iPhone)
            if url_mobile_site is not None:
                mobile_target_url = url_mobile_site
            elif url is not None:
                mobile_target_url = url
            else:
               mobile_target_url = f"http://{domain}"

            # ウェブサイトにアクセス
            # url_mobile_siteのデータがNullの場合はurlを使う
            if url_mobile_site is None:
                html_content, redirect_url = fetch_website(target_url, user_agent)

            # url_mobile_siteのデータがNullでなかった場合はurl_mobileを使う
            if url_mobile_site is not None:
                mobile_html_content, mobile_redirect_url = fetch_website(mobile_target_url, user_agent)

            # 取得したSSL証明書情報の保存
            ssl_certificate_info = get_ssl_certificate_info(domain)


            print(get_ssl_certificate_info(domain))
            if ssl_certificate_info:
                save_ssl_certificate_info(website_id, domain, ssl_certificate_info)

            print(domain)
            #print(html_content)
            # データベースの更新
            if html_content is not None and redirect_url is not None and mobile_html_content is not None and mobile_redirect_url is not None:
                cur.execute("UPDATE website_data SET html_pc_site = %s, url_pc_redirect = %s, html_mobile_site_iphone = %s, url_mobile_redirect_iphone = %s, html_mobile_site_android = %s, url_mobile_redirect_android = %s, status = 6, last_update = NOW() WHERE id = %s", (html_content, redirect_url, mobile_html_content, mobile_redirect_url, mobile_html_content, mobile_redirect_url, id))
                conn.commit()
                
        cur.close()
        conn.close()

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"{datetime.now().isoformat()} - Error in get_website_data function: {str(error)}")

# SSL証明書情報を取得する関数
def get_ssl_certificate_info(target_url):
    try:
        # OpenSSL コマンドを実行して SSL 証明書情報を取得
        openssl_cmd = f"openssl s_client -connect {target_url}:443 -showcerts"
        print(openssl_cmd)
        openssl_output = subprocess.check_output(openssl_cmd, shell=True, text=True, timeout=3, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE)
        #print(openssl_output)
        
        cert = ssl.get_server_certificate((target_url, 443))
        #print(cert)
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        #print(x509)

        domain = x509.get_subject().CN
        #print(domain)u
        issuer = x509.get_issuer().CN
        #print(issuer)
        expiry_date = x509.get_notAfter().decode('utf-8')
        #print(expiry_date)
        public_key = OpenSSL.crypto.dump_publickey(OpenSSL.crypto.FILETYPE_PEM, x509.get_pubkey()).decode('utf-8')
        #print(public_key)
        signature_algorithm = x509.get_signature_algorithm().decode('utf-8')
        #print(signature_algorithm)
        #extensions = [ext.get_short_name().decode('utf-8') for ext in x509.get_extensions()]
        extensions = [x509.get_extension(i).get_short_name().decode('utf-8') for i in range(x509.get_extension_count())]


        #print(extensions)

        return {
            'https_certficate_all':openssl_output,
            'cert': cert,  # 'cert' キーを追加
            'domain': domain,
            'issuer': issuer,
            'expiry_date': expiry_date,
            'public_key': public_key,
            'signature_algorithm': signature_algorithm,
            'extensions': extensions
        }
    except Exception as e:
        logging.error(f"{datetime.now().isoformat()} - SSL Certificate Error: {str(e)} - {target_url}")
        return None

# 取得したSSL証明書情報をデータベースに保存する関数
import psycopg2
import json

# データベースへの接続を確立
def connect_to_database():
    return psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)

# 取得したSSL証明書情報をデータベースに保存する関数
def save_ssl_certificate_info(website_id, domain, certificate_info):
    conn = None
    try:
        conn = connect_to_database()
        cur = conn.cursor()

        # SQLクエリを実行
        cur.execute("""
            UPDATE website_data SET 
            https_certificate_date = NOW(), 
            https_certificate_all = %s, 
            https_certificate_body = %s, 
            https_certificate_domain = %s, 
            https_certificate_issuer = %s, 
            https_certificate_expiry = %s, 
            https_certificate_public_key = %s, 
            https_certificate_signature_algorithm = %s, 
            https_certificate_extensions = %s 
            WHERE id = %s
        """, (
            certificate_info['https_certificate_all'],
            certificate_info['cert'],
            certificate_info['domain'],
            certificate_info['issuer'],
            certificate_info['expiry_date'],
            certificate_info['public_key'],
            certificate_info['signature_algorithm'],
            json.dumps(certificate_info['extensions']),
            website_id
        ))

        # SQL文を表示
        print("SQL Query:", sql_query)

        
        conn.commit()
    except psycopg2.DatabaseError as e:
        # エラーが発生した場合はロールバック
        if conn:
            conn.rollback()
        print(f"Database Error: {e}")
        logging.error(f"{datetime.now().isoformat()} - Database Error: {str(e)}")
    finally:
        # 接続をクローズ
        if conn:
            conn.close()



def save_ssl_certificate_info_temp(website_id, domain, certificate_info):
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
    cur = conn.cursor()

    #print(certificate_info)
    cur.execute("UPDATE website_data SET https_certificate_date = NOW(), https_certificate_all = %s, https_certificate_body = %s, https_certificate_domain = %s, https_certificate_issuer = %s, https_certificate_expiry = %s, https_certificate_public_key = %s, https_certificate_signature_algorithm = %s, https_certificate_extensions = %s WHERE id = %s", (
        certificate_info['https_certificate_all'],
        certificate_info['cert'],
        certificate_info['domain'],
        certificate_info['issuer'],
        certificate_info['expiry_date'],
        certificate_info['public_key'],
        certificate_info['signature_algorithm'],
        json.dumps(certificate_info['extensions']),
        website_id
    ))

    conn.commit()
    cur.close()
    conn.close()

# ウェブサイトにアクセスし、HTMLコンテンツを取得する関数（リダイレクトも処理する）
def fetch_website(url, user_agent):
    headers = {'User-Agent': user_agent}
    redirect_url = None
    html_content = None
    redirects = 0
    response = None

    try:
        while redirects <= MAX_REDIRECTS:
            try:
                response = requests.get(url, headers=headers, allow_redirects=False)
            except RequestException as e:
                logging.error(f"{datetime.now().isoformat()} - HTTP Error: {str(e)}")
                handle_http_error(e.response.status_code, url, user_agent)
                return None, None
            
            response.raise_for_status()

            if response.status_code == 200:
                html_content = response.text
                break
            elif response.status_code in (301, 302, 307, 308):
                redirect_url = response.headers.get('Location')
                url = redirect_url
                redirects += 1
            else:
                break

            if redirects > MAX_REDIRECTS:
                logging.error(f"{datetime.now().isoformat()} - Max redirects exceeded for {url}")
                break

    except RequestException as e:
        logging.error(f"{datetime.now().isoformat()} - HTTP Error: {str(e)}")
        handle_http_error(response.status_code, url, user_agent)
        return None, None

    except Exception as e:
        logging.error(f"{datetime.now().isoformat()} - System Error: {str(e)}")
        return None, None

    return html_content, redirect_url

# HTTPエラーのハンドリングを行う関数
def handle_http_error(status_code, url, user_agent):
    if status_code == 404:
        pass
    elif status_code == 104:
        pass
    elif status_code == 500:
        retries = 3
        while retries > 0:
            time.sleep(5)
            html_content, redirect_url = fetch_website(url, user_agent)
            if html_content is not None:
                break
            retries -= 1
    elif status_code == 503:
        retries = 2
        while retries > 0:
            time.sleep(10)
            html_content, redirect_url = fetch_website(url, user_agent)
            if html_content is not None:
                break
            retries -= 1

# メイン処理
for user_agent_name, user_agent_value in user_agents.items():
    get_website_data(user_agent_value)
