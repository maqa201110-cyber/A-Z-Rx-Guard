import logging
import asyncio
import re
from flask import Flask
from threading import Thread
import html
import os
import pickle
from google import genai as google_genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- 7/24 UYANIK TUTMA SİSTEMİ ---
server = Flask('')

@server.route('/')
def home():
    return "AZRxGUARD Çok Dilli Bot Aktif!"

def run():
    server.run(host='0.0.0.0', port=6000)

def uyanik_tut():
    t = Thread(target=run)
    t.daemon = True
    t.start()

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

MY_ID = 74210240
KANAL_ID = -1003930940829
KONTROL_KANAL_USER = "@azrXmaqa"
YONETIM_KANAL_ID = -1003918825511

# --- GEMINI AI KURULUMU ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
gemini_client = None
if GEMINI_API_KEY:
    try:
        gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Gemini AI başarıyla yüklendi.")
    except Exception as e:
        logger.error(f"Gemini AI yükleme hatası: {e}")

# --- KÜFÜR FİLTRESİ LİSTESİ ---
# \b yerine boşluk/satır başı/sonu kontrolü — Türkçe/Rusça özel karakterlerle çalışır
KUFUR_KELIMELER = [
    # Türkçe
    'orospu', 'orospuçocuğu', 'orospu çocuğu', 'orospu cocugu',
    'piç', 'pic', 'sik', 'siktiir', 'siktir', 'sikiş', 'sikis',
    'amk', 'amına', 'amını', 'amın', 'aminakoyim', 'oç', 'oc',
    'göt', 'got', 'ibne', 'orospu', 'bok', 'boktan',
    'gerizekalı', 'gerzek', 'şerefsiz', 'serefsiz',
    'kaltak', 'kaltaklar', 'kaltaklık', 'kahpe', 'sürtük', 'surtuk',
    'pezevenk', 'bok', 'boktan', 'boklu', 'salak', 'aptal',
    'dangalak', 'haysiyetsiz', 'namussuz', 'puşt', 'pusht',
    'götveren', 'liboş', 'libos', 'götoğlanı', 'ananı', 'ananı',
    'sıçtım', 'sıçayım', 'sıç', 'sic', 'yarrak', 'yarak',
    # Azerbaycanca
    'sikin', 'sikib', 'anasını', 'anasini', 'götver', 'gotveren',
    'sürün', 'surun', 'it heyvan', 'eşşek', 'essek', 'naxuy',
    'götünə', 'soxum', 'sikdir', 'ananı sikım', 'sik get',
    # Rusça
    'блядь', 'бля', 'блять', 'хуй', 'хуйня', 'хуйло',
    'пизда', 'пиздец', 'пиздёж', 'ёбаный', 'ёб', 'ёбать',
    'еба', 'ебать', 'ебло', 'ёблан', 'сука', 'суки',
    'мудак', 'мудила', 'ублюдок', 'нахуй', 'нахер',
    'пидор', 'пидр', 'пидрила', 'курва', 'залупа',
    'шлюха', 'ёбтвоюмать', 'твоюмать', 'бляха',
    # İngilizce
    'fuck', 'fucking', 'fucker', 'fucked', 'fck', 'f*ck',
    'shit', 'shitty', 'sh*t', 'bitch', 'b*tch', 'btch',
    'asshole', 'bastard', 'cunt', 'dick', 'pussy',
    'whore', 'slut', 'motherfucker', 'mf', 'faggot', 'fag',
    'nigga', 'nigger', 'retard', 'stfu', 'wtf',
    # Yıldızlı / gizlenmiş yazılış
    's*k', 'f**k', 's**t', 'b**ch', 'a**hole',
]

