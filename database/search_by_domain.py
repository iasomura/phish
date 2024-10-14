import psycopg2

# データベース接続の設定
conn = psycopg2.connect(
    dbname="website_data",
    user="postgres",
    password="asomura",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# 検索するdomainを指定
search_domain = "waseda.jp"

# SQLクエリを実行
query = """
    SELECT id, status, last_update, phish_from, url, phish_id, phish_detail_url, phish_ip_address,
           cidr_block, verified, online_status, target, domain_db_inserted_at, domain_id, domain,
           domain_status, domain_registrar, whois_date, whois_domain, registrant_name, admin_name,
           tech_name, dig_info_a, dig_info_mx, dig_info_ns, dig_info_ttl_a, dig_info_ttl_ns,
           dig_info_ttl_mx, ip_address, ip_info, ip_retrieval_date, ip_organization, ip_location,
           hosting_provider, whois_ip, url_date, url_pc_site, url_pc_redirect, url_mobile_site,
           html_pc_site, screenshot_iphone, screenshot_android, screenshot_chrome, https_certificate_date,
           https_certificate_body, https_certificate_domain, https_certificate_issuer, https_certificate_expiry,
           https_certificate_public_key, https_certificate_signature_algorithm, https_certificate_extensions,
           phishing_flag, phishing_flag_date, phishing_confirm_flag, phishing_confirm_flag_date, actor,
           html_mobile_site_iphone, html_mobile_site_android, html_pc_redirect, html_mobile_redirect_iphone,
           html_mobile_redirect_android, screenshot_availability, url_mobile_redirect_iphone, url_mobile_redirect_android,
           https_certficate_all, https_certificate_all
    FROM website_data
    WHERE domain = %s;
"""
cursor.execute(query, (search_domain,))
result = cursor.fetchone()

# 結果がある場合に指定されたフォーマットで出力
if result:
    columns = [
        "id", "status", "last_update", "phish_from", "url", "phish_id", "phish_detail_url", "phish_ip_address",
        "cidr_block", "verified", "online_status", "target", "domain_db_inserted_at", "domain_id", "domain",
        "domain_status", "domain_registrar", "whois_date", "whois_domain", "registrant_name", "admin_name",
        "tech_name", "dig_info_a", "dig_info_mx", "dig_info_ns", "dig_info_ttl_a", "dig_info_ttl_ns",
        "dig_info_ttl_mx", "ip_address", "ip_info", "ip_retrieval_date", "ip_organization", "ip_location",
        "hosting_provider", "whois_ip", "url_date", "url_pc_site", "url_pc_redirect", "url_mobile_site",
        "html_pc_site", "screenshot_iphone", "screenshot_android", "screenshot_chrome", "https_certificate_date",
        "https_certificate_body", "https_certificate_domain", "https_certificate_issuer", "https_certificate_expiry",
        "https_certificate_public_key", "https_certificate_signature_algorithm", "https_certificate_extensions",
        "phishing_flag", "phishing_flag_date", "phishing_confirm_flag", "phishing_confirm_flag_date", "actor",
        "html_mobile_site_iphone", "html_mobile_site_android", "html_pc_redirect", "html_mobile_redirect_iphone",
        "html_mobile_redirect_android", "screenshot_availability", "url_mobile_redirect_iphone", "url_mobile_redirect_android",
        "https_certficate_all", "https_certificate_all"
    ]
    
    for col, data in zip(columns, result):
        print(f"{col}：{data}")
else:
    print(f"ドメイン {search_domain} のデータは見つかりませんでした。")

# 接続を閉じる
cursor.close()
conn.close()
