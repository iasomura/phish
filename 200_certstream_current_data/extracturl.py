import re

def extract_urls(file_path):
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    urls = url_pattern.findall(content)

    return urls

if __name__ == "__main__":
    input_file = 'urls.txt'  # ファイル名を適宜変更してください
    extracted_urls = extract_urls(input_file)
    
    for url in extracted_urls:
        print(url)