def kufur_var_mi(metin: str) -> bool:
    metin_kucuk = metin.lower()
    metin_temiz = re.sub(r'[\s\-_\.\*]+', '', metin_kucuk)
    for kelime in KUFUR_KELIMELER:
        k = kelime.lower()
        if k in metin_kucuk:
            return True
        k_temiz = re.sub(r'[\s\-_\.\*]+', '', k)
        if k_temiz and k_temiz in metin_temiz:
            return True
    return False

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
        'ask_admin_msg': "📝 Lütfen iletmek istediğiniz şeyi yazın:",
        'msg_sent': "✅ Mesaj başarıyla iletildi!",
        'fun_welcome': "🚀 **Eğlence & Araçlar Menüsü**\n\nZar atmak için aşağıdaki butona basın:",
        'azr_welcome': "🔥 **AZRxGUARD Özel Menüsüne Hoş Geldiniz!**\n\nBot istatistiklerini canlı görmek için aşağıdaki butona tıklayın:",
        'force_join_text': "⚠️ **DURUN!** Botu kullanabilmek için önce resmi kanalımıza katılmanız gerekmektedir.\n\nKatıldıktan sonra bota tekrar `/start` yazabilir veya menüyü kullanabilirsiniz.",
        'btn_join_now': "📢 Kanala Katıl",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **Kullanıcı Bilgilerin**"
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
        'ask_admin_msg': "📝 Xahiş edirik çatdırmaq istədiyiniz şeyi yazın:",
        'msg_sent': "✅ Mesaj uğurla göndərildi!",
        'fun_welcome': "🚀 **Əyləncə & Alətlər Menyusu**\n\nZar atmaq üçün aşağıdakı düyməyə basın:",
        'azr_welcome': "🔥 **AZRxGUARD Özel Menyusuna Xoş Gəldiniz!**\n\nBot statistikasını canlı görmək üçün aşağıdakı düyməyə vurun:",
        'force_join_text': "⚠️ **DAYANIN!** Botdan istifadə edə bilmək üçün əvvəlcə rəsmi kanalımıza qoşulmalısınız.\n\nQoşulduqdan sonra bota yenidən `/start` yaza bilərsiniz.",
        'btn_join_now': "📢 Kanala Qoşul",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **İstifadəçi Məlumatların**"
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
        'ask_admin_msg': "📝 Пожалуйста, напишите то, что вы хотите передать:",
        'msg_sent': "✅ Сообщение успешно отправлено!",
        'fun_welcome': "🚀 **Развлекательное меню**\n\nНажмите кнопку ниже, чтобы бросить кубик:",
        'azr_welcome': "🔥 **Специальное меню AZRxGUARD!**\n\nНажмите кнопку ниже, чтобы увидеть статистику бота:",
        'force_join_text': "⚠️ **ВНИМАНИЕ!** Чтобы использовать бота, вы должны сначала подписаться на наш официальный канал.\n\nПосле подписки отправьте `/start` снова.",
        'btn_join_now': "📢 Подписаться на канал",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **Информация о тебе**"
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
        'ask_admin_msg': "📝 Please write what you want to convey:",
        'msg_sent': "✅ Message successfully sent!",
        'fun_welcome': "🚀 **Entertainment & Tools Menu**\n\nPress the button below to roll the dice:",
        'azr_welcome': "🔥 **Welcome to AZRxGUARD Special Menu!**\n\nClick the button below to view live bot statistics:",
        'force_join_text': "⚠️ **ATTENTION!** To use this bot, you must first join our official channel.\n\nAfter joining, please send `/start` again to unlock.",
        'btn_join_now': "📢 Join Channel",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **Your Information**"
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
        'ask_admin_msg': "📝 Bitte schreiben Sie, was Sie übermitteln möchten:",
        'msg_sent': "✅ Nachricht erfolgreich gesendet!",
        'fun_welcome': "🚀 **Unterhaltungs- & Tools-Menü**\n\nDrücken Sie die Taste unten, um zu würfeln:",
        'azr_welcome': "🔥 **Willkommen im AZRxGUARD Spezialmenü!**\n\nKlicken Sie auf die Schaltfläche unten, um die Live-Bot-Statistiken anzuzeigen:",
        'force_join_text': "⚠️ **ACHTUNG!** Um diesen Bot nutzen zu können, müssen Sie zuerst unserem offiziellen Kanal beitreten.\n\nNach dem Beitritt senden Sie bitte erneut `/start`.",
        'btn_join_now': "📢 Kanal beitreten",
        'btn_meid': "🪪 Me ID",
        'meid_title': "🪪 **Deine Informationen**"
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
            InlineKeyboardButton(strings['btn_admin'], callback_data='menu_admin')
        ],
        [
            InlineKeyboardButton(strings['btn_azr_special'], callback_data='menu_azr_special')
        ]
    ]
    return InlineKeyboardMarkup(klavye)

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
def meid_bilgisi_olustur(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> str:
    from datetime import datetime, timezone
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    # — Kullanıcı bilgileri —
    ad = html.escape(user.first_name) if user.first_name else "—"
    soyad = html.escape(user.last_name) if user.last_name else "—"
    tam_ad = f"{ad} {soyad}".strip() if user.last_name else ad
    kullanici_adi = f"@{user.username}" if user.username else "—"
    tiklanabilir = f"[{html.escape(tam_ad)}](tg://user?id={user.id})"
    bot_dili_map = {'tr': '🇹🇷 Türkçe', 'az': '🇦🇿 Azərbaycanca', 'ru': '🇷🇺 Русский', 'en': '🇬🇧 English', 'de': '🇩🇪 Deutsch'}
    bot_dili = bot_dili_map.get(lang, lang)
    tg_dili = user.language_code.upper() if user.language_code else "—"
    premium = "✅ Evet" if getattr(user, 'is_premium', False) else "❌ Hayır"
    dogrulandi = "✅ Evet" if getattr(user, 'is_verified', False) else "❌ Hayır"
    kisitlandi = "⚠️ Evet" if getattr(user, 'is_restricted', False) else "✅ Hayır"
    hesap_turu = "🤖 Bot" if user.is_bot else "👤 Normal Kullanıcı"

    # — Sohbet bilgileri —
    chat_turu_map = {
        'private': '💬 Özel Mesaj (DM)',
        'group': '👥 Grup',
        'supergroup': '👥 Süper Grup',
        'channel': '📢 Kanal'
    }
    chat_turu = chat_turu_map.get(chat.type, chat.type) if chat else "—"
    chat_id = str(chat.id) if chat else "—"
    chat_adi = html.escape(chat.title) if chat and chat.title else "—"

    # — Mesaj bilgileri —
    mesaj_id = str(msg.message_id) if msg else "—"
    mesaj_zamani = "—"
    if msg and msg.date:
        mesaj_zamani = msg.date.strftime("%d.%m.%Y %H:%M:%S UTC")

    yanit_mi = "✅ Evet" if msg and msg.reply_to_message else "❌ Hayır"
    medya_turu = "—"
    if msg:
        if msg.photo: medya_turu = "🖼️ Fotoğraf"
        elif msg.video: medya_turu = "🎥 Video"
        elif msg.voice: medya_turu = "🎙️ Sesli Mesaj"
        elif msg.document: medya_turu = "📄 Dosya"
        elif msg.sticker: medya_turu = "🎭 Sticker"
        elif msg.animation: medya_turu = "🎬 GIF"
        elif msg.text: medya_turu = "💬 Metin"

    # — Bot kayıt durumu —
    toplam_uyeler = uyeleri_getir()
    kayitli = "✅ Evet" if user.id in toplam_uyeler else "❌ Hayır"
    toplam_uye_sayisi = len(toplam_uyeler)

    title = LANG_DATA[lang].get('meid_title', '🪪 **Kullanıcı Bilgilerin**')

    return (
        f"{title}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 **Ad Soyad:** {tiklanabilir}\n"
        f"🏷️ **Kullanıcı Adı:** `{kullanici_adi}`\n"
        f"🆔 **Kullanıcı ID:** `{user.id}`\n"
        f"🧩 **Hesap Türü:** {hesap_turu}\n\n"
        f"🌍 **Bot Dili:** {bot_dili}\n"
        f"📱 **Telegram Dili:** `{tg_dili}`\n"
        f"💎 **Telegram Premium:** {premium}\n"
        f"✅ **Doğrulanmış Hesap:** {dogrulandi}\n"
        f"🚫 **Kısıtlanmış:** {kisitlandi}\n\n"
        f"💬 **Sohbet Türü:** {chat_turu}\n"
        f"🏠 **Sohbet Adı:** `{chat_adi}`\n"
        f"📌 **Sohbet ID:** `{chat_id}`\n\n"
        f"📨 **Mesaj ID:** `{mesaj_id}`\n"
        f"📎 **İçerik Türü:** {medya_turu}\n"
        f"↩️ **Yanıt mı?:** {yanit_mi}\n"
        f"🕒 **Mesaj Zamanı:** `{mesaj_zamani}`\n\n"
        f"📋 **Bot'a Kayıtlı:** {kayitli}\n"
        f"👥 **Toplam Bot Üyesi:** `{toplam_uye_sayisi}`\n\n"
        f"🔗 **Profil Linki:** tg://user?id={user.id}\n\n"
        f"🤖 _AZRxGUARD tarafından oluşturuldu_"
    )

async def meid_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    user_id = update.effective_user.id
    lang = get_lang(context, user_id)
    strings = LANG_DATA[lang]
    bilgi = meid_bilgisi_olustur(update, context, lang)
    geri_klavye = None
    if update.effective_chat and update.effective_chat.type == 'private':
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_azr_special')]])
    try:
        await update.effective_message.reply_text(bilgi, parse_mode='Markdown', reply_markup=geri_klavye)
    except Exception:
        await update.effective_message.reply_text(bilgi, reply_markup=geri_klavye)

# --- 🚫 KÜFÜR FİLTRESİ ---
async def kufur_filtre_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text:
        return
    if not kufur_var_mi(msg.text):
        return
    user = update.effective_user
    if not user:
        return

    guvenli_isim = html.escape(user.first_name) if user.first_name else "Kullanıcı"
    uyari_metni = (
        f"⚠️ [{guvenli_isim}](tg://user?id={user.id}), **uygunsuz dil kullandın!**\n\n"
        f"Bu tür ifadeler yasaktır. Lütfen saygılı ol. 🔇\n"
        f"_Bu mesaj 5 saniye içinde silinecek._"
    )
    try:
        uyari = await msg.reply_text(uyari_metni, parse_mode='Markdown')
        asyncio.create_task(mesajlari_5s_sonra_sil(context, msg.chat_id, uyari.message_id, msg.message_id))
    except Exception as e:
        logger.error(f"Küfür filtresi hatası: {e}")

# --- 🤖 GEMİNİ AI YANIT ---
GEMINI_SISTEM = (
    "Sen AZRxGUARD botunun yapay zeka asistanısın. "
    "Türkçe, Azerbaycanca, Rusça, İngilizce ve Almanca konuşabilirsin. "
    "Kullanıcının dilinde kısa, net ve yardımcı cevaplar ver. "
    "Zararlı, yasadışı veya uygunsuz içerik üretme."
)

async def gemini_ai_yanit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not gemini_client:
        return
    msg = update.effective_message
    if not msg or not msg.text:
        return
    user_text = msg.text.strip()
    if not user_text:
        return
    bekle = None
    try:
        bekle = await msg.reply_text("🤖 _Düşünüyorum..._", parse_mode='Markdown')
        yanit = await asyncio.to_thread(
            lambda: gemini_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=user_text,
                config=google_genai.types.GenerateContentConfig(
                    system_instruction=GEMINI_SISTEM,
                    temperature=0.7,
                )
            ).text
        )
        await bekle.edit_text(f"🤖 {yanit}")
    except Exception as e:
        logger.error(f"Gemini AI hatası: {e}")
        if bekle:
            try:
                await bekle.edit_text("⚠️ Yapay zeka şu an yanıt veremiyor, lütfen tekrar dene.")
            except Exception:
                pass

