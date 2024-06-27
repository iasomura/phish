import requests
from tqdm import tqdm

def check_server_status(domain):
    http_url = f"http://{domain}"
    https_url = f"https://{domain}"

    http_status = False
    https_status = False

    try:
        http_response = requests.get(http_url, timeout=5)
        if http_response.status_code == 200:
            http_status = True
    except requests.RequestException:
        pass

    try:
        https_response = requests.get(https_url, timeout=5)
        if https_response.status_code == 200:
            https_status = True
    except requests.RequestException:
        pass

    return http_status, https_status

def main(file_path, output_path):
    with open(file_path, 'r') as file:
        domains = file.readlines()

    domains = [domain.strip() for domain in domains]

    results = []
    for domain in tqdm(domains, desc="Checking domains", unit="domain"):
        http_status, https_status = check_server_status(domain)
        if http_status or https_status:
            results.append((domain, http_status, https_status))

    with open(output_path, 'w') as output_file:
        for domain, http_status, https_status in results:
            if http_status:
                output_file.write(f"http://{domain}\n")
            if https_status:
                output_file.write(f"https://{domain}\n")

    for domain, http_status, https_status in results:
        print(f"Domain: {domain}")
        print(f"  HTTP: {'Running' if http_status else 'Not Running'}")
        print(f"  HTTPS: {'Running' if https_status else 'Not Running'}")
        print()

if __name__ == "__main__":
    input_file_path = 'domains.txt'  # ドメイン一覧が記載されたテキストファイルのパスを指定
    output_file_path = 'active_domains.txt'  # 稼働中のドメインを保存するファイルのパスを指定
    main(input_file_path, output_file_path)
