import psycopg2
import subprocess
import signal
import json

# タイムアウト処理のための関数
def timeout_handler(signum, frame):
    raise TimeoutError("dig command timed out")

# 設定ファイルの読み込み
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# データベース接続情報
db_config = config['database']
db_host = db_config['host']
db_name = db_config['name']
db_user = db_config['user']
db_password = db_config['password']

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
            # タイムアウトの設定（例：10秒）
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)
            try:
                # digコマンドの実行
                result = subprocess.run(['dig', domain, 'AAA'], capture_output=True, text=True, timeout=10)
                dig_output = result.stdout.strip()
                
                # タイムアウトのキャンセル
                signal.alarm(0)
                # NXDOMAINまたはNOERRORのみの場合のみ記録
                if 'NXDOMAIN' in dig_output:
                    domain_status = 'NXDOMAIN'
                elif 'NOERROR' in dig_output:
                    domain_status = 'NOERROR'
                else:
                    domain_status = 'ERROR'  # NXDOMAINまたはNOERROR以外の場合はERROR
            except (subprocess.TimeoutExpired, TimeoutError):
                domain_status = 'TIMEOUT'
            
            # データベースの更新
            if domain_status in ['NXDOMAIN', 'NOERROR', 'ERROR', 'TIMEOUT']:
                status = 1 if domain_status in ['NXDOMAIN', 'NOERROR'] else 99
                cur.execute("UPDATE website_data SET domain_status = %s, last_update = now(), status = %s WHERE id = %s", (domain_status, status, domain_id))
                conn.commit()
                domains_processed += 1
                print(f"Updated domain {domain} with status {domain_status} - {domains_processed}/{total_domains} domains processed")
            else:
                print(f"No valid status found for domain {domain}")
        except Exception as e:
            print(f"Error processing domain {domain}: {e}")
        finally:
            # タイムアウトのリセット
            signal.alarm(0)
except Exception as e:
    print(f"Database connection error: {e}")
finally:
    # データベース接続を閉じる
    if conn:
        cur.close()
        conn.close()
