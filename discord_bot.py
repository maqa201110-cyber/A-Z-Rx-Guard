"""
AZRxGUARD — Discord Şubesi (Full Feature Port)
Telegram botundaki tüm özellikler Discord'a aktarılmıştır.
"""

import ast
import asyncio
import base64 as b64lib
import datetime
import hashlib
import html as _html
import io
import json
import logging
import math
import os
import random
import re
import socket as _socket
import string
import urllib.parse

import discord
from discord import app_commands
import requests as http_requests

logger = logging.getLogger(__name__)

# ─── Renkler ───────────────────────────────────────────────────────────────────
RENK_ANA     = 0x5865F2
RENK_YESIL   = 0x57F287
RENK_KIRMIZI = 0xED4245
RENK_SARI    = 0xFEE75C
RENK_TURUNCU = 0xEB6C34
RENK_MAVI    = 0x3498DB

_APK_DOSYALAR_YOL = 'apk_dosyalar.json'
TR_SAAT = datetime.timezone(datetime.timedelta(hours=3))

# ══════════════════════════════════════════════════════════════════════════════
# 📱 TELEFON VERİTABANI (Özet — 12 marka, 400+ model)
# ══════════════════════════════════════════════════════════════════════════════
TELEFON_VERITABANI = {
    'sam': {'ad': 'Samsung', 'emoji': '📱', 'modeller': [
        'Galaxy S25 Ultra','Galaxy S25+','Galaxy S25','Galaxy S25 Edge',
        'Galaxy S24 Ultra','Galaxy S24+','Galaxy S24','Galaxy S24 FE',
        'Galaxy S23 Ultra','Galaxy S23+','Galaxy S23','Galaxy S23 FE',
        'Galaxy S22 Ultra','Galaxy S22+','Galaxy S22',
        'Galaxy S21 Ultra','Galaxy S21+','Galaxy S21','Galaxy S21 FE',
        'Galaxy S20 Ultra','Galaxy S20+','Galaxy S20','Galaxy S20 FE',
        'Galaxy Z Fold 6','Galaxy Z Fold 5','Galaxy Z Fold 4','Galaxy Z Fold 3',
        'Galaxy Z Flip 6','Galaxy Z Flip 5','Galaxy Z Flip 4','Galaxy Z Flip 3',
        'Galaxy A56 5G','Galaxy A55 5G','Galaxy A54 5G','Galaxy A53 5G',
        'Galaxy A36 5G','Galaxy A35 5G','Galaxy A34 5G','Galaxy A33 5G',
        'Galaxy A26 5G','Galaxy A25 5G','Galaxy A24','Galaxy A23 5G',
        'Galaxy A16 5G','Galaxy A15 5G','Galaxy A15','Galaxy A14 5G','Galaxy A14',
        'Galaxy A06','Galaxy A05s','Galaxy A05','Galaxy A04s','Galaxy A03s',
        'Galaxy M55 5G','Galaxy M54 5G','Galaxy M35 5G','Galaxy M34 5G',
    ]},
    'iph': {'ad': 'iPhone (Apple)', 'emoji': '🍎', 'modeller': [
        'iPhone 16 Pro Max','iPhone 16 Pro','iPhone 16 Plus','iPhone 16','iPhone 16e',
        'iPhone 15 Pro Max','iPhone 15 Pro','iPhone 15 Plus','iPhone 15',
        'iPhone 14 Pro Max','iPhone 14 Pro','iPhone 14 Plus','iPhone 14',
        'iPhone 13 Pro Max','iPhone 13 Pro','iPhone 13 mini','iPhone 13',
        'iPhone 12 Pro Max','iPhone 12 Pro','iPhone 12 mini','iPhone 12',
        'iPhone 11 Pro Max','iPhone 11 Pro','iPhone 11',
        'iPhone XS Max','iPhone XS','iPhone XR','iPhone X',
        'iPhone SE (2022)','iPhone SE (2020)',
    ]},
    'xia': {'ad': 'Xiaomi / Redmi / POCO', 'emoji': '📱', 'modeller': [
        'Xiaomi 15 Ultra','Xiaomi 15 Pro','Xiaomi 15',
        'Xiaomi 14 Ultra','Xiaomi 14 Pro','Xiaomi 14','Xiaomi 14T Pro','Xiaomi 14T','Xiaomi 14C',
        'Xiaomi 13 Ultra','Xiaomi 13 Pro','Xiaomi 13','Xiaomi 13T Pro','Xiaomi 13T',
        'Redmi Note 14 Pro+ 5G','Redmi Note 14 Pro 5G','Redmi Note 14 Pro','Redmi Note 14 5G','Redmi Note 14',
        'Redmi Note 13 Pro+ 5G','Redmi Note 13 Pro 5G','Redmi Note 13 Pro','Redmi Note 13',
        'Redmi Note 12 Pro+ 5G','Redmi Note 12 Pro 5G','Redmi Note 12',
        'Redmi 14C','Redmi 13C','Redmi 13','Redmi 12C','Redmi 12',
        'POCO X7 Pro 5G','POCO X7 5G','POCO X6 Pro 5G','POCO X5 Pro 5G',
        'POCO F6 Pro','POCO F6 5G','POCO F5 Pro 5G','POCO F5 5G','POCO F4 5G',
        'POCO M6 Pro 5G','POCO M5s','POCO C75','POCO C65',
    ]},
    'hua': {'ad': 'Huawei', 'emoji': '📱', 'modeller': [
        'Pura 70 Ultra','Pura 70 Pro+','Pura 70 Pro','Pura 70',
        'Mate 60 Pro+','Mate 60 Pro','Mate 60','Mate X5',
        'P60 Pro','P60 Art','P60','P50 Pro','P50','P40 Pro+','P40 Pro','P40',
        'Nova 12 Ultra','Nova 12 Pro','Nova 12','Nova 11 Ultra','Nova 11 Pro',
    ]},
    'opo': {'ad': 'OPPO', 'emoji': '📱', 'modeller': [
        'Find X8 Pro','Find X8','Find X7 Ultra','Find X7','Find X6 Pro','Find N3 Flip',
        'Reno 12 Pro','Reno 12','Reno 11 Pro','Reno 11','Reno 10 Pro+','Reno 10 Pro','Reno 10',
        'A99','A79 5G','A78 5G','A58','A38','A18',
    ]},
    'viv': {'ad': 'Vivo', 'emoji': '📱', 'modeller': [
        'X200 Ultra','X200 Pro','X200','X100 Ultra','X100 Pro','X100',
        'V40 Pro','V40','V30 Pro','V30','V29 Pro','V29',
        'Y300 Pro+','Y300 Pro','Y200 GT','Y200 Pro','Y100',
    ]},
    'goo': {'ad': 'Google Pixel', 'emoji': '📱', 'modeller': [
        'Pixel 9 Pro XL','Pixel 9 Pro','Pixel 9','Pixel 9a','Pixel 9 Pro Fold',
        'Pixel 8 Pro','Pixel 8','Pixel 8a',
        'Pixel 7 Pro','Pixel 7','Pixel 7a',
        'Pixel 6 Pro','Pixel 6','Pixel 6a',
        'Pixel 5a','Pixel 5',
    ]},
    'one': {'ad': 'OnePlus', 'emoji': '📱', 'modeller': [
        'OnePlus 13','OnePlus 13R','OnePlus 12','OnePlus 12R','OnePlus 11','OnePlus 11R',
        'OnePlus Nord 4','OnePlus Nord CE 4 Lite','OnePlus Nord CE 4','OnePlus Nord CE 3 Lite','OnePlus Nord 3',
        'OnePlus Open',
    ]},
    'rea': {'ad': 'Realme', 'emoji': '📱', 'modeller': [
        'GT 7 Pro','GT 6T','GT 6','GT Neo 6 SE','GT Neo 6',
        'GT 5 Pro','GT 5 240W','GT 3',
        '12 Pro+ 5G','12 Pro 5G','12 5G','12+','12',
        'C67 5G','C65 5G','C61 5G','C55','C53',
    ]},
    'mot': {'ad': 'Motorola', 'emoji': '📱', 'modeller': [
        'Edge 50 Ultra','Edge 50 Pro','Edge 50 Fusion','Edge 50',
        'Edge 40 Pro','Edge 40 Neo','Edge 40',
        'Moto G85 5G','Moto G75 5G','Moto G55 5G','Moto G35 5G','Moto G15',
        'Razr 50 Ultra','Razr 50','Razr 40 Ultra',
    ]},
    'nok': {'ad': 'Nokia', 'emoji': '📱', 'modeller': [
        'XR21','X30 5G','G60 5G','G42 5G','G22','G21',
        'C32','C22','C12','C02','105 Plus','106',
    ]},
    'son': {'ad': 'Sony Xperia', 'emoji': '📱', 'modeller': [
        'Xperia 1 VI','Xperia 5 VI','Xperia 10 VI',
        'Xperia 1 V','Xperia 5 V','Xperia 10 V',
        'Xperia 1 IV','Xperia 5 IV','Xperia 10 IV',
    ]},
}

FIYAT_GE_DB = {
    'Samsung Galaxy S25 Ultra':'4 499 ₾','Samsung Galaxy S25+':'3 499 ₾','Samsung Galaxy S25':'2 799 ₾',
    'Samsung Galaxy S24 Ultra':'3 899 ₾','Samsung Galaxy S24+':'3 199 ₾','Samsung Galaxy S24':'2 599 ₾','Samsung Galaxy S24 FE':'1 899 ₾',
    'Samsung Galaxy S23 Ultra':'3 199 ₾','Samsung Galaxy S23+':'2 499 ₾','Samsung Galaxy S23':'1 999 ₾',
    'Samsung Galaxy Z Fold 6':'5 999 ₾','Samsung Galaxy Z Fold 5':'4 999 ₾','Samsung Galaxy Z Flip 6':'3 499 ₾','Samsung Galaxy Z Flip 5':'2 799 ₾',
    'Samsung Galaxy A55 5G':'1 299 ₾','Samsung Galaxy A54 5G':'1 099 ₾','Samsung Galaxy A35 5G':'999 ₾',
    'Samsung Galaxy A25 5G':'749 ₾','Samsung Galaxy A15 5G':'549 ₾','Samsung Galaxy A05s':'379 ₾',
    'iPhone 16 Pro Max':'4 999 ₾','iPhone 16 Pro':'4 399 ₾','iPhone 16 Plus':'3 699 ₾','iPhone 16':'3 199 ₾','iPhone 16e':'2 299 ₾',
    'iPhone 15 Pro Max':'4 299 ₾','iPhone 15 Pro':'3 699 ₾','iPhone 15 Plus':'3 199 ₾','iPhone 15':'2 699 ₾',
    'iPhone 14 Pro Max':'3 699 ₾','iPhone 14 Pro':'3 199 ₾','iPhone 14 Plus':'2 699 ₾','iPhone 14':'2 299 ₾',
    'iPhone 13 Pro Max':'2 999 ₾','iPhone 13 Pro':'2 499 ₾','iPhone 13':'1 899 ₾',
    'iPhone 12 Pro Max':'2 199 ₾','iPhone 12':'1 499 ₾','iPhone 11':'1 099 ₾',
    'iPhone XS Max':'899 ₾','iPhone XR':'699 ₾','iPhone SE (2022)':'999 ₾',
    'Xiaomi 15 Ultra':'3 999 ₾','Xiaomi 15 Pro':'3 299 ₾','Xiaomi 15':'2 699 ₾',
    'Xiaomi 14 Ultra':'3 499 ₾','Xiaomi 14 Pro':'2 899 ₾','Xiaomi 14':'2 299 ₾',
    'Xiaomi 13 Ultra':'2 799 ₾','Xiaomi 13':'1 899 ₾',
    'Redmi Note 14 Pro+ 5G':'1 199 ₾','Redmi Note 14 Pro 5G':'999 ₾','Redmi Note 14':'699 ₾',
    'Redmi Note 13 Pro+ 5G':'1 099 ₾','Redmi Note 13 Pro':'899 ₾','Redmi Note 13':'649 ₾',
    'POCO X7 Pro 5G':'1 199 ₾','POCO X7 5G':'999 ₾','POCO F6 Pro':'1 499 ₾','POCO F6 5G':'1 299 ₾',
    'Pixel 9 Pro XL':'3 799 ₾','Pixel 9 Pro':'3 299 ₾','Pixel 9':'2 799 ₾','Pixel 9a':'1 999 ₾',
    'Pixel 8 Pro':'2 999 ₾','Pixel 8':'2 299 ₾','Pixel 8a':'1 799 ₾',
    'OnePlus 13':'2 999 ₾','OnePlus 12':'2 299 ₾','OnePlus 11':'1 799 ₾',
}

