import logging
import asyncio
import re
import datetime
import socket as _socket
import requests as http_requests
import html
import os
import pickle
import hashlib
import base64 as b64lib
import math
import ast
import random
import string
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- 7/24 UYANIK TUTMA SİSTEMİ ---
# Replit keeps the bot alive natively; no separate Flask keep-alive needed.
def uyanik_tut():
    pass

# --- LOG AYARLARI ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

MY_ID = 5730924995
KANAL_ID = -1003930940829
KONTROL_KANAL_USER = "@azrXmaqa"
YONETIM_KANAL_ID = -1003918825511
ZAMANLI_KANAL_ID = -1003775055611
TR_SAAT = datetime.timezone(datetime.timedelta(hours=3))
AZ_SAAT = datetime.timezone(datetime.timedelta(hours=4))

FILIGRAN_METNI = (
    "__________________________________\n"
    "|\n"
    "|⚡ 𝑴𝑨𝑫𝑬 𝑩𝒀  ➣ M̶A̶Q̶A̶💎 | 𝑶𝑾𝑵𝑬𝑹\n"
    "|__________________________________\n"
    "|\n"
    "|𝑪𝑯𝑨𝑵𝑵𝑬𝑳 ➣ 𝐚𝐳𝐫𝐗𝐦𝐚𝐪𝐚 \n"
    "|__________________________________"
)

# --- KALICI HAFIZA DOSYASI SİSTEMİ ---
HAFIZA_DOSYASI = "bot_uyeleri.dat"

