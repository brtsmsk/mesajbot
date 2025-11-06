import asyncio
import os
import re
import sys
import requests
import time
from telethon import TelegramClient, events
from telethon.errors import (
    ChannelInvalidError, UsernameNotOccupiedError,
    SessionPasswordNeededError, FloodWaitError
)
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH") or ""
PHONE = os.getenv("PHONE_NUMBER") or ""          # yalnızca +90... biçiminde
BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
CHANNEL = os.getenv("CHANNEL") or ""
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "0"))
KEYWORD = (os.getenv("KEYWORD") or "oran").lower()
TWO_FA = os.getenv("TELEGRAM_2FA_PASSWORD") or ""

if ":" in PHONE:
    sys.exit("HATA: PHONE_NUMBER alanına bot token girilmiş. PHONE_NUMBER +90... olmalı.")
if not (API_ID and API_HASH and PHONE and BOT_TOKEN and CHANNEL and TARGET_CHAT_ID):
    sys.exit("HATA: .env zorunlu alanlardan biri boş.")

BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_bot_message(text, disable_preview=True):
    try:
        r = requests.post(
            BOT_API,
            data={"chat_id": TARGET_CHAT_ID, "text": text, "disable_web_page_preview": disable_preview, "parse_mode": "HTML"},
            timeout=10
        )
        r.raise_for_status()
    except Exception as e:
        print(f"[BOT SEND ERROR] {e}")

def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

client = TelegramClient("user_session", API_ID, API_HASH)
target_chat = None

# --- BURASI: GELİŞMİŞ GİRİŞ AKIŞI ---
async def login_user():
    """
    1) Yetkili oturum varsa geç
    2) QR ile giriş (Telegram uygulamasından 'Cihazlar > Masaüstü Bağla' mantığı)
    3) SMS'i zorla
    4) Çağrı (voice) ile kod
    5) 2FA varsa uygula
    """
    from qrcode import QRCode
    from qrcode.image.pil import PilImage

    await client.connect()
    if await client.is_user_authorized():
        print("✅ Zaten yetkili oturum bulundu.")
        return

    # 2.1) QR login dene
    try:
        print("🔐 QR ile giriş deneniyor...")
        qr_login = await client.qr_login()  # Telegram Desktop’taki QR süreciyle aynı
        # QR URL’sini ASCII QR olarak bas
        try:
            qr = QRCode(border=1)
            qr.add_data(qr_login.url)
            qr.make(fit=True)
            ascii_qr = qr.get_matrix()
            print("\nTarayıp giriş yap: (Telegram > Ayarlar > Cihazlar > 'Masaüstü cihaz bağla')\n")
            for row in ascii_qr:
                print("".join("██" if cell else "  " for cell in row))
            print("\nEğer QR görünmüyorsa bu linki kopyala/QR’e dönüştür: \n", qr_login.url)
        except Exception:
            print("QR üretimi başarısız, URL:", qr_login.url)

        # Kullanıcı uygulamadan onaylayana kadar bekle
        me = await qr_login.wait(timeout=120)  # 2 dk bekle
        if me:
            print(f"✅ QR ile giriş başarılı: {me.username or me.id}")
            return
    except Exception as e:
        print(f"[QR LOGIN] QR denemesi atlandı/başarısız: {e}")

    # 2.2) Kod iste (önce app bildirimi, olmazsa SMS)
    try:
        print("📩 Kod isteği gönderiliyor (önce app bildirimi)...")
        sent = await client.send_code_request(PHONE, force_sms=False)
    except Exception as e:
        print(f"[SEND_CODE_REQUEST] {e} → SMS zorlanıyor...")
        sent = await client.send_code_request(PHONE, force_sms=True)

    # 2.3) Çağrı (voice) yedeği: code gelmediyse isteğe bağlı
    got_code = False
    code = ""
    try:
        code = input("Telegram’dan gelen 5 haneli kodu gir (gelmediyse boş bırak ve Enter’a bas): ").strip()
        got_code = bool(code)
        if not got_code:
            use_call = input("Kod gelmediyse 'A'rama ile kod gelsin mi? (A/e): ").strip().lower().startswith("a")
            if use_call:
                print("📞 Arama talep ediliyor...")
                await client.send_code_request(PHONE, force_sms=False)  # çoğu zaman arama otomatik devreye girer
                print("Telegram aramasını bekle. Ardından kodu gir.")
                code = input("Telefonla gelen kodu gir: ").strip()
                got_code = bool(code)
    except KeyboardInterrupt:
        sys.exit("İptal edildi.")

    if not got_code:
        sys.exit("Kod girilmedi. Giriş tamamlanamadı.")

    # 2.4) Giriş yap
    try:
        await client.sign_in(PHONE, code, phone_code_hash=sent.phone_code_hash)
    except SessionPasswordNeededError:
        pw = TWO_FA or input("2 Adımlı Doğrulama parolasını gir: ").strip()
        await client.sign_in(password=pw)
    except FloodWaitError as fw:
        sys.exit(f"FloodWait: Çok deneme yapıldı. {int(fw.seconds)} saniye sonra tekrar deneyin.")
    except Exception as e:
        sys.exit(f"Giriş başarısız: {e}")

async def resolve_channel():
    try:
        return await client.get_entity(CHANNEL)
    except (ChannelInvalidError, UsernameNotOccupiedError):
        raise RuntimeError("Kanal bulunamadı. CHANNEL değerini @kullanıcıadı veya sayısal ID olarak gir ve "
                           "kullanıcı hesabınla kanala katıldığından emin ol.")

async def main():
    await login_user()

    global target_chat
    target_chat = await resolve_channel()

    # Başlangıçta son mesajı gönder
    last = await client.get_messages(target_chat, limit=1)
    if last and last[0]:
        send_bot_message(f"✅ Başlatıldı. Kanaldaki <b>son mesaj</b>:\n\n{last[0].message or '(metin yok)'}")
    else:
        send_bot_message("✅ Başlatıldı. Kanalda henüz mesaj yok.")

    @client.on(events.NewMessage(chats=target_chat))
    async def _handler(event):
        try:
            msg_text = event.message.message or ""
            if KEYWORD in normalize_text(msg_text):
                send_bot_message(f"🔔 <b>‘{KEYWORD}’</b> içeren yeni mesaj:</b>\n\n{msg_text}")
        except Exception as e:
            print(f"[HANDLER ERROR] {e}")

    print("Dinleniyor... Çıkmak için Ctrl+C")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Durduruldu.")