# ─── Sahte kimlik verileri ──────────────────────────────────────────────────────
_TR_ISIMLER = [
    ("Ahmet","Yılmaz"),("Mehmet","Kaya"),("Ayşe","Demir"),("Fatma","Şahin"),
    ("Ali","Çelik"),("Mustafa","Koç"),("Zeynep","Arslan"),("Elif","Aydın"),
    ("Emre","Doğan"),("Selin","Kurt"),("Can","Öztürk"),("Deniz","Kaplan"),
    ("Berk","Aslan"),("İrem","Polat"),("Kemal","Erdoğan"),("Esra","Şimşek"),
    ("Yusuf","Güneş"),("Leyla","Akbulut"),("Tarık","Yıldız"),("Nur","Özdemir"),
]
_MESLEKLER = [
    "Yazılım Mühendisi","Öğretmen","Doktor","Avukat","Mimar","Muhasebeci",
    "Eczacı","Grafik Tasarımcı","Pazarlama Uzmanı","Veri Analisti",
    "Hemşire","Elektrik Mühendisi","Gazeteci","Psikolog","Ekonomist",
    "Makine Mühendisi","Web Tasarımcı","İnsan Kaynakları Uzmanı","Aktüer","Tercüman",
]
_SEHIRLER = [
    "İstanbul","Ankara","İzmir","Bursa","Antalya","Adana",
    "Konya","Gaziantep","Trabzon","Kayseri","Diyarbakır","Eskişehir",
    "Bakü","Tiflis","Moskova","Berlin","Londra",
]

# ─── Şifreleme ────────────────────────────────────────────────────────────────
_MORSE = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....',
    'I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-',
    'R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....',
    '6':'-....','7':'--...','8':'---..','9':'----.','  ':'/',
}

# ─── Oyun state ───────────────────────────────────────────────────────────────
_oyun_state: dict = {}   # user_id -> {'hedef': int, 'denemeler': int}

# ══════════════════════════════════════════════════════════════════════════════
# Yardımcı fonksiyonlar
# ══════════════════════════════════════════════════════════════════════════════

def _caesar(metin: str, n: int) -> str:
    return ''.join(
        chr((ord(c) - (ord('A') if c.isupper() else ord('a')) + n) % 26 + (ord('A') if c.isupper() else ord('a')))
        if c.isalpha() else c for c in metin
    )

def _hex_to_rgb(hex_str: str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c*2 for c in hex_str)
    if len(hex_str) != 6:
        return None
    try:
        return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    except ValueError:
        return None

def _rgb_to_hsl(r, g, b):
    r, g, b = r/255, g/255, b/255
    cmax, cmin = max(r,g,b), min(r,g,b)
    delta = cmax - cmin
    lv = (cmax + cmin) / 2
    if delta == 0:
        h = s = 0.0
    else:
        s = delta / (1 - abs(2*lv - 1))
        if cmax == r:   h = 60 * (((g-b)/delta) % 6)
        elif cmax == g: h = 60 * ((b-r)/delta + 2)
        else:           h = 60 * ((r-g)/delta + 4)
    return round(h), round(s*100), round(lv*100)

def guvenli_hesapla(ifade: str) -> str:
    try:
        ifade_clean = ifade.strip().replace('^', '**')
        if len(ifade_clean) > 200:
            return "❌ İfade çok uzun! (max 200 karakter)"
        for forbidden in ['import','exec','eval','open','os','sys','__','compile']:
            if forbidden in ifade_clean.lower():
                return "❌ Geçersiz ifade!"
        tree = ast.parse(ifade_clean, mode='eval')
        for node in ast.walk(tree):
            if not isinstance(node, (
                ast.Expression,ast.BinOp,ast.UnaryOp,
                ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,
                ast.Mod,ast.Pow,ast.USub,ast.UAdd,ast.Constant,
                ast.Call,ast.Name,ast.Load,ast.Attribute
            )):
                return "❌ Geçersiz ifade! Sadece matematik işlemleri desteklenir."
        safe_funcs = {
            'sin':math.sin,'cos':math.cos,'tan':math.tan,
            'asin':math.asin,'acos':math.acos,'atan':math.atan,
            'sqrt':math.sqrt,'abs':abs,'log':math.log,
            'log2':math.log2,'log10':math.log10,'pi':math.pi,'e':math.e,
            'round':round,'floor':math.floor,'ceil':math.ceil,
            'pow':pow,'factorial':math.factorial,
        }
        sonuc = eval(compile(tree,'<expr>','eval'), {"__builtins__": {}}, safe_funcs)
        if isinstance(sonuc, float):
            if math.isnan(sonuc): return "❌ Tanımsız sonuç (NaN)"
            if math.isinf(sonuc): return "❌ Sonsuz sonuç (∞)"
            sonuc_str = f"{sonuc:.10g}"
        else:
            sonuc_str = str(sonuc)
        return (
            f"🧮 **HESAP MAKİNESİ**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 **İfade:** `{ifade}`\n"
            f"📤 **Sonuç:** `{sonuc_str}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _sin, cos, sqrt, log, pi, e, factorial_"
        )
    except ZeroDivisionError:
        return "❌ **Sıfıra bölme hatası!**"
    except Exception:
        return "❌ **Geçersiz ifade!** Örnek: `2**10` veya `sqrt(144)` veya `sin(pi/2)`"

def hash_uret(metin: str) -> str:
    if not metin.strip(): return "❌ Metin boş olamaz!"
    if len(metin) > 5000: return "❌ Metin çok uzun (max 5000 karakter)"
    veri = metin.encode('utf-8')
    ozet = metin[:40] + ('...' if len(metin) > 40 else '')
    return (
        f"🔐 **HASH ÜRETİCİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 **Metin:** `{ozet}`\n"
        f"📊 **Uzunluk:** `{len(metin)} karakter`\n\n"
        f"🔸 **MD5:**\n`{hashlib.md5(veri).hexdigest()}`\n\n"
        f"🔸 **SHA-1:**\n`{hashlib.sha1(veri).hexdigest()}`\n\n"
        f"🔸 **SHA-256:**\n`{hashlib.sha256(veri).hexdigest()}`\n\n"
        f"🔸 **SHA-512:**\n`{hashlib.sha512(veri).hexdigest()}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n🤖 _AZRxGUARD Hash Engine_"
    )

def base64_islem(metin: str) -> str:
    metin = metin.strip()
    parts = metin.split(None, 1)
    if len(parts) < 2:
        return "❌ **Format:** `encode metin` veya `decode bWV0aW4=`"
    mod, icerik = parts[0].lower(), parts[1]
    try:
        if mod in ('encode','enc','e'):
            sonuc = b64lib.b64encode(icerik.encode('utf-8')).decode('ascii')
            return f"🔒 **BASE64 ENCODE**\n━━━━━━━━━━━━━━━━━━━━━━\n\n📥 **Giriş:** `{icerik[:100]}`\n\n📤 **Sonuç:**\n`{sonuc}`"
        elif mod in ('decode','dec','d'):
            pad = 4 - len(icerik) % 4
            if pad != 4: icerik += '=' * pad
            sonuc = b64lib.b64decode(icerik).decode('utf-8', errors='replace')
            return f"🔓 **BASE64 DECODE**\n━━━━━━━━━━━━━━━━━━━━━━\n\n📥 **Giriş:** `{icerik[:80]}`\n\n📤 **Sonuç:**\n`{sonuc[:500]}`"
        else:
            return "❌ **Format:** `encode metin` veya `decode bWV0aW4=`"
    except Exception as e:
        return f"❌ **Hata:** `{str(e)[:100]}`"

def dunya_saati() -> str:
    sehirler = [
        ("🇬🇪 Tiflis",      datetime.timezone(datetime.timedelta(hours=4))),
        ("🇦🇿 Bakü",        datetime.timezone(datetime.timedelta(hours=4))),
        ("🇹🇷 İstanbul",    datetime.timezone(datetime.timedelta(hours=3))),
        ("🇷🇺 Moskova",     datetime.timezone(datetime.timedelta(hours=3))),
        ("🇸🇦 Riyad",       datetime.timezone(datetime.timedelta(hours=3))),
        ("🇮🇶 Bağdat",      datetime.timezone(datetime.timedelta(hours=3))),
        ("🇦🇪 Dubai",       datetime.timezone(datetime.timedelta(hours=4))),
        ("🇮🇷 Tahran",      datetime.timezone(datetime.timedelta(hours=3, minutes=30))),
        ("🇵🇰 Karaçi",      datetime.timezone(datetime.timedelta(hours=5))),
        ("🇰🇿 Astana",      datetime.timezone(datetime.timedelta(hours=5))),
        ("🇮🇳 Mumbai",      datetime.timezone(datetime.timedelta(hours=5, minutes=30))),
        ("🇨🇳 Pekin",       datetime.timezone(datetime.timedelta(hours=8))),
        ("🇯🇵 Tokyo",       datetime.timezone(datetime.timedelta(hours=9))),
        ("🇩🇪 Berlin",      datetime.timezone(datetime.timedelta(hours=2))),
        ("🇬🇧 Londra",      datetime.timezone(datetime.timedelta(hours=1))),
        ("🇺🇸 New York",    datetime.timezone(datetime.timedelta(hours=-4))),
        ("🇺🇸 Los Angeles", datetime.timezone(datetime.timedelta(hours=-7))),
        ("🇧🇷 São Paulo",   datetime.timezone(datetime.timedelta(hours=-3))),
    ]
    simdi_utc = datetime.datetime.now(datetime.timezone.utc)
    metin = f"🕐 **DÜNYA SAATİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    metin += f"🌐 **UTC:** `{simdi_utc.strftime('%H:%M')}` — `{simdi_utc.strftime('%d.%m.%Y')}`\n\n"
    for isim, tz in sehirler:
        s = datetime.datetime.now(tz)
        metin += f"{isim}: `{s.strftime('%H:%M')}` _{s.strftime('%d.%m')}_\n"
    metin += f"\n━━━━━━━━━━━━━━━━━━━━━━\n🤖 _AZRxGUARD Zaman Servisi_"
    return metin

def sifre_uret(uzunluk: int = 16, buyuk: bool = True, rakam: bool = True, sembol: bool = True) -> str:
    karakterler = string.ascii_lowercase
    zorunlu = [random.choice(string.ascii_lowercase)]
    if buyuk:
        karakterler += string.ascii_uppercase
        zorunlu.append(random.choice(string.ascii_uppercase))
    if rakam:
        karakterler += string.digits
        zorunlu.append(random.choice(string.digits))
    if sembol:
        sem = '!@#$%^&*()-_=+[]{}|;:,.<>?'
        karakterler += sem
        zorunlu.append(random.choice(sem))
    kalan = [random.choice(karakterler) for _ in range(uzunluk - len(zorunlu))]
    liste = zorunlu + kalan
    random.shuffle(liste)
    return ''.join(liste)

def sahte_kimlik_uret() -> str:
    ad, soyad = random.choice(_TR_ISIMLER)
    sehir = random.choice(_SEHIRLER)
    yas = random.randint(18, 55)
    meslek = random.choice(_MESLEKLER)
    telefon = f"+90{random.randint(500,549)}{random.randint(100,999)}{random.randint(10,99)}{random.randint(10,99)}"
    email_ad = ad.lower().replace('ş','s').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ı','i').replace('ç','c')
    email = f"{email_ad}{random.randint(10,99)}@{'gmail' if random.random()>0.5 else 'hotmail'}.com"
    return (
        f"🎭 **SAHTE KİMLİK**\n\n"
        f"👤 **Ad Soyad:** {ad} {soyad}\n"
        f"🎂 **Yaş:** {yas}\n"
        f"🏙️ **Şehir:** {sehir}\n"
        f"💼 **Meslek:** {meslek}\n"
        f"📞 **Telefon:** `{telefon}`\n"
        f"📧 **E-posta:** `{email}`\n\n"
        f"⚠️ _Bu kimlik tamamen sahte ve rastgele üretilmiştir!_"
    )

