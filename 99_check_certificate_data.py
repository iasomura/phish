import psycopg2
import pandas as pd
import json
import matplotlib.pyplot as plt

# config.json ファイルの読み込み
with open('config.json', 'r') as f:
    config = json.load(f)

# PostgreSQLデータベースに接続
connection = psycopg2.connect(
    host=config["database"]["host"],
    database=config["database"]["dbname"],
    user=config["database"]["user"],
    password=config["database"]["password"]
)

# クエリを作成 (status = 7 の条件を追加し、url と domain を含む)
query = """
    SELECT id, url, domain, https_certificate_date, https_certificate_body, https_certificate_domain,
           https_certificate_issuer, https_certificate_expiry, https_certificate_public_key,
           https_certificate_signature_algorithm, https_certificate_extensions
    FROM website_data
    WHERE status = 7
       AND (https_certificate_date IS NULL
       OR https_certificate_body IS NULL
       OR https_certificate_domain IS NULL
       OR https_certificate_issuer IS NULL
       OR https_certificate_expiry IS NULL
       OR https_certificate_public_key IS NULL
       OR https_certificate_signature_algorithm IS NULL
       OR https_certificate_extensions IS NULL)
"""

# データを抽出し、pandasのDataFrameに格納
df = pd.read_sql(query, connection)

# 全体のデータ件数を取得
total_count = len(df)

# 欠損データの集計
missing_data_count = df.isnull().sum()

# 欠損データの割合を計算
missing_data_ratio = (df.isnull().sum() / total_count) * 100

# データベース接続を閉じる
connection.close()

# 全体の件数を表示
print(f"全体のデータ件数: {total_count} 件")

# 欠損データの割合も表示
print("欠損データの割合:\n", missing_data_ratio)

# 欠損データが多いカラムを棒グラフで可視化
plt.figure(figsize=(10, 6))
missing_data_count.plot(kind='bar', color='skyblue')
plt.title(f'Missing Data Count per Column (Total {total_count} entries)')
plt.ylabel('Number of Missing Entries')
plt.xlabel('Columns')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# グラフを表示
plt.show()

# 結果の上位5行を表示 (urlとdomainを含む)
print(df[['id', 'url', 'domain']].head())
