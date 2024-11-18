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
#logging.basicConfig(filename=log_file, level=logging.DEBUG)  # DEBUGレベルに変更

# 設定ファイルの読み込み
config_file = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

db_host = config['database']['host']
db_name = config['database']['name']
db_user = config['database']['user']
db_password = config['database']['password']


async def get_ssl_certificate_info(domain, max_retries=3):
    for attempt in range(max_retries):
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as conn:
                    https_certificate_all = ""
                    
                    # SSL/TLS handshake information
                    https_certificate_all += f"Connected to {domain}:{conn.getpeername()[1]}\n"
                    https_certificate_all += f"Protocol: {conn.version()}\n"
                    https_certificate_all += f"Cipher: {conn.cipher()[0]}\n\n"
                    
                    # Certificate chain
                    cert = conn.getpeercert(True)
                    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)
                    
                    https_certificate_all += "Certificate chain:\n"
                    cert_chain = conn.getpeercert()
                    for i, cert_dict in enumerate(cert_chain.get('subject', []) + cert_chain.get('issuer', [])):
                        cert_info = ', '.join([f"{k}={v}" for k, v in cert_dict])
                        https_certificate_all += f" {i} s:{cert_info}\n"
                    
                    https_certificate_all += "\nServer certificate:\n"
                    https_certificate_all += ssl.DER_cert_to_PEM_cert(cert)
                    
                    subject = x509.get_subject()
                    issuer = x509.get_issuer()
                    expiry_date = x509.get_notAfter().decode('utf-8')
                    public_key = OpenSSL.crypto.dump_publickey(OpenSSL.crypto.FILETYPE_PEM, x509.get_pubkey()).decode('utf-8')
                    signature_algorithm = x509.get_signature_algorithm().decode('utf-8')
                    extensions = [x509.get_extension(i) for i in range(x509.get_extension_count())]
                    
                    https_certificate_all += f"subject={', '.join([f'{k.decode()}={v.decode()}' for k, v in subject.get_components()])}\n"
                    https_certificate_all += f"issuer={', '.join([f'{k.decode()}={v.decode()}' for k, v in issuer.get_components()])}\n"
                    https_certificate_all += f"---\nNo client certificate CA names sent\n"
                    https_certificate_all += f"---\nSSL handshake has read {conn.context.verify_mode} bytes and written {conn.context.verify_mode} bytes\n"
                    https_certificate_all += f"---\nNew, {conn.version()}, Cipher is {conn.cipher()[0]}\n"
                    https_certificate_all += f"Server public key is {x509.get_pubkey().bits()} bit\n"
                    https_certificate_all += f"Secure Renegotiation IS NOT supported\n"
                    https_certificate_all += f"Compression: NONE\n"
                    https_certificate_all += f"Expansion: NONE\n"
                    https_certificate_all += f"No ALPN negotiated\n"
                    https_certificate_all += f"Early data was not sent\n"
                    https_certificate_all += f"Verify return code: {conn.context.verify_mode}\n"
                    https_certificate_all += f"---\n"
                    
                    logging.info(f"Certificate info retrieved for {domain}")
                    return {
                        'https_certificate_all': https_certificate_all,
                        'cert': cert,
                        'domain': subject.CN,
                        'issuer': issuer.CN,
                        'expiry_date': expiry_date,
                        'public_key': public_key,
                        'signature_algorithm': signature_algorithm,
                        'extensions': [ext.get_short_name().decode('utf-8') for ext in extensions]
                    }
        except Exception as e:
            logging.error(f"{datetime.now().isoformat()} - SSL Certificate Error: {str(e)} - {domain}")
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(2 ** attempt)  # 指数バックオフ


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