def _ipapi_basit_getir(ip: str) -> dict:
    try:
        r = http_requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,"
            f"regionName,city,zip,timezone,isp,org,as,asname,mobile,proxy,hosting,query,lat,lon",
            timeout=8
        )
        return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def ip_basit_rapor(veri: dict, aranan_ip: str) -> str:
    if veri.get("status") != "success":
        return f"❌ **IP sorgulanamadı:** `{veri.get('message','Bilinmeyen hata')}`\n\nGirilen değer: `{aranan_ip}`"
    lat = veri.get('lat', '')
    lon = veri.get('lon', '')
    harita = f"https://maps.google.com/?q={lat},{lon}" if lat and lon else None
    rozetler = []
    if veri.get('proxy'):   rozetler.append("🔴 Proxy/VPN")
    if veri.get('hosting'): rozetler.append("🟠 Hosting/Sunucu")
    if veri.get('mobile'):  rozetler.append("📱 Mobil Hat")
    rozet_str = " · ".join(rozetler) if rozetler else "✅ Temiz (Normal Kullanıcı)"
    return (
        f"🌐 **IP Sorgulama — AZRxGUARD**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 **Sorgulanan IP:** `{veri.get('query', aranan_ip)}`\n\n"
        f"🏳️ **Ülke:** {veri.get('country','—')} ({veri.get('countryCode','—')})\n"
        f"🏙️ **Bölge:** {veri.get('regionName','—')} / {veri.get('city','—')}\n"
        f"📮 **Posta Kodu:** {veri.get('zip','—')}\n"
        f"🕐 **Saat Dilimi:** `{veri.get('timezone','—')}`\n\n"
        f"📍 **Koordinat:** {lat}, {lon}\n"
        + (f"🗺️ **Harita:** [Google Maps]({harita})\n\n" if harita else "\n")
        + f"🏢 **ISP:** {veri.get('isp','—')}\n"
        f"🏛️ **Org:** {veri.get('org','—')}\n"
        f"📡 **AS:** {veri.get('as','—')}\n\n"
        f"🛡️ **IP Türü:** {rozet_str}\n\n"
        f"🤖 _AZRxGUARD tarafından sorgulandı_"
    )

PORT_ADLARI = {
    21:'FTP',22:'SSH',23:'Telnet',25:'SMTP',53:'DNS',
    80:'HTTP',110:'POP3',143:'IMAP',443:'HTTPS',445:'SMB',
    1433:'MSSQL',3306:'MySQL',3389:'RDP',5432:'PostgreSQL',
    6379:'Redis',8080:'HTTP-Alt',8443:'HTTPS-Alt',27017:'MongoDB',
}
TARANACAK_PORTLAR = list(PORT_ADLARI.keys())

async def _port_tara(ip: str, port: int, timeout: float = 1.2) -> bool:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=timeout)
        writer.close()
        try: await writer.wait_closed()
        except: pass
        return True
    except:
        return False

async def ip_tam_analiz_yap(ip_adresi: str) -> str:
    def _ipapi_full(ip):
        try:
            r = http_requests.get(
                f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,"
                f"regionName,city,timezone,isp,org,as,asname,mobile,proxy,hosting,query",
                timeout=8
            )
            return r.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    def _proxycheck(ip):
        try:
            r = http_requests.get(f"http://proxycheck.io/v2/{ip}?vpn=1&asn=1&risk=1&seen=1&days=7", timeout=8)
            d = r.json()
            if d.get("status") == "ok" and ip in d:
                return d[ip]
            return {}
        except:
            return {}
    def _ptr(ip):
        try: return _socket.gethostbyaddr(ip)[0]
        except: return "—"

    tasks = [asyncio.to_thread(_ipapi_full, ip_adresi), asyncio.to_thread(_proxycheck, ip_adresi),
             asyncio.to_thread(_ptr, ip_adresi)]
    port_tasks = [_port_tara(ip_adresi, p) for p in TARANACAK_PORTLAR]
    results = await asyncio.gather(*tasks, *port_tasks)
    ipapi, proxycheck, ptr = results[0], results[1], results[2]
    acik_portlar = [TARANACAK_PORTLAR[i] for i, ok in enumerate(results[3:]) if ok]

    if ipapi.get("status") != "success":
        return f"❌ **IP sorgulanamadı:** `{ipapi.get('message','Bilinmeyen hata')}`\n\nIP: `{ip_adresi}`"

    pc_type = str(proxycheck.get('type','')).lower()
    pc_vpn  = str(proxycheck.get('vpn','no')).lower() in ('yes','true','1')
    pc_risk = proxycheck.get('risk', None)
    is_vpn   = pc_vpn or (ipapi.get('proxy',False) and 'datacenter' not in pc_type)
    is_proxy = 'proxy' in pc_type
    is_tor   = 'tor' in pc_type
    hosting  = ipapi.get('hosting', False)

    if pc_risk is not None:
        risk_sayi = int(pc_risk)
    else:
        risk_sayi = 0
        if is_vpn:   risk_sayi += 40
        if is_proxy: risk_sayi += 35
        if is_tor:   risk_sayi += 65
        if hosting:  risk_sayi += 20
        risk_sayi = min(100, risk_sayi)

    risk_str = (f"🔴 %{risk_sayi} Yüksek Risk" if risk_sayi >= 70 else
                f"🟡 %{risk_sayi} Orta Risk"   if risk_sayi >= 40 else
                f"🟢 %{risk_sayi} Düşük Risk")
    dc_uyari = " ⚠️ *[VERİ MERKEZİ]*" if hosting else ""
    port_str = ", ".join([f"{p} ({PORT_ADLARI[p]})" for p in acik_portlar]) if acik_portlar else "Açık port bulunamadı"

    return (
        f"🛡️ **IP Detaylı Güvenlik Analizi**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 **Sorgu:** `{ipapi.get('query', ip_adresi)}`\n\n"
        f"📍 **Konum**\n"
        f"🏳️ **Ülke:** {ipapi.get('country','—')} ({ipapi.get('countryCode','—')})\n"
        f"🏙️ **Bölge:** {ipapi.get('regionName','—')} / {ipapi.get('city','—')}\n"
        f"🕐 **Saat Dilimi:** `{ipapi.get('timezone','—')}`\n\n"
        f"🔌 **Ağ**\n"
        f"🏢 **ISP:** {ipapi.get('isp','—')}\n"
        f"🏛️ **Org:** {ipapi.get('org','—')}\n"
        f"📡 **ASN:** `{ipapi.get('as','—')}`{dc_uyari}\n"
        f"📱 **Mobil:** {'✅ Evet' if ipapi.get('mobile') else '❌ Hayır'}\n"
        f"🏷️ **PTR:** `{ptr}`\n\n"
        f"🕵️ **Gizlilik & Tehdit**\n"
        f"VPN: {'✅' if is_vpn else '❌'} | Proxy: {'✅' if is_proxy else '❌'} | Tor: {'✅' if is_tor else '❌'}\n"
        f"⚠️ **Tehdit Skoru:** {risk_str}\n\n"
        f"🔓 **Açık Portlar:** `{port_str}`\n\n"
        f"🤖 _AZRxGUARD Güvenlik Analizi_"
    )

async def hava_durumu_getir(sehir: str) -> str:
    try:
        sehir_enc = sehir.strip().replace(' ', '+')
        def fetch():
            r = http_requests.get(f"https://wttr.in/{sehir_enc}?format=j1", timeout=10,
                                   headers={"User-Agent": "AZRxGUARD-Bot/2.0"})
            return r.json() if r.status_code == 200 else None
        data = await asyncio.to_thread(fetch)
        if not data or 'current_condition' not in data:
            return f"❌ `{sehir}` için hava durumu bulunamadı!\n💡 Şehri İngilizce yaz: `Istanbul`, `Baku`, `Moscow`"
        c = data['current_condition'][0]
        nearest = data.get('nearest_area', [{}])[0]
        country = nearest.get('country', [{'value': ''}])[0]['value']
        desc = c.get('weatherDesc', [{'value': '—'}])[0]['value']
        dl = desc.lower()
        if any(w in dl for w in ['sunny','clear']): icon = '☀️'
        elif 'partly' in dl: icon = '⛅'
        elif any(w in dl for w in ['overcast','cloud']): icon = '☁️'
        elif any(w in dl for w in ['drizzle','shower']): icon = '🌦️'
        elif 'rain' in dl: icon = '🌧️'
        elif any(w in dl for w in ['snow','blizzard']): icon = '❄️'
        elif any(w in dl for w in ['thunder','storm']): icon = '⛈️'
        elif any(w in dl for w in ['fog','mist','haze']): icon = '🌫️'
        else: icon = '🌤️'
        loc = sehir.strip() + (f", {country}" if country else "")
        return (
            f"{icon} **HAVA DURUMU**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📍 **Konum:** {loc}\n\n"
            f"🌡️ **Sıcaklık:** `{c['temp_C']}°C`\n"
            f"🤔 **Hissedilen:** `{c['FeelsLikeC']}°C`\n"
            f"💧 **Nem:** `%{c['humidity']}`\n"
            f"💨 **Rüzgar:** `{c['windspeedKmph']} km/h`\n"
            f"🌡 **Basınç:** `{c.get('pressure','—')} hPa`\n"
            f"☁️ **Durum:** {desc}\n"
            f"🌞 **UV:** `{c.get('uvIndex','—')}`\n"
            f"👁️ **Görüş:** `{c.get('visibility','—')} km`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n🤖 _AZRxGUARD Hava Servisi_"
        )
    except Exception as e:
        logger.error(f"Hava hatası: {e}")
        return "❌ Hava servisi şu an erişilemiyor. Şehri İngilizce yaz."

async def doviz_cevir(metin: str) -> str:
    try:
        parts = metin.strip().upper().split()
        if len(parts) < 3:
            return "❌ **Format:** `100 USD TRY`\nÖrnek: `50 EUR USD`"
        try:
            miktar = float(parts[0].replace(',','.'))
        except ValueError:
            return "❌ **Geçersiz miktar!**"
        kfrom, kto = parts[1], parts[2]
        def fetch():
            r = http_requests.get(f"https://open.er-api.com/v6/latest/{kfrom}", timeout=10)
            return r.json() if r.status_code == 200 else None
        data = await asyncio.to_thread(fetch)
        if not data or data.get('result') != 'success':
            return f"❌ `{kfrom}` para birimi bulunamadı!\n💡 Örnek: USD, EUR, TRY, GBP, AZN, GEL, RUB, AED..."
        rates = data.get('rates', {})
        sonuc = rates.get(kto)
        if sonuc is None:
            return f"❌ `{kto}` hedef para birimi bulunamadı!"
        tarih = data.get('time_last_update_utc', '—')[:16]
        return (
            f"💱 **DÖVİZ ÇEVİRİCİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 **Giriş:** `{miktar:,.2f} {kfrom}`\n"
            f"📤 **Sonuç:** `{miktar * sonuc:,.4f} {kto}`\n"
            f"📊 **Kur:** `1 {kfrom} = {sonuc:,.4f} {kto}`\n\n"
            f"📅 **Güncelleme:** `{tarih}`\n"
            f"🌐 **Kaynak:** Open Exchange Rates\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n🤖 _AZRxGUARD Döviz Servisi_"
        )
    except Exception as e:
        return "❌ Döviz servisi şu an erişilemiyor. Lütfen sonra tekrar dene."

async def wikipedia_ara(sorgu: str) -> str:
    try:
        def fetch():
            for lang in ['tr', 'en']:
                r = http_requests.get(
                    f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{sorgu.replace(' ','_')}",
                    timeout=10, headers={"User-Agent": "AZRxGUARD-Bot/1.0"}
                )
                if r.status_code == 200:
                    d = r.json()
                    if d.get('type') != 'disambiguation':
                        return d
            return None
        data = await asyncio.to_thread(fetch)
        if not data:
            return f"❌ `{sorgu}` için Wikipedia'da sonuç bulunamadı.\n💡 Farklı kelimeler deneyin."
        ozet = data.get('extract', '—')
        if len(ozet) > 900: ozet = ozet[:900] + '...'
        wiki_url = data.get('content_urls',{}).get('desktop',{}).get('page','')
        return (
            f"🌐 **WIKIPEDIA**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📖 **{data.get('title', sorgu)}**\n\n"
            f"{ozet}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n🔗 [Tam makale]({wiki_url})"
        )
    except:
        return "❌ Wikipedia'ya ulaşılamadı. Lütfen sonra tekrar dene."

