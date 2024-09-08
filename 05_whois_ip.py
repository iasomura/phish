import psycopg2
import subprocess
import shlex
import signal
import config

# タイムアウト処理のための関数
def timeout_handler(signum, frame):
    raise TimeoutError("whois command timed out")

# データベース接続情報をロード
db_config = config.load_db_config()

try:
    # データベース接続
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    # IPアドレスのうち、whois情報が未登録のものを抽出
    cur.execute("SELECT id, ip_address FROM website_data WHERE domain_status = 'NOERROR' AND whois_ip IS NULL AND status = 4")
    rows = cur.fetchall()
    total_ips = len(rows)
    ips_processed = 0

    # whoisの結果を更新
    for row in rows:
        id, ip_address = row
        try:
            ips_processed += 1
            
            # 進捗を表示
            print(f"Processing IP {ip_address} ({ips_processed}/{total_ips})")

            # タイムアウトの設定（例：30秒）
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)

            try:
                # whoisコマンドを実行
                cmd = f"whois {ip_address}"
                result = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30)
                
                # タイムアウトのキャンセル
                signal.alarm(0)

                # whoisの結果を取得
                whois_info = result.stdout
                
                # データベースの更新
                cur.execute("""
                    UPDATE website_data
                    SET last_update = now(),
                        status = 5,  -- ステータスを5に変更
                        whois_date = now(),
                        whois_ip = %s
                    WHERE id = %s
                """, (whois_info, id))
                conn.commit()

            except (subprocess.TimeoutExpired, TimeoutError):
                # タイムアウト時の処理
                print(f"Timeout occurred for IP {ip_address}")
                cur.execute("""
                    UPDATE website_data
                    SET last_update = now(),
                        status = 98,
                        whois_ip = 'TIMEOUT'
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
            print(f"Error processing IP {ip_address}: {e}")
        finally:
            # タイムアウトのリセット
            signal.alarm(0)

    # 処理完了を表示
    print("All IPs processed.")

    # データベースの更新を確認
    print("\nVerifying database updates:")
    cur.execute("SELECT id, ip_address, whois_ip FROM website_data WHERE status = 5 LIMIT 5")
    verified_rows = cur.fetchall()

    if verified_rows:
        for row in verified_rows:
            print(f"\nID: {row[0]}")
            print(f"IP Address: {row[1]}")
            print(f"WHOIS IP: {'Updated' if row[2] else 'Not Updated'}")
    else:
        print("No updated records found.")

    # タイムアウトしたIPの数を確認
    cur.execute("SELECT COUNT(*) FROM website_data WHERE status = 98")
    timeout_count = cur.fetchone()[0]
    print(f"\nNumber of IPs that timed out: {timeout_count}")

    # エラーが発生したIPの数を確認
    cur.execute("SELECT COUNT(*) FROM website_data WHERE status = 99")
    error_count = cur.fetchone()[0]
    print(f"Number of IPs with errors: {error_count}")


except Exception as e:
    print(f"Database connection error: {e}")

finally:
    # データベース接続を閉じる
    if cur:
        cur.close()
