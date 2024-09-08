import psycopg2
import subprocess
import shlex
import tldextract
import signal
import config

"""
このプログラムは、データベース内の特定のドメインに対してWHOIS情報を取得し、その結果をデータベースに更新するものです。
whoisの応答結果は不定形なデータとなるため、次のデータベースカラムについては、データが入らない可能性があります。
whoisdomain_registrar | registrant_name | admin_name | tech_name 
"""

# タイムアウト処理のための関数
def timeout_handler(signum, frame):
    raise TimeoutError("whois command timed out")

# データベース接続情報をロード
db_config = config.load_db_config()

# サブドメインを削除する関数
def remove_subdomain(domain):
    ext = tldextract.extract(domain)
    subdomain = ext.subdomain
    domain = ext.registered_domain
    if subdomain:
        return domain
    else:
        return domain

try:
    # データベース接続
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    # NOERRORのドメインを抽出
    cur.execute("SELECT id, domain FROM website_data WHERE domain_status = 'NOERROR' AND whois_domain IS NULL AND status = 1")
    rows = cur.fetchall()
    total_domains = len(rows)
    domains_processed = 0

    # whoisの結果を更新
    for row in rows:
        id, domain = row
        try:
            domains_processed += 1
            # サブドメインを削除
            domain = remove_subdomain(domain)
            
            # 進捗を表示
            print(f"Processing domain {domain} ({domains_processed}/{total_domains})")

            # タイムアウトの設定（例：30秒）
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)

            try:
                # whoisコマンドを実行
                cmd = f"whois {domain}"
                result = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30)
                
                # タイムアウトのキャンセル
                signal.alarm(0)

                # whoisの結果から必要な情報を抽出
                whois_info = result.stdout
                domain_registrar = ""
                registrant_name = ""
                admin_name = ""
                tech_name = ""
                
                for line in whois_info.split("\n"):
                    if "Registrar:" in line:
                        domain_registrar = line.split(":")[1].strip()
                    elif "Registrant Name:" in line:
                        registrant_name = line.split(":")[1].strip()
                    elif "Admin Name:" in line:
                        admin_name = line.split(":")[1].strip()
                    elif "Tech Name:" in line:
                        tech_name = line.split(":")[1].strip()
                
                # データベースの更新
                cur.execute("""
                    UPDATE website_data
                    SET last_update = now(),
                        status = 2,
                        whois_date = now(),
                        whois_domain = %s,
                        domain_registrar = %s,
                        registrant_name = %s,
                        admin_name = %s,
                        tech_name = %s
                    WHERE id = %s
                """, (whois_info, domain_registrar, registrant_name, admin_name, tech_name, id))
                conn.commit()
            except (subprocess.TimeoutExpired, TimeoutError):
                # タイムアウト時の処理
                print(f"Timeout occurred for domain {domain}")
                cur.execute("""
                    UPDATE website_data
                    SET last_update = now(),
                        status = 98,
                        whois_domain = 'TIMEOUT'
                    WHERE id = %s
                """, (id,))
                conn.commit()
        except Exception as e:
            # その他のエラー時の処理
            cur.execute("""
                UPDATE website_data
                SET last_update = now(),
                    status = 99
                WHERE id = %s
            """, (id,))
            conn.commit()
            print(f"Error processing domain {domain}: {e}")
        finally:
            # タイムアウトのリセット
            signal.alarm(0)

    # 処理完了を表示
    print("All domains processed.")

    # データベースの更新を確認
    print("\nVerifying database updates:")
    cur.execute("SELECT id, domain, whois_domain, domain_registrar, registrant_name, admin_name, tech_name FROM website_data WHERE status = 2 LIMIT 5")
    verified_rows = cur.fetchall()

    if verified_rows:
        for row in verified_rows:
            print(f"\nID: {row[0]}")
            print(f"Domain: {row[1]}")
            print(f"WHOIS Domain: {'Updated' if row[2] else 'Not Updated'}")
            print(f"Domain Registrar: {row[3] or 'Not Available'}")
            print(f"Registrant Name: {row[4] or 'Not Available'}")
            print(f"Admin Name: {row[5] or 'Not Available'}")
            print(f"Tech Name: {row[6] or 'Not Available'}")
    else:
        print("No updated records found.")

    # タイムアウトしたドメインの数を確認
    cur.execute("SELECT COUNT(*) FROM website_data WHERE status = 98")
    timeout_count = cur.fetchone()[0]
    print(f"\nNumber of domains that timed out: {timeout_count}")

    # エラーが発生したドメインの数を確認
    cur.execute("SELECT COUNT(*) FROM website_data WHERE status = 99")
    error_count = cur.fetchone()[0]
    print(f"Number of domains with errors: {error_count}")


except Exception as e:
    print(f"Database connection error: {e}")

finally:
    # データベース接続を閉じる
    if cur:
        cur.close()
