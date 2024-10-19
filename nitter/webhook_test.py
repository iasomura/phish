import requests

def send_discord_notification(webhook_url, message):
    data = {
        "content": message
    }
    
    response = requests.post(webhook_url, json=data)
    
    if response.status_code == 204:
        print("メッセージが送信されました")
    else:
        print(f"エラーが発生しました: {response.status_code}")

# DiscordのWebhook URL
webhook_url = "https://discord.com/api/webhooks/1297092831135141928/vTynmQcDMiuGIJ3GLuyy0MEivfJeV9PNUBaDABH29oc4_vqX_Fa6nhiDzTbtAvCM4AiM"
message = "これはPythonからの通知です！"

send_discord_notification(webhook_url, message)