def uyeleri_getir():
    if os.path.exists(HAFIZA_DOSYASI):
        try:
            with open(HAFIZA_DOSYASI, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Hafıza okuma hatası: {e}")
    return set()

def uyeleri_kaydet(uyeler_seti):
    try:
        with open(HAFIZA_DOSYASI, "wb") as f:
            pickle.dump(uyeler_seti, f)
    except Exception as e:
        logger.error(f"Hafıza yazma hatası: {e}")

# --- DİL SÖZLÜĞÜ ---
LANG_DATA = {
    'tr': {
        'welcome': "👋 **AZRxGUARD'a hoş geldin!**\n\nLütfen işlem yapmak için aşağıdaki butonları kullanın.",
        'lang_select': "🌍 **Lütfen bir dil seçin / Please select a language:**",
        'lang_changed': "✅ Bot dili başarıyla **Türkçe** olarak ayarlandı!",
        'btn_lang': "🌍 Dil / Language",
        'btn_channel': "📢 Kanalımız",
        'btn_admin': "📩 Admin'e Yaz",
        'btn_fun': "🚀 Eğlence & Araçlar",
        'btn_azr_special': "🚀 AZRxGUARD Özel",
        'btn_stats': "📊 İstatistik",
        'btn_roll_dice': "🎲 Zar At",
        'btn_back': "⬅️ Geri",
        'btn_ip': "🌐 IP Sorgula",
        'btn_ip_sorgu': "🌐 IP Sorgu",
        'btn_hatirlat': "⏰ Hatırlatıcı",
        'btn_panel': "🔍 TG PANELİ",
        'ip_ask': "🌐 **IP Sorgulama**\n\nSorgulamak istediğiniz IP adresini yazın:\nÖrnek: `8.8.8.8`",
        'ip_sorgu_welcome': "🌐 **IP Sorgu Menüsü**\n\nAşağıdan sorgu türünü seçin:",
        'ask_admin_msg': "📝 Lütfen iletmek istediğiniz şeyi yazın:",
        'msg_sent': "✅ Mesaj başarıyla iletildi!",
        'fun_welcome': "🚀 **Eğlence & Araçlar Menüsü**\n\nZar atmak için aşağıdaki butona basın:",
        'azr_welcome': "🔥 **AZRxGUARD Özel Menüsüne Hoş Geldiniz!**\n\nBot istatistiklerini canlı görmek için aşağıdaki butona tıklayın:",
        'force_join_text': "⚠️ **DURUN!** Botu kullanabilmek için önce resmi kanalımıza katılmanız gerekmektedir.\n\nKatıldıktan sonra bota tekrar `/start` yazabilir veya menüyü kullanabilirsiniz.",
        'btn_join_now': "📢 Kanala Katıl",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **Kullanıcı Bilgilerin**",
        'panel_welcome': "🔍 **PANEL — Kullanıcı Sorgu Merkezi**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nSorgulamak istediğin kullanıcının:\n• `@kullaniciadi` yazabilirsin\n• Sayısal `ID` yazabilirsin\n\nÖrnek: `@durov` veya `12345678`\n\n_Her bilgi ekrana dökülecek!_ 🔎",
        'panel_sorgulanıyor': "🔍 Sorgulanıyor...",
        'panel_bulunamadi': "❌ **Kullanıcı bulunamadı!**\n\nKullanıcı adını `@` ile ya da sayısal ID olarak gir.\nÖrnek: `@durov` veya `12345678`",
        'btn_guvenli_sorgu': "🕵️ USERNAME HUNTER",
        'guvenli_sorgu_welcome': "🕵️ **USERNAME HUNTER**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nKullanıcı adını 14 platformda aynı anda tara:",
        'btn_username_checker': "🔎 Platform Kullanıcı Adı Kontrolü",
        'username_checker_ask': "🔎 **Platform Kullanıcı Adı Kontrolü**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n14 platformda aynı anda kontrol edilecek.\nKullanıcı adını yaz (@ olmadan da olur):\nÖrnek: `maqa_01`",
        'btn_pro_araclar': "⚡ PRO ARAÇLAR",
        'pro_araclar_welcome': "⚡ **PRO ARAÇLAR MERKEZİ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nGüçlü araçlardan birini seçin:",
        'btn_hesap_arac': "🧮 Hesap Makinesi",
        'btn_hash_arac': "🔐 Hash Üretici",
        'btn_hava_arac': "🌍 Hava Durumu",
        'btn_doviz_arac': "💱 Döviz Kuru",
        'btn_saat_arac': "🕐 Dünya Saati",
        'btn_b64_arac': "🔒 Base64",
        'btn_sifre_arac': "🔑 Şifre Üretici",
        'btn_not_arac': "📝 Not Defterim",
        'btn_wiki_arac': "🌐 Wikipedia Ara",
        'btn_gunsozu_arac': "💡 Günün Sözü",
        'btn_birim_arac': "📐 Birim Çevir",
        'btn_sans_arac': "🎱 Şans Topu",
        'hesap_ask': "🧮 **Hesap Makinesi**\n\nMatematik ifadesi girin:\nÖrnek: `2**10` veya `sqrt(144)` veya `sin(pi/2)`",
        'hash_ask': "🔐 **Hash Üretici**\n\nHashlenmesini istediğiniz metni girin:\nÖrnek: `AZRxGUARD`",
        'hava_ulke_sec': "🌍 **Hava Durumu**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nÜlke seçin:",
        'hava_sehir_sec': "🏙️ **Şehir / Köy seçin:**",
        'doviz_from_sec': "💱 **Kaynak döviz seçin:**",
        'doviz_to_sec': "💱 **Hedef döviz seçin:**",
        'doviz_miktar_ask': "💰 **Miktarı girin:**\nÖrnek: `100` veya `250.50`",
        'b64_ask': "🔒 **Base64 Aracı**\n\nFormat: `encode metin` veya `decode bWV0aW4=`\nÖrnek: `encode AZRxGUARD`",
    },
    'az': {
        'welcome': "👋 **AZRxGUARD-a xoş gəldiniz!**\n\nXahiş edirik əməliyyat aparmaq üçün aşağıdakı düymələrdən istifadə edin.",
        'lang_select': "🌍 **Lütfen bir dil seçin / Please select a language:**",
        'lang_changed': "✅ Bot dili uğurla **Azərbaycanca** olaraq dəyişdirildi!",
        'btn_lang': "🌍 Dil / Language",
        'btn_channel': "📢 Kanalımız",
        'btn_admin': "📩 Adminə Yaz",
        'btn_fun': "🚀 Əyləncə & Alətlər",
        'btn_azr_special': "🚀 AZRxGUARD Özel",
        'btn_stats': "📊 Statistika",
        'btn_roll_dice': "🎲 Zar At",
        'btn_back': "⬅️ Geri",
        'btn_ip': "🌐 IP Sorğu",
        'btn_ip_sorgu': "🌐 IP Sorğu",
        'btn_hatirlat': "⏰ Xatırladıcı",
        'btn_panel': "🔍 TG PANELİ",
        'ip_ask': "🌐 **IP Sorğulama**\n\nSorğulamaq istədiyiniz IP ünvanını yazın:\nNümunə: `8.8.8.8`",
        'ip_sorgu_welcome': "🌐 **IP Sorğu Menyusu**\n\nAşağıdan sorğu növünü seçin:",
        'ask_admin_msg': "📝 Xahiş edirik çatdırmaq istədiyiniz şeyi yazın:",
        'msg_sent': "✅ Mesaj uğurla göndərildi!",
        'fun_welcome': "🚀 **Əyləncə & Alətlər Menyusu**\n\nZar atmaq üçün aşağıdakı düyməyə basın:",
        'azr_welcome': "🔥 **AZRxGUARD Özel Menyusuna Xoş Gəldiniz!**\n\nBot statistikasını canlı görmək üçün aşağıdakı düyməyə vurun:",
        'force_join_text': "⚠️ **DAYANIN!** Botdan istifadə edə bilmək üçün əvvəlcə rəsmi kanalımıza qoşulmalısınız.\n\nQoşulduqdan sonra bota yenidən `/start` yaza bilərsiniz.",
        'btn_join_now': "📢 Kanala Qoşul",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **İstifadəçi Məlumatların**",
        'panel_welcome': "🔍 **PANEL — İstifadəçi Sorğu Mərkəzi**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nSorğulamaq istədiyin istifadəçinin:\n• `@istifadəçiadı` yaza bilərsən\n• Rəqəmsal `ID` yaza bilərsən\n\nNümunə: `@durov` və ya `12345678`\n\n_Bütün məlumatlar ekrana çıxacaq!_ 🔎",
        'panel_sorgulanıyor': "🔍 Sorğulanır...",
        'panel_bulunamadi': "❌ **İstifadəçi tapılmadı!**\n\nİstifadəçi adını `@` ilə ya da rəqəmsal ID kimi daxil et.\nNümunə: `@durov` və ya `12345678`",
        'btn_guvenli_sorgu': "🕵️ USERNAME HUNTER",
        'guvenli_sorgu_welcome': "🕵️ **USERNAME HUNTER**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nİstifadəçi adını 14 platformda eyni anda tara:",
        'btn_username_checker': "🔎 Platforma İstifadəçi Adı Yoxlaması",
        'username_checker_ask': "🔎 **Platforma İstifadəçi Adı Yoxlaması**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n14 platformda eyni anda yoxlanacaq.\nİstifadəçi adını yaz:\nNümunə: `maqa_01`",
        'btn_pro_araclar': "⚡ PRO ALƏTLƏR",
        'pro_araclar_welcome': "⚡ **PRO ALƏTLƏR MƏRKƏZİ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nGüclü alətlərdən birini seçin:",
        'btn_hesap_arac': "🧮 Kalkulyator",
        'btn_hash_arac': "🔐 Hash Yaradıcı",
        'btn_hava_arac': "🌍 Hava Proqnozu",
        'btn_doviz_arac': "💱 Valyuta Kursu",
        'btn_saat_arac': "🕐 Dünya Saatı",
        'btn_b64_arac': "🔒 Base64",
        'btn_sifre_arac': "🔑 Şifrə Yaradıcı",
        'btn_not_arac': "📝 Qeydlərim",
        'btn_wiki_arac': "🌐 Wikipedia Axtar",
        'btn_gunsozu_arac': "💡 Günün Sözü",
        'btn_birim_arac': "📐 Vahid Çeviricisi",
        'btn_sans_arac': "🎱 Şans Topu",
        'hesap_ask': "🧮 **Kalkulyator**\n\nRiyazi ifadə daxil edin:\nNümunə: `2**10` və ya `sqrt(144)`",
        'hash_ask': "🔐 **Hash Yaradıcı**\n\nHash etmək istədiyiniz mətni daxil edin:\nNümunə: `AZRxGUARD`",
        'hava_ulke_sec': "🌍 **Hava Proqnozu**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nÖlkə seçin:",
        'hava_sehir_sec': "🏙️ **Şəhər / Kənd seçin:**",
        'doviz_from_sec': "💱 **Mənbə valyuta seçin:**",
        'doviz_to_sec': "💱 **Hədəf valyuta seçin:**",
        'doviz_miktar_ask': "💰 **Məbləği daxil edin:**\nNümunə: `100` və ya `250.50`",
        'b64_ask': "🔒 **Base64 Aləti**\n\nFormat: `encode mətn` və ya `decode bWV0aW4=`\nNümunə: `encode AZRxGUARD`",
    },
    'ru': {
        'welcome': "👋 **Добро пожаловать в AZRxGUARD!**\n\nПожалуйста, используйте кнопки ниже для выполнения действий.",
        'lang_select': "🌍 **Пожалуйста, выберите язык / Please select a language:**",
        'lang_changed': "✅ Язык бота успешно изменен на **Русский**!",
        'btn_lang': "🌍 Язык / Language",
        'btn_channel': "📢 Наш канал",
        'btn_admin': "📩 Написать админу",
        'btn_fun': "🚀 Развлечения и Инструменты",
        'btn_azr_special': "🚀 AZRxGUARD Специальный",
        'btn_stats': "📊 Статистика",
        'btn_roll_dice': "🎲 Бросить кубик",
        'btn_back': "⬅️ Назад",
        'btn_ip': "🌐 IP Запрос",
        'btn_ip_sorgu': "🌐 IP Запрос",
        'btn_hatirlat': "⏰ Напоминание",
        'btn_panel': "🔍 TG PANELİ",
        'ip_ask': "🌐 **IP Запрос**\n\nВведите IP-адрес для проверки:\nПример: `8.8.8.8`",
        'ip_sorgu_welcome': "🌐 **Меню IP Запроса**\n\nВыберите тип запроса:",
        'ask_admin_msg': "📝 Пожалуйста, напишите то, что вы хотите передать:",
        'msg_sent': "✅ Сообщение успешно отправлено!",
        'fun_welcome': "🚀 **Развлекательное меню**\n\nНажмите кнопку ниже, чтобы бросить кубик:",
        'azr_welcome': "🔥 **Специальное меню AZRxGUARD!**\n\nНажмите кнопку ниже, чтобы увидеть статистику бота:",
        'force_join_text': "⚠️ **ВНИМАНИЕ!** Чтобы использовать бота, вы должны сначала подписаться на наш официальный канал.\n\nПосле подписки отправьте `/start` снова.",
        'btn_join_now': "📢 Подписаться на канал",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **Информация о тебе**",
        'panel_welcome': "🔍 **PANEL — Центр запросов пользователей**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nВведи:\n• `@username` пользователя\n• Числовой `ID` пользователя\n\nПример: `@durov` или `12345678`\n\n_Вся информация будет выведена!_ 🔎",
        'panel_sorgulanıyor': "🔍 Запрос выполняется...",
        'panel_bulunamadi': "❌ **Пользователь не найден!**\n\nВведи username через `@` или числовой ID.\nПример: `@durov` или `12345678`",
        'btn_guvenli_sorgu': "🕵️ USERNAME HUNTER",
        'guvenli_sorgu_welcome': "🕵️ **USERNAME HUNTER**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nПроверьте имя на 14 платформах одновременно:",
        'btn_username_checker': "🔎 Проверка имени на платформах",
        'username_checker_ask': "🔎 **Проверка имени пользователя**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nПроверка на 14 платформах одновременно.\nВведите имя пользователя:\nПример: `maqa_01`",
        'btn_pro_araclar': "⚡ PRO ИНСТРУМЕНТЫ",
        'pro_araclar_welcome': "⚡ **PRO ИНСТРУМЕНТЫ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nВыберите мощный инструмент:",
        'btn_hesap_arac': "🧮 Калькулятор",
        'btn_hash_arac': "🔐 Генератор Hash",
        'btn_hava_arac': "🌍 Погода",
        'btn_doviz_arac': "💱 Курс валют",
        'btn_saat_arac': "🕐 Мировое время",
        'btn_b64_arac': "🔒 Base64",
        'btn_sifre_arac': "🔑 Генератор паролей",
        'btn_not_arac': "📝 Мои заметки",
        'btn_wiki_arac': "🌐 Поиск Wikipedia",
        'btn_gunsozu_arac': "💡 Цитата дня",
        'btn_birim_arac': "📐 Конвертер единиц",
        'btn_sans_arac': "🎱 Шар удачи",
        'hesap_ask': "🧮 **Калькулятор**\n\nВведите математическое выражение:\nПример: `2**10` или `sqrt(144)`",
        'hash_ask': "🔐 **Генератор Hash**\n\nВведите текст для хеширования:\nПример: `AZRxGUARD`",
        'hava_ulke_sec': "🌍 **Погода**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nВыберите страну:",
        'hava_sehir_sec': "🏙️ **Выберите город / деревню:**",
        'doviz_from_sec': "💱 **Выберите исходную валюту:**",
        'doviz_to_sec': "💱 **Выберите целевую валюту:**",
        'doviz_miktar_ask': "💰 **Введите сумму:**\nПример: `100` или `250.50`",
        'b64_ask': "🔒 **Инструмент Base64**\n\nФормат: `encode текст` или `decode bWV0aW4=`\nПример: `encode AZRxGUARD`",
    },
    'en': {
        'welcome': "👋 **Welcome to AZRxGUARD!**\n\nPlease use the buttons below to proceed.",
        'lang_select': "🌍 **Please select a language / Lütfen bir dil seçin:**",
        'lang_changed': "✅ Bot language has been successfully set to **English**!",
        'btn_lang': "🌍 Dil / Language",
        'btn_channel': "📢 Our Channel",
        'btn_admin': "📩 Contact Admin",
        'btn_fun': "🚀 Entertainment & Tools",
        'btn_azr_special': "🚀 AZRxGUARD Special",
        'btn_stats': "📊 Statistics",
        'btn_roll_dice': "🎲 Roll Dice",
        'btn_back': "⬅️ Back",
        'btn_ip': "🌐 IP Lookup",
        'btn_ip_sorgu': "🌐 IP Query",
        'btn_hatirlat': "⏰ Reminder",
        'btn_panel': "🔍 TG PANELİ",
        'ip_ask': "🌐 **IP Lookup**\n\nEnter the IP address to query:\nExample: `8.8.8.8`",
        'ip_sorgu_welcome': "🌐 **IP Query Menu**\n\nSelect a query type below:",
        'ask_admin_msg': "📝 Please write what you want to convey:",
        'msg_sent': "✅ Message successfully sent!",
        'fun_welcome': "🚀 **Entertainment & Tools Menu**\n\nPress the button below to roll the dice:",
        'azr_welcome': "🔥 **Welcome to AZRxGUARD Special Menu!**\n\nClick the button below to view live bot statistics:",
        'force_join_text': "⚠️ **ATTENTION!** To use this bot, you must first join our official channel.\n\nAfter joining, please send `/start` again to unlock.",
        'btn_join_now': "📢 Join Channel",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **Your Information**",
        'panel_welcome': "🔍 **PANEL — User Query Center**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nEnter:\n• `@username` of the user\n• Numeric `ID` of the user\n\nExample: `@durov` or `12345678`\n\n_All information will be displayed!_ 🔎",
        'panel_sorgulanıyor': "🔍 Querying...",
        'panel_bulunamadi': "❌ **User not found!**\n\nEnter username with `@` or a numeric ID.\nExample: `@durov` or `12345678`",
        'btn_guvenli_sorgu': "🕵️ USERNAME HUNTER",
        'guvenli_sorgu_welcome': "🕵️ **USERNAME HUNTER**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nScan a username across 14 platforms at once:",
        'btn_username_checker': "🔎 Platform Username Checker",
        'username_checker_ask': "🔎 **Platform Username Checker**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nChecks 14 platforms simultaneously.\nEnter a username:\nExample: `maqa_01`",
        'btn_pro_araclar': "⚡ PRO TOOLS",
        'pro_araclar_welcome': "⚡ **PRO TOOLS CENTER**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nChoose a powerful tool:",
        'btn_hesap_arac': "🧮 Calculator",
        'btn_hash_arac': "🔐 Hash Generator",
        'btn_hava_arac': "🌍 Weather",
        'btn_doviz_arac': "💱 Currency Converter",
        'btn_saat_arac': "🕐 World Clock",
        'btn_b64_arac': "🔒 Base64",
        'btn_sifre_arac': "🔑 Password Generator",
        'btn_not_arac': "📝 My Notes",
        'btn_wiki_arac': "🌐 Wikipedia Search",
        'btn_gunsozu_arac': "💡 Quote of the Day",
        'btn_birim_arac': "📐 Unit Converter",
        'btn_sans_arac': "🎱 Lucky Ball",
        'hesap_ask': "🧮 **Calculator**\n\nEnter a math expression:\nExample: `2**10` or `sqrt(144)` or `sin(pi/2)`",
        'hash_ask': "🔐 **Hash Generator**\n\nEnter text to hash:\nExample: `AZRxGUARD`",
        'hava_ulke_sec': "🌍 **Weather**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nSelect a country:",
        'hava_sehir_sec': "🏙️ **Select city / town:**",
        'doviz_from_sec': "💱 **Select source currency:**",
        'doviz_to_sec': "💱 **Select target currency:**",
        'doviz_miktar_ask': "💰 **Enter amount:**\nExample: `100` or `250.50`",
        'b64_ask': "🔒 **Base64 Tool**\n\nFormat: `encode text` or `decode bWV0aW4=`\nExample: `encode AZRxGUARD`",
    },
    'de': {
        'welcome': "👋 **Willkommen bei AZRxGUARD!**\n\nBitte nutzen Sie die folgenden Schaltflächen, um fortzufahren.",
        'lang_select': "🌍 **Bitte wählen Sie eine Sprache / Please select a language:**",
        'lang_changed': "✅ Die Botsprache wurde erfolgreich auf **Deutsch** umgestellt!",
        'btn_lang': "🌍 Sprache / Language",
        'btn_channel': "📢 Unser Kanal",
        'btn_admin': "📩 Admin schreiben",
        'btn_fun': "🚀 Unterhaltung & Tools",
        'btn_azr_special': "🚀 AZRxGUARD Spezial",
        'btn_stats': "📊 Statistiken",
        'btn_roll_dice': "🎲 Würfel werfen",
        'btn_back': "⬅️ Zurück",
        'btn_ip': "🌐 IP Abfrage",
        'btn_ip_sorgu': "🌐 IP Abfrage",
        'btn_hatirlat': "⏰ Erinnerung",
        'btn_panel': "🔍 TG PANELİ",
        'ip_ask': "🌐 **IP Abfrage**\n\nGeben Sie die IP-Adresse ein:\nBeispiel: `8.8.8.8`",
        'ip_sorgu_welcome': "🌐 **IP Abfrage-Menü**\n\nWählen Sie unten einen Abfragetyp:",
        'ask_admin_msg': "📝 Bitte schreiben Sie, was Sie übermitteln möchten:",
        'msg_sent': "✅ Nachricht erfolgreich gesendet!",
        'fun_welcome': "🚀 **Unterhaltungs- & Tools-Menü**\n\nDrücken Sie die Taste unten, um zu würfeln:",
        'azr_welcome': "🔥 **Willkommen im AZRxGUARD Spezialmenü!**\n\nKlicken Sie auf die Schaltfläche unten, um die Live-Bot-Statistiken anzuzeigen:",
        'force_join_text': "⚠️ **ACHTUNG!** Um diesen Bot nutzen zu können, müssen Sie zuerst unserem offiziellen Kanal beitreten.\n\nNach dem Beitritt senden Sie bitte erneut `/start`.",
        'btn_join_now': "📢 Kanal beitreten",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **Deine Informationen**",
        'panel_welcome': "🔍 **PANEL — Benutzer-Abfragezentrum**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nGib ein:\n• `@benutzername` des Nutzers\n• Numerische `ID` des Nutzers\n\nBeispiel: `@durov` oder `12345678`\n\n_Alle Informationen werden angezeigt!_ 🔎",
        'panel_sorgulanıyor': "🔍 Abfrage läuft...",
        'panel_bulunamadi': "❌ **Benutzer nicht gefunden!**\n\nGib den Benutzernamen mit `@` oder eine numerische ID ein.\nBeispiel: `@durov` oder `12345678`",
        'btn_guvenli_sorgu': "🕵️ USERNAME HUNTER",
        'guvenli_sorgu_welcome': "🕵️ **USERNAME HUNTER**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nBenutzernamen auf 14 Plattformen gleichzeitig prüfen:",
        'btn_username_checker': "🔎 Benutzername auf Plattformen prüfen",
        'username_checker_ask': "🔎 **Benutzername-Prüfung**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nPrüft 14 Plattformen gleichzeitig.\nBenutzernamen eingeben:\nBeispiel: `maqa_01`",
        'btn_pro_araclar': "⚡ PRO WERKZEUGE",
        'pro_araclar_welcome': "⚡ **PRO WERKZEUGE**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nWählen Sie ein leistungsstarkes Werkzeug:",
        'btn_hesap_arac': "🧮 Taschenrechner",
        'btn_hash_arac': "🔐 Hash-Generator",
        'btn_hava_arac': "🌍 Wetter",
        'btn_doviz_arac': "💱 Währungsrechner",
        'btn_saat_arac': "🕐 Weltzeit",
        'btn_b64_arac': "🔒 Base64",
        'btn_sifre_arac': "🔑 Passwort-Generator",
        'btn_not_arac': "📝 Meine Notizen",
        'btn_wiki_arac': "🌐 Wikipedia Suche",
        'btn_gunsozu_arac': "💡 Zitat des Tages",
        'btn_birim_arac': "📐 Einheitenumrechner",
        'btn_sans_arac': "🎱 Glückskugel",
        'hesap_ask': "🧮 **Taschenrechner**\n\nMathematischen Ausdruck eingeben:\nBeispiel: `2**10` oder `sqrt(144)`",
        'hash_ask': "🔐 **Hash-Generator**\n\nText zum Hashen eingeben:\nBeispiel: `AZRxGUARD`",
        'hava_ulke_sec': "🌍 **Wetter**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nBitte Land auswählen:",
        'hava_sehir_sec': "🏙️ **Stadt auswählen:**",
        'doviz_from_sec': "💱 **Ausgangswährung wählen:**",
        'doviz_to_sec': "💱 **Zielwährung wählen:**",
        'doviz_miktar_ask': "💰 **Betrag eingeben:**\nBeispiel: `100` oder `250.50`",
        'b64_ask': "🔒 **Base64-Tool**\n\nFormat: `encode Text` oder `decode bWV0aW4=`\nBeispiel: `encode AZRxGUARD`",
    },
    'ka': {
        'welcome': "👋 **მოგესალმებით AZRxGUARD-ში!**\n\nგთხოვთ გამოიყენოთ ქვემოთ მოცემული ღილაკები.",
        'lang_select': "🌍 **გთხოვთ აირჩიოთ ენა / Please select a language:**",
        'lang_changed': "✅ ბოტის ენა წარმატებით შეიცვალა **ქართულად**!",
        'btn_lang': "🌍 ენა / Language",
        'btn_channel': "📢 არხი",
        'btn_fun': "🎲 გასართობი",
        'btn_admin': "📩 ადმინს მიწერე",
        'btn_roll_dice': "🎲 კამათელი",
        'btn_back': "⬅️ უკან",
        'btn_stats': "📊 სტატისტიკა",
        'btn_ip': "🌐 IP ძიება",
        'btn_ip_sorgu': "🌐 IP ძიება",
        'btn_hatirlat': "⏰ შეხსენება",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **შენი ინფორმაცია**",
        'btn_azr_special': "⭐ AZRx სპეციალური",
        'btn_panel': "🔍 PANEL",
        'ip_ask': "🌐 **IP ძიება**\n\nIP მისამართი შეიყვანეთ:\nმაგ: `8.8.8.8`",
        'ip_sorgu_welcome': "🌐 **IP ძიება**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nIP მისამართი შეიყვანეთ:",
        'ask_admin_msg': "📝 გთხოვთ დაწეროთ თქვენი შეტყობინება:",
        'msg_sent': "✅ შეტყობინება გაიგზავნა!",
        'fun_welcome': "🎲 **გასართობი მენიუ**\n\nდაჭირეთ ქვემოთ მოცემულ ღილაკს:",
        'azr_welcome': "🔥 **AZRxGUARD სპეციალური მენიუ!**\n\nბოტის სტატისტიკის სანახავად ქვემოთ ღილაკს დააჭირეთ:",
        'force_join_text': "⚠️ **გაჩერდი!** ბოტის გამოსაყენებლად ჯერ ჩვენს არხს გამოიწერეთ.\n\nგამოწერის შემდეგ კვლავ `/start` გაგზავნეთ.",
        'btn_join_now': "📢 არხის გამოწერა",
        'panel_welcome': "🔍 **PANEL — მომხმარებლის ძიება**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nშეიყვანეთ:\n• `@username` ან ციფრული `ID`\n\nმაგ: `@durov` ან `12345678`\n\n_ყველა ინფო ეკრანზე გამოჩნდება!_ 🔎",
        'panel_sorgulanıyor': "🔍 მიმდინარეობს ძიება...",
        'panel_bulunamadi': "❌ **მომხმარებელი ვერ მოიძებნა!**\n\nშეიყვანეთ `@` სახელი ან ID.\nმაგ: `@durov` ან `12345678`",
        'btn_guvenli_sorgu': "🕵️ USERNAME HUNTER",
        'guvenli_sorgu_welcome': "🕵️ **USERNAME HUNTER**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n14 პლატფორმაზე სახელის ძიება:",
        'btn_username_checker': "🔎 პლატფორმის სახელის შემოწმება",
        'username_checker_ask': "🔎 **პლატფორმის სახელის შემოწმება**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n14 პლატფორმაზე ერთდროულად შემოწმება.\nსახელი შეიყვანეთ:\nმაგ: `maqa_01`",
        'btn_pro_araclar': "⚡ PRO ინსტრუმენტები",
        'pro_araclar_welcome': "⚡ **PRO ინსტრუმენტები**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nაირჩიეთ ინსტრუმენტი:",
        'btn_hesap_arac': "🧮 კალკულატორი",
        'btn_hash_arac': "🔐 Hash გენერატორი",
        'btn_hava_arac': "🌍 ამინდი",
        'btn_doviz_arac': "💱 ვალუტა",
        'btn_saat_arac': "🕐 მსოფლიო დრო",
        'btn_b64_arac': "🔒 Base64",
        'btn_sifre_arac': "🔑 პაროლის გენერატორი",
        'btn_not_arac': "📝 ჩემი ჩანაწერები",
        'btn_wiki_arac': "🌐 Wikipedia",
        'btn_gunsozu_arac': "💡 დღის ციტატა",
        'btn_birim_arac': "📐 ერთეულის გადამყვანი",
        'btn_sans_arac': "🎱 იღბლიანი ბურთი",
        'hesap_ask': "🧮 **კალკულატორი**\n\nმათემატიკური გამოსახულება შეიყვანეთ:\nმაგ: `2**10` ან `sqrt(144)`",
        'hash_ask': "🔐 **Hash გენერატორი**\n\nტექსტი შეიყვანეთ:\nმაგ: `AZRxGUARD`",
        'hava_ulke_sec': "🌍 **ამინდი**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nქვეყანა აირჩიეთ:",
        'hava_sehir_sec': "🏙️ **ქალაქი/სოფელი აირჩიეთ:**",
        'doviz_from_sec': "💱 **საწყისი ვალუტა აირჩიეთ:**",
        'doviz_to_sec': "💱 **სამიზნე ვალუტა აირჩიეთ:**",
        'doviz_miktar_ask': "💰 **თანხა შეიყვანეთ:**\nმაგ: `100` ან `250.50`",
        'b64_ask': "🔒 **Base64**\n\nფორმატი: `encode ტექსტი` ან `decode bWV0aW4=`\nმაგ: `encode AZRxGUARD`",
    }
}

# --- YARDIMCI FONKSİYONLAR ---
def get_lang(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> str:
    if 'lang' not in context.bot_data:
        context.bot_data['lang'] = {}
    return context.bot_data['lang'].get(user_id, 'tr')

def ana_menu_klavye(lang: str) -> InlineKeyboardMarkup:
    strings = LANG_DATA[lang]
    klavye = [
        [
            InlineKeyboardButton(strings['btn_lang'], callback_data='menu_lang'),
            InlineKeyboardButton(strings['btn_channel'], url='https://t.me/azrXmaqa')
        ],
        [
            InlineKeyboardButton(strings['btn_fun'], callback_data='menu_fun'),
            InlineKeyboardButton(strings['btn_admin'], url='https://t.me/Maqa343')
        ],
        [
            InlineKeyboardButton(strings.get('btn_ip_sorgu', '🌐 IP Sorgu'), callback_data='menu_ip_sorgu')
        ],
        [
            InlineKeyboardButton(strings['btn_azr_special'], callback_data='menu_azr_special')
        ],
        [
            InlineKeyboardButton(strings.get('btn_panel', '🔍 PANEL'), callback_data='menu_panel')
        ],
        [
            InlineKeyboardButton(strings.get('btn_guvenli_sorgu', '🕵️ USERNAME HUNTER'), callback_data='menu_guvenli_sorgu')
        ],
        [
            InlineKeyboardButton(strings.get('btn_pro_araclar', '⚡ PRO ARAÇLAR'), callback_data='menu_pro_araclar')
        ]
    ]
    return InlineKeyboardMarkup(klavye)

# --- 🔍 TG PANELİ — GELİŞMİŞ KULLANICI/GRUP/KANAL SORGU FONKSİYONU ---
async def panel_kullanici_sorgula(bot, sorgu: str) -> str:
    try:
        hedef = int(sorgu) if sorgu.lstrip('-').isdigit() else (sorgu if sorgu.startswith('@') else f"@{sorgu}")
        chat  = await bot.get_chat(hedef)

        tip_map = {'private':'👤 Kullanıcı','bot':'🤖 Bot','group':'👥 Grup','supergroup':'👥 Süper Grup','channel':'📢 Kanal'}
        tip = tip_map.get(chat.type, chat.type)

        ad    = html.escape(chat.first_name or '') if chat.first_name else '—'
        soyad = html.escape(chat.last_name  or '') if chat.last_name  else '—'
        tam_ad = f"{ad} {soyad}".strip() if chat.last_name else ad
        kullanici_adi = f"@{chat.username}" if chat.username else '—'
        profil_link   = f"tg://user?id={chat.id}"

        dogrulandi = '✅ Evet' if getattr(chat, 'is_verified', False) else '❌ Hayır'
        scam       = '🚨 SCAM' if getattr(chat, 'is_scam', False)    else '✅ Temiz'
        fake       = '⚠️ FAKE' if getattr(chat, 'is_fake', False)    else '✅ Gerçek'

        aktif_kullanici_adlari = '—'
        if getattr(chat, 'active_usernames', None):
            aktif_kullanici_adlari = '  |  '.join([f"@{u}" for u in chat.active_usernames])

        id_basamak   = len(str(abs(chat.id)))

        metin = (
            f"🔍 **TG KANAL SOHBET PANELİ GÜVENLİ**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📂 **Tür:** {tip}\n"
            f"👤 **Ad:** [{tam_ad}]({profil_link})\n"
            f"🔤 **Soyad:** `{soyad}`\n"
            f"🏷️ **Kullanıcı Adı:** `{kullanici_adi}`\n"
            f"🆔 **Telegram ID:** `{chat.id}`\n"
            f"🔢 **ID Basamak Sayısı:** `{id_basamak}`\n"
            f"🔤 **Aktif Kullanıcı Adları:** {aktif_kullanici_adlari}\n\n"
            f"✅ **Doğrulanmış:** {dogrulandi}\n"
            f"🚨 **Scam:** {scam}\n"
            f"⚠️ **Fake:** {fake}\n\n"
        )

        # ── KULLANICI / BOT ──────────────────────────────────────────
        if chat.type in ('private', 'bot'):
            premium    = '✅ Evet' if getattr(chat, 'is_premium', False)    else '❌ Hayır'
            kisitlandi = '⚠️ Evet' if getattr(chat, 'is_restricted', False) else '✅ Hayır'
            bio         = html.escape(chat.bio) if getattr(chat, 'bio', None) else '—'
            ozel_iletme = "🔒 Gizli" if getattr(chat, 'has_private_forwards', False) else "✅ Açık"
            emoji_durum = f"`{chat.emoji_status_custom_emoji_id}`" if getattr(chat, 'emoji_status_custom_emoji_id', None) else '—'
            kisisel_chat    = "✅ Var" if getattr(chat, 'has_personal_chat', False) else "❌ Yok"
            vurgu_renk      = f"`{chat.accent_color_id}`" if getattr(chat, 'accent_color_id', None) is not None else '—'
            profil_vurgu    = f"`{chat.profile_accent_color_id}`" if getattr(chat, 'profile_accent_color_id', None) is not None else '—'

            foto_sayisi = '—'
            try:
                fotolar = await bot.get_user_profile_photos(chat.id, limit=1)
                foto_sayisi = str(fotolar.total_count)
            except Exception:
                pass

            metin += (
                f"💎 **Telegram Premium:** {premium}\n"
                f"🚫 **Kısıtlanmış:** {kisitlandi}\n"
                f"🔀 **Mesaj Yönlendirme:** {ozel_iletme}\n"
                f"😀 **Emoji Durumu ID:** {emoji_durum}\n"
                f"💬 **Kişisel Sohbet:** {kisisel_chat}\n"
                f"🎨 **Vurgu Rengi:** {vurgu_renk}\n"
                f"🖌️ **Profil Vurgu Rengi:** {profil_vurgu}\n\n"
                f"📝 **Bio:** {bio}\n"
                f"🖼️ **Profil Fotoğraf Sayısı:** `{foto_sayisi}`\n\n"
                f"🔗 **Profil Linki:** {profil_link}\n\n"
            )

            if chat.type == 'bot':
                b_gruba    = "✅" if getattr(chat, 'can_join_groups', False)            else "❌"
                b_oku      = "✅" if getattr(chat, 'can_read_all_group_messages', False) else "❌"
                b_inline   = "✅" if getattr(chat, 'supports_inline_queries', False)     else "❌"
                b_biz      = "✅" if getattr(chat, 'can_connect_to_business', False)     else "❌"
                b_web      = "✅" if getattr(chat, 'has_main_web_app', False)            else "❌"
                metin += (
                    f"🤖 **Bot Detayları:**\n"
                    f"  👥 Gruba Eklenebilir: {b_gruba}\n"
                    f"  📖 Tüm Mesajları Okur: {b_oku}\n"
                    f"  ⚡ Inline Mod: {b_inline}\n"
                    f"  💼 İş Hesabına Bağlanır: {b_biz}\n"
                    f"  🌐 Ana Web Uygulaması: {b_web}\n\n"
                )

        # ── GRUP / SÜPER GRUP ────────────────────────────────────────
        elif chat.type in ('group', 'supergroup'):
            aciklama    = html.escape(chat.description) if getattr(chat, 'description', None) else '—'
            davet_linki = getattr(chat, 'invite_link', None) or '—'
            linked_chat = str(getattr(chat, 'linked_chat_id', None) or '—')
            sticker_set = getattr(chat, 'sticker_set_name', None) or '—'
            chat_user   = f"@{chat.username}" if chat.username else '—'

            uye_sayisi = '—'
            try:
                uye_sayisi = str(await bot.get_chat_member_count(chat.id))
            except Exception:
                pass

            admin_satirlari = []
            admin_izin_satirlari = []
            admin_sayisi = bot_sayisi = 0
            try:
                adminler = await bot.get_chat_administrators(chat.id)
                admin_sayisi = len(adminler)
                for a in adminler:
                    if a.user.is_bot:
                        bot_sayisi += 1
                for a in adminler[:10]:
                    a_adi = html.escape(a.user.first_name or '?')
                    a_un  = f"@{a.user.username}" if a.user.username else f"#{a.user.id}"
                    rol   = "👑 Kurucu" if a.status == 'creator' else "🛡️ Admin"
                    rozet = " 🤖" if a.user.is_bot else ""
                    admin_satirlari.append(f"  {rol}{rozet} [{a_adi}](tg://user?id={a.user.id}) `{a_un}`")
                    if hasattr(a, 'can_delete_messages'):
                        def f(v): return "✅" if v else "❌"
                        admin_izin_satirlari.append(
                            f"  ┗ [{a_adi}] Sil:{f(a.can_delete_messages)} Pin:{f(getattr(a,'can_pin_messages',None))} "
                            f"Davet:{f(getattr(a,'can_invite_users',None))} "
                            f"Kısıtla:{f(getattr(a,'can_restrict_members',None))} "
                            f"Yönet:{f(getattr(a,'can_manage_chat',None))}"
                        )
            except Exception:
                pass

            perms = getattr(chat, 'permissions', None)
            perm_satirlari = ''
            if perms:
                def e(v): return "✅" if v else "❌"
                perm_satirlari = (
                    f"  💬 Mesaj: {e(perms.can_send_messages)}  |  🖼️ Fotoğraf: {e(perms.can_send_photos)}  |  🎥 Video: {e(perms.can_send_videos)}\n"
                    f"  🎙️ Ses: {e(perms.can_send_voice_notes)}  |  📄 Dosya: {e(perms.can_send_documents)}  |  🎵 Audio: {e(perms.can_send_audios)}\n"
                    f"  🎭 Sticker/GIF: {e(perms.can_send_other_messages)}  |  📊 Poll: {e(perms.can_send_polls)}\n"
                    f"  🔗 Link Önizleme: {e(perms.can_add_web_page_previews)}  |  📌 Pin: {e(perms.can_pin_messages)}\n"
                    f"  👥 Davet: {e(perms.can_invite_users)}  |  ℹ️ Bilgi Değiştir: {e(perms.can_change_info)}\n"
                    f"  📹 Video Note: {e(perms.can_send_video_notes)}"
                )

            has_protected  = "🔒 Evet" if getattr(chat, 'has_protected_content', False) else "✅ Hayır"
            is_forum       = "✅ Evet" if getattr(chat, 'is_forum', False) else "❌ Hayır"
            join_req       = "✅ Evet" if getattr(chat, 'join_by_request', False) else "❌ Hayır"
            join_send      = "✅ Evet" if getattr(chat, 'join_to_send_messages', False) else "❌ Hayır"
            hidden_members = "🔒 Evet" if getattr(chat, 'has_hidden_members', False) else "✅ Hayır"
            anti_spam      = "✅ Aktif" if getattr(chat, 'has_aggressive_anti_spam_enabled', False) else "❌ Kapalı"
            slow_mode      = f"`{chat.slow_mode_delay}s`" if getattr(chat, 'slow_mode_delay', None) else "❌ Kapalı"
            auto_delete    = f"`{chat.message_auto_delete_time}s`" if getattr(chat, 'message_auto_delete_time', None) else "❌ Kapalı"
            visible_hist   = "✅ Evet" if getattr(chat, 'has_visible_history', False) else "❌ Hayır"

            metin += (
                f"🏷️ **Kullanıcı Adı:** `{chat_user}`\n"
                f"👥 **Üye Sayısı:** `{uye_sayisi}`\n"
                f"🛡️ **Admin Sayısı:** `{admin_sayisi}`\n"
                f"🤖 **Bot Sayısı:** `{bot_sayisi}`\n\n"
                f"📝 **Açıklama:** {aciklama}\n"
                f"🔗 **Davet Linki:** {davet_linki}\n"
                f"💬 **Bağlı Kanal ID:** `{linked_chat}`\n"
                f"🎭 **Sticker Seti:** `{sticker_set}`\n\n"
                f"🗂️ **Forum Modu:** {is_forum}\n"
                f"🔒 **İçerik Koruması:** {has_protected}\n"
                f"✋ **Onay ile Katılım:** {join_req}\n"
                f"✉️ **Mesaj için Katılım:** {join_send}\n"
                f"👥 **Gizli Üyeler:** {hidden_members}\n"
                f"📜 **Geçmiş Mesajlar:** {visible_hist}\n"
                f"🛡️ **Agresif Anti-Spam:** {anti_spam}\n"
                f"🐌 **Yavaş Mod:** {slow_mode}\n"
                f"⏱️ **Otomatik Mesaj Silme:** {auto_delete}\n\n"
            )

            if perm_satirlari:
                metin += f"🔐 **Üye İzinleri:**\n{perm_satirlari}\n\n"

            if admin_satirlari:
                metin += "👑 **Adminler:**\n" + "\n".join(admin_satirlari) + "\n\n"

            if admin_izin_satirlari:
                metin += "🔑 **Admin Yetkileri:**\n" + "\n".join(admin_izin_satirlari) + "\n\n"

        # ── KANAL ────────────────────────────────────────────────────
        elif chat.type == 'channel':
            aciklama    = html.escape(chat.description) if getattr(chat, 'description', None) else '—'
            davet_linki = getattr(chat, 'invite_link', None) or '—'
            linked_chat = str(getattr(chat, 'linked_chat_id', None) or '—')
            has_protected = "🔒 Evet" if getattr(chat, 'has_protected_content', False) else "✅ Hayır"
            auto_delete   = f"`{chat.message_auto_delete_time}s`" if getattr(chat, 'message_auto_delete_time', None) else "❌ Kapalı"
            chat_user     = f"@{chat.username}" if chat.username else '—'

            uye_sayisi = '—'
            try:
                uye_sayisi = str(await bot.get_chat_member_count(chat.id))
            except Exception:
                pass

            admin_satirlari = []
            admin_izin_satirlari = []
            admin_sayisi = bot_sayisi = 0
            try:
                adminler = await bot.get_chat_administrators(chat.id)
                admin_sayisi = len(adminler)
                for a in adminler:
                    if a.user.is_bot:
                        bot_sayisi += 1
                for a in adminler[:10]:
                    a_adi = html.escape(a.user.first_name or '?')
                    a_un  = f"@{a.user.username}" if a.user.username else f"#{a.user.id}"
                    rol   = "👑 Kurucu" if a.status == 'creator' else "🛡️ Admin"
                    rozet = " 🤖" if a.user.is_bot else ""
                    admin_satirlari.append(f"  {rol}{rozet} [{a_adi}](tg://user?id={a.user.id}) `{a_un}`")
                    if hasattr(a, 'can_post_messages'):
                        def fp(v): return "✅" if v else "❌"
                        admin_izin_satirlari.append(
                            f"  ┗ [{a_adi}] Post:{fp(a.can_post_messages)} Düzenle:{fp(getattr(a,'can_edit_messages',None))} "
                            f"Sil:{fp(getattr(a,'can_delete_messages',None))} "
                            f"Yönet:{fp(getattr(a,'can_manage_chat',None))}"
                        )
            except Exception:
                pass

            metin += (
                f"🏷️ **Kullanıcı Adı:** `{chat_user}`\n"
                f"👥 **Abone Sayısı:** `{uye_sayisi}`\n"
                f"🛡️ **Admin Sayısı:** `{admin_sayisi}`\n"
                f"🤖 **Bot Sayısı:** `{bot_sayisi}`\n\n"
                f"📝 **Açıklama:** {aciklama}\n"
                f"🔗 **Davet Linki:** {davet_linki}\n"
                f"💬 **Bağlı Grup ID:** `{linked_chat}`\n"
                f"🔒 **İçerik Koruması:** {has_protected}\n"
                f"⏱️ **Otomatik Mesaj Silme:** {auto_delete}\n\n"
            )

            if admin_satirlari:
                metin += "👑 **Adminler:**\n" + "\n".join(admin_satirlari) + "\n\n"

            if admin_izin_satirlari:
                metin += "🔑 **Admin Yetkileri:**\n" + "\n".join(admin_izin_satirlari) + "\n\n"

        metin += "🤖 _AZRxGUARD TG PANELİ GÜVENLİ tarafından sorgulandı_"
        return metin

    except Exception as e:
        logger.error(f"Panel sorgu hatası: {e}")
        return None

async def platform_username_kontrol(username: str) -> str:
    username = username.lstrip('@').strip()
    if not username:
        return "❌ Kullanıcı adı gerekli. Örnek: `maqa_01`"

    platformlar = [
        ("🎵 TikTok",      "https://www.tiktok.com/@{u}"),
        ("📸 Instagram",   "https://www.instagram.com/{u}/"),
        ("▶️ YouTube",     "https://www.youtube.com/@{u}"),
        ("🐙 GitHub",      "https://github.com/{u}"),
        ("🎮 Twitch",      "https://www.twitch.tv/{u}"),
        ("🤖 Reddit",      "https://www.reddit.com/user/{u}/about.json"),
        ("🐦 Twitter/X",   "https://twitter.com/{u}"),
        ("📌 Pinterest",   "https://www.pinterest.com/{u}/"),
        ("👻 Snapchat",    "https://www.snapchat.com/add/{u}"),
        ("🔊 SoundCloud",  "https://soundcloud.com/{u}"),
        ("🎮 Roblox",      "https://www.roblox.com/users/profile?username={u}"),
        ("💬 Telegram",    "https://t.me/{u}"),
        ("🎵 Spotify",     "https://open.spotify.com/user/{u}"),
        ("💼 LinkedIn",    "https://www.linkedin.com/in/{u}/"),
    ]

    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5",
    }

    def kontrol_et(ad, url_tpl):
        url = url_tpl.replace('{u}', username)
        try:
            r = http_requests.get(url, headers=hdrs, timeout=8, allow_redirects=True)
            if r.status_code == 404:
                return ad, False, url
            elif r.status_code == 200:
                return ad, True, url
            else:
                return ad, None, url
        except Exception:
            return ad, None, url

    loop = asyncio.get_event_loop()
    sonuclar = await asyncio.gather(*[
        loop.run_in_executor(None, kontrol_et, ad, url_tpl)
        for ad, url_tpl in platformlar
    ])

    dolu = [(a, u) for a, d, u in sonuclar if d is True]
    bos  = [(a, u) for a, d, u in sonuclar if d is False]
    bilm = [(a, u) for a, d, u in sonuclar if d is None]

    metin = (
        f"🔎 **PLATFORM KULLANICI ADI KONTROLÜ**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔤 **Aranan:** `@{username}`\n"
        f"❌ **Dolu:** `{len(dolu)}` | ✅ **Boşta:** `{len(bos)}` | ⚪ **Bilinmiyor:** `{len(bilm)}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    if dolu:
        metin += "❌ **DOLU PLATFORMLAR:**\n"
        for ad, url in dolu:
            metin += f"  └ {ad} → [profil]({url})\n"
        metin += "\n"
    if bos:
        metin += "✅ **BOŞTA OLAN PLATFORMLAR:**\n"
        for ad, _ in bos:
            metin += f"  └ {ad}\n"
        metin += "\n"
    if bilm:
        metin += "⚪ **KONTROL EDİLEMEYEN:**\n"
        for ad, _ in bilm:
            metin += f"  └ {ad}\n"
        metin += "\n"
    metin += "━━━━━━━━━━━━━━━━━━━━━━\n"
    metin += "🤖 _AZRxGUARD USERNAME HUNTER tarafından kontrol edildi_"
    return metin


# --- ⚡ PRO ARAÇLAR — UTILITY FONKSİYONLARI ---

def guvenli_hesapla(ifade: str) -> str:
    try:
        ifade_clean = ifade.strip().replace('^', '**')
        if len(ifade_clean) > 200:
            return "❌ İfade çok uzun! (max 200 karakter)"
        for forbidden in ['import', 'exec', 'eval', 'open', 'os', 'sys', '__', 'compile']:
            if forbidden in ifade_clean.lower():
                return "❌ Geçersiz ifade!"
        tree = ast.parse(ifade_clean, mode='eval')
        for node in ast.walk(tree):
            if not isinstance(node, (
                ast.Expression, ast.BinOp, ast.UnaryOp,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
                ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.Constant,
                ast.Call, ast.Name, ast.Load, ast.Attribute
            )):
                return "❌ Geçersiz ifade! Sadece matematik işlemleri desteklenir."
        safe_funcs = {
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
            'sqrt': math.sqrt, 'abs': abs, 'log': math.log,
            'log2': math.log2, 'log10': math.log10,
            'pi': math.pi, 'e': math.e,
            'round': round, 'floor': math.floor, 'ceil': math.ceil,
            'pow': pow, 'factorial': math.factorial,
        }
        sonuc = eval(compile(tree, '<expr>', 'eval'), {"__builtins__": {}}, safe_funcs)
        if isinstance(sonuc, float):
            if math.isnan(sonuc):
                return "❌ Tanımsız sonuç (NaN)"
            if math.isinf(sonuc):
                return "❌ Sonsuz sonuç (∞)"
            sonuc_str = f"{sonuc:.10g}"
        else:
            sonuc_str = str(sonuc)
        return (
            f"🧮 **HESAP MAKİNESİ**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 **İfade:** `{html.escape(ifade)}`\n"
            f"📤 **Sonuç:** `{sonuc_str}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _sin, cos, sqrt, log, pi, e, factorial desteklenir_"
        )
    except ZeroDivisionError:
        return "❌ **Sıfıra bölme hatası!**"
    except (ValueError, OverflowError) as e:
        return f"❌ **Matematiksel hata:** `{str(e)[:80]}`"
    except Exception:
        return "❌ **Geçersiz ifade!** Örnek: `2**10` veya `sqrt(144)` veya `sin(pi/2)`"

def hash_uret(metin: str) -> str:
    if not metin.strip():
        return "❌ Metin boş olamaz!"
    if len(metin) > 5000:
        return "❌ Metin çok uzun (max 5000 karakter)"
    veri = metin.encode('utf-8')
    md5_h    = hashlib.md5(veri).hexdigest()
    sha1_h   = hashlib.sha1(veri).hexdigest()
    sha256_h = hashlib.sha256(veri).hexdigest()
    sha512_h = hashlib.sha512(veri).hexdigest()
    ozet = metin[:40] + ('...' if len(metin) > 40 else '')
    return (
        f"🔐 **HASH ÜRETİCİ**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 **Metin:** `{html.escape(ozet)}`\n"
        f"📊 **Uzunluk:** `{len(metin)} karakter`\n\n"
        f"🔸 **MD5:**\n`{md5_h}`\n\n"
        f"🔸 **SHA-1:**\n`{sha1_h}`\n\n"
        f"🔸 **SHA-256:**\n`{sha256_h}`\n\n"
        f"🔸 **SHA-512:**\n`{sha512_h}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _AZRxGUARD Hash Engine_"
    )

def base64_islem(metin: str) -> str:
    metin = metin.strip()
    parts = metin.split(None, 1)
    if len(parts) < 2:
        return "❌ **Format:** `encode metin` veya `decode bWV0aW4=`"
    mod, icerik = parts[0].lower(), parts[1]
    try:
        if mod in ('encode', 'enc', 'e'):
            sonuc = b64lib.b64encode(icerik.encode('utf-8')).decode('ascii')
            return (
                f"🔒 **BASE64 ENCODE**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📥 **Giriş:** `{html.escape(icerik[:100])}`\n\n"
                f"📤 **Sonuç:**\n`{sonuc}`"
            )
        elif mod in ('decode', 'dec', 'd'):
            padding = 4 - len(icerik) % 4
            if padding != 4:
                icerik += '=' * padding
            sonuc = b64lib.b64decode(icerik).decode('utf-8', errors='replace')
            return (
                f"🔓 **BASE64 DECODE**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📥 **Giriş:** `{icerik[:80]}`\n\n"
                f"📤 **Sonuç:**\n`{html.escape(sonuc[:500])}`"
            )
        else:
            return "❌ **Format:** `encode metin` veya `decode bWV0aW4=`"
    except Exception as e:
        return f"❌ **Hata:** `{str(e)[:100]}`"

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
        semboller = '!@#$%^&*()-_=+[]{}|;:,.<>?'
        karakterler += semboller
        zorunlu.append(random.choice(semboller))
    kalan = [random.choice(karakterler) for _ in range(uzunluk - len(zorunlu))]
    sifre_listesi = zorunlu + kalan
    random.shuffle(sifre_listesi)
    return ''.join(sifre_listesi)

async def wikipedia_ara(sorgu: str, lang: str = 'tr') -> str:
    try:
        wiki_lang = {'tr': 'tr', 'az': 'az', 'ru': 'ru', 'en': 'en', 'de': 'de', 'ka': 'ka'}.get(lang, 'tr')
        loop = asyncio.get_event_loop()
        def fetch():
            search_url = f"https://{wiki_lang}.wikipedia.org/api/rest_v1/page/summary/{sorgu.replace(' ', '_')}"
            r = http_requests.get(search_url, timeout=10, headers={"User-Agent": "AZRxGUARD-Bot/1.0"})
            if r.status_code == 200:
                return r.json()
            # Fallback to English
            r2 = http_requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{sorgu.replace(' ', '_')}", timeout=10, headers={"User-Agent": "AZRxGUARD-Bot/1.0"})
            if r2.status_code == 200:
                return r2.json()
            return None
        data = await loop.run_in_executor(None, fetch)
        if not data or data.get('type') == 'disambiguation':
            return f"❌ `{html.escape(sorgu)}` için Wikipedia'da sonuç bulunamadı.\n\n💡 Farklı kelimeler deneyin veya İngilizce yazın."
        baslik = data.get('title', sorgu)
        ozet   = data.get('extract', '—')
        wiki_url = data.get('content_urls', {}).get('desktop', {}).get('page', '')
        if len(ozet) > 600:
            ozet = ozet[:600] + '...'
        return (
            f"🌐 **WIKIPEDIA**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📖 **{html.escape(baslik)}**\n\n"
            f"{html.escape(ozet)}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 [Tam makale için tıkla]({wiki_url})"
        )
    except Exception as e:
        logger.error(f"Wikipedia hatası: {e}")
        return "❌ Wikipedia'ya ulaşılamadı. Lütfen sonra tekrar dene."

# ─── NOT DEFTERİ (kalıcı dosya depolama) ───────────────────────────────────
NOTES_FILE = 'notes_data.json'

def not_yukle(user_id: int) -> list:
    try:
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get(str(user_id), [])
    except Exception:
        return []

def not_kaydet(user_id: int, notlar: list):
    try:
        try:
            with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
        data[str(user_id)] = notlar
        with open(NOTES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Not kaydetme hatası: {e}")

# ─── GÜNÜN SÖZÜ ──────────────────────────────────────────────────────────────
GUNUN_SOZLERI = [
    "💡 _\"Bugün yapabileceğini yarına bırakma.\"_\n— Benjamin Franklin",
    "💡 _\"Başarı, her gün tekrar edilen küçük çabaların toplamıdır.\"_\n— Robert Collier",
    "💡 _\"Düşündüğün gibi yaşamazsan, yaşadığın gibi düşünmeye başlarsın.\"_\n— Paul Bourget",
    "💡 _\"Zorluklar olmadan büyüme olmaz.\"_\n— Anonim",
    "💡 _\"Hedefsiz bir gemi, her rüzgarı karşı rüzgar sayar.\"_\n— Montaigne",
    "💡 _\"Başarısızlık, başarıya giden yolun taşlarından biridir.\"_\n— Anonim",
    "💡 _\"Önce kendin değiş, sonra dünyayı değiştirmeyi dene.\"_\n— Mahatma Gandhi",
    "💡 _\"Hayatın en büyük mirası umuttur.\"_\n— Victor Hugo",
    "💡 _\"Dün tarihtir, yarın sırdır, bugün hediyedir.\"_\n— Anonim",
    "💡 _\"Bir yolculuk, tek bir adımla başlar.\"_\n— Lao Tzu",
    "💡 _\"İmkânsız, büyük işler yapmaya karar vermeyenler için vardır.\"_\n— Napoleon Bonaparte",
    "💡 _\"Karanlıkta bir mum yakmak, karanlığa sövmekten iyidir.\"_\n— Konfüçyüs",
    "💡 _\"Harekete geç. İlham yolda seni bulur.\"_\n— Jack London",
    "💡 _\"Bir insanın en büyük düşmanı cehalettir.\"_\n— Anonim",
    "💡 _\"Zamanın değerini bil — her saniye geri gelmez.\"_\n— Anonim",
    "💡 _\"Azmin önünde her engel eğilir.\"_\n— Anonim",
    "💡 _\"Bilgi güçtür.\"_\n— Francis Bacon",
    "💡 _\"İyilik yap, suya at — balık bilmese de Allah bilir.\"_\n— Türk Atasözü",
    "💡 _\"Qüvvət bilikdədir.\"_\n— Anonim",
    "💡 _\"Hər gecənin bir sabahı var.\"_\n— Azərbaycan atalar sözü",
    "💡 _\"Səbrli olan, muradına çatar.\"_\n— Azərbaycan atalar sözü",
    "💡 _\"Достаточно сделать один шаг — остальное сложится само.\"_\n— Anonim",
    "💡 _\"Не бойся медленно идти — бойся стоять на месте.\"_\n— Китайская мудрость",
    "💡 _\"The secret of getting ahead is getting started.\"_\n— Mark Twain",
    "💡 _\"In the middle of every difficulty lies opportunity.\"_\n— Albert Einstein",
    "💡 _\"მარტო მოიყვანე ცხენი წყლამდე, სასმელს ვეღარ მოაქცევ.\"_\n— ქართული სიბრძნე",
    "💡 _\"Hardship often prepares an ordinary person for an extraordinary destiny.\"_\n— C.S. Lewis",
    "💡 _\"Do not watch the clock. Do what it does — keep going.\"_\n— Sam Levenson",
    "💡 _\"Eğer hayaller görmüyorsan, uykun değil, gözlerin kapalıdır.\"_\n— Anonim",
    "💡 _\"Kısmet bekleyene değil, çalışana güler.\"_\n— Türk Atasözü",
]

def gunun_sozu_getir() -> str:
    return random.choice(GUNUN_SOZLERI)

# ─── BİRİM ÇEVİRİCİ ──────────────────────────────────────────────────────────
BIRIM_TABLOLARI = {
    'sicaklik': (
        "🌡️ **SICAKLIK ÇEVİRİCİSİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "| °C | °F | K |\n"
        "|:---:|:---:|:---:|\n"
        "| -40 | -40 | 233 |\n"
        "| 0 | 32 | 273 |\n"
        "| 10 | 50 | 283 |\n"
        "| 20 | 68 | 293 |\n"
        "| 25 | 77 | 298 |\n"
        "| 30 | 86 | 303 |\n"
        "| 37 | 99 | 310 |\n"
        "| 40 | 104 | 313 |\n"
        "| 100 | 212 | 373 |\n\n"
        "📐 _Formül: °F = °C×1.8+32 | K = °C+273_"
    ),
    'uzunluk': (
        "📏 **UZUNLUK ÇEVİRİCİSİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "| km | mil | m | ft |\n"
        "|:---:|:---:|:---:|:---:|\n"
        "| 1 | 0.62 | 1000 | 3281 |\n"
        "| 5 | 3.1 | 5000 | 16404 |\n"
        "| 10 | 6.2 | 10000 | 32808 |\n"
        "| 50 | 31 | 50000 | 164042 |\n"
        "| 100 | 62 | 100000 | 328084 |\n\n"
        "| cm | inch | mm |\n"
        "|:---:|:---:|:---:|\n"
        "| 1 | 0.39 | 10 |\n"
        "| 10 | 3.94 | 100 |\n"
        "| 30 | 11.81 | 300 |\n"
        "| 100 | 39.37 | 1000 |\n\n"
        "📐 _1 mil = 1.609 km | 1 ft = 30.48 cm | 1 inch = 2.54 cm_"
    ),
    'agirlik': (
        "⚖️ **AĞIRLIK ÇEVİRİCİSİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "| kg | lb | g | oz |\n"
        "|:---:|:---:|:---:|:---:|\n"
        "| 0.5 | 1.1 | 500 | 17.6 |\n"
        "| 1 | 2.2 | 1000 | 35.3 |\n"
        "| 5 | 11 | 5000 | 176 |\n"
        "| 10 | 22 | 10000 | 353 |\n"
        "| 50 | 110 | 50000 | 1764 |\n"
        "| 70 | 154 | 70000 | 2469 |\n"
        "| 100 | 220 | 100000 | 3527 |\n\n"
        "📐 _1 kg = 2.205 lb | 1 lb = 453.6 g | 1 oz = 28.35 g_"
    ),
    'hiz': (
        "🚗 **HIZ ÇEVİRİCİSİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "| km/s | mil/s | m/s | knot |\n"
        "|:---:|:---:|:---:|:---:|\n"
        "| 30 | 18.6 | 8.3 | 16.2 |\n"
        "| 50 | 31.1 | 13.9 | 27.0 |\n"
        "| 60 | 37.3 | 16.7 | 32.4 |\n"
        "| 80 | 49.7 | 22.2 | 43.2 |\n"
        "| 100 | 62.1 | 27.8 | 54.0 |\n"
        "| 120 | 74.6 | 33.3 | 64.8 |\n"
        "| 300 | 186 | 83.3 | 162 |\n\n"
        "📐 _1 km/s = 0.621 mph | 1 knot = 1.852 km/s_"
    ),
}

# ─── ŞANS TOPU ────────────────────────────────────────────────────────────────
SANS_CEVAPLARI = [
    ("✅", "Kesinlikle evet!"),
    ("✅", "Evet, öyle görünüyor."),
    ("✅", "Bence evet!"),
    ("✅", "Şüphesiz!"),
    ("✅", "Evet, güvenebilirsin."),
    ("✅", "Sinyaller evet diyor."),
    ("🤔", "Şu an belirsiz, tekrar sor."),
    ("🤔", "Cevap bulanık — biraz bekle."),
    ("🤔", "Odaklan ve tekrar sor."),
    ("🤔", "Şimdi tahmin edemiyorum."),
    ("❌", "Pek öyle görünmüyor."),
    ("❌", "Cevabım hayır."),
    ("❌", "Kesinlikle hayır!"),
    ("❌", "Beklentini düşür."),
    ("❌", "Şüpheli görünüyor."),
    ("❌", "Hayır, bu sefer olmaz."),
]

def sans_cevap_getir() -> str:
    emoji, cevap = random.choice(SANS_CEVAPLARI)
    return (
        f"🎱 **ŞANS TOPU**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**{emoji} {cevap}**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Sorunuzu düşünün ve tekrar basın._"
    )

async def hava_durumu_getir(sehir: str) -> str:
    try:
        sehir_enc = sehir.strip().replace(' ', '+')
        url = f"https://wttr.in/{sehir_enc}?format=j1"
        loop = asyncio.get_event_loop()
        def fetch():
            r = http_requests.get(url, timeout=10, headers={"User-Agent": "AZRxGUARD-Bot/2.0"})
            if r.status_code == 200:
                return r.json()
            return None
        data = await loop.run_in_executor(None, fetch)
        if not data or 'current_condition' not in data:
            return f"❌ `{html.escape(sehir)}` için hava durumu bulunamadı!\n💡 Şehri İngilizce yaz: `Istanbul`, `Baku`, `Moscow`"
        current  = data['current_condition'][0]
        nearest  = data.get('nearest_area', [{}])[0]
        area_val = nearest.get('areaName', [{'value': sehir}])[0]['value']
        country  = nearest.get('country', [{'value': ''}])[0]['value']
        temp_c      = current['temp_C']
        feels_like  = current['FeelsLikeC']
        humidity    = current['humidity']
        windspeed   = current['windspeedKmph']
        desc        = current.get('weatherDesc', [{'value': '—'}])[0]['value']
        uv          = current.get('uvIndex', '—')
        visibility  = current.get('visibility', '—')
        pressure    = current.get('pressure', '—')
        dl = desc.lower()
        if any(w in dl for w in ['sunny', 'clear']):          icon = '☀️'
        elif any(w in dl for w in ['partly']):                icon = '⛅'
        elif any(w in dl for w in ['overcast', 'cloud']):     icon = '☁️'
        elif any(w in dl for w in ['drizzle', 'shower']):     icon = '🌦️'
        elif any(w in dl for w in ['rain']):                   icon = '🌧️'
        elif any(w in dl for w in ['snow', 'blizzard']):      icon = '❄️'
        elif any(w in dl for w in ['thunder', 'storm']):      icon = '⛈️'
        elif any(w in dl for w in ['fog', 'mist', 'haze']):   icon = '🌫️'
        else:                                                   icon = '🌤️'
        loc = area_val + (f", {country}" if country else "")
        return (
            f"{icon} **HAVA DURUMU**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📍 **Konum:** {loc}\n\n"
            f"🌡️ **Sıcaklık:** `{temp_c}°C`\n"
            f"🤔 **Hissedilen:** `{feels_like}°C`\n"
            f"💧 **Nem:** `%{humidity}`\n"
            f"💨 **Rüzgar:** `{windspeed} km/h`\n"
            f"🌡 **Basınç:** `{pressure} hPa`\n"
            f"☁️ **Durum:** {desc}\n"
            f"🌞 **UV Endeksi:** `{uv}`\n"
            f"👁️ **Görüş:** `{visibility} km`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _AZRxGUARD Hava Servisi_"
        )
    except Exception as e:
        logger.error(f"Hava durumu hatası: {e}")
        return "❌ Hava servisi şu an erişilemiyor. Lütfen şehri İngilizce yaz.\nÖrnek: `Istanbul`, `Baku`, `Moscow`"

async def doviz_cevir(metin: str) -> str:
    try:
        parts = metin.strip().upper().split()
        if len(parts) < 3:
            return "❌ **Format:** `100 USD TRY`\nÖrnek: `50 EUR USD` veya `1000 TRY GEL`"
        try:
            miktar = float(parts[0].replace(',', '.'))
        except ValueError:
            return "❌ **Geçersiz miktar!** Örnek: `100 USD TRY`"
        kfrom, kto = parts[1], parts[2]
        loop = asyncio.get_event_loop()
        def fetch():
            url = f"https://open.er-api.com/v6/latest/{kfrom}"
            r = http_requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        data = await loop.run_in_executor(None, fetch)
        if not data or data.get('result') != 'success':
            return (
                f"❌ `{kfrom}` para birimi bulunamadı veya servis yanıt vermedi!\n\n"
                f"💡 Desteklenen para birimleri: USD, EUR, TRY, GBP, RUB, AZN, GEL, AED, SAR, KZT, UAH ve daha fazlası."
            )
        rates = data.get('rates', {})
        sonuc = rates.get(kto)
        if sonuc is None:
            return f"❌ `{kto}` hedef para birimi bulunamadı!"
        sonuc_miktar = miktar * sonuc
        tarih = data.get('time_last_update_utc', '—')[:16]
        return (
            f"💱 **DÖVİZ ÇEVİRİCİ**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 **Giriş:** `{miktar:,.2f} {kfrom}`\n"
            f"📤 **Sonuç:** `{sonuc_miktar:,.4f} {kto}`\n"
            f"📊 **Kur:** `1 {kfrom} = {sonuc:,.4f} {kto}`\n\n"
            f"📅 **Güncelleme:** `{tarih}`\n"
            f"🌐 **Kaynak:** Open Exchange Rates\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _AZRxGUARD Döviz Servisi_"
        )
    except Exception as e:
        logger.error(f"Döviz hatası: {e}")
        return "❌ Döviz servisi şu an erişilemiyor. Lütfen sonra tekrar dene."

def dunya_saati() -> str:
    sehirler = [
        # Gürcistan
        ("🇬🇪 Tiflis",         datetime.timezone(datetime.timedelta(hours=4))),
        # Azerbaycan
        ("🇦🇿 Bakü",           datetime.timezone(datetime.timedelta(hours=4))),
        # Türkiye
        ("🇹🇷 İstanbul",       datetime.timezone(datetime.timedelta(hours=3))),
        # Rusya
        ("🇷🇺 Moskova",        datetime.timezone(datetime.timedelta(hours=3))),
        # Müslüman ülkeler
        ("🇸🇦 Riyad",          datetime.timezone(datetime.timedelta(hours=3))),
        ("🇮🇶 Bağdat",         datetime.timezone(datetime.timedelta(hours=3))),
        ("🇯🇴 Amman",          datetime.timezone(datetime.timedelta(hours=3))),
        ("🇪🇬 Kahire",         datetime.timezone(datetime.timedelta(hours=3))),
        ("🇮🇷 Tahran",         datetime.timezone(datetime.timedelta(hours=3, minutes=30))),
        ("🇦🇪 Dubai",          datetime.timezone(datetime.timedelta(hours=4))),
        ("🇵🇰 Karaçi",         datetime.timezone(datetime.timedelta(hours=5))),
        ("🇰🇿 Astana",         datetime.timezone(datetime.timedelta(hours=5))),
        ("🇺🇿 Taşkent",        datetime.timezone(datetime.timedelta(hours=5))),
        ("🇮🇩 Cakarta",        datetime.timezone(datetime.timedelta(hours=7))),
        ("🇲🇾 Kuala Lumpur",   datetime.timezone(datetime.timedelta(hours=8))),
        ("🇲🇦 Kazablanka",     datetime.timezone(datetime.timedelta(hours=1))),
        # Avrupa
        ("🇩🇪 Berlin",         datetime.timezone(datetime.timedelta(hours=2))),
        ("🇬🇧 Londra",         datetime.timezone(datetime.timedelta(hours=1))),
        # Amerika
        ("🇧🇷 São Paulo",      datetime.timezone(datetime.timedelta(hours=-3))),
        ("🇺🇸 New York",       datetime.timezone(datetime.timedelta(hours=-4))),
        ("🇺🇸 Los Angeles",    datetime.timezone(datetime.timedelta(hours=-7))),
        # Asya
        ("🇮🇳 Mumbai",         datetime.timezone(datetime.timedelta(hours=5, minutes=30))),
        ("🇨🇳 Pekin",          datetime.timezone(datetime.timedelta(hours=8))),
        ("🇯🇵 Tokyo",          datetime.timezone(datetime.timedelta(hours=9))),
    ]
    simdi_utc = datetime.datetime.now(datetime.timezone.utc)
    metin = f"🕐 **DÜNYA SAATİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    metin += f"🌐 **UTC:** `{simdi_utc.strftime('%H:%M')}` — `{simdi_utc.strftime('%d.%m.%Y')}`\n\n"
    for isim, tz in sehirler:
        simdi = datetime.datetime.now(tz)
        metin += f"{isim}: `{simdi.strftime('%H:%M')}` _{simdi.strftime('%d.%m')}_\n"
    metin += "\n━━━━━━━━━━━━━━━━━━━━━━\n🤖 _AZRxGUARD Zaman Servisi_"
    return metin

# --- 🌍 ÜLKE / ŞEHİR / RAYON / KÖY HİYERARŞİSİ ---
# Yapı: { ülke_kodu: { flag, name, sehirler: { şehir: { rayon: [köy...] } }, koyler: [...] } }
ULKE_HIYERARSI = {
    'ge': {
        'flag': '🇬🇪', 'name': 'Gürcistan',
        'sehirler': {
            'Tbilisi': {
                'Mtatsminda': ['Mtatsminda', 'Betlemi', 'Sololaki', 'Tabori', 'Tsavkisi', 'Kojori'],
                'Vake': ['Vake Park', 'Makhata', 'Kiketi', 'Saguramo', 'Shindisi'],
                'Saburtalo': ['Saburtalo', 'Mukhiani', 'Delisi', 'Nutsubidze', 'Vaziani', 'Digomi'],
                'Krtsanisi': ['Krtsanisi', 'Ortachala', 'Isani', 'Ponichala', 'Lilo'],
                'Isani': ['Isani', 'Varketili', 'Samgori', 'Norio', 'Eldari'],
                'Samgori': ['Navtlugi', 'Ortachala', 'Samgori', 'Nosiri', 'Soghanlug', 'Akhali Samgori'],
                'Gldani': ['Gldani', 'Temka', 'Dighomi', 'Sanzona', 'Mukhad', 'Zahesi'],
                'Didube': ['Didube', 'Chughureti', 'Abanotubani', 'Kala', 'Old Town'],
                'Chughureti': ['Chughureti', 'Kukia', 'Avlabari', 'Metekhi', 'Isani'],
                'Nadzaladevi': ['Nadzaladevi', 'Ghrmaghele', 'Ponichala', 'Didi Dighomi', 'Liliani'],
            },
            'Batumi': {
                'Batumi Merkez': ['Batumi', 'Makhinjauri', 'Tsikhisdziri', 'Chakvi', 'Kobuleti'],
                'Khelvachauri': ['Khelvachauri', 'Gonio', 'Sarpi', 'Kvariati', 'Tsikhisdziri'],
                'Keda': ['Keda', 'Dandalo', 'Zeda Keda', 'Tcherencha', 'Bzhutubani'],
                'Shuakhevi': ['Shuakhevi', 'Zeda Shuakhevi', 'Beshumi', 'Zekari'],
                'Khulo': ['Khulo', 'Zeda Khulo', 'Beshumi', 'Shuakhevi', 'Chitakhevi'],
                'Kobuleti': ['Kobuleti', 'Ureki', 'Grigoleti', 'Shekvetili', 'Naghvarevi'],
            },
            'Kutaisi': {
                'Kutaisi Merkez': ['Kutaisi', 'Rioni', 'Tskaltubo', 'Gori-Tskali', 'Sveti'],
                'Baghdati': ['Baghdati', 'Vani', 'Dimisi', 'Katskhuri', 'Kveda Shuakhevi'],
                'Zestaponi': ['Zestaponi', 'Shorapani', 'Kvishkheti', 'Terjola', 'Khoni'],
                'Sachkhere': ['Sachkhere', 'Chiatura', 'Sakara', 'Sori'],
                'Tkibuli': ['Tkibuli', 'Rikoti', 'Shaori', 'Tvishi'],
                'Kharagauli': ['Kharagauli', 'Sviri', 'Zekari', 'Khargheti'],
                'Samtredia': ['Samtredia', 'Abasha', 'Shuakhevi', 'Khoni'],
            },
            'Rustavi': {
                'Rustavi Merkez': ['Rustavi', 'Kvemo Rustavi', 'Msakhuri', 'Krtsanisi'],
                'Gardabani': ['Gardabani', 'Ponichala', 'Soganluq', 'Agstafa', 'Vaziani'],
                'Marneuli': ['Marneuli', 'Sadaxlı', 'Qızılajlo', 'Muğanlı', 'Sabirkənd', 'Kosalar', 'Ağcabədi', 'Baydar', 'Tamarisi', 'Şülavəri', 'Dalis Mta', 'Karakilis', 'Algeti', 'Ulaşhlo', 'Kasumlo'],
                'Bolnisi': ['Bolnisi', 'Dmanisi', 'Kazreti', 'Dashbulagi', 'Başkənd', 'Sarvan'],
                'Tetritskaro': ['Tetritskaro', 'Algeti', 'Kldeisi', 'Manglisi', 'Tsalka yolu'],
                'Tsalka': ['Tsalka', 'Bediani', 'Dariali', 'Trialeti', 'Patara Tsalka'],
            },
            'Marneuli': {
                'Marneuli Şəhər': ['Marneuli', 'Böyük Marneuli', 'Kiçik Marneuli', 'Marneulis Sənaye'],
                'Sadaxlı': ['Sadaxlı', 'Ağbulaq', 'Qaçağan', 'Corablar', 'Hacıkənd'],
                'Ulaşhlo-Kasumlo': ['Ulaşhlo', 'Kasumlo', 'Qızılajlo', 'Kepenekçi', 'Avranlo'],
                'Muğanlı-Sabirkənd': ['Muğanlı', 'Sabirkənd', 'Kosalar', 'Ağcabədi', 'Bəhrəmtəpə'],
                'Baydar-Tamarisi': ['Baydar', 'Tamarisi', 'Şülavəri', 'Dalis Mta', 'Algeti'],
                'Karakilis-Bolnisi': ['Karakilis', 'Bolnisi Khevi', 'Orjonikidze', 'Sarvan'],
            },
            'Gardabani': {
                'Gardabani Merkez': ['Gardabani', 'Rustavi', 'Ponichala', 'Soğanlıq'],
                'Vaziani': ['Vaziani', 'Norio', 'Eldari', 'Samgori', 'Akhali Samgori'],
                'Krasnogorsk': ['Krasnogorsk', 'Tetri Tskaro', 'Nazarlevani', 'Patardzeuli'],
            },
            'Gori': {
                'Gori Merkez': ['Gori', 'Akhaldaba', 'Kvakhvreli', 'Variani', 'Skra'],
                'Kareli': ['Kareli', 'Ruisi', 'Ateni', 'Surami', 'Agara'],
                'Kaspi': ['Kaspi', 'Agara', 'Tsinari', 'Skulani', 'Khashuri'],
                'Borjomi': ['Borjomi', 'Bakuriani', 'Likani', 'Tsagveri', 'Abastumani'],
                'Khashuri': ['Khashuri', 'Surami', 'Kvishkheti', 'Agara', 'Tsikhisjvari'],
            },
            'Borjomi': {
                'Borjomi Merkez': ['Borjomi', 'Likani', 'Tsagveri', 'Abastumani', 'Vale'],
                'Bakuriani': ['Bakuriani', 'Kokhta', 'Tba', 'Didveli', 'Mitarbi'],
                'Akhaltsikhe': ['Akhaltsikhe', 'Aspindza', 'Adigeni', 'Zarzma', 'Vale'],
            },
            'Zugdidi': {
                'Zugdidi Merkez': ['Zugdidi', 'Jvari', 'Anaklia', 'Ganmukhuri', 'Ingiri'],
                'Senaki': ['Senaki', 'Abasha', 'Kortskheli', 'Orsantia'],
                'Mestia-Svaneti': ['Mestia', 'Ushguli', 'Becho', 'Latali', 'Lentekhi', 'Mulakhi'],
                'Martvili': ['Martvili', 'Khobi', 'Khoni', 'Salkhino', 'Tsalenjikha'],
            },
            'Telavi': {
                'Telavi Merkez': ['Telavi', 'Ikalto', 'Kondoli', 'Akura', 'Napareuli'],
                'Gurjaani': ['Gurjaani', 'Velistsikhe', 'Ujarma', 'Chabukiauri', 'Bakurtsikhe'],
                'Sighnaghi': ['Sighnaghi', 'Bodbe', 'Tsnori', 'Anaga', 'Vakiri'],
                'Lagodekhi': ['Lagodekhi', 'Ninotsminda', 'Khornabuji', 'Shroma', 'Matani'],
                'Kvareli': ['Kvareli', 'Alvani', 'Eniseli', 'Shilda', 'Kabali'],
                'Akhmeta': ['Akhmeta', 'Omalo', 'Batsara', 'Tusheti', 'Shuakhevi'],
                'Dedoplistskaro': ['Dedoplistskaro', 'Udabno', 'Shilda', 'Samreklo', 'Vashlovani'],
            },
            'Poti': {
                'Poti Merkez': ['Poti', 'Maltakva', 'Shekvetili', 'Ureki', 'Grigoleti'],
            },
            'Mtskheta': {
                'Mtskheta Merkez': ['Mtskheta', 'Svetitskhoveli', 'Jvari', 'Shio-Mgvime'],
                'Dusheti': ['Dusheti', 'Ananuri', 'Zhinvali', 'Pasanauri', 'Gudauri'],
                'Stepantsminda': ['Stepantsminda', 'Kazbegi', 'Gergeti', 'Truso', 'Dariali'],
                'Tianeti': ['Tianeti', 'Sioni', 'Khevsureti', 'Barisakho', 'Shuakhevi'],
            },
            'Akhaltsikhe': {
                'Akhaltsikhe': ['Akhaltsikhe', 'Aspindza', 'Adigeni', 'Zarzma', 'Vale'],
                'Akhalkalaki': ['Akhalkalaki', 'Ninotsminda', 'Bavra', 'Kartsakhi', 'Gandzani'],
                'Adygeni': ['Adygeni', 'Zarzma', 'Chule', 'Vale', 'Nakalakevi'],
            },
            'Ozurgeti': {
                'Ozurgeti Merkez': ['Ozurgeti', 'Chokhatauri', 'Lanchkhuti', 'Nasakirali'],
                'Lanchkhuti': ['Lanchkhuti', 'Shekvetili', 'Ureki', 'Naghvarevi'],
            },
            'Ambrolauri': {
                'Ambrolauri Merkez': ['Ambrolauri', 'Oni', 'Tvishi', 'Utsera', 'Shovi'],
                'Racha-Lechkhumi': ['Racha', 'Lentekhi', 'Khvamli', 'Alpana'],
            },
        },
        'koyler': {
            'Marneuli Rayonu 🇦🇿': [
                'Marneuli', 'Sadaxlı', 'Ulaşhlo', 'Kasumlo', 'Ağbulaq',
                'Qızılajlo', 'Qaçağan', 'Muğanlı', 'Sabirkənd', 'Kosalar',
                'Ağcabədi', 'Baydar', 'Tamarisi', 'Şülavəri', 'Dalis Mta',
                'Karakilis', 'Algeti', 'Bolnisi Khevi', 'Avranlo', 'Kepenekçi',
                'Corablar', 'Hacıkənd', 'Bəhrəmtəpə', 'Sarvan', 'Orjonikidze',
            ],
            'Gardabani Rayonu 🇦🇿': [
                'Gardabani', 'Rustavi', 'Soğanlıq', 'Ponichala', 'Krasnogorsk',
                'Akhali Samgori', 'Norio', 'Eldari', 'Tetri Tskaro', 'Nazarlevani',
                'Vaziani', 'Patardzeuli', 'Kvemo Ponichala', 'Samgori',
            ],
            'Bolnisi Rayonu 🇦🇿': [
                'Bolnisi', 'Dmanisi', 'Kazreti', 'Dashbulagi', 'Başkənd',
                'Sarvan', 'Moliti', 'Qızılhacılı', 'Kvemo Bolnisi', 'Karatakla',
                'Sioni', 'Klde', 'Tambovka',
            ],
            'Tetritskaro Rayonu': [
                'Tetritskaro', 'Algeti', 'Kldeisi', 'Manglisi', 'Trialeti',
                'Tsalka yolu', 'Bershveti', 'Khashuri',
            ],
            'Tsalka Rayonu': [
                'Tsalka', 'Bediani', 'Dariali', 'Trialeti', 'Patara Tsalka',
                'Gantiadi', 'Ktsia', 'Kumisi',
            ],
            'Akhalkalaki Rayonu 🇦🇿': [
                'Akhalkalaki', 'Ninotsminda', 'Bavra', 'Kartsakhi',
                'Gandzani', 'Arjevaniskhevi', 'Sameba',
            ],
            'Borjomi Rayonu': [
                'Borjomi', 'Bakuriani', 'Likani', 'Tsagveri', 'Abastumani',
                'Kodistskali', 'Patara Borjomi', 'Tabatskuri',
            ],
        },
    },
    'tr': {
        'flag': '🇹🇷', 'name': 'Türkiye',
        'sehirler': {
            'Istanbul': {
                'Avrupa Yakası': ['Beşiktaş', 'Beyoğlu', 'Fatih', 'Bakırköy', 'Şişli', 'Sarıyer', 'Eyüp', 'Bağcılar', 'Bahçelievler', 'Avcılar', 'Beylikdüzü', 'Esenyurt', 'Küçükçekmece', 'Büyükçekmece', 'Arnavutköy', 'Başakşehir'],
                'Anadolu Yakası': ['Kadıköy', 'Üsküdar', 'Ataşehir', 'Maltepe', 'Kartal', 'Pendik', 'Tuzla', 'Ümraniye', 'Beykoz', 'Sancaktepe', 'Adalar'],
            },
            'Ankara': {
                'Merkez': ['Çankaya', 'Keçiören', 'Mamak', 'Yenimahalle', 'Altındağ', 'Etimesgut', 'Sincan', 'Gölbaşı', 'Pursaklar'],
            },
            'Izmir': {
                'Merkez': ['Konak', 'Karşıyaka', 'Bornova', 'Buca', 'Çiğli', 'Balçova', 'Narlıdere', 'Gaziemir', 'Karabağlar'],
            },
            'Antalya': {
                'Merkez': ['Muratpaşa', 'Konyaaltı', 'Kepez', 'Alanya', 'Manavgat', 'Kaş', 'Kemer', 'Side', 'Belek'],
            },
            'Trabzon': {
                'Merkez': ['Merkez', 'Akçaabat', 'Araklı', 'Vakfıkebir', 'Of', 'Çaykara'],
            },
            'Bursa': {
                'Merkez': ['Osmangazi', 'Nilüfer', 'Yıldırım', 'Gemlik', 'İnegöl', 'Mudanya', 'Orhangazi'],
            },
            'Gaziantep': {
                'Merkez': ['Şahinbey', 'Şehitkamil', 'Islahiye', 'Nizip', 'Karkamış'],
            },
            'Bodrum': {
                'Merkez': ['Bodrum', 'Turgutreis', 'Gümbet', 'Yalıkavak', 'Torba', 'Bitez'],
            },
        },
        'koyler': ['Pamukkale', 'Goreme', 'Avanos', 'Urgup', 'Efes', 'Marmaris', 'Fethiye', 'Kas', 'Oludeniz', 'Cesme', 'Kusadasi', 'Canakkale', 'Safranbolu', 'Amasra'],
    },
    'az': {
        'flag': '🇦🇿', 'name': 'Azerbaycan',
        'sehirler': {
            'Baku': {
                'Merkez': ['Nizami', 'Sabail', 'Narimanov', 'Binagadi', 'Nasimi', 'Sabunchu'],
                'Abşeron': ['Sumqayit', 'Mashtaga', 'Nardaran', 'Balakhani', 'Ramana', 'Zabrat'],
                'Surakhani': ['Surakhani', 'Hazi Aslanov', 'Bilajer', 'Saray'],
                'Khazar': ['Novkhani', 'Buzovna', 'Nardaran', 'Bilgah', 'Pirshagi'],
            },
            'Ganja': {
                'Merkez': ['Ganja', 'Khanlar', 'Kapaz', 'Samux'],
            },
            'Nakhchivan': {
                'Merkez': ['Nakhchivan', 'Julfa', 'Ordubad', 'Sharur', 'Babek'],
            },
            'Lankaran': {
                'Merkez': ['Lankaran', 'Astara', 'Lerik', 'Masalli', 'Jalilabad'],
            },
            'Shaki': {
                'Merkez': ['Shaki', 'Gabala', 'Qax', 'Oguz', 'Zagatala'],
            },
            'Quba': {
                'Merkez': ['Quba', 'Qusar', 'Khachmaz', 'Siazan', 'Shabran'],
            },
        },
        'koyler': ['Lahic', 'Xinaliq', 'Ilisu', 'Gatiq', 'Gobustan', 'Laza', 'Khizi', 'Ismailli', 'Lerikend', 'Ivanovka'],
    },
    'ru': {
        'flag': '🇷🇺', 'name': 'Rusya',
        'sehirler': {
            'Moscow': {
                'Merkez': ['Tverskoy', 'Arbat', 'Presnensky', 'Khamovniki', 'Yakimanka'],
                'Kuzey': ['Dmitrovsky', 'Korovino', 'Hovrino', 'Levoberezhny'],
                'Güney': ['Tsaritsyno', 'Biryulevo', 'Orekhovo-Borisovo'],
                'Doğu': ['Sokolniki', 'Izmailovo', 'Vostochny'],
            },
            'Saint Petersburg': {
                'Merkez': ['Admiralteysky', 'Petrogradsky', 'Vasileostrovsky', 'Tsentralny'],
                'Diğer': ['Peterhof', 'Pushkin', 'Kronshtadt', 'Kolpino'],
            },
            'Kazan': {
                'Merkez': ['Vakhitovsky', 'Sovetsky', 'Privolzhsky', 'Aviastroitelny'],
            },
            'Sochi': {
                'Merkez': ['Tsentralny', 'Adler', 'Khosta', 'Lazarevsky', 'Krasnaya Polyana'],
            },
            'Krasnodar': {
                'Merkez': ['Tsentralny', 'Prikubansky', 'Karasunsky'],
            },
        },
        'koyler': ['Suzdal', 'Sergiyev Posad', 'Yaroslavl', 'Pskov', 'Veliky Novgorod', 'Irkutsk', 'Murmansk', 'Vladivostok'],
    },
    'sa': {
        'flag': '🇸🇦', 'name': 'Suudi Arabistan',
        'sehirler': {
            'Riyadh': {'Merkez': ['Al Olaya', 'Al Malaz', 'Al Muraba', 'Diriyah', 'Al Nakheel']},
            'Jeddah': {'Merkez': ['Al Balad', 'Al Hamra', 'Al Rawdah', 'Al Safa', 'Al Zahra']},
            'Mecca': {'Merkez': ['Haram', 'Ajyad', 'Al Aziziyah', 'Mina', 'Arafat', 'Muzdalifah']},
            'Medina': {'Merkez': ['Al Haram', 'Quba', 'Al Anbariyah', 'Al Aziziyah']},
            'Dammam': {'Merkez': ['Al Faisaliyah', 'Al Anud', 'Al Muraikabat', 'Al Khobar']},
            'Taif': {'Merkez': ['Al Hada', 'Al Shafa', 'Al Hawiyah', 'Souq Okaz']},
        },
        'koyler': ['Tabuk', 'Al Ula', 'Hegra', 'Al Bahah', 'Jizan', 'Najran', 'Hail', 'Yanbu'],
    },
    'ae': {
        'flag': '🇦🇪', 'name': 'BAE',
        'sehirler': {
            'Dubai': {
                'Merkez': ['Deira', 'Bur Dubai', 'Jumeirah', 'Downtown', 'Marina', 'JBR', 'Karama'],
                'Yeni Bölgeler': ['Al Barsha', 'Jumeirah Village', 'Discovery Gardens', 'Silicon Oasis', 'DIFC'],
            },
            'Abu Dhabi': {
                'Merkez': ['Al Markaziyah', 'Al Khalidiyah', 'Al Bateen', 'Corniche'],
                'Diğer': ['Al Ain', 'Musaffah', 'Yas Island', 'Saadiyat Island'],
            },
            'Sharjah': {'Merkez': ['Al Nabba', 'Al Qasimia', 'Al Taawun', 'Muwaileh']},
            'Ajman': {'Merkez': ['Ajman', 'Al Rashidiya', 'Al Nuaimiya']},
            'Ras al-Khaimah': {'Merkez': ['RAK City', 'Al Nakheel', 'Al Hamra', 'Khuzam']},
        },
        'koyler': ['Fujairah', 'Umm al-Quwain', 'Al Dhaid', 'Hatta', 'Liwa Oasis', 'Sir Bani Yas'],
    },
    'ir': {
        'flag': '🇮🇷', 'name': 'İran',
        'sehirler': {
            'Tehran': {
                'Merkez': ['Shemiran', 'Elahieh', 'Darband', 'Vanak', 'Tajrish', 'Niavaran'],
                'Güney': ['Rey', 'Qarchak', 'Pakdasht', 'Islamshahr', 'Robat Karim'],
            },
            'Isfahan': {'Merkez': ['Naqsh-e Jahan', 'Chaharbagh', 'Jolfa', 'Siosepol', 'Hasht Behesht']},
            'Mashhad': {'Merkez': ['Imam Reza Shrine', 'Bazaar', 'Torqabeh', 'Ferdowsi']},
            'Tabriz': {'Merkez': ['Bazar', 'Arg', 'El Goli', 'Shahriar', 'Valiasr']},
            'Shiraz': {'Merkez': ['Persepolis', 'Vakil', 'Eram', 'Hafez Tomb', 'Nasir al-Mulk']},
            'Rasht': {'Merkez': ['Rasht', 'Bandar Anzali', 'Astara', 'Masal', 'Fooman']},
        },
        'koyler': ['Qom', 'Ahvaz', 'Kerman', 'Yazd', 'Hamedan', 'Qazvin', 'Ardabil', 'Zanjan'],
    },
    'pk': {
        'flag': '🇵🇰', 'name': 'Pakistan',
        'sehirler': {
            'Karachi': {
                'Merkez': ['Saddar', 'Clifton', 'Defence', 'Gulshan', 'Malir'],
                'Diğer': ['Korangi', 'Lyari', 'Orangi', 'Baldia', 'Keamari'],
            },
            'Lahore': {'Merkez': ['Gulberg', 'DHA', 'Model Town', 'Johar Town', 'Walled City', 'Cantt']},
            'Islamabad': {'Merkez': ['F-6', 'F-7 Jinnah', 'G-9 Markaz', 'I-8 Markaz', 'Blue Area', 'F-10']},
            'Rawalpindi': {'Merkez': ['Satellite Town', 'Cantt', 'Murree Road', 'Raja Bazaar']},
            'Peshawar': {'Merkez': ['Cantonment', 'Hayatabad', 'University Town', 'Saddar', 'Qissa Khwani']},
        },
        'koyler': ['Swat', 'Hunza', 'Skardu', 'Murree', 'Chitral', 'Kaghan', 'Nathiagali', 'Neelum Valley'],
    },
    'eg': {
        'flag': '🇪🇬', 'name': 'Mısır',
        'sehirler': {
            'Cairo': {
                'Merkez': ['Zamalek', 'Maadi', 'Heliopolis', 'Nasr City', 'Downtown', 'Al Mohandessin'],
                'Çevre': ['Giza', '6th of October', 'New Cairo', 'Rehab City', 'Madinaty'],
            },
            'Alexandria': {'Merkez': ['Montaza', 'Smouha', 'Stanley', 'Sidi Bishr', 'Mamura', 'Corniche']},
            'Luxor': {'Merkez': ['East Bank', 'West Bank', 'Karnak', 'Valley of the Kings', 'Deir el-Bahari']},
            'Hurghada': {'Merkez': ['El Dahar', 'Sekalla', 'Sahl Hasheesh', 'El Gouna', 'Makadi Bay']},
            'Sharm el-Sheikh': {'Merkez': ['Naama Bay', 'Hadaba', 'Old Market', 'Shark Bay', 'Ras Um Sid']},
        },
        'koyler': ['Aswan', 'Siwa Oasis', 'Marsa Matruh', 'Dahab', 'Nuweiba', 'Abu Simbel', 'Edfu', 'Kom Ombo'],
    },
    'ma': {
        'flag': '🇲🇦', 'name': 'Fas',
        'sehirler': {
            'Casablanca': {'Merkez': ['Ain Diab', 'Anfa', 'Bourgogne', 'Maarif', 'Gueliz', 'Hay Hassani']},
            'Rabat': {'Merkez': ['Agdal', 'Hassan', 'Kasbah', 'Medina', 'Youssoufia', 'Hay Riad']},
            'Marrakech': {'Merkez': ['Medina', 'Gueliz', 'Hivernage', 'Palmeraie', 'Mellah']},
            'Fez': {'Merkez': ['Fes el-Bali', 'Fes el-Jdid', 'Ville Nouvelle', 'Saiss', 'Mellah']},
            'Tangier': {'Merkez': ['Medina', 'Malabata', 'Marshan', 'Beni Makada', 'Corniche']},
        },
        'koyler': ['Chefchaouen', 'Essaouira', 'Ouarzazate', 'Merzouga', 'Agadir', 'Meknes', 'Ifrane', 'Asilah'],
    },
    'jo': {
        'flag': '🇯🇴', 'name': 'Ürdün',
        'sehirler': {
            'Amman': {
                'Merkez': ['Downtown', '1st Circle', '3rd Circle', 'Abdoun', 'Shmeisani', 'Sweifieh'],
                'Çevre': ['Zarqa', 'Russeifa', 'Mafraq', 'Al Salt', 'Fuheis'],
            },
            'Aqaba': {'Merkez': ['Aqaba City', 'Tala Bay', 'South Beach', 'Al Rayyan']},
            'Irbid': {'Merkez': ['Irbid City', 'Ramtha', 'Ajloun', 'Jerash']},
            'Petra': {'Merkez': ['Wadi Musa', 'Beidha', 'Little Petra', 'Siq Entrance']},
        },
        'koyler': ['Jerash', 'Madaba', 'Um Qais', 'Azraq', 'Wadi Rum', 'Karak', 'Dana', 'Shobak'],
    },
    'iq': {
        'flag': '🇮🇶', 'name': 'Irak',
        'sehirler': {
            'Baghdad': {'Merkez': ['Mansour', 'Karrada', 'Jadriyah', 'Sadr City', 'Zayona', 'Kadhimiya', 'Rusafa']},
            'Erbil': {'Merkez': ['Citadel', 'Shar Park', 'Gulan', 'Italian Village', 'Dream City', 'Ankawa']},
            'Basra': {'Merkez': ['Ashar', 'Margil', 'Shat Al-Arab', 'Abu Al-Khasib', 'Khorramshahr']},
            'Sulaymaniyah': {'Merkez': ['City Center', 'Rizgari', 'Bakhtiari', 'Ahmad Awa', 'Azmar']},
            'Najaf': {'Merkez': ['Imam Ali Shrine', 'Old City', 'Kufa', 'Al Hanana']},
        },
        'koyler': ['Karbala', 'Kirkuk', 'Tikrit', 'Samarra', 'Hillah', 'Amarah', 'Duhok', 'Zakho'],
    },
    'kz': {
        'flag': '🇰🇿', 'name': 'Kazakistan',
        'sehirler': {
            'Astana': {'Merkez': ['Khan Shatyr', 'Bayterek', 'Expo City', 'Nurzhol Boulevard', 'Esil']},
            'Almaty': {
                'Merkez': ['Medeu', 'Alatau', 'Bostandyq', 'Almaly', 'Turksib'],
                'Dağ Bölgesi': ['Shymbulak', 'Big Almaty Lake', 'Chimbulak', 'Kok-Tobe'],
            },
            'Shymkent': {'Merkez': ['Al-Farabi', 'Abesov', 'Enbekshi', 'Karatau']},
            'Karaganda': {'Merkez': ['Kazybek Bi', 'Oktyabr', 'Bukhar-Zhyrau', 'Mishino']},
        },
        'koyler': ['Turkestan', 'Taraz', 'Semey', 'Atyrau', 'Aktobe', 'Aktau', 'Petropavl', 'Kyzylorda'],
    },
    'uz': {
        'flag': '🇺🇿', 'name': 'Özbekistan',
        'sehirler': {
            'Tashkent': {'Merkez': ['Yunusabad', 'Mirabad', 'Yashnabad', 'Chilanzar', 'Hamza', 'Olmazor']},
            'Samarkand': {'Merkez': ['Registan', 'Shah-i-Zinda', 'Bibi-Khanym', 'Afrosiab', 'Ulugbek']},
            'Bukhara': {'Merkez': ['Old City', 'Lyabi Hauz', 'Ark Citadel', 'Bolo Hauz', 'Chor Minor']},
            'Namangan': {'Merkez': ['Yangi Namangan', 'Chorsu', 'Bozortalik', 'Kosonsoy']},
            'Fergana': {'Merkez': ['Fergana City', 'Margilan', 'Quvasoy', 'Rishtan']},
        },
        'koyler': ['Andijan', 'Nukus', 'Termez', 'Karshi', 'Jizzakh', 'Navoi', 'Urgench', 'Khiva', 'Shakhrisabz'],
    },
    'id': {
        'flag': '🇮🇩', 'name': 'Endonezya',
        'sehirler': {
            'Jakarta': {
                'Merkez': ['Menteng', 'Gambir', 'Tanah Abang', 'Kemayoran'],
                'Diğer': ['South Jakarta', 'East Jakarta', 'North Jakarta', 'West Jakarta', 'Depok'],
            },
            'Bali': {
                'Kuta': ['Kuta', 'Legian', 'Seminyak', 'Canggu', 'Pererenan'],
                'Ubud': ['Ubud', 'Tegalalang', 'Payangan', 'Gianyar'],
                'Nusa Dua': ['Nusa Dua', 'Jimbaran', 'Bukit Peninsula', 'Ungasan'],
            },
            'Yogyakarta': {'Merkez': ['Keraton', 'Prawirotaman', 'Malioboro', 'Kotagede', 'Prambanan']},
            'Surabaya': {'Merkez': ['Wonokromo', 'Gubeng', 'Genteng', 'Tegalsari', 'Kenjeran']},
            'Lombok': {'Merkez': ['Mataram', 'Senggigi', 'Kuta Lombok', 'Gili Islands', 'Rinjani']},
        },
        'koyler': ['Bandung', 'Medan', 'Semarang', 'Makassar', 'Palembang', 'Malang', 'Manado', 'Labuan Bajo'],
    },
    'my': {
        'flag': '🇲🇾', 'name': 'Malezya',
        'sehirler': {
            'Kuala Lumpur': {
                'Merkez': ['KLCC', 'Bukit Bintang', 'Chow Kit', 'Brickfields', 'Bangsar'],
                'Diğer': ['Mont Kiara', 'Damansara', 'Kepong', 'Ampang', 'Cheras'],
            },
            'Penang': {'Merkez': ['George Town', 'Batu Ferringhi', 'Bukit Mertajam', 'Air Itam']},
            'Johor Bahru': {'Merkez': ['JB City', 'Iskandar Puteri', 'Skudai', 'Senai', 'Kulai']},
            'Kota Kinabalu': {'Merkez': ['City Center', 'Api-Api', 'Inanam', 'Menggatal', 'Tuaran']},
            'Kuching': {'Merkez': ['Padungan', 'Samarahan', 'Kota Samarahan', 'Serian']},
        },
        'koyler': ['Langkawi', 'Cameron Highlands', 'Ipoh', 'Malacca', 'Mersing', 'Tioman', 'Redang'],
    },
    'de': {
        'flag': '🇩🇪', 'name': 'Almanya',
        'sehirler': {
            'Berlin': {
                'Merkez': ['Mitte', 'Prenzlauer Berg', 'Kreuzberg', 'Charlottenburg', 'Friedrichshain'],
                'Çevre': ['Spandau', 'Pankow', 'Treptow', 'Köpenick', 'Tempelhof'],
            },
            'Munich': {'Merkez': ['Altstadt-Lehel', 'Maxvorstadt', 'Schwabing', 'Haidhausen', 'Neuhausen']},
            'Hamburg': {'Merkez': ['HafenCity', 'Altona', 'Eimsbüttel', 'Wandsbek', 'Harburg']},
            'Frankfurt': {'Merkez': ['Sachsenhausen', 'Bornheim', 'Westend', 'Nordend', 'Innenstadt']},
            'Cologne': {'Merkez': ['Innenstadt', 'Ehrenfeld', 'Nippes', 'Mülheim', 'Deutz']},
        },
        'koyler': ['Stuttgart', 'Dusseldorf', 'Leipzig', 'Heidelberg', 'Rothenburg', 'Bamberg', 'Freiburg'],
    },
    'gb': {
        'flag': '🇬🇧', 'name': 'İngiltere',
        'sehirler': {
            'London': {
                'Merkez': ['Westminster', 'City of London', 'Kensington', 'Chelsea', 'Camden', 'Islington'],
                'Diğer': ['Croydon', 'Bromley', 'Enfield', 'Barnet', 'Ealing', 'Hackney'],
            },
            'Manchester': {'Merkez': ['City Centre', 'Salford', 'Trafford', 'Didsbury', 'Withington']},
            'Birmingham': {'Merkez': ['City Centre', 'Digbeth', 'Harborne', 'Solihull', 'Edgbaston']},
            'Edinburgh': {'Merkez': ['Old Town', 'New Town', 'Leith', 'Corstorphine', 'Morningside']},
            'Glasgow': {'Merkez': ['City Centre', 'West End', 'Southside', 'East End', 'Merchant City']},
        },
        'koyler': ['Oxford', 'Cambridge', 'Bath', 'Bristol', 'York', 'Liverpool', 'Brighton', 'Canterbury'],
    },
    'fr': {
        'flag': '🇫🇷', 'name': 'Fransa',
        'sehirler': {
            'Paris': {
                'Merkez': ['Montmartre', 'Marais', 'Champs-Elysees', 'Rive Gauche', 'Bastille'],
                'Banlieue': ['Versailles', 'Saint-Denis', 'Boulogne', 'Vincennes', 'Neuilly'],
            },
            'Lyon': {'Merkez': ['Presquile', 'Croix-Rousse', 'Vieux Lyon', 'Part-Dieu', 'Confluence']},
            'Marseille': {'Merkez': ['Vieux-Port', 'Noailles', 'Endoume', 'Castellane', 'La Joliette']},
            'Nice': {'Merkez': ['Vieux-Nice', 'Promenade des Anglais', 'Cimiez', 'Liberation']},
        },
        'koyler': ['Strasbourg', 'Bordeaux', 'Toulouse', 'Nantes', 'Montpellier', 'Rennes', 'Avignon'],
    },
    'us': {
        'flag': '🇺🇸', 'name': 'ABD',
        'sehirler': {
            'New York': {
                'Manhattan': ['Midtown', 'Downtown', 'Upper East Side', 'Harlem', 'Financial District', 'SoHo'],
                'Diğer Boroughs': ['Brooklyn', 'Queens', 'Bronx', 'Staten Island', 'Flushing'],
            },
            'Los Angeles': {'Merkez': ['Hollywood', 'Beverly Hills', 'Santa Monica', 'Downtown', 'Venice Beach', 'Malibu']},
            'Chicago': {'Merkez': ['Loop', 'River North', 'Wicker Park', 'Lincoln Park', 'Magnificent Mile']},
            'Miami': {'Merkez': ['South Beach', 'Brickell', 'Wynwood', 'Coconut Grove', 'Coral Gables']},
            'Las Vegas': {'Merkez': ['The Strip', 'Downtown Fremont', 'Henderson', 'Summerlin', 'Paradise']},
        },
        'koyler': ['Houston', 'Phoenix', 'Philadelphia', 'San Francisco', 'Seattle', 'Boston', 'Denver', 'Nashville'],
    },
    'in': {
        'flag': '🇮🇳', 'name': 'Hindistan',
        'sehirler': {
            'Mumbai': {
                'Merkez': ['Colaba', 'Bandra', 'Andheri', 'Powai', 'Juhu', 'Worli'],
                'Çevre': ['Thane', 'Navi Mumbai', 'Kalyan', 'Ulhasnagar'],
            },
            'Delhi': {
                'Merkez': ['Connaught Place', 'Karol Bagh', 'Lajpat Nagar', 'Daryaganj', 'Chandni Chowk'],
                'NCR': ['Noida', 'Gurgaon', 'Faridabad', 'Ghaziabad'],
            },
            'Bangalore': {'Merkez': ['MG Road', 'Indiranagar', 'Koramangala', 'Whitefield', 'Electronic City']},
            'Kolkata': {'Merkez': ['Park Street', 'Esplanade', 'Salt Lake', 'Howrah', 'New Town']},
            'Chennai': {'Merkez': ['T Nagar', 'Anna Nagar', 'Egmore', 'Mylapore', 'Adyar']},
        },
        'koyler': ['Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Agra', 'Varanasi', 'Goa', 'Kochi', 'Rishikesh'],
    },
    'cn': {
        'flag': '🇨🇳', 'name': 'Çin',
        'sehirler': {
            'Beijing': {'Merkez': ['Chaoyang', 'Haidian', 'Dongcheng', 'Xicheng', 'Fengtai', 'Shijingshan']},
            'Shanghai': {'Merkez': ['Huangpu', 'Lujiazui', 'Xuhui', 'Jing An', 'Pudong', 'Bund']},
            'Guangzhou': {'Merkez': ['Tianhe', 'Yuexiu', 'Haizhu', 'Baiyun', 'Panyu']},
            'Shenzhen': {'Merkez': ['Futian', 'Nanshan', 'Longhua', 'Bao An', 'Luohu']},
            'Chengdu': {'Merkez': ['Jinjiang', 'Wuhou', 'Qingyang', 'Chenghua', 'Jinniu']},
        },
        'koyler': ['Xian', 'Hangzhou', 'Wuhan', 'Nanjing', 'Kunming', 'Guilin', 'Lijiang', 'Zhangjiajie'],
    },
    'jp': {
        'flag': '🇯🇵', 'name': 'Japonya',
        'sehirler': {
            'Tokyo': {
                'Merkez': ['Shinjuku', 'Shibuya', 'Harajuku', 'Akihabara', 'Ginza', 'Asakusa'],
                'Diğer': ['Ikebukuro', 'Ueno', 'Odaiba', 'Roppongi', 'Shimokitazawa'],
            },
            'Osaka': {'Merkez': ['Namba', 'Shinsaibashi', 'Umeda', 'Dotonbori', 'Tennoji', 'Shinsekai']},
            'Kyoto': {'Merkez': ['Gion', 'Arashiyama', 'Higashiyama', 'Nishiki Market', 'Fushimi Inari']},
            'Sapporo': {'Merkez': ['Susukino', 'Odori Park', 'Hokkaido University', 'Tanukikoji']},
            'Fukuoka': {'Merkez': ['Hakata', 'Tenjin', 'Ohori', 'Momochi', 'Nakasu']},
        },
        'koyler': ['Hiroshima', 'Nagoya', 'Yokohama', 'Nara', 'Nikko', 'Hakone', 'Kamakura', 'Takayama'],
    },
    'br': {
        'flag': '🇧🇷', 'name': 'Brezilya',
        'sehirler': {
            'Sao Paulo': {'Merkez': ['Centro', 'Paulista', 'Jardins', 'Vila Madalena', 'Pinheiros', 'Liberdade']},
            'Rio de Janeiro': {'Merkez': ['Ipanema', 'Copacabana', 'Leblon', 'Santa Teresa', 'Centro', 'Barra']},
            'Brasilia': {'Merkez': ['Plano Piloto', 'Asa Sul', 'Asa Norte', 'Lago Sul', 'Sudoeste']},
            'Salvador': {'Merkez': ['Pelourinho', 'Barra', 'Ondina', 'Orla', 'Bonfim']},
            'Manaus': {'Merkez': ['Centro', 'Adrianopolis', 'Chapada', 'Taruma', 'Ponta Negra']},
        },
        'koyler': ['Curitiba', 'Fortaleza', 'Recife', 'Belem', 'Natal', 'Florianopolis', 'Foz do Iguacu', 'Gramado'],
    },
}

# Döviz para birimleri
DOVIZ_LISTESI = [
    ('🇺🇸 USD', 'USD'), ('🇪🇺 EUR', 'EUR'), ('🇹🇷 TRY', 'TRY'),
    ('🇬🇧 GBP', 'GBP'), ('🇷🇺 RUB', 'RUB'), ('🇨🇭 CHF', 'CHF'),
    ('🇦🇿 AZN', 'AZN'), ('🇬🇪 GEL', 'GEL'), ('🇸🇦 SAR', 'SAR'),
    ('🇦🇪 AED', 'AED'), ('🇯🇵 JPY', 'JPY'), ('🇨🇳 CNY', 'CNY'),
    ('🇮🇳 INR', 'INR'), ('🇰🇿 KZT', 'KZT'), ('🇺🇦 UAH', 'UAH'),
    ('🇨🇦 CAD', 'CAD'), ('🇦🇺 AUD', 'AUD'), ('🇧🇷 BRL', 'BRL'),
]

def ulke_klavyesi(geri_cb: str) -> InlineKeyboardMarkup:
    """Ülke seçim klavyesi — 3 sütun."""
    kodlar = list(ULKE_HIYERARSI.keys())
    satirlar = []
    for i in range(0, len(kodlar), 3):
        satir = []
        for kod in kodlar[i:i+3]:
            u = ULKE_HIYERARSI[kod]
            satir.append(InlineKeyboardButton(f"{u['flag']} {u['name']}", callback_data=f"hava_u_{kod}"))
        satirlar.append(satir)
    satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data=geri_cb)])
    return InlineKeyboardMarkup(satirlar)

def kategori_klavyesi(ulke_kodu: str) -> InlineKeyboardMarkup:
    """Ülke için ŞEHİR / KÖY / ARAMA kategori seçimi."""
    ulke = ULKE_HIYERARSI.get(ulke_kodu, {})
    satirlar = []
    row = []
    if ulke.get('sehirler'):
        row.append(InlineKeyboardButton("🏙 ŞEHİR", callback_data=f"hava_cs_{ulke_kodu}"))
    if ulke.get('koyler'):
        row.append(InlineKeyboardButton("🏘 KÖY/KƏND", callback_data=f"hava_kv_{ulke_kodu}"))
    if row:
        satirlar.append(row)
    satirlar.append([InlineKeyboardButton("🔍 ARAMA", callback_data=f"hava_sx_{ulke_kodu}")])
    satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data='pro_hava')])
    return InlineKeyboardMarkup(satirlar)

def sehirler_klavyesi(ulke_kodu: str) -> InlineKeyboardMarkup:
    """Ülkedeki şehirleri listeler — 2 sütun + ARAMA."""
    ulke = ULKE_HIYERARSI.get(ulke_kodu, {})
    sehirler = list(ulke.get('sehirler', {}).keys())
    satirlar = []
    for i in range(0, len(sehirler), 2):
        satir = []
        for s in sehirler[i:i+2]:
            cb = f"hava_ci_{ulke_kodu}:{s}"
            satir.append(InlineKeyboardButton(s, callback_data=cb[:64]))
        satirlar.append(satir)
    satirlar.append([InlineKeyboardButton("🔍 ARAMA", callback_data=f"hava_sx_{ulke_kodu}")])
    satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data=f"hava_u_{ulke_kodu}")])
    return InlineKeyboardMarkup(satirlar)

