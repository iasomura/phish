# Nitter RSS Monitor

フィッシングサイトやマルウェアサイトなどの不正なウェブサイトの情報を収集するためのRSSフィード監視システムです。

## 機能概要

- 複数のRSSフィードを同時に監視
- デファングされたURL（hxxp://example[.]com形式）を検出し、通常のURLに変換
- 検出したURLをPostgreSQLデータベースに登録
- 登録したURLに対して自動的に追加分析を実行
- ローテーションログによる動作記録

## 必要要件

- Python 3.8以上
- PostgreSQLデータベース
- 以下のPythonパッケージ：
  ```bash
  pip install feedparser schedule psycopg2-binary requests
  ```

## インストール方法

1. リポジトリをクローン
```bash
git clone [repository-url]
cd nitter
```

2. 設定ファイルの作成
```python
# config.py
def load_db_config():
    return {
        'host': 'localhost',
        'database': 'your_database_name',
        'user': 'your_username',
        'password': 'your_password',
        'port': '5432'
    }

RSS_FEEDS = [
    {
        'name': 'feed_name',
        'url': 'feed_url'
    }
]

LOG_DIR = 'logs'
NITTER_LOG = 'nitter.log'
```

## データベース設定

対象のPostgreSQLデータベースに以下のテーブルが必要です：

```sql
CREATE TABLE website_data (
    id SERIAL PRIMARY KEY,
    status INTEGER DEFAULT 0,
    last_update TIMESTAMP WITH TIME ZONE,
    phish_from VARCHAR(255),
    url TEXT,
    phish_id VARCHAR(255),
    phish_detail_url TEXT,
    phish_ip_address INET,
    cidr_block CIDR,
    verified BOOLEAN DEFAULT FALSE,
    online_status BOOLEAN DEFAULT FALSE,
    target VARCHAR(255),
    domain VARCHAR(255) UNIQUE
);
```

## 使用方法

1. config.pyの設定
- データベース接続情報の設定
- 監視対象RSSフィードの設定
- ログディレクトリの設定

2. プログラムの実行
```bash
python main.py
```

3. ログの確認
- logs/nitter.log に動作ログが記録されます
- ログは100KBごとにローテーションされ、最大5世代保存されます

## 動作の流れ

1. RSSフィードの監視（1分間隔）
2. 新規エントリーの検出
3. デファングされたURLの抽出と変換
4. データベースへの登録
5. 追加分析スクリプトの実行
   - ドメインステータスチェック
   - WHOIS情報取得
   - DNS情報取得
   - IP情報取得
   - IP WHOIS情報取得
   - HTMLコンテンツ取得

## ログ出力例

```
2024-11-16 10:00:00 - INFO - nitter: 監視を開始します...
2024-11-16 10:01:00 - INFO - nitter: 更新: 新しいフィッシングサイトを検出
2024-11-16 10:01:01 - INFO - nitter: Inserted URL to database: http://example.com
```

## 注意事項

- プログラムの重複実行は防止されます
- 同一ドメインのURLは重複して登録されません
- ネットワークエラーやデータベースエラーは自動的に記録されます
- 分析スクリプトのエラーは個別に記録され、他の処理は継続されます

## エラー対応

1. データベース接続エラー
   - config.pyの接続情報を確認
   - PostgreSQLサーバーの状態を確認

2. RSSフィード取得エラー
   - フィードURLの有効性を確認
   - ネットワーク接続を確認

3. 分析スクリプト実行エラー
   - スクリプトのパスを確認
   - 各スクリプトの動作状態を確認

## ライセンス

[ライセンス情報を記載]

## 作者

[作者情報を記載]