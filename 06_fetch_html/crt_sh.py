import aiohttp
import psycopg2
import psycopg2.extras
import asyncio
import logging
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

# データベース設定
DATABASE_CONFIG = {
    'dbname': DB_NAME,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'host': DB_HOST
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def fetch_certificate_data(domain):
    url = f"https://crt.sh/?q={domain}&output=json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                logging.error(f"Failed to fetch data for domain {domain}: HTTP {response.status}")
                return None

async def save_certificate_data(conn, certificate_data, domain, ip_address):
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO certificate_data (
        id, issuer_ca_id, issuer_name, common_name, name_value, entry_timestamp, 
        not_before, not_after, serial_number, result_count, domain_name, ip_address,
        country, organization, cn
    ) VALUES (
        %(id)s, %(issuer_ca_id)s, %(issuer_name)s, %(common_name)s, %(name_value)s, %(entry_timestamp)s,
        %(not_before)s, %(not_after)s, %(serial_number)s, %(result_count)s, %(domain_name)s, %(ip_address)s,
        %(country)s, %(organization)s, %(cn)s
    ) ON CONFLICT (id) DO NOTHING;
    """
    for record in certificate_data:
        issuer_name_parts = record['issuer_name'].split(', ')
        country = organization = cn = None
        for part in issuer_name_parts:
            if part.startswith('C='):
                country = part[2:]
            elif part.startswith('O='):
                organization = part[2:]
            elif part.startswith('CN='):
                cn = part[3:]

        record.update({
            'domain_name': domain,
            'ip_address': ip_address,
            'country': country,
            'organization': organization,
            'cn': cn
        })
        
        cursor.execute(insert_query, record)
    conn.commit()

async def update_website_status(conn, domain, status):
    cursor = conn.cursor()
    update_query = """
    UPDATE website_data SET status = %s WHERE domain = %s
    """
    cursor.execute(update_query, (status, domain))
    conn.commit()

async def process_domains():
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    select_query = """
    SELECT domain, ip_address FROM website_data 
    WHERE domain IS NOT NULL 
    AND mhtml_mobile_site_iphone IS NOT NULL 
    AND https_certificate_issuer IS NOT NULL 
    AND status IN (7, 98);
    """
    cursor.execute(select_query)
    domains = cursor.fetchall()

    for row in domains:
        domain = row['domain']
        ip_address = row['ip_address']
        await handle_domain(conn, domain, ip_address)
        await asyncio.sleep(200)  # 15秒の待機

    conn.close()

async def handle_domain(conn, domain, ip_address):
    certificate_data = await fetch_certificate_data(domain)
    if certificate_data:
        await save_certificate_data(conn, certificate_data, domain, ip_address)
    else:
        await update_website_status(conn, domain, 100)
        logging.error(f"Failed to retrieve certificate data for domain {domain}, status updated to 100")

if __name__ == '__main__':
    asyncio.run(process_domains())