def koyler_klavyesi(ulke_kodu: str) -> InlineKeyboardMarkup:
    """KÖY/KƏND listesi. Dict ise rayonlar gösterir; list ise direkt hava."""
    ulke = ULKE_HIYERARSI.get(ulke_kodu, {})
    koyler = ulke.get('koyler', [])
    satirlar = []
    if isinstance(koyler, dict):
        rayonlar = list(koyler.keys())
        for i in range(0, len(rayonlar), 2):
            satir = []
            for r in rayonlar[i:i+2]:
                cb = f"hava_kr_{ulke_kodu}:{r}"
                satir.append(InlineKeyboardButton(r, callback_data=cb[:64]))
            satirlar.append(satir)
    else:
        for i in range(0, len(koyler), 2):
            satir = []
            for k in koyler[i:i+2]:
                satir.append(InlineKeyboardButton(k, callback_data=f"hava_wx_{k[:45]}"))
            satirlar.append(satir)
    satirlar.append([InlineKeyboardButton("🔍 ARAMA", callback_data=f"hava_sx_{ulke_kodu}")])
    satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data=f"hava_u_{ulke_kodu}")])
    return InlineKeyboardMarkup(satirlar)

def koy_rayon_klavyesi(ulke_kodu: str, rayon: str) -> InlineKeyboardMarkup:
    """KÖY/KƏND yolunda: bir rayonun köylerini listeler — 2 sütun."""
    ulke = ULKE_HIYERARSI.get(ulke_kodu, {})
    koyler_dict = ulke.get('koyler', {})
    koy_listesi = koyler_dict.get(rayon, []) if isinstance(koyler_dict, dict) else []
    satirlar = []
    for i in range(0, len(koy_listesi), 2):
        satir = []
        for k in koy_listesi[i:i+2]:
            satir.append(InlineKeyboardButton(k, callback_data=f"hava_wx_{k[:45]}"))
        satirlar.append(satir)
    satirlar.append([InlineKeyboardButton("🔍 ARAMA", callback_data=f"hava_sx_{ulke_kodu}")])
    satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data=f"hava_kv_{ulke_kodu}")])
    return InlineKeyboardMarkup(satirlar)