async def url_kisalt(url: str) -> str:
    try:
        encoded = urllib.parse.quote(url, safe='')
        r = await asyncio.to_thread(
            lambda: http_requests.get(f"https://tinyurl.com/api-create.php?url={encoded}", timeout=8)
        )
        if r.status_code == 200 and r.text.startswith('http'):
            return r.text.strip()
    except:
        pass
    return url

async def qr_kod_olustur(metin: str) -> bytes | None:
    encoded = urllib.parse.quote(metin, safe='')
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={encoded}&size=400x400&margin=10&format=png"
    def fetch():
        r = http_requests.get(qr_url, timeout=10)
        return r.content if r.status_code == 200 else None
    return await asyncio.to_thread(fetch)

def apk_dosyalari_yukle() -> dict:
    try:
        with open(_APK_DOSYALAR_YOL, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

# ─── Gemini AI ─────────────────────────────────────────────────────────────────
_gemini_chat_history: dict = {}  # user_id -> list of messages

async def gemini_yanit(user_id: int, soru: str) -> str:
    try:
        from google import genai
        from google.genai import types
        gecmis = _gemini_chat_history.get(user_id, [])
        gecmis.append({"role": "user", "parts": [{"text": soru}]})
        if len(gecmis) > 20:
            gecmis = gecmis[-20:]
        def call_api():
            client = genai.Client()
            system_prompt = (
                "Sen AZRxGUARD botunun yapay zeka asistanısın. "
                "Türkçe konuşuyorsun, samimi ve yardımsever bir üslup kullanıyorsun. "
                "Kısa ve net cevaplar ver. Markdown kullanabilirsin."
            )
            contents = []
            for m in gecmis:
                contents.append(types.Content(role=m["role"], parts=[types.Part.from_text(text=m["parts"][0]["text"])]))
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=1024,
                    temperature=0.7,
                )
            )
            return response.text
        yanit = await asyncio.to_thread(call_api)
        if yanit:
            gecmis.append({"role": "model", "parts": [{"text": yanit}]})
            _gemini_chat_history[user_id] = gecmis[-20:]
        return yanit or "❌ AI yanıt üretemedi."
    except Exception as e:
        logger.error(f"Gemini hatası: {e}")
        return f"❌ AI servisi şu an erişilemiyor.\n`{str(e)[:100]}`"

# ══════════════════════════════════════════════════════════════════════════════
# 📦 APK / OBB / CONFİG Views
# ══════════════════════════════════════════════════════════════════════════════
class APKDosyaView(discord.ui.View):
    def __init__(self, uid: str, bilgi: dict, tg_username: str):
        super().__init__(timeout=300)
        self.uid = uid
        self.bilgi = bilgi
        tg_link = f"https://t.me/{tg_username}?start=apk_{uid}"
        self.add_item(discord.ui.Button(label="📥 Telegram'dan İndir", url=tg_link, style=discord.ButtonStyle.link))

    @discord.ui.button(label="⬅️ Listeye Dön", style=discord.ButtonStyle.secondary, row=1)
    async def geri_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        dosyalar = apk_dosyalari_yukle()
        embed, view = apk_liste_embed_view(dosyalar)
        await interaction.response.edit_message(embed=embed, view=view)


class APKSecimButonu(discord.ui.Button):
    def __init__(self, uid: str, bilgi: dict):
        super().__init__(label=f"📦 {bilgi.get('isim','Dosya')[:75]}", style=discord.ButtonStyle.primary, custom_id=f"apk_sec_{uid}")
        self.uid = uid
        self.bilgi = bilgi

    async def callback(self, interaction: discord.Interaction):
        tg_botname = os.environ.get('TG_BOT_USERNAME', 'AzrXguard_bot')
        embed = discord.Embed(title=f"📦 {self.bilgi.get('isim','?')}", description=self.bilgi.get('aciklama','_Açıklama yok_'), color=RENK_YESIL)
        embed.add_field(name="📅 Yükleme Tarihi", value=self.bilgi.get('tarih','—'), inline=True)
        embed.add_field(name="🔗 Kaynak", value="Telegram Kanalı", inline=True)
        embed.set_footer(text="Dosyayı indirmek için Telegram butonuna bas.")
        view = APKDosyaView(uid=self.uid, bilgi=self.bilgi, tg_username=tg_botname)
        await interaction.response.edit_message(embed=embed, view=view)


class APKListeView(discord.ui.View):
    def __init__(self, dosyalar: dict):
        super().__init__(timeout=300)
        for uid, bilgi in list(dosyalar.items())[:24]:
            self.add_item(APKSecimButonu(uid=uid, bilgi=bilgi))

    @discord.ui.button(label="🔄 Yenile", style=discord.ButtonStyle.secondary, row=4)
    async def yenile_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        dosyalar = apk_dosyalari_yukle()
        embed, view = apk_liste_embed_view(dosyalar)
        await interaction.response.edit_message(embed=embed, view=view)


def apk_liste_embed_view(dosyalar: dict):
    if not dosyalar:
        embed = discord.Embed(title="📦 APK-OBB-CONFİG", description="📭 Henüz hiç dosya yüklenmemiş.", color=RENK_KIRMIZI)
        return embed, discord.ui.View()
    embed = discord.Embed(title="📦 APK-OBB-CONFİG", description=f"📁 **{len(dosyalar)} dosya mevcut.** İndirmek istediğin dosyayı seç:", color=RENK_ANA)
    embed.set_footer(text="Dosyalar Telegram kanalından yönetilir • AZRxGUARD")
    return embed, APKListeView(dosyalar)

# ══════════════════════════════════════════════════════════════════════════════
# 📱 TELEFON FİYATLARI Views
# ══════════════════════════════════════════════════════════════════════════════
class TelefonMarkalarView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        markalar = list(TELEFON_VERITABANI.items())
        row = 0
        for i, (kod, info) in enumerate(markalar[:25]):
            if i > 0 and i % 5 == 0:
                row += 1
            btn = discord.ui.Button(
                label=f"{info['emoji']} {info['ad'][:20]}",
                style=discord.ButtonStyle.primary,
                custom_id=f"tel_marka_{kod}",
                row=min(row, 4)
            )
            btn.callback = self._make_callback(kod)
            self.add_item(btn)

    def _make_callback(self, kod: str):
        async def callback(interaction: discord.Interaction):
            info = TELEFON_VERITABANI[kod]
            modeller = info['modeller']
            embed = discord.Embed(
                title=f"{info['emoji']} {info['ad']} — Modeller",
                description=f"📋 **{len(modeller)} model** listeleniyor.\nBir modele tıklayarak Gürcistan fiyatını gör:",
                color=RENK_ANA
            )
            embed.set_footer(text="Fiyatlar Gürcistan piyasasına göredir (₾ GEL) • AZRxGUARD")
            view = TelefonModellerView(kod, modeller[:24])
            await interaction.response.edit_message(embed=embed, view=view)
        return callback


class TelefonModellerView(discord.ui.View):
    def __init__(self, marka_kodu: str, modeller: list):
        super().__init__(timeout=300)
        self.marka_kodu = marka_kodu
        row = 0
        for i, model in enumerate(modeller[:24]):
            if i > 0 and i % 5 == 0:
                row += 1
            btn = discord.ui.Button(
                label=model[:40],
                style=discord.ButtonStyle.secondary,
                custom_id=f"tel_model_{i}",
                row=min(row, 3)
            )
            btn.callback = self._make_callback(model, marka_kodu)
            self.add_item(btn)

        back_btn = discord.ui.Button(label="⬅️ Markalar", style=discord.ButtonStyle.danger, custom_id="tel_geri", row=4)
        back_btn.callback = self._geri_callback
        self.add_item(back_btn)

    def _make_callback(self, model: str, marka_kodu: str):
        async def callback(interaction: discord.Interaction):
            info = TELEFON_VERITABANI.get(marka_kodu, {})
            marka_adi = info.get('ad', marka_kodu)
            tam_isim = f"{marka_adi} {model}"
            fiyat_ge = FIYAT_GE_DB.get(tam_isim) or FIYAT_GE_DB.get(model) or "Fiyat bilgisi mevcut değil"
            embed = discord.Embed(
                title=f"📱 {tam_isim}",
                color=RENK_YESIL
            )
            embed.add_field(name="🇬🇪 Gürcistan (GEL)", value=f"**{fiyat_ge}**", inline=True)
            embed.add_field(name="📊 Kaynak", value="Zoommer.ge / Alta.ge", inline=True)
            embed.set_footer(text="Fiyatlar yaklaşıktır, değişkenlik gösterebilir • AZRxGUARD")
            view = TelefonModellerView(marka_kodu, info.get('modeller', [model])[:24])
            await interaction.response.edit_message(embed=embed, view=view)
        return callback

    async def _geri_callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📱 Telefon Fiyatları", description="Bir marka seç:", color=RENK_ANA)
        embed.set_footer(text="Gürcistan Piyasası • AZRxGUARD")
        await interaction.response.edit_message(embed=embed, view=TelefonMarkalarView())

# ══════════════════════════════════════════════════════════════════════════════
# 🎮 EĞLENCE MENÜSÜ Views
# ══════════════════════════════════════════════════════════════════════════════
class EglenceMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="🎲 Zar At", style=discord.ButtonStyle.primary, row=0)
    async def zar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        sonuc = random.randint(1, 6)
        yuzler = {1:'⚀',2:'⚁',3:'⚂',4:'⚃',5:'⚄',6:'⚅'}
        embed = discord.Embed(
            title="🎲 ZAR ATIŞI",
            description=f"## {yuzler[sonuc]}\n**Sonuç: `{sonuc}`**",
            color=RENK_SARI
        )
        embed.set_footer(text="AZRxGUARD Eğlence • Tekrar atmak için butona bas")
        await interaction.response.edit_message(embed=embed, view=EglenceMenuView())

    @discord.ui.button(label="✊ Taş-Kağıt-Makas", style=discord.ButtonStyle.success, row=0)
    async def tkm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="✊ TAŞ - KAĞIT - MAKAS", description="Seçimini yap:", color=RENK_YESIL)
        await interaction.response.edit_message(embed=embed, view=TKMView())

    @discord.ui.button(label="🔢 Sayı Tahmin", style=discord.ButtonStyle.danger, row=0)
    async def sayi_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        hedef = random.randint(1, 100)
        _oyun_state[interaction.user.id] = {'hedef': hedef, 'denemeler': 0}
        embed = discord.Embed(
            title="🔢 SAYI TAHMİN OYUNU",
            description="1-100 arasında bir sayı tuttum!\n\n`/tahmin <sayı>` komutuyla tahmin et.\n\n💡 10 hakkın var!",
            color=RENK_MAVI
        )
        await interaction.response.edit_message(embed=embed, view=EglenceMenuView())

    @discord.ui.button(label="🪙 Para At", style=discord.ButtonStyle.secondary, row=1)
    async def para_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        sonuc = random.choice([("🟡 YAZI", 0xFEE75C), ("🔵 TURA", 0x3498DB)])
        embed = discord.Embed(title="🪙 PARA ATIŞI", description=f"## {sonuc[0]}", color=sonuc[1])
        await interaction.response.edit_message(embed=embed, view=EglenceMenuView())

    @discord.ui.button(label="🎯 Rus Ruleti", style=discord.ButtonStyle.danger, row=1)
    async def rulet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if random.randint(1, 6) == 1:
            desc = "## 💥 BANG!\n*Şanssızdın...*"
            color = RENK_KIRMIZI
        else:
            desc = "## 😮‍💨 KLIK!\n*Bu sefer şanslısın!*"
            color = RENK_YESIL
        embed = discord.Embed(title="🎯 RUS RULETİ", description=desc, color=color)
        await interaction.response.edit_message(embed=embed, view=EglenceMenuView())

    @discord.ui.button(label="🔮 Kehanet", style=discord.ButtonStyle.secondary, row=1)
    async def kehanet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        kehanetler = [
            "✨ Büyük bir fırsat kapıda seni bekliyor!",
            "⚠️ Bugün önemli kararlar almaktan kaçın.",
            "💫 Eski bir arkadaşından haber alacaksın.",
            "🌟 Başarı çok yakın, vazgeçme!",
            "🌊 Değişim rüzgarları esiyor, hazır ol.",
            "🍀 Şans bugün seninle — bir şans dene!",
            "🔮 Gizem içinde bir cevap yatıyor.",
            "💡 Aklındaki fikir düşündüğünden daha değerli.",
            "🌙 Geceleri daha çok çalışman gerekiyor.",
            "☀️ Sabah güzel haberler gelecek.",
        ]
        embed = discord.Embed(title="🔮 KEHANET", description=random.choice(kehanetler), color=0x9B59B6)
        await interaction.response.edit_message(embed=embed, view=EglenceMenuView())


