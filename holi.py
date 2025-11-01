from telethon import TelegramClient, events
import requests

# Telegram API bilgileri
api_id = '25327248'  # Kendi API ID'nizi yazın
api_hash = '5f822b461c79a74ea333ef87b679ee11'  # Kendi API Hash'inizi yazın
bot_token = '8594053154:AAGIYnXB2yU8OQ7SgDLxezMaH-kBnDUol84'  # Kendi bot tokenınızı buraya yaz
chat_id = '@holimesajbot'  # Bot kanalınızın @username'ini buraya yazın (örneğin: @botkanalim)

# Telegram Client başlatma
client = TelegramClient('session_name', api_id, api_hash)

# Mesaj gönderme fonksiyonu
def send_to_bot_channel(message):
    url = f'https://api.telegram.org/bot{8594053154:AAHMJQVtXfDUkwXnHCqPbIMsEsJ6lDJxPN4}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("Mesaj başarıyla gönderildi!")
    else:
        print("Mesaj gönderilemedi!")

# Bonuspops kanalındaki mesajları dinleme
@client.on(events.NewMessage(chats='https://t.me/bonuspopsresmi'))
async def handler(event):
    message = event.message.text
    if 'Holigan' in message:  # Anahtar kelimeyi kontrol et
        print(f"Yeni mesaj bulundu: {message}")
        send_to_bot_channel(message)  # Bot kanalına gönder

# Bağlantıyı başlat
client.start()
print("Bot çalışıyor, mesajları dinliyor...")
client.run_until_disconnected()