def rayon_klavyesi(ulke_kodu: str, sehir: str) -> InlineKeyboardMarkup:
    """Bir şehrin rayon/ilçelerini listeler — 2 sütun + ARAMA."""
    ulke = ULKE_HIYERARSI.get(ulke_kodu, {})
    sehir_data = ulke.get('sehirler', {}).get(sehir, {})
    rayonlar = list(sehir_data.keys())
    satirlar = []
    for i in range(0, len(rayonlar), 2):
        satir = []
        for r in rayonlar[i:i+2]:
            cb = f"hava_ri_{ulke_kodu}:{sehir}:{r}"
            satir.append(InlineKeyboardButton(r, callback_data=cb[:64]))
        satirlar.append(satir)
    satirlar.append([InlineKeyboardButton("🔍 ARAMA", callback_data=f"hava_sx_{ulke_kodu}")])
    satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data=f"hava_cs_{ulke_kodu}")])
    return InlineKeyboardMarkup(satirlar)

def koy_listesi_klavyesi(ulke_kodu: str, sehir: str, rayon: str) -> InlineKeyboardMarkup:
    """Bir rayonun köy/kəndlerini listeler — 2 sütun + ARAMA."""
    ulke = ULKE_HIYERARSI.get(ulke_kodu, {})
    sehir_data = ulke.get('sehirler', {}).get(sehir, {})
    koyler = sehir_data.get(rayon, [])
    satirlar = []
    for i in range(0, len(koyler), 2):
        satir = []
        for k in koyler[i:i+2]:
            satir.append(InlineKeyboardButton(k, callback_data=f"hava_wx_{k[:45]}"))
        satirlar.append(satir)
    satirlar.append([InlineKeyboardButton("🔍 ARAMA", callback_data=f"hava_sx_{ulke_kodu}")])
    geri_cb = f"hava_ci_{ulke_kodu}:{sehir}"
    satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data=geri_cb[:64])])
    return InlineKeyboardMarkup(satirlar)

def doviz_from_klavyesi() -> InlineKeyboardMarkup:
    satirlar = []
    for i in range(0, len(DOVIZ_LISTESI), 3):
        satir = [InlineKeyboardButton(ad, callback_data=f"kur_f_{kod}") for ad, kod in DOVIZ_LISTESI[i:i+3]]
        satirlar.append(satir)
    satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data='menu_pro_araclar')])
    return InlineKeyboardMarkup(satirlar)

def doviz_to_klavyesi(from_kur: str) -> InlineKeyboardMarkup:
    satirlar = []
    for i in range(0, len(DOVIZ_LISTESI), 3):
        satir = [InlineKeyboardButton(ad, callback_data=f"kur_t_{from_kur}_{kod}") for ad, kod in DOVIZ_LISTESI[i:i+3]]
        satirlar.append(satir)
    satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data='pro_doviz')])
    return InlineKeyboardMarkup(satirlar)

