"""
このプログラムは、PhishTankから提供されたgzip形式のXMLファイルをパースし、フィッシング情報をPostgreSQLデータベースに挿入します。

主な機能:
1. XMLファイルを展開して解析
2. URLを正規化し、無効なURLはスキップ
3. データベースに接続し、フィッシング情報（URL、IPアドレス、ターゲットなど）を挿入
4. データが重複しないように、ドメイン名に基づいて一意性を保証
5. サニタイズ処理を行い、安全にデータベースへ格納

使い方:
- gzip_xml_file 変数に対象のgzip形式のXMLファイルのパスを指定
- データベース接続情報（db_host, db_name, db_user, db_password）を適切に設定

"""

import xml.etree.ElementTree as ET
import gzip
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
import ipaddress
import logging

# データベース接続情報
db_host = 'localhost'
db_name = 'website_data'
db_user = 'postgres'
db_password = 'asomura'

# gzip形式のXMLファイルのパス
gzip_xml_file = 'online-valid.xml.gz'

# ログ設定
logging.basicConfig(level=logging.INFO)

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
            # 固定値や要素を抽出
            phish_from = "PhishTank"
            original_url = entry.find('url').text
            url = normalize_url(original_url)

            # URLが無効な場合はスキップ
            if url is None:
                logging.warning(f"Skipping invalid URL: {original_url}")
                continue

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
            sql = """INSERT INTO website_data (status, last_update, phish_from, url, phish_id, phish_detail_url, phish_ip_address, cidr_block, verified, online_status, target, domain)
                     VALUES (0, now(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                     ON CONFLICT (domain) DO NOTHING"""

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


# サニタイズ関数
def sanitize(value):
    """
    入力値を安全にデータベースに挿入できる形にサニタイズする関数。
    - Noneの場合はそのまま返す。
    - psycopg2.sql.Literalは文字列に変換する。
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, sql.Literal):
        return str(value)
    return value


# URLを正規化する関数
def normalize_url(url):
    """
    URLを正規化する関数。
    - URLスキームやネットロケーションを小文字に変換。
    - URLが無効な場合はNoneを返す。
    """
    try:
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme.lower()
        netloc = parsed_url.netloc.lower()

        # IPアドレスまたはホスト名の検証
        if not is_valid_hostname(netloc):
            logging.error(f"Invalid hostname: {netloc}")
            return None

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
    except Exception as e:
        logging.error(f"Error normalizing URL {url}: {e}")
        return None

# ホスト名が正しいかを検証する関数
def is_valid_hostname(hostname):
    """
    ホスト名が有効なIPアドレスまたはドメイン名かを確認する関数。
    """
    try:
        # IP アドレスとして解釈できるかをチェック
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        # IPアドレスでない場合、ドメイン名としての妥当性をチェック（簡易版）
        if hostname and isinstance(hostname, str) and "." in hostname:
            return True
        return False


# URLからドメインを抽出する関数
def extract_domain_from_url(url):
    """
    URLからドメイン名を抽出する関数。
    - www. がついている場合は取り除く。
    """
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


# メイン関数
if __name__ == "__main__":
    insert_xml_data(gzip_xml_file)