# --- YÖNETİM KANALINDAN ÜYELERE KOPYALAMA SİSTEMİ ---
async def grup_ve_kanal_mesaj_yonet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        channel_post = update.channel_post

        if channel_post.chat_id == YONETIM_KANAL_ID:
            tum_uyeler = uyeleri_getir()
            if not tum_uyeler:
                return
            basarili = 0
            liste_degisti = False
            for u_id in list(tum_uyeler):
                try:
                    await context.bot.copy_message(
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
                await context.bot.send_message(
                    chat_id=YONETIM_KANAL_ID,
                    text=f"📢 **Toplu Gönderim Başarıyla Tamamlandı!**\n\nKanala attığınız içerik toplam `{basarili}` kullanıcıya ulaştırıldı. 🔥"
                )
            except Exception:
                pass

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

    mesaj = await update.message.reply_text("⏳ Başlatılıyor...")
    await asyncio.sleep(1.0)
    await mesaj.edit_text("📥 Veri yükleniyor...")
    await asyncio.sleep(1.0)
    await mesaj.edit_text("✅ Sistem hazır!")
    await asyncio.sleep(0.8)
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
            [InlineKeyboardButton("🇩🇪 Deutsch", callback_data='set_lang_de')],
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
    elif query.data == 'menu_azr_special':
        azr_klavye = [
            [InlineKeyboardButton(strings['btn_stats'], callback_data='show_inline_stats')],
            [InlineKeyboardButton(strings['btn_meid'], callback_data='show_meid')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(strings['azr_welcome'], reply_markup=InlineKeyboardMarkup(azr_klavye), parse_mode='Markdown')
    elif query.data == 'show_inline_stats':
        rapor_metni = istatistik_raporu_hazirla(context)
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_azr_special')]])
        await query.edit_message_text(text=rapor_metni, reply_markup=geri_klavye, parse_mode='Markdown')
    elif query.data == 'show_meid':
        bilgi = meid_bilgisi_olustur(update, context, lang)
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_azr_special')]])
        await query.edit_message_text(text=bilgi, reply_markup=geri_klavye, parse_mode='Markdown')
    elif query.data == 'roll_dice':
        await query.message.delete()
        await query.message.chat.send_dice(emoji='🎲')
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

    # Admin bekleme durumunda değilse → Gemini AI yanıtla
    await gemini_ai_yanit(update, context)

def main():
    uyanik_tut()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("stats", stats_komut_tetikleyici, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("meid", meid_komutu))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, gelen_mesajlari_yonet))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, kanala_veya_gruba_yeni_uye_katildi))
    application.add_handler(MessageHandler((filters.ChatType.GROUPS | filters.ChatType.CHANNEL) & filters.ALL, grup_ve_kanal_mesaj_yonet))
    # Küfür filtresi — tüm chatlerde ayrı grupta çalışır (grup 1)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, kufur_filtre_handler),
        group=1
    )

    logger.info("AZRxGUARD Sistemi Sorunsuz Başlatıldı...")
    application.run_polling(allowed_updates=["message", "callback_query", "channel_post", "chat_member"])

if __name__ == '__main__':
    main()
