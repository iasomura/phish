# phish

### Readme.md に記載する文章とステータス番号一覧


#### 英語 (English):

**Program Overview**  
This project contains a series of scripts that collect data from websites, perform WHOIS lookups, gather IP information, check domain status, capture screenshots, and manage SSL certificates. The data is stored in a PostgreSQL database for further analysis. Each operation logs a numeric status in the database to indicate the outcome of the process.

**Status Codes and Their Meanings**:

- **0 - Pending**: The process is still ongoing.
- **1 - Success (NOERROR or NXDOMAIN)**: The `dig` command was successful, and the data was updated in the database.
- **2 - WHOIS Success**: The WHOIS query was successful, and the database was updated.
- **3 - DNS Records Updated**: DNS records such as A, MX, and NS records were updated successfully.
- **4 - IP Info Updated**: IP information was retrieved and updated in the database.
- **5 - WHOIS IP Updated**: WHOIS IP information was updated successfully.
- **6 - MHTML Content Updated**: MHTML (webpage archive format) data was updated successfully.
- **7 - SSL Certificate Updated**: SSL certificate information was updated successfully.
- **97 - SSL Certificate Failed**: Failed to retrieve SSL certificate information.
- **98 - Timeout**: The process timed out.
- **99 - Error**: An error occurred during the process.

This status code system helps track the success or failure of each operation. By monitoring these codes, users can easily identify issues and take corrective actions.

---

#### 日本語 (Japanese):

**プログラム概要**  
このプロジェクトには、ウェブサイトからデータを収集し、WHOISルックアップを実行し、IP情報を取得し、ドメインステータスを確認し、スクリーンショットをキャプチャし、SSL証明書を管理するための一連のスクリプトが含まれています。データはPostgreSQLデータベースに保存され、後で分析されます。各操作は、そのプロセスの結果を示す数値ステータスをデータベースに記録します。

**ステータスコードとその意味**:

- **0 - 保留中 (Pending)**: 処理がまだ進行中であることを示します。
- **1 - 成功 (Success: NOERROR or NXDOMAIN)**: `dig`コマンドが成功し、データがデータベースに更新されたことを示します。
- **2 - WHOIS 成功 (WHOIS Success)**: WHOISクエリが成功し、データベースが更新されました。
- **3 - DNSレコード更新 (DNS Records Updated)**: Aレコード、MXレコード、NSレコードなどのDNS情報が正常に更新されました。
- **4 - IP情報更新 (IP Info Updated)**: IPアドレス情報が正常に取得され、データベースに更新されました。
- **5 - WHOIS IP更新 (WHOIS IP Updated)**: WHOIS IP情報が正常に更新されました。
- **6 - MHTMLコンテンツ更新 (MHTML Content Updated)**: MHTML（ウェブページのアーカイブ形式）のデータが正常に更新されました。
- **7 - SSL証明書更新 (SSL Certificate Updated)**: SSL証明書情報が正常に更新されました。
- **97 - SSL証明書失敗 (SSL Certificate Failed)**: SSL証明書情報の取得に失敗しました。
- **98 - タイムアウト (Timeout)**: 処理がタイムアウトしました。
- **99 - エラー (Error)**: 処理中にエラーが発生しました。

このステータスコードシステムにより、各操作の成功や失敗を追跡することができます。これらのコードを監視することで、ユーザーは問題を迅速に特定し、対応することが可能になります。

---