class TKMView(discord.ui.View):
    SECENEKLER = {"✊ Taş": "tas", "📄 Kağıt": "kagit", "✂️ Makas": "makas"}
    KAZANAN = {"tas": "makas", "makas": "kagit", "kagit": "tas"}
    EMOJIS = {"tas": "✊", "kagit": "📄", "makas": "✂️"}

    def __init__(self):
        super().__init__(timeout=60)
        for label, val in self.SECENEKLER.items():
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id=f"tkm_{val}")
            btn.callback = self._make_callback(val)
            self.add_item(btn)
        back = discord.ui.Button(label="⬅️ Geri", style=discord.ButtonStyle.secondary, custom_id="tkm_geri")
        back.callback = self._geri
        self.add_item(back)

    def _make_callback(self, secim: str):
        async def callback(interaction: discord.Interaction):
            bot_secim = random.choice(list(self.KAZANAN.keys()))
            user_emoji = self.EMOJIS[secim]
            bot_emoji = self.EMOJIS[bot_secim]
            if secim == bot_secim:
                sonuc = "🟡 **Berabere!**"
                color = RENK_SARI
            elif self.KAZANAN[secim] == bot_secim:
                sonuc = "🟢 **Sen kazandın!**"
                color = RENK_YESIL
            else:
                sonuc = "🔴 **Bot kazandı!**"
                color = RENK_KIRMIZI
            embed = discord.Embed(title="✊ TAŞ - KAĞIT - MAKAS", color=color)
            embed.add_field(name="Senin Seçimin", value=f"{user_emoji} {secim.title()}", inline=True)
            embed.add_field(name="Botun Seçimi", value=f"{bot_emoji} {bot_secim.title()}", inline=True)
            embed.add_field(name="Sonuç", value=sonuc, inline=False)
            await interaction.response.edit_message(embed=embed, view=TKMView())
        return callback

    async def _geri(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎮 EĞLENCE MENÜSÜ", description="Ne oynamak istiyorsun?", color=RENK_ANA)
        await interaction.response.edit_message(embed=embed, view=EglenceMenuView())

# ══════════════════════════════════════════════════════════════════════════════
# Discord istemcisi
# ══════════════════════════════════════════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

discord_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(discord_client)


@discord_client.event
async def on_ready():
    await tree.sync()
    logger.info(f"Discord botu hazır → {discord_client.user} (ID: {discord_client.user.id})")
    print(f"✅ Discord botu hazır: {discord_client.user}")


@discord_client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if discord_client.user in message.mentions and message.content:
        soru = re.sub(r'<@!?\d+>', '', message.content).strip()
        if not soru:
            soru = "Merhaba! Nasılsın?"
        async with message.channel.typing():
            yanit = await gemini_yanit(message.author.id, soru)
        embed = discord.Embed(description=yanit[:4000], color=RENK_MAVI)
        embed.set_author(name=f"🤖 AI — {message.author.display_name} için", icon_url=str(message.author.display_avatar.url))
        embed.set_footer(text="AZRxGUARD AI • Gemini 2.0 Flash")
        await message.reply(embed=embed)

# ══════════════════════════════════════════════════════════════════════════════
# 📌 SLASH KOMUTLARI
# ══════════════════════════════════════════════════════════════════════════════

# ── /apk ──────────────────────────────────────────────────────────────────────
@tree.command(name="apk", description="📦 APK-OBB-CONFİG dosya listesini göster")
async def apk_komutu(interaction: discord.Interaction):
    dosyalar = apk_dosyalari_yukle()
    embed, view = apk_liste_embed_view(dosyalar)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ── /bilgi ────────────────────────────────────────────────────────────────────
@tree.command(name="bilgi", description="ℹ️ AZRxGUARD Discord botu hakkında")
async def bilgi_komutu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ AZRxGUARD — Discord Şubesi",
        description=(
            "Telegram tabanlı **AZRxGUARD** sisteminin Discord uzantısı.\n\n"
            "**🛠️ Komutlar:**\n"
            "`/apk` 📦 APK-OBB-CONFİG dosyaları\n"
            "`/telefon` 📱 Telefon fiyatları\n"
            "`/ip` 🌐 IP sorgulama\n"
            "`/ip_analiz` 🛡️ Derin IP güvenlik analizi\n"
            "`/hesap` 🧮 Hesap makinesi\n"
            "`/hash` 🔐 Hash üretici\n"
            "`/hava` 🌦️ Hava durumu\n"
            "`/kur` 💱 Döviz çevirici\n"
            "`/saat` 🕐 Dünya saatleri\n"
            "`/b64` 🔒 Base64 encode/decode\n"
            "`/renk` 🎨 Renk dönüştürücü\n"
            "`/metin` 📊 Metin analizi\n"
            "`/rastgele` 🎲 Rastgele araçlar\n"
            "`/sifrele` 🔠 Şifreleme araçları\n"
            "`/bmi` 💪 BMI hesaplayıcı\n"
            "`/yuzde` 💯 Yüzde hesaplayıcı\n"
            "`/sifre` 🔑 Şifre üretici\n"
            "`/ping` 🏓 Bot gecikmesi\n"
            "`/id` 🆔 ID bilgisi\n"
            "`/kimlik` 🎭 Sahte kimlik üret\n"
            "`/qr` 📱 QR kod oluştur\n"
            "`/kisalt` 🔗 URL kısalt\n"
            "`/wiki` 🌐 Wikipedia ara\n"
            "`/ai` 🤖 Yapay zeka sohbet\n"
            "`/temizle` 🗑️ Mesaj temizle\n"
            "`/ban` `/kick` `/mute` 🛡️ Moderasyon\n"
            "`/eglence` 🎮 Oyun ve eğlence menüsü\n"
        ),
        color=RENK_ANA
    )
    embed.set_footer(text="𝑴𝑨𝑫𝑬 𝑩𝒀 ➣ M̶A̶Q̶A̶💎 | 𝑶𝑾𝑵𝑬𝑹 • azrXmaqa")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ── /ping ─────────────────────────────────────────────────────────────────────
@tree.command(name="ping", description="🏓 Bot gecikme süresini ölç")
async def ping_komutu(interaction: discord.Interaction):
    latency = round(discord_client.latency * 1000)
    if latency < 100:    durum = "🟢 Mükemmel"
    elif latency < 200:  durum = "🟡 İyi"
    elif latency < 400:  durum = "🟠 Orta"
    else:                durum = "🔴 Zayıf"
    embed = discord.Embed(title="🏓 PONG!", color=RENK_YESIL)
    embed.add_field(name="⚡ Gecikme", value=f"`{latency} ms`", inline=True)
    embed.add_field(name="📶 Durum", value=durum, inline=True)
    embed.add_field(name="🕐 Saat (TR)", value=f"`{datetime.datetime.now(TR_SAAT).strftime('%H:%M:%S')}`", inline=True)
    embed.set_footer(text="AZRxGUARD 2.0")
    await interaction.response.send_message(embed=embed)

# ── /id ───────────────────────────────────────────────────────────────────────
@tree.command(name="id", description="🆔 Kullanıcı ve sunucu ID bilgisi")
@app_commands.describe(kullanici="ID'sini görmek istediğin kullanıcı (opsiyonel)")
async def id_komutu(interaction: discord.Interaction, kullanici: discord.Member = None):
    hedef = kullanici or interaction.user
    embed = discord.Embed(title="🆔 ID BİLGİLERİ", color=RENK_ANA)
    embed.add_field(name="👤 Kullanıcı", value=f"`{hedef.id}`", inline=True)
    embed.add_field(name="💬 Kanal", value=f"`{interaction.channel_id}`", inline=True)
    if interaction.guild:
        embed.add_field(name="🏠 Sunucu", value=f"`{interaction.guild.id}`", inline=True)
        embed.add_field(name="Sunucu Adı", value=interaction.guild.name, inline=True)
    embed.add_field(name="👤 Kullanıcı Adı", value=f"{hedef}", inline=True)
    embed.add_field(name="📅 Hesap Oluşturulma", value=f"<t:{int(hedef.created_at.timestamp())}:D>", inline=True)
    embed.set_thumbnail(url=str(hedef.display_avatar.url))
    await interaction.response.send_message(embed=embed)

# ── /ip ───────────────────────────────────────────────────────────────────────
@tree.command(name="ip", description="🌐 IP adresi hakkında temel bilgi al")
@app_commands.describe(adres="Sorgulanacak IP adresi (örn: 8.8.8.8)")
async def ip_komutu(interaction: discord.Interaction, adres: str):
    if not re.match(r'^[0-9a-fA-F.:]{3,45}$', adres.strip()):
        await interaction.response.send_message("❌ Geçersiz IP formatı. Örnek: `8.8.8.8`", ephemeral=True)
        return
    await interaction.response.defer()
    veri = await asyncio.to_thread(_ipapi_basit_getir, adres.strip())
    rapor = ip_basit_rapor(veri, adres.strip())
    embed = discord.Embed(description=rapor, color=RENK_ANA)
    await interaction.followup.send(embed=embed)

# ── /ip_analiz ────────────────────────────────────────────────────────────────
@tree.command(name="ip_analiz", description="🛡️ IP adresi derin güvenlik analizi (port tarama)")
@app_commands.describe(adres="Analiz edilecek IP adresi")
async def ip_analiz_komutu(interaction: discord.Interaction, adres: str):
    if not re.match(r'^[0-9a-fA-F.:]{3,45}$', adres.strip()):
        await interaction.response.send_message("❌ Geçersiz IP formatı.", ephemeral=True)
        return
    await interaction.response.defer()
    rapor = await ip_tam_analiz_yap(adres.strip())
    embed = discord.Embed(description=rapor[:4000], color=RENK_KIRMIZI)
    embed.set_footer(text="AZRxGUARD Güvenlik Analizi • Proxycheck.io + ip-api.com")
    await interaction.followup.send(embed=embed)

# ── /hesap ────────────────────────────────────────────────────────────────────
@tree.command(name="hesap", description="🧮 Matematik ifadesi hesapla")
@app_commands.describe(ifade="Hesaplanacak ifade (örn: sqrt(144) veya 2**10)")
async def hesap_komutu(interaction: discord.Interaction, ifade: str):
    sonuc = guvenli_hesapla(ifade)
    embed = discord.Embed(description=sonuc, color=RENK_YESIL)
    await interaction.response.send_message(embed=embed)

# ── /hash ─────────────────────────────────────────────────────────────────────
@tree.command(name="hash", description="🔐 Metin için MD5/SHA1/SHA256/SHA512 hash üret")
@app_commands.describe(metin="Hash üretilecek metin")
async def hash_komutu(interaction: discord.Interaction, metin: str):
    sonuc = hash_uret(metin)
    embed = discord.Embed(description=sonuc, color=RENK_TURUNCU)
    await interaction.response.send_message(embed=embed)

# ── /hava ─────────────────────────────────────────────────────────────────────
@tree.command(name="hava", description="🌦️ Hava durumu sorgula")
@app_commands.describe(sehir="Şehir adı (İngilizce: Istanbul, Baku, Moscow)")
async def hava_komutu(interaction: discord.Interaction, sehir: str):
    await interaction.response.defer()
    sonuc = await hava_durumu_getir(sehir)
    embed = discord.Embed(description=sonuc, color=RENK_MAVI)
    await interaction.followup.send(embed=embed)

