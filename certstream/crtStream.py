#UFJ → R3
#SMBC → R10
#みずほ → R11
import certstream
import json
from datetime import datetime

# ファイルに出力するための関数
def write_to_file(data):
    with open('certificates.txt', 'a') as f:
        f.write(json.dumps(data, indent=2))
        f.write("\n\n")

def print_callback(message, context):
    if message['message_type'] == "certificate_update":
        data = message['data']
        cert_chain = data['leaf_cert']
        subject = cert_chain['subject']
        issuer = cert_chain['issuer']
        all_domains = cert_chain.get('all_domains', [])
        not_before = cert_chain.get('not_before')

        # 証明書の有効開始日時を確認
        if not_before:
            # not_before は秒単位のタイムスタンプ
            not_before_date = datetime.utcfromtimestamp(not_before)

            # 2024/06/19 以降に発行された証明書か確認
            if not_before_date >= datetime(2024, 6, 19):
                # 条件に合致するか確認
                if (issuer.get('O') == "Let's Encrypt" and
                    #issuer.get('CN') == "R11" and
                    issuer.get('CN') in ["R11","R3", "R10"] and

                    any(domain.endswith('.duckdns.org') for domain in all_domains)):
                    
                    # SANが複数ある場合、情報をファイルに書き出す
                    if len(all_domains) > 20:
                        cert_info = {
                            "subject": subject,
                            "issuer": issuer,
                            "all_domains": all_domains,
                            "not_before": not_before_date.isoformat()
                        }
                        write_to_file(cert_info)
                        print("Certificate written to file.")

print("Starting Certstream listener...")
certstream.listen_for_events(print_callback, url='wss://certstream.calidog.io/')
