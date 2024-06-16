import pandas as pd
from urllib.parse import urlparse

# CSVファイルのパス
csv_file_path = "URL.csv"

# CSVファイルを読み込む
df = pd.read_csv(csv_file_path)

# url_pc_site列からドメインを抽出し、新しい列 domain を追加
df['domain'] = df['url_pc_site'].apply(lambda x: urlparse(x).netloc)

# 変更を保存
df.to_csv(csv_file_path, index=False)

print("ドメインの抽出と追加が完了しました。")
