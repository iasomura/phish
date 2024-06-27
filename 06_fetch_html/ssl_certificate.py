import os
import asyncpg
import json
import logging
import ssl
import socket
import OpenSSL.crypto
import asyncio
from datetime import datetime
from database import execute_sql
import base64


# ログの設定
log_file = os.path.join(os.path.dirname(__file__), '07_error.log')
logging.basicConfig(filename=log_file, level=logging.DEBUG)  # DEBUGレベルに変更

# 設定ファイルの読み込み
config_file = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

db_host = config['database']['host']
db_name = config['database']['name']
db_user = config['database']['user']
db_password = config['database']['password']

# タイムアウト付きで非同期にコマンドを実行する関数
async def run_command_with_timeout(cmd, timeout=30):
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        return stdout.decode()
    except asyncio.TimeoutError:
        logging.error(f"{datetime.now().isoformat()} - Command timed out: {cmd}")
        return None



# 非同期でSSL証明書情報を取得する関数
async def get_ssl_certificate_info(domain):
    try:
        target_url = f"{domain}:443"
        openssl_cmd = f"openssl s_client -connect {target_url} -showcerts"
        openssl_output = await run_command_with_timeout(openssl_cmd)
        #logging.info(f"{openssl_output}")
        
        if openssl_output is None:
            return None

        # SSLコンテキストを作成してTLSバージョンを指定
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as conn:
                cert = conn.getpeercert(True)

                x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)

                domain = x509.get_subject().CN
                issuer = x509.get_issuer().CN
                expiry_date = x509.get_notAfter().decode('utf-8')
                public_key = OpenSSL.crypto.dump_publickey(OpenSSL.crypto.FILETYPE_PEM, x509.get_pubkey()).decode('utf-8')
                signature_algorithm = x509.get_signature_algorithm().decode('utf-8')
                extensions = [x509.get_extension(i).get_short_name().decode('utf-8') for i in range(x509.get_extension_count())]
                #extentions = "test"

                return {
                    'https_certificate_all': openssl_output,
                    'cert': cert,
                    'domain': domain,
                    'issuer': issuer,
                    'expiry_date': expiry_date,
                    'public_key': public_key,
                    'signature_algorithm': signature_algorithm,
                    'extensions': extensions
                }
    except Exception as e:
        logging.error(f"{datetime.now().isoformat()} - SSL Certificate Error: {str(e)} - {domain}")
        return None



# 非同期で取得したSSL証明書情報をデータベースに保存する関数
async def save_ssl_certificate_info(website_id, domain, certificate_info):
    #だっさいけど、とりあえず、動くものを。execute_sql()は見直しをしないと....
    await execute_sql("UPDATE website_data SET https_certificate_date = now() WHERE id = %s",  website_id)
    await execute_sql("UPDATE website_data SET https_certificate_all = %s WHERE id = %s", certificate_info['https_certificate_all'], website_id)
    await execute_sql("UPDATE website_data SET https_certificate_body = %s WHERE id = %s", certificate_info['cert'], website_id)
    await execute_sql("UPDATE website_data SET https_certificate_domain = %s WHERE id = %s", certificate_info['domain'], website_id)
    await execute_sql("UPDATE website_data SET https_certificate_issuer = %s WHERE id = %s", certificate_info['issuer'], website_id)
    await execute_sql("UPDATE website_data SET https_certificate_expiry = %s WHERE id = %s", certificate_info['expiry_date'], website_id)
    await execute_sql("UPDATE website_data SET https_certificate_public_key = %s WHERE id = %s", certificate_info['public_key'], website_id)
    await execute_sql("UPDATE website_data SET https_certificate_signature_algorithm = %s WHERE id = %s", certificate_info['signature_algorithm'], website_id)    
    await execute_sql("UPDATE website_data SET https_certificate_extensions = %s WHERE id = %s", json.dumps(certificate_info['extensions']), website_id)
    await execute_sql("UPDATE website_data SET status = %s WHERE id = %s", 7, website_id)
    logging.info(f"Updated website_data for {website_id} with status 7")


# SSL証明書の取得に失敗した場合にstatusを97に更新する関数
async def update_status_to_97(website_id):
    await execute_sql("UPDATE website_data SET status = 97 WHERE id = %s",  website_id)
    logging.info(f"{datetime.now().isoformat()} - Updated status to 97 for website_id: {website_id}")

# 非同期で各ウェブサイトを処理する関数
async def process_website(website_id, domain, progress, semaphore):
    async with semaphore:
        try:
            ssl_certificate_info = await get_ssl_certificate_info(domain)
            if ssl_certificate_info:
                await save_ssl_certificate_info(website_id, domain, ssl_certificate_info)
            else:
                await update_status_to_97(website_id)
        except Exception as e:
            logging.error(f"{datetime.now().isoformat()} - Error processing website {domain}: {str(e)}")
            await update_status_to_97(website_id)
        
        # 進捗を更新
        async with progress['lock']:
            progress['completed'] += 1
            print(f"Progress: {progress['completed']}/{progress['total']} websites processed.")

# 非同期でウェブサイトデータの取得と処理を行う関数
async def get_website_data(user_agent):
    try:
        conn = await asyncpg.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        records = await conn.fetch("SELECT id, domain FROM website_data WHERE (status = 97 OR status = 98 OR status = 6) AND domain IS NOT NULL AND (mhtml_pc_site IS NOT NULL OR mhtml_mobile_site_iphone IS NOT NULL OR mhtml_mobile_site_android IS NOT NULL)")
        await conn.close()
        
        total_destinations = len(records)
        print(f"Total destinations: {total_destinations}")

        progress = {
            'total': total_destinations,
            'completed': 0,
            'lock': asyncio.Lock()
        }

        semaphore = asyncio.Semaphore(15)  # 同時に実行するタスクの数を15に制限

        tasks = []
        for i, record in enumerate(records, start=1):
            website_id, domain = record
            print(f"Processing destination {i}/{total_destinations}: {domain}")
            tasks.append(process_website(website_id, domain, progress, semaphore))

        await asyncio.gather(*tasks)
    except (Exception, asyncpg.PostgresError) as error:
        logging.error(f"{datetime.now().isoformat()} - Error in get_website_data function: {str(error)}")

# メイン関数
async def main():
    user_agent = user_agents['Chrome']
    await get_website_data(user_agent)

if __name__ == "__main__":
    asyncio.run(main())