# ── /kur ──────────────────────────────────────────────────────────────────────
@tree.command(name="kur", description="💱 Döviz çevirici")
@app_commands.describe(islem="Örnek: 100 USD TRY  veya  50 EUR GEL")
async def kur_komutu(interaction: discord.Interaction, islem: str):
    await interaction.response.defer()
    sonuc = await doviz_cevir(islem)
    embed = discord.Embed(description=sonuc, color=RENK_YESIL)
    await interaction.followup.send(embed=embed)

# ── /saat ─────────────────────────────────────────────────────────────────────
@tree.command(name="saat", description="🕐 Dünya saatlerini göster")
async def saat_komutu(interaction: discord.Interaction):
    embed = discord.Embed(description=dunya_saati(), color=RENK_ANA)
    await interaction.response.send_message(embed=embed)

# ── /b64 ──────────────────────────────────────────────────────────────────────
@tree.command(name="b64", description="🔒 Base64 encode/decode")
@app_commands.describe(islem="encode veya decode, sonra metin. Örnek: encode Merhaba")
async def b64_komutu(interaction: discord.Interaction, islem: str):
    sonuc = base64_islem(islem)
    embed = discord.Embed(description=sonuc, color=RENK_TURUNCU)
    await interaction.response.send_message(embed=embed)

# ── /renk ─────────────────────────────────────────────────────────────────────
@tree.command(name="renk", description="🎨 HEX ya da RGB renk analizi")
@app_commands.describe(deger="HEX kodu (#FF5733) veya RGB değerleri (255 87 51)")
async def renk_komutu(interaction: discord.Interaction, deger: str):
    girdi = deger.strip()
    r = g = b = None
    hex_str = None
    args = girdi.split()
    if girdi.startswith('#') or (len(girdi.lstrip('#')) in (3,6) and all(c in '0123456789abcdefABCDEF' for c in girdi.lstrip('#'))):
        res = _hex_to_rgb(girdi)
        if res:
            r, g, b = res
            h_raw = girdi.lstrip('#').upper()
            hex_str = ''.join(c*2 for c in h_raw) if len(h_raw) == 3 else h_raw
    elif len(args) == 3:
        try:
            r, g, b = int(args[0]), int(args[1]), int(args[2])
            if not all(0 <= x <= 255 for x in (r,g,b)): raise ValueError
            hex_str = f"{r:02X}{g:02X}{b:02X}"
        except ValueError:
            await interaction.response.send_message("❌ RGB değerleri 0-255 arasında olmalı!", ephemeral=True); return
    if r is None:
        await interaction.response.send_message("❌ Geçersiz format! Örnek: `#FF5733` veya `255 87 51`", ephemeral=True); return
    h, s, lv = _rgb_to_hsl(r, g, b)
    if   r>180 and g<100 and b<100: ton = "🔴 Kırmızı tonu"
    elif r<100 and g>150 and b<100: ton = "🟢 Yeşil tonu"
    elif r<100 and g<100 and b>150: ton = "🔵 Mavi tonu"
    elif r>200 and g>200 and b<80:  ton = "🟡 Sarı tonu"
    elif r>200 and g>100 and b<80:  ton = "🟠 Turuncu tonu"
    elif r>100 and g<80  and b>150: ton = "🟣 Mor tonu"
    elif r>200 and g>200 and b>200: ton = "⬜ Beyaz / Açık"
    elif r<60  and g<60  and b<60:  ton = "⬛ Siyah / Koyu"
    else: ton = "🎨 Karma renk"
    embed = discord.Embed(
        title="🎨 RENK ANALİZİ",
        color=int(hex_str, 16)
    )
    embed.add_field(name="🔷 HEX",       value=f"`#{hex_str}`",         inline=True)
    embed.add_field(name="🔴🟢🔵 RGB",  value=f"`rgb({r}, {g}, {b})`", inline=True)
    embed.add_field(name="🌈 HSL",       value=f"`hsl({h}°, {s}%, {lv}%)`", inline=True)
    embed.add_field(name="🎯 Renk Tonu", value=ton,                      inline=False)
    embed.set_footer(text="AZRxGUARD 2.0 Renk Motoru")
    await interaction.response.send_message(embed=embed)

# ── /metin ────────────────────────────────────────────────────────────────────
@tree.command(name="metin", description="📊 Metin analizi yap")
@app_commands.describe(metin="Analiz edilecek metin")
async def metin_komutu(interaction: discord.Interaction, metin: str):
    kelimeler = metin.split()
    satirlar  = metin.splitlines()
    karakter  = len(metin)
    bosluksuz = len(metin.replace(' ','').replace('\n',''))
    kelime_sayi = len(kelimeler)
    freq = {}
    for k in kelimeler:
        k2 = k.lower().strip('.,!?;:()[]{}"\'-')
        if len(k2) > 2: freq[k2] = freq.get(k2,0) + 1
    en_sik = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
    en_sik_str = '\n'.join(f"  `{k}` → {v}x" for k,v in en_sik) if en_sik else "  —"
    ort_uzunluk = sum(len(k) for k in kelimeler) / max(kelime_sayi, 1)
    okuma_sn = (kelime_sayi / 200) * 60
    okuma_str = f"{int(okuma_sn)} saniye" if okuma_sn < 60 else f"{okuma_sn/60:.1f} dakika"
    embed = discord.Embed(title="📊 METİN ANALİZİ", color=RENK_MAVI)
    embed.add_field(name="🔤 Karakter",         value=f"`{karakter}` (boşluksuz: `{bosluksuz}`)", inline=False)
    embed.add_field(name="📝 Kelime",            value=f"`{kelime_sayi}`", inline=True)
    embed.add_field(name="📄 Satır",             value=f"`{len(satirlar)}`", inline=True)
    embed.add_field(name="📏 Ort. Kelime Uzunl.",value=f"`{ort_uzunluk:.1f}`", inline=True)
    embed.add_field(name="⏱️ Tahmini Okuma",     value=f"`{okuma_str}`", inline=True)
    embed.add_field(name="🔝 En Sık Kelimeler",  value=en_sik_str, inline=False)
    embed.set_footer(text="AZRxGUARD 2.0 Metin Motoru")
    await interaction.response.send_message(embed=embed)

# ── /rastgele ─────────────────────────────────────────────────────────────────
@tree.command(name="rastgele", description="🎲 Rastgele araçlar (sayi/zar/para/sec)")
@app_commands.describe(mod="sayi / zar / para / sec", parametre="Ek parametre (sayi: 1 100 | zar: 2 6 | sec: elma muz)")
async def rastgele_komutu(interaction: discord.Interaction, mod: str, parametre: str = ""):
    mod = mod.lower()
    args = parametre.split()
    if mod in ('sayi','sayı','number'):
        try:
            alt = int(args[0]) if len(args) > 0 else 1
            ust = int(args[1]) if len(args) > 1 else 100
            if alt >= ust: raise ValueError
            sonuc = random.randint(alt, ust)
            embed = discord.Embed(title="🎲 RASTGELE SAYI", color=RENK_SARI)
            embed.add_field(name="🔢 Aralık", value=f"`{alt}` — `{ust}`", inline=True)
            embed.add_field(name="🎯 Sonuç",  value=f"**`{sonuc}`**",     inline=True)
        except ValueError:
            await interaction.response.send_message("❌ Kullanım: `/rastgele sayi 1 100`", ephemeral=True); return
    elif mod in ('zar','dice'):
        try:
            adet = min(int(args[0]) if args else 1, 20)
            yuze = min(int(args[1]) if len(args) > 1 else 6, 1000)
            if adet < 1 or yuze < 2: raise ValueError
            atislar = [random.randint(1, yuze) for _ in range(adet)]
            embed = discord.Embed(title=f"🎲 ZAR ATIŞI — {adet}d{yuze}", color=RENK_SARI)
            embed.add_field(name="📊 Sonuçlar", value=' + '.join(f'`{a}`' for a in atislar), inline=False)
            embed.add_field(name="✨ Toplam", value=f"**`{sum(atislar)}`**", inline=True)
        except ValueError:
            await interaction.response.send_message("❌ Kullanım: `/rastgele zar 2 6`", ephemeral=True); return
    elif mod in ('para','coin'):
        sonuc = random.choice([("🟡 YAZI", RENK_SARI), ("🔵 TURA", RENK_MAVI)])
        embed = discord.Embed(title="🪙 PARA ATIŞI", description=f"## {sonuc[0]}", color=sonuc[1])
    elif mod in ('sec','seç','pick'):
        if len(args) < 2:
            await interaction.response.send_message("❌ En az 2 seçenek gir! Örnek: `/rastgele sec elma muz çilek`", ephemeral=True); return
        secilen = random.choice(args)
        embed = discord.Embed(title="🎯 RASTGELE SEÇİM", color=RENK_YESIL)
        embed.add_field(name="📋 Seçenekler", value=' · '.join(f'`{s}`' for s in args), inline=False)
        embed.add_field(name="✨ Seçilen",    value=f"**`{secilen}`**", inline=True)
    else:
        embed = discord.Embed(
            title="🎲 RASTGELE ARAÇLAR",
            description=(
                "`/rastgele sayi 1 100` — Sayı üret\n"
                "`/rastgele zar` — 1d6 zar at\n"
                "`/rastgele zar 2 20` — 2×d20 zar\n"
                "`/rastgele para` — Yazı / Tura\n"
                "`/rastgele sec elma muz çilek` — Listeden seç"
            ),
            color=RENK_ANA
        )
    await interaction.response.send_message(embed=embed)

# ── /sifrele ──────────────────────────────────────────────────────────────────
@tree.command(name="sifrele", description="🔠 Şifreleme araçları (caesar/rot13/ters/morse)")
@app_commands.describe(mod="caesar / rot13 / ters / morse", metin="Şifrelenecek metin")
async def sifrele_komutu(interaction: discord.Interaction, mod: str, metin: str):
    mod = mod.lower()
    if mod == 'caesar':
        parts = metin.split(None, 1)
        try:
            n = int(parts[0])
            txt = parts[1] if len(parts) > 1 else ''
            if not txt: raise ValueError
        except (ValueError, IndexError):
            await interaction.response.send_message("❌ Kullanım: `/sifrele caesar 13 Merhaba`\n(önce kaydırma sayısı, sonra metin)", ephemeral=True); return
        embed = discord.Embed(title="🔠 CAESAR ŞİFRE", color=RENK_TURUNCU)
        embed.add_field(name="📥 Giriş",      value=f"`{txt}`",             inline=False)
        embed.add_field(name="🔢 Kaydırma",   value=f"`{n}`",               inline=True)
        embed.add_field(name="🔒 Şifreli",    value=f"`{_caesar(txt, n)}`", inline=False)
        embed.add_field(name=f"🔓 Çözülmüş (-{n})", value=f"`{_caesar(txt, -n)}`", inline=False)
    elif mod == 'rot13':
        embed = discord.Embed(title="🔄 ROT-13", color=RENK_TURUNCU)
        embed.add_field(name="📥 Giriş",   value=f"`{metin}`",              inline=False)
        embed.add_field(name="📤 ROT-13",  value=f"`{_caesar(metin, 13)}`", inline=False)
        embed.set_footer(text="Tekrar aynı komutla geri alınır")
    elif mod == 'ters':
        embed = discord.Embed(title="🔃 METİN TERSİ", color=RENK_TURUNCU)
        embed.add_field(name="📥 Giriş", value=f"`{metin}`",         inline=False)
        embed.add_field(name="📤 Ters",  value=f"`{metin[::-1]}`",   inline=False)
    elif mod == 'morse':
        morse = ' '.join(_MORSE.get(c.upper(), '?') for c in metin.upper())
        embed = discord.Embed(title="📡 MORSE KODU", color=RENK_TURUNCU)
        embed.add_field(name="📥 Giriş",   value=f"`{metin.upper()}`", inline=False)
        embed.add_field(name="📤 Morse",   value=f"`{morse[:1000]}`",  inline=False)
    else:
        await interaction.response.send_message(
            "❌ Geçersiz mod!\n`caesar` / `rot13` / `ters` / `morse`", ephemeral=True); return
    await interaction.response.send_message(embed=embed)