# BUG FIX: Bu fonksiyon ana_menu_klavye içinde yanlış girintilenmişti, düzeltildi
async def kanal_takip_kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str) -> bool:
    if user_id == MY_ID:
        return True

    try:
        member = await context.bot.get_chat_member(chat_id=KONTROL_KANAL_USER, user_id=user_id)
        if member.status in ['member', 'creator', 'administrator']:
            return True
    except Exception as e:
        logger.error(f"Kanal kontrol hatası: {e}")
        return True

    strings = LANG_DATA[lang]
    join_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(strings['btn_join_now'], url=f"https://t.me/{KONTROL_KANAL_USER.replace('@', '')}")]
    ])

    if update.message:
        await update.message.reply_text(strings['force_join_text'], reply_markup=join_keyboard, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(strings['force_join_text'], reply_markup=join_keyboard, parse_mode='Markdown')

    return False

# --- ROSE BOT TARZI HOŞ GELDİN SİSTEMİ ---
def rose_welcome_klavye() -> InlineKeyboardMarkup:
    klavye = [[InlineKeyboardButton("📢 AZRxMAQA KANALI", url='https://t.me/azrXmaqa')]]
    return InlineKeyboardMarkup(klavye)

async def kanala_veya_gruba_yeni_uye_katildi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_member:
        chat_member_update = update.chat_member
        if chat_member_update.new_chat_member.status == "member":
            yeni_uye = chat_member_update.new_chat_member.user
            if yeni_uye.is_bot:
                return
            guvenli_isim = html.escape(yeni_uye.first_name) if yeni_uye.first_name else "Yeni Üye"
            hos_geldin_metni = (
                f"✨ **Grubumuza Hoş Geldin, [{guvenli_isim}](tg://user?id={yeni_uye.id})!**\n\n"
                f"Aramıza katıldığın için mutluyuz! Sohbet etmeye başlamadan önce lütfen kurallarımıza göz atmayı unutma. 🔥"
            )
            try:
                await context.bot.send_message(
                    chat_id=chat_member_update.chat.id,
                    text=hos_geldin_metni,
                    reply_markup=rose_welcome_klavye(),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Rose karşılama hatası: {e}")

    elif update.message and update.message.new_chat_members:
        for yeni_uye in update.message.new_chat_members:
            if yeni_uye.is_bot:
                continue
            guvenli_isim = html.escape(yeni_uye.first_name) if yeni_uye.first_name else "Yeni Üye"
            hos_geldin_metni = (
                f"✨ **Grubumuza Hoş Geldin, [{guvenli_isim}](tg://user?id={yeni_uye.id})!**\n\n"
                f"Aramıza katıldığın için mutluyuz! Sohbet etmeye başlaya bilirsin iyi sohbetler. "
                f"lütfen diğer insanlara karşı saygılı ol. yoksa ban yersin. ve ana kanala katıla bilirsin kanal altda 👇🏻"
            )
            try:
                await update.message.reply_text(
                    text=hos_geldin_metni,
                    reply_markup=rose_welcome_klavye(),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Rose normal grup karşılama hatası: {e}")

# --- ASENKRON MESAJ SİLME ZAMANLAYICISI ---
async def mesajlari_5s_sonra_sil(context: ContextTypes.DEFAULT_TYPE, chat_id: int, bot_msg_id: int, user_msg_id: int):
    await asyncio.sleep(5.0)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=bot_msg_id)
    except Exception:
        pass
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=user_msg_id)
    except Exception:
        pass

# --- GELİŞMİŞ İSTATİSTİK OLUŞTURUCU ---
def istatistik_raporu_hazirla(context: ContextTypes.DEFAULT_TYPE) -> str:
    tum_uyeler = uyeleri_getir()
    toplam_uye = len(tum_uyeler)

    dil_verileri = context.bot_data.get('lang', {})
    tr_sayi = 0
    az_sayi = 0
    ru_sayi = 0
    en_sayi = 0
    de_sayi = 0

    for u_id in tum_uyeler:
        d = dil_verileri.get(u_id, 'tr')
        if d == 'tr': tr_sayi += 1
        elif d == 'az': az_sayi += 1
        elif d == 'ru': ru_sayi += 1
        elif d == 'en': en_sayi += 1
        elif d == 'de': de_sayi += 1

    return (
        f"📊 **AZRxGUARD - Gelişmiş Bot İstatistikleri**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 **Toplam Kayıtlı Kullanıcı:** `{toplam_uye}`\n\n"
        f"🌍 **Kullanıcı Dil Dağılımı:**\n"
        f"🇹🇷 **Türkçe (TR):** `{tr_sayi}`\n"
        f"🇦🇿 **Azərbaycanca (AZ):** `{az_sayi}`\n"
        f"🇷🇺 **Русский (RU):** `{ru_sayi}`\n"
        f"🇬🇧 **English (EN):** `{en_sayi}`\n"
        f"🇩🇪 **Deutsch (DE):** `{de_sayi}`\n\n"
        f"🤖 *Sistem Durumu: Aktif & Stabil*"
    )

async def stats_komut_tetikleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rapor = istatistik_raporu_hazirla(context)
    await update.message.reply_text(rapor, parse_mode='Markdown')

# --- 🪪 ME ID KOMUTU ---
async def meid_bilgisi_olustur(bot, update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> str:
    user = update.effective_user
    chat = update.effective_chat
    msg  = update.effective_message

    # Tam chat objesi
    full_chat = None
    try:
        full_chat = await bot.get_chat(user.id)
    except Exception:
        pass

    # Profil fotoğraf sayısı
    foto_sayisi = '—'
    try:
        fotolar = await bot.get_user_profile_photos(user.id, limit=1)
        foto_sayisi = str(fotolar.total_count)
    except Exception:
        pass

    # Gruptaki rolü
    chat_rolu = '—'
    if chat and chat.type in ('group', 'supergroup'):
        try:
            member = await bot.get_chat_member(chat.id, user.id)
            rol_map = {'creator': '👑 Kurucu', 'administrator': '🛡️ Admin',
                       'member': '👤 Üye', 'restricted': '⚠️ Kısıtlı',
                       'left': '🚪 Ayrılmış', 'kicked': '🔨 Banlı'}
            chat_rolu = rol_map.get(member.status, member.status)
        except Exception:
            pass

    # Kayıt tarihi tahmini
    kayit_tarihi = id_den_kayit_tarihi_tahmin_et(user.id)
    id_basamak = len(str(abs(user.id)))

    # Temel bilgiler
    ad       = html.escape(user.first_name) if user.first_name else "—"
    soyad    = html.escape(user.last_name)  if user.last_name  else "—"
    tam_ad   = f"{ad} {soyad}".strip() if user.last_name else ad
    kullanici_adi = f"@{user.username}" if user.username else "❌ Yok"
    mention       = f"@{user.username}" if user.username else f"[{ad}](tg://user?id={user.id})"
    tiklanabilir  = f"[{html.escape(tam_ad)}](tg://user?id={user.id})"

    bot_dili_map = {'tr':'🇹🇷 Türkçe','az':'🇦🇿 Azərbaycanca','ru':'🇷🇺 Русский','en':'🇬🇧 English','de':'🇩🇪 Deutsch'}
    bot_dili = bot_dili_map.get(lang, lang)
    tg_dili  = user.language_code.upper() if user.language_code else "—"
    tg_dili_tam = {
        'TR':'Türkçe','AZ':'Azərbaycan','RU':'Rusça','EN':'İngilizce','DE':'Almanca',
        'FA':'Farsça','AR':'Arapça','UK':'Ukraynaca','FR':'Fransızca','ES':'İspanyolca',
        'IT':'İtalyanca','PT':'Portekizce','PL':'Lehçe','KO':'Korece','JA':'Japonca',
        'ZH':'Çince','NL':'Hollandaca','HI':'Hintçe','VI':'Vietnamca','ID':'Endonezce',
    }.get(user.language_code.upper() if user.language_code else '', '')
    tg_dili_goster = f"`{tg_dili}`" + (f" ({tg_dili_tam})" if tg_dili_tam else "")

    # Hesap bayrakları
    premium    = "✅ Evet" if getattr(user, 'is_premium', False)    else "❌ Hayır"
    dogrulandi = "✅ Evet" if getattr(user, 'is_verified', False)   else "❌ Hayır"
    kisitlandi = "⚠️ Evet" if getattr(user, 'is_restricted', False) else "✅ Hayır"
    scam       = "🚨 SCAM" if getattr(user, 'is_scam', False)      else "✅ Temiz"
    fake       = "⚠️ FAKE" if getattr(user, 'is_fake', False)      else "✅ Gerçek"
    hesap_turu = "🤖 Bot"  if user.is_bot else "👤 Normal Kullanıcı"

    # full_chat ek veriler
    bio = ozel_iletme = aktif_kullanici_adlari = emoji_durum = '—'
    kisisel_chat = vurgu_renk = profil_vurgu_renk = '—'
    if full_chat:
        bio          = html.escape(full_chat.bio) if getattr(full_chat, 'bio', None) else '—'
        ozel_iletme  = "🔒 Gizli" if getattr(full_chat, 'has_private_forwards', False) else "✅ Açık"
        if getattr(full_chat, 'active_usernames', None):
            aktif_kullanici_adlari = '  |  '.join([f"@{u}" for u in full_chat.active_usernames])
        if getattr(full_chat, 'emoji_status_custom_emoji_id', None):
            emoji_durum = f"`{full_chat.emoji_status_custom_emoji_id}`"
        kisisel_chat    = "✅ Var" if getattr(full_chat, 'has_personal_chat', False) else "❌ Yok"
        if getattr(full_chat, 'accent_color_id', None) is not None:
            vurgu_renk = f"`{full_chat.accent_color_id}`"
        if getattr(full_chat, 'profile_accent_color_id', None) is not None:
            profil_vurgu_renk = f"`{full_chat.profile_accent_color_id}`"

    # Bot-a özgü bayraklar
    bot_gruba = bot_tum_mesaj = bot_inline = bot_business = bot_web_app = '—'
    if user.is_bot:
        bot_gruba      = "✅ Evet" if getattr(user, 'can_join_groups', False)            else "❌ Hayır"
        bot_tum_mesaj  = "✅ Evet" if getattr(user, 'can_read_all_group_messages', False) else "❌ Hayır"
        bot_inline     = "✅ Evet" if getattr(user, 'supports_inline_queries', False)     else "❌ Hayır"
        bot_business   = "✅ Evet" if getattr(user, 'can_connect_to_business', False)     else "❌ Hayır"
        bot_web_app    = "✅ Evet" if getattr(user, 'has_main_web_app', False)            else "❌ Hayır"

    # Sohbet bilgileri
    chat_turu_map = {'private':'💬 Özel Mesaj (DM)','group':'👥 Grup','supergroup':'👥 Süper Grup','channel':'📢 Kanal'}
    chat_turu = chat_turu_map.get(chat.type, chat.type) if chat else "—"
    chat_id   = str(chat.id)    if chat else "—"
    chat_adi  = html.escape(chat.title) if chat and chat.title else "—"
    chat_user = f"@{chat.username}"     if chat and chat.username else "—"

    chat_uye = '—'
    if chat and chat.type in ('group', 'supergroup', 'channel'):
        try:
            chat_uye = str(await bot.get_chat_member_count(chat.id))
        except Exception:
            pass

    chat_koruma  = "🔒 Evet" if chat and getattr(chat, 'has_protected_content', False) else "✅ Hayır" if chat else "—"
    chat_gizli   = "🔒 Evet" if chat and getattr(chat, 'has_hidden_members', False)    else "✅ Hayır" if chat else "—"
    chat_forum   = "✅ Evet" if chat and getattr(chat, 'is_forum', False)              else "❌ Hayır" if chat else "—"
    chat_slow    = f"`{chat.slow_mode_delay}s`" if chat and getattr(chat, 'slow_mode_delay', None) else "❌ Kapalı"

    # Mesaj bilgileri
    mesaj_id      = str(msg.message_id) if msg else "—"
    mesaj_zamani  = msg.date.strftime("%d.%m.%Y %H:%M:%S UTC") if msg and msg.date else "—"
    duzenleme     = msg.edit_date.strftime("%d.%m.%Y %H:%M:%S UTC") if msg and msg.edit_date else "❌ Düzenlenmedi"
    yanit_mi      = "✅ Evet" if msg and msg.reply_to_message else "❌ Hayır"
    yanit_kime    = '—'
    if msg and msg.reply_to_message and msg.reply_to_message.from_user:
        ru = msg.reply_to_message.from_user
        yanit_kime = f"[{html.escape(ru.first_name or '?')}](tg://user?id={ru.id})"

    iletildi_mi  = "✅ Evet" if msg and msg.forward_origin else "❌ Hayır"
    iletildi_kim = '—'
    if msg and msg.forward_origin:
        try:
            fo = msg.forward_origin
            if hasattr(fo, 'sender_user') and fo.sender_user:
                iletildi_kim = f"[{html.escape(fo.sender_user.first_name or '?')}](tg://user?id={fo.sender_user.id})"
            elif hasattr(fo, 'chat') and fo.chat:
                iletildi_kim = html.escape(fo.chat.title or '?')
            elif hasattr(fo, 'sender_user_name'):
                iletildi_kim = html.escape(fo.sender_user_name or '?')
        except Exception:
            pass

    via_bot = '—'
    if msg and msg.via_bot:
        via_bot = f"@{msg.via_bot.username}" if msg.via_bot.username else f"`{msg.via_bot.id}`"

    entity_sayisi = str(len(msg.entities)) if msg and msg.entities else "0"
    caption_var   = "✅ Evet" if msg and msg.caption else "❌ Hayır"
    medya_grubu   = f"`{msg.media_group_id}`" if msg and msg.media_group_id else "❌ Yok"
    mesaj_uzunluk = str(len(msg.text)) + " karakter" if msg and msg.text else "—"

    medya_turu = "—"
    if msg:
        if msg.photo:        medya_turu = "🖼️ Fotoğraf"
        elif msg.video:      medya_turu = "🎥 Video"
        elif msg.voice:      medya_turu = "🎙️ Sesli Mesaj"
        elif msg.document:   medya_turu = "📄 Dosya"
        elif msg.sticker:    medya_turu = "🎭 Sticker"
        elif msg.animation:  medya_turu = "🎬 GIF"
        elif msg.audio:      medya_turu = "🎵 Ses Dosyası"
        elif msg.video_note: medya_turu = "📹 Yuvarlak Video"
        elif msg.contact:    medya_turu = "📞 Kişi"
        elif msg.location:   medya_turu = "📍 Konum"
        elif msg.poll:       medya_turu = "📊 Anket"
        elif msg.game:       medya_turu = "🎮 Oyun"
        elif msg.dice:       medya_turu = "🎲 Zar"
        elif msg.text:       medya_turu = "💬 Metin"

    # Bot kayıt durumu
    toplam_uyeler     = uyeleri_getir()
    kayitli           = "✅ Evet" if user.id in toplam_uyeler else "❌ Hayır"
    toplam_uye_sayisi = len(toplam_uyeler)

    title = LANG_DATA[lang].get('meid_title', '🪪 **Kullanıcı Bilgilerin**')

    metin = (
        f"{title}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 **Ad:** {tiklanabilir}\n"
        f"🔤 **Soyad:** `{soyad}`\n"
        f"🏷️ **Kullanıcı Adı:** `{kullanici_adi}`\n"
        f"🔗 **Mention:** {mention}\n"
        f"🆔 **Kullanıcı ID:** `{user.id}`\n"
        f"🔢 **ID Basamak Sayısı:** `{id_basamak}`\n"
        f"🧩 **Hesap Türü:** {hesap_turu}\n"
        f"🌍 **Bot Dili:** {bot_dili}\n"
        f"📱 **Telegram Dili:** {tg_dili_goster}\n\n"
        f"💎 **Telegram Premium:** {premium}\n"
        f"✅ **Doğrulanmış:** {dogrulandi}\n"
        f"🚫 **Kısıtlanmış:** {kisitlandi}\n"
        f"🚨 **Scam İşareti:** {scam}\n"
        f"⚠️ **Fake İşareti:** {fake}\n\n"
        f"📝 **Bio:** {bio}\n"
        f"🖼️ **Profil Fotoğraf Sayısı:** `{foto_sayisi}`\n"
        f"🔀 **Mesaj Yönlendirme:** {ozel_iletme}\n"
        f"😀 **Emoji Durumu ID:** {emoji_durum}\n"
        f"🔤 **Aktif Kullanıcı Adları:** {aktif_kullanici_adlari}\n"
        f"💬 **Kişisel Sohbet:** {kisisel_chat}\n"
        f"🎨 **Vurgu Rengi:** {vurgu_renk}\n"
        f"🖌️ **Profil Vurgu Rengi:** {profil_vurgu_renk}\n\n"
    )

    if user.is_bot:
        metin += (
            f"🤖 **Bot Özellikleri:**\n"
            f"  👥 Gruba Eklenebilir: {bot_gruba}\n"
            f"  📖 Tüm Mesajları Okur: {bot_tum_mesaj}\n"
            f"  ⚡ Inline Mod: {bot_inline}\n"
            f"  💼 İş Hesabı Bağlanır: {bot_business}\n"
            f"  🌐 Ana Web Uygulaması: {bot_web_app}\n\n"
        )

    metin += (
        f"💬 **Sohbet Türü:** {chat_turu}\n"
        f"🏠 **Sohbet Adı:** `{chat_adi}`\n"
        f"📌 **Sohbet ID:** `{chat_id}`\n"
        f"🏷️ **Sohbet Kullanıcı Adı:** `{chat_user}`\n"
        f"👥 **Sohbet Üye Sayısı:** `{chat_uye}`\n"
        f"🎭 **Sohbetteki Rolüm:** {chat_rolu}\n"
        f"🔒 **Sohbet İçerik Koruması:** {chat_koruma}\n"
        f"👁️ **Sohbet Gizli Üyeler:** {chat_gizli}\n"
        f"🗂️ **Forum Modu:** {chat_forum}\n"
        f"🐌 **Yavaş Mod:** {chat_slow}\n\n"
        f"📨 **Mesaj ID:** `{mesaj_id}`\n"
        f"📎 **İçerik Türü:** {medya_turu}\n"
        f"📏 **Mesaj Uzunluğu:** {mesaj_uzunluk}\n"
        f"🔗 **Entity Sayısı:** `{entity_sayisi}`\n"
        f"📸 **Caption Var mı:** {caption_var}\n"
        f"🖼️ **Medya Grubu:** {medya_grubu}\n"
        f"↩️ **Yanıt mı?:** {yanit_mi}\n"
        f"👁️ **Kime Yanıt:** {yanit_kime}\n"
        f"📤 **İletildi mi?:** {iletildi_mi}\n"
        f"👤 **İleten:** {iletildi_kim}\n"
        f"🤖 **Via Bot:** {via_bot}\n"
        f"✏️ **Düzenlenme:** {duzenleme}\n"
        f"🕒 **Mesaj Zamanı:** `{mesaj_zamani}`\n\n"
        f"📋 **Bot'a Kayıtlı:** {kayitli}\n"
        f"👥 **Toplam Bot Üyesi:** `{toplam_uye_sayisi}`\n\n"
        f"🔗 **Profil Linki:** tg://user?id={user.id}\n\n"
        f"🤖 _AZRxGUARD tarafından oluşturuldu_"
    )
    return metin

async def meid_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    user_id = update.effective_user.id
    lang = get_lang(context, user_id)
    strings = LANG_DATA[lang]
    bilgi = await meid_bilgisi_olustur(context.bot, update, context, lang)
    geri_klavye = None
    if update.effective_chat and update.effective_chat.type == 'private':
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_azr_special')]])
    try:
        await update.effective_message.reply_text(bilgi, parse_mode='Markdown', reply_markup=geri_klavye)
    except Exception:
        await update.effective_message.reply_text(bilgi, reply_markup=geri_klavye)

# --- 🌐 IP BASİT SORGULAMA ---
def _ipapi_basit_getir(ip: str) -> dict:
    try:
        r = http_requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,"
            f"regionName,city,zip,lat,lon,timezone,isp,org,as,asname,mobile,proxy,hosting,query",
            timeout=8
        )
        return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def ip_basit_rapor(veri: dict, aranan_ip: str) -> str:
    if veri.get("status") != "success":
        hata = veri.get("message", "Bilinmeyen hata")
        return f"❌ **IP sorgulanamadı:** `{hata}`\n\nGirilen değer: `{aranan_ip}`"

    lat = veri.get('lat', '')
    lon = veri.get('lon', '')
    harita = f"https://maps.google.com/?q={lat},{lon}" if lat and lon else None

    rozetler = []
    if veri.get('proxy'):   rozetler.append("🔴 Proxy/VPN")
    if veri.get('hosting'): rozetler.append("🟠 Hosting/Sunucu")
    if veri.get('mobile'):  rozetler.append("📱 Mobil Hat")
    rozet_str = " · ".join(rozetler) if rozetler else "✅ Temiz (Normal Kullanıcı)"

    return (
        f"🌐 **IP Sorgulama — AZRxGUARD**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 **Sorgulan IP:** `{veri.get('query', aranan_ip)}`\n\n"
        f"🏳️ **Ülke:** {veri.get('country', '—')} ({veri.get('countryCode', '—')})\n"
        f"🏙️ **Bölge:** {veri.get('regionName', '—')} / {veri.get('city', '—')}\n"
        f"📮 **Posta Kodu:** {veri.get('zip', '—')}\n"
        f"🕐 **Saat Dilimi:** `{veri.get('timezone', '—')}`\n\n"
        f"📍 **Koordinat:** {lat}, {lon}\n"
        + (f"🗺️ **Harita:** [Google Maps'te Gör]({harita})\n\n" if harita else "\n")
        + f"🏢 **ISP:** {veri.get('isp', '—')}\n"
        f"🏛️ **Organizasyon:** {veri.get('org', '—')}\n"
        f"📡 **AS:** {veri.get('as', '—')}\n"
        f"🔤 **AS Adı:** {veri.get('asname', '—')}\n\n"
        f"🛡️ **IP Türü:** {rozet_str}\n\n"
        f"🤖 _AZRxGUARD tarafından sorgulandı_"
    )

async def ip_basit_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "🌐 **IP Sorgulama**\n\nKullanım: `/ip <IP adresi>`\nÖrnek: `/ip 8.8.8.8`",
            parse_mode='Markdown'
        )
        return
    ip_adresi = context.args[0].strip()
    if not re.match(r'^[0-9a-fA-F.:]{3,45}$', ip_adresi):
        await update.effective_message.reply_text("❌ Geçersiz IP formatı. Örnek: `/ip 8.8.8.8`", parse_mode='Markdown')
        return
    bekle = await update.effective_message.reply_text(f"🔍 `{ip_adresi}` sorgulanıyor...", parse_mode='Markdown')
    try:
        veri = await asyncio.to_thread(_ipapi_basit_getir, ip_adresi)
        rapor = ip_basit_rapor(veri, ip_adresi)
        await bekle.edit_text(rapor, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"IP basit hatası: {e}")
        await bekle.edit_text("❌ Sorgulama sırasında bir hata oluştu.")

# --- 🛡️ IP GELİŞMİŞ GÜVENLİK ANALİZİ ---

PORT_ADLARI = {
    21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
    80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 445: 'SMB',
    1433: 'MSSQL', 3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL',
    6379: 'Redis', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt', 27017: 'MongoDB'
}
TARANACAK_PORTLAR = list(PORT_ADLARI.keys())

async def _port_tara(ip: str, port: int, timeout: float = 1.2) -> bool:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False

async def _acik_portlari_bul(ip: str) -> list:
    sonuclar = await asyncio.gather(*[_port_tara(ip, p) for p in TARANACAK_PORTLAR])
    return [TARANACAK_PORTLAR[i] for i, acik in enumerate(sonuclar) if acik]

def _ptr_getir(ip: str) -> str:
    try:
        return _socket.gethostbyaddr(ip)[0]
    except Exception:
        return "—"

def _ipapi_getir(ip: str) -> dict:
    try:
        r = http_requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,"
            f"regionName,city,timezone,isp,org,as,asname,mobile,proxy,hosting,query",
            timeout=8
        )
        return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _proxycheck_getir(ip: str) -> dict:
    try:
        r = http_requests.get(
            f"http://proxycheck.io/v2/{ip}?vpn=1&asn=1&risk=1&port=1&seen=1&days=7",
            timeout=8
        )
        data = r.json()
        if data.get("status") == "ok" and ip in data:
            return data[ip]
        return {}
    except Exception:
        return {}

async def ip_tam_analiz_yap(ip_adresi: str) -> str:
    ipapi, proxycheck, ptr, acik_portlar = await asyncio.gather(
        asyncio.to_thread(_ipapi_getir, ip_adresi),
        asyncio.to_thread(_proxycheck_getir, ip_adresi),
        asyncio.to_thread(_ptr_getir, ip_adresi),
        _acik_portlari_bul(ip_adresi),
    )

    if ipapi.get("status") != "success":
        hata = ipapi.get("message", "Bilinmeyen hata")
        return f"❌ **IP sorgulanamadı:** `{hata}`\n\nGirilen IP: `{ip_adresi}`"

    gercek_ip  = ipapi.get('query', ip_adresi)
    ulke       = f"{ipapi.get('country', '—')} ({ipapi.get('countryCode', '—')})"
    bolge      = f"{ipapi.get('regionName', '—')} / {ipapi.get('city', '—')}"
    saat_dilimi = ipapi.get('timezone', '—')
    isp        = ipapi.get('isp', '—')
    org        = ipapi.get('org', '—')
    asn_raw    = ipapi.get('as', '—')
    asn_adi    = ipapi.get('asname', '—')
    hosting    = ipapi.get('hosting', False)
    mobil      = "📱 Evet" if ipapi.get('mobile', False) else "❌ Hayır"

    # Veri merkezi uyarısı
    dc_uyari = "  ⚠️ *[VERİ MERKEZİ IP'si!]*" if hosting else ""
    asn_str  = f"`{asn_raw}` ({asn_adi}){dc_uyari}"

    # Gizlilik — proxycheck.io + ip-api.com
    pc_type   = str(proxycheck.get('type', '')).lower()
    pc_vpn    = str(proxycheck.get('vpn', 'no')).lower() in ('yes', 'true', '1')
    pc_risk   = proxycheck.get('risk', None)
    is_vpn    = pc_vpn or (ipapi.get('proxy', False) and 'datacenter' not in pc_type)
    is_proxy  = 'proxy' in pc_type
    is_tor    = 'tor' in pc_type

    vpn_str   = "✅ Evet" if is_vpn   else "❌ Hayır"
    proxy_str = "✅ Evet" if is_proxy else "❌ Hayır"
    tor_str   = "✅ Evet" if is_tor   else "❌ Hayır"

    # Tehdit skoru
    if pc_risk is not None:
        risk_sayi = int(pc_risk)
    else:
        risk_sayi = 0
        if is_vpn:    risk_sayi += 40
        if is_proxy:  risk_sayi += 35
        if is_tor:    risk_sayi += 65
        if hosting:   risk_sayi += 20
        risk_sayi = min(100, risk_sayi)

    if risk_sayi >= 70:
        risk_str = f"🔴 %{risk_sayi} (Yüksek Risk)"
    elif risk_sayi >= 40:
        risk_str = f"🟡 %{risk_sayi} (Orta Risk)"
    else:
        risk_str = f"🟢 %{risk_sayi} (Düşük Risk)"

    # Portlar
    if acik_portlar:
        port_str = ", ".join([f"{p} ({PORT_ADLARI[p]})" for p in acik_portlar])
    else:
        port_str = "Açık port bulunamadı"

    return (
        f"🛡️ **IP Detaylı Güvenlik Analizi**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 **Sorgu:** `{gercek_ip}`\n\n"
        f"📍 **Konum Bilgisi**\n"
        f"🏳️ **Ülke:** {ulke}\n"
        f"🏙️ **Bölge:** {bolge}\n"
        f"🕐 **Saat Dilimi:** `{saat_dilimi}`\n\n"
        f"🔌 **Ağ Bilgisi**\n"
        f"🌐 **İnternet IP:** `{gercek_ip}`\n"
        f"🏢 **İnternet İsmi (ISP):** {isp}\n"
        f"🏛️ **Organizasyon:** {org}\n"
        f"📡 **Altyapı (ASN):** {asn_str}\n"
        f"📱 **Mobil Hat:** {mobil}\n"
        f"🏷️ **Ters DNS (PTR):** `{ptr}`\n\n"
        f"🕵️ **Gizlilik & Tehdit Durumu**\n"
        f"VPN: {vpn_str}  |  Proxy: {proxy_str}  |  Tor: {tor_str}\n"
        f"⚠️ **Tehdit Skoru:** {risk_str}\n\n"
        f"🔓 **Açık Portlar:** `{port_str}`\n\n"
        f"🤖 _AZRxGUARD Güvenlik Analizi_"
    )

async def ip_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "🛡️ **IP Güvenlik Analizi**\n\nKullanım: `/ip_analiz <IP adresi>`\nÖrnek: `/ip_analiz 8.8.8.8`\n\n"
            "_VPN/Proxy/Tor tespiti, tehdit skoru, açık portlar ve daha fazlası._",
            parse_mode='Markdown'
        )
        return
    ip_adresi = context.args[0].strip()
    if not re.match(r'^[0-9a-fA-F.:]{3,45}$', ip_adresi):
        await update.effective_message.reply_text("❌ Geçersiz IP formatı. Örnek: `/ip_analiz 8.8.8.8`", parse_mode='Markdown')
        return
    bekle = await update.effective_message.reply_text(
        f"🔍 `{ip_adresi}` analiz ediliyor...\n_Bu işlem birkaç saniye sürebilir._",
        parse_mode='Markdown'
    )
    try:
        rapor = await ip_tam_analiz_yap(ip_adresi)
        await bekle.edit_text(rapor, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"IP analiz hatası: {e}")
        await bekle.edit_text("❌ Analiz sırasında bir hata oluştu. Lütfen tekrar dene.")

# --- YÖNETİM KANALINDAN ÜYELERE KOPYALAMA SİSTEMİ ---
async def _toplu_gonderim_yap(bot, channel_post, rapor_chat_id):
    tum_uyeler = uyeleri_getir()
    if not tum_uyeler:
        return
    basarili = 0
    liste_degisti = False
    for u_id in list(tum_uyeler):
        try:
            await bot.copy_message(
                chat_id=u_id,
                from_chat_id=channel_post.chat_id,
                message_id=channel_post.message_id
            )
            basarili += 1
            await asyncio.sleep(0.05)
        except Exception:
            tum_uyeler.discard(u_id)
            liste_degisti = True
    if liste_degisti:
        uyeleri_kaydet(tum_uyeler)
    try:
        await bot.send_message(
            chat_id=rapor_chat_id,
            text=f"📢 **Toplu Gönderim Tamamlandı!**\n\nİçerik toplam `{basarili}` kullanıcıya ulaştırıldı. 🔥"
        )
    except Exception:
        pass

