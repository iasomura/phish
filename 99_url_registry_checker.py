import psycopg2
import json

# ---------------------------------------------------------------
# プログラムの機能:
# 1. URLの一覧をファイルから読み込みます。
# 2. 読み込んだURLが、PostgreSQLデータベースのwebsite_dataテーブルのURLカラムに
#    記録されているか確認します。
# 3. URLカラムに登録されていた場合、そのURLをregistered.txtに書き込みます。
# 4. URLカラムに登録されていない場合、そのURLをurls.txtに書き込みます。
# 5. データベースの接続情報はconfig.jsonから読み込みます。
# ---------------------------------------------------------------

# config.jsonからデータベース設定を読み込む
with open('config.json') as config_file:
    config = json.load(config_file)

# config.jsonからデータベース接続情報を取得
db_config = config['database']

# ファイルパス
url_list_file = 'urls_to_check.txt'  # URLリストのファイル名
registered_file = 'registered.txt'
unregistered_file = 'kesagatame.txt'

# PostgreSQLデータベースに接続
conn = psycopg2.connect(
    host=db_config['host'],
    dbname=db_config['dbname'],
    user=db_config['user'],
    password=db_config['password']
)
cursor = conn.cursor()

# URLが登録済みかどうかを確認する関数
def is_url_registered(url):
    cursor.execute("SELECT 1 FROM website_data WHERE url = %s", (url,))
    return cursor.fetchone() is not None

# URLリストのファイルと出力ファイルを開く
with open(url_list_file, 'r') as url_file, \
        open(registered_file, 'a') as reg_file, \
        open(unregistered_file, 'a') as unreg_file:

    # リストの各URLを処理
    for url in url_file:
        url = url.strip()  # URLの前後の余白を削除
        if is_url_registered(url):
            reg_file.write(url + '\n')  # registered.txtに書き込む
        else:
            unreg_file.write(url + '\n')  # urls.txtに書き込む

# クリーンアップ
cursor.close()
conn.close()

print("処理が完了しました！")
