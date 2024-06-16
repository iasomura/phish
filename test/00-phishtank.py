import xml.etree.ElementTree as ET
import gzip
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
import hashlib

# データベース接続情報
db_host = 'localhost'
db_name = 'website_data'
db_user = 'postgres'
db_password = 'asomura'

# gzip形式のXMLファイルのパス
gzip_xml_file = 'online-valid.xml.gz'

# XMLをパースしてデータベースに挿入する関数
def insert_xml_data(gzip_xml_file):
    # gzip形式のXMLファイルをオープンして展開
    with gzip.open(gzip_xml_file, 'rt') as f:
        # XMLをパース
        tree = ET.parse(f)
        root = tree.getroot()

        # データベースに接続
        conn = psycopg2.connect(host=db_host, dbname=db_name, user=db_user, password=db_password)
        cursor = conn.cursor()

        # エントリーごとに処理
        for entry in root.findall('./entries/entry'):
            # 指定された要素を抽出
            phish_from = "PhishTank"  # 固定値
            original_url = entry.find('url').text
            url = normalize_url(original_url)
            phish_id = int(entry.find('phish_id').text)
            phish_detail_url = entry.find('phish_detail_url').text
            phish_ip_address_element = entry.find('details/detail/ip_address')
            phish_ip_address = phish_ip_address_element.text if phish_ip_address_element is not None else None
            cidr_block_element = entry.find('details/detail/cidr_block')
            cidr_block = cidr_block_element.text if cidr_block_element is not None else None
            verified = entry.find('verification/verified').text.lower() == 'yes'
            online_status = entry.find('status/online').text.lower() == 'yes'
            target = entry.find('target').text

            # URLからドメインを抽出
            domain = extract_domain_from_url(url)

            # データベースに挿入
            sql = """INSERT INTO website_data (status,last_update,phish_from, url, phish_id, phish_detail_url, phish_ip_address, cidr_block, verified, online_status, target, domain)
                     VALUES (0,now(),%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                     ON CONFLICT (domain) DO NOTHING"""

            #values = (phish_from, url, phish_id, phish_detail_url, phish_ip_address, cidr_block, verified, online_status, target, domain)
            values = (
                sanitize(phish_from),
                sanitize(url),
                sanitize(phish_id),
                sanitize(phish_detail_url),
                sanitize(phish_ip_address),
                sanitize(cidr_block),
                sanitize(verified),
                sanitize(online_status),
                sanitize(target),
                sanitize(domain)
            )
            
            cursor.execute(sql, values)
        
        # データベースにコミット
        conn.commit()

        # データベース接続をクローズ
        cursor.close()
        conn.close()


#サニタイズ
def sanitize(value):
    # 文字列がNoneの場合はそのまま返す
    if value is None:
        return None
    
    # 文字列の場合はサニタイズして返す
    if isinstance(value, str):
        return value
    
    # psycopg2.sql.Literal() を文字列に変換して返す
    if isinstance(value, sql.Literal):
        return str(value)
    
    # それ以外の場合はそのまま返す
    return value


# URLを正規化する関数
def normalize_url(url):
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme.lower()
    netloc = parsed_url.netloc.lower()
    path = parsed_url.path
    params = parsed_url.params
    query = parsed_url.query
    fragment = parsed_url.fragment
    normalized_url = f"{scheme}://{netloc}{path}"
    if params:
        normalized_url += f";{params}"
    if query:
        normalized_url += f"?{query}"
    if fragment:
        normalized_url += f"#{fragment}"
    return normalized_url

# URLからドメインを抽出する関数
def extract_domain_from_url(url):
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc.lower()
    # wwwを削除
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc

# メイン関数
if __name__ == "__main__":
    insert_xml_data(gzip_xml_file)