async def grup_ve_kanal_mesaj_yonet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        channel_post = update.channel_post

        if channel_post.chat_id == YONETIM_KANAL_ID:
            await _toplu_gonderim_yap(context.bot, channel_post, YONETIM_KANAL_ID)

        elif channel_post.text:
            if channel_post.sender_chat or (channel_post.from_user and channel_post.from_user.is_bot):
                return
            komut_parcalari = channel_post.text.split()[0].split('@')
            if komut_parcalari[0] == '/start':
                if len(komut_parcalari) == 1 or (len(komut_parcalari) > 1 and "azr" in komut_parcalari[1].lower()):
                    try:
                        bot_msg = await context.bot.send_message(
                            chat_id=channel_post.chat_id,
                            text="⚠️ **Bu mesaj sadece kanalda çalışır! Botun tüm menü ve özelliklerini kullanmak için lütfen DM (Özel Mesaj) üzerinden bota yazın.**"
                        )
                        asyncio.create_task(mesajlari_5s_sonra_sil(context, channel_post.chat_id, bot_msg.message_id, channel_post.message_id))
                    except Exception:
                        pass

    elif update.message:
        if update.message.from_user and update.message.from_user.is_bot:
            return

        # Gece modu: ZAMANLI_KANAL_ID grubundaki tüm mesajları max 2 saniyede sil
        if update.message.chat_id == ZAMANLI_KANAL_ID and gece_modu_aktif_mi():
            await asyncio.sleep(1.5)
            try:
                await context.bot.delete_message(
                    chat_id=ZAMANLI_KANAL_ID,
                    message_id=update.message.message_id
                )
            except Exception:
                pass
            return

        if update.message.text and update.message.text.startswith('/'):
            komut_parcalari = update.message.text.split()[0].split('@')
            if komut_parcalari[0] == '/start':
                if len(komut_parcalari) == 1 or (len(komut_parcalari) > 1 and "azr" in komut_parcalari[1].lower()):
                    try:
                        bot_msg = await update.message.reply_text("⚠️ **Bu komut kanalda çalışmaz sadece dm de çalışa bilir!**")
                        asyncio.create_task(
                            mesajlari_5s_sonra_sil(
                                context,
                                chat_id=update.message.chat_id,
                                bot_msg_id=bot_msg.message_id,
                                user_msg_id=update.message.message_id
                            )
                        )
                    except Exception:
                        pass

# --- BOT DM TETİKLEYİCİLERİ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(context, user_id)
    tum_uyeler = uyeleri_getir()
    if user_id not in tum_uyeler:
        tum_uyeler.add(user_id)
        uyeleri_kaydet(tum_uyeler)

    if 'lang' not in context.bot_data:
        context.bot_data['lang'] = {}
    context.bot_data['lang'][user_id] = lang

    if not await kanal_takip_kontrol(update, context, user_id, lang):
        return

    def yuklenme_cubugu(yuzde: int) -> str:
        dolu = yuzde // 10
        bos  = 10 - dolu
        return f"🚀 *AZRxGUARD Başlatılıyor...*\n\n{'█' * dolu}{'░' * bos}  {yuzde}%"

    mesaj = await update.message.reply_text(yuklenme_cubugu(0), parse_mode='Markdown')
    for yuzde in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        await asyncio.sleep(0.3)
        try:
            await mesaj.edit_text(yuklenme_cubugu(yuzde), parse_mode='Markdown')
        except Exception:
            pass
    await asyncio.sleep(0.4)
    await mesaj.edit_text(LANG_DATA[lang]['welcome'], reply_markup=ana_menu_klavye(lang), parse_mode='Markdown')

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang = get_lang(context, user_id)
    strings = LANG_DATA[lang]
    await query.answer()

    if not await kanal_takip_kontrol(update, context, user_id, lang):
        return

    if query.data == 'menu_lang':
        dil_klavye = [
            [InlineKeyboardButton("🇹🇷 Türkçe", callback_data='set_lang_tr'), InlineKeyboardButton("🇦🇿 Azərbaycanca", callback_data='set_lang_az')],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang_ru'), InlineKeyboardButton("🇬🇧 English", callback_data='set_lang_en')],
            [InlineKeyboardButton("🇩🇪 Deutsch", callback_data='set_lang_de'), InlineKeyboardButton("🇬🇪 ქართული", callback_data='set_lang_ka')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(strings['lang_select'], reply_markup=InlineKeyboardMarkup(dil_klavye), parse_mode='Markdown')
    elif query.data.startswith('set_lang_'):
        yeni_dil = query.data.split('_')[-1]
        if 'lang' not in context.bot_data:
            context.bot_data['lang'] = {}
        context.bot_data['lang'][user_id] = yeni_dil
        yeni_strings = LANG_DATA[yeni_dil]
        await query.edit_message_text(
            f"{yeni_strings['lang_changed']}\n\n{yeni_strings['welcome']}",
            reply_markup=ana_menu_klavye(yeni_dil),
            parse_mode='Markdown'
        )
    elif query.data == 'menu_admin':
        context.user_data['durum'] = 'admin_mesaj_bekliyor'
        await query.edit_message_text(strings['ask_admin_msg'], parse_mode='Markdown')
    elif query.data == 'menu_fun':
        fun_klavye = [
            [InlineKeyboardButton(strings['btn_roll_dice'], callback_data='roll_dice')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(strings['fun_welcome'], reply_markup=InlineKeyboardMarkup(fun_klavye), parse_mode='Markdown')
    elif query.data == 'menu_ip_sorgu':
        ip_klavye = [
            [
                InlineKeyboardButton(strings.get('btn_ip', '🌐 IP Sorgula'), callback_data='menu_ip'),
                InlineKeyboardButton('🛡️ IP Analiz', callback_data='menu_ip_analiz')
            ],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(
            strings.get('ip_sorgu_welcome', '🌐 **IP Sorgu Menüsü**\n\nAşağıdan sorgu türünü seçin:'),
            reply_markup=InlineKeyboardMarkup(ip_klavye), parse_mode='Markdown'
        )
    elif query.data == 'menu_azr_special':
        azr_klavye = [
            [InlineKeyboardButton(strings['btn_stats'], callback_data='show_inline_stats')],
            [InlineKeyboardButton(strings['btn_meid'], callback_data='show_meid')],
            [InlineKeyboardButton(strings.get('btn_hatirlat', '⏰ Hatırlatıcı'), callback_data='menu_hatirlat')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(strings['azr_welcome'], reply_markup=InlineKeyboardMarkup(azr_klavye), parse_mode='Markdown')
    elif query.data == 'show_inline_stats':
        rapor_metni = istatistik_raporu_hazirla(context)
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_azr_special')]])
        await query.edit_message_text(text=rapor_metni, reply_markup=geri_klavye, parse_mode='Markdown')
    elif query.data == 'show_meid':
        bilgi = await meid_bilgisi_olustur(context.bot, update, context, lang)
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_azr_special')]])
        await query.edit_message_text(text=bilgi, reply_markup=geri_klavye, parse_mode='Markdown')
    elif query.data == 'menu_hatirlat':
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_azr_special')]])
        await query.edit_message_text(
            "⏰ **Hatırlatıcı**\n\n"
            "Örnek: `/hatirlat 21:20 Ödev`\n"
            "Örnek: `/hatirlat 25.05.2026 09:00 Toplantı`\n\n"
            "_Saat Azerbaycan saatiyle çalışır_ 🇦🇿",
            reply_markup=geri_klavye, parse_mode='Markdown'
        )
    elif query.data == 'menu_ip':
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_ip_sorgu')]])
        context.user_data['durum'] = 'ip_bekliyor'
        await query.edit_message_text(
            strings.get('ip_ask', '🌐 **IP Sorgulama**\n\nSorgulamak istediğiniz IP adresini yazın:\nÖrnek: `8.8.8.8`'),
            reply_markup=geri_klavye, parse_mode='Markdown'
        )
    elif query.data == 'menu_ip_analiz':
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_ip_sorgu')]])
        context.user_data['durum'] = 'ip_analiz_bekliyor'
        await query.edit_message_text(
            "🛡️ **IP Güvenlik Analizi**\n\nAnaliz etmek istediğiniz IP adresini yazın:\nÖrnek: `185.220.101.1`",
            reply_markup=geri_klavye, parse_mode='Markdown'
        )
    elif query.data == 'roll_dice':
        await query.message.delete()
        await query.message.chat.send_dice(emoji='🎲')
    elif query.data == 'menu_panel':
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]])
        context.user_data['durum'] = 'panel_sorgu_bekliyor'
        await query.edit_message_text(
            strings.get('panel_welcome', '🔍 **PANEL**\n\n@kullaniciadi veya ID yaz:'),
            reply_markup=geri_klavye,
            parse_mode='Markdown'
        )
    elif query.data == 'menu_guvenli_sorgu':
        gs_klavye = [
            [InlineKeyboardButton(strings.get('btn_username_checker', '🔎 Platform Kontrolü'), callback_data='menu_username_checker')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(
            strings.get('guvenli_sorgu_welcome', '🕵️ **USERNAME HUNTER**\n\nKullanıcı adını 14 platformda tara:'),
            reply_markup=InlineKeyboardMarkup(gs_klavye),
            parse_mode='Markdown'
        )
    elif query.data == 'menu_username_checker':
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_guvenli_sorgu')]])
        context.user_data['durum'] = 'username_checker_bekliyor'
        await query.edit_message_text(
            strings.get('username_checker_ask', '🔎 Kullanıcı adını yaz:'),
            reply_markup=geri_klavye,
            parse_mode='Markdown'
        )
    elif query.data == 'menu_pro_araclar':
        pro_klavye = [
            [InlineKeyboardButton(strings.get('btn_hesap_arac', '🧮 Hesap Makinesi'), callback_data='pro_hesap'),
             InlineKeyboardButton(strings.get('btn_hash_arac', '🔐 Hash Üretici'), callback_data='pro_hash')],
            [InlineKeyboardButton(strings.get('btn_hava_arac', '🌍 Hava Durumu'), callback_data='pro_hava'),
             InlineKeyboardButton(strings.get('btn_doviz_arac', '💱 Döviz Kuru'), callback_data='pro_doviz')],
            [InlineKeyboardButton(strings.get('btn_saat_arac', '🕐 Dünya Saati'), callback_data='pro_saat'),
             InlineKeyboardButton(strings.get('btn_b64_arac', '🔒 Base64'), callback_data='pro_b64')],
            [InlineKeyboardButton(strings.get('btn_sifre_arac', '🔑 Şifre Üretici'), callback_data='pro_sifre'),
             InlineKeyboardButton(strings.get('btn_wiki_arac', '🌐 Wikipedia'), callback_data='pro_wiki')],
            [InlineKeyboardButton(strings.get('btn_not_arac', '📝 Not Defterim'), callback_data='pro_not'),
             InlineKeyboardButton(strings.get('btn_gunsozu_arac', '💡 Günün Sözü'), callback_data='pro_gunsozu')],
            [InlineKeyboardButton(strings.get('btn_birim_arac', '📐 Birim Çevir'), callback_data='pro_birim'),
             InlineKeyboardButton(strings.get('btn_sans_arac', '🎱 Şans Topu'), callback_data='pro_sans')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(
            strings.get('pro_araclar_welcome', '⚡ **PRO ARAÇLAR**\n\nBir araç seçin:'),
            reply_markup=InlineKeyboardMarkup(pro_klavye),
            parse_mode='Markdown'
        )
    elif query.data == 'pro_hesap':
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        context.user_data['durum'] = 'hesap_bekliyor'
        await query.edit_message_text(strings.get('hesap_ask', '🧮 Matematik ifadesi girin:'), reply_markup=geri, parse_mode='Markdown')
    elif query.data == 'pro_hash':
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        context.user_data['durum'] = 'hash_bekliyor'
        await query.edit_message_text(strings.get('hash_ask', '🔐 Hashlenecek metni girin:'), reply_markup=geri, parse_mode='Markdown')
    elif query.data == 'pro_hava':
        await query.edit_message_text(
            strings.get('hava_ulke_sec', '🌍 Ülke seçin:'),
            reply_markup=ulke_klavyesi('menu_pro_araclar'),
            parse_mode='Markdown'
        )
    elif query.data.startswith('hava_u_'):
        ulke_kodu = query.data[7:]
        ulke = ULKE_HIYERARSI.get(ulke_kodu)
        if ulke:
            await query.edit_message_text(
                f"{ulke['flag']} **{ulke['name']}** — Kategori seçin:",
                reply_markup=kategori_klavyesi(ulke_kodu),
                parse_mode='Markdown'
            )
    elif query.data.startswith('hava_cs_'):
        ulke_kodu = query.data[8:]
        ulke = ULKE_HIYERARSI.get(ulke_kodu)
        if ulke:
            await query.edit_message_text(
                f"{ulke['flag']} **{ulke['name']}** — 🏙 Şehir seçin:",
                reply_markup=sehirler_klavyesi(ulke_kodu),
                parse_mode='Markdown'
            )
    elif query.data.startswith('hava_kv_'):
        ulke_kodu = query.data[8:]
        ulke = ULKE_HIYERARSI.get(ulke_kodu)
        if ulke:
            koyler = ulke.get('koyler', [])
            baslik = "Rayon seçin:" if isinstance(koyler, dict) else "🏘 Köy/Kənd seçin:"
            await query.edit_message_text(
                f"{ulke['flag']} **{ulke['name']}** — {baslik}",
                reply_markup=koyler_klavyesi(ulke_kodu),
                parse_mode='Markdown'
            )
    elif query.data.startswith('hava_kr_'):
        rest = query.data[8:]
        parts = rest.split(':', 1)
        if len(parts) == 2:
            ulke_kodu, rayon = parts
            ulke = ULKE_HIYERARSI.get(ulke_kodu, {})
            rayon_display = rayon.replace(' 🇦🇿', '')
            await query.edit_message_text(
                f"🏘 **{rayon_display}** — Köy/Kənd seçin:",
                reply_markup=koy_rayon_klavyesi(ulke_kodu, rayon),
                parse_mode='Markdown'
            )
    elif query.data.startswith('hava_ci_'):
        rest = query.data[8:]
        parts = rest.split(':', 1)
        if len(parts) == 2:
            ulke_kodu, sehir = parts
            ulke = ULKE_HIYERARSI.get(ulke_kodu)
            if ulke:
                await query.edit_message_text(
                    f"{ulke['flag']} **{sehir}** — Rayon/İlçe seçin:",
                    reply_markup=rayon_klavyesi(ulke_kodu, sehir),
                    parse_mode='Markdown'
                )
    elif query.data.startswith('hava_ri_'):
        rest = query.data[8:]
        parts = rest.split(':', 2)
        if len(parts) == 3:
            ulke_kodu, sehir, rayon = parts
            ulke = ULKE_HIYERARSI.get(ulke_kodu)
            if ulke:
                await query.edit_message_text(
                    f"📍 **{rayon}** ({sehir}) — Köy/Kənd seçin:",
                    reply_markup=koy_listesi_klavyesi(ulke_kodu, sehir, rayon),
                    parse_mode='Markdown'
                )
    elif query.data.startswith('hava_wx_'):
        lokasyon = query.data[8:]
        await query.answer()
        bekle_msg = await query.message.reply_text(f"🌍 `{html.escape(lokasyon)}` hava durumu getiriliyor...", parse_mode='Markdown')
        sonuc = await hava_durumu_getir(lokasyon)
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Başka Konum", callback_data='pro_hava')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        try:
            await bekle_msg.edit_text(sonuc, parse_mode='Markdown', reply_markup=geri)
        except Exception:
            await bekle_msg.edit_text(sonuc, reply_markup=geri)
        return
    elif query.data.startswith('hava_sx_'):
        ulke_kodu = query.data[8:]
        ulke = ULKE_HIYERARSI.get(ulke_kodu, {})
        context.user_data['durum'] = 'hava_arama'
        context.user_data['hava_ulke'] = ulke_kodu
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data=f"hava_u_{ulke_kodu}")]])
        await query.edit_message_text(
            f"🔍 **Konum Arama**\n\n{ulke.get('flag', '')} **{ulke.get('name', '')}**\n\n"
            f"Aradığınız şehir, köy veya bölge adını yazın:\n"
            f"_(Örnek: Marneuli, Bakuriani, Ushguli)_",
            reply_markup=geri,
            parse_mode='Markdown'
        )
    elif query.data == 'pro_doviz':
        await query.edit_message_text(
            strings.get('doviz_from_sec', '💱 Kaynak döviz seçin:'),
            reply_markup=doviz_from_klavyesi(),
            parse_mode='Markdown'
        )
    elif query.data.startswith('kur_f_'):
        from_kur = query.data[6:]
        await query.edit_message_text(
            strings.get('doviz_to_sec', '💱 Hedef döviz seçin:'),
            reply_markup=doviz_to_klavyesi(from_kur),
            parse_mode='Markdown'
        )
    elif query.data.startswith('kur_t_'):
        parts = query.data[6:].split('_', 1)
        if len(parts) == 2:
            from_kur, to_kur = parts[0], parts[1]
            context.user_data['kur_from'] = from_kur
            context.user_data['kur_to'] = to_kur
            context.user_data['durum'] = 'kur_miktar_bekliyor'
            geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='pro_doviz')]])
            await query.edit_message_text(
                f"💱 `{from_kur}` → `{to_kur}`\n\n" + strings.get('doviz_miktar_ask', '💰 Miktarı girin:'),
                reply_markup=geri,
                parse_mode='Markdown'
            )
    elif query.data == 'pro_saat':
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yenile", callback_data='pro_saat')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        await query.edit_message_text(dunya_saati(), reply_markup=geri, parse_mode='Markdown')
    elif query.data == 'pro_b64':
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        context.user_data['durum'] = 'b64_bekliyor'
        await query.edit_message_text(strings.get('b64_ask', '🔒 encode metin / decode bWV0aW4='), reply_markup=geri, parse_mode='Markdown')
    elif query.data == 'pro_sifre':
        sifre_klavye = [
            [InlineKeyboardButton("8 karakter", callback_data='sifre_8'),
             InlineKeyboardButton("12 karakter", callback_data='sifre_12'),
             InlineKeyboardButton("16 karakter", callback_data='sifre_16')],
            [InlineKeyboardButton("20 karakter", callback_data='sifre_20'),
             InlineKeyboardButton("24 karakter", callback_data='sifre_24'),
             InlineKeyboardButton("32 karakter", callback_data='sifre_32')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ]
        await query.edit_message_text(
            "🔑 **ŞİFRE ÜRETİCİ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nKaç karakterli şifre üreteyim?\n_Büyük harf + rakam + sembol içerir._",
            reply_markup=InlineKeyboardMarkup(sifre_klavye),
            parse_mode='Markdown'
        )
    elif query.data.startswith('sifre_'):
        uzunluk = int(query.data.split('_')[1])
        sifre1 = sifre_uret(uzunluk)
        sifre2 = sifre_uret(uzunluk)
        sifre3 = sifre_uret(uzunluk)
        yenile_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yenile", callback_data=query.data),
             InlineKeyboardButton("📏 Başka Uzunluk", callback_data='pro_sifre')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        await query.edit_message_text(
            f"🔑 **{uzunluk} Karakterli Şifreler**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"1️⃣ `{sifre1}`\n"
            f"2️⃣ `{sifre2}`\n"
            f"3️⃣ `{sifre3}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Kopyalamak için şifreye dokun._",
            reply_markup=yenile_klavye,
            parse_mode='Markdown'
        )
    elif query.data == 'pro_wiki':
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        context.user_data['durum'] = 'wiki_bekliyor'
        await query.edit_message_text(
            "🌐 **WİKİPEDİA ARAMA**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Aramak istediğiniz konuyu yazın:\nÖrnek: `Marneuli`, `Tbilisi`, `Azerbaycan`\n\n"
            "_Seçtiğiniz dilde aranır, yoksa İngilizce._",
            reply_markup=geri,
            parse_mode='Markdown'
        )
    elif query.data == 'pro_not':
        notlar = not_yukle(user_id)
        not_klavye_geri = [[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]]
        if not notlar:
            await query.edit_message_text(
                "📝 **NOT DEFTERİM**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n📭 Henüz hiç notun yok.\n\n✍️ İlk notunu eklemek için aşağıdaki butona bas!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Not Ekle", callback_data='not_ekle')],
                    *not_klavye_geri
                ]),
                parse_mode='Markdown'
            )
        else:
            not_metni = f"📝 **NOT DEFTERİM** ({len(notlar)} not)\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, not_ in enumerate(notlar[-10:], 1):
                not_metni += f"{i}\\. {not_[:80]}\n"
            await query.edit_message_text(
                not_metni,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Not Ekle", callback_data='not_ekle'),
                     InlineKeyboardButton("🗑️ Not Sil", callback_data='not_sil_menu')],
                    *not_klavye_geri
                ]),
                parse_mode='MarkdownV2'
            )
    elif query.data == 'not_ekle':
        context.user_data['durum'] = 'not_ekle_bekliyor'
        await query.edit_message_text(
            "📝 **Not Ekle**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nYeni notunu yaz:\n_İptal için /start yaz_",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='pro_not')]]),
            parse_mode='Markdown'
        )
    elif query.data == 'not_sil_menu':
        notlar = not_yukle(user_id)
        if not notlar:
            await query.answer("Silinecek not yok!", show_alert=True)
            return
        satirlar = []
        for i, not_ in enumerate(notlar):
            satirlar.append([InlineKeyboardButton(f"🗑️ {i+1}. {not_[:28]}...", callback_data=f"not_sil_{i}")])
        satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data='pro_not')])
        await query.edit_message_text(
            "🗑️ **Silmek istediğin notu seç:**",
            reply_markup=InlineKeyboardMarkup(satirlar),
            parse_mode='Markdown'
        )
    elif query.data.startswith('not_sil_') and query.data != 'not_sil_menu':
        idx = int(query.data[8:])
        notlar = not_yukle(user_id)
        if 0 <= idx < len(notlar):
            notlar.pop(idx)
            not_kaydet(user_id, notlar)
            await query.answer("✅ Not silindi!", show_alert=False)
        if not notlar:
            await query.edit_message_text(
                "📝 **NOT DEFTERİM**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n📭 Tüm notlar silindi.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Not Ekle", callback_data='not_ekle')],
                    [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
                ]),
                parse_mode='Markdown'
            )
        else:
            not_metni = f"📝 **NOT DEFTERİM** ({len(notlar)} not)\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, n in enumerate(notlar[-10:], 1):
                not_metni += f"{i}\\. {n[:80]}\n"
            await query.edit_message_text(
                not_metni,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Not Ekle", callback_data='not_ekle'),
                     InlineKeyboardButton("🗑️ Not Sil", callback_data='not_sil_menu')],
                    [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
                ]),
                parse_mode='MarkdownV2'
            )
    elif query.data == 'pro_gunsozu':
        soz = gunun_sozu_getir()
        await query.edit_message_text(
            f"💡 **GÜNÜN SÖZÜ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n{soz}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Yeni Söz", callback_data='pro_gunsozu')],
                [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
            ]),
            parse_mode='Markdown'
        )
    elif query.data == 'pro_birim':
        await query.edit_message_text(
            "📐 **BİRİM ÇEVİRİCİSİ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nHangi birim kategorisini görmek istiyorsunuz?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌡️ Sıcaklık (°C/°F/K)", callback_data='birim_sicaklik'),
                 InlineKeyboardButton("📏 Uzunluk (km/m/mil)", callback_data='birim_uzunluk')],
                [InlineKeyboardButton("⚖️ Ağırlık (kg/lb/g)", callback_data='birim_agirlik'),
                 InlineKeyboardButton("🚗 Hız (km/s-mph)", callback_data='birim_hiz')],
                [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
            ]),
            parse_mode='Markdown'
        )
    elif query.data.startswith('birim_'):
        tip = query.data[6:]
        tablo = BIRIM_TABLOLARI.get(tip, "❌ Bilinmeyen kategori.")
        await query.edit_message_text(
            tablo,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌡️ Sıcaklık", callback_data='birim_sicaklik'),
                 InlineKeyboardButton("📏 Uzunluk", callback_data='birim_uzunluk')],
                [InlineKeyboardButton("⚖️ Ağırlık", callback_data='birim_agirlik'),
                 InlineKeyboardButton("🚗 Hız", callback_data='birim_hiz')],
                [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
            ]),
            parse_mode='Markdown'
        )
    elif query.data == 'pro_sans':
        await query.edit_message_text(
            sans_cevap_getir(),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎱 Tekrar Sor", callback_data='pro_sans')],
                [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
            ]),
            parse_mode='Markdown'
        )
    elif query.data == 'go_home':
        await query.edit_message_text(strings['welcome'], reply_markup=ana_menu_klavye(lang), parse_mode='Markdown')

