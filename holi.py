from telethon import TelegramClient, events

api_id = 25327248  # Kendi API ID'nizi yazın
api_hash = '5f822b461c79a74ea333ef87b679ee11'  # Kendi API Hash'inizi yazın
phone_number = '+905367714495'  # Telefon numaranızı buraya yazın (örneğin, '+1234567890')
chat_id = '@holimesajbot'  # Bot kanalınızın @username'ini buraya yazın

client = TelegramClient('session_name', api_id, api_hash)

# /bildirim komutunu aldığında botun cevap vermesi
@client.on(events.NewMessage(pattern='/bildirim'))  # '/bildirim' komutuna karşılık verir
async def handler(event):
    user_id = event.sender_id  # Mesajı gönderen kullanıcının ID'si
    print(f"Yeni /bildirim komutu geldi, Gönderen Kullanıcı ID: {user_id}")  # Gelen kullanıcıyı yazdır

    # Botun cevabını gönder
    response_message = "Holi kaldırdı sikecek kaç"
    await client.send_message(user_id, response_message)  # Yanıtı kullanıcıya gönder

# Telegram'a giriş yapma
async def start():
    await client.start(phone_number)
    print("Hesabınızla giriş yapıldı!")

    # Botun çalışmaya başladığına dair bildirim gönderebiliriz (Örneğin, kendinize)
    startup_message = "Bot çalışmaya başladı ve mesajlar dinleniyor..."
    print(startup_message)  # Burada sadece başlatma mesajını konsola yazdırıyoruz

# Bağlantıyı başlat
client.loop.run_until_complete(start())

print("Bot çalışıyor, mesajları dinliyor...")
client.run_until_disconnected()
