from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
import requests
import asyncio
import os

# 1. Render'ın uyutmaması için mini web sunucusu
app = Flask('')

@app.route('/')
def home():
    return "Steam İstek Botu aktif ve çalışıyor!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Discord Bot Ayarları
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- KANAL ID'LERİ ---
ISTEK_KANAL_ID = 1547075206693261385    # Kullanıcıların App ID atacağı kanal ID'si
YETKILI_LOG_ID = 1547080310410186794    # Yetkililerin/YT'lerin göreceği gizli kanal ID'si

# Gelen Steam App ID'lerini takip etmek için hafıza
oyun_istekleri = set()

def steam_oyun_adi_getir(app_id):
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=turkish"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            app_str = str(app_id)
            if data and app_str in data and data[app_str].get("success"):
                return data[app_str]["data"].get("name", "Bilinmeyen Oyun")
    except Exception:
        pass
    return None

@bot.event
async def on_ready():
    print(f"{bot.user.name} başarıyla giriş yaptı ve istek sistemi aktif!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Sadece belirlenen istek kanalında çalışır
    if message.channel.id == ISTEK_KANAL_ID:
        app_id = message.content.strip()

        # Sayı (App ID) kontrolü
        if not app_id.isdigit():
            uyari = await message.channel.send(f"{message.author.mention} ❌ Lütfen sadece geçerli bir Steam App ID (sayı) girin!")
            await asyncio.sleep(4)
            try:
                await message.delete()
                await uyari.delete()
            except:
                pass
            return

        # Daha önce istenmiş mi kontrolü
        if app_id in oyun_istekleri:
            uyari = await message.channel.send(f"{message.author.mention} ❌ Bu oyun zaten istek listemizde veya uygulamamızda var!")
            await asyncio.sleep(4)
            try:
                await message.delete()
                await uyari.delete()
            except:
                pass
            return

        # Steam'den oyun adını çek
        oyun_adi = steam_oyun_adi_getir(app_id)
        if not oyun_adi:
            uyari = await message.channel.send(f"{message.author.mention} ❌ Bu App ID ile eşleşen bir Steam oyunu bulunamadı!")
            await asyncio.sleep(4)
            try:
                await message.delete()
                await uyari.delete()
            except:
                pass
            return

        # Listeye ekle (aynı ID tekrar atılmasın diye)
        oyun_istekleri.add(app_id)

        # Kullanıcıya bilgi ver (✅ bas ve mesaj gönder)
        await message.add_reaction("✅")
        cevap = await message.channel.send(f"{message.author.mention} İstek oyununuz yetkililere yönlendirildi!")
        
        # Sadece yetkililerin/YT'lerin göreceği kanala rapor düş
        yetkili_kanal = bot.get_channel(YETKILI_LOG_ID)
        if yetkili_kanal:
            await yetkili_kanal.send(f"🎮 **Yeni Oyun İsteği!**\n🔹 **Oyun:** {oyun_adi}\n👤 **İsteyen:** {message.author.mention}\n🔗 **Steam:** https://store.steampowered.com/app/{app_id}")

        # Kullanıcının gönderdiği App ID mesajını ve botun "yönlendirildi" mesajını temizle (isteğe bağlı, ortalık temiz dursun diye)
        await asyncio.sleep(5)
        try:
            await message.delete()
            await cevap.delete()
        except:
            pass
        return

    await bot.process_commands(message)

# 3. Web sunucusunu başlat ve botu çalıştır
keep_alive()
bot.run(os.getenv("BOT_TOKEN"))