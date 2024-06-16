import psycopg2
import subprocess

# データベース接続設定
connection = psycopg2.connect(
    host='localhost',  # ホスト名
    database='website_data',  # データベース名
    user='postgres',  # ユーザ名
    password='asomura'  # パスワード
)

# カーソルの作成
cursor = connection.cursor()


# domainを読み取る
cursor.execute("SELECT id, domain FROM website_data WHERE domain_status IS NULL OR domain_status = '';")
#cursor.execute("SELECT id, domain FROM website_data";)
domains = cursor.fetchall()
total_domains = len(domains)  # 総ドメイン数

# 各ドメインについてdigコマンドを実行し、結果を更新
for index, (domain_id, domain) in enumerate(domains):
    if domain:  # ドメインが None または空文字列でないことを確認
        try:
            # digコマンドの実行
            command = ['dig', domain, '+noall', '+answer', '+comments', '+stats']
            result = subprocess.run(command, capture_output=True, text=True)
            output = result.stdout

            # NXDOMAIN または NOERROR の抽出
            status = None
            if 'NXDOMAIN' in output:
                status = 'NXDOMAIN'
            elif 'NOERROR' in output and 'ANSWER: 0,' in output:
                status = 'NOERROR'

            if status:
                # domain_statusカラムの更新
                cursor.execute("UPDATE website_data SET domain_status = %s WHERE id = %s;", (status, domain_id))
                connection.commit()  # 各更新後にコミット

                # 進捗の表示
                progress = (index + 1) / total_domains * 100
                print(f"Processed {index + 1}/{total_domains} domains ({progress:.2f}%) - Updated domain {domain} with status {status}")
            else:
                print(f"No relevant status found for domain {domain}. Skipping update.")
        except Exception as e:
            print(f"Error processing domain {domain}: {e}")
    else:
        print(f"Skipped processing for domain_id {domain_id} due to invalid domain.")

# カーソルとコネクションのクローズ
cursor.close()
connection.close()