async def gelen_mesajlari_yonet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(context, user_id)
    strings = LANG_DATA[lang]
    if not await kanal_takip_kontrol(update, context, user_id, lang):
        return

    if context.user_data.get('durum') == 'admin_mesaj_bekliyor':
        user = update.effective_user
        guvenli_isim = html.escape(user.first_name) if user.first_name else "Kullanıcı"
        guvenli_mesaj = html.escape(update.message.text) if update.message.text else ""
        username = f"@{user.username}" if user.username else "Yok"
        tiklanabilir_isim = f'<a href="tg://user?id={user.id}">{guvenli_isim}</a> ({user.id})'
        rapor = (
            f"📩 <b>YENİ ADMİN MESAJI!</b>\n\n"
            f"👤 <b>Gönderen:</b> {tiklanabilir_isim}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"🏷️ <b>Kullanıcı Adı:</b> {username}\n"
            f"💬 <b>İletilen Mesaj:</b> {guvenli_mesaj}"
        )
        try:
            await context.bot.send_message(chat_id=MY_ID, text=rapor, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Kurucuya mesaj hatası: {e}")
        try:
            await context.bot.send_message(chat_id=KANAL_ID, text=rapor, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Kanala mesaj hatası: {e}")
        try:
            await update.message.reply_text(strings['msg_sent'], parse_mode='Markdown')
            await update.message.reply_text(strings['welcome'], reply_markup=ana_menu_klavye(lang), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Cevap iletme hatası: {e}")
        context.user_data['durum'] = None
        return

    if context.user_data.get('durum') == 'ip_bekliyor':
        context.user_data['durum'] = None
        ip_adresi = update.message.text.strip()
        if not re.match(r'^[0-9a-fA-F.:]{3,45}$', ip_adresi):
            await update.message.reply_text("❌ Geçersiz IP formatı. Örnek: `8.8.8.8`", parse_mode='Markdown')
            return
        bekle = await update.message.reply_text(f"🔍 `{ip_adresi}` sorgulanıyor...", parse_mode='Markdown')
        try:
            veri = await asyncio.to_thread(_ipapi_basit_getir, ip_adresi)
            rapor = ip_basit_rapor(veri, ip_adresi)
            await bekle.edit_text(rapor, parse_mode='Markdown', disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"IP menü hatası: {e}")
            await bekle.edit_text("❌ Sorgulama sırasında bir hata oluştu.")
        return

    if context.user_data.get('durum') == 'ip_analiz_bekliyor':
        context.user_data['durum'] = None
        ip_adresi = update.message.text.strip()
        if not re.match(r'^[0-9a-fA-F.:]{3,45}$', ip_adresi):
            await update.message.reply_text("❌ Geçersiz IP formatı. Örnek: `185.220.101.1`", parse_mode='Markdown')
            return
        bekle = await update.message.reply_text(
            f"🔍 `{ip_adresi}` analiz ediliyor...\n_Bu işlem birkaç saniye sürebilir._",
            parse_mode='Markdown'
        )
        try:
            rapor = await ip_tam_analiz_yap(ip_adresi)
            await bekle.edit_text(rapor, parse_mode='Markdown', disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"IP analiz menü hatası: {e}")
            await bekle.edit_text("❌ Analiz sırasında bir hata oluştu.")
        return

    if context.user_data.get('durum') == 'username_checker_bekliyor':
        context.user_data['durum'] = None
        kullanici_adi = update.message.text.strip()
        bekle = await update.message.reply_text(
            f"🔎 `@{kullanici_adi.lstrip('@')}` 14 platformda kontrol ediliyor...\n_Bu işlem ~10 saniye sürebilir._",
            parse_mode='Markdown'
        )
        rapor = await platform_username_kontrol(kullanici_adi)
        geri_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔎 Yeni Kontrol", callback_data='menu_username_checker')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_guvenli_sorgu')]
        ])
        try:
            await bekle.edit_text(rapor, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=geri_klavye)
        except Exception:
            await bekle.edit_text(rapor, disable_web_page_preview=True, reply_markup=geri_klavye)
        return

    if context.user_data.get('durum') == 'panel_sorgu_bekliyor':
        context.user_data['durum'] = None
        sorgu = update.message.text.strip()
        bekle = await update.message.reply_text(
            strings.get('panel_sorgulanıyor', '🔍 Sorgulanıyor...'),
            parse_mode='Markdown'
        )
        rapor = await panel_kullanici_sorgula(context.bot, sorgu)
        geri_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Yeni Sorgu", callback_data='menu_panel')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ])
        if rapor:
            try:
                await bekle.edit_text(rapor, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=geri_klavye)
            except Exception:
                await bekle.edit_text(rapor, disable_web_page_preview=True, reply_markup=geri_klavye)
        else:
            await bekle.edit_text(
                strings.get('panel_bulunamadi', '❌ Kullanıcı bulunamadı!'),
                parse_mode='Markdown',
                reply_markup=geri_klavye
            )
        return

    # --- ⚡ PRO ARAÇLAR mesaj state'leri ---
    if context.user_data.get('durum') == 'hesap_bekliyor':
        context.user_data['durum'] = None
        ifade = update.message.text.strip()
        sonuc = guvenli_hesapla(ifade)
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yeni Hesap", callback_data='pro_hesap')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        await update.message.reply_text(sonuc, parse_mode='Markdown', reply_markup=geri)
        return

    if context.user_data.get('durum') == 'hash_bekliyor':
        context.user_data['durum'] = None
        metin = update.message.text.strip()
        sonuc = hash_uret(metin)
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yeni Hash", callback_data='pro_hash')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        await update.message.reply_text(sonuc, parse_mode='Markdown', reply_markup=geri)
        return

    if context.user_data.get('durum') == 'hava_bekliyor':
        context.user_data['durum'] = None
        sehir = update.message.text.strip()
        bekle = await update.message.reply_text(f"🌍 `{html.escape(sehir)}` için hava durumu getiriliyor...", parse_mode='Markdown')
        sonuc = await hava_durumu_getir(sehir)
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yeni Şehir", callback_data='pro_hava')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        try:
            await bekle.edit_text(sonuc, parse_mode='Markdown', reply_markup=geri)
        except Exception:
            await bekle.edit_text(sonuc, reply_markup=geri)
        return

    if context.user_data.get('durum') == 'kur_miktar_bekliyor':
        context.user_data['durum'] = None
        from_kur = context.user_data.pop('kur_from', 'USD')
        to_kur   = context.user_data.pop('kur_to', 'EUR')
        miktar_str = update.message.text.strip().replace(',', '.')
        try:
            float(miktar_str)
        except ValueError:
            await update.message.reply_text("❌ Geçersiz miktar! Sadece sayı girin. Örnek: `100`", parse_mode='Markdown')
            return
        bekle = await update.message.reply_text("💱 Kur bilgisi getiriliyor...", parse_mode='Markdown')
        sonuc = await doviz_cevir(f"{miktar_str} {from_kur} {to_kur}")
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yeni Çeviri", callback_data='pro_doviz')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        try:
            await bekle.edit_text(sonuc, parse_mode='Markdown', reply_markup=geri)
        except Exception:
            await bekle.edit_text(sonuc, reply_markup=geri)
        return

    if context.user_data.get('durum') == 'hava_arama':
        context.user_data['durum'] = None
        lokasyon = update.message.text.strip()
        ulke_kodu = context.user_data.pop('hava_ulke', 'ge')
        bekle = await update.message.reply_text(f"🔍 `{html.escape(lokasyon)}` aranıyor...", parse_mode='Markdown')
        sonuc = await hava_durumu_getir(lokasyon)
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Tekrar Ara", callback_data=f"hava_sx_{ulke_kodu}")],
            [InlineKeyboardButton("🌍 Ülke Seç", callback_data='pro_hava')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        try:
            await bekle.edit_text(sonuc, parse_mode='Markdown', reply_markup=geri)
        except Exception:
            await bekle.edit_text(sonuc, reply_markup=geri)
        return

    if context.user_data.get('durum') == 'b64_bekliyor':
        context.user_data['durum'] = None
        metin = update.message.text.strip()
        sonuc = base64_islem(metin)
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yeni İşlem", callback_data='pro_b64')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        await update.message.reply_text(sonuc, parse_mode='Markdown', reply_markup=geri)
        return

    if context.user_data.get('durum') == 'wiki_bekliyor':
        context.user_data['durum'] = None
        sorgu = update.message.text.strip()
        bekle = await update.message.reply_text(f"🌐 `{html.escape(sorgu)}` Wikipedia'da aranıyor...", parse_mode='Markdown')
        sonuc = await wikipedia_ara(sorgu, lang)
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Başka Arama", callback_data='pro_wiki')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        try:
            await bekle.edit_text(sonuc, parse_mode='Markdown', reply_markup=geri, disable_web_page_preview=True)
        except Exception:
            await bekle.edit_text(sonuc, reply_markup=geri, disable_web_page_preview=True)
        return

    if context.user_data.get('durum') == 'not_ekle_bekliyor':
        context.user_data['durum'] = None
        yeni_not = update.message.text.strip()
        if not yeni_not:
            return
        notlar = not_yukle(user_id)
        notlar.append(yeni_not)
        not_kaydet(user_id, notlar)
        await update.message.reply_text(
            f"✅ **Not kaydedildi!**\n\n`{html.escape(yeni_not[:120])}`\n\n📝 Toplam {len(notlar)} not.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Not Defterime Git", callback_data='pro_not'),
                 InlineKeyboardButton("➕ Bir Tane Daha", callback_data='not_ekle')],
                [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
            ])
        )
        return

# --- 🖼️ FİLİGRAN SİSTEMİ ---
FILIGRAN_KANALLARI = {-1003775055611, -1003930940829}
FILIGRAN_KANAL_LINK = "https://t.me/azrXmaqa"

async def filigran_ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = update.effective_message
    if mesaj is None:
        return
    if not (mesaj.photo or mesaj.video):
        return

    gonderen = update.effective_user
    kanal_post = update.channel_post is not None
    chat_id = mesaj.chat_id

    logger.info(f"Filigran tetiklendi: chat_id={chat_id}, kanal_post={kanal_post}, user={getattr(gonderen, 'id', None)}")

    filigran_klavye = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanala Git", url=FILIGRAN_KANAL_LINK)]
    ])

    if kanal_post:
        if chat_id not in FILIGRAN_KANALLARI:
            logger.info(f"Filigran: kanal {chat_id} listede yok, atlanıyor.")
            return
        hedef = chat_id if chat_id != -1003775055611 else chat_id
        try:
            await context.bot.send_message(chat_id=hedef, text=FILIGRAN_METNI, reply_markup=filigran_klavye)
            logger.info(f"Filigran gönderildi: {hedef}")
        except Exception as e:
            logger.warning(f"Filigran ID ile gönderilemedi ({hedef}): {e} — @AZRxMAQAsohbet deneniyor")
            try:
                await context.bot.send_message(chat_id="@AZRxMAQAsohbet", text=FILIGRAN_METNI, reply_markup=filigran_klavye)
                logger.info("Filigran @AZRxMAQAsohbet ile gönderildi.")
            except Exception as e2:
                logger.error(f"Filigran @AZRxMAQAsohbet ile de gönderilemedi: {e2}")
    else:
        if gonderen is None or gonderen.id != MY_ID:
            return
        try:
            await mesaj.reply_text(FILIGRAN_METNI, reply_markup=filigran_klavye)
        except Exception as e:
            logger.error(f"Filigran (DM/grup) eklenemedi: {e}")

# --- ⏰ KİŞİSEL HATIRLATICI ---

async def hatirlat_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    yardim = (
        "⏰ **Hatırlatıcı**\n\n"
        "Örnek: `/hatirlat 21:20 Ödev`\n"
        "Örnek: `/hatirlat 25.05.2026 09:00 Toplantı`"
    )
    if not context.args:
        await update.effective_message.reply_text(yardim, parse_mode='Markdown')
        return

    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id
    args = context.args
    simdi = datetime.datetime.now(AZ_SAAT)
    hedef_zaman = None
    mesaj_parcalari = []

    # Format: GG.AA.YYYY HH:MM mesaj
    if len(args) >= 2 and re.match(r'^\d{2}\.\d{2}\.\d{4}$', args[0]) and re.match(r'^\d{2}:\d{2}$', args[1]):
        try:
            tarih = datetime.datetime.strptime(args[0], '%d.%m.%Y').date()
            s, m = int(args[1].split(':')[0]), int(args[1].split(':')[1])
            hedef_zaman = datetime.datetime(tarih.year, tarih.month, tarih.day, s, m, 0, tzinfo=AZ_SAAT)
            mesaj_parcalari = args[2:]
        except ValueError:
            pass

    # Format: GG.AA.YYYY mesaj (saat yok → 09:00)
    if hedef_zaman is None and re.match(r'^\d{2}\.\d{2}\.\d{4}$', args[0]):
        try:
            tarih = datetime.datetime.strptime(args[0], '%d.%m.%Y').date()
            hedef_zaman = datetime.datetime(tarih.year, tarih.month, tarih.day, 9, 0, 0, tzinfo=AZ_SAAT)
            mesaj_parcalari = args[1:]
        except ValueError:
            pass

    # Format: HH:MM mesaj (bugün)
    if hedef_zaman is None and re.match(r'^\d{2}:\d{2}$', args[0]):
        try:
            s, m = int(args[0].split(':')[0]), int(args[0].split(':')[1])
            hedef_zaman = simdi.replace(hour=s, minute=m, second=0, microsecond=0)
            mesaj_parcalari = args[1:]
        except ValueError:
            pass

    if hedef_zaman is None:
        await update.effective_message.reply_text(
            "❌ **Geçersiz format!**\n\n" + yardim, parse_mode='Markdown'
        )
        return

    if hedef_zaman <= simdi:
        await update.effective_message.reply_text(
            "❌ Belirtilen saat zaten geçmiş! Lütfen gelecekteki bir zaman girin.",
            parse_mode='Markdown'
        )
        return

    hatirlat_metni = " ".join(mesaj_parcalari).strip() if mesaj_parcalari else "⏰ Hatırlatıcı!"
    gecen_sure = (hedef_zaman - simdi).total_seconds()
    isim = user.first_name or "Kullanıcı"

    async def hatirlat_gonder(ctx: ContextTypes.DEFAULT_TYPE):
        try:
            await ctx.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"🔔 **HATIRLATICI!**\n\n"
                    f"👤 [{isim}](tg://user?id={user_id}), hatırlatıcın geldi!\n\n"
                    f"📝 **Not:** {hatirlat_metni}\n\n"
                    f"🕐 **Ayarlanan Saat:** `{hedef_zaman.strftime('%d.%m.%Y %H:%M')}` 🇦🇿"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Hatırlatıcı gönderilemedi: {e}")

    context.job_queue.run_once(
        hatirlat_gonder,
        when=gecen_sure,
        name=f"hatirlat_{user_id}_{int(hedef_zaman.timestamp())}"
    )

    await update.effective_message.reply_text(
        f"✅ **Hatırlatıcı Kuruldu!**\n\n"
        f"📅 **Zaman:** `{hedef_zaman.strftime('%d.%m.%Y saat %H:%M')}` 🇦🇿\n"
        f"📝 **Not:** {hatirlat_metni}\n\n"
        f"_O an geldiğinde seni burada etiketleyeceğim!_ ⏰",
        parse_mode='Markdown'
    )

# --- ⏰ ZAMANLI GÖREV FONKSİYONLARI ---

def id_den_kayit_tarihi_tahmin_et(user_id: int) -> str:
    if user_id < 0:
        abs_id = abs(user_id)
        if abs_id > 999_999_999_999:
            user_id = abs_id - 1_000_000_000_000
        else:
            user_id = abs_id
    if user_id <= 0:
        return "—"
    ref = [
        (0,              2013,  8),
        (10_000_000,     2013, 12),
        (100_000_000,    2016,  1),
        (200_000_000,    2017, 10),
        (300_000_000,    2018,  5),
        (400_000_000,    2019,  1),
        (500_000_000,    2019,  8),
        (600_000_000,    2020,  3),
        (700_000_000,    2020, 11),
        (800_000_000,    2021,  5),
        (900_000_000,    2021,  9),
        (1_000_000_000,  2022,  2),
        (1_200_000_000,  2022, 10),
        (1_500_000_000,  2023,  4),
        (1_800_000_000,  2023,  9),
        (2_000_000_000,  2024,  2),
        (2_500_000_000,  2024, 10),
        (3_000_000_000,  2025,  5),
        (3_500_000_000,  2025, 10),
        (4_000_000_000,  2026,  3),
        (4_500_000_000,  2026,  8),
        (5_000_000_000,  2027,  1),
    ]
    ay_adlari = {1:'Ocak',2:'Şubat',3:'Mart',4:'Nisan',5:'Mayıs',6:'Haziran',
                 7:'Temmuz',8:'Ağustos',9:'Eylül',10:'Ekim',11:'Kasım',12:'Aralık'}

    def hesapla(uid, p_id, p_y, p_m, r_id, r_y, r_m):
        ratio    = (uid - p_id) / max(r_id - p_id, 1)
        pm_total = p_y * 12 + p_m - 1
        rm_total = r_y * 12 + r_m - 1
        est      = pm_total + ratio * (rm_total - pm_total)
        y = int(est) // 12
        m = int(est) % 12 + 1
        return y, m

    p_id, p_y, p_m = ref[0]
    for r_id, r_y, r_m in ref[1:]:
        if user_id <= r_id:
            y, m = hesapla(user_id, p_id, p_y, p_m, r_id, r_y, r_m)
            return f"~{ay_adlari.get(m, str(m))} {y}"
        p_id, p_y, p_m = r_id, r_y, r_m

    # Tablonun ötesi — son iki noktadan lineer ekstrapolasyon
    prev_id, prev_y, prev_m = ref[-2]
    last_id, last_y, last_m = ref[-1]
    aylik_hiz = (last_id - prev_id) / max((last_y * 12 + last_m) - (prev_y * 12 + prev_m), 1)
    baz_ay    = last_y * 12 + last_m - 1
    ekstra    = (user_id - last_id) / aylik_hiz
    est       = baz_ay + ekstra
    y = int(est) // 12
    m = int(est) % 12 + 1
    m = max(1, min(12, m))
    return f"~{ay_adlari.get(m, str(m))} {y}"

def gece_modu_aktif_mi() -> bool:
    simdi = datetime.datetime.now(TR_SAAT)
    return simdi.hour >= 22 or simdi.hour < 8

async def gece_modu_uyari_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(
            chat_id=ZAMANLI_KANAL_ID,
            text=(
                "⚠️ *Gece Modu Uyarısı*\n\n"
                "🌒 Birazdan *Gece Modu* başlıyor\\!\n\n"
                "🇹🇷 Türkiye: saat *22:00*'de grup kapanacak\n"
                "🇦🇿 Azərbaycan: saat *23:00*\\-da qrup bağlanacaq\n\n"
                "Tekrar açılış / Yenidən açılış:\n"
                "🇹🇷 *08:00* \\| 🇦🇿 *09:00* 💤"
            ),
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logger.error(f"Gece modu uyarı hatası: {e}")

async def gece_modu_baslat_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(
            chat_id=ZAMANLI_KANAL_ID,
            text=(
                "🌒 *Gece Modu Başladı / Gecə Rejimi Başladı*\n\n"
                "Grup şu an mesajlara kapalı\\. Qrup hazırda mesajlara bağlıdır\\.\n\n"
                "🇹🇷 Sabah *08:00*'e kadar kimse mesaj atamaz\n"
                "🇦🇿 Sabah *09:00*\\-a qədər heç kim mesaj yaza bilməz\n\n"
                "_🌙 İyi geceler\\! / Yaxşı gecələr\\!_"
            ),
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logger.error(f"Gece modu başlatma mesaj hatası: {e}")
    try:
        await context.bot.set_chat_permissions(
            chat_id=ZAMANLI_KANAL_ID,
            permissions=ChatPermissions(can_send_messages=False),
            use_independent_chat_permissions=True
        )
    except Exception as e:
        logger.error(f"Gece modu kısıtlama hatası: {e}")

async def gece_modu_bitir_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.set_chat_permissions(
            chat_id=ZAMANLI_KANAL_ID,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True
            )
        )
        await context.bot.send_message(
            chat_id=ZAMANLI_KANAL_ID,
            text=(
                "🌅 *Gece Modu Sona Erdi / Gecə Rejimi Bitti*\n\n"
                "🇹🇷 ☀️ Günaydın\\! Artık herkes sohbete mesaj yazabilir\\.\n"
                "🇦🇿 ☀️ Sabahınız xeyir\\! Artıq hamı qrupa mesaj yaza bilər\\.\n\n"
                "_Güzel bir gün\\! / Xoş bir gün\\! 😊_"
            ),
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logger.error(f"Gece modu bitirme hatası: {e}")

async def oglen_uyari_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(
            chat_id=ZAMANLI_KANAL_ID,
            text=(
                "🍽️ *Öğle Yemeği Yaklaşıyor\\!*\n\n"
                "🇹🇷 Saat *12:00* — birazdan yemek zamanı\\! 😋\n"
                "🇦🇿 Saat *13:00* — az sonra nahar vaxtıdır\\! 😋\n\n"
                "_🥗 Afiyet olsun\\! / Nuş olsun\\!_"
            ),
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logger.error(f"Öğle uyarı hatası: {e}")

async def oglen_yemek_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(
            chat_id=ZAMANLI_KANAL_ID,
            text=(
                "🍴 *Yemek Saati / Nahar Vaxtı\\!*\n\n"
                "🇹🇷 Saat *13:00* — Hadi herkes yemeye\\! 🥘\n"
                "🇦🇿 Saat *14:00* — Hamı nahara\\! 🥘\n\n"
                "_Afiyet olsun\\! / Nuş olsun\\! 😄_"
            ),
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logger.error(f"Öğle yemek hatası: {e}")

# --- ⚡ HIZLI KOMUTLAR ---

async def hesap_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "🧮 **Hesap Makinesi**\n\nKullanım: `/hesap 2**10`\nÖrnek: `/hesap sqrt(144)` veya `/hesap sin(pi/2)`",
            parse_mode='Markdown'
        )
        return
    ifade = ' '.join(context.args)
    sonuc = guvenli_hesapla(ifade)
    await update.effective_message.reply_text(sonuc, parse_mode='Markdown')

async def hash_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "🔐 **Hash Üretici**\n\nKullanım: `/hash metin`\nÖrnek: `/hash AZRxGUARD`",
            parse_mode='Markdown'
        )
        return
    metin = ' '.join(context.args)
    sonuc = hash_uret(metin)
    await update.effective_message.reply_text(sonuc, parse_mode='Markdown')

async def hava_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "🌍 **Hava Durumu**\n\nKullanım: `/hava Istanbul`\nÖrnek: `/hava Baku` veya `/hava Moscow`",
            parse_mode='Markdown'
        )
        return
    sehir = ' '.join(context.args)
    bekle = await update.effective_message.reply_text(f"🌍 `{html.escape(sehir)}` sorgulanıyor...", parse_mode='Markdown')
    sonuc = await hava_durumu_getir(sehir)
    try:
        await bekle.edit_text(sonuc, parse_mode='Markdown')
    except Exception:
        await bekle.edit_text(sonuc)

async def kur_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.effective_message.reply_text(
            "💱 **Döviz Çevirici**\n\nKullanım: `/kur 100 USD TRY`\nÖrnek: `/kur 50 EUR USD`",
            parse_mode='Markdown'
        )
        return
    metin = ' '.join(context.args)
    bekle = await update.effective_message.reply_text("💱 Kur bilgisi getiriliyor...", parse_mode='Markdown')
    sonuc = await doviz_cevir(metin)
    try:
        await bekle.edit_text(sonuc, parse_mode='Markdown')
    except Exception:
        await bekle.edit_text(sonuc)

async def saat_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sonuc = dunya_saati()
    await update.effective_message.reply_text(sonuc, parse_mode='Markdown')

async def b64_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "🔒 **Base64 Aracı**\n\nKullanım:\n`/b64 encode metin`\n`/b64 decode bWV0aW4=`",
            parse_mode='Markdown'
        )
        return
    metin = ' '.join(context.args)
    sonuc = base64_islem(metin)
    await update.effective_message.reply_text(sonuc, parse_mode='Markdown')

async def id_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg  = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    metin = (
        f"🆔 **ID BİLGİLERİ**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 **Sen:** `{user.id}`\n"
        f"💬 **Bu Sohbet:** `{chat.id}`\n"
    )
    if msg.reply_to_message and msg.reply_to_message.from_user:
        hedef = msg.reply_to_message.from_user
        metin += f"↩️ **Yanıtlanan:** `{hedef.id}` ({html.escape(hedef.first_name or '')})\n"
    await msg.reply_text(metin, parse_mode='Markdown')


def main():
    uyanik_tut()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("stats", stats_komut_tetikleyici, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("meid", meid_komutu))
    application.add_handler(CommandHandler("ip", ip_basit_komutu))
    application.add_handler(CommandHandler("ip_analiz", ip_komutu))
    application.add_handler(CommandHandler("hatirlat", hatirlat_komutu))
    # ⚡ PRO ARAÇLAR — Hızlı komutlar
    application.add_handler(CommandHandler("hesap", hesap_komutu))
    application.add_handler(CommandHandler("hash", hash_komutu))
    application.add_handler(CommandHandler("hava", hava_komutu))
    application.add_handler(CommandHandler("kur", kur_komutu))
    application.add_handler(CommandHandler("saat", saat_komutu))
    application.add_handler(CommandHandler("b64", b64_komutu))
    application.add_handler(CommandHandler("id", id_komutu))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, gelen_mesajlari_yonet))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, kanala_veya_gruba_yeni_uye_katildi))
    application.add_handler(MessageHandler((filters.ChatType.GROUPS | filters.ChatType.CHANNEL) & filters.ALL, grup_ve_kanal_mesaj_yonet))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, filigran_ekle), group=-1)

    # --- ZAMANLI GÖREVLER ---
    jq = application.job_queue

    # 21:00 — Gece modu uyarısı
    jq.run_daily(
        callback=gece_modu_uyari_job,
        time=datetime.time(hour=21, minute=0, second=0, tzinfo=TR_SAAT),
        name="gece_modu_uyari"
    )
    # 22:00 — Gece modu başlar (grup kilitlenir)
    jq.run_daily(
        callback=gece_modu_baslat_job,
        time=datetime.time(hour=22, minute=0, second=0, tzinfo=TR_SAAT),
        name="gece_modu_baslat"
    )
    # 08:00 — Gece modu biter (grup açılır)
    jq.run_daily(
        callback=gece_modu_bitir_job,
        time=datetime.time(hour=8, minute=0, second=0, tzinfo=TR_SAAT),
        name="gece_modu_bitir"
    )
    # 12:00 — Öğle yemeği uyarısı
    jq.run_daily(
        callback=oglen_uyari_job,
        time=datetime.time(hour=12, minute=0, second=0, tzinfo=TR_SAAT),
        name="oglen_uyari"
    )
    # 13:00 — Yemek saati
    jq.run_daily(
        callback=oglen_yemek_job,
        time=datetime.time(hour=13, minute=0, second=0, tzinfo=TR_SAAT),
        name="oglen_yemek"
    )

    logger.info("AZRxGUARD Sistemi Sorunsuz Başlatıldı...")
    application.run_polling(allowed_updates=["message", "callback_query", "channel_post", "chat_member"])

if __name__ == '__main__':
    main()
