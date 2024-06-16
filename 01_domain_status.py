import psycopg2
import subprocess

# データベース接続情報
db_host = 'localhost'
db_name = 'website_data'
db_user = 'postgres'
db_password = 'asomura'

try:
    # データベースへの接続
    conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host)
    cur = conn.cursor()

    # ドメイン情報を取得
    cur.execute("SELECT id, domain FROM website_data WHERE domain_status IS NULL AND status = 0")
    domains = cur.fetchall()

    total_domains = len(domains)
    domains_processed = 0

    for domain_data in domains:
        domain_id, domain = domain_data
        try:
            # digコマンドの実行
            result = subprocess.run(['dig', domain, 'AAA'], capture_output=True, text=True)
            dig_output = result.stdout.strip()

            # NXDOMAINまたはNOERRORのみの場合のみ記録
            if 'NXDOMAIN' in dig_output:
                domain_status = 'NXDOMAIN'

            elif 'NOERROR' in dig_output:
                domain_status = 'NOERROR'

            else:
                domain_status = 'ERROR'  # NXDOMAINまたはNOERROR以外の場合はNoneとする


            # データベースの更新
            if domain_status in ['NXDOMAIN', 'NOERROR']:
                cur.execute("UPDATE website_data SET domain_status = %s, last_update = now(), status = 1 WHERE id = %s", (domain_status, domain_id))
                conn.commit()
                domains_processed += 1
                print(f"Updated domain {domain} with status {domain_status} - {domains_processed}/{total_domains} domains processed")
            elif domain_status == 'ERROR':
                cur.execute("UPDATE website_data SET domain_status = %s, last_update = now(), status = 99 WHERE id = %s", (domain_status, domain_id))
                conn.commit()
                domains_processed += 1
                print(f"Updated domain {domain} with status {domain_status} - {domains_processed}/{total_domains} domains processed")

                print(f"No valid status found for domain {domain}")
        except Exception as e:
            print(f"Error processing domain {domain}: {e}")

except Exception as e:
    print(f"Database connection error: {e}")

finally:
    # データベース接続を閉じる
    if conn:
        cur.close()
        conn.close()