# ── /bmi ──────────────────────────────────────────────────────────────────────
@tree.command(name="bmi", description="💪 BMI (Vücut Kitle İndeksi) hesapla")
@app_commands.describe(boy="Boy (cm, örn: 175)", kilo="Kilo (kg, örn: 70)")
async def bmi_komutu(interaction: discord.Interaction, boy: float, kilo: float):
    if not (50 <= boy <= 300 and 10 <= kilo <= 500):
        await interaction.response.send_message("❌ Geçersiz değer! Boy: 50-300 cm, Kilo: 10-500 kg", ephemeral=True); return
    boy_m = boy / 100
    bmi = kilo / (boy_m ** 2)
    if   bmi < 18.5: durum = "🔵 Zayıf";      tavsiye = "Daha fazla kalori ve güç antrenmanı önerilir."; color = RENK_MAVI
    elif bmi < 25:   durum = "🟢 Normal";      tavsiye = "Mevcut yaşam tarzını sürdür. Harika!";          color = RENK_YESIL
    elif bmi < 30:   durum = "🟡 Fazla Kilolu";tavsiye = "Hafif egzersiz ve dengeli beslenme önerilir.";  color = RENK_SARI
    elif bmi < 35:   durum = "🟠 Obez I";      tavsiye = "Düzenli egzersiz ve diyet programı önerilir.";  color = RENK_TURUNCU
    else:            durum = "🔴 Obez II+";    tavsiye = "Bir sağlık uzmanıyla görüşmeniz önerilir.";     color = RENK_KIRMIZI
    embed = discord.Embed(title="💪 BMI ANALİZİ", color=color)
    embed.add_field(name="📏 Boy",   value=f"`{boy} cm`",  inline=True)
    embed.add_field(name="⚖️ Kilo",  value=f"`{kilo} kg`", inline=True)
    embed.add_field(name="📊 BMI",   value=f"**`{bmi:.1f}`**", inline=True)
    embed.add_field(name="🏷️ Durum", value=durum, inline=True)
    embed.add_field(name="💡 Tavsiye", value=f"_{tavsiye}_", inline=False)
    ideal_alt = 18.5 * (boy_m ** 2)
    ideal_ust = 24.9 * (boy_m ** 2)
    embed.add_field(name="🎯 İdeal Kilo Aralığı", value=f"`{ideal_alt:.1f} — {ideal_ust:.1f} kg`", inline=False)
    embed.set_footer(text="⚠️ Yalnızca bilgilendirme amaçlıdır. • AZRxGUARD")
    await interaction.response.send_message(embed=embed)

# ── /yuzde ────────────────────────────────────────────────────────────────────
@tree.command(name="yuzde", description="💯 Yüzde hesaplayıcı")
@app_commands.describe(islem="Örnekler: '20% 500' | '75 150' | 'artis 200 250' | 'azalis 300 240'")
async def yuzde_komutu(interaction: discord.Interaction, islem: str):
    try:
        parts = islem.strip().split()
        mod = parts[0].lower()
        if mod in ('artis','artış'):
            a, b = float(parts[1]), float(parts[2])
            oran = ((b - a) / a) * 100
            emoji = "📈" if oran >= 0 else "📉"
            embed = discord.Embed(title="💯 YÜZDE DEĞİŞİM", color=RENK_YESIL if oran >= 0 else RENK_KIRMIZI)
            embed.add_field(name="🔢 Değişim", value=f"`{a}` → `{b}`", inline=True)
            embed.add_field(name=f"{emoji} Artış", value=f"**`{oran:+.2f}%`**", inline=True)
        elif mod in ('azalis','azalış'):
            a, b = float(parts[1]), float(parts[2])
            oran = ((a - b) / a) * 100
            embed = discord.Embed(title="💯 YÜZDE DEĞİŞİM", color=RENK_KIRMIZI)
            embed.add_field(name="🔢 Değişim", value=f"`{a}` → `{b}`", inline=True)
            embed.add_field(name="📉 Azalış", value=f"**`{oran:.2f}%`**", inline=True)
        elif '%' in mod:
            yv = float(mod.replace('%',''))
            sayi = float(parts[1])
            sonuc = (yv / 100) * sayi
            embed = discord.Embed(title="💯 YÜZDE HESABI", color=RENK_SARI)
            embed.add_field(name="Hesap", value=f"`{sayi}`'nin `%{yv}`'i = **`{sonuc:.4g}`**", inline=False)
        else:
            parca, toplam = float(parts[0]), float(parts[1])
            oran = (parca / toplam) * 100
            embed = discord.Embed(title="💯 YÜZDE HESABI", color=RENK_SARI)
            embed.add_field(name="Hesap", value=f"`{parca}`, `{toplam}`'nin → **`%{oran:.2f}`**", inline=False)
        embed.set_footer(text="AZRxGUARD 2.0")
        await interaction.response.send_message(embed=embed)
    except (ValueError, IndexError, ZeroDivisionError):
        await interaction.response.send_message(
            "❌ Geçersiz format!\n"
            "Örnekler: `/yuzde 20% 500`  |  `/yuzde 75 150`  |  `/yuzde artis 200 250`",
            ephemeral=True
        )

# ── /sifre ────────────────────────────────────────────────────────────────────
@tree.command(name="sifre", description="🔑 Güvenli rastgele şifre üret")
@app_commands.describe(uzunluk="Şifre uzunluğu (8-64, varsayılan: 16)")
async def sifre_komutu(interaction: discord.Interaction, uzunluk: int = 16):
    if not 8 <= uzunluk <= 64:
        await interaction.response.send_message("❌ Uzunluk 8-64 arasında olmalı!", ephemeral=True); return
    sifre = sifre_uret(uzunluk)
    embed = discord.Embed(title="🔑 ŞİFRE ÜRETİCİ", color=RENK_YESIL)
    embed.add_field(name="🔐 Üretilen Şifre", value=f"||`{sifre}`||", inline=False)
    embed.add_field(name="📏 Uzunluk", value=f"`{uzunluk} karakter`", inline=True)
    embed.add_field(name="💪 İçerik",  value="Büyük/küçük harf + rakam + sembol", inline=True)
    embed.set_footer(text="⚠️ Bu şifreyi güvenli bir yere kaydet! • AZRxGUARD")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ── /kimlik ───────────────────────────────────────────────────────────────────
@tree.command(name="kimlik", description="🎭 Sahte (rastgele) kimlik üret")
async def kimlik_komutu(interaction: discord.Interaction):
    sonuc = sahte_kimlik_uret()
    embed = discord.Embed(description=sonuc, color=0x9B59B6)
    embed.set_footer(text="Tamamen sahte ve rastgele üretilmiştir • AZRxGUARD")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ── /qr ───────────────────────────────────────────────────────────────────────
@tree.command(name="qr", description="📱 Metin veya URL için QR kod oluştur")
@app_commands.describe(metin="QR koda dönüştürülecek metin veya URL")
async def qr_komutu(interaction: discord.Interaction, metin: str):
    await interaction.response.defer()
    data = await qr_kod_olustur(metin)
    if data:
        dosya = discord.File(io.BytesIO(data), filename="qr.png")
        embed = discord.Embed(title="📱 QR KOD", description=f"`{metin[:200]}`", color=RENK_ANA)
        embed.set_image(url="attachment://qr.png")
        embed.set_footer(text="AZRxGUARD QR Servisi")
        await interaction.followup.send(embed=embed, file=dosya)
    else:
        await interaction.followup.send("❌ QR kod oluşturulamadı.", ephemeral=True)

# ── /kisalt ───────────────────────────────────────────────────────────────────
@tree.command(name="kisalt", description="🔗 URL kısalt (TinyURL)")
@app_commands.describe(url="Kısaltılacak URL")
async def kisalt_komutu(interaction: discord.Interaction, url: str):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    await interaction.response.defer()
    kisa = await url_kisalt(url)
    embed = discord.Embed(title="🔗 URL KISALTICI", color=RENK_YESIL)
    embed.add_field(name="🔗 Orijinal", value=url[:200], inline=False)
    embed.add_field(name="✂️ Kısa URL", value=f"**{kisa}**", inline=False)
    embed.set_footer(text="AZRxGUARD • TinyURL")
    await interaction.followup.send(embed=embed)

# ── /wiki ─────────────────────────────────────────────────────────────────────
@tree.command(name="wiki", description="🌐 Wikipedia'dan bilgi ara")
@app_commands.describe(sorgu="Aranacak konu")
async def wiki_komutu(interaction: discord.Interaction, sorgu: str):
    await interaction.response.defer()
    sonuc = await wikipedia_ara(sorgu)
    embed = discord.Embed(description=sonuc[:4000], color=RENK_MAVI)
    await interaction.followup.send(embed=embed)

# ── /ai ───────────────────────────────────────────────────────────────────────
@tree.command(name="ai", description="🤖 Yapay zeka ile sohbet et (Gemini)")
@app_commands.describe(soru="AI'ye soracağın soru veya mesaj")
async def ai_komutu(interaction: discord.Interaction, soru: str):
    await interaction.response.defer()
    yanit = await gemini_yanit(interaction.user.id, soru)
    embed = discord.Embed(description=yanit[:4000], color=RENK_MAVI)
    embed.set_author(name=f"🤖 AZRxGUARD AI • Gemini 2.0 Flash")
    embed.set_footer(text=f"Soru: {soru[:100]}")
    await interaction.followup.send(embed=embed)

# ── /ai_sifirla ───────────────────────────────────────────────────────────────
@tree.command(name="ai_sifirla", description="🔄 AI sohbet geçmişini temizle")
async def ai_sifirla_komutu(interaction: discord.Interaction):
    _gemini_chat_history.pop(interaction.user.id, None)
    await interaction.response.send_message("✅ AI sohbet geçmişin temizlendi!", ephemeral=True)

# ── /telefon ──────────────────────────────────────────────────────────────────
@tree.command(name="telefon", description="📱 Telefon fiyatları (Gürcistan piyasası)")
async def telefon_komutu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📱 Telefon Fiyatları — Gürcistan Piyasası",
        description="Bir marka seç:",
        color=RENK_ANA
    )
    embed.set_footer(text="Fiyatlar Zoommer.ge / Alta.ge'ye göredir • AZRxGUARD")
    await interaction.response.send_message(embed=embed, view=TelefonMarkalarView(), ephemeral=True)

# ── /eglence ──────────────────────────────────────────────────────────────────
@tree.command(name="eglence", description="🎮 Eğlence menüsü — Oyunlar ve şans")
async def eglence_komutu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 EĞLENCE MENÜSÜ",
        description=(
            "Bir aktivite seç:\n\n"
            "🎲 **Zar At** — 1d6 zar\n"
            "✊ **Taş-Kağıt-Makas** — Bota karşı oyna\n"
            "🔢 **Sayı Tahmin** — 1-100 arası tahmin et\n"
            "🪙 **Para At** — Yazı mı tura mı?\n"
            "🎯 **Rus Ruleti** — 1/6 ihtimal!\n"
            "🔮 **Kehanet** — Geleceğini öğren"
        ),
        color=RENK_ANA
    )
    await interaction.response.send_message(embed=embed, view=EglenceMenuView())

# ── /tahmin ───────────────────────────────────────────────────────────────────
@tree.command(name="tahmin", description="🔢 Sayı tahmin oyununda tahmin yap")
@app_commands.describe(sayi="Tahmin ettiğin sayı (1-100)")
async def tahmin_komutu(interaction: discord.Interaction, sayi: int):
    uid = interaction.user.id
    if uid not in _oyun_state:
        await interaction.response.send_message("❌ Aktif oyun yok! `/eglence` menüsünden oyunu başlat.", ephemeral=True); return
    state = _oyun_state[uid]
    hedef = state['hedef']
    state['denemeler'] += 1
    denemeler = state['denemeler']
    if sayi == hedef:
        del _oyun_state[uid]
        embed = discord.Embed(title="🎉 DOĞRU!", description=f"**{hedef}** sayısını `{denemeler}` denemede buldun!", color=RENK_YESIL)
    elif denemeler >= 10:
        del _oyun_state[uid]
        embed = discord.Embed(title="💀 OYUN BİTTİ", description=f"10 hakkını bitirdin! Doğru cevap: **{hedef}**", color=RENK_KIRMIZI)
    elif sayi < hedef:
        kalan = 10 - denemeler
        embed = discord.Embed(title="⬆️ DAHA BÜYÜK!", description=f"`{sayi}` küçük. Daha büyük dene!\n\n💡 {kalan} hakkın kaldı.", color=RENK_SARI)
    else:
        kalan = 10 - denemeler
        embed = discord.Embed(title="⬇️ DAHA KÜÇÜK!", description=f"`{sayi}` büyük. Daha küçük dene!\n\n💡 {kalan} hakkın kaldı.", color=RENK_SARI)
    embed.set_footer(text=f"Deneme {denemeler}/10 • AZRxGUARD")
    await interaction.response.send_message(embed=embed)

