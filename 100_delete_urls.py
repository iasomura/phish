import psycopg2

# データベース接続情報
db_host = "localhost"
db_name = "website_data"
db_user = "postgres"
db_password = "asomura"

# URLファイルのパス
url_file_path = "url_for_delete.txt"

def read_urls(file_path):
    """ファイルからURLリストを読み込む"""
    with open(file_path, "r") as file:
        urls = [line.strip() for line in file]
    return urls

def delete_matching_urls(urls):
    """データベースから一致するURLを削除する"""
    try:
        # データベースに接続
        connection = psycopg2.connect(
            host=db_host,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        cursor = connection.cursor()

        # URLリストを使って削除クエリを実行
        for url in urls:
            delete_query = "DELETE FROM website_data WHERE url = %s"
            cursor.execute(delete_query, (url,))

        # 変更をコミット
        connection.commit()
        print("一致するURLの行を削除しました。")

    except Exception as error:
        print(f"エラーが発生しました: {error}")

    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    urls = read_urls(url_file_path)
    delete_matching_urls(urls)