# ── /temizle ──────────────────────────────────────────────────────────────────
@tree.command(name="temizle", description="🗑️ Kanaldan mesaj sil (Mod yetkisi gerekir)")
@app_commands.describe(adet="Silinecek mesaj sayısı (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def temizle_komutu(interaction: discord.Interaction, adet: int):
    if not 1 <= adet <= 100:
        await interaction.response.send_message("❌ 1-100 arasında bir sayı gir.", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    silindi = await interaction.channel.purge(limit=adet)
    embed = discord.Embed(title="🗑️ MESAJLAR SİLİNDİ", color=RENK_YESIL)
    embed.add_field(name="✅ Silinen", value=f"`{len(silindi)}` mesaj", inline=True)
    embed.add_field(name="👤 Yetkili", value=interaction.user.mention, inline=True)
    await interaction.followup.send(embed=embed, ephemeral=True)

@temizle_komutu.error
async def temizle_hata(interaction: discord.Interaction, error: app_commands.AppCommandError):
    await interaction.response.send_message("❌ Bu komutu kullanmak için **Mesajları Yönet** yetkisi gerekiyor.", ephemeral=True)

# ── /ban ──────────────────────────────────────────────────────────────────────
@tree.command(name="ban", description="🔨 Kullanıcıyı sunucudan banla (Mod yetkisi gerekir)")
@app_commands.describe(kullanici="Banlanacak kullanıcı", sebep="Ban sebebi")
@app_commands.checks.has_permissions(ban_members=True)
async def ban_komutu(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
    if kullanici.id == interaction.user.id:
        await interaction.response.send_message("❌ Kendini banlayamazsın!", ephemeral=True); return
    if kullanici.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Bu kullanıcıyı banlama yetkin yok!", ephemeral=True); return
    try:
        await kullanici.ban(reason=f"{sebep} | Yetkili: {interaction.user}")
        embed = discord.Embed(title="🔨 KULLANICI BANLANDI", color=RENK_KIRMIZI)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici} (`{kullanici.id}`)", inline=True)
        embed.add_field(name="👮 Yetkili",   value=interaction.user.mention, inline=True)
        embed.add_field(name="📋 Sebep",      value=sebep, inline=False)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Yetkim yetersiz!", ephemeral=True)

@ban_komutu.error
async def ban_hata(interaction: discord.Interaction, error: app_commands.AppCommandError):
    await interaction.response.send_message("❌ Bu komutu kullanmak için **Üyeleri Banla** yetkisi gerekiyor.", ephemeral=True)

# ── /unban ────────────────────────────────────────────────────────────────────
@tree.command(name="unban", description="✅ Banlı kullanıcının banını kaldır")
@app_commands.describe(kullanici_id="Banı kaldırılacak kullanıcının ID'si")
@app_commands.checks.has_permissions(ban_members=True)
async def unban_komutu(interaction: discord.Interaction, kullanici_id: str):
    try:
        uid = int(kullanici_id)
        kullanici = await discord_client.fetch_user(uid)
        await interaction.guild.unban(kullanici)
        embed = discord.Embed(title="✅ BAN KALDIRILDI", color=RENK_YESIL)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici} (`{uid}`)", inline=True)
        embed.add_field(name="👮 Yetkili",   value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)
    except (discord.NotFound, discord.Forbidden, ValueError):
        await interaction.response.send_message("❌ Kullanıcı bulunamadı veya yetkim yetersiz.", ephemeral=True)

@unban_komutu.error
async def unban_hata(interaction: discord.Interaction, error: app_commands.AppCommandError):
    await interaction.response.send_message("❌ Bu komutu kullanmak için **Üyeleri Banla** yetkisi gerekiyor.", ephemeral=True)

# ── /kick ─────────────────────────────────────────────────────────────────────
@tree.command(name="kick", description="👢 Kullanıcıyı sunucudan at (Mod yetkisi gerekir)")
@app_commands.describe(kullanici="Atılacak kullanıcı", sebep="Atma sebebi")
@app_commands.checks.has_permissions(kick_members=True)
async def kick_komutu(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
    if kullanici.id == interaction.user.id:
        await interaction.response.send_message("❌ Kendini atamazsın!", ephemeral=True); return
    try:
        await kullanici.kick(reason=f"{sebep} | Yetkili: {interaction.user}")
        embed = discord.Embed(title="👢 KULLANICI ATILDI", color=RENK_TURUNCU)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici} (`{kullanici.id}`)", inline=True)
        embed.add_field(name="👮 Yetkili",   value=interaction.user.mention, inline=True)
        embed.add_field(name="📋 Sebep",      value=sebep, inline=False)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Yetkim yetersiz!", ephemeral=True)

@kick_komutu.error
async def kick_hata(interaction: discord.Interaction, error: app_commands.AppCommandError):
    await interaction.response.send_message("❌ Bu komutu kullanmak için **Üyeleri At** yetkisi gerekiyor.", ephemeral=True)

# ── /mute ─────────────────────────────────────────────────────────────────────
@tree.command(name="mute", description="🔇 Kullanıcıyı sustur (timeout)")
@app_commands.describe(kullanici="Susturulacak kullanıcı", dakika="Süre (dakika, max 40320=28 gün)", sebep="Susturma sebebi")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute_komutu(interaction: discord.Interaction, kullanici: discord.Member, dakika: int = 10, sebep: str = "Sebep belirtilmedi"):
    if not 1 <= dakika <= 40320:
        await interaction.response.send_message("❌ Süre 1-40320 dakika arasında olmalı!", ephemeral=True); return
    sure = datetime.timedelta(minutes=dakika)
    try:
        await kullanici.timeout(sure, reason=f"{sebep} | Yetkili: {interaction.user}")
        embed = discord.Embed(title="🔇 KULLANICI SUSTURULDU", color=RENK_SARI)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici} (`{kullanici.id}`)", inline=True)
        embed.add_field(name="⏱️ Süre",      value=f"`{dakika} dakika`", inline=True)
        embed.add_field(name="👮 Yetkili",   value=interaction.user.mention, inline=True)
        embed.add_field(name="📋 Sebep",      value=sebep, inline=False)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Yetkim yetersiz!", ephemeral=True)

@mute_komutu.error
async def mute_hata(interaction: discord.Interaction, error: app_commands.AppCommandError):
    await interaction.response.send_message("❌ Bu komutu kullanmak için **Üyeleri Yönet** yetkisi gerekiyor.", ephemeral=True)

# ── /unmute ───────────────────────────────────────────────────────────────────
@tree.command(name="unmute", description="🔊 Kullanıcının timeout'unu kaldır")
@app_commands.describe(kullanici="Timeout'u kaldırılacak kullanıcı")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute_komutu(interaction: discord.Interaction, kullanici: discord.Member):
    try:
        await kullanici.timeout(None)
        embed = discord.Embed(title="🔊 SUSTURMA KALDIRILDI", color=RENK_YESIL)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici} (`{kullanici.id}`)", inline=True)
        embed.add_field(name="👮 Yetkili",   value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Yetkim yetersiz!", ephemeral=True)

@unmute_komutu.error
async def unmute_hata(interaction: discord.Interaction, error: app_commands.AppCommandError):
    await interaction.response.send_message("❌ Bu komutu kullanmak için **Üyeleri Yönet** yetkisi gerekiyor.", ephemeral=True)

# ── /sunucu ───────────────────────────────────────────────────────────────────
@tree.command(name="sunucu", description="🏠 Sunucu hakkında bilgi")
async def sunucu_komutu(interaction: discord.Interaction):
    g = interaction.guild
    if not g:
        await interaction.response.send_message("❌ Bu komut sadece sunucularda kullanılabilir.", ephemeral=True); return
    embed = discord.Embed(title=f"🏠 {g.name}", color=RENK_ANA)
    embed.add_field(name="🆔 ID",              value=f"`{g.id}`",                         inline=True)
    embed.add_field(name="👑 Sahip",            value=f"<@{g.owner_id}>",                 inline=True)
    embed.add_field(name="👥 Üye Sayısı",       value=f"`{g.member_count}`",              inline=True)
    embed.add_field(name="📅 Oluşturulma",      value=f"<t:{int(g.created_at.timestamp())}:D>", inline=True)
    embed.add_field(name="💬 Kanal Sayısı",     value=f"`{len(g.channels)}`",             inline=True)
    embed.add_field(name="🎭 Rol Sayısı",       value=f"`{len(g.roles)}`",                inline=True)
    embed.add_field(name="📊 Boost Seviyesi",   value=f"`{g.premium_tier}`",              inline=True)
    embed.add_field(name="💎 Boost Sayısı",     value=f"`{g.premium_subscription_count}`", inline=True)
    if g.icon:
        embed.set_thumbnail(url=str(g.icon.url))
    embed.set_footer(text="AZRxGUARD")
    await interaction.response.send_message(embed=embed)

# ── /avatar ───────────────────────────────────────────────────────────────────
@tree.command(name="avatar", description="🖼️ Kullanıcının avatarını göster")
@app_commands.describe(kullanici="Avatarı gösterilecek kullanıcı")
async def avatar_komutu(interaction: discord.Interaction, kullanici: discord.Member = None):
    hedef = kullanici or interaction.user
    embed = discord.Embed(title=f"🖼️ {hedef.display_name} — Avatar", color=RENK_ANA)
    embed.set_image(url=str(hedef.display_avatar.url))
    embed.add_field(name="🔗 PNG", value=f"[İndir]({hedef.display_avatar.with_format('png').url})", inline=True)
    embed.add_field(name="🔗 JPG", value=f"[İndir]({hedef.display_avatar.with_format('jpeg').url})", inline=True)
    embed.set_footer(text="AZRxGUARD")
    await interaction.response.send_message(embed=embed)

# ── /sasi ─────────────────────────────────────────────────────────────────────
@tree.command(name="sasi", description="🚗 Araç şasi no (VIN) sorgula — NHTSA veritabanı")
@app_commands.describe(sasi_no="17 haneli şasi numarası (örn: WBA5A5C54FD520774)")
async def sasi_komutu(interaction: discord.Interaction, sasi_no: str):
    await interaction.response.defer()
    from bot import vin_bilgi_al, vin_foto_bul
    sonuc = await vin_bilgi_al(sasi_no.strip())
    rapor = sonuc["rapor"]
    embed = discord.Embed(description=rapor[:4090], color=RENK_ANA)
    if sonuc.get("gecerli"):
        foto_url = await vin_foto_bul(sonuc["marka"], sonuc["model"], sonuc["yil"])
        if foto_url:
            embed.set_image(url=foto_url)
        embed.set_author(name=f"🚗 {sonuc['yil']} {sonuc['marka']} {sonuc['model']}")
    embed.set_footer(text="AZRxGUARD Otomotiv OSINT • NHTSA vPIC + Recalls + Complaints")
    await interaction.followup.send(embed=embed)

# ══════════════════════════════════════════════════════════════════════════════
# Ana coroutine (bot.py'dan çağrılır)
# ══════════════════════════════════════════════════════════════════════════════
async def run_discord():
    token = os.environ.get('DISCORD_TOKEN', '').strip()
    if not token:
        logger.warning("DISCORD_TOKEN ayarlı değil — Discord botu başlatılmadı.")
        return
    try:
        logger.info("Discord botu başlatılıyor...")
        await discord_client.start(token)
    except discord.LoginFailure:
        logger.error("Discord: Geçersiz token! DISCORD_TOKEN'ı kontrol et.")
    except asyncio.CancelledError:
        logger.info("Discord botu durduruldu.")
    except Exception as e:
        logger.error(f"Discord botu beklenmedik hata: {e}", exc_info=True)
    finally:
        if not discord_client.is_closed():
            await discord_client.close()
