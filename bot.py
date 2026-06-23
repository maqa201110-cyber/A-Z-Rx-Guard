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
import tempfile
import shutil
import urllib.parse

try:
    from akinator.async_client import AsyncAkinator as _AsyncAkinator
    from akinator.exceptions import CantGoBackAnyFurther as _CantGoBack
    AKINATOR_YUKLU = True
except Exception:
    AKINATOR_YUKLU = False
    _AsyncAkinator = None
    _CantGoBack = Exception

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, BotCommandScopeDefault, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, JobQueue

# --- 7/24 UYANIK TUTMA SİSTEMİ ---
# Replit keeps the bot alive natively; no separate Flask keep-alive needed.
def uyanik_tut():
    pass

# --- LOG AYARLARI ---
import logging.handlers as _log_handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
# Kalıcı dosya logu — tüm bilgiler, sınır yok
_file_handler = _log_handlers.RotatingFileHandler(
    'azrxguard.log', maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8'
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
))
logging.getLogger().addHandler(_file_handler)

# 3. parti kütüphaneleri sadece WARNING ve üstü göstersin (konsol kirlenmesi önlenir)
for _noisy in ('httpx', 'httpcore', 'telegram.ext', 'apscheduler'):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

MY_ID = int(os.environ.get("BOT_OWNER_ID", "0"))
KANAL_ID = -1003930940829
KONTROL_KANAL_USER = "@azrXmaqa"
YONETIM_KANAL_ID = -1003918825511
ZAMANLI_KANAL_ID = -1003775055611
LOG_KANAL_ID = -1003996192485
_APK_KANAL_ID = -1004299694640         # APK-OBB-CONFİG yükleme kanalı
TR_SAAT = datetime.timezone(datetime.timedelta(hours=4))   # 🇬🇪 Gürcistan / Georgia (UTC+4)
AZ_SAAT = datetime.timezone(datetime.timedelta(hours=4))   # 🇦🇿 Azerbaycan (UTC+4)

FILIGRAN_METNI = (
    "__________________________________\n"
    "|\n"
    "|⚡ 𝑴𝑨𝑫𝑬 𝑩𝒀  ➣ M̶A̶Q̶A̶💎 | 𝑶𝑾𝑵𝑬𝑹\n"
    "|__________________________________\n"
    "|\n"
    "|𝑪𝑯𝑨𝑵𝑵𝑬𝑳 ➣ 𝐚𝐳𝐫𝐗𝐦𝐚𝐪𝐚 \n"
    "|__________________________________"
)

# --- 🔤 YAZI TİPİ SİSTEMİ ---
_CAPS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
_LOWS = 'abcdefghijklmnopqrstuvwxyz'
_DIGS = '0123456789'

def _harita_olustur(kap_str: str, kuc_str: str, rak_str: str = '') -> dict:
    h = {}
    for i, c in enumerate(_CAPS):
        if i < len(kap_str):
            h[c] = kap_str[i]
    for i, c in enumerate(_LOWS):
        if i < len(kuc_str):
            h[c] = kuc_str[i]
    for i, c in enumerate(_DIGS):
        if i < len(rak_str):
            h[c] = rak_str[i]
    return h

YAZI_TIPI_HARITASI: dict = {
    'normal':           {},
    'bold':             _harita_olustur(
        '𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙',
        '𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳',
        '𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗'),
    'bold_italic':      _harita_olustur(
        '𝑨𝑩𝑪𝑫𝑬𝑭𝑮𝑯𝑰𝑱𝑲𝑳𝑴𝑵𝑶𝑷𝑸𝑹𝑺𝑻𝑼𝑽𝑾𝑿𝒀𝒁',
        '𝒂𝒃𝒄𝒅𝒆𝒇𝒈𝒉𝒊𝒋𝒌𝒍𝒎𝒏𝒐𝒑𝒒𝒓𝒔𝒕𝒖𝒗𝒘𝒙𝒚𝒛'),
    'italic':           _harita_olustur(
        '𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍',
        '𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧'),
    'sans_bold':        _harita_olustur(
        '𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭',
        '𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇',
        '𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵'),
    'sans_italic':      _harita_olustur(
        '𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡',
        '𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻'),
    'sans_bold_italic': _harita_olustur(
        '𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕',
        '𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯'),
    'monospace':        _harita_olustur(
        '𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉',
        '𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣',
        '𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿'),
    'double_struck':    _harita_olustur(
        '𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ',
        '𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫',
        '𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡'),
    'fraktur':          _harita_olustur(
        '𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ',
        '𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷'),
    'strikethrough':    'strikethrough',
    'underline':        'underline',
    'bubble':           _harita_olustur(
        'ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ',
        'ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ'),
}

# ─── İSİM FONTU — EK KARAKTER HARİTALARI ────────────────────────
_IF_EK_HARITALAR: dict = {
    'sans_serif':   _harita_olustur(
        '𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹',
        '𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓'),
    'script':       _harita_olustur(
        '𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵',
        '𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏'),
    'bold_script':  _harita_olustur(
        '𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩',
        '𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃'),
    'bold_fraktur': _harita_olustur(
        '𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅',
        '𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟'),
    'fullwidth':    _harita_olustur(
        'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ',
        'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
        '０１２３４５６７８９'),
    'small_caps':   _harita_olustur(
        'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ',
        'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'),
    'superscript':  _harita_olustur(
        'ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿˢᵀᵁᵛᵂˣʸᶻ',
        'ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖqʳˢᵗᵘᵛʷˣʸᶻ',
        '⁰¹²³⁴⁵⁶⁷⁸⁹'),
    'inverted':     _harita_olustur(
        '∀ᗺƆᗡƎℲƃHIſʞ˥WNOdQᴚS⊥∩ΛMXʎZ',
        'ɐqɔpǝɟɓɥıɾʞlɯuodbɹsʇnʌʍxʎz'),
}

# Turkish character decomposition for font transformation
_TR_DECOMP = {
    'ö': 'o\u0308', 'Ö': 'O\u0308',
    'ü': 'u\u0308', 'Ü': 'U\u0308',
    'ç': 'c\u0327', 'Ç': 'C\u0327',
    'ş': 's\u0327', 'Ş': 'S\u0327',
    'ğ': 'g\u0306', 'Ğ': 'G\u0306',
    'ı': 'i',       'İ': 'I',
}

# Font display names for the selection menu
YAZI_TIPLERI = [
    ('normal',           '𝗡𝗼𝗿𝗺𝗮𝗹  —  Normal'),
    ('bold',             '𝐁𝐨𝐥𝐝  —  𝐁𝐎̈𝐘𝐋𝐄'),
    ('bold_italic',      '𝑩𝒐𝒍𝒅 𝑰𝒕𝒂𝒍𝒊𝒄  —  𝑩𝑶̈𝒀𝑳𝑬'),
    ('italic',           '𝐼𝑡𝑎𝑙𝑖𝑐  —  𝐵𝑂̈𝑌𝐿𝐸'),
    ('sans_bold',        '𝗦𝗮𝗻𝘀 𝗕𝗼𝗹𝗱  —  𝗕𝗢̈𝗬𝗟𝗘'),
    ('sans_italic',      '𝘚𝘢𝘯𝘴 𝘐𝘵𝘢𝘭𝘪𝘤  —  𝘉𝘖̈𝘠𝘓𝘌'),
    ('sans_bold_italic', '𝙎𝙖𝙣𝙨 𝘽𝙤𝙡𝙙 𝙄𝙩𝙖𝙡𝙞𝙘  —  𝘽𝙊̈𝙔𝙇𝙀'),
    ('monospace',        '𝙼𝚘𝚗𝚘𝚜𝚙𝚊𝚌𝚎  —  𝙱𝙾̈𝚈𝙻𝙴'),
    ('double_struck',    '𝔻𝕠𝕦𝕓𝕝𝕖 𝕊𝕥𝕣𝕦𝕔𝕜  —  𝔹𝕆̈𝕐𝕃𝔼'),
    ('fraktur',          '𝔉𝔯𝔞𝔨𝔱𝔲𝔯  —  𝔅𝔒̈𝔜𝔏𝔈'),
    ('bubble',           'Ⓑⓤⓑⓑⓛⓔ  —  ⒷÖⓎⓁⒺ'),
    ('strikethrough',    'S̶t̶r̶i̶k̶e̶  —  B̶Ö̶Y̶L̶E̶'),
    ('underline',        'U͟n͟d͟e͟r͟l͟i͟n͟e͟  —  B͟Ö͟Y͟L͟E͟'),
]

def font_donustur(metin: str, font_id: str) -> str:
    """Apply font transformation to text, preserving code blocks and URLs."""
    if not font_id or font_id == 'normal':
        return metin
    combining = None
    harita: dict = {}
    if font_id == 'strikethrough':
        combining = '\u0336'
    elif font_id == 'underline':
        combining = '\u0332'
    else:
        harita = YAZI_TIPI_HARITASI.get(font_id, {})
        if not harita:
            return metin

    result = []
    i = 0
    in_code = False
    n = len(metin)

    while i < n:
        ch = metin[i]
        if ch == '`':
            in_code = not in_code
            result.append(ch)
            i += 1
            continue
        if in_code:
            result.append(ch)
            i += 1
            continue
        # Skip URLs
        if metin[i:i+7] == 'http://' or metin[i:i+8] == 'https://':
            j = i
            while j < n and metin[j] not in (' ', '\n', '\t', ')', ']'):
                j += 1
            result.append(metin[i:j])
            i = j
            continue
        # Decompose Turkish characters
        if ch in _TR_DECOMP:
            for ec in _TR_DECOMP[ch]:
                if combining:
                    result.append(ec + combining)
                elif ec in harita:
                    result.append(harita[ec])
                else:
                    result.append(ec)
            i += 1
            continue
        if combining:
            result.append(ch + combining)
            i += 1
            continue
        result.append(harita.get(ch, ch))
        i += 1

    return ''.join(result)

# ─── İSİM FONTU DÖNÜŞTÜRÜCÜ ──────────────────────────────────────
_IF_SEP = {
    'sep_star':'★','sep_dot':'·','sep_diamond':'◆','sep_heart':'♥',
    'sep_arrow':'→','sep_tri':'▸','sep_bullet':'•','sep_pipe':'│',
    'sep_wave':'~','sep_star4':'✦','sep_plus':'+','sep_dash':'-',
    'sep_space2':'  ','sep_times':'×','sep_slash':'/',
}
_IF_COMBO = {
    'bold_strike':   ('bold',          '\u0336'),
    'bold_under':    ('bold',          '\u0332'),
    'bold_over':     ('bold',          '\u0305'),
    'italic_strike': ('italic',        '\u0336'),
    'mono_under':    ('monospace',     '\u0332'),
    'script_under':  ('script',        '\u0332'),
    'dstruck_str':   ('double_struck', '\u0336'),
    'fraktur_under': ('fraktur',       '\u0332'),
    'bscript_under': ('bold_script',   '\u0332'),
    'fw_under':      ('fullwidth',     '\u0332'),
}
_IF_BOLD_SEP = {
    'bold_sep_star':    ('bold',         '★'),
    'bold_sep_dot':     ('bold',         '·'),
    'bold_sep_diamond': ('bold',         '◆'),
    'italic_sep_star':  ('italic',       '★'),
    'script_sep_dot':   ('script',       '·'),
    'mono_sep_bullet':  ('monospace',    '•'),
    'bscript_sep_star': ('bold_script',  '★'),
}
_IF_COMB_MARK = {
    'overline':    '\u0305',
    'double_under':'\u0333',
    'tilde':       '\u0303',
    'dot_above':   '\u0307',
    'ring':        '\u030a',
    'wavy_below':  '\u0330',
    'dot_below':   '\u0323',
    'xthrough':    '\u0338',
}

def _isim_fontu_uygula(metin: str, stil: str) -> str:
    """Apply a font style transformation for İsim Fontu feature."""
    if stil in _IF_SEP:
        return _IF_SEP[stil].join(metin)
    if stil in _IF_BOLD_SEP:
        base, sep = _IF_BOLD_SEP[stil]
        return sep.join(_isim_fontu_uygula(c, base) for c in metin)
    if stil in _IF_COMBO:
        base, comb = _IF_COMBO[stil]
        return ''.join(c + comb for c in _isim_fontu_uygula(metin, base))
    if stil in _IF_COMB_MARK:
        comb = _IF_COMB_MARK[stil]
        return ''.join(c + comb for c in metin)
    if stil == 'inverted':
        h = _IF_EK_HARITALAR['inverted']
        return ''.join(h.get(c, c) for c in reversed(metin))
    if stil in YAZI_TIPI_HARITASI:
        if stil == 'strikethrough':
            return ''.join(c + '\u0336' for c in metin)
        elif stil == 'underline':
            return ''.join(c + '\u0332' for c in metin)
        h = YAZI_TIPI_HARITASI[stil]
        return ''.join(h.get(c, c) for c in metin)
    if stil in _IF_EK_HARITALAR:
        h = _IF_EK_HARITALAR[stil]
        return ''.join(h.get(c, c) for c in metin)
    return metin

_ISIM_FONTU_LISTESI = [
    # ── Bot ayarlarındaki fontlar ──
    ('bold',            '𝐁𝐨𝐥𝐝'),
    ('italic',          '𝐼𝑡𝑎𝑙𝑖𝑐'),
    ('bold_italic',     '𝑩𝒐𝒍𝒅 𝑰𝒕𝒂𝒍𝒊𝒄'),
    ('sans_bold',       '𝗦𝗮𝗻𝘀 𝗕𝗼𝗹𝗱'),
    ('sans_italic',     '𝘚𝘢𝘯𝘴 𝘐𝘵𝘢𝘭𝘪𝘤'),
    ('sans_bold_italic','𝙎𝘽 𝙄𝙩𝙖𝙡𝙞𝙘'),
    ('monospace',       '𝙼𝚘𝚗𝚘𝚜𝚙𝚊𝚌𝚎'),
    ('double_struck',   '𝔻𝕠𝕦𝕓𝕝𝕖 𝕊𝕥𝕣𝕦𝕔𝕜'),
    ('fraktur',         '𝔉𝔯𝔞𝔨𝔱𝔲𝔯'),
    ('bubble',          'Ⓑⓤⓑⓑⓛⓔ'),
    ('strikethrough',   'S̶t̶r̶i̶k̶e̶t̶h̶r̶o̶u̶g̶h̶'),
    ('underline',       'U͟n͟d͟e͟r͟l͟i͟n͟e͟'),
    # ── Yeni Unicode Math Alphabets ──
    ('sans_serif',      '𝖲𝖺𝗇𝗌-𝖲𝖾𝗋𝗂𝖿'),
    ('script',          '𝒮𝒸𝓇𝒾𝓅𝓉'),
    ('bold_script',     '𝓑𝓸𝓵𝓭 𝓢𝓬𝓻𝓲𝓹𝓽'),
    ('bold_fraktur',    '𝕭𝖔𝖑𝖉 𝕱𝖗𝖆𝖐𝖙𝖚𝖗'),
    # ── Özel Karakter Eşlemeleri ──
    ('fullwidth',       'ＦＵＬＬ ＷＩＤＴＨ'),
    ('small_caps',      'sᴍᴀʟʟ ᴄᴀᴘs'),
    ('superscript',     'ˢᵘᵖᵉʳˢᶜʳⁱᵖᵗ'),
    ('inverted',        'pǝʇɹǝʌuı'),
    # ── Birleştirici Karakter Stilleri ──
    ('overline',        'O̅v̅e̅r̅l̅i̅n̅e̅'),
    ('double_under',    'D͇o͇u͇b͇l͇e͇ U͇n͇d͇e͇r͇'),
    ('tilde',           'T̃ĩl̃d̃ẽ'),
    ('dot_above',       'Ḋȯṫ Ȧḃȯṿė'),
    ('ring',            'R̊i̊n̊g̊'),
    ('wavy_below',      'W̰a̰v̰y̰'),
    ('dot_below',       'Ḍọṭ Ḅẹḷọẉ'),
    ('xthrough',        'X̸ T̸h̸r̸o̸u̸g̸h̸'),
    # ── Kombo Stiller ──
    ('bold_strike',     '𝐁̶𝐨̶𝐥̶𝐝̶ 𝐒̶𝐭̶𝐫̶𝐢̶𝐤̶𝐞̶'),
    ('bold_under',      '𝐁͟𝐨͟𝐥͟𝐝͟ 𝐔͟𝐧͟𝐝͟𝐞͟𝐫͟'),
    ('bold_over',       '𝐁̅𝐨̅𝐥̅𝐝̅ 𝐎̅𝐯̅𝐞̅𝐫̅'),
    ('italic_strike',   '𝐼̶𝑡̶𝑎̶𝑙̶𝑖̶𝑐̶ 𝑆̶𝑡̶𝑟̶'),
    ('mono_under',      '𝙼͟𝚘͟𝚗͟𝚘͟ 𝚄͟𝚗͟𝚍͟𝚎͟𝚛͟'),
    ('script_under',    '𝒮͟𝒸͟𝓇͟𝒾͟𝓅͟𝓉͟'),
    ('dstruck_str',     '𝔸̶𝔹̶ℂ̶ 𝕊̶𝕥̶𝕣̶'),
    ('fraktur_under',   '𝔄͟𝔅͟ℭ͟ 𝔘͟𝔫͟𝔡͟'),
    ('bscript_under',   '𝓑͟𝓸͟𝓵͟𝓭͟ 𝓢͟𝓬͟𝓻͟'),
    ('fw_under',        'Ｆ͟Ｕ͟Ｌ͟Ｌ͟'),
    # ── Ayırıcı Stiller ──
    ('sep_star',        'A★B★C'),
    ('sep_dot',         'A·B·C'),
    ('sep_diamond',     'A◆B◆C'),
    ('sep_heart',       'A♥B♥C'),
    ('sep_arrow',       'A→B→C'),
    ('sep_tri',         'A▸B▸C'),
    ('sep_bullet',      'A•B•C'),
    ('sep_pipe',        'A│B│C'),
    ('sep_wave',        'A~B~C'),
    ('sep_star4',       'A✦B✦C'),
    ('sep_plus',        'A+B+C'),
    ('sep_dash',        'A-B-C'),
    ('sep_space2',      'A  B  C'),
    ('sep_times',       'A×B×C'),
    ('sep_slash',       'A/B/C'),
    # ── Bold/Script + Ayırıcı Kombolar ──
    ('bold_sep_star',    '𝐀★𝐁★𝐂'),
    ('bold_sep_dot',     '𝐀·𝐁·𝐂'),
    ('bold_sep_diamond', '𝐀◆𝐁◆𝐂'),
    ('italic_sep_star',  '𝐴★𝐵★𝐶'),
    ('script_sep_dot',   '𝒜·ℬ·𝒞'),
    ('mono_sep_bullet',  '𝙰•𝙱•𝙲'),
    ('bscript_sep_star', '𝓐★𝓑★𝓒'),
]

def get_font(context, user_id: int) -> str:
    """Get user's chosen font style id."""
    if 'font' not in context.bot_data:
        context.bot_data['font'] = {}
    return context.bot_data['font'].get(user_id, 'normal')

def ft(metin: str, context, user_id: int) -> str:
    """Apply user's selected font to text."""
    return font_donustur(metin, get_font(context, user_id))

class FontStrings:
    """LANG_DATA wrapper: auto-applies user font to every string value."""
    __slots__ = ('_d', '_f')
    def __init__(self, data: dict, font_id: str):
        self._d = data
        self._f = font_id
    def __getitem__(self, key: str) -> str:
        val = self._d[key]
        return font_donustur(val, self._f) if isinstance(val, str) else val
    def get(self, key: str, default=None):
        val = self._d.get(key, default)
        return font_donustur(val, self._f) if (isinstance(val, str) and val is not None) else val
    def __contains__(self, key: str) -> bool:
        return key in self._d

def fs(context, user_id: int, lang: str) -> FontStrings:
    """Shortcut: returns a FontStrings wrapper for the given lang + user."""
    return FontStrings(LANG_DATA[lang], get_font(context, user_id))

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
        'out_hava_title': 'HAVA DURUMU', 'out_hava_konum': 'Konum', 'out_hava_sicaklik': 'Sıcaklık',
        'out_hava_hissedilen': 'Hissedilen', 'out_hava_nem': 'Nem', 'out_hava_ruzgar': 'Rüzgar',
        'out_hava_basinc': 'Basınç', 'out_hava_durum': 'Durum', 'out_hava_uv': 'UV Endeksi',
        'out_hava_gorus': 'Görüş', 'out_hava_servis': 'AZRxGUARD Hava Servisi',
        'out_doviz_title': 'DÖVİZ ÇEVİRİCİ', 'out_doviz_giris': 'Giriş', 'out_doviz_sonuc': 'Sonuç',
        'out_doviz_kur': 'Kur', 'out_doviz_guncelleme': 'Güncelleme', 'out_doviz_kaynak': 'Kaynak',
        'out_doviz_servis': 'AZRxGUARD Döviz Servisi',
        'out_saat_title': 'DÜNYA SAATİ', 'out_saat_servis': 'AZRxGUARD Zaman Servisi',
        'out_hash_title': 'HASH ÜRETİCİ', 'out_hash_metin': 'Metin', 'out_hash_uzunluk': 'Uzunluk', 'out_hash_karakter': 'karakter',
        'out_b64_enc': 'BASE64 ENCODE', 'out_b64_dec': 'BASE64 DECODE', 'out_b64_giris': 'Giriş', 'out_b64_sonuc': 'Sonuç',
        'out_ip_title': 'IP Detaylı Güvenlik Analizi', 'out_ip_sorgu': 'Sorgu',
        'out_ip_konum_bilgi': 'Konum Bilgisi', 'out_ip_ulke': 'Ülke', 'out_ip_bolge': 'Bölge',
        'out_ip_saat': 'Saat Dilimi', 'out_ip_ag_bilgi': 'Ağ Bilgisi', 'out_ip_inet': 'İnternet IP',
        'out_ip_isp': 'İnternet İsmi (ISP)', 'out_ip_org': 'Organizasyon', 'out_ip_asn': 'Altyapı (ASN)',
        'out_ip_mobil': 'Mobil Hat', 'out_ip_ptr': 'Ters DNS (PTR)',
        'out_ip_gizlilik': 'Gizlilik & Tehdit Durumu', 'out_ip_tehdit': 'Tehdit Skoru',
        'out_ip_portlar': 'Açık Portlar', 'out_ip_servis': 'AZRxGUARD Güvenlik Analizi',
        'out_ip_evet': '✅ Evet', 'out_ip_hayir': '❌ Hayır', 'out_ip_mobil_evet': '📱 Evet',
        'out_ip_risk_yuksek': 'Yüksek Risk', 'out_ip_risk_orta': 'Orta Risk', 'out_ip_risk_dusuk': 'Düşük Risk',
        'out_ip_dc': "VERİ MERKEZİ IP'si!", 'out_ip_port_yok': 'Açık port bulunamadı',
        'out_hesap_title': 'HESAP MAKİNESİ', 'out_hesap_ifade': 'İfade', 'out_hesap_sonuc': 'Sonuç',
        'btn_bot_ayarlari': "⚙️ BOT AYARLARI",
        'bot_ayarlari_welcome': "⚙️ **BOT AYARLARI**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nBir ayar seçin:",
        'btn_yazi_tipi': "🔤 BOT YAZI TİPİ",
        'yazi_tipi_welcome': "🔤 **BOT YAZI TİPİ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nBir yazı tipi seçin:\n_Tüm bot yazıları seçtiğin tipte görünecek!_",
        'font_changed': "✅ Yazı tipi değiştirildi!",
        'font_active': "✅ Aktif",
        'btn_siber_guvenlik': "🛡️ SİBER GÜVENLİK",
        'siber_guvenlik_welcome': "🛡️ **SİBER GÜVENLİK MERKEZİ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nAraçlardan birini seçin:",
        'btn_sifre_guc': "🔐 Şifre Güç Testi",
        'btn_oyun_tkmk': "✊ Taş-Kağıt-Makas",
        'btn_oyun_sayi': "🔢 Sayı Tahmin Oyunu",
        'btn_video_olusturucu': "🎬 Video Editör",
        'btn_ved_kirp': "✂️ Video Kırp",
        'btn_ved_hiz': "⚡ Hız Değiştir",
        'btn_ved_don': "🔄 Video Döndür",
        'btn_ved_ses': "🎵 Ses Çıkar",
        'btn_ved_sessiz': "🔇 Sessizleştir",
        'btn_ved_kare': "📸 Kare Al",
        'btn_ved_gif': "🎞️ GIF Yap",
        'btn_ved_boyut': "📐 Boyutlandır",
        'btn_ved_filtre': "🎨 Filtre Uygula",
        'btn_ved_yazi': "🎬 Yazı Ekle",
        'btn_sohbet_araclari': "💬 SOHBET ARAÇLARI",
        'sohbet_araclari_welcome': (
            "💬 **SOHBET ARAÇLARI**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Günlük hayatı kolaylaştıran araçlar:"
        ),
        'btn_sa_qr': "📱 QR Kod Üret",
        'btn_sa_url': "🌐 URL Kısalt",
        'btn_sa_kimlik': "🎭 Sahte Kimlik",
        'btn_sa_tarih': "📅 Yaş / Tarih Hesapla",
        'btn_sa_sans': "🎰 Şans Oyunları",
        'sa_qr_ask': "📱 **QR Kod Üretici**\n\nQR koda dönüştürmek istediğiniz metin veya linki girin:\nÖrnek: `https://t.me/azrXmaqa`",
        'sa_url_ask': "🌐 **URL Kısaltıcı**\n\nKısaltmak istediğiniz URL'yi girin:\nÖrnek: `https://example.com/cok/uzun/bir/link`",
        'sa_tarih_ask': "📅 **Yaş / Tarih Hesaplayıcı**\n\nDoğum tarihinizi girin (GG.AA.YYYY):\nÖrnek: `15.03.1995`",
        'sa_sans_welcome': (
            "🎰 **ŞANS OYUNLARI**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Bir şans oyunu seç:"
        ),
        'btn_sa_yazi_tura': "🪙 Yazı / Tura",
        'btn_sa_zar': "🎲 Zar At",
        'btn_sa_8top': "🎱 8-Top Sorgula",
        'sa_8top_ask': "🎱 **8-Top**\n\nSorunuzu yazın, 8-Top cevaplasın:",
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
        'out_hava_title': 'HAVA PROQNOZU', 'out_hava_konum': 'Məkan', 'out_hava_sicaklik': 'Temperatur',
        'out_hava_hissedilen': 'Hiss edilən', 'out_hava_nem': 'Rütubət', 'out_hava_ruzgar': 'Külək',
        'out_hava_basinc': 'Təzyiq', 'out_hava_durum': 'Vəziyyət', 'out_hava_uv': 'UV İndeksi',
        'out_hava_gorus': 'Görünüş', 'out_hava_servis': 'AZRxGUARD Hava Xidməti',
        'out_doviz_title': 'VALYUTA ÇEVİRİCİSİ', 'out_doviz_giris': 'Giriş', 'out_doviz_sonuc': 'Nəticə',
        'out_doviz_kur': 'Kurs', 'out_doviz_guncelleme': 'Yenilənmə', 'out_doviz_kaynak': 'Mənbə',
        'out_doviz_servis': 'AZRxGUARD Valyuta Xidməti',
        'out_saat_title': 'DÜNYA SAATİ', 'out_saat_servis': 'AZRxGUARD Zaman Xidməti',
        'out_hash_title': 'HASH YARADICI', 'out_hash_metin': 'Mətn', 'out_hash_uzunluk': 'Uzunluq', 'out_hash_karakter': 'simvol',
        'out_b64_enc': 'BASE64 ENCODE', 'out_b64_dec': 'BASE64 DECODE', 'out_b64_giris': 'Giriş', 'out_b64_sonuc': 'Nəticə',
        'out_ip_title': 'IP Ətraflı Təhlükəsizlik Analizi', 'out_ip_sorgu': 'Sorğu',
        'out_ip_konum_bilgi': 'Məkan Məlumatı', 'out_ip_ulke': 'Ölkə', 'out_ip_bolge': 'Bölgə',
        'out_ip_saat': 'Saat Qurşağı', 'out_ip_ag_bilgi': 'Şəbəkə Məlumatı', 'out_ip_inet': 'İnternet IP',
        'out_ip_isp': 'İnternet Provayderi (ISP)', 'out_ip_org': 'Təşkilat', 'out_ip_asn': 'İnfrastruktur (ASN)',
        'out_ip_mobil': 'Mobil Xətt', 'out_ip_ptr': 'Əks DNS (PTR)',
        'out_ip_gizlilik': 'Məxfilik & Təhlükə Vəziyyəti', 'out_ip_tehdit': 'Təhlükə Skoru',
        'out_ip_portlar': 'Açıq Portlar', 'out_ip_servis': 'AZRxGUARD Təhlükəsizlik Analizi',
        'out_ip_evet': '✅ Bəli', 'out_ip_hayir': '❌ Xeyr', 'out_ip_mobil_evet': '📱 Bəli',
        'out_ip_risk_yuksek': 'Yüksək Risk', 'out_ip_risk_orta': 'Orta Risk', 'out_ip_risk_dusuk': 'Aşağı Risk',
        'out_ip_dc': 'VERİ MƏRKƏZİ IP-si!', 'out_ip_port_yok': 'Açıq port tapılmadı',
        'out_hesap_title': 'KALKULYATOR', 'out_hesap_ifade': 'İfadə', 'out_hesap_sonuc': 'Nəticə',
        'btn_bot_ayarlari': "⚙️ BOT AYARLARI",
        'bot_ayarlari_welcome': "⚙️ **BOT AYARLARI**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nBir ayar seçin:",
        'btn_yazi_tipi': "🔤 BOT YAZI TİPİ",
        'yazi_tipi_welcome': "🔤 **BOT YAZI TİPİ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nYazı tipi seçin:\n_Bütün bot yazıları seçdiyiniz tiplə görünəcək!_",
        'font_changed': "✅ Yazı tipi dəyişdirildi!",
        'font_active': "✅ Aktiv",
        'btn_siber_guvenlik': "🛡️ KİBER TƏHLÜKƏSİZLİK",
        'siber_guvenlik_welcome': "🛡️ **KİBER TƏHLÜKƏSİZLİK MƏRKƏZİ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nAlətlərdən birini seçin:",
        'btn_sifre_guc': "🔐 Şifrə Gücü Testi",
        'btn_oyun_tkmk': "✊ Daş-Kağız-Qayçı",
        'btn_oyun_sayi': "🔢 Rəqəm Tapmaca",
        'btn_video_olusturucu': "🎬 Video Redaktor",
        'btn_ved_kirp': "✂️ Video Kəs",
        'btn_ved_hiz': "⚡ Sürəti Dəyiş",
        'btn_ved_don': "🔄 Video Döndür",
        'btn_ved_ses': "🎵 Səs Çıxar",
        'btn_ved_sessiz': "🔇 Səssizləşdir",
        'btn_ved_kare': "📸 Kadr Al",
        'btn_ved_gif': "🎞️ GIF Et",
        'btn_ved_boyut': "📐 Ölçüləndir",
        'btn_ved_filtre': "🎨 Filtr Tətbiq Et",
        'btn_ved_yazi': "🎬 Yazı Əlavə Et",
        'btn_sohbet_araclari': "💬 SÖHBƏT ALƏTLƏRI",
        'sohbet_araclari_welcome': (
            "💬 **SÖHBƏT ALƏTLƏRI**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Gündəlik həyatı asanlaşdıran alətlər:"
        ),
        'btn_sa_qr': "📱 QR Kod Yarat",
        'btn_sa_url': "🌐 URL Qısalt",
        'btn_sa_kimlik': "🎭 Saxta Kimlik",
        'btn_sa_tarih': "📅 Yaş / Tarix Hesabla",
        'btn_sa_sans': "🎰 Şans Oyunları",
        'sa_qr_ask': "📱 **QR Kod Yaradıcı**\n\nQR koda çevirmək istədiyiniz mətn və ya linki daxil edin:",
        'sa_url_ask': "🌐 **URL Qısaldıcı**\n\nQısaltmaq istədiyiniz URL-i daxil edin:",
        'sa_tarih_ask': "📅 **Yaş / Tarix Hesabçısı**\n\nDoğum tarixinizi daxil edin (GG.AA.YYYY):\nNümunə: `15.03.1995`",
        'sa_sans_welcome': (
            "🎰 **ŞANS OYUNLARI**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Bir şans oyunu seç:"
        ),
        'btn_sa_yazi_tura': "🪙 Yazı / Tura",
        'btn_sa_zar': "🎲 Zər At",
        'btn_sa_8top': "🎱 8-Top Sorğu",
        'sa_8top_ask': "🎱 **8-Top**\n\nSualınızı yazın, 8-Top cavablasın:",
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
        'out_hava_title': 'ПОГОДА', 'out_hava_konum': 'Местоположение', 'out_hava_sicaklik': 'Температура',
        'out_hava_hissedilen': 'Ощущается', 'out_hava_nem': 'Влажность', 'out_hava_ruzgar': 'Ветер',
        'out_hava_basinc': 'Давление', 'out_hava_durum': 'Состояние', 'out_hava_uv': 'UV Индекс',
        'out_hava_gorus': 'Видимость', 'out_hava_servis': 'AZRxGUARD Служба Погоды',
        'out_doviz_title': 'КОНВЕРТЕР ВАЛЮТ', 'out_doviz_giris': 'Введено', 'out_doviz_sonuc': 'Результат',
        'out_doviz_kur': 'Курс', 'out_doviz_guncelleme': 'Обновлено', 'out_doviz_kaynak': 'Источник',
        'out_doviz_servis': 'AZRxGUARD Служба Валют',
        'out_saat_title': 'МИРОВОЕ ВРЕМЯ', 'out_saat_servis': 'AZRxGUARD Служба Времени',
        'out_hash_title': 'ГЕНЕРАТОР HASH', 'out_hash_metin': 'Текст', 'out_hash_uzunluk': 'Длина', 'out_hash_karakter': 'симв.',
        'out_b64_enc': 'BASE64 ENCODE', 'out_b64_dec': 'BASE64 DECODE', 'out_b64_giris': 'Ввод', 'out_b64_sonuc': 'Результат',
        'out_ip_title': 'IP Детальный Анализ Безопасности', 'out_ip_sorgu': 'Запрос',
        'out_ip_konum_bilgi': 'Данные о местоположении', 'out_ip_ulke': 'Страна', 'out_ip_bolge': 'Регион',
        'out_ip_saat': 'Часовой пояс', 'out_ip_ag_bilgi': 'Данные о сети', 'out_ip_inet': 'IP адрес',
        'out_ip_isp': 'Провайдер (ISP)', 'out_ip_org': 'Организация', 'out_ip_asn': 'Инфраструктура (ASN)',
        'out_ip_mobil': 'Мобильная сеть', 'out_ip_ptr': 'Обратный DNS (PTR)',
        'out_ip_gizlilik': 'Конфиденциальность & Угрозы', 'out_ip_tehdit': 'Оценка угрозы',
        'out_ip_portlar': 'Открытые порты', 'out_ip_servis': 'AZRxGUARD Анализ Безопасности',
        'out_ip_evet': '✅ Да', 'out_ip_hayir': '❌ Нет', 'out_ip_mobil_evet': '📱 Да',
        'out_ip_risk_yuksek': 'Высокий риск', 'out_ip_risk_orta': 'Средний риск', 'out_ip_risk_dusuk': 'Низкий риск',
        'out_ip_dc': 'IP ЦОД!', 'out_ip_port_yok': 'Открытых портов нет',
        'out_hesap_title': 'КАЛЬКУЛЯТОР', 'out_hesap_ifade': 'Выражение', 'out_hesap_sonuc': 'Результат',
        'btn_bot_ayarlari': "⚙️ НАСТРОЙКИ БОТА",
        'bot_ayarlari_welcome': "⚙️ **НАСТРОЙКИ БОТА**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nВыберите настройку:",
        'btn_yazi_tipi': "🔤 ШРИФТ БОТА",
        'yazi_tipi_welcome': "🔤 **ШРИФТ БОТА**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nВыберите шрифт:\n_Весь текст бота будет отображаться в выбранном стиле!_",
        'font_changed': "✅ Шрифт изменён!",
        'font_active': "✅ Активен",
        'btn_siber_guvenlik': "🛡️ КИБЕРБЕЗОПАСНОСТЬ",
        'siber_guvenlik_welcome': "🛡️ **ЦЕНТР КИБЕРБЕЗОПАСНОСТИ**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nВыберите инструмент:",
        'btn_sifre_guc': "🔐 Тест надёжности пароля",
        'btn_oyun_tkmk': "✊ Камень-Ножницы-Бумага",
        'btn_oyun_sayi': "🔢 Угадай число",
        'btn_video_olusturucu': "🎬 Видео Редактор",
        'btn_ved_kirp': "✂️ Обрезать видео",
        'btn_ved_hiz': "⚡ Изменить скорость",
        'btn_ved_don': "🔄 Повернуть",
        'btn_ved_ses': "🎵 Извлечь звук",
        'btn_ved_sessiz': "🔇 Заглушить",
        'btn_ved_kare': "📸 Снять кадр",
        'btn_ved_gif': "🎞️ Сделать GIF",
        'btn_ved_boyut': "📐 Изменить размер",
        'btn_ved_filtre': "🎨 Применить фильтр",
        'btn_ved_yazi': "🎬 Добавить текст",
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
        'out_hava_title': 'WEATHER', 'out_hava_konum': 'Location', 'out_hava_sicaklik': 'Temperature',
        'out_hava_hissedilen': 'Feels Like', 'out_hava_nem': 'Humidity', 'out_hava_ruzgar': 'Wind',
        'out_hava_basinc': 'Pressure', 'out_hava_durum': 'Condition', 'out_hava_uv': 'UV Index',
        'out_hava_gorus': 'Visibility', 'out_hava_servis': 'AZRxGUARD Weather Service',
        'out_doviz_title': 'CURRENCY CONVERTER', 'out_doviz_giris': 'Input', 'out_doviz_sonuc': 'Result',
        'out_doviz_kur': 'Rate', 'out_doviz_guncelleme': 'Updated', 'out_doviz_kaynak': 'Source',
        'out_doviz_servis': 'AZRxGUARD Currency Service',
        'out_saat_title': 'WORLD CLOCK', 'out_saat_servis': 'AZRxGUARD Time Service',
        'out_hash_title': 'HASH GENERATOR', 'out_hash_metin': 'Text', 'out_hash_uzunluk': 'Length', 'out_hash_karakter': 'chars',
        'out_b64_enc': 'BASE64 ENCODE', 'out_b64_dec': 'BASE64 DECODE', 'out_b64_giris': 'Input', 'out_b64_sonuc': 'Result',
        'out_ip_title': 'IP Detailed Security Analysis', 'out_ip_sorgu': 'Query',
        'out_ip_konum_bilgi': 'Location Info', 'out_ip_ulke': 'Country', 'out_ip_bolge': 'Region',
        'out_ip_saat': 'Timezone', 'out_ip_ag_bilgi': 'Network Info', 'out_ip_inet': 'Internet IP',
        'out_ip_isp': 'Internet Provider (ISP)', 'out_ip_org': 'Organization', 'out_ip_asn': 'Infrastructure (ASN)',
        'out_ip_mobil': 'Mobile Network', 'out_ip_ptr': 'Reverse DNS (PTR)',
        'out_ip_gizlilik': 'Privacy & Threat Status', 'out_ip_tehdit': 'Threat Score',
        'out_ip_portlar': 'Open Ports', 'out_ip_servis': 'AZRxGUARD Security Analysis',
        'out_ip_evet': '✅ Yes', 'out_ip_hayir': '❌ No', 'out_ip_mobil_evet': '📱 Yes',
        'out_ip_risk_yuksek': 'High Risk', 'out_ip_risk_orta': 'Medium Risk', 'out_ip_risk_dusuk': 'Low Risk',
        'out_ip_dc': 'DATACENTER IP!', 'out_ip_port_yok': 'No open ports found',
        'out_hesap_title': 'CALCULATOR', 'out_hesap_ifade': 'Expression', 'out_hesap_sonuc': 'Result',
        'btn_bot_ayarlari': "⚙️ BOT SETTINGS",
        'bot_ayarlari_welcome': "⚙️ **BOT SETTINGS**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nChoose a setting:",
        'btn_yazi_tipi': "🔤 BOT FONT STYLE",
        'yazi_tipi_welcome': "🔤 **BOT FONT STYLE**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nChoose a font style:\n_All bot text will appear in the selected style!_",
        'font_changed': "✅ Font style changed!",
        'font_active': "✅ Active",
        'btn_siber_guvenlik': "🛡️ CYBER SECURITY",
        'siber_guvenlik_welcome': "🛡️ **CYBER SECURITY CENTER**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nChoose a tool:",
        'btn_sifre_guc': "🔐 Password Strength Test",
        'btn_oyun_tkmk': "✊ Rock-Paper-Scissors",
        'btn_oyun_sayi': "🔢 Number Guess Game",
        'btn_video_olusturucu': "🎬 Video Editor",
        'btn_ved_kirp': "✂️ Trim Video",
        'btn_ved_hiz': "⚡ Change Speed",
        'btn_ved_don': "🔄 Rotate Video",
        'btn_ved_ses': "🎵 Extract Audio",
        'btn_ved_sessiz': "🔇 Mute Video",
        'btn_ved_kare': "📸 Extract Frame",
        'btn_ved_gif': "🎞️ Make GIF",
        'btn_ved_boyut': "📐 Resize",
        'btn_ved_filtre': "🎨 Apply Filter",
        'btn_ved_yazi': "🎬 Add Text",
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
        'out_hava_title': 'WETTER', 'out_hava_konum': 'Standort', 'out_hava_sicaklik': 'Temperatur',
        'out_hava_hissedilen': 'Gefühlt', 'out_hava_nem': 'Luftfeuchtigkeit', 'out_hava_ruzgar': 'Wind',
        'out_hava_basinc': 'Luftdruck', 'out_hava_durum': 'Zustand', 'out_hava_uv': 'UV-Index',
        'out_hava_gorus': 'Sichtweite', 'out_hava_servis': 'AZRxGUARD Wetterdienst',
        'out_doviz_title': 'WÄHRUNGSRECHNER', 'out_doviz_giris': 'Eingabe', 'out_doviz_sonuc': 'Ergebnis',
        'out_doviz_kur': 'Kurs', 'out_doviz_guncelleme': 'Aktualisiert', 'out_doviz_kaynak': 'Quelle',
        'out_doviz_servis': 'AZRxGUARD Währungsdienst',
        'out_saat_title': 'WELTZEIT', 'out_saat_servis': 'AZRxGUARD Zeitdienst',
        'out_hash_title': 'HASH-GENERATOR', 'out_hash_metin': 'Text', 'out_hash_uzunluk': 'Länge', 'out_hash_karakter': 'Zeichen',
        'out_b64_enc': 'BASE64 ENCODE', 'out_b64_dec': 'BASE64 DECODE', 'out_b64_giris': 'Eingabe', 'out_b64_sonuc': 'Ergebnis',
        'out_ip_title': 'IP Detaillierte Sicherheitsanalyse', 'out_ip_sorgu': 'Anfrage', 
        'out_ip_konum_bilgi': 'Standortdaten', 'out_ip_ulke': 'Land', 'out_ip_bolge': 'Region',
        'out_ip_saat': 'Zeitzone', 'out_ip_ag_bilgi': 'Netzwerkdaten', 'out_ip_inet': 'Internet IP',
        'out_ip_isp': 'Internetanbieter (ISP)', 'out_ip_org': 'Organisation', 'out_ip_asn': 'Infrastruktur (ASN)',
        'out_ip_mobil': 'Mobilfunknetz', 'out_ip_ptr': 'Reverse DNS (PTR)',
        'out_ip_gizlilik': 'Datenschutz & Bedrohung', 'out_ip_tehdit': 'Bedrohungswert',
        'out_ip_portlar': 'Offene Ports', 'out_ip_servis': 'AZRxGUARD Sicherheitsanalyse',
        'out_ip_evet': '✅ Ja', 'out_ip_hayir': '❌ Nein', 'out_ip_mobil_evet': '📱 Ja',
        'out_ip_risk_yuksek': 'Hohes Risiko', 'out_ip_risk_orta': 'Mittleres Risiko', 'out_ip_risk_dusuk': 'Geringes Risiko',
        'out_ip_dc': 'RECHENZENTRUM IP!', 'out_ip_port_yok': 'Keine offenen Ports',
        'out_hesap_title': 'TASCHENRECHNER', 'out_hesap_ifade': 'Ausdruck', 'out_hesap_sonuc': 'Ergebnis',
        'btn_bot_ayarlari': "⚙️ BOT EINSTELLUNGEN",
        'bot_ayarlari_welcome': "⚙️ **BOT EINSTELLUNGEN**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nEinstellung auswählen:",
        'btn_yazi_tipi': "🔤 BOT SCHRIFTART",
        'yazi_tipi_welcome': "🔤 **BOT SCHRIFTART**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nSchriftart wählen:\n_Alle Texte werden im gewählten Stil angezeigt!_",
        'font_changed': "✅ Schriftart geändert!",
        'font_active': "✅ Aktiv",
        'btn_siber_guvenlik': "🛡️ CYBERSICHERHEIT",
        'siber_guvenlik_welcome': "🛡️ **CYBERSICHERHEITSZENTRUM**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nWählen Sie ein Tool:",
        'btn_sifre_guc': "🔐 Passwort-Stärke-Test",
        'btn_oyun_tkmk': "✊ Stein-Schere-Papier",
        'btn_oyun_sayi': "🔢 Zahlen-Ratespiel",
        'btn_video_olusturucu': "🎬 Video-Editor",
        'btn_ved_kirp': "✂️ Video schneiden",
        'btn_ved_hiz': "⚡ Geschwindigkeit",
        'btn_ved_don': "🔄 Drehen",
        'btn_ved_ses': "🎵 Ton extrahieren",
        'btn_ved_sessiz': "🔇 Stummschalten",
        'btn_ved_kare': "📸 Frame entnehmen",
        'btn_ved_gif': "🎞️ GIF erstellen",
        'btn_ved_boyut': "📐 Größe ändern",
        'btn_ved_filtre': "🎨 Filter anwenden",
        'btn_ved_yazi': "🎬 Text hinzufügen",
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
        'out_hava_title': 'ამინდი', 'out_hava_konum': 'მდებარეობა', 'out_hava_sicaklik': 'ტემპერატურა',
        'out_hava_hissedilen': 'შეგრძნება', 'out_hava_nem': 'ტენიანობა', 'out_hava_ruzgar': 'ქარი',
        'out_hava_basinc': 'წნევა', 'out_hava_durum': 'მდგომარეობა', 'out_hava_uv': 'UV ინდექსი',
        'out_hava_gorus': 'ხილვადობა', 'out_hava_servis': 'AZRxGUARD ამინდის სერვისი',
        'out_doviz_title': 'ვალუტის გადამყვანი', 'out_doviz_giris': 'შეყვანა', 'out_doviz_sonuc': 'შედეგი',
        'out_doviz_kur': 'კურსი', 'out_doviz_guncelleme': 'განახლება', 'out_doviz_kaynak': 'წყარო',
        'out_doviz_servis': 'AZRxGUARD ვალუტის სერვისი',
        'out_saat_title': 'მსოფლიო საათი', 'out_saat_servis': 'AZRxGUARD დროის სერვისი',
        'out_hash_title': 'HASH გენერატორი', 'out_hash_metin': 'ტექსტი', 'out_hash_uzunluk': 'სიგრძე', 'out_hash_karakter': 'სიმბ.',
        'out_b64_enc': 'BASE64 ENCODE', 'out_b64_dec': 'BASE64 DECODE', 'out_b64_giris': 'შეყვანა', 'out_b64_sonuc': 'შედეგი',
        'out_ip_title': 'IP დეტალური უსაფრთხოების ანალიზი', 'out_ip_sorgu': 'მოთხოვნა',
        'out_ip_konum_bilgi': 'მდებარეობის ინფო', 'out_ip_ulke': 'ქვეყანა', 'out_ip_bolge': 'რეგიონი',
        'out_ip_saat': 'დროის სარტყელი', 'out_ip_ag_bilgi': 'ქსელის ინფო', 'out_ip_inet': 'ინტერნეტ IP',
        'out_ip_isp': 'ინტერნეტ პროვაიდერი (ISP)', 'out_ip_org': 'ორგანიზაცია', 'out_ip_asn': 'ინფრასტრუქტურა (ASN)',
        'out_ip_mobil': 'მობილური ქსელი', 'out_ip_ptr': 'Reverse DNS (PTR)',
        'out_ip_gizlilik': 'კონფიდენციალობა & საფრთხე', 'out_ip_tehdit': 'საფრთხის ქულა',
        'out_ip_portlar': 'ღია პორტები', 'out_ip_servis': 'AZRxGUARD უსაფრთხოების ანალიზი',
        'out_ip_evet': '✅ დიახ', 'out_ip_hayir': '❌ არა', 'out_ip_mobil_evet': '📱 დიახ',
        'out_ip_risk_yuksek': 'მაღალი რისკი', 'out_ip_risk_orta': 'საშუალო რისკი', 'out_ip_risk_dusuk': 'დაბალი რისკი',
        'out_ip_dc': 'მონაცემთა ცენტრის IP!', 'out_ip_port_yok': 'ღია პორტი ვერ მოიძებნა',
        'out_hesap_title': 'კალკულატორი', 'out_hesap_ifade': 'გამოსახულება', 'out_hesap_sonuc': 'შედეგი',
        'btn_bot_ayarlari': "⚙️ BOT პარამეტრები",
        'bot_ayarlari_welcome': "⚙️ **BOT პარამეტრები**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nპარამეტრი აირჩიეთ:",
        'btn_yazi_tipi': "🔤 BOT შრიფტი",
        'yazi_tipi_welcome': "🔤 **BOT შრიფტი**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nშრიფტი აირჩიეთ:\n_ყველა ტექსტი არჩეულ სტილში გამოჩნდება!_",
        'font_changed': "✅ შრიფტი შეიცვალა!",
        'font_active': "✅ აქტიური",
        'btn_siber_guvenlik': "🛡️ კიბერ უსაფრთხოება",
        'siber_guvenlik_welcome': "🛡️ **კიბერ უსაფრთხოების ცენტრი**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nაირჩიეთ ინსტრუმენტი:",
        'btn_sifre_guc': "🔐 პაროლის სიძლიერის ტესტი",
        'btn_oyun_tkmk': "✊ ქვა-ქაღალდი-მაკრატელი",
        'btn_oyun_sayi': "🔢 ნომრის გამოცნობა",
        'btn_video_olusturucu': "🎬 ვიდეო რედაქტორი",
        'btn_ved_kirp': "✂️ ვიდეოს კვეთა",
        'btn_ved_hiz': "⚡ სიჩქარის შეცვლა",
        'btn_ved_don': "🔄 ვიდეოს ბრუნვა",
        'btn_ved_ses': "🎵 ხმის ამოღება",
        'btn_ved_sessiz': "🔇 ხმის გამორთვა",
        'btn_ved_kare': "📸 კადრის ამოღება",
        'btn_ved_gif': "🎞️ GIF-ად გადაყვანა",
        'btn_ved_boyut': "📐 ზომის შეცვლა",
        'btn_ved_filtre': "🎨 ფილტრის გამოყენება",
        'btn_ved_yazi': "🎬 ტექსტის დამატება",
    }
}

# --- YARDIMCI FONKSİYONLAR ---
def get_lang(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> str:
    if 'lang' not in context.bot_data:
        context.bot_data['lang'] = {}
    return context.bot_data['lang'].get(user_id, 'tr')

def ana_menu_klavye(lang: str, font_id: str = 'normal') -> InlineKeyboardMarkup:
    strings = FontStrings(LANG_DATA[lang], font_id)
    klavye = [
        [
            InlineKeyboardButton(strings.get('btn_bot_ayarlari', '⚙️ BOT AYARLARI'), callback_data='menu_bot_ayarlari'),
            InlineKeyboardButton(strings['btn_channel'], url='https://t.me/azrXmaqa')
        ],
        [
            InlineKeyboardButton(strings['btn_admin'], callback_data='menu_admin')
        ],
        [
            InlineKeyboardButton(strings['btn_azr_special'], callback_data='menu_azr_special')
        ],
        [
            InlineKeyboardButton(strings.get('btn_pro_araclar', '⚡ PRO ARAÇLAR'), callback_data='menu_pro_araclar')
        ],
        [
            InlineKeyboardButton(strings.get('btn_video_olusturucu', '🎬 VİDEO OLUŞTURUCU'), callback_data='menu_video_olusturucu')
        ],
        [
            InlineKeyboardButton('📦 APK-OBB-CONFİG', callback_data='menu_apk_obb')
        ],
        [
            InlineKeyboardButton('🚗 ARABA MENÜSÜ', callback_data='menu_araba')
        ],
    ]
    return InlineKeyboardMarkup(klavye)


# ─────────────────────────────────────────────────────────────
# 📱 TELEFON FİYATLARI VERİTABANI — 22 MARKA / 400+ MODEL
# ─────────────────────────────────────────────────────────────
TELEFON_VERITABANI = {
    'sam': {'ad': 'Samsung', 'emoji': '📱', 'modeller': [
        # Galaxy S25 Serisi (2025)
        'Galaxy S25 Ultra','Galaxy S25+','Galaxy S25','Galaxy S25 Edge',
        # Galaxy S24 Serisi
        'Galaxy S24 Ultra','Galaxy S24+','Galaxy S24','Galaxy S24 FE',
        # Galaxy S23 Serisi
        'Galaxy S23 Ultra','Galaxy S23+','Galaxy S23','Galaxy S23 FE',
        # Galaxy S22 Serisi
        'Galaxy S22 Ultra','Galaxy S22+','Galaxy S22',
        # Galaxy S21 Serisi
        'Galaxy S21 Ultra','Galaxy S21+','Galaxy S21','Galaxy S21 FE',
        # Galaxy S20 Serisi
        'Galaxy S20 Ultra','Galaxy S20+','Galaxy S20','Galaxy S20 FE',
        # Galaxy S10 Serisi
        'Galaxy S10+','Galaxy S10','Galaxy S10e','Galaxy S10 5G',
        # Note Serisi
        'Galaxy Note 20 Ultra','Galaxy Note 20','Galaxy Note 10+','Galaxy Note 10','Galaxy Note 10 Lite',
        # Z Serisi (Katlanabilir)
        'Galaxy Z Fold 6','Galaxy Z Fold 5','Galaxy Z Fold 4','Galaxy Z Fold 3',
        'Galaxy Z Flip 6','Galaxy Z Flip 5','Galaxy Z Flip 4','Galaxy Z Flip 3',
        # A Serisi (2025 — Yeni)
        'Galaxy A56 5G','Galaxy A36 5G','Galaxy A26 5G','Galaxy A16 5G','Galaxy A06',
        # A Serisi
        'Galaxy A55 5G','Galaxy A54 5G','Galaxy A53 5G','Galaxy A52s 5G','Galaxy A52',
        'Galaxy A35 5G','Galaxy A34 5G','Galaxy A33 5G','Galaxy A32','Galaxy A32 5G',
        'Galaxy A25 5G','Galaxy A24','Galaxy A23 5G','Galaxy A23','Galaxy A22 5G','Galaxy A22',
        'Galaxy A15 5G','Galaxy A15','Galaxy A14 5G','Galaxy A14','Galaxy A13','Galaxy A13 5G',
        'Galaxy A05s','Galaxy A05','Galaxy A04s','Galaxy A03s','Galaxy A03',
        # F Serisi
        'Galaxy F55 5G','Galaxy F35 5G','Galaxy F15 5G',
        # M Serisi (2025)
        'Galaxy M55 5G','Galaxy M35 5G',
        # M Serisi
        'Galaxy M54 5G','Galaxy M53 5G','Galaxy M34 5G','Galaxy M33 5G','Galaxy M14 5G',
    ]},
    'iph': {'ad': 'iPhone (Apple)', 'emoji': '🍎', 'modeller': [
        # iPhone 16 Serisi (2024)
        'iPhone 16 Pro Max','iPhone 16 Pro','iPhone 16 Plus','iPhone 16','iPhone 16e',
        # iPhone 15 Serisi
        'iPhone 15 Pro Max','iPhone 15 Pro','iPhone 15 Plus','iPhone 15',
        # iPhone 14 Serisi
        'iPhone 14 Pro Max','iPhone 14 Pro','iPhone 14 Plus','iPhone 14',
        # iPhone 13 Serisi
        'iPhone 13 Pro Max','iPhone 13 Pro','iPhone 13 mini','iPhone 13',
        # iPhone 12 Serisi
        'iPhone 12 Pro Max','iPhone 12 Pro','iPhone 12 mini','iPhone 12',
        # iPhone 11 Serisi
        'iPhone 11 Pro Max','iPhone 11 Pro','iPhone 11',
        # iPhone X Serisi
        'iPhone XS Max','iPhone XS','iPhone XR','iPhone X',
        # iPhone SE
        'iPhone SE (2022)','iPhone SE (2020)',
    ]},
    'xia': {'ad': 'Xiaomi', 'emoji': '📱', 'modeller': [
        # Xiaomi 15 Serisi (2025 — Yeni)
        'Xiaomi 15 Ultra','Xiaomi 15 Pro','Xiaomi 15','Xiaomi 15 Ultra Manga',
        # Xiaomi 14 Serisi
        'Xiaomi 14 Ultra','Xiaomi 14 Pro','Xiaomi 14','Xiaomi 14T Pro','Xiaomi 14T','Xiaomi 14C',
        # Xiaomi 13 Serisi
        'Xiaomi 13 Ultra','Xiaomi 13 Pro','Xiaomi 13','Xiaomi 13T Pro','Xiaomi 13T',
        # Xiaomi 12 Serisi
        'Xiaomi 12 Pro','Xiaomi 12','Xiaomi 12T Pro','Xiaomi 12T','Xiaomi 12 Lite',
        # Xiaomi 11 Serisi
        'Xiaomi 11 Ultra','Xiaomi 11 Pro','Xiaomi 11','Xiaomi 11T Pro','Xiaomi 11T','Xiaomi 11 Lite 5G NE',
        # Redmi Note 14 Serisi (2025 — Yeni)
        'Redmi Note 14 Pro+ 5G','Redmi Note 14 Pro 5G','Redmi Note 14 5G','Redmi Note 14','Redmi Note 14 Pro',
        # Redmi Note 13 Serisi
        'Redmi Note 13 Pro+ 5G','Redmi Note 13 Pro 5G','Redmi Note 13 5G','Redmi Note 13','Redmi Note 13 Pro',
        # Redmi Note 12 Serisi
        'Redmi Note 12 Pro+ 5G','Redmi Note 12 Pro 5G','Redmi Note 12 5G','Redmi Note 12','Redmi Note 12s','Redmi Note 12 Turbo',
        # Redmi Note 11 Serisi
        'Redmi Note 11 Pro+ 5G','Redmi Note 11 Pro','Redmi Note 11S 5G','Redmi Note 11S','Redmi Note 11','Redmi Note 11 5G',
        # Redmi Note 10 Serisi
        'Redmi Note 10 Pro Max','Redmi Note 10 Pro','Redmi Note 10','Redmi Note 10s','Redmi Note 10 5G',
        # Redmi Serisi (2025)
        'Redmi 14C','Redmi 14 5G',
        # Redmi Serisi
        'Redmi 13C 5G','Redmi 13C','Redmi 13','Redmi 12C','Redmi 12','Redmi 12 5G',
        'Redmi 10C','Redmi 10','Redmi 10A','Redmi A3','Redmi A2+','Redmi A2','Redmi A1+',
        # Xiaomi Pad
        'Xiaomi Pad 7 Pro','Xiaomi Pad 7','Xiaomi Pad 6 Pro','Xiaomi Pad 6',
    ]},
    'poc': {'ad': 'POCO', 'emoji': '📱', 'modeller': [
        # POCO X7 Serisi (2025 — Yeni)
        'POCO X7 Pro 5G','POCO X7 5G',
        # POCO X6 Serisi
        'POCO X6 Pro 5G','POCO X6 5G',
        # POCO X5 Serisi
        'POCO X5 Pro 5G','POCO X5 5G',
        # POCO X4/X3 Serisi
        'POCO X4 Pro 5G','POCO X4 GT','POCO X3 Pro','POCO X3 GT','POCO X3 NFC','POCO X3',
        # POCO F Serisi
        'POCO F6 Pro','POCO F6 5G','POCO F5 Pro 5G','POCO F5 5G','POCO F4 GT','POCO F4 5G','POCO F3','POCO F2 Pro',
        # POCO M Serisi
        'POCO M6 Pro 5G','POCO M6 5G','POCO M5s','POCO M5','POCO M4 Pro 5G','POCO M4 Pro','POCO M4 5G','POCO M3 Pro 5G',
        # POCO C Serisi
        'POCO C75','POCO C65','POCO C55','POCO C51','POCO C40',
    ]},
    'gpx': {'ad': 'Google Pixel', 'emoji': '🔵', 'modeller': [
        # Pixel 9 Serisi (2024)
        'Pixel 9 Pro XL','Pixel 9 Pro','Pixel 9','Pixel 9 Pro Fold',
        # Pixel 9a (2025)
        'Pixel 9a',
        # Pixel 8 Serisi
        'Pixel 8 Pro','Pixel 8','Pixel 8a',
        # Pixel 7 Serisi
        'Pixel 7 Pro','Pixel 7','Pixel 7a',
        # Pixel 6 Serisi
        'Pixel 6 Pro','Pixel 6','Pixel 6a',
        # Pixel 5 ve öncesi
        'Pixel 5','Pixel 5a 5G','Pixel 4a 5G','Pixel 4a',
        'Pixel 4 XL','Pixel 4',
    ]},
    'tec': {'ad': 'Tecno', 'emoji': '📱', 'modeller': [
        'Phantom V Fold 2 5G','Phantom V Flip 5G',
        'Phantom X2 Pro','Phantom X2','Phantom X',
        'Camon 30 Premier 5G','Camon 30 Pro 5G','Camon 30 5G','Camon 30',
        'Camon 20 Premier 5G','Camon 20 Pro 5G','Camon 20 Pro','Camon 20','Camon 19 Pro','Camon 19',
        'Spark 20 Pro+','Spark 20 Pro','Spark 20C','Spark 20','Spark 10 Pro','Spark 10','Spark 10C',
        'Pova 6 Pro 5G','Pova 6 5G','Pova 5 Pro','Pova 5',
        'Spark Go 2024','Spark Go 2023',
    ]},
    'hon': {'ad': 'Honor', 'emoji': '📱', 'modeller': [
        'Honor Magic6 Pro','Honor Magic6','Honor Magic6 Lite',
        'Honor Magic5 Pro','Honor Magic5 Lite',
        'Honor 200 Pro','Honor 200','Honor 200 Lite',
        'Honor 90 GT','Honor 90 Pro','Honor 90','Honor 90 Lite',
        'Honor 80 Pro','Honor 80','Honor 80 Lite','Honor 80 SE',
        'Honor X9b 5G','Honor X8b','Honor X7b','Honor X6b',
        'Honor X9a 5G','Honor X8a','Honor X7a','Honor X6a',
        'Honor X50 5G','Honor X40 5G','Honor X30i','Honor X20',
        'Honor Play 8T','Honor Play 7T','Honor Pad 9',
    ]},
    'can': {'ad': 'CANE', 'emoji': '📱', 'modeller': [
        'CANE P10 Pro','CANE P10','CANE P8 Pro','CANE P8',
        'CANE X5 5G','CANE X5','CANE Note 10',
        'CANE S6 Pro','CANE S6',
    ]},
    'hua': {'ad': 'Huawei', 'emoji': '📱', 'modeller': [
        # Mate Serisi
        'Huawei Mate 60 Pro+','Huawei Mate 60 Pro','Huawei Mate 60','Huawei Mate 60 RS',
        'Huawei Mate 50 Pro','Huawei Mate 50','Huawei Mate 50E',
        'Huawei Mate 40 Pro+','Huawei Mate 40 Pro','Huawei Mate 40',
        # P Serisi
        'Huawei P60 Pro','Huawei P60','Huawei P60 Art',
        'Huawei P50 Pro','Huawei P50','Huawei P50 Pocket',
        'Huawei P40 Pro+','Huawei P40 Pro','Huawei P40','Huawei P40 Lite',
        'Huawei P30 Pro','Huawei P30','Huawei P30 Lite',
        # Nova Serisi
        'Huawei Nova 12 Pro','Huawei Nova 12','Huawei Nova 11 Pro','Huawei Nova 11',
        'Huawei Nova 10 Pro','Huawei Nova 10','Huawei Nova 9','Huawei Nova 9 SE',
        # Y Serisi & Diğer
        'Huawei Y9s','Huawei Y9a','Huawei Y7a','Huawei Y6p',
        'Huawei Pocket 2','Huawei Pocket S',
    ]},
    'lov': {'ad': 'LOVEIR', 'emoji': '📱', 'modeller': [
        'LOVEIR X1 Pro','LOVEIR X1','LOVEIR V10 Pro','LOVEIR V10',
        'LOVEIR Note 8 Pro','LOVEIR Note 8','LOVEIR S7',
    ]},
    'opp': {'ad': 'OPPO / Realme', 'emoji': '📱', 'modeller': [
        # OPPO
        'OPPO Find X7 Ultra','OPPO Find X7 Pro','OPPO Find X7',
        'OPPO Find X6 Pro','OPPO Find X5 Pro','OPPO Find X5',
        'OPPO Reno 12 Pro','OPPO Reno 12','OPPO Reno 11 Pro 5G','OPPO Reno 11',
        'OPPO Reno 10 Pro+ 5G','OPPO Reno 10 Pro 5G','OPPO Reno 10 5G',
        'OPPO Reno 9 Pro+','OPPO Reno 9','OPPO Reno 8 Pro','OPPO Reno 8',
        'OPPO A79 5G','OPPO A78 5G','OPPO A58 5G','OPPO A38','OPPO A18',
        # Realme
        'Realme GT 6 Pro','Realme GT 6','Realme GT 5 Pro','Realme GT 5',
        'Realme GT 2 Pro','Realme GT 2','Realme GT Master Edition',
        'Realme 12 Pro+','Realme 12 Pro','Realme 12+','Realme 12',
        'Realme 11 Pro+ 5G','Realme 11 Pro','Realme 11',
        'Realme C65 5G','Realme C55','Realme C53','Realme C51','Realme C35',
        'Realme Narzo 70 Pro','Realme Narzo 60 Pro','Realme Narzo 50',
    ]},
    'inf': {'ad': 'Infinix', 'emoji': '📱', 'modeller': [
        'Infinix Zero 40 5G','Infinix Zero 40','Infinix Zero 30 5G','Infinix Zero 30','Infinix Zero 20',
        'Infinix Note 40 Pro+ 5G','Infinix Note 40 Pro 5G','Infinix Note 40 Pro','Infinix Note 40',
        'Infinix Note 30 Pro 5G','Infinix Note 30 VIP','Infinix Note 30 5G','Infinix Note 30',
        'Infinix Note 12 Pro+','Infinix Note 12 Pro','Infinix Note 12 G96','Infinix Note 12 5G',
        'Infinix Hot 40 Pro','Infinix Hot 40','Infinix Hot 40i',
        'Infinix Hot 30 Play','Infinix Hot 30 5G','Infinix Hot 30',
        'Infinix Hot 20 Pro','Infinix Hot 20',
        'Infinix GT 20 Pro','Infinix GT 10 Pro',
        'Infinix Smart 8 Plus','Infinix Smart 8',
    ]},
    'one': {'ad': 'OnePlus', 'emoji': '📱', 'modeller': [
        # OnePlus 13 Serisi (2025 — Yeni)
        'OnePlus 13','OnePlus 13R',
        # OnePlus 12 Serisi
        'OnePlus 12R','OnePlus 12',
        # OnePlus 11 Serisi
        'OnePlus 11R','OnePlus 11 5G',
        # OnePlus 10 Serisi
        'OnePlus 10 Pro','OnePlus 10T 5G','OnePlus 10R',
        # OnePlus 9 Serisi
        'OnePlus 9 Pro','OnePlus 9','OnePlus 9R',
        # OnePlus 8 Serisi
        'OnePlus 8 Pro','OnePlus 8T','OnePlus 8',
        # OnePlus Open (Katlanabilir)
        'OnePlus Open','OnePlus Open 2',
        # Nord Serisi
        'OnePlus Nord 4 5G','OnePlus Nord 3 5G','OnePlus Nord 2T 5G','OnePlus Nord 2 5G',
        'OnePlus Nord CE 4 Lite 5G','OnePlus Nord CE 4','OnePlus Nord CE 3 Lite 5G','OnePlus Nord CE 3 5G',
        'OnePlus Nord CE 2 Lite 5G','OnePlus Nord CE 2 5G',
        'OnePlus Nord N30 5G','OnePlus Nord N20 5G',
    ]},
    'viv': {'ad': 'Vivo', 'emoji': '📱', 'modeller': [
        'Vivo X100 Ultra','Vivo X100 Pro','Vivo X100+','Vivo X100',
        'Vivo X90 Pro+','Vivo X90 Pro','Vivo X90',
        'Vivo X80 Pro','Vivo X80',
        'Vivo V30 Pro','Vivo V30','Vivo V29 Pro','Vivo V29',
        'Vivo V27 Pro','Vivo V27','Vivo V25 Pro','Vivo V25',
        'Vivo Y200 Pro 5G','Vivo Y200 5G','Vivo Y100 5G','Vivo Y100',
        'Vivo Y78 5G','Vivo Y78+','Vivo Y56 5G','Vivo Y36 5G','Vivo Y36',
        'Vivo Y27s','Vivo Y27 5G','Vivo Y17s',
    ]},
    'asd': {'ad': 'ASD', 'emoji': '📱', 'modeller': [
        'ASD X9 Pro','ASD X9','ASD X7 Pro',
        'ASD Note 12 Pro','ASD Note 12',
        'ASD P9 Pro','ASD P7','ASD S8','ASD S6',
    ]},
    'nok': {'ad': 'Nokia / Motorola', 'emoji': '📱', 'modeller': [
        # Nokia
        'Nokia G42 5G','Nokia G60 5G','Nokia G400 5G','Nokia G310 5G',
        'Nokia X30 5G','Nokia XR21','Nokia C32','Nokia C22',
        # Motorola
        'Motorola Edge 50 Ultra','Motorola Edge 50 Pro','Motorola Edge 50 Fusion','Motorola Edge 50',
        'Motorola Edge 40 Neo','Motorola Edge 40 Pro','Motorola Edge 40',
        'Motorola Edge 30 Ultra','Motorola Edge 30 Pro','Motorola Edge 30',
        'Motorola Moto G85 5G','Motorola Moto G84 5G','Motorola Moto G73 5G',
        'Motorola Moto G54 5G','Motorola Moto G34 5G','Motorola Moto G24',
        'Motorola Moto G14','Motorola Moto G62 5G',
    ]},
    'gam': {'ad': 'Gaming Telefonlar 🎮', 'emoji': '🎮', 'modeller': [
        'ASUS ROG Phone 8 Pro','ASUS ROG Phone 8','ASUS ROG Phone 7 Pro','ASUS ROG Phone 7 Ultimate',
        'ASUS ROG Phone 7','ASUS ROG Phone 6 Pro','ASUS ROG Phone 6',
        'Nubia RedMagic 9 Pro+','Nubia RedMagic 9 Pro','Nubia RedMagic 9S',
        'Nubia RedMagic 8 Pro+','Nubia RedMagic 8 Pro','Nubia RedMagic 8S Pro',
        'Nubia RedMagic 7 Pro','Nubia RedMagic 7',
        'Xiaomi Black Shark 5 Pro','Xiaomi Black Shark 5',
        'Lenovo Legion Phone 3 Pro','Lenovo Legion Phone 2 Pro',
    ]},
    'son': {'ad': 'Sony', 'emoji': '📱', 'modeller': [
        'Sony Xperia 1 VI','Sony Xperia 1 V','Sony Xperia 1 IV','Sony Xperia 1 III',
        'Sony Xperia 5 VI','Sony Xperia 5 V','Sony Xperia 5 IV','Sony Xperia 5 III',
        'Sony Xperia 10 VI','Sony Xperia 10 V','Sony Xperia 10 IV','Sony Xperia 10 III',
        'Sony Xperia Pro-I','Sony Xperia Pro',
        'Sony Xperia L4','Sony Xperia Ace III',
    ]},
    'zte': {'ad': 'ZTE / Nubia', 'emoji': '📱', 'modeller': [
        'ZTE Blade V60 Design','ZTE Blade V50 Design','ZTE Blade V50 Vita',
        'ZTE Blade A75 5G','ZTE Blade A75','ZTE Blade A54','ZTE Blade A34','ZTE Blade A73 5G',
        'Nubia Z60 Ultra','Nubia Z50S Pro','Nubia Z50 Ultra','Nubia Z50',
        'Nubia Focus 5G','Nubia Neo 5G','Nubia Music',
    ]},
    'lav': {'ad': 'Lava', 'emoji': '📱', 'modeller': [
        'Lava Agni 3 5G','Lava Agni 2 5G','Lava Agni 1 5G',
        'Lava Blaze 2 5G','Lava Blaze Curve 5G','Lava Blaze 5G',
        'Lava Storm 5G','Lava O2 5G','Lava X3 5G',
        'Lava Yuva 3 Pro','Lava Yuva 2 Pro',
    ]},
    'sha': {'ad': 'Sharp / Meizu', 'emoji': '📱', 'modeller': [
        # Sharp
        'Sharp AQUOS R9','Sharp AQUOS R8 Pro','Sharp AQUOS R8',
        'Sharp AQUOS R7','Sharp AQUOS sense8','Sharp AQUOS sense7',
        'Sharp AQUOS wish3','Sharp AQUOS zero6',
        # Meizu
        'Meizu 21 Pro','Meizu 21','Meizu 21 Note',
        'Meizu 20 Pro','Meizu 20','Meizu 20 Infinity',
        'Meizu Note 21 Pro','Meizu Note 21','Meizu Blue Note 21S',
    ]},
    'dog': {'ad': 'Doogee / Ulefone', 'emoji': '📱', 'modeller': [
        # Doogee
        'Doogee V Max Pro','Doogee V Max','Doogee V30 Pro','Doogee V30','Doogee V20 Pro',
        'Doogee S100 Pro','Doogee S100','Doogee S98 Pro','Doogee S98',
        'Doogee N55 Pro','Doogee N40 Pro','Doogee X98 Pro','Doogee X98',
        # Ulefone
        'Ulefone Power Armor 23 Ultra','Ulefone Power Armor 23','Ulefone Power Armor 19T',
        'Ulefone Armor 23 Ultra','Ulefone Armor 21','Ulefone Armor 20WT',
        'Ulefone Note 17 Pro','Ulefone Note 16 Pro',
    ]},
}

# Telefon detaylı özellikler (popüler modeller)
TELEFON_SPECS_DB = {
    # ── SAMSUNG S SERİSİ ──
    'Samsung Galaxy S24 Ultra': {'5g': True, 'ram': '12 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5000 mAh', 'ekran': '6.8" QHD+ LTPO AMOLED 120Hz', 'kamera': '200MP+50MP+10MP+12MP', 'os': 'Android 14'},
    'Samsung Galaxy S24+': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '4900 mAh', 'ekran': '6.7" QHD+ AMOLED 120Hz', 'kamera': '50MP+12MP+10MP', 'os': 'Android 14'},
    'Samsung Galaxy S24': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '4000 mAh', 'ekran': '6.2" FHD+ AMOLED 120Hz', 'kamera': '50MP+12MP+10MP', 'os': 'Android 14'},
    'Samsung Galaxy S24 FE': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ekim', 'islemci': 'Exynos 2500', 'batarya': '4700 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+10MP+8MP', 'os': 'Android 14'},
    'Samsung Galaxy S23 Ultra': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.8" QHD+ LTPO AMOLED 120Hz', 'kamera': '200MP+12MP+10MP+10MP', 'os': 'Android 13→14'},
    'Samsung Galaxy S23+': {'5g': True, 'ram': '8 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '4700 mAh', 'ekran': '6.6" FHD+ AMOLED 120Hz', 'kamera': '50MP+12MP+10MP', 'os': 'Android 13→14'},
    'Samsung Galaxy S23': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '3900 mAh', 'ekran': '6.1" FHD+ AMOLED 120Hz', 'kamera': '50MP+12MP+10MP', 'os': 'Android 13→14'},
    'Samsung Galaxy S23 FE': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '4500 mAh', 'ekran': '6.4" FHD+ AMOLED 120Hz', 'kamera': '50MP+12MP+8MP', 'os': 'Android 13→14'},
    'Samsung Galaxy S22 Ultra': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256/512/1TB', 'sim': 2, 'cikis': '2022 Şubat', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.8" QHD+ LTPO AMOLED 120Hz', 'kamera': '108MP+12MP+10MP+10MP', 'os': 'Android 12→14'},
    'Samsung Galaxy S22+': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Şubat', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '4500 mAh', 'ekran': '6.6" FHD+ AMOLED 120Hz', 'kamera': '50MP+12MP+10MP', 'os': 'Android 12→14'},
    'Samsung Galaxy S22': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Şubat', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '3700 mAh', 'ekran': '6.1" FHD+ AMOLED 120Hz', 'kamera': '50MP+12MP+10MP', 'os': 'Android 12→14'},
    'Samsung Galaxy S21 Ultra': {'5g': True, 'ram': '12/16 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2021 Ocak', 'islemci': 'Snapdragon 888', 'batarya': '5000 mAh', 'ekran': '6.8" QHD+ LTPO AMOLED 120Hz', 'kamera': '108MP+12MP+10MP+10MP', 'os': 'Android 11→14'},
    'Samsung Galaxy S21+': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Ocak', 'islemci': 'Snapdragon 888', 'batarya': '4800 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '12MP+64MP+12MP', 'os': 'Android 11→14'},
    'Samsung Galaxy S21': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Ocak', 'islemci': 'Snapdragon 888', 'batarya': '4000 mAh', 'ekran': '6.2" FHD+ AMOLED 120Hz', 'kamera': '12MP+64MP+12MP', 'os': 'Android 11→14'},
    'Samsung Galaxy S21 FE': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ocak', 'islemci': 'Snapdragon 888', 'batarya': '4500 mAh', 'ekran': '6.4" FHD+ AMOLED 120Hz', 'kamera': '12MP+32MP+8MP', 'os': 'Android 12→14'},
    'Samsung Galaxy S20 Ultra': {'5g': True, 'ram': '12/16 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2020 Mart', 'islemci': 'Snapdragon 865', 'batarya': '5000 mAh', 'ekran': '6.9" QHD+ LTPO AMOLED 120Hz', 'kamera': '108MP+12MP+48MP', 'os': 'Android 10→13'},
    'Samsung Galaxy S20+': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2020 Mart', 'islemci': 'Snapdragon 865', 'batarya': '4500 mAh', 'ekran': '6.7" QHD+ AMOLED 120Hz', 'kamera': '12MP+64MP+12MP', 'os': 'Android 10→13'},
    'Samsung Galaxy S20': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2020 Mart', 'islemci': 'Snapdragon 865', 'batarya': '4000 mAh', 'ekran': '6.2" QHD+ AMOLED 120Hz', 'kamera': '12MP+64MP+12MP', 'os': 'Android 10→13'},
    'Samsung Galaxy S20 FE': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2020 Ekim', 'islemci': 'Snapdragon 865', 'batarya': '4500 mAh', 'ekran': '6.5" FHD+ AMOLED 120Hz', 'kamera': '12MP+8MP+8MP', 'os': 'Android 10→13'},
    'Samsung Galaxy S10+': {'5g': False, 'ram': '8/12 GB', 'depolama': '128/512/1TB', 'sim': 2, 'cikis': '2019 Mart', 'islemci': 'Snapdragon 855', 'batarya': '4100 mAh', 'ekran': '6.4" QHD+ AMOLED 60Hz', 'kamera': '12MP+12MP+16MP', 'os': 'Android 9→12'},
    'Samsung Galaxy S10': {'5g': False, 'ram': '8/12 GB', 'depolama': '128/512GB', 'sim': 2, 'cikis': '2019 Mart', 'islemci': 'Snapdragon 855', 'batarya': '3400 mAh', 'ekran': '6.1" QHD+ AMOLED 60Hz', 'kamera': '12MP+12MP+16MP', 'os': 'Android 9→12'},
    'Samsung Galaxy S10e': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2019 Mart', 'islemci': 'Snapdragon 855', 'batarya': '3100 mAh', 'ekran': '5.8" FHD+ AMOLED 60Hz', 'kamera': '12MP+16MP', 'os': 'Android 9→12'},
    'Samsung Galaxy S10 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2019 Nisan', 'islemci': 'Snapdragon 855', 'batarya': '4500 mAh', 'ekran': '6.7" QHD+ AMOLED 60Hz', 'kamera': '12MP+12MP+16MP+DepthVision', 'os': 'Android 9→12'},
    # Note Serisi
    'Samsung Galaxy Note 20 Ultra': {'5g': True, 'ram': '12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2020 Ağustos', 'islemci': 'Snapdragon 865+', 'batarya': '4500 mAh', 'ekran': '6.9" QHD+ LTPO AMOLED 120Hz', 'kamera': '108MP+12MP+12MP', 'os': 'Android 10→13'},
    'Samsung Galaxy Note 20': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2020 Ağustos', 'islemci': 'Snapdragon 865+', 'batarya': '4300 mAh', 'ekran': '6.7" FHD+ AMOLED 60Hz', 'kamera': '12MP+64MP+12MP', 'os': 'Android 10→13'},
    'Samsung Galaxy Note 10+': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2019 Ağustos', 'islemci': 'Snapdragon 855', 'batarya': '4300 mAh', 'ekran': '6.8" QHD+ AMOLED 60Hz', 'kamera': '12MP+16MP+12MP+DepthVision', 'os': 'Android 9→12'},
    'Samsung Galaxy Note 10': {'5g': False, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2019 Ağustos', 'islemci': 'Snapdragon 855', 'batarya': '3500 mAh', 'ekran': '6.3" FHD+ AMOLED 60Hz', 'kamera': '12MP+16MP+12MP', 'os': 'Android 9→12'},
    'Samsung Galaxy Note 10 Lite': {'5g': False, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2020 Ocak', 'islemci': 'Exynos 9810', 'batarya': '4500 mAh', 'ekran': '6.7" FHD+ AMOLED 60Hz', 'kamera': '12MP+12MP+12MP', 'os': 'Android 10→13'},
    # Z Fold
    'Samsung Galaxy Z Fold 6': {'5g': True, 'ram': '12 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2024 Temmuz', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '4400 mAh', 'ekran': '7.6" QXGA+ LTPO AMOLED 120Hz', 'kamera': '50MP+10MP+10MP', 'os': 'Android 14'},
    'Samsung Galaxy Z Fold 5': {'5g': True, 'ram': '12 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '4400 mAh', 'ekran': '7.6" QXGA+ LTPO AMOLED 120Hz', 'kamera': '50MP+10MP+10MP', 'os': 'Android 13→14'},
    'Samsung Galaxy Z Fold 4': {'5g': True, 'ram': '12 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2022 Ağustos', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '4400 mAh', 'ekran': '7.6" QXGA+ LTPO AMOLED 120Hz', 'kamera': '50MP+10MP+12MP', 'os': 'Android 12→14'},
    'Samsung Galaxy Z Fold 3': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2021 Ağustos', 'islemci': 'Snapdragon 888', 'batarya': '4400 mAh', 'ekran': '7.6" QXGA+ LTPO AMOLED 120Hz', 'kamera': '12MP+12MP+12MP', 'os': 'Android 11→14'},
    'Samsung Galaxy Z Flip 6': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Temmuz', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '4000 mAh', 'ekran': '6.7" FHD+ LTMO AMOLED 120Hz', 'kamera': '50MP+12MP', 'os': 'Android 14'},
    'Samsung Galaxy Z Flip 5': {'5g': True, 'ram': '8 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '3700 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '12MP+12MP', 'os': 'Android 13→14'},
    'Samsung Galaxy Z Flip 4': {'5g': True, 'ram': '8 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Ağustos', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '3700 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '12MP+12MP', 'os': 'Android 12→14'},
    'Samsung Galaxy Z Flip 3': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Ağustos', 'islemci': 'Snapdragon 888', 'batarya': '3300 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '12MP+12MP', 'os': 'Android 11→14'},
    # A Serisi
    'Samsung Galaxy A55 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'Exynos 1480', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ Super AMOLED 120Hz', 'kamera': '50MP+12MP+5MP', 'os': 'Android 14'},
    'Samsung Galaxy A54 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Exynos 1380', 'batarya': '5000 mAh', 'ekran': '6.4" FHD+ Super AMOLED 120Hz', 'kamera': '50MP+12MP+5MP', 'os': 'Android 13→14'},
    'Samsung Galaxy A53 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'Exynos 1280', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ Super AMOLED 120Hz', 'kamera': '64MP+12MP+5MP+5MP', 'os': 'Android 12→14'},
    'Samsung Galaxy A52s 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Eylül', 'islemci': 'Snapdragon 778G', 'batarya': '4500 mAh', 'ekran': '6.5" FHD+ Super AMOLED 120Hz', 'kamera': '64MP+12MP+5MP+5MP', 'os': 'Android 11→14'},
    'Samsung Galaxy A52': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Mart', 'islemci': 'Snapdragon 720G', 'batarya': '4500 mAh', 'ekran': '6.5" FHD+ Super AMOLED 90Hz', 'kamera': '64MP+12MP+5MP+5MP', 'os': 'Android 11→14'},
    'Samsung Galaxy A35 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'Exynos 1380', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ Super AMOLED 120Hz', 'kamera': '50MP+8MP+5MP', 'os': 'Android 14'},
    'Samsung Galaxy A34 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Dimensity 1080', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ Super AMOLED 120Hz', 'kamera': '48MP+8MP+5MP', 'os': 'Android 13→14'},
    'Samsung Galaxy A33 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'Exynos 1280', 'batarya': '5000 mAh', 'ekran': '6.4" FHD+ Super AMOLED 90Hz', 'kamera': '48MP+8MP+5MP+2MP', 'os': 'Android 12→14'},
    'Samsung Galaxy A32': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Ocak', 'islemci': 'MediaTek Helio G80', 'batarya': '5000 mAh', 'ekran': '6.4" FHD+ Super AMOLED 90Hz', 'kamera': '64MP+8MP+5MP+5MP', 'os': 'Android 11→13'},
    'Samsung Galaxy A32 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Ocak', 'islemci': 'MediaTek Dimensity 720', 'batarya': '5000 mAh', 'ekran': '6.5" HD+ TFT 90Hz', 'kamera': '48MP+8MP+5MP+2MP', 'os': 'Android 11→13'},
    'Samsung Galaxy A25 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Aralık', 'islemci': 'Exynos 1280', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ Super AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 14'},
    'Samsung Galaxy A24': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ Super AMOLED 90Hz', 'kamera': '50MP+5MP+2MP', 'os': 'Android 13→14'},
    'Samsung Galaxy A23 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Temmuz', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ PLS TFT 120Hz', 'kamera': '50MP+5MP+2MP+2MP', 'os': 'Android 12→14'},
    'Samsung Galaxy A23': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'Snapdragon 680 4G', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ PLS TFT 90Hz', 'kamera': '50MP+5MP+2MP+2MP', 'os': 'Android 12→14'},
    'Samsung Galaxy A22 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Temmuz', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ TFT 90Hz', 'kamera': '48MP+5MP+2MP', 'os': 'Android 11→13'},
    'Samsung Galaxy A22': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Temmuz', 'islemci': 'MediaTek Helio G80', 'batarya': '5000 mAh', 'ekran': '6.4" FHD+ Super AMOLED 90Hz', 'kamera': '48MP+8MP+2MP+2MP', 'os': 'Android 11→13'},
    'Samsung Galaxy A15 5G': {'5g': True, 'ram': '4/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Aralık', 'islemci': 'MediaTek Dimensity 6100+', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ Super AMOLED 90Hz', 'kamera': '50MP+5MP+2MP', 'os': 'Android 14'},
    'Samsung Galaxy A15': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Aralık', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ Super AMOLED 90Hz', 'kamera': '50MP+5MP+2MP', 'os': 'Android 14'},
    'Samsung Galaxy A14 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ PLS TFT 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 13→14'},
    'Samsung Galaxy A14': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'Exynos 850', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ PLS TFT 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 13→14'},
    'Samsung Galaxy A13': {'5g': False, 'ram': '3/4/6 GB', 'depolama': '32/64/128GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'Exynos 850', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ PLS TFT 60Hz', 'kamera': '50MP+5MP+2MP+2MP', 'os': 'Android 12→13'},
    'Samsung Galaxy A13 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Aralık', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ PLS TFT 90Hz', 'kamera': '50MP+5MP+2MP', 'os': 'Android 11→13'},
    'Samsung Galaxy A05s': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Snapdragon 680 4G', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ PLS TFT 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 13'},
    'Samsung Galaxy A05': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Kasım', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.7" HD+ PLS TFT 60Hz', 'kamera': '50MP+2MP', 'os': 'Android 13'},
    'Samsung Galaxy A04s': {'5g': False, 'ram': '3/4 GB', 'depolama': '32/64/128GB', 'sim': 2, 'cikis': '2022 Ağustos', 'islemci': 'Exynos 850', 'batarya': '5000 mAh', 'ekran': '6.5" HD+ PLS TFT 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 12→13'},
    # M Serisi
    'Samsung Galaxy M54 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Exynos 1380', 'batarya': '6000 mAh', 'ekran': '6.7" FHD+ Super AMOLED 120Hz', 'kamera': '108MP+8MP+2MP', 'os': 'Android 13→14'},
    'Samsung Galaxy M53 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'MediaTek Dimensity 900', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ Super AMOLED 120Hz', 'kamera': '108MP+8MP+2MP+2MP', 'os': 'Android 12→13'},
    'Samsung Galaxy M34 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'Exynos 1280', 'batarya': '6000 mAh', 'ekran': '6.5" FHD+ Super AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13→14'},
    'Samsung Galaxy M33 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'Exynos 1280', 'batarya': '6000 mAh', 'ekran': '6.6" FHD+ TFT 120Hz', 'kamera': '50MP+5MP+2MP+2MP', 'os': 'Android 12→13'},
    'Samsung Galaxy M14 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Exynos 1330', 'batarya': '6000 mAh', 'ekran': '6.7" FHD+ PLS TFT 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 13→14'},
    # ── iPHONE ──
    'iPhone 15 Pro Max': {'5g': True, 'ram': '8 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Apple A17 Pro', 'batarya': '4422 mAh', 'ekran': '6.7" LTPO Super Retina XDR OLED 120Hz', 'kamera': '48MP+12MP+12MP', 'os': 'iOS 17'},
    'iPhone 15 Pro': {'5g': True, 'ram': '8 GB', 'depolama': '128/256/512/1TB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Apple A17 Pro', 'batarya': '3274 mAh', 'ekran': '6.1" LTPO Super Retina XDR OLED 120Hz', 'kamera': '48MP+12MP+12MP', 'os': 'iOS 17'},
    'iPhone 15 Plus': {'5g': True, 'ram': '6 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Apple A16 Bionic', 'batarya': '4383 mAh', 'ekran': '6.7" Super Retina XDR OLED 60Hz', 'kamera': '48MP+12MP', 'os': 'iOS 17'},
    'iPhone 15': {'5g': True, 'ram': '6 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Apple A16 Bionic', 'batarya': '3349 mAh', 'ekran': '6.1" Super Retina XDR OLED 60Hz', 'kamera': '48MP+12MP', 'os': 'iOS 17'},
    'iPhone 14 Pro Max': {'5g': True, 'ram': '6 GB', 'depolama': '128/256/512/1TB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'Apple A16 Bionic', 'batarya': '4323 mAh', 'ekran': '6.7" LTPO Super Retina XDR OLED 120Hz', 'kamera': '48MP+12MP+12MP', 'os': 'iOS 16→17'},
    'iPhone 14 Pro': {'5g': True, 'ram': '6 GB', 'depolama': '128/256/512/1TB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'Apple A16 Bionic', 'batarya': '3200 mAh', 'ekran': '6.1" LTPO Super Retina XDR OLED 120Hz', 'kamera': '48MP+12MP+12MP', 'os': 'iOS 16→17'},
    'iPhone 14 Plus': {'5g': True, 'ram': '6 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'Apple A15 Bionic', 'batarya': '4325 mAh', 'ekran': '6.7" Super Retina XDR OLED 60Hz', 'kamera': '12MP+12MP', 'os': 'iOS 16→17'},
    'iPhone 14': {'5g': True, 'ram': '6 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'Apple A15 Bionic', 'batarya': '3279 mAh', 'ekran': '6.1" Super Retina XDR OLED 60Hz', 'kamera': '12MP+12MP', 'os': 'iOS 16→17'},
    'iPhone 13 Pro Max': {'5g': True, 'ram': '6 GB', 'depolama': '128/256/512/1TB', 'sim': 2, 'cikis': '2021 Eylül', 'islemci': 'Apple A15 Bionic', 'batarya': '4352 mAh', 'ekran': '6.7" LTPO Super Retina XDR OLED 120Hz', 'kamera': '12MP+12MP+12MP', 'os': 'iOS 15→17'},
    'iPhone 13 Pro': {'5g': True, 'ram': '6 GB', 'depolama': '128/256/512/1TB', 'sim': 2, 'cikis': '2021 Eylül', 'islemci': 'Apple A15 Bionic', 'batarya': '3095 mAh', 'ekran': '6.1" LTPO Super Retina XDR OLED 120Hz', 'kamera': '12MP+12MP+12MP', 'os': 'iOS 15→17'},
    'iPhone 13 mini': {'5g': True, 'ram': '4 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2021 Eylül', 'islemci': 'Apple A15 Bionic', 'batarya': '2406 mAh', 'ekran': '5.4" Super Retina XDR OLED 60Hz', 'kamera': '12MP+12MP', 'os': 'iOS 15→17'},
    'iPhone 13': {'5g': True, 'ram': '4 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2021 Eylül', 'islemci': 'Apple A15 Bionic', 'batarya': '3227 mAh', 'ekran': '6.1" Super Retina XDR OLED 60Hz', 'kamera': '12MP+12MP', 'os': 'iOS 15→17'},
    'iPhone 12 Pro Max': {'5g': True, 'ram': '6 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2020 Kasım', 'islemci': 'Apple A14 Bionic', 'batarya': '3687 mAh', 'ekran': '6.7" Super Retina XDR OLED 60Hz', 'kamera': '12MP+12MP+12MP', 'os': 'iOS 14→15'},
    'iPhone 12 Pro': {'5g': True, 'ram': '6 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2020 Ekim', 'islemci': 'Apple A14 Bionic', 'batarya': '2815 mAh', 'ekran': '6.1" Super Retina XDR OLED 60Hz', 'kamera': '12MP+12MP+12MP', 'os': 'iOS 14→15'},
    'iPhone 12 mini': {'5g': True, 'ram': '4 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2020 Ekim', 'islemci': 'Apple A14 Bionic', 'batarya': '2227 mAh', 'ekran': '5.4" Super Retina XDR OLED 60Hz', 'kamera': '12MP+12MP', 'os': 'iOS 14→15'},
    'iPhone 12': {'5g': True, 'ram': '4 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2020 Ekim', 'islemci': 'Apple A14 Bionic', 'batarya': '2815 mAh', 'ekran': '6.1" Super Retina XDR OLED 60Hz', 'kamera': '12MP+12MP', 'os': 'iOS 14→15'},
    'iPhone 11 Pro Max': {'5g': False, 'ram': '4 GB', 'depolama': '64/256/512GB', 'sim': 2, 'cikis': '2019 Eylül', 'islemci': 'Apple A13 Bionic', 'batarya': '3969 mAh', 'ekran': '6.5" Super Retina XDR OLED 60Hz', 'kamera': '12MP+12MP+12MP', 'os': 'iOS 13→15'},
    'iPhone 11 Pro': {'5g': False, 'ram': '4 GB', 'depolama': '64/256/512GB', 'sim': 2, 'cikis': '2019 Eylül', 'islemci': 'Apple A13 Bionic', 'batarya': '3046 mAh', 'ekran': '5.8" Super Retina XDR OLED 60Hz', 'kamera': '12MP+12MP+12MP', 'os': 'iOS 13→15'},
    'iPhone 11': {'5g': False, 'ram': '4 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2019 Eylül', 'islemci': 'Apple A13 Bionic', 'batarya': '3110 mAh', 'ekran': '6.1" Liquid Retina IPS LCD 60Hz', 'kamera': '12MP+12MP', 'os': 'iOS 13→15'},
    'iPhone SE (2022)': {'5g': True, 'ram': '4 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'Apple A15 Bionic', 'batarya': '2018 mAh', 'ekran': '4.7" Retina HD IPS LCD 60Hz', 'kamera': '12MP', 'os': 'iOS 15→16'},
    'iPhone SE (2020)': {'5g': False, 'ram': '3 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2020 Nisan', 'islemci': 'Apple A13 Bionic', 'batarya': '1821 mAh', 'ekran': '4.7" Retina HD IPS LCD 60Hz', 'kamera': '12MP', 'os': 'iOS 13→15'},
    # ── XİAOMİ ──
    'Xiaomi 14 Ultra': {'5g': True, 'ram': '16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5300 mAh', 'ekran': '6.73" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+50MP+50MP+50MP', 'os': 'Android 14 (HyperOS)'},
    'Xiaomi 14 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '4880 mAh', 'ekran': '6.73" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+50MP+50MP', 'os': 'Android 14 (HyperOS)'},
    'Xiaomi 14': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '4610 mAh', 'ekran': '6.36" FHD+ AMOLED 120Hz', 'kamera': '50MP+50MP+50MP', 'os': 'Android 14 (HyperOS)'},
    'Xiaomi 13 Ultra': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.73" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+50MP+50MP+50MP', 'os': 'Android 13 (MIUI 14)'},
    'Xiaomi 13 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '4820 mAh', 'ekran': '6.73" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+50MP+50MP', 'os': 'Android 13 (MIUI 14)'},
    'Xiaomi 13': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '4500 mAh', 'ekran': '6.36" FHD+ AMOLED 120Hz', 'kamera': '54MP+12MP+10MP', 'os': 'Android 13 (MIUI 14)'},
    'Xiaomi 13T Pro': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'MediaTek Dimensity 9200+', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '50MP+50MP+50MP', 'os': 'Android 13 (MIUI 14)'},
    'Xiaomi 13T': {'5g': True, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'MediaTek Dimensity 8200 Ultra', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '50MP+12MP+50MP', 'os': 'Android 13 (MIUI 14)'},
    'Xiaomi 12 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Aralık', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '4600 mAh', 'ekran': '6.73" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+50MP+50MP', 'os': 'Android 12 (MIUI 13)'},
    'Xiaomi 12': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Aralık', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '4500 mAh', 'ekran': '6.28" FHD+ AMOLED 120Hz', 'kamera': '50MP+13MP+5MP', 'os': 'Android 12 (MIUI 13)'},
    'Xiaomi 12T Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '200MP+8MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'Xiaomi 12T': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'MediaTek Dimensity 8100 Ultra', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '108MP+8MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'Xiaomi 11 Ultra': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Nisan', 'islemci': 'Snapdragon 888', 'batarya': '5000 mAh', 'ekran': '6.81" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+48MP+48MP', 'os': 'Android 11 (MIUI 12.5)'},
    'Xiaomi 11 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Nisan', 'islemci': 'Snapdragon 888', 'batarya': '5000 mAh', 'ekran': '6.81" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+48MP+48MP', 'os': 'Android 11 (MIUI 12.5)'},
    'Xiaomi 11': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2020 Aralık', 'islemci': 'Snapdragon 888', 'batarya': '4600 mAh', 'ekran': '6.81" QHD+ AMOLED 120Hz', 'kamera': '108MP+13MP+5MP', 'os': 'Android 11 (MIUI 12)'},
    'Xiaomi 11T Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Eylül', 'islemci': 'Snapdragon 888', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+8MP+5MP', 'os': 'Android 11 (MIUI 12.5)'},
    'Xiaomi 11T': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Eylül', 'islemci': 'MediaTek Dimensity 1200 Ultra', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+8MP+5MP', 'os': 'Android 11 (MIUI 12.5)'},
    'Redmi Note 13 Pro+ 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Dimensity 7200 Ultra', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '200MP+8MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'Redmi Note 13 Pro 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Snapdragon 7s Gen 2', 'batarya': '5100 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '200MP+8MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'Redmi Note 13 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+8MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'Redmi Note 13': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Snapdragon 685', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+8MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'Redmi Note 12 Pro+ 5G': {'5g': True, 'ram': '6/8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'MediaTek Dimensity 1080', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '200MP+8MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'Redmi Note 12 Pro 5G': {'5g': True, 'ram': '6/8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'MediaTek Dimensity 1080', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'Redmi Note 12 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'Snapdragon 4 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '48MP+8MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'Redmi Note 12': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'Snapdragon 685', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'Redmi Note 12s': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'MediaTek Helio G96', 'batarya': '5000 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '108MP+8MP+2MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'Redmi Note 11 Pro+ 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Ekim', 'islemci': 'MediaTek Dimensity 920', 'batarya': '4500 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+8MP+2MP+2MP', 'os': 'Android 11 (MIUI 12.5)'},
    'Redmi Note 11 Pro': {'5g': False, 'ram': '6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Ocak', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+8MP+2MP+2MP', 'os': 'Android 11 (MIUI 13)'},
    'Redmi Note 11S 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'MediaTek Dimensity 810', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 11 (MIUI 13)'},
    'Redmi Note 11S': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Şubat', 'islemci': 'MediaTek Helio G96', 'batarya': '5000 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '108MP+8MP+2MP+2MP', 'os': 'Android 11 (MIUI 13)'},
    'Redmi Note 11': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Ekim', 'islemci': 'Snapdragon 680 4G', 'batarya': '5000 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '50MP+8MP+2MP+2MP', 'os': 'Android 11 (MIUI 13)'},
    'Redmi Note 11 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Ekim', 'islemci': 'MediaTek Dimensity 810', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 11 (MIUI 13)'},
    'Redmi Note 10 Pro': {'5g': False, 'ram': '6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Mart', 'islemci': 'Snapdragon 732G', 'batarya': '5020 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+8MP+5MP+2MP', 'os': 'Android 11 (MIUI 12)'},
    'Redmi Note 10': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Mart', 'islemci': 'Snapdragon 678', 'batarya': '5000 mAh', 'ekran': '6.43" FHD+ AMOLED 60Hz', 'kamera': '48MP+8MP+2MP+2MP', 'os': 'Android 11 (MIUI 12)'},
    'Redmi Note 10s': {'5g': False, 'ram': '6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Nisan', 'islemci': 'MediaTek Helio G95', 'batarya': '5000 mAh', 'ekran': '6.43" FHD+ AMOLED 60Hz', 'kamera': '64MP+8MP+2MP+2MP', 'os': 'Android 11 (MIUI 12.5)'},
    'Redmi Note 10 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Mart', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ IPS LCD 90Hz', 'kamera': '48MP+8MP+2MP', 'os': 'Android 11 (MIUI 12)'},
    'Redmi 13C 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Aralık', 'islemci': 'MediaTek Dimensity 6100+', 'batarya': '5000 mAh', 'ekran': '6.74" HD+ IPS LCD 90Hz', 'kamera': '50MP+AI+AI', 'os': 'Android 13 (MIUI 14)'},
    'Redmi 13C': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2023 Kasım', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.74" HD+ IPS LCD 90Hz', 'kamera': '50MP+AI+AI', 'os': 'Android 13 (MIUI 14)'},
    'Redmi 13': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Haziran', 'islemci': 'MediaTek Helio G91 Ultra', 'batarya': '5030 mAh', 'ekran': '6.79" FHD+ IPS LCD 90Hz', 'kamera': '108MP+2MP+AI', 'os': 'Android 14 (HyperOS)'},
    'Redmi 12C': {'5g': False, 'ram': '3/4/6 GB', 'depolama': '32/64/128GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.71" HD+ IPS LCD 60Hz', 'kamera': '50MP+AI', 'os': 'Android 12 (MIUI 13)'},
    'Redmi 12': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'Snapdragon 4 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.79" FHD+ IPS LCD 90Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'Redmi 12 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'Snapdragon 4 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.79" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'Redmi 10C': {'5g': False, 'ram': '3/4/6 GB', 'depolama': '32/64/128GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'Snapdragon 680 4G', 'batarya': '5000 mAh', 'ekran': '6.71" HD+ IPS LCD 60Hz', 'kamera': '50MP+2MP', 'os': 'Android 11 (MIUI 13)'},
    'Redmi 10': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Ağustos', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ IPS LCD 90Hz', 'kamera': '50MP+8MP+2MP+2MP', 'os': 'Android 11 (MIUI 12.5)'},
    'Redmi 10A': {'5g': False, 'ram': '2/3/4 GB', 'depolama': '32/64/128GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'MediaTek Helio G25', 'batarya': '5000 mAh', 'ekran': '6.53" HD+ IPS LCD 60Hz', 'kamera': '13MP', 'os': 'Android 11 (MIUI 12.5)'},
    'Redmi A3': {'5g': False, 'ram': '3/4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'MediaTek Helio G36', 'batarya': '5000 mAh', 'ekran': '6.71" HD+ IPS LCD 90Hz', 'kamera': '8MP', 'os': 'Android 14 (HyperOS)'},
    'Redmi A2+': {'5g': False, 'ram': '2/3 GB', 'depolama': '32/64GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'MediaTek Helio G36', 'batarya': '5000 mAh', 'ekran': '6.52" HD+ IPS LCD 60Hz', 'kamera': '8MP', 'os': 'Android 12 (MIUI 13)'},
    'Redmi A2': {'5g': False, 'ram': '2/3 GB', 'depolama': '32/64GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'MediaTek Helio G36', 'batarya': '5000 mAh', 'ekran': '6.52" HD+ IPS LCD 60Hz', 'kamera': '8MP', 'os': 'Android 12 (MIUI 13)'},
    'Redmi A1+': {'5g': False, 'ram': '2/3 GB', 'depolama': '32/64GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'MediaTek Helio A22', 'batarya': '5000 mAh', 'ekran': '6.52" HD+ IPS LCD 60Hz', 'kamera': '8MP', 'os': 'Android 12'},
    'Xiaomi Pad 6 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 1, 'cikis': '2023 Mayıs', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '8600 mAh', 'ekran': '11" 2.8K IPS LCD 144Hz', 'kamera': '50MP+13MP', 'os': 'Android 13 (MIUI 14)'},
    'Xiaomi Pad 6': {'5g': True, 'ram': '6/8/12 GB', 'depolama': '128/256GB', 'sim': 1, 'cikis': '2023 Mayıs', 'islemci': 'Snapdragon 870', 'batarya': '8840 mAh', 'ekran': '11" 2.8K IPS LCD 144Hz', 'kamera': '50MP+13MP', 'os': 'Android 13 (MIUI 14)'},
    # ── POCO ──
    'POCO X6 Pro 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Dimensity 8300 Ultra', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 14 (MIUI 14)'},
    'POCO X6 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 7s Gen 2', 'batarya': '5100 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 14 (MIUI 14)'},
    'POCO X5 Pro 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'Snapdragon 778G', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+8MP+2MP', 'os': 'Android 12 (MIUI 14)'},
    'POCO X5 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '48MP+8MP+2MP', 'os': 'Android 12 (MIUI 14)'},
    'POCO X4 Pro 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+8MP+2MP', 'os': 'Android 11 (MIUI 13)'},
    'POCO X4 GT': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Temmuz', 'islemci': 'MediaTek Dimensity 8100', 'batarya': '5080 mAh', 'ekran': '6.6" FHD+ IPS LCD 144Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'POCO X3 Pro': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Mart', 'islemci': 'Snapdragon 860', 'batarya': '5160 mAh', 'ekran': '6.67" FHD+ IPS LCD 120Hz', 'kamera': '48MP+8MP+2MP+2MP', 'os': 'Android 11 (MIUI 12)'},
    'POCO X3 GT': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Temmuz', 'islemci': 'MediaTek Dimensity 1100', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 11 (MIUI 12.5)'},
    'POCO X3 NFC': {'5g': False, 'ram': '6/8 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2020 Eylül', 'islemci': 'Snapdragon 732G', 'batarya': '6000 mAh', 'ekran': '6.67" FHD+ IPS LCD 120Hz', 'kamera': '64MP+13MP+2MP+2MP', 'os': 'Android 10 (MIUI 12)'},
    'POCO X3': {'5g': False, 'ram': '6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2020 Eylül', 'islemci': 'Snapdragon 732G', 'batarya': '6000 mAh', 'ekran': '6.67" FHD+ IPS LCD 120Hz', 'kamera': '64MP+13MP+2MP+2MP', 'os': 'Android 10 (MIUI 12)'},
    'POCO F6 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.67" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 14 (HyperOS)'},
    'POCO F6 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'Snapdragon 8s Gen 3', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 14 (HyperOS)'},
    'POCO F5 Pro 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5160 mAh', 'ekran': '6.67" QHD+ LTPO AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'POCO F5 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'Snapdragon 7+ Gen 2', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'POCO F4 GT': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '4700 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'POCO F4 5G': {'5g': True, 'ram': '6/8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'Snapdragon 870', 'batarya': '4500 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'POCO F3': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Mart', 'islemci': 'Snapdragon 870', 'batarya': '4520 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '48MP+8MP+5MP', 'os': 'Android 11 (MIUI 12)'},
    'POCO F2 Pro': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2020 Mayıs', 'islemci': 'Snapdragon 865', 'batarya': '4700 mAh', 'ekran': '6.67" FHD+ AMOLED 60Hz', 'kamera': '64MP+5MP+13MP+2MP', 'os': 'Android 10 (MIUI 12)'},
    'POCO M6 Pro 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.79" FHD+ IPS LCD 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'POCO M6 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 6100+', 'batarya': '5000 mAh', 'ekran': '6.74" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13 (MIUI 14)'},
    'POCO M5s': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'MediaTek Helio G95', 'batarya': '5000 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '64MP+8MP+2MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'POCO M5': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.58" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'POCO M4 Pro 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2021 Kasım', 'islemci': 'MediaTek Dimensity 810', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ AMOLED 90Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 11 (MIUI 12.5)'},
    'POCO M4 Pro': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2022 Şubat', 'islemci': 'MediaTek Helio G96', 'batarya': '5000 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 11 (MIUI 13)'},
    'POCO M4 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.58" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 12 (MIUI 13)'},
    'POCO M3 Pro 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2021 Mayıs', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ IPS LCD 90Hz', 'kamera': '48MP+2MP+2MP', 'os': 'Android 11 (MIUI 12)'},
    'POCO C65': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.74" HD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13 (MIUI 14)'},
    'POCO C55': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.71" HD+ IPS LCD 60Hz', 'kamera': '50MP+AI', 'os': 'Android 12 (MIUI 13)'},
    'POCO C51': {'5g': False, 'ram': '2/4 GB', 'depolama': '64GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Helio G36', 'batarya': '5000 mAh', 'ekran': '6.52" HD+ IPS LCD 60Hz', 'kamera': '8MP+AI', 'os': 'Android 13 (MIUI 14)'},
    'POCO C40': {'5g': False, 'ram': '3/4/6 GB', 'depolama': '32/64GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'JLQ JR510', 'batarya': '6000 mAh', 'ekran': '6.71" HD+ IPS LCD 60Hz', 'kamera': '13MP+2MP', 'os': 'Android 11 (MIUI for POCO)'},
    # ── GOOGLE PİXEL ──
    'Pixel 9 Pro XL': {'5g': True, 'ram': '16 GB', 'depolama': '128/256/512/1TB', 'sim': 2, 'cikis': '2024 Ağustos', 'islemci': 'Google Tensor G4', 'batarya': '5060 mAh', 'ekran': '6.8" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+48MP+48MP', 'os': 'Android 14'},
    'Pixel 9 Pro': {'5g': True, 'ram': '16 GB', 'depolama': '128/256/512/1TB', 'sim': 2, 'cikis': '2024 Ağustos', 'islemci': 'Google Tensor G4', 'batarya': '4700 mAh', 'ekran': '6.3" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+48MP+48MP', 'os': 'Android 14'},
    'Pixel 9': {'5g': True, 'ram': '12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ağustos', 'islemci': 'Google Tensor G4', 'batarya': '4700 mAh', 'ekran': '6.3" FHD+ OLED 120Hz', 'kamera': '50MP+48MP', 'os': 'Android 14'},
    'Pixel 9 Pro Fold': {'5g': True, 'ram': '16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Ağustos', 'islemci': 'Google Tensor G4', 'batarya': '4650 mAh', 'ekran': '8.0" QHD+ LTPO OLED 120Hz', 'kamera': '48MP+10.5MP+10.8MP', 'os': 'Android 14'},
    'Pixel 8 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '128/256/1TB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'Google Tensor G3', 'batarya': '5050 mAh', 'ekran': '6.7" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+48MP+48MP', 'os': 'Android 14'},
    'Pixel 8': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'Google Tensor G3', 'batarya': '4575 mAh', 'ekran': '6.2" FHD+ OLED 120Hz', 'kamera': '50MP+12MP', 'os': 'Android 14'},
    'Pixel 8a': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'Google Tensor G3', 'batarya': '4492 mAh', 'ekran': '6.1" FHD+ OLED 120Hz', 'kamera': '64MP+13MP', 'os': 'Android 14'},
    'Pixel 7 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'Google Tensor G2', 'batarya': '5000 mAh', 'ekran': '6.7" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+48MP+12MP', 'os': 'Android 13→14'},
    'Pixel 7': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'Google Tensor G2', 'batarya': '4355 mAh', 'ekran': '6.3" FHD+ OLED 90Hz', 'kamera': '50MP+12MP', 'os': 'Android 13→14'},
    'Pixel 7a': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'Google Tensor G2', 'batarya': '4385 mAh', 'ekran': '6.1" FHD+ OLED 90Hz', 'kamera': '64MP+13MP', 'os': 'Android 13→14'},
    'Pixel 6 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2021 Ekim', 'islemci': 'Google Tensor', 'batarya': '5003 mAh', 'ekran': '6.7" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+48MP+12MP', 'os': 'Android 12→14'},
    'Pixel 6': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Ekim', 'islemci': 'Google Tensor', 'batarya': '4614 mAh', 'ekran': '6.4" FHD+ OLED 90Hz', 'kamera': '50MP+12MP', 'os': 'Android 12→14'},
    'Pixel 6a': {'5g': True, 'ram': '6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2022 Temmuz', 'islemci': 'Google Tensor', 'batarya': '4306 mAh', 'ekran': '6.1" FHD+ OLED 60Hz', 'kamera': '12MP+12MP', 'os': 'Android 12→14'},
    'Pixel 5': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2020 Ekim', 'islemci': 'Snapdragon 765G', 'batarya': '4080 mAh', 'ekran': '6" FHD+ OLED 90Hz', 'kamera': '12MP+16MP', 'os': 'Android 11→13'},
    'Pixel 5a 5G': {'5g': True, 'ram': '6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2021 Ağustos', 'islemci': 'Snapdragon 765G', 'batarya': '4680 mAh', 'ekran': '6.34" FHD+ OLED 60Hz', 'kamera': '12MP+16MP', 'os': 'Android 11→13'},
    'Pixel 4a 5G': {'5g': True, 'ram': '6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2020 Ekim', 'islemci': 'Snapdragon 765G', 'batarya': '3885 mAh', 'ekran': '6.2" FHD+ OLED 60Hz', 'kamera': '12MP+16MP', 'os': 'Android 11→12'},
    'Pixel 4a': {'5g': False, 'ram': '6 GB', 'depolama': '128GB', 'sim': 1, 'cikis': '2020 Ağustos', 'islemci': 'Snapdragon 730G', 'batarya': '3140 mAh', 'ekran': '5.81" FHD+ OLED 60Hz', 'kamera': '12MP', 'os': 'Android 10→12'},
    'Pixel 4 XL': {'5g': False, 'ram': '6 GB', 'depolama': '64/128GB', 'sim': 1, 'cikis': '2019 Ekim', 'islemci': 'Snapdragon 855', 'batarya': '3700 mAh', 'ekran': '6.3" QHD+ OLED 90Hz', 'kamera': '12MP+16MP', 'os': 'Android 10→12'},
    'Pixel 4': {'5g': False, 'ram': '6 GB', 'depolama': '64/128GB', 'sim': 1, 'cikis': '2019 Ekim', 'islemci': 'Snapdragon 855', 'batarya': '2800 mAh', 'ekran': '5.7" FHD+ OLED 90Hz', 'kamera': '12MP+16MP', 'os': 'Android 10→12'},
    # ── TECNO ──
    'Phantom V Fold 2 5G': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'MediaTek Dimensity 9000+', 'batarya': '5000 mAh', 'ekran': '8.0" FHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+13MP+10MP', 'os': 'Android 13 (HiOS 13)'},
    'Phantom V Flip 5G': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'MediaTek Dimensity 8050', 'batarya': '4000 mAh', 'ekran': '6.9" FHD+ AMOLED 120Hz', 'kamera': '64MP+13MP', 'os': 'Android 13 (HiOS 13)'},
    'Phantom X2 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'MediaTek Dimensity 9000', 'batarya': '5160 mAh', 'ekran': '6.8" FHD+ AMOLED 120Hz', 'kamera': '50MP+50MP+13MP', 'os': 'Android 12 (HiOS 12)'},
    'Phantom X2': {'5g': True, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'MediaTek Dimensity 9000', 'batarya': '5160 mAh', 'ekran': '6.8" FHD+ AMOLED 120Hz', 'kamera': '64MP+13MP+2MP', 'os': 'Android 12 (HiOS 12)'},
    'Phantom X': {'5g': False, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2021 Temmuz', 'islemci': 'MediaTek Helio G95', 'batarya': '4700 mAh', 'ekran': '6.7" FHD+ AMOLED 90Hz', 'kamera': '50MP+50MP+13MP', 'os': 'Android 11 (HiOS 7.6)'},
    'Camon 30 Premier 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 8200', 'batarya': '5000 mAh', 'ekran': '6.77" FHD+ AMOLED 144Hz', 'kamera': '50MP+50MP+2MP', 'os': 'Android 14 (HiOS 14)'},
    'Camon 30 Pro 5G': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 7020', 'batarya': '5000 mAh', 'ekran': '6.77" FHD+ AMOLED 120Hz', 'kamera': '50MP+50MP+2MP', 'os': 'Android 14 (HiOS 14)'},
    'Camon 30 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '50MP+AI+AI', 'os': 'Android 14 (HiOS 14)'},
    'Camon 30': {'5g': False, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Helio G91 Ultra', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '50MP+AI+AI', 'os': 'Android 14 (HiOS 14)'},
    'Camon 20 Premier 5G': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'MediaTek Dimensity 8050', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '50MP+50MP+2MP', 'os': 'Android 13 (HiOS 13)'},
    'Camon 20 Pro 5G': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'MediaTek Dimensity 8050', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '50MP+50MP+2MP', 'os': 'Android 13 (HiOS 13)'},
    'Camon 20 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '64MP+AI+AI', 'os': 'Android 13 (HiOS 13)'},
    'Camon 20': {'5g': False, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 60Hz', 'kamera': '64MP+AI+AI', 'os': 'Android 13 (HiOS 13)'},
    'Camon 19 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'MediaTek Helio G96', 'batarya': '5000 mAh', 'ekran': '6.8" FHD+ AMOLED 90Hz', 'kamera': '64MP+AI+AI', 'os': 'Android 12 (HiOS 12)'},
    'Camon 19': {'5g': False, 'ram': '4/6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.8" FHD+ IPS LCD 90Hz', 'kamera': '48MP+AI+AI', 'os': 'Android 12 (HiOS 12)'},
    'Spark 20 Pro+': {'5g': False, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G99 Ultimate', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 14 (HiOS 14)'},
    'Spark 20 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 14 (HiOS 14)'},
    'Spark 20C': {'5g': False, 'ram': '4/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.56" HD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13 (HiOS 14)'},
    'Spark 20': {'5g': False, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.56" HD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13 (HiOS 14)'},
    'Spark 10 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.8" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP+AI', 'os': 'Android 13 (HiOS 13)'},
    'Spark 10': {'5g': False, 'ram': '4/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.8" FHD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13 (HiOS 13)'},
    'Spark 10C': {'5g': False, 'ram': '4/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.6" HD+ IPS LCD 60Hz', 'kamera': '13MP+AI', 'os': 'Android 13 (HiOS 13)'},
    'Pova 6 Pro 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '6000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 14 (HiOS 14)'},
    'Pova 6 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '6000 mAh', 'ekran': '6.78" FHD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 14 (HiOS 14)'},
    'Pova 5 Pro': {'5g': False, 'ram': '8/16 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'MediaTek Helio G99', 'batarya': '6000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 13 (HiOS 13)'},
    'Pova 5': {'5g': False, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'MediaTek Helio G85', 'batarya': '6000 mAh', 'ekran': '6.78" FHD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13 (HiOS 13)'},
    'Spark Go 2024': {'5g': False, 'ram': '4/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio A22', 'batarya': '5000 mAh', 'ekran': '6.56" HD+ IPS LCD 60Hz', 'kamera': '8MP+AI', 'os': 'Android 13 (HiOS 13)'},
    'Spark Go 2023': {'5g': False, 'ram': '2/4 GB', 'depolama': '32/64GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'MediaTek Helio A22', 'batarya': '5000 mAh', 'ekran': '6.56" HD+ IPS LCD 60Hz', 'kamera': '8MP+AI', 'os': 'Android 12 (HiOS 12)'},
    # ── HONOR ──
    'Honor Magic6 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5600 mAh', 'ekran': '6.8" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+180MP+40MP', 'os': 'Android 14 (MagicOS 8.0)'},
    'Honor Magic6': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5450 mAh', 'ekran': '6.78" FHD+ OLED 120Hz', 'kamera': '50MP+50MP+32MP', 'os': 'Android 14 (MagicOS 8.0)'},
    'Honor Magic6 Lite': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Snapdragon 6 Gen 1', 'batarya': '5300 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '108MP+5MP+2MP', 'os': 'Android 13 (MagicOS 7.2)'},
    'Honor Magic5 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5100 mAh', 'ekran': '6.81" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+50MP+50MP', 'os': 'Android 13 (MagicOS 7.1)'},
    'Honor Magic5 Lite': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'Snapdragon 695 5G', 'batarya': '5100 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '64MP+5MP+2MP', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor 200 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'Snapdragon 8s Gen 3', 'batarya': '5200 mAh', 'ekran': '6.78" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+50MP+50MP', 'os': 'Android 14 (MagicOS 8.0)'},
    'Honor 200': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'Snapdragon 7s Gen 2', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ OLED 120Hz', 'kamera': '50MP+12MP+2MP', 'os': 'Android 14 (MagicOS 8.0)'},
    'Honor 200 Lite': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'Snapdragon 4 Gen 2', 'batarya': '4500 mAh', 'ekran': '6.7" FHD+ AMOLED 90Hz', 'kamera': '108MP+5MP+2MP', 'os': 'Android 14 (MagicOS 8.0)'},
    'Honor 90 GT': {'5g': True, 'ram': '16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Aralık', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 13 (MagicOS 7.2)'},
    'Honor 90 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '5000 mAh', 'ekran': '6.78" QHD+ LTPO OLED 120Hz', 'kamera': '200MP+12MP+32MP', 'os': 'Android 13 (MagicOS 7.1)'},
    'Honor 90': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 7 Gen 1 Accelerated', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ OLED 120Hz', 'kamera': '200MP+12MP+2MP', 'os': 'Android 13 (MagicOS 7.1)'},
    'Honor 90 Lite': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'MediaTek Dimensity 6020', 'batarya': '4500 mAh', 'ekran': '6.7" FHD+ IPS LCD 90Hz', 'kamera': '100MP+5MP+2MP', 'os': 'Android 13 (MagicOS 7.1)'},
    'Honor 80 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '4800 mAh', 'ekran': '6.78" FHD+ OLED 120Hz', 'kamera': '160MP+8MP+2MP', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor 80': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'Snapdragon 7 Gen 1', 'batarya': '4800 mAh', 'ekran': '6.67" FHD+ OLED 120Hz', 'kamera': '200MP+2MP+2MP', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor 80 Lite': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'MediaTek Dimensity 900', 'batarya': '4300 mAh', 'ekran': '6.7" FHD+ OLED 90Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor 80 SE': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'MediaTek Dimensity 900', 'batarya': '4500 mAh', 'ekran': '6.67" FHD+ OLED 90Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor X9b 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 6 Gen 1', 'batarya': '5800 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '108MP+5MP+2MP', 'os': 'Android 13 (MagicOS 7.2)'},
    'Honor X8b': {'5g': False, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 6s Gen 3', 'batarya': '4500 mAh', 'ekran': '6.7" FHD+ AMOLED 90Hz', 'kamera': '108MP+5MP+2MP', 'os': 'Android 13 (MagicOS 7.2)'},
    'Honor X7b': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 680 4G', 'batarya': '6000 mAh', 'ekran': '6.8" FHD+ IPS LCD 90Hz', 'kamera': '108MP+5MP+2MP', 'os': 'Android 13 (MagicOS 7.2)'},
    'Honor X6b': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'MediaTek Helio G88', 'batarya': '5200 mAh', 'ekran': '6.74" HD+ IPS LCD 90Hz', 'kamera': '108MP+2MP', 'os': 'Android 13 (MagicOS 7.2)'},
    'Honor X9a 5G': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'Snapdragon 695 5G', 'batarya': '5100 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor X8a': {'5g': False, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Helio G88', 'batarya': '4500 mAh', 'ekran': '6.7" FHD+ AMOLED 90Hz', 'kamera': '100MP+5MP+2MP', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor X7a': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Snapdragon 680 4G', 'batarya': '6000 mAh', 'ekran': '6.74" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor X6a': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Helio G25', 'batarya': '5200 mAh', 'ekran': '6.56" HD+ IPS LCD 60Hz', 'kamera': '50MP+2MP', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor X50 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'Snapdragon 6 Gen 1', 'batarya': '5800 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '108MP+5MP+2MP', 'os': 'Android 13 (MagicOS 7.1)'},
    'Honor X40 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'Snapdragon 695 5G', 'batarya': '5100 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor X30i': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Kasım', 'islemci': 'MediaTek Dimensity 810', 'batarya': '4300 mAh', 'ekran': '6.7" FHD+ OLED 90Hz', 'kamera': '64MP+5MP+2MP', 'os': 'Android 11 (MagicOS 6.0)'},
    'Honor X20': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Ağustos', 'islemci': 'MediaTek Dimensity 900', 'batarya': '4300 mAh', 'ekran': '6.67" FHD+ OLED 120Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 11 (MagicOS 6.0)'},
    'Honor Play 8T': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Helio G85', 'batarya': '6000 mAh', 'ekran': '6.8" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor Play 7T': {'5g': False, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'MediaTek Helio G25', 'batarya': '6000 mAh', 'ekran': '6.75" HD+ IPS LCD 90Hz', 'kamera': '48MP+AI', 'os': 'Android 12 (MagicOS 7.0)'},
    'Honor Pad 9': {'5g': False, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 1, 'cikis': '2023 Temmuz', 'islemci': 'Snapdragon 6 Gen 1', 'batarya': '8300 mAh', 'ekran': '12.1" 2.5K IPS LCD 120Hz', 'kamera': '13MP+AI', 'os': 'Android 13 (MagicOS 7.1)'},
    # ── CANE (bölgesel marka) ──
    'CANE P10 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Dimensity 7200', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '108MP+8MP+2MP', 'os': 'Android 14'},
    'CANE P10': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 14'},
    'CANE P8 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 90Hz', 'kamera': '64MP+5MP+2MP', 'os': 'Android 13'},
    'CANE P8': {'5g': False, 'ram': '6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ IPS LCD 90Hz', 'kamera': '50MP+5MP+2MP', 'os': 'Android 13'},
    'CANE X5 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 13'},
    'CANE X5': {'5g': False, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 680 4G', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+5MP+2MP', 'os': 'Android 13'},
    'CANE Note 10': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Helio G99', 'batarya': '5500 mAh', 'ekran': '6.9" FHD+ AMOLED 90Hz', 'kamera': '108MP+8MP+2MP', 'os': 'Android 13'},
    'CANE S6 Pro': {'5g': False, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'MediaTek Helio G96', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ AMOLED 90Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 12'},
    'CANE S6': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.5" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 12'},
    # ── HUAWEI ──
    'Huawei Mate 60 Pro+': {'5g': True, 'ram': '16 GB', 'depolama': '512/1TB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Kirin 9010', 'batarya': '5000 mAh', 'ekran': '6.82" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+48MP+40MP', 'os': 'HarmonyOS 4.0'},
    'Huawei Mate 60 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2023 Ağustos', 'islemci': 'Kirin 9010', 'batarya': '5000 mAh', 'ekran': '6.82" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+48MP+40MP', 'os': 'HarmonyOS 4.0'},
    'Huawei Mate 60': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Ağustos', 'islemci': 'Kirin 9010', 'batarya': '5000 mAh', 'ekran': '6.69" FHD+ OLED 120Hz', 'kamera': '50MP+12MP+40MP', 'os': 'HarmonyOS 4.0'},
    'Huawei Mate 60 RS': {'5g': True, 'ram': '16 GB', 'depolama': '512/1TB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Kirin 9010', 'batarya': '5000 mAh', 'ekran': '6.82" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+48MP+40MP', 'os': 'HarmonyOS 4.0'},
    'Huawei Mate 50 Pro': {'5g': False, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'SD 8+ Gen 1 (4G)', 'batarya': '4700 mAh', 'ekran': '6.74" QHD+ OLED 120Hz', 'kamera': '50MP+13MP+64MP', 'os': 'HarmonyOS 3.0'},
    'Huawei Mate 50': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'SD 8+ Gen 1 (4G)', 'batarya': '4460 mAh', 'ekran': '6.7" FHD+ OLED 90Hz', 'kamera': '50MP+12MP+13MP', 'os': 'HarmonyOS 3.0'},
    'Huawei Mate 50E': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'SD 778G (4G)', 'batarya': '4460 mAh', 'ekran': '6.7" FHD+ OLED 90Hz', 'kamera': '50MP+13MP+12MP', 'os': 'HarmonyOS 3.0'},
    'Huawei Mate 40 Pro+': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2020 Ekim', 'islemci': 'Kirin 9000', 'batarya': '4400 mAh', 'ekran': '6.76" QHD+ LTPO OLED 90Hz', 'kamera': '50MP+12MP+20MP+ToF', 'os': 'Android 10 (EMUI 11)'},
    'Huawei Mate 40 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2020 Ekim', 'islemci': 'Kirin 9000', 'batarya': '4400 mAh', 'ekran': '6.76" QHD+ LTPO OLED 90Hz', 'kamera': '50MP+12MP+20MP+ToF', 'os': 'Android 10 (EMUI 11)'},
    'Huawei Mate 40': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2020 Ekim', 'islemci': 'Kirin 9000E', 'batarya': '4200 mAh', 'ekran': '6.76" FHD+ OLED 90Hz', 'kamera': '50MP+16MP+8MP', 'os': 'Android 10 (EMUI 11)'},
    'Huawei P60 Pro': {'5g': False, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'SD 8+ Gen 1 (4G)', 'batarya': '5000 mAh', 'ekran': '6.67" QHD+ OLED 120Hz', 'kamera': '48MP+13MP+48MP', 'os': 'HarmonyOS 3.1'},
    'Huawei P60': {'5g': False, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'SD 8+ Gen 1 (4G)', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ OLED 120Hz', 'kamera': '48MP+13MP+12MP', 'os': 'HarmonyOS 3.1'},
    'Huawei P60 Art': {'5g': False, 'ram': '12 GB', 'depolama': '512GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'SD 8+ Gen 1 (4G)', 'batarya': '5000 mAh', 'ekran': '6.67" QHD+ OLED 120Hz', 'kamera': '48MP+13MP+48MP', 'os': 'HarmonyOS 3.1'},
    'Huawei P50 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Temmuz', 'islemci': 'Kirin 9000 (4G)', 'batarya': '4360 mAh', 'ekran': '6.6" QHD+ OLED 120Hz', 'kamera': '50MP+64MP+40MP+13MP', 'os': 'HarmonyOS 2.0'},
    'Huawei P50': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Temmuz', 'islemci': 'SD 888 (4G)', 'batarya': '4100 mAh', 'ekran': '6.5" FHD+ OLED 90Hz', 'kamera': '50MP+12MP+13MP', 'os': 'HarmonyOS 2.0'},
    'Huawei P50 Pocket': {'5g': False, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2021 Aralık', 'islemci': 'SD 888 (4G)', 'batarya': '4000 mAh', 'ekran': '6.9" FHD+ OLED 120Hz', 'kamera': '40MP+13MP+32MP', 'os': 'HarmonyOS 2.0'},
    'Huawei P40 Pro+': {'5g': True, 'ram': '8 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2020 Nisan', 'islemci': 'Kirin 990 5G', 'batarya': '4200 mAh', 'ekran': '6.58" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+40MP+12MP+ToF', 'os': 'Android 10 (EMUI 10.1)'},
    'Huawei P40 Pro': {'5g': True, 'ram': '8 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2020 Mart', 'islemci': 'Kirin 990 5G', 'batarya': '4200 mAh', 'ekran': '6.58" QHD+ LTPO OLED 90Hz', 'kamera': '50MP+40MP+12MP+ToF', 'os': 'Android 10 (EMUI 10.1)'},
    'Huawei P40': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2020 Mart', 'islemci': 'Kirin 990 5G', 'batarya': '3800 mAh', 'ekran': '6.1" FHD+ OLED 60Hz', 'kamera': '50MP+16MP+8MP', 'os': 'Android 10 (EMUI 10.1)'},
    'Huawei P40 Lite': {'5g': False, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2020 Şubat', 'islemci': 'Kirin 810', 'batarya': '4200 mAh', 'ekran': '6.4" FHD+ IPS LCD 60Hz', 'kamera': '48MP+8MP+2MP+2MP', 'os': 'Android 10 (EMUI 10.0)'},
    'Huawei P30 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2019 Mart', 'islemci': 'Kirin 980', 'batarya': '4200 mAh', 'ekran': '6.47" FHD+ OLED 60Hz', 'kamera': '40MP+20MP+8MP+ToF', 'os': 'Android 9 (EMUI 9.1)'},
    'Huawei P30': {'5g': False, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2019 Mart', 'islemci': 'Kirin 980', 'batarya': '3650 mAh', 'ekran': '6.1" FHD+ OLED 60Hz', 'kamera': '40MP+16MP+8MP', 'os': 'Android 9 (EMUI 9.1)'},
    'Huawei P30 Lite': {'5g': False, 'ram': '4/6 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2019 Mart', 'islemci': 'Kirin 710', 'batarya': '3340 mAh', 'ekran': '6.15" FHD+ IPS LCD 60Hz', 'kamera': '24MP+8MP+2MP', 'os': 'Android 9 (EMUI 9.0)'},
    'Huawei Nova 12 Pro': {'5g': False, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Kirin 8000E', 'batarya': '4600 mAh', 'ekran': '6.76" FHD+ OLED 120Hz', 'kamera': '50MP+8MP', 'os': 'HarmonyOS 4.0'},
    'Huawei Nova 12': {'5g': False, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Kirin 8000', 'batarya': '4500 mAh', 'ekran': '6.88" FHD+ OLED 120Hz', 'kamera': '50MP+8MP', 'os': 'HarmonyOS 4.0'},
    'Huawei Nova 11 Pro': {'5g': False, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'SD 778G (4G)', 'batarya': '4500 mAh', 'ekran': '6.78" FHD+ OLED 120Hz', 'kamera': '100MP+8MP', 'os': 'HarmonyOS 3.1'},
    'Huawei Nova 11': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'SD 778G (4G)', 'batarya': '4500 mAh', 'ekran': '6.7" FHD+ OLED 90Hz', 'kamera': '50MP+2MP', 'os': 'HarmonyOS 3.1'},
    'Huawei Nova 10 Pro': {'5g': False, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Temmuz', 'islemci': 'SD 778G (4G)', 'batarya': '4500 mAh', 'ekran': '6.78" FHD+ OLED 120Hz', 'kamera': '100MP+8MP', 'os': 'HarmonyOS 3.0'},
    'Huawei Nova 10': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Temmuz', 'islemci': 'SD 778G (4G)', 'batarya': '4000 mAh', 'ekran': '6.67" FHD+ OLED 90Hz', 'kamera': '50MP+8MP', 'os': 'HarmonyOS 3.0'},
    'Huawei Nova 9': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Ekim', 'islemci': 'SD 778G (4G)', 'batarya': '4300 mAh', 'ekran': '6.57" FHD+ OLED 120Hz', 'kamera': '50MP+8MP+2MP+2MP', 'os': 'HarmonyOS 2.0'},
    'Huawei Nova 9 SE': {'5g': False, 'ram': '6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Ocak', 'islemci': 'SD 680 (4G)', 'batarya': '4000 mAh', 'ekran': '6.78" FHD+ IPS LCD 90Hz', 'kamera': '108MP+8MP+2MP+2MP', 'os': 'HarmonyOS 2.0'},
    'Huawei Y9s': {'5g': False, 'ram': '6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2019 Ekim', 'islemci': 'Kirin 710F', 'batarya': '4000 mAh', 'ekran': '6.59" FHD+ IPS LCD 60Hz', 'kamera': '48MP+8MP+2MP', 'os': 'Android 9 (EMUI 9.1)'},
    'Huawei Y9a': {'5g': False, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2020 Ağustos', 'islemci': 'Kirin 800', 'batarya': '4300 mAh', 'ekran': '6.63" FHD+ IPS LCD 90Hz', 'kamera': '64MP+8MP+2MP+2MP', 'os': 'Android 10 (EMUI 10.1)'},
    'Huawei Y7a': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2020 Kasım', 'islemci': 'Kirin 710A', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ IPS LCD 60Hz', 'kamera': '48MP+8MP+2MP+2MP', 'os': 'Android 10 (EMUI 10.1)'},
    'Huawei Y6p': {'5g': False, 'ram': '3/4 GB', 'depolama': '64GB', 'sim': 2, 'cikis': '2020 Mayıs', 'islemci': 'MediaTek Helio P22', 'batarya': '5000 mAh', 'ekran': '6.3" HD+ IPS LCD 60Hz', 'kamera': '13MP+5MP+2MP', 'os': 'Android 10 (EMUI 10.0)'},
    'Huawei Pocket 2': {'5g': False, 'ram': '12 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Kirin 9010', 'batarya': '4000 mAh', 'ekran': '6.94" FHD+ OLED 120Hz', 'kamera': '50MP+40MP+12MP', 'os': 'HarmonyOS 4.2'},
    'Huawei Pocket S': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'SD 778G (4G)', 'batarya': '4000 mAh', 'ekran': '6.9" FHD+ OLED 120Hz', 'kamera': '40MP+12MP+10MP', 'os': 'HarmonyOS 3.0'},
    # ── LOVEIR (bölgesel marka) ──
    'LOVEIR X1 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Dimensity 7200', 'batarya': '5100 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 13'},
    'LOVEIR X1': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 90Hz', 'kamera': '50MP+5MP+2MP', 'os': 'Android 13'},
    'LOVEIR V10 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 90Hz', 'kamera': '64MP+5MP+2MP', 'os': 'Android 13'},
    'LOVEIR V10': {'5g': False, 'ram': '6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ IPS LCD 90Hz', 'kamera': '50MP+5MP+2MP', 'os': 'Android 13'},
    'LOVEIR Note 8 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Helio G96', 'batarya': '5500 mAh', 'ekran': '6.8" FHD+ AMOLED 90Hz', 'kamera': '108MP+8MP+2MP', 'os': 'Android 12'},
    'LOVEIR Note 8': {'5g': False, 'ram': '6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Helio G88', 'batarya': '5500 mAh', 'ekran': '6.8" FHD+ IPS LCD 90Hz', 'kamera': '64MP+5MP+2MP', 'os': 'Android 12'},
    'LOVEIR S7': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ IPS LCD 60Hz', 'kamera': '50MP+2MP', 'os': 'Android 12'},
    # ── OPPO / REALME ──
    'OPPO Find X7 Ultra': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5000 mAh', 'ekran': '6.82" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+50MP+50MP+50MP', 'os': 'Android 14 (ColorOS 14)'},
    'OPPO Find X7 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Aralık', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5000 mAh', 'ekran': '6.78" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+50MP+64MP', 'os': 'Android 14 (ColorOS 14)'},
    'OPPO Find X7': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Aralık', 'islemci': 'MediaTek Dimensity 9300', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ OLED 120Hz', 'kamera': '50MP+64MP+50MP', 'os': 'Android 14 (ColorOS 14)'},
    'OPPO Find X6 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.82" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+50MP+48MP', 'os': 'Android 13 (ColorOS 13)'},
    'OPPO Find X5 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.7" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+50MP+13MP', 'os': 'Android 12 (ColorOS 12)'},
    'OPPO Find X5': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'Snapdragon 888', 'batarya': '4800 mAh', 'ekran': '6.55" FHD+ AMOLED 120Hz', 'kamera': '50MP+50MP+13MP', 'os': 'Android 12 (ColorOS 12)'},
    'OPPO Reno 12 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'MediaTek Dimensity 9200+', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+50MP', 'os': 'Android 14 (ColorOS 14.1)'},
    'OPPO Reno 12': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'MediaTek Dimensity 7300 Energy', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+AI', 'os': 'Android 14 (ColorOS 14.1)'},
    'OPPO Reno 11 Pro 5G': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'MediaTek Dimensity 8200', 'batarya': '4600 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+32MP+64MP', 'os': 'Android 14 (ColorOS 14)'},
    'OPPO Reno 11': {'5g': True, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+AI', 'os': 'Android 14 (ColorOS 14)'},
    'OPPO Reno 10 Pro+ 5G': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '4700 mAh', 'ekran': '6.74" FHD+ AMOLED 120Hz', 'kamera': '50MP+64MP+32MP', 'os': 'Android 13 (ColorOS 13.1)'},
    'OPPO Reno 10 Pro 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 778G', 'batarya': '4600 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+32MP+8MP', 'os': 'Android 13 (ColorOS 13.1)'},
    'OPPO Reno 10 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 778G', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 13 (ColorOS 13.1)'},
    'OPPO Reno 9 Pro+': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '4700 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (ColorOS 13)'},
    'OPPO Reno 9': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'SD 778G (4G)', 'batarya': '4500 mAh', 'ekran': '6.7" FHD+ OLED 90Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 13 (ColorOS 13)'},
    'OPPO Reno 8 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'MediaTek Dimensity 8100 Max', 'batarya': '4500 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 12 (ColorOS 12.1)'},
    'OPPO Reno 8': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'Snapdragon 695 5G', 'batarya': '4500 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 12 (ColorOS 12.1)'},
    'OPPO A79 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Dimensity 6020', 'batarya': '5000 mAh', 'ekran': '6.72" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13 (ColorOS 13.1)'},
    'OPPO A78 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.56" FHD+ AMOLED 120Hz', 'kamera': '50MP+2MP', 'os': 'Android 13 (ColorOS 13.1)'},
    'OPPO A58 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.72" FHD+ IPS LCD 90Hz', 'kamera': '64MP+2MP', 'os': 'Android 13 (ColorOS 13)'},
    'OPPO A38': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.56" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13 (ColorOS 13)'},
    'OPPO A18': {'5g': False, 'ram': '4 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.56" HD+ IPS LCD 90Hz', 'kamera': '13MP+AI', 'os': 'Android 13 (ColorOS 13)'},
    'Realme GT 6 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2024 Haziran', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5500 mAh', 'ekran': '6.78" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+8MP+64MP', 'os': 'Android 14 (Realme UI 5.0)'},
    'Realme GT 6': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Haziran', 'islemci': 'Snapdragon 8s Gen 3', 'batarya': '5500 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 14 (Realme UI 5.0)'},
    'Realme GT 5 Pro': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '128/256/512GB/1TB', 'sim': 2, 'cikis': '2023 Aralık', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5400 mAh', 'ekran': '6.78" QHD+ LTPO AMOLED 144Hz', 'kamera': '50MP+8MP+50MP', 'os': 'Android 14 (Realme UI 5.0)'},
    'Realme GT 5': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2023 Ağustos', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5240 mAh', 'ekran': '6.74" FHD+ AMOLED 144Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (Realme UI 4.0)'},
    'Realme GT 2 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ocak', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.7" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+50MP+2MP', 'os': 'Android 12 (Realme UI 3.0)'},
    'Realme GT 2': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ocak', 'islemci': 'Snapdragon 888', 'batarya': '5000 mAh', 'ekran': '6.62" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 12 (Realme UI 3.0)'},
    'Realme GT Master Edition': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Ağustos', 'islemci': 'Snapdragon 778G', 'batarya': '4300 mAh', 'ekran': '6.43" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 11 (Realme UI 2.0)'},
    'Realme 12 Pro+': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Snapdragon 7s Gen 2', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+64MP+8MP', 'os': 'Android 14 (Realme UI 5.0)'},
    'Realme 12 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Snapdragon 6 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+32MP+8MP', 'os': 'Android 14 (Realme UI 5.0)'},
    'Realme 12+': {'5g': True, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Haziran', 'islemci': 'MediaTek Dimensity 7050', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 14 (Realme UI 5.0)'},
    'Realme 12': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.72" FHD+ AMOLED 120Hz', 'kamera': '108MP+2MP+2MP', 'os': 'Android 14 (Realme UI 5.0)'},
    'Realme 11 Pro+ 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Dimensity 7050', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '200MP+8MP+2MP', 'os': 'Android 13 (Realme UI 4.0)'},
    'Realme 11 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Dimensity 7050', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '100MP+2MP+2MP', 'os': 'Android 13 (Realme UI 4.0)'},
    'Realme 11': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.72" FHD+ AMOLED 90Hz', 'kamera': '108MP+2MP', 'os': 'Android 13 (Realme UI 4.0)'},
    'Realme C65 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 6100+', 'batarya': '5000 mAh', 'ekran': '6.67" HD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 14 (Realme UI 5.0)'},
    'Realme C55': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.72" FHD+ IPS LCD 90Hz', 'kamera': '64MP+2MP', 'os': 'Android 13 (Realme UI 4.0)'},
    'Realme C53': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 680', 'batarya': '5000 mAh', 'ekran': '6.74" FHD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13 (Realme UI 4.0)'},
    'Realme C51': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.74" HD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13 (Realme UI 4.0)'},
    'Realme C35': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Şubat', 'islemci': 'Unisoc T616', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 60Hz', 'kamera': '50MP+2MP+0.3MP', 'os': 'Android 11 (Realme UI R)'},
    'Realme Narzo 70 Pro': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 7050', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '50MP+AI', 'os': 'Android 14 (Realme UI 5.0)'},
    'Realme Narzo 60 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '100MP+AI', 'os': 'Android 13 (Realme UI 4.0)'},
    'Realme Narzo 50': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'MediaTek Helio G96', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 120Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 11 (Realme UI 2.0)'},
    # ── İNFİNİX ──
    'Infinix Zero 40 5G': {'5g': True, 'ram': '12/16 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Ağustos', 'islemci': 'MediaTek Dimensity 8350', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 144Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 14 (XOS 14)'},
    'Infinix Zero 40': {'5g': False, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Ağustos', 'islemci': 'MediaTek Helio G100 Ultra', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 144Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 14 (XOS 14)'},
    'Infinix Zero 30 5G': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'MediaTek Dimensity 8020', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 144Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Zero 30': {'5g': False, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'MediaTek Helio G99 Ultimate', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 144Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Zero 20': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'MediaTek Helio G99', 'batarya': '4500 mAh', 'ekran': '6.7" FHD+ AMOLED 60Hz', 'kamera': '60MP+13MP+AI', 'os': 'Android 12 (XOS 12)'},
    'Infinix Note 40 Pro+ 5G': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Nisan', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '4600 mAh', 'ekran': '6.78" FHD+ AMOLED 144Hz', 'kamera': '108MP+2MP+AI', 'os': 'Android 14 (XOS 14)'},
    'Infinix Note 40 Pro 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Nisan', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '4600 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '108MP+2MP+AI', 'os': 'Android 14 (XOS 14)'},
    'Infinix Note 40 Pro': {'5g': False, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Nisan', 'islemci': 'MediaTek Helio G99 Ultimate', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '108MP+2MP+AI', 'os': 'Android 14 (XOS 14)'},
    'Infinix Note 40': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Nisan', 'islemci': 'MediaTek Helio G99 Ultra', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 14 (XOS 14)'},
    'Infinix Note 30 Pro 5G': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+2MP+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Note 30 VIP': {'5g': False, 'ram': '8/16 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '108MP+2MP+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Note 30 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ IPS LCD 120Hz', 'kamera': '64MP+2MP+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Note 30': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ IPS LCD 90Hz', 'kamera': '64MP+2MP+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Note 12 Pro+': {'5g': False, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '108MP+13MP+2MP', 'os': 'Android 12 (XOS 12)'},
    'Infinix Note 12 Pro': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'MediaTek Helio G96', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 60Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 12 (XOS 12)'},
    'Infinix Note 12 G96': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'MediaTek Helio G96', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+AI+AI', 'os': 'Android 12 (XOS 12)'},
    'Infinix Note 12 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Ağustos', 'islemci': 'MediaTek Dimensity 810', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP+AI', 'os': 'Android 12 (XOS 12)'},
    'Infinix Hot 40 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ IPS LCD 120Hz', 'kamera': '108MP+AI+AI', 'os': 'Android 14 (XOS 14)'},
    'Infinix Hot 40': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ IPS LCD 90Hz', 'kamera': '50MP+AI+AI', 'os': 'Android 14 (XOS 14)'},
    'Infinix Hot 40i': {'5g': False, 'ram': '4/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.56" HD+ IPS LCD 90Hz', 'kamera': '13MP+AI', 'os': 'Android 14 (XOS 14)'},
    'Infinix Hot 30 Play': {'5g': False, 'ram': '4/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'MediaTek Helio G37', 'batarya': '6000 mAh', 'ekran': '6.82" HD+ IPS LCD 90Hz', 'kamera': '13MP+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Hot 30 5G': {'5g': True, 'ram': '4/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'MediaTek Dimensity 6020', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Hot 30': {'5g': False, 'ram': '4/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Hot 20 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'MediaTek Helio G96', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 120Hz', 'kamera': '64MP+AI+AI', 'os': 'Android 12 (XOS 12)'},
    'Infinix Hot 20': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+AI+AI', 'os': 'Android 12 (XOS 12)'},
    'Infinix GT 20 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Nisan', 'islemci': 'MediaTek Dimensity 8200', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '108MP+2MP+AI', 'os': 'Android 14 (XOS 14)'},
    'Infinix GT 10 Pro': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Ağustos', 'islemci': 'MediaTek Dimensity 8050', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '108MP+2MP+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Smart 8 Plus': {'5g': False, 'ram': '4 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G36', 'batarya': '5000 mAh', 'ekran': '6.78" HD+ IPS LCD 90Hz', 'kamera': '13MP+AI', 'os': 'Android 13 (XOS 13)'},
    'Infinix Smart 8': {'5g': False, 'ram': '3/4 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G36', 'batarya': '5000 mAh', 'ekran': '6.6" HD+ IPS LCD 60Hz', 'kamera': '13MP+AI', 'os': 'Android 13 (XOS 13)'},
    # ── ONEPLUS ──
    'OnePlus 12R': {'5g': True, 'ram': '8/16 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5500 mAh', 'ekran': '6.78" FHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 14 (OxygenOS 14)'},
    'OnePlus 12': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5400 mAh', 'ekran': '6.82" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+48MP+64MP', 'os': 'Android 14 (OxygenOS 14)'},
    'OnePlus 11R': {'5g': True, 'ram': '8/16 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '5000 mAh', 'ekran': '6.74" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (OxygenOS 13)'},
    'OnePlus 11 5G': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.7" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+48MP+32MP', 'os': 'Android 13 (OxygenOS 13)'},
    'OnePlus 10 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ocak', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.7" QHD+ LTPO AMOLED 120Hz', 'kamera': '48MP+50MP+8MP', 'os': 'Android 12 (OxygenOS 12)'},
    'OnePlus 10T 5G': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ağustos', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '4800 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 12 (OxygenOS 12.1)'},
    'OnePlus 10R': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'MediaTek Dimensity 8100 Max', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 12 (OxygenOS 12)'},
    'OnePlus 9 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Mart', 'islemci': 'Snapdragon 888', 'batarya': '4500 mAh', 'ekran': '6.7" QHD+ LTPO AMOLED 120Hz', 'kamera': '48MP+50MP+8MP+2MP', 'os': 'Android 11 (OxygenOS 11)'},
    'OnePlus 9': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Mart', 'islemci': 'Snapdragon 888', 'batarya': '4500 mAh', 'ekran': '6.55" FHD+ AMOLED 120Hz', 'kamera': '48MP+50MP+2MP', 'os': 'Android 11 (OxygenOS 11)'},
    'OnePlus 9R': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Nisan', 'islemci': 'Snapdragon 870', 'batarya': '4500 mAh', 'ekran': '6.55" FHD+ AMOLED 120Hz', 'kamera': '48MP+16MP+5MP+2MP', 'os': 'Android 11 (OxygenOS 11)'},
    'OnePlus 8 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2020 Nisan', 'islemci': 'Snapdragon 865', 'batarya': '4510 mAh', 'ekran': '6.78" QHD+ LTPO AMOLED 120Hz', 'kamera': '48MP+48MP+8MP+5MP', 'os': 'Android 10 (OxygenOS 10)'},
    'OnePlus 8T': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2020 Ekim', 'islemci': 'Snapdragon 865', 'batarya': '4500 mAh', 'ekran': '6.55" FHD+ AMOLED 120Hz', 'kamera': '48MP+16MP+5MP+2MP', 'os': 'Android 11 (OxygenOS 11)'},
    'OnePlus 8': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2020 Nisan', 'islemci': 'Snapdragon 865', 'batarya': '4300 mAh', 'ekran': '6.55" FHD+ AMOLED 90Hz', 'kamera': '48MP+16MP+2MP', 'os': 'Android 10 (OxygenOS 10)'},
    'OnePlus Open': {'5g': True, 'ram': '16 GB', 'depolama': '512GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '4805 mAh', 'ekran': '7.82" QHD+ LTPO AMOLED 120Hz', 'kamera': '48MP+48MP+64MP', 'os': 'Android 13 (OxygenOS 13.2)'},
    'OnePlus Nord 4 5G': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2024 Temmuz', 'islemci': 'Snapdragon 7+ Gen 3', 'batarya': '5500 mAh', 'ekran': '6.74" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP', 'os': 'Android 14 (OxygenOS 14.1)'},
    'OnePlus Nord 3 5G': {'5g': True, 'ram': '8/16 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'MediaTek Dimensity 9000', 'batarya': '5000 mAh', 'ekran': '6.74" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (OxygenOS 13.1)'},
    'OnePlus Nord 2T 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Mayıs', 'islemci': 'MediaTek Dimensity 1300', 'batarya': '4500 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 12 (OxygenOS 12.1)'},
    'OnePlus Nord 2 5G': {'5g': True, 'ram': '6/8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Temmuz', 'islemci': 'MediaTek Dimensity 1200 AI', 'batarya': '4500 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 11 (OxygenOS 11.3)'},
    'OnePlus Nord CE 4': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Nisan', 'islemci': 'Snapdragon 7 Gen 3', 'batarya': '5500 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 14 (OxygenOS 14.1)'},
    'OnePlus Nord CE 3 Lite 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.72" FHD+ IPS LCD 120Hz', 'kamera': '108MP+2MP+2MP', 'os': 'Android 13 (OxygenOS 13.1)'},
    'OnePlus Nord CE 3 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Snapdragon 782G', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (OxygenOS 13.1)'},
    'OnePlus Nord CE 2 Lite 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.59" FHD+ IPS LCD 120Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 12 (OxygenOS 12.1)'},
    'OnePlus Nord CE 2 5G': {'5g': True, 'ram': '6/8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Şubat', 'islemci': 'MediaTek Dimensity 900', 'batarya': '4500 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 11 (OxygenOS 12)'},
    'OnePlus Nord N30 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.72" FHD+ IPS LCD 120Hz', 'kamera': '108MP+2MP+2MP', 'os': 'Android 13 (OxygenOS 13.1)'},
    'OnePlus Nord N20 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'Snapdragon 695 5G', 'batarya': '4500 mAh', 'ekran': '6.49" FHD+ AMOLED 60Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 12 (OxygenOS 12.1)'},
    # ── VİVO ──
    'Vivo X100 Ultra': {'5g': True, 'ram': '16 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5500 mAh', 'ekran': '6.82" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+200MP+50MP', 'os': 'Android 14 (OriginOS 4)'},
    'Vivo X100 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Kasım', 'islemci': 'MediaTek Dimensity 9300', 'batarya': '5400 mAh', 'ekran': '6.78" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+50MP+64MP', 'os': 'Android 14 (OriginOS 4)'},
    'Vivo X100+': {'5g': True, 'ram': '16 GB', 'depolama': '512/1TB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '6000 mAh', 'ekran': '6.78" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+50MP+100MP', 'os': 'Android 14 (OriginOS 4)'},
    'Vivo X100': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Kasım', 'islemci': 'MediaTek Dimensity 9300', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '50MP+50MP+64MP', 'os': 'Android 14 (OriginOS 4)'},
    'Vivo X90 Pro+': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '4700 mAh', 'ekran': '6.78" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+50MP+64MP', 'os': 'Android 13 (OriginOS 3)'},
    'Vivo X90 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'MediaTek Dimensity 9200', 'batarya': '4870 mAh', 'ekran': '6.78" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+50MP+12MP', 'os': 'Android 13 (OriginOS 3)'},
    'Vivo X90': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'MediaTek Dimensity 9200', 'batarya': '4810 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '54MP+13MP+12MP', 'os': 'Android 13 (OriginOS 3)'},
    'Vivo X80 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '4700 mAh', 'ekran': '6.78" QHD+ LTPO AMOLED 120Hz', 'kamera': '50MP+48MP+8MP+12MP', 'os': 'Android 12 (OriginOS Ocean)'},
    'Vivo X80': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'MediaTek Dimensity 9000', 'batarya': '4500 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '50MP+12MP+12MP', 'os': 'Android 12 (OriginOS Ocean)'},
    'Vivo V30 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Snapdragon 7 Gen 3', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '50MP+50MP+8MP', 'os': 'Android 14 (Funtouch OS 14)'},
    'Vivo V30': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Snapdragon 7 Gen 3', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '50MP+50MP+8MP', 'os': 'Android 14 (Funtouch OS 14)'},
    'Vivo V29 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Snapdragon 778G', 'batarya': '4600 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '50MP+50MP+8MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo V29': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Snapdragon 778G', 'batarya': '4600 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo V27 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Dimensity 8200', 'batarya': '4600 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo V27': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Dimensity 7200', 'batarya': '4600 mAh', 'ekran': '6.74" FHD+ AMOLED 90Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo V25 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ağustos', 'islemci': 'MediaTek Dimensity 1300', 'batarya': '4830 mAh', 'ekran': '6.56" FHD+ AMOLED 90Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 12 (Funtouch OS 12)'},
    'Vivo V25': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ağustos', 'islemci': 'MediaTek Dimensity 900', 'batarya': '4500 mAh', 'ekran': '6.44" FHD+ AMOLED 90Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 12 (Funtouch OS 12)'},
    'Vivo Y200 Pro 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Snapdragon 7 Gen 3', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 14 (Funtouch OS 14)'},
    'Vivo Y200 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'Snapdragon 4 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 120Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 14 (Funtouch OS 14)'},
    'Vivo Y100 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 60Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo Y100': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'Snapdragon 695', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 60Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo Y78 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'Snapdragon 695 5G', 'batarya': '4600 mAh', 'ekran': '6.64" FHD+ AMOLED 120Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo Y78+': {'5g': True, 'ram': '8/16 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Snapdragon 695 5G', 'batarya': '4800 mAh', 'ekran': '6.64" FHD+ AMOLED 120Hz', 'kamera': '64MP+2MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo Y56 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.58" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo Y36 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Snapdragon 4 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.64" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo Y36': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Snapdragon 680', 'batarya': '5000 mAh', 'ekran': '6.64" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo Y27s': {'5g': False, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.64" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo Y27 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'MediaTek Dimensity 6020', 'batarya': '5000 mAh', 'ekran': '6.64" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13 (Funtouch OS 13)'},
    'Vivo Y17s': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.67" HD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13 (Funtouch OS 13)'},
    # ── ASD (bölgesel marka) ──
    'ASD X9 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Dimensity 7200', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 14'},
    'ASD X9': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 90Hz', 'kamera': '50MP+5MP+2MP', 'os': 'Android 14'},
    'ASD X7 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 90Hz', 'kamera': '64MP+5MP+2MP', 'os': 'Android 13'},
    'ASD Note 12 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Helio G96', 'batarya': '5500 mAh', 'ekran': '6.9" FHD+ AMOLED 90Hz', 'kamera': '108MP+5MP+2MP', 'os': 'Android 12'},
    'ASD Note 12': {'5g': False, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Helio G88', 'batarya': '5500 mAh', 'ekran': '6.9" FHD+ IPS LCD 90Hz', 'kamera': '64MP+5MP+2MP', 'os': 'Android 12'},
    'ASD P9 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'MediaTek Helio G99', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ AMOLED 90Hz', 'kamera': '64MP+5MP+2MP', 'os': 'Android 12'},
    'ASD P7': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.6" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 11'},
    'ASD S8': {'5g': False, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'MediaTek Helio G96', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ AMOLED 90Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 12'},
    'ASD S6': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Ocak', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.5" HD+ IPS LCD 60Hz', 'kamera': '50MP+2MP', 'os': 'Android 11'},
    # ── NOKİA / MOTOROLA ──
    'Nokia G42 5G': {'5g': True, 'ram': '6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'Snapdragon 480+ 5G', 'batarya': '5000 mAh', 'ekran': '6.56" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 13'},
    'Nokia G60 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'Snapdragon 695 5G', 'batarya': '4500 mAh', 'ekran': '6.58" FHD+ IPS LCD 120Hz', 'kamera': '50MP+5MP+2MP', 'os': 'Android 12'},
    'Nokia G400 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'Snapdragon 480+ 5G', 'batarya': '5000 mAh', 'ekran': '6.58" FHD+ IPS LCD 120Hz', 'kamera': '48MP+5MP+2MP', 'os': 'Android 11'},
    'Nokia G310 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Ağustos', 'islemci': 'Snapdragon 480+ 5G', 'batarya': '5000 mAh', 'ekran': '6.56" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13'},
    'Nokia X30 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'Snapdragon 695 5G', 'batarya': '4200 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '50MP+13MP', 'os': 'Android 12'},
    'Nokia XR21': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'Snapdragon 695 5G', 'batarya': '4800 mAh', 'ekran': '6.49" FHD+ IPS LCD 90Hz', 'kamera': '64MP+13MP', 'os': 'Android 12'},
    'Nokia C32': {'5g': False, 'ram': '3/4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Unisoc SC9863A1', 'batarya': '5000 mAh', 'ekran': '6.52" HD+ IPS LCD 60Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 12'},
    'Nokia C22': {'5g': False, 'ram': '2/3/4 GB', 'depolama': '32/64/128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Unisoc SC9863A1', 'batarya': '5000 mAh', 'ekran': '6.52" HD+ IPS LCD 60Hz', 'kamera': '13MP+2MP', 'os': 'Android 12'},
    'Motorola Edge 50 Ultra': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'Snapdragon 8s Gen 3', 'batarya': '4500 mAh', 'ekran': '6.67" QHD+ LTPO pOLED 165Hz', 'kamera': '50MP+64MP+50MP', 'os': 'Android 14'},
    'Motorola Edge 50 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Nisan', 'islemci': 'Snapdragon 7 Gen 3', 'batarya': '4500 mAh', 'ekran': '6.7" FHD+ pOLED 144Hz', 'kamera': '50MP+13MP+10MP', 'os': 'Android 14'},
    'Motorola Edge 50 Fusion': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'Snapdragon 7s Gen 2', 'batarya': '5000 mAh', 'ekran': '6.7" FHD+ pOLED 144Hz', 'kamera': '50MP+13MP+10MP', 'os': 'Android 14'},
    'Motorola Edge 50': {'5g': True, 'ram': '8/12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Haziran', 'islemci': 'Snapdragon 7 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ pOLED 144Hz', 'kamera': '50MP+13MP+10MP', 'os': 'Android 14'},
    'Motorola Edge 40 Neo': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Dimensity 7030', 'batarya': '5000 mAh', 'ekran': '6.55" FHD+ pOLED 144Hz', 'kamera': '50MP+10MP', 'os': 'Android 13'},
    'Motorola Edge 40 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '4600 mAh', 'ekran': '6.67" FHD+ pOLED 165Hz', 'kamera': '50MP+12MP+10MP', 'os': 'Android 13'},
    'Motorola Edge 40': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Dimensity 8020', 'batarya': '4400 mAh', 'ekran': '6.55" FHD+ pOLED 144Hz', 'kamera': '50MP+13MP+10MP', 'os': 'Android 13'},
    'Motorola Edge 30 Ultra': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Eylül', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '4610 mAh', 'ekran': '6.67" FHD+ pOLED 144Hz', 'kamera': '200MP+50MP+12MP', 'os': 'Android 12'},
    'Motorola Edge 30 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Şubat', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '4800 mAh', 'ekran': '6.7" FHD+ pOLED 144Hz', 'kamera': '50MP+50MP+2MP', 'os': 'Android 12'},
    'Motorola Edge 30': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Mayıs', 'islemci': 'Snapdragon 778G+', 'batarya': '4020 mAh', 'ekran': '6.5" FHD+ pOLED 144Hz', 'kamera': '50MP+50MP+2MP', 'os': 'Android 12'},
    'Motorola Moto G85 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Temmuz', 'islemci': 'Snapdragon 6s Gen 3', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ pOLED 120Hz', 'kamera': '50MP+8MP', 'os': 'Android 14'},
    'Motorola Moto G84 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Ağustos', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.55" FHD+ pOLED 120Hz', 'kamera': '50MP+8MP', 'os': 'Android 13'},
    'Motorola Moto G73 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'MediaTek Dimensity 930', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ IPS LCD 120Hz', 'kamera': '50MP+8MP', 'os': 'Android 13'},
    'Motorola Moto G54 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Ağustos', 'islemci': 'MediaTek Dimensity 7020', 'batarya': '6000 mAh', 'ekran': '6.5" FHD+ IPS LCD 120Hz', 'kamera': '50MP+2MP', 'os': 'Android 13'},
    'Motorola Moto G34 5G': {'5g': True, 'ram': '4/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ IPS LCD 120Hz', 'kamera': '50MP+2MP', 'os': 'Android 14'},
    'Motorola Moto G24': {'5g': False, 'ram': '4/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.56" HD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 14'},
    'Motorola Moto G14': {'5g': False, 'ram': '4/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'Unisoc T616', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13'},
    'Motorola Moto G62 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ IPS LCD 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 12'},
    # ── GAMİNG TELEFONLAR ──
    'ASUS ROG Phone 8 Pro': {'5g': True, 'ram': '16/24 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5500 mAh', 'ekran': '6.78" FHD+ AMOLED 165Hz', 'kamera': '50MP+13MP+5MP', 'os': 'Android 14 (ROG UI)'},
    'ASUS ROG Phone 8': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5500 mAh', 'ekran': '6.78" FHD+ AMOLED 165Hz', 'kamera': '50MP+13MP+5MP', 'os': 'Android 14 (ROG UI)'},
    'ASUS ROG Phone 7 Pro': {'5g': True, 'ram': '16/18 GB', 'depolama': '512GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '6000 mAh', 'ekran': '6.78" FHD+ AMOLED 165Hz', 'kamera': '50MP+13MP+5MP', 'os': 'Android 13 (ROG UI)'},
    'ASUS ROG Phone 7 Ultimate': {'5g': True, 'ram': '16 GB', 'depolama': '512GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '6000 mAh', 'ekran': '6.78" FHD+ AMOLED 165Hz', 'kamera': '50MP+13MP+5MP', 'os': 'Android 13 (ROG UI)'},
    'ASUS ROG Phone 7': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '6000 mAh', 'ekran': '6.78" FHD+ AMOLED 165Hz', 'kamera': '50MP+13MP+5MP', 'os': 'Android 13 (ROG UI)'},
    'ASUS ROG Phone 6 Pro': {'5g': True, 'ram': '18 GB', 'depolama': '512GB', 'sim': 2, 'cikis': '2022 Ağustos', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '6000 mAh', 'ekran': '6.78" FHD+ AMOLED 165Hz', 'kamera': '50MP+13MP+5MP', 'os': 'Android 12 (ROG UI)'},
    'ASUS ROG Phone 6': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Ağustos', 'islemci': 'Snapdragon 8+ Gen 1', 'batarya': '6000 mAh', 'ekran': '6.78" FHD+ AMOLED 165Hz', 'kamera': '50MP+13MP+5MP', 'os': 'Android 12 (ROG UI)'},
    'Nubia RedMagic 9 Pro+': {'5g': True, 'ram': '16/24 GB', 'depolama': '512GB/1TB', 'sim': 2, 'cikis': '2023 Kasım', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '6500 mAh', 'ekran': '6.8" FHD+ AMOLED 144Hz', 'kamera': '50MP+50MP+2MP', 'os': 'Android 14 (RedMagic OS 9.0)'},
    'Nubia RedMagic 9 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Kasım', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '6500 mAh', 'ekran': '6.8" FHD+ AMOLED 144Hz', 'kamera': '50MP+50MP+2MP', 'os': 'Android 14 (RedMagic OS 9.0)'},
    'Nubia RedMagic 9S': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Haziran', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '6500 mAh', 'ekran': '6.8" FHD+ AMOLED 144Hz', 'kamera': '50MP+2MP+AI', 'os': 'Android 14 (RedMagic OS 9.5)'},
    'Nubia RedMagic 8 Pro+': {'5g': True, 'ram': '16/18 GB', 'depolama': '512GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '6000 mAh', 'ekran': '6.8" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (RedMagic OS 8.0)'},
    'Nubia RedMagic 8 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '6000 mAh', 'ekran': '6.8" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (RedMagic OS 8.0)'},
    'Nubia RedMagic 8S Pro': {'5g': True, 'ram': '12/16/18 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '6000 mAh', 'ekran': '6.8" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 13 (RedMagic OS 8.5)'},
    'Nubia RedMagic 7 Pro': {'5g': True, 'ram': '8/12/16/18 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.8" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 12 (RedMagic OS 7.0)'},
    'Nubia RedMagic 7': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Mart', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '4500 mAh', 'ekran': '6.8" FHD+ AMOLED 165Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 12 (RedMagic OS 5.0)'},
    'Xiaomi Black Shark 5 Pro': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '4650 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '108MP+13MP+5MP', 'os': 'Android 12 (JoyUI 13)'},
    'Xiaomi Black Shark 5': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'Snapdragon 870', 'batarya': '4650 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '108MP+13MP+5MP', 'os': 'Android 12 (JoyUI 13)'},
    'Lenovo Legion Phone 3 Pro': {'5g': True, 'ram': '12/16/18 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.92" FHD+ AMOLED 144Hz', 'kamera': '64MP+16MP+5MP', 'os': 'Android 12 (ZUI 14)'},
    'Lenovo Legion Phone 2 Pro': {'5g': True, 'ram': '12/16/18 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2021 Nisan', 'islemci': 'Snapdragon 888', 'batarya': '5500 mAh', 'ekran': '6.92" FHD+ AMOLED 144Hz', 'kamera': '64MP+16MP+ToF', 'os': 'Android 11 (ZUI 12.5)'},
    # ── SONY ──
    'Sony Xperia 1 VI': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ OLED 120Hz', 'kamera': '52MP+48MP+12MP', 'os': 'Android 14'},
    'Sony Xperia 1 V': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.5" 4K OLED 120Hz', 'kamera': '52MP+48MP+12MP', 'os': 'Android 13'},
    'Sony Xperia 1 IV': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2022 Mayıs', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.5" 4K OLED 120Hz', 'kamera': '12MP+12MP+12MP', 'os': 'Android 12'},
    'Sony Xperia 1 III': {'5g': True, 'ram': '12 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2021 Ağustos', 'islemci': 'Snapdragon 888', 'batarya': '4500 mAh', 'ekran': '6.5" 4K OLED 120Hz', 'kamera': '12MP+12MP+12MP', 'os': 'Android 11'},
    'Sony Xperia 5 VI': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Temmuz', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5000 mAh', 'ekran': '6.1" FHD+ OLED 120Hz', 'kamera': '48MP+12MP+12MP', 'os': 'Android 14'},
    'Sony Xperia 5 V': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.1" FHD+ OLED 120Hz', 'kamera': '52MP+12MP', 'os': 'Android 13'},
    'Sony Xperia 5 IV': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.1" FHD+ OLED 120Hz', 'kamera': '12MP+12MP+12MP', 'os': 'Android 12'},
    'Sony Xperia 5 III': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Ekim', 'islemci': 'Snapdragon 888', 'batarya': '4500 mAh', 'ekran': '6.1" FHD+ OLED 120Hz', 'kamera': '12MP+12MP+12MP', 'os': 'Android 11'},
    'Sony Xperia 10 VI': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Haziran', 'islemci': 'Snapdragon 6 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.1" FHD+ OLED 60Hz', 'kamera': '48MP+8MP', 'os': 'Android 14'},
    'Sony Xperia 10 V': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.1" FHD+ OLED 60Hz', 'kamera': '48MP+8MP+AI', 'os': 'Android 13'},
    'Sony Xperia 10 IV': {'5g': True, 'ram': '6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.0" FHD+ OLED 60Hz', 'kamera': '12MP+8MP+8MP', 'os': 'Android 12'},
    'Sony Xperia 10 III': {'5g': True, 'ram': '6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2021 Haziran', 'islemci': 'Snapdragon 690 5G', 'batarya': '4500 mAh', 'ekran': '6.0" FHD+ OLED 60Hz', 'kamera': '12MP+8MP+8MP', 'os': 'Android 11'},
    'Sony Xperia Pro-I': {'5g': True, 'ram': '12 GB', 'depolama': '512GB', 'sim': 2, 'cikis': '2021 Kasım', 'islemci': 'Snapdragon 888', 'batarya': '4500 mAh', 'ekran': '6.5" 4K OLED 120Hz', 'kamera': '12MP+12MP+12MP', 'os': 'Android 11'},
    'Sony Xperia Pro': {'5g': True, 'ram': '12 GB', 'depolama': '512GB', 'sim': 1, 'cikis': '2021 Mart', 'islemci': 'Snapdragon 888', 'batarya': '4000 mAh', 'ekran': '6.5" 4K OLED 120Hz', 'kamera': '12MP+12MP+12MP+ToF', 'os': 'Android 10'},
    'Sony Xperia L4': {'5g': False, 'ram': '3 GB', 'depolama': '64GB', 'sim': 2, 'cikis': '2020 Mart', 'islemci': 'MediaTek Helio P22', 'batarya': '3580 mAh', 'ekran': '6.2" HD+ IPS LCD 60Hz', 'kamera': '13MP+5MP+2MP', 'os': 'Android 9'},
    'Sony Xperia Ace III': {'5g': False, 'ram': '4 GB', 'depolama': '64GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'Snapdragon 480', 'batarya': '4500 mAh', 'ekran': '5.5" HD+ IPS LCD 60Hz', 'kamera': '13MP', 'os': 'Android 12'},
    # ── ZTE / NUBİA ──
    'ZTE Blade V60 Design': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Haziran', 'islemci': 'MediaTek Helio G88', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 14'},
    'ZTE Blade V50 Design': {'5g': False, 'ram': '4/6/8 GB', 'depolama': '64/128/256GB', 'sim': 2, 'cikis': '2023 Ağustos', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 13'},
    'ZTE Blade V50 Vita': {'5g': False, 'ram': '4/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Ağustos', 'islemci': 'MediaTek Helio G37', 'batarya': '5000 mAh', 'ekran': '6.75" HD+ IPS LCD 60Hz', 'kamera': '13MP+2MP', 'os': 'Android 13'},
    'ZTE Blade A75 5G': {'5g': True, 'ram': '4/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Dimensity 6020', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 14'},
    'ZTE Blade A75': {'5g': False, 'ram': '4/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Unisoc T606', 'batarya': '5000 mAh', 'ekran': '6.75" HD+ IPS LCD 60Hz', 'kamera': '50MP+2MP', 'os': 'Android 13'},
    'ZTE Blade A54': {'5g': False, 'ram': '3/4 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Unisoc T606', 'batarya': '5000 mAh', 'ekran': '6.52" HD+ IPS LCD 60Hz', 'kamera': '13MP+2MP', 'os': 'Android 12'},
    'ZTE Blade A34': {'5g': False, 'ram': '2/3 GB', 'depolama': '32/64GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Unisoc SC9863A', 'batarya': '4000 mAh', 'ekran': '6.0" HD+ IPS LCD 60Hz', 'kamera': '8MP', 'os': 'Android 12'},
    'ZTE Blade A73 5G': {'5g': True, 'ram': '4/6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.52" FHD+ IPS LCD 90Hz', 'kamera': '48MP+5MP+2MP', 'os': 'Android 13'},
    'Nubia Z60 Ultra': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2023 Aralık', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '6000 mAh', 'ekran': '6.8" FHD+ AMOLED 144Hz', 'kamera': '50MP+64MP+50MP', 'os': 'Android 14 (MyOS 13)'},
    'Nubia Z50S Pro': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '128/256/512/1TB', 'sim': 2, 'cikis': '2023 Temmuz', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 144Hz', 'kamera': '35MP+50MP+64MP', 'os': 'Android 13 (MyOS 13)'},
    'Nubia Z50 Ultra': {'5g': True, 'ram': '8/12/16 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.8" FHD+ AMOLED 144Hz', 'kamera': '50MP+64MP+50MP', 'os': 'Android 12 (MyOS 12)'},
    'Nubia Z50': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 144Hz', 'kamera': '64MP+50MP+2MP', 'os': 'Android 12 (MyOS 12)'},
    'Nubia Focus 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'Snapdragon 695 5G', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 14'},
    'Nubia Neo 5G': {'5g': True, 'ram': '4/6/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.675" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 14'},
    'Nubia Music': {'5g': False, 'ram': '4/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Helio G85', 'batarya': '5000 mAh', 'ekran': '6.6" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP', 'os': 'Android 13'},
    # ── LAVA ──
    'Lava Agni 3 5G': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 7050', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 14'},
    'Lava Agni 2 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'MediaTek Dimensity 7050', 'batarya': '4700 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP+2MP', 'os': 'Android 13'},
    'Lava Agni 1 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'MediaTek Dimensity 810', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '50MP+8MP+5MP+2MP', 'os': 'Android 12'},
    'Lava Blaze 2 5G': {'5g': True, 'ram': '6/8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.52" HD+ IPS LCD 90Hz', 'kamera': '50MP+AI+AI', 'os': 'Android 12'},
    'Lava Blaze Curve 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '5000 mAh', 'ekran': '6.67" FHD+ AMOLED 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13'},
    'Lava Blaze 5G': {'5g': True, 'ram': '4/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2022 Aralık', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ IPS LCD 90Hz', 'kamera': '50MP+2MP+2MP', 'os': 'Android 12'},
    'Lava Storm 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Dimensity 1080', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 13'},
    'Lava O2 5G': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2024 Mayıs', 'islemci': 'MediaTek Dimensity 6020', 'batarya': '5000 mAh', 'ekran': '6.56" FHD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 14'},
    'Lava X3 5G': {'5g': True, 'ram': '4/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Dimensity 700', 'batarya': '5000 mAh', 'ekran': '6.52" HD+ IPS LCD 90Hz', 'kamera': '50MP+AI', 'os': 'Android 13'},
    'Lava Yuva 3 Pro': {'5g': False, 'ram': '4/8 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'MediaTek Helio G37', 'batarya': '5000 mAh', 'ekran': '6.5" HD+ IPS LCD 90Hz', 'kamera': '13MP+2MP', 'os': 'Android 12'},
    'Lava Yuva 2 Pro': {'5g': False, 'ram': '4 GB', 'depolama': '64GB', 'sim': 2, 'cikis': '2023 Şubat', 'islemci': 'MediaTek Helio A22', 'batarya': '5000 mAh', 'ekran': '6.5" HD+ IPS LCD 60Hz', 'kamera': '13MP+2MP', 'os': 'Android 12'},
    # ── SHARP / MEİZU ──
    'Sharp AQUOS R9': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2024 Temmuz', 'islemci': 'Snapdragon 7 Gen 3', 'batarya': '5000 mAh', 'ekran': '6.5" FHD+ OLED 240Hz', 'kamera': '50MP+50MP', 'os': 'Android 14'},
    'Sharp AQUOS R8 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 1, 'cikis': '2023 Temmuz', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.6" QHD+ LTPO OLED 240Hz', 'kamera': '52MP+50MP', 'os': 'Android 13'},
    'Sharp AQUOS R8': {'5g': True, 'ram': '8 GB', 'depolama': '256GB', 'sim': 1, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.39" FHD+ LTPO OLED 240Hz', 'kamera': '52MP+50MP', 'os': 'Android 13'},
    'Sharp AQUOS R7': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 1, 'cikis': '2022 Haziran', 'islemci': 'Snapdragon 8 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.6" 4K IGZO LTPS LCD 240Hz', 'kamera': '47.2MP', 'os': 'Android 12'},
    'Sharp AQUOS sense8': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Ekim', 'islemci': 'Snapdragon 6 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.1" FHD+ IGZO OLED 90Hz', 'kamera': '50MP+13MP', 'os': 'Android 13'},
    'Sharp AQUOS sense7': {'5g': True, 'ram': '4/6 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2022 Kasım', 'islemci': 'Snapdragon 695 5G', 'batarya': '4570 mAh', 'ekran': '6.1" FHD+ IGZO OLED 60Hz', 'kamera': '50MP+8MP', 'os': 'Android 12'},
    'Sharp AQUOS wish3': {'5g': False, 'ram': '4/6 GB', 'depolama': '64/128GB', 'sim': 2, 'cikis': '2023 Haziran', 'islemci': 'Snapdragon 695 5G', 'batarya': '4570 mAh', 'ekran': '6.0" HD+ IGZO IPS LCD 60Hz', 'kamera': '13MP', 'os': 'Android 13'},
    'Sharp AQUOS zero6': {'5g': True, 'ram': '8 GB', 'depolama': '128GB', 'sim': 2, 'cikis': '2021 Haziran', 'islemci': 'Snapdragon 750G 5G', 'batarya': '4000 mAh', 'ekran': '6.4" FHD+ IGZO OLED 240Hz', 'kamera': '48MP+8MP', 'os': 'Android 11'},
    'Meizu 21 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'Snapdragon 8 Gen 3', 'batarya': '5000 mAh', 'ekran': '6.79" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+50MP+32MP', 'os': 'Android 14 (Flyme 21)'},
    'Meizu 21': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2023 Kasım', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '4800 mAh', 'ekran': '6.55" FHD+ AMOLED 144Hz', 'kamera': '50MP+50MP+12MP', 'os': 'Android 14 (Flyme 21)'},
    'Meizu 21 Note': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'Snapdragon 8s Gen 3', 'batarya': '5000 mAh', 'ekran': '6.79" FHD+ AMOLED 144Hz', 'kamera': '200MP+12MP+12MP', 'os': 'Android 14 (Flyme 21)'},
    'Meizu 20 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512/1TB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.79" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+50MP+12MP', 'os': 'Android 13 (Flyme 10)'},
    'Meizu 20': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256/512GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '4800 mAh', 'ekran': '6.55" FHD+ AMOLED 144Hz', 'kamera': '50MP+12MP+8MP', 'os': 'Android 13 (Flyme 10)'},
    'Meizu 20 Infinity': {'5g': True, 'ram': '16 GB', 'depolama': '512GB/1TB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'Snapdragon 8 Gen 2', 'batarya': '4800 mAh', 'ekran': '6.79" QHD+ LTPO OLED 120Hz', 'kamera': '50MP+50MP+12MP', 'os': 'Android 13 (Flyme 10)'},
    'Meizu Note 21 Pro': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Nisan', 'islemci': 'Snapdragon 7s Gen 2', 'batarya': '5000 mAh', 'ekran': '6.79" FHD+ AMOLED 144Hz', 'kamera': '50MP+8MP+2MP', 'os': 'Android 14 (Flyme 21)'},
    'Meizu Note 21': {'5g': True, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Nisan', 'islemci': 'Snapdragon 4 Gen 2', 'batarya': '5000 mAh', 'ekran': '6.79" FHD+ AMOLED 120Hz', 'kamera': '50MP+2MP', 'os': 'Android 14 (Flyme 21)'},
    'Meizu Blue Note 21S': {'5g': True, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Ağustos', 'islemci': 'Snapdragon 6 Gen 1', 'batarya': '5000 mAh', 'ekran': '6.78" FHD+ AMOLED 120Hz', 'kamera': '64MP+8MP+2MP', 'os': 'Android 13 (Flyme 10.3)'},
    # ── DOOGEE / ULEFONE ──
    'Doogee V Max Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Şubat', 'islemci': 'MediaTek Dimensity 7050', 'batarya': '22000 mAh', 'ekran': '6.58" FHD+ AMOLED 120Hz', 'kamera': '108MP+20MP+20MP', 'os': 'Android 13'},
    'Doogee V Max': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Dimensity 1080', 'batarya': '22000 mAh', 'ekran': '6.58" FHD+ IPS LCD 120Hz', 'kamera': '64MP+20MP+20MP', 'os': 'Android 12'},
    'Doogee V30 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Dimensity 1080', 'batarya': '10800 mAh', 'ekran': '6.58" FHD+ IPS LCD 120Hz', 'kamera': '50MP+20MP+20MP', 'os': 'Android 12'},
    'Doogee V30': {'5g': True, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Ekim', 'islemci': 'MediaTek Dimensity 900', 'batarya': '10800 mAh', 'ekran': '6.58" FHD+ IPS LCD 120Hz', 'kamera': '50MP+20MP+2MP', 'os': 'Android 12'},
    'Doogee V20 Pro': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2022 Ağustos', 'islemci': 'MediaTek Dimensity 1080', 'batarya': '6000 mAh', 'ekran': '6.43" FHD+ AMOLED 90Hz', 'kamera': '64MP+8MP+20MP', 'os': 'Android 12'},
    'Doogee S100 Pro': {'5g': True, 'ram': '12/16 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Dimensity 1080', 'batarya': '26000 mAh', 'ekran': '6.58" FHD+ IPS LCD 120Hz', 'kamera': '64MP+20MP+20MP', 'os': 'Android 13'},
    'Doogee S100': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Dimensity 1080', 'batarya': '26000 mAh', 'ekran': '6.58" FHD+ IPS LCD 120Hz', 'kamera': '64MP+20MP+20MP', 'os': 'Android 13'},
    'Doogee S98 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2022 Temmuz', 'islemci': 'MediaTek Helio G96', 'batarya': '6000 mAh', 'ekran': '6.3" FHD+ AMOLED 60Hz', 'kamera': '48MP+20MP+8MP', 'os': 'Android 12'},
    'Doogee S98': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2022 Haziran', 'islemci': 'MediaTek Helio G96', 'batarya': '6000 mAh', 'ekran': '6.3" FHD+ AMOLED 60Hz', 'kamera': '48MP+20MP+8MP', 'os': 'Android 12'},
    'Doogee N55 Pro': {'5g': False, 'ram': '8/16 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Nisan', 'islemci': 'MediaTek Helio G99', 'batarya': '6000 mAh', 'ekran': '6.58" FHD+ IPS LCD 90Hz', 'kamera': '50MP+16MP+8MP', 'os': 'Android 14'},
    'Doogee N40 Pro': {'5g': False, 'ram': '6/8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2021 Aralık', 'islemci': 'MediaTek Helio P60', 'batarya': '6300 mAh', 'ekran': '6.52" FHD+ IPS LCD 90Hz', 'kamera': '48MP+8MP+8MP', 'os': 'Android 11'},
    'Doogee X98 Pro': {'5g': False, 'ram': '4 GB', 'depolama': '64GB', 'sim': 2, 'cikis': '2022 Nisan', 'islemci': 'MediaTek Helio A22', 'batarya': '4200 mAh', 'ekran': '6.52" HD+ IPS LCD 60Hz', 'kamera': '8MP+2MP+2MP', 'os': 'Android 11'},
    'Doogee X98': {'5g': False, 'ram': '3 GB', 'depolama': '16/32GB', 'sim': 2, 'cikis': '2022 Ocak', 'islemci': 'MediaTek Helio A22', 'batarya': '4200 mAh', 'ekran': '6.52" HD+ IPS LCD 60Hz', 'kamera': '8MP+2MP+2MP', 'os': 'Android 10'},
    'Ulefone Power Armor 23 Ultra': {'5g': True, 'ram': '12/16 GB', 'depolama': '256/512GB', 'sim': 2, 'cikis': '2024 Mart', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '23000 mAh', 'ekran': '6.78" FHD+ IPS LCD 120Hz', 'kamera': '64MP+20MP+2MP', 'os': 'Android 13'},
    'Ulefone Power Armor 23': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Eylül', 'islemci': 'MediaTek Dimensity 6080', 'batarya': '23000 mAh', 'ekran': '6.78" FHD+ IPS LCD 120Hz', 'kamera': '64MP+20MP+2MP', 'os': 'Android 13'},
    'Ulefone Power Armor 19T': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Nisan', 'islemci': 'MediaTek Dimensity 900', 'batarya': '9600 mAh', 'ekran': '6.58" FHD+ IPS LCD 120Hz', 'kamera': '64MP+20MP+AI', 'os': 'Android 13'},
    'Ulefone Armor 23 Ultra': {'5g': True, 'ram': '16 GB', 'depolama': '512GB', 'sim': 2, 'cikis': '2024 Haziran', 'islemci': 'MediaTek Dimensity 7020', 'batarya': '9800 mAh', 'ekran': '6.78" FHD+ IPS LCD 120Hz', 'kamera': '64MP+20MP+2MP', 'os': 'Android 14'},
    'Ulefone Armor 21': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Ocak', 'islemci': 'MediaTek Dimensity 900', 'batarya': '7500 mAh', 'ekran': '6.58" FHD+ IPS LCD 120Hz', 'kamera': '64MP+20MP+2MP', 'os': 'Android 12'},
    'Ulefone Armor 20WT': {'5g': True, 'ram': '12 GB', 'depolama': '256GB', 'sim': 2, 'cikis': '2023 Mart', 'islemci': 'MediaTek Dimensity 900', 'batarya': '9200 mAh', 'ekran': '6.58" FHD+ IPS LCD 120Hz', 'kamera': '64MP+20MP+2MP', 'os': 'Android 13'},
    'Ulefone Note 17 Pro': {'5g': False, 'ram': '8/12 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2024 Ocak', 'islemci': 'MediaTek Helio G99', 'batarya': '5200 mAh', 'ekran': '6.78" FHD+ IPS LCD 90Hz', 'kamera': '108MP+8MP+2MP', 'os': 'Android 13'},
    'Ulefone Note 16 Pro': {'5g': False, 'ram': '8 GB', 'depolama': '128/256GB', 'sim': 2, 'cikis': '2023 Mayıs', 'islemci': 'MediaTek Helio G85', 'batarya': '4400 mAh', 'ekran': '6.52" HD+ IPS LCD 60Hz', 'kamera': '48MP+5MP+AI', 'os': 'Android 13'},
}

# Oyun FPS Veritabanı (PUBG Mobile, COD Mobile, Genshin Impact, Free Fire)
# Tier 1: SD 8 Gen 3 / A17 Pro / Tensor G4 / Exynos 2500  → PUBG Ultra HD 90 | COD Maks 120 | Genshin En Yüksek 60 | FF Ultra 90
# Tier 2: SD 8 Gen 2 / A16 Bionic / Tensor G3 / Kirin 9010 / Dim 9200+      → PUBG Ultra HD 90 | COD Maks 120 | Genshin En Yüksek 60 | FF Ultra 90
# Tier 3: SD 8 Gen 1 / SD 8+ Gen 1 / A15 / Tensor G2 / SD 888 / Dim 9000   → PUBG Ultra HD 90 | COD Yüksek 90 | Genshin Yüksek 60 | FF Ultra 60
# Tier 4: SD 865/870 / Kirin 9000 / Dim 8100/8200 / A14 Bionic               → PUBG HDR 60 | COD Yüksek 90 | Genshin Yüksek 60 | FF Maks 60
# Tier 5: SD 778G/782G / SD 7 Gen 1-3 / Dim 1080/7200 / Dim 8300 / Exynos 1380/1480 → PUBG HDR 60 | COD Yüksek 60 | Genshin Orta 60 | FF Maks 60
# Tier 6: SD 695/732G / Dim 6080/7050/900/930 / Helio G99 / SD 6 Gen 1       → PUBG Smooth 60 | COD Orta 60 | Genshin Düşük 30 | FF Normal 60
# Tier 7: SD 680/685 / Dim 700/720/810 / Helio G88/G96/G95                    → PUBG Smooth 60 | COD Düşük 60 | Genshin Düşük 30 | FF Normal 60
# Tier 8: Helio G85/G37/G36/G25/A22 / SD 480 / Unisoc / Exynos 850           → PUBG Smooth 30 | COD Düşük 30 | Genshin Düşük 30 | FF Normal 30
# Gaming phones (ROG/RedMagic) get COD boost to 120fps

_T1 = {'pubg': ('Ultra HD', '90 FPS'), 'cod': ('Maksimum', '120 FPS'), 'genshin': ('En Yüksek 60FPS', '60 FPS'), 'ff': ('Ultra', '90 FPS')}
_T2 = {'pubg': ('Ultra HD', '90 FPS'), 'cod': ('Maksimum', '120 FPS'), 'genshin': ('En Yüksek 60FPS', '60 FPS'), 'ff': ('Ultra', '90 FPS')}
_T3 = {'pubg': ('Ultra HD', '90 FPS'), 'cod': ('Yüksek', '90 FPS'), 'genshin': ('Yüksek 60FPS', '60 FPS'), 'ff': ('Ultra', '60 FPS')}
_T4 = {'pubg': ('HDR', '60 FPS'), 'cod': ('Yüksek', '90 FPS'), 'genshin': ('Yüksek 60FPS', '60 FPS'), 'ff': ('Maks', '60 FPS')}
_T5 = {'pubg': ('HDR', '60 FPS'), 'cod': ('Yüksek', '60 FPS'), 'genshin': ('Orta 60FPS', '60 FPS'), 'ff': ('Maks', '60 FPS')}
_T6 = {'pubg': ('Smooth', '60 FPS'), 'cod': ('Orta', '60 FPS'), 'genshin': ('Düşük 30FPS', '30 FPS'), 'ff': ('Normal', '60 FPS')}
_T7 = {'pubg': ('Smooth', '60 FPS'), 'cod': ('Düşük', '60 FPS'), 'genshin': ('Düşük 30FPS', '30 FPS'), 'ff': ('Normal', '60 FPS')}
_T8 = {'pubg': ('Smooth', '30 FPS'), 'cod': ('Düşük', '30 FPS'), 'genshin': ('Düşük 30FPS', '30 FPS'), 'ff': ('Normal', '30 FPS')}
_GAM_T1 = {'pubg': ('Ultra HD', '90 FPS'), 'cod': ('Maksimum', '120 FPS'), 'genshin': ('En Yüksek 60FPS', '60 FPS'), 'ff': ('Ultra', '90 FPS')}
_GAM_T3 = {'pubg': ('Ultra HD', '90 FPS'), 'cod': ('Maksimum', '120 FPS'), 'genshin': ('Yüksek 60FPS', '60 FPS'), 'ff': ('Ultra', '60 FPS')}

TELEFON_FPS_DB = {
    # ── SAMSUNG S SERİSİ (T1/T2/T3/T4) ──
    'Samsung Galaxy S24 Ultra': _T1, 'Samsung Galaxy S24+': _T1, 'Samsung Galaxy S24': _T1, 'Samsung Galaxy S24 FE': _T1,
    'Samsung Galaxy S23 Ultra': _T2, 'Samsung Galaxy S23+': _T2, 'Samsung Galaxy S23': _T2, 'Samsung Galaxy S23 FE': _T3,
    'Samsung Galaxy S22 Ultra': _T3, 'Samsung Galaxy S22+': _T3, 'Samsung Galaxy S22': _T3,
    'Samsung Galaxy S21 Ultra': _T3, 'Samsung Galaxy S21+': _T3, 'Samsung Galaxy S21': _T3, 'Samsung Galaxy S21 FE': _T3,
    'Samsung Galaxy S20 Ultra': _T4, 'Samsung Galaxy S20+': _T4, 'Samsung Galaxy S20': _T4, 'Samsung Galaxy S20 FE': _T4,
    'Samsung Galaxy S10+': _T4, 'Samsung Galaxy S10': _T4, 'Samsung Galaxy S10e': _T4, 'Samsung Galaxy S10 5G': _T4,
    # Note
    'Samsung Galaxy Note 20 Ultra': _T4, 'Samsung Galaxy Note 20': _T4,
    'Samsung Galaxy Note 10+': _T4, 'Samsung Galaxy Note 10': _T4, 'Samsung Galaxy Note 10 Lite': _T7,
    # Z Fold/Flip
    'Samsung Galaxy Z Fold 6': _T1, 'Samsung Galaxy Z Fold 5': _T2, 'Samsung Galaxy Z Fold 4': _T3, 'Samsung Galaxy Z Fold 3': _T3,
    'Samsung Galaxy Z Flip 6': _T1, 'Samsung Galaxy Z Flip 5': _T2, 'Samsung Galaxy Z Flip 4': _T3, 'Samsung Galaxy Z Flip 3': _T3,
    # A Serisi
    'Samsung Galaxy A55 5G': _T5, 'Samsung Galaxy A54 5G': _T5, 'Samsung Galaxy A53 5G': _T6,
    'Samsung Galaxy A52s 5G': _T5, 'Samsung Galaxy A52': _T6,
    'Samsung Galaxy A35 5G': _T5, 'Samsung Galaxy A34 5G': _T5, 'Samsung Galaxy A33 5G': _T6,
    'Samsung Galaxy A32': _T8, 'Samsung Galaxy A32 5G': _T7,
    'Samsung Galaxy A25 5G': _T6, 'Samsung Galaxy A24': _T6,
    'Samsung Galaxy A23 5G': _T6, 'Samsung Galaxy A23': _T7,
    'Samsung Galaxy A22 5G': _T7, 'Samsung Galaxy A22': _T8,
    'Samsung Galaxy A15 5G': _T7, 'Samsung Galaxy A15': _T6,
    'Samsung Galaxy A14 5G': _T7, 'Samsung Galaxy A14': _T8,
    'Samsung Galaxy A13': _T8, 'Samsung Galaxy A13 5G': _T7,
    'Samsung Galaxy A05s': _T7, 'Samsung Galaxy A05': _T8, 'Samsung Galaxy A04s': _T8,
    # M Serisi
    'Samsung Galaxy M54 5G': _T5, 'Samsung Galaxy M53 5G': _T6,
    'Samsung Galaxy M34 5G': _T6, 'Samsung Galaxy M33 5G': _T6, 'Samsung Galaxy M14 5G': _T6,
    # ── iPHONE ──
    'iPhone 15 Pro Max': _T1, 'iPhone 15 Pro': _T1,
    'iPhone 15 Plus': _T2, 'iPhone 15': _T2,
    'iPhone 14 Pro Max': _T2, 'iPhone 14 Pro': _T2, 'iPhone 14 Plus': _T3, 'iPhone 14': _T3,
    'iPhone 13 Pro Max': _T3, 'iPhone 13 Pro': _T3, 'iPhone 13 mini': _T3, 'iPhone 13': _T3,
    'iPhone 12 Pro Max': _T3, 'iPhone 12 Pro': _T3, 'iPhone 12 mini': _T3, 'iPhone 12': _T3,
    'iPhone 11 Pro Max': _T4, 'iPhone 11 Pro': _T4, 'iPhone 11': _T4,
    'iPhone SE (2022)': _T3, 'iPhone SE (2020)': _T4,
    # ── XİAOMİ ──
    'Xiaomi 14 Ultra': _T1, 'Xiaomi 14 Pro': _T1, 'Xiaomi 14': _T1,
    'Xiaomi 13 Ultra': _T2, 'Xiaomi 13 Pro': _T2, 'Xiaomi 13': _T2,
    'Xiaomi 13T Pro': _T2, 'Xiaomi 13T': _T4,
    'Xiaomi 12 Pro': _T3, 'Xiaomi 12': _T3, 'Xiaomi 12T Pro': _T3, 'Xiaomi 12T': _T4,
    'Xiaomi 11 Ultra': _T3, 'Xiaomi 11 Pro': _T3, 'Xiaomi 11': _T3,
    'Xiaomi 11T Pro': _T3, 'Xiaomi 11T': _T5,
    'Redmi Note 13 Pro+ 5G': _T5, 'Redmi Note 13 Pro 5G': _T5,
    'Redmi Note 13 5G': _T6, 'Redmi Note 13': _T7,
    'Redmi Note 12 Pro+ 5G': _T5, 'Redmi Note 12 Pro 5G': _T5,
    'Redmi Note 12 5G': _T8, 'Redmi Note 12': _T7, 'Redmi Note 12s': _T7,
    'Redmi Note 11 Pro+ 5G': _T6, 'Redmi Note 11 Pro': _T6,
    'Redmi Note 11S 5G': _T7, 'Redmi Note 11S': _T7,
    'Redmi Note 11': _T7, 'Redmi Note 11 5G': _T7,
    'Redmi Note 10 Pro': _T6, 'Redmi Note 10': _T7, 'Redmi Note 10s': _T7, 'Redmi Note 10 5G': _T7,
    'Redmi 13C 5G': _T7, 'Redmi 13C': _T8, 'Redmi 13': _T8,
    'Redmi 12C': _T8, 'Redmi 12': _T8, 'Redmi 12 5G': _T8,
    'Redmi 10C': _T7, 'Redmi 10': _T8, 'Redmi 10A': _T8,
    'Redmi A3': _T8, 'Redmi A2+': _T8, 'Redmi A2': _T8, 'Redmi A1+': _T8,
    'Xiaomi Pad 6 Pro': _T3, 'Xiaomi Pad 6': _T4,
    # ── POCO ──
    'POCO X6 Pro 5G': _T5, 'POCO X6 5G': _T5,
    'POCO X5 Pro 5G': _T5, 'POCO X5 5G': _T6,
    'POCO X4 Pro 5G': _T6, 'POCO X4 GT': _T4,
    'POCO X3 Pro': _T4, 'POCO X3 GT': _T5, 'POCO X3 NFC': _T6, 'POCO X3': _T6,
    'POCO F6 Pro': _T2, 'POCO F6 5G': _T2,
    'POCO F5 Pro 5G': _T2, 'POCO F5 5G': _T5,
    'POCO F4 GT': _T3, 'POCO F4 5G': _T4, 'POCO F3': _T4, 'POCO F2 Pro': _T4,
    'POCO M6 Pro 5G': _T6, 'POCO M6 5G': _T7,
    'POCO M5s': _T7, 'POCO M5': _T6,
    'POCO M4 Pro 5G': _T7, 'POCO M4 Pro': _T7, 'POCO M4 5G': _T7, 'POCO M3 Pro 5G': _T7,
    'POCO C65': _T8, 'POCO C55': _T8, 'POCO C51': _T8, 'POCO C40': _T8,
    # ── GOOGLE PİXEL ──
    'Pixel 9 Pro XL': _T1, 'Pixel 9 Pro': _T1, 'Pixel 9': _T1, 'Pixel 9 Pro Fold': _T1,
    'Pixel 8 Pro': _T2, 'Pixel 8': _T2, 'Pixel 8a': _T2,
    'Pixel 7 Pro': _T3, 'Pixel 7': _T3, 'Pixel 7a': _T3,
    'Pixel 6 Pro': _T3, 'Pixel 6': _T3, 'Pixel 6a': _T3,
    'Pixel 5': _T6, 'Pixel 5a 5G': _T6, 'Pixel 4a 5G': _T6, 'Pixel 4a': _T6,
    'Pixel 4 XL': _T4, 'Pixel 4': _T4,
    # ── TECNO ──
    'Phantom V Fold 2 5G': _T3, 'Phantom V Flip 5G': _T5,
    'Phantom X2 Pro': _T3, 'Phantom X2': _T3, 'Phantom X': _T7,
    'Camon 30 Premier 5G': _T4, 'Camon 30 Pro 5G': _T6,
    'Camon 30 5G': _T6, 'Camon 30': _T8,
    'Camon 20 Premier 5G': _T5, 'Camon 20 Pro 5G': _T5,
    'Camon 20 Pro': _T6, 'Camon 20': _T8,
    'Camon 19 Pro': _T7, 'Camon 19': _T8,
    'Spark 20 Pro+': _T6, 'Spark 20 Pro': _T6,
    'Spark 20C': _T8, 'Spark 20': _T8,
    'Spark 10 Pro': _T7, 'Spark 10': _T7, 'Spark 10C': _T8,
    'Pova 6 Pro 5G': _T6, 'Pova 6 5G': _T6, 'Pova 5 Pro': _T6, 'Pova 5': _T8,
    'Spark Go 2024': _T8, 'Spark Go 2023': _T8,
    # ── HONOR ──
    'Honor Magic6 Pro': _T1, 'Honor Magic6': _T1, 'Honor Magic6 Lite': _T6,
    'Honor Magic5 Pro': _T2, 'Honor Magic5 Lite': _T6,
    'Honor 200 Pro': _T2, 'Honor 200': _T5, 'Honor 200 Lite': _T8,
    'Honor 90 GT': _T2, 'Honor 90 Pro': _T3, 'Honor 90': _T5, 'Honor 90 Lite': _T7,
    'Honor 80 Pro': _T3, 'Honor 80': _T5, 'Honor 80 Lite': _T6, 'Honor 80 SE': _T6,
    'Honor X9b 5G': _T6, 'Honor X8b': _T6, 'Honor X7b': _T7, 'Honor X6b': _T7,
    'Honor X9a 5G': _T6, 'Honor X8a': _T7, 'Honor X7a': _T7, 'Honor X6a': _T8,
    'Honor X50 5G': _T6, 'Honor X40 5G': _T6, 'Honor X30i': _T7, 'Honor X20': _T6,
    'Honor Play 8T': _T8, 'Honor Play 7T': _T8, 'Honor Pad 9': _T6,
    # ── CANE ──
    'CANE P10 Pro': _T5, 'CANE P10': _T6, 'CANE P8 Pro': _T6, 'CANE P8': _T7,
    'CANE X5 5G': _T6, 'CANE X5': _T7, 'CANE Note 10': _T6,
    'CANE S6 Pro': _T7, 'CANE S6': _T7,
    # ── HUAWEI ──
    'Huawei Mate 60 Pro+': _T2, 'Huawei Mate 60 Pro': _T2, 'Huawei Mate 60': _T2, 'Huawei Mate 60 RS': _T2,
    'Huawei Mate 50 Pro': _T3, 'Huawei Mate 50': _T3, 'Huawei Mate 50E': _T5,
    'Huawei Mate 40 Pro+': _T3, 'Huawei Mate 40 Pro': _T3, 'Huawei Mate 40': _T3,
    'Huawei P60 Pro': _T3, 'Huawei P60': _T3, 'Huawei P60 Art': _T3,
    'Huawei P50 Pro': _T3, 'Huawei P50': _T3, 'Huawei P50 Pocket': _T3,
    'Huawei P40 Pro+': _T3, 'Huawei P40 Pro': _T3, 'Huawei P40': _T3, 'Huawei P40 Lite': _T7,
    'Huawei P30 Pro': _T4, 'Huawei P30': _T4, 'Huawei P30 Lite': _T7,
    'Huawei Nova 12 Pro': _T6, 'Huawei Nova 12': _T6,
    'Huawei Nova 11 Pro': _T5, 'Huawei Nova 11': _T5,
    'Huawei Nova 10 Pro': _T5, 'Huawei Nova 10': _T5,
    'Huawei Nova 9': _T5, 'Huawei Nova 9 SE': _T7,
    'Huawei Y9s': _T8, 'Huawei Y9a': _T7, 'Huawei Y7a': _T8, 'Huawei Y6p': _T8,
    'Huawei Pocket 2': _T2, 'Huawei Pocket S': _T5,
    # ── LOVEIR ──
    'LOVEIR X1 Pro': _T5, 'LOVEIR X1': _T6, 'LOVEIR V10 Pro': _T6, 'LOVEIR V10': _T7,
    'LOVEIR Note 8 Pro': _T7, 'LOVEIR Note 8': _T7, 'LOVEIR S7': _T8,
    # ── OPPO / REALME ──
    'OPPO Find X7 Ultra': _T1, 'OPPO Find X7 Pro': _T1, 'OPPO Find X7': _T1,
    'OPPO Find X6 Pro': _T2, 'OPPO Find X5 Pro': _T3, 'OPPO Find X5': _T3,
    'OPPO Reno 12 Pro': _T2, 'OPPO Reno 12': _T5,
    'OPPO Reno 11 Pro 5G': _T4, 'OPPO Reno 11': _T6,
    'OPPO Reno 10 Pro+ 5G': _T3, 'OPPO Reno 10 Pro 5G': _T5, 'OPPO Reno 10 5G': _T5,
    'OPPO Reno 9 Pro+': _T3, 'OPPO Reno 9': _T5,
    'OPPO Reno 8 Pro': _T4, 'OPPO Reno 8': _T6,
    'OPPO A79 5G': _T7, 'OPPO A78 5G': _T6, 'OPPO A58 5G': _T7,
    'OPPO A38': _T8, 'OPPO A18': _T8,
    'Realme GT 6 Pro': _T1, 'Realme GT 6': _T2,
    'Realme GT 5 Pro': _T1, 'Realme GT 5': _T2,
    'Realme GT 2 Pro': _T3, 'Realme GT 2': _T3, 'Realme GT Master Edition': _T5,
    'Realme 12 Pro+': _T5, 'Realme 12 Pro': _T6, 'Realme 12+': _T6, 'Realme 12': _T6,
    'Realme 11 Pro+ 5G': _T6, 'Realme 11 Pro': _T6, 'Realme 11': _T6,
    'Realme C65 5G': _T7, 'Realme C55': _T7, 'Realme C53': _T7, 'Realme C51': _T7, 'Realme C35': _T8,
    'Realme Narzo 70 Pro': _T6, 'Realme Narzo 60 Pro': _T6, 'Realme Narzo 50': _T7,
    # ── İNFİNİX ──
    'Infinix Zero 40 5G': _T4, 'Infinix Zero 40': _T6,
    'Infinix Zero 30 5G': _T5, 'Infinix Zero 30': _T6, 'Infinix Zero 20': _T6,
    'Infinix Note 40 Pro+ 5G': _T6, 'Infinix Note 40 Pro 5G': _T6,
    'Infinix Note 40 Pro': _T6, 'Infinix Note 40': _T6,
    'Infinix Note 30 Pro 5G': _T6, 'Infinix Note 30 VIP': _T6,
    'Infinix Note 30 5G': _T6, 'Infinix Note 30': _T6,
    'Infinix Note 12 Pro+': _T6, 'Infinix Note 12 Pro': _T7, 'Infinix Note 12 G96': _T7, 'Infinix Note 12 5G': _T7,
    'Infinix Hot 40 Pro': _T6, 'Infinix Hot 40': _T7, 'Infinix Hot 40i': _T8,
    'Infinix Hot 30 Play': _T8, 'Infinix Hot 30 5G': _T7, 'Infinix Hot 30': _T7,
    'Infinix Hot 20 Pro': _T7, 'Infinix Hot 20': _T8,
    'Infinix GT 20 Pro': _T4, 'Infinix GT 10 Pro': _T5,
    'Infinix Smart 8 Plus': _T8, 'Infinix Smart 8': _T8,
    # ── ONEPLUS ──
    'OnePlus 12R': _T2, 'OnePlus 12': _T1,
    'OnePlus 11R': _T3, 'OnePlus 11 5G': _T2,
    'OnePlus 10 Pro': _T3, 'OnePlus 10T 5G': _T3, 'OnePlus 10R': _T4,
    'OnePlus 9 Pro': _T3, 'OnePlus 9': _T3, 'OnePlus 9R': _T4,
    'OnePlus 8 Pro': _T4, 'OnePlus 8T': _T4, 'OnePlus 8': _T4,
    'OnePlus Open': _T2,
    'OnePlus Nord 4 5G': _T5, 'OnePlus Nord 3 5G': _T3,
    'OnePlus Nord 2T 5G': _T5, 'OnePlus Nord 2 5G': _T5,
    'OnePlus Nord CE 4': _T5, 'OnePlus Nord CE 3 Lite 5G': _T6, 'OnePlus Nord CE 3 5G': _T5,
    'OnePlus Nord CE 2 Lite 5G': _T6, 'OnePlus Nord CE 2 5G': _T6,
    'OnePlus Nord N30 5G': _T6, 'OnePlus Nord N20 5G': _T6,
    # ── VİVO ──
    'Vivo X100 Ultra': _T1, 'Vivo X100 Pro': _T2, 'Vivo X100+': _T1, 'Vivo X100': _T2,
    'Vivo X90 Pro+': _T2, 'Vivo X90 Pro': _T2, 'Vivo X90': _T2,
    'Vivo X80 Pro': _T3, 'Vivo X80': _T3,
    'Vivo V30 Pro': _T5, 'Vivo V30': _T5,
    'Vivo V29 Pro': _T5, 'Vivo V29': _T5,
    'Vivo V27 Pro': _T4, 'Vivo V27': _T5,
    'Vivo V25 Pro': _T5, 'Vivo V25': _T6,
    'Vivo Y200 Pro 5G': _T5, 'Vivo Y200 5G': _T8,
    'Vivo Y100 5G': _T6, 'Vivo Y100': _T6,
    'Vivo Y78 5G': _T6, 'Vivo Y78+': _T6,
    'Vivo Y56 5G': _T7, 'Vivo Y36 5G': _T8, 'Vivo Y36': _T7,
    'Vivo Y27s': _T8, 'Vivo Y27 5G': _T7, 'Vivo Y17s': _T8,
    # ── ASD ──
    'ASD X9 Pro': _T5, 'ASD X9': _T6, 'ASD X7 Pro': _T6,
    'ASD Note 12 Pro': _T7, 'ASD Note 12': _T7,
    'ASD P9 Pro': _T6, 'ASD P7': _T7, 'ASD S8': _T7, 'ASD S6': _T8,
    # ── NOKİA / MOTOROLA ──
    'Nokia G42 5G': _T8, 'Nokia G60 5G': _T6, 'Nokia G400 5G': _T8, 'Nokia G310 5G': _T8,
    'Nokia X30 5G': _T6, 'Nokia XR21': _T6, 'Nokia C32': _T8, 'Nokia C22': _T8,
    'Motorola Edge 50 Ultra': _T2, 'Motorola Edge 50 Pro': _T5, 'Motorola Edge 50 Fusion': _T5, 'Motorola Edge 50': _T5,
    'Motorola Edge 40 Neo': _T6, 'Motorola Edge 40 Pro': _T2, 'Motorola Edge 40': _T5,
    'Motorola Edge 30 Ultra': _T3, 'Motorola Edge 30 Pro': _T3, 'Motorola Edge 30': _T5,
    'Motorola Moto G85 5G': _T6, 'Motorola Moto G84 5G': _T6, 'Motorola Moto G73 5G': _T6,
    'Motorola Moto G54 5G': _T6, 'Motorola Moto G34 5G': _T6,
    'Motorola Moto G24': _T8, 'Motorola Moto G14': _T8, 'Motorola Moto G62 5G': _T6,
    # ── GAMİNG TELEFONLAR ──
    'ASUS ROG Phone 8 Pro': _GAM_T1, 'ASUS ROG Phone 8': _GAM_T1,
    'ASUS ROG Phone 7 Pro': _GAM_T1, 'ASUS ROG Phone 7 Ultimate': _GAM_T1, 'ASUS ROG Phone 7': _GAM_T1,
    'ASUS ROG Phone 6 Pro': _GAM_T3, 'ASUS ROG Phone 6': _GAM_T3,
    'Nubia RedMagic 9 Pro+': _GAM_T1, 'Nubia RedMagic 9 Pro': _GAM_T1, 'Nubia RedMagic 9S': _GAM_T1,
    'Nubia RedMagic 8 Pro+': _GAM_T1, 'Nubia RedMagic 8 Pro': _GAM_T1, 'Nubia RedMagic 8S Pro': _GAM_T1,
    'Nubia RedMagic 7 Pro': _GAM_T3, 'Nubia RedMagic 7': _GAM_T3,
    'Xiaomi Black Shark 5 Pro': _T3, 'Xiaomi Black Shark 5': _T4,
    'Lenovo Legion Phone 3 Pro': _T3, 'Lenovo Legion Phone 2 Pro': _T3,
    # ── SONY ──
    'Sony Xperia 1 VI': _T1, 'Sony Xperia 1 V': _T2, 'Sony Xperia 1 IV': _T3, 'Sony Xperia 1 III': _T3,
    'Sony Xperia 5 VI': _T1, 'Sony Xperia 5 V': _T2, 'Sony Xperia 5 IV': _T3, 'Sony Xperia 5 III': _T3,
    'Sony Xperia 10 VI': _T6, 'Sony Xperia 10 V': _T6, 'Sony Xperia 10 IV': _T6, 'Sony Xperia 10 III': _T6,
    'Sony Xperia Pro-I': _T3, 'Sony Xperia Pro': _T3,
    'Sony Xperia L4': _T8, 'Sony Xperia Ace III': _T8,
    # ── ZTE / NUBİA ──
    'ZTE Blade V60 Design': _T7, 'ZTE Blade V50 Design': _T8, 'ZTE Blade V50 Vita': _T8,
    'ZTE Blade A75 5G': _T7, 'ZTE Blade A75': _T8, 'ZTE Blade A54': _T8, 'ZTE Blade A34': _T8, 'ZTE Blade A73 5G': _T7,
    'Nubia Z60 Ultra': _T1, 'Nubia Z50S Pro': _T2, 'Nubia Z50 Ultra': _T2, 'Nubia Z50': _T2,
    'Nubia Focus 5G': _T6, 'Nubia Neo 5G': _T6, 'Nubia Music': _T8,
    # ── LAVA ──
    'Lava Agni 3 5G': _T6, 'Lava Agni 2 5G': _T6, 'Lava Agni 1 5G': _T7,
    'Lava Blaze 2 5G': _T7, 'Lava Blaze Curve 5G': _T6, 'Lava Blaze 5G': _T7,
    'Lava Storm 5G': _T5, 'Lava O2 5G': _T7, 'Lava X3 5G': _T7,
    'Lava Yuva 3 Pro': _T8, 'Lava Yuva 2 Pro': _T8,
    # ── SHARP / MEİZU ──
    'Sharp AQUOS R9': _T5, 'Sharp AQUOS R8 Pro': _T2, 'Sharp AQUOS R8': _T2,
    'Sharp AQUOS R7': _T3, 'Sharp AQUOS sense8': _T6, 'Sharp AQUOS sense7': _T6,
    'Sharp AQUOS wish3': _T6, 'Sharp AQUOS zero6': _T6,
    'Meizu 21 Pro': _T1, 'Meizu 21': _T2, 'Meizu 21 Note': _T2,
    'Meizu 20 Pro': _T2, 'Meizu 20': _T2, 'Meizu 20 Infinity': _T2,
    'Meizu Note 21 Pro': _T5, 'Meizu Note 21': _T8, 'Meizu Blue Note 21S': _T6,
    # ── DOOGEE / ULEFONE ──
    'Doogee V Max Pro': _T6, 'Doogee V Max': _T5, 'Doogee V30 Pro': _T5, 'Doogee V30': _T6, 'Doogee V20 Pro': _T5,
    'Doogee S100 Pro': _T5, 'Doogee S100': _T5, 'Doogee S98 Pro': _T7, 'Doogee S98': _T7,
    'Doogee N55 Pro': _T6, 'Doogee N40 Pro': _T8, 'Doogee X98 Pro': _T8, 'Doogee X98': _T8,
    'Ulefone Power Armor 23 Ultra': _T6, 'Ulefone Power Armor 23': _T6, 'Ulefone Power Armor 19T': _T6,
    'Ulefone Armor 23 Ultra': _T6, 'Ulefone Armor 21': _T6, 'Ulefone Armor 20WT': _T6,
    'Ulefone Note 17 Pro': _T6, 'Ulefone Note 16 Pro': _T8,
}

# ─────────────────────────────────────────────────────────────
# 💰 GÜRCİSTAN TELEFON FİYAT VERİTABANI (₾ GEL) — Zoommer.ge / Alta.ge / MyMarket.ge
# ─────────────────────────────────────────────────────────────
FIYAT_GE_DB = {
    # Samsung Galaxy S25 Serisi (2025 — Yeni)
    'Samsung Galaxy S25 Ultra': '4 499 ₾', 'Samsung Galaxy S25+': '3 499 ₾', 'Samsung Galaxy S25': '2 799 ₾', 'Samsung Galaxy S25 Edge': '3 799 ₾',
    # Samsung Galaxy S Serisi
    'Samsung Galaxy S24 Ultra': '3 899 ₾', 'Samsung Galaxy S24+': '3 199 ₾', 'Samsung Galaxy S24': '2 599 ₾', 'Samsung Galaxy S24 FE': '1 899 ₾',
    'Samsung Galaxy S23 Ultra': '3 199 ₾', 'Samsung Galaxy S23+': '2 499 ₾', 'Samsung Galaxy S23': '1 999 ₾', 'Samsung Galaxy S23 FE': '1 499 ₾',
    'Samsung Galaxy S22 Ultra': '2 499 ₾', 'Samsung Galaxy S22+': '1 999 ₾', 'Samsung Galaxy S22': '1 599 ₾',
    'Samsung Galaxy S21 Ultra': '1 899 ₾', 'Samsung Galaxy S21+': '1 499 ₾', 'Samsung Galaxy S21': '1 199 ₾', 'Samsung Galaxy S21 FE': '899 ₾',
    'Samsung Galaxy S20 Ultra': '1 399 ₾', 'Samsung Galaxy S20+': '1 099 ₾', 'Samsung Galaxy S20': '899 ₾', 'Samsung Galaxy S20 FE': '749 ₾',
    'Samsung Galaxy S10+': '799 ₾', 'Samsung Galaxy S10': '699 ₾', 'Samsung Galaxy S10e': '599 ₾', 'Samsung Galaxy S10 5G': '849 ₾',
    # Samsung Galaxy Note
    'Samsung Galaxy Note 20 Ultra': '1 799 ₾', 'Samsung Galaxy Note 20': '1 299 ₾',
    'Samsung Galaxy Note 10+': '1 099 ₾', 'Samsung Galaxy Note 10': '899 ₾', 'Samsung Galaxy Note 10 Lite': '699 ₾',
    # Samsung Galaxy Z
    'Samsung Galaxy Z Fold 6': '5 999 ₾', 'Samsung Galaxy Z Fold 5': '4 999 ₾', 'Samsung Galaxy Z Fold 4': '3 999 ₾', 'Samsung Galaxy Z Fold 3': '2 999 ₾',
    'Samsung Galaxy Z Flip 6': '3 499 ₾', 'Samsung Galaxy Z Flip 5': '2 799 ₾', 'Samsung Galaxy Z Flip 4': '2 199 ₾', 'Samsung Galaxy Z Flip 3': '1 699 ₾',
    # Samsung Galaxy A
    'Samsung Galaxy A55 5G': '1 299 ₾', 'Samsung Galaxy A54 5G': '1 099 ₾', 'Samsung Galaxy A53 5G': '899 ₾', 'Samsung Galaxy A52s 5G': '799 ₾', 'Samsung Galaxy A52': '699 ₾',
    'Samsung Galaxy A35 5G': '999 ₾', 'Samsung Galaxy A34 5G': '849 ₾', 'Samsung Galaxy A33 5G': '749 ₾', 'Samsung Galaxy A32': '599 ₾', 'Samsung Galaxy A32 5G': '649 ₾',
    'Samsung Galaxy A25 5G': '749 ₾', 'Samsung Galaxy A24': '599 ₾', 'Samsung Galaxy A23 5G': '649 ₾', 'Samsung Galaxy A23': '549 ₾', 'Samsung Galaxy A22 5G': '549 ₾', 'Samsung Galaxy A22': '499 ₾',
    'Samsung Galaxy A15 5G': '549 ₾', 'Samsung Galaxy A15': '499 ₾', 'Samsung Galaxy A14 5G': '499 ₾', 'Samsung Galaxy A14': '449 ₾', 'Samsung Galaxy A13': '399 ₾', 'Samsung Galaxy A13 5G': '449 ₾',
    'Samsung Galaxy A05s': '379 ₾', 'Samsung Galaxy A05': '349 ₾', 'Samsung Galaxy A04s': '299 ₾', 'Samsung Galaxy A03s': '249 ₾', 'Samsung Galaxy A03': '229 ₾',
    # Samsung Galaxy A Serisi (2025 — Yeni)
    'Samsung Galaxy A56 5G': '1 399 ₾', 'Samsung Galaxy A36 5G': '1 099 ₾', 'Samsung Galaxy A26 5G': '849 ₾', 'Samsung Galaxy A16 5G': '599 ₾', 'Samsung Galaxy A06': '299 ₾',
    # Samsung Galaxy F Serisi
    'Samsung Galaxy F55 5G': '999 ₾', 'Samsung Galaxy F35 5G': '749 ₾', 'Samsung Galaxy F15 5G': '499 ₾',
    # Samsung Galaxy M (2025)
    'Samsung Galaxy M55 5G': '1 099 ₾', 'Samsung Galaxy M35 5G': '849 ₾',
    # Samsung Galaxy M
    'Samsung Galaxy M54 5G': '999 ₾', 'Samsung Galaxy M53 5G': '849 ₾', 'Samsung Galaxy M34 5G': '749 ₾', 'Samsung Galaxy M33 5G': '649 ₾', 'Samsung Galaxy M14 5G': '499 ₾',
    # iPhone 16 Serisi (2024 — Yeni)
    'iPhone 16 Pro Max': '4 999 ₾', 'iPhone 16 Pro': '4 399 ₾', 'iPhone 16 Plus': '3 699 ₾', 'iPhone 16': '3 199 ₾', 'iPhone 16e': '2 299 ₾',
    # iPhone
    'iPhone 15 Pro Max': '4 299 ₾', 'iPhone 15 Pro': '3 699 ₾', 'iPhone 15 Plus': '3 199 ₾', 'iPhone 15': '2 699 ₾',
    'iPhone 14 Pro Max': '3 699 ₾', 'iPhone 14 Pro': '3 199 ₾', 'iPhone 14 Plus': '2 699 ₾', 'iPhone 14': '2 299 ₾',
    'iPhone 13 Pro Max': '2 999 ₾', 'iPhone 13 Pro': '2 499 ₾', 'iPhone 13 mini': '1 599 ₾', 'iPhone 13': '1 899 ₾',
    'iPhone 12 Pro Max': '2 199 ₾', 'iPhone 12 Pro': '1 899 ₾', 'iPhone 12 mini': '1 299 ₾', 'iPhone 12': '1 499 ₾',
    'iPhone 11 Pro Max': '1 699 ₾', 'iPhone 11 Pro': '1 399 ₾', 'iPhone 11': '1 099 ₾',
    'iPhone XS Max': '899 ₾', 'iPhone XS': '799 ₾', 'iPhone XR': '699 ₾', 'iPhone X': '599 ₾',
    'iPhone SE (2022)': '999 ₾', 'iPhone SE (2020)': '799 ₾',
    # Xiaomi 15 Serisi (2025 — Yeni)
    'Xiaomi 15 Ultra': '3 999 ₾', 'Xiaomi 15 Pro': '3 299 ₾', 'Xiaomi 15': '2 699 ₾',
    # Xiaomi
    'Xiaomi 14 Ultra': '3 499 ₾', 'Xiaomi 14 Pro': '2 899 ₾', 'Xiaomi 14': '2 299 ₾', 'Xiaomi 14T Pro': '2 099 ₾', 'Xiaomi 14T': '1 799 ₾', 'Xiaomi 14C': '849 ₾',
    'Xiaomi 13 Ultra': '2 799 ₾', 'Xiaomi 13 Pro': '2 299 ₾', 'Xiaomi 13': '1 899 ₾', 'Xiaomi 13T Pro': '1 799 ₾', 'Xiaomi 13T': '1 499 ₾',
    'Xiaomi 12 Pro': '1 799 ₾', 'Xiaomi 12': '1 499 ₾', 'Xiaomi 12T Pro': '1 599 ₾', 'Xiaomi 12T': '1 299 ₾',
    'Xiaomi 11 Ultra': '1 699 ₾', 'Xiaomi 11 Pro': '1 399 ₾', 'Xiaomi 11': '1 099 ₾', 'Xiaomi 11T Pro': '1 199 ₾', 'Xiaomi 11T': '999 ₾',
    # Redmi Note 14 Serisi (2025 — Yeni)
    'Redmi Note 14 Pro+ 5G': '1 199 ₾', 'Redmi Note 14 Pro 5G': '999 ₾', 'Redmi Note 14 Pro': '949 ₾', 'Redmi Note 14 5G': '799 ₾', 'Redmi Note 14': '699 ₾',
    # Redmi Note 14C
    'Redmi 14C': '449 ₾', 'Redmi 14 5G': '549 ₾',
    # Redmi Note
    'Redmi Note 13 Pro+ 5G': '1 099 ₾', 'Redmi Note 13 Pro 5G': '899 ₾', 'Redmi Note 13 5G': '749 ₾', 'Redmi Note 13': '649 ₾', 'Redmi Note 13 Pro': '849 ₾',
    'Redmi Note 12 Pro+ 5G': '949 ₾', 'Redmi Note 12 Pro 5G': '799 ₾', 'Redmi Note 12 5G': '649 ₾', 'Redmi Note 12': '549 ₾', 'Redmi Note 12s': '599 ₾',
    'Redmi Note 11 Pro+ 5G': '799 ₾', 'Redmi Note 11 Pro': '649 ₾', 'Redmi Note 11S': '499 ₾', 'Redmi Note 11': '449 ₾', 'Redmi Note 11 5G': '499 ₾',
    'Redmi Note 10 Pro': '549 ₾', 'Redmi Note 10': '399 ₾', 'Redmi Note 10s': '449 ₾', 'Redmi Note 10 5G': '449 ₾',
    # Redmi
    'Redmi 13C 5G': '499 ₾', 'Redmi 13C': '399 ₾', 'Redmi 13': '449 ₾', 'Redmi 12C': '349 ₾', 'Redmi 12': '449 ₾', 'Redmi 12 5G': '499 ₾',
    'Redmi 10C': '329 ₾', 'Redmi 10': '379 ₾', 'Redmi A3': '299 ₾', 'Redmi A2+': '279 ₾', 'Redmi A2': '249 ₾',
    # POCO X7 Serisi (2025 — Yeni)
    'POCO X7 Pro 5G': '1 199 ₾', 'POCO X7 5G': '999 ₾',
    # POCO C75 (Yeni)
    'POCO C75': '399 ₾',
    # POCO
    'POCO X6 Pro 5G': '999 ₾', 'POCO X6 5G': '849 ₾', 'POCO X5 Pro 5G': '799 ₾', 'POCO X5 5G': '649 ₾',
    'POCO X4 Pro 5G': '699 ₾', 'POCO X3 Pro': '549 ₾', 'POCO X3 NFC': '449 ₾',
    'POCO F6 Pro': '1 499 ₾', 'POCO F6 5G': '1 299 ₾', 'POCO F5 Pro 5G': '1 199 ₾', 'POCO F5 5G': '999 ₾', 'POCO F4 GT': '999 ₾', 'POCO F4 5G': '849 ₾', 'POCO F3': '699 ₾',
    'POCO M6 Pro 5G': '649 ₾', 'POCO M5s': '449 ₾', 'POCO M5': '399 ₾', 'POCO M4 Pro 5G': '549 ₾', 'POCO M4 Pro': '499 ₾',
    'POCO C65': '349 ₾', 'POCO C55': '299 ₾',
    # Google Pixel
    'Pixel 9 Pro XL': '3 799 ₾', 'Pixel 9 Pro': '3 299 ₾', 'Pixel 9': '2 799 ₾', 'Pixel 9 Pro Fold': '5 499 ₾',
    'Pixel 9a': '1 999 ₾',
    'Pixel 8 Pro': '2 999 ₾', 'Pixel 8': '2 299 ₾', 'Pixel 8a': '1 799 ₾',
    'Pixel 7 Pro': '2 199 ₾', 'Pixel 7': '1 699 ₾', 'Pixel 7a': '1 399 ₾',
    'Pixel 6 Pro': '1 599 ₾', 'Pixel 6': '1 199 ₾', 'Pixel 6a': '899 ₾',
    # OnePlus 13 Serisi (2025 — Yeni)
    'OnePlus 13': '2 999 ₾', 'OnePlus 13R': '2 199 ₾',
    # OnePlus
    'OnePlus 12R': '1 999 ₾', 'OnePlus 12': '2 499 ₾', 'OnePlus 11 5G': '1 999 ₾', 'OnePlus 10 Pro': '1 699 ₾', 'OnePlus 10T 5G': '1 499 ₾',
    'OnePlus Nord 4 5G': '1 299 ₾', 'OnePlus Nord 3 5G': '1 099 ₾', 'OnePlus Nord 2T 5G': '849 ₾',
    'OnePlus Nord CE 4': '999 ₾', 'OnePlus Nord CE 3 Lite 5G': '699 ₾', 'OnePlus Nord CE 3 5G': '849 ₾',
    # Vivo
    'Vivo X100 Ultra': '3 299 ₾', 'Vivo X100 Pro': '2 799 ₾', 'Vivo X100': '2 299 ₾',
    'Vivo V30 Pro': '1 499 ₾', 'Vivo V30': '1 199 ₾', 'Vivo V29 Pro': '1 299 ₾', 'Vivo V29': '999 ₾',
    'Vivo V27 Pro': '1 099 ₾', 'Vivo V27': '849 ₾', 'Vivo Y200 Pro 5G': '799 ₾', 'Vivo Y200 5G': '699 ₾',
    # OPPO / Realme
    'OPPO Find X7 Ultra': '3 499 ₾', 'OPPO Find X7 Pro': '2 899 ₾', 'OPPO Reno 12 Pro': '1 499 ₾', 'OPPO Reno 12': '1 199 ₾',
    'Realme GT 6 Pro': '1 799 ₾', 'Realme GT 6': '1 499 ₾', 'Realme GT 5 Pro': '1 499 ₾',
    'Realme 12 Pro+': '1 199 ₾', 'Realme 12 Pro': '999 ₾', 'Realme 12': '799 ₾',
    'Realme 11 Pro+ 5G': '1 099 ₾', 'Realme 11 Pro': '849 ₾', 'Realme 11': '649 ₾',
    'Realme C65 5G': '499 ₾', 'Realme C55': '449 ₾', 'Realme C53': '399 ₾',
    # Tecno
    'Tecno Camon 30 Premier 5G': '1 199 ₾', 'Tecno Camon 30 Pro 5G': '999 ₾', 'Tecno Camon 30 5G': '799 ₾', 'Tecno Camon 30': '649 ₾',
    'Tecno Camon 20 Premier 5G': '999 ₾', 'Tecno Camon 20 Pro 5G': '799 ₾', 'Tecno Camon 20': '549 ₾',
    'Tecno Spark 20 Pro+': '599 ₾', 'Tecno Spark 20 Pro': '499 ₾', 'Tecno Spark 20': '399 ₾',
    'Tecno Pova 6 Pro 5G': '799 ₾', 'Tecno Pova 6 5G': '649 ₾',
    # Honor
    'Honor Magic6 Pro': '2 299 ₾', 'Honor Magic6': '1 799 ₾', 'Honor Magic6 Lite': '999 ₾',
    'Honor Magic5 Pro': '1 999 ₾', 'Honor Magic5 Lite': '799 ₾',
    'Honor 200 Pro': '1 799 ₾', 'Honor 200': '1 399 ₾', 'Honor 200 Lite': '849 ₾',
    'Honor 90 Pro': '1 299 ₾', 'Honor 90': '999 ₾', 'Honor 90 Lite': '649 ₾',
    'Honor X9b 5G': '849 ₾', 'Honor X8b': '699 ₾', 'Honor X7b': '549 ₾',
    # Infinix
    'Infinix Zero 40 5G': '899 ₾', 'Infinix Zero 40': '749 ₾', 'Infinix Zero 30 5G': '799 ₾', 'Infinix Zero 30': '649 ₾',
    'Infinix Note 40 Pro+ 5G': '849 ₾', 'Infinix Note 40 Pro 5G': '699 ₾', 'Infinix Note 40 Pro': '599 ₾', 'Infinix Note 40': '499 ₾',
    'Infinix Note 30 Pro 5G': '749 ₾', 'Infinix Note 30 5G': '599 ₾', 'Infinix Note 30': '449 ₾',
    'Infinix Hot 40 Pro': '499 ₾', 'Infinix Hot 40': '399 ₾', 'Infinix Hot 40i': '349 ₾',
    'Infinix GT 20 Pro': '749 ₾', 'Infinix GT 10 Pro': '599 ₾',
    # Huawei
    'Huawei Mate 60 Pro+': '3 299 ₾', 'Huawei Mate 60 Pro': '2 799 ₾', 'Huawei Mate 60': '2 299 ₾',
    'Huawei Mate 50 Pro': '2 199 ₾', 'Huawei Mate 50': '1 699 ₾',
    'Huawei P60 Pro': '2 099 ₾', 'Huawei P60': '1 699 ₾',
    'Huawei P50 Pro': '1 799 ₾', 'Huawei P50': '1 399 ₾', 'Huawei P50 Pocket': '1 999 ₾',
    'Huawei Nova 12 Pro': '1 299 ₾', 'Huawei Nova 12': '999 ₾', 'Huawei Nova 11 Pro': '1 099 ₾', 'Huawei Nova 11': '849 ₾',
    # Gaming
    'ASUS ROG Phone 8 Pro': '3 799 ₾', 'ASUS ROG Phone 8': '3 199 ₾', 'ASUS ROG Phone 7 Pro': '2 799 ₾', 'ASUS ROG Phone 7': '2 299 ₾',
    'Nubia RedMagic 9 Pro+': '2 999 ₾', 'Nubia RedMagic 9 Pro': '2 499 ₾', 'Nubia RedMagic 8 Pro': '1 999 ₾',
    # Motorola
    'Motorola Edge 50 Ultra': '2 299 ₾', 'Motorola Edge 50 Pro': '1 799 ₾', 'Motorola Edge 50 Fusion': '1 299 ₾', 'Motorola Edge 50': '1 099 ₾',
    'Motorola Edge 40 Pro': '1 599 ₾', 'Motorola Edge 40': '1 099 ₾',
    'Motorola Moto G85 5G': '749 ₾', 'Motorola Moto G84 5G': '649 ₾', 'Motorola Moto G54 5G': '549 ₾', 'Motorola Moto G34 5G': '449 ₾',
    # Sony
    'Sony Xperia 1 VI': '3 199 ₾', 'Sony Xperia 1 V': '2 699 ₾', 'Sony Xperia 5 V': '2 199 ₾', 'Sony Xperia 5 IV': '1 699 ₾',
    'Sony Xperia 10 VI': '1 299 ₾', 'Sony Xperia 10 V': '999 ₾',
}

async def _tfn_sayfa_goster(query, context, mid: str, sayfa: int):
    """Marka model listesini sayfalı gösterir (8/sayfa)."""
    if mid not in TELEFON_VERITABANI:
        await query.answer("❌ Marka bulunamadı", show_alert=True)
        return
    mdata = TELEFON_VERITABANI[mid]
    modeller = mdata['modeller']
    toplam = len(modeller)
    sayfa_boyutu = 8
    toplam_sayfa = max(1, math.ceil(toplam / sayfa_boyutu))
    sayfa = max(0, min(sayfa, toplam_sayfa - 1))
    baslangic = sayfa * sayfa_boyutu
    bitis = min(baslangic + sayfa_boyutu, toplam)
    sayfa_modeller = modeller[baslangic:bitis]

    satir = []
    for i, model in enumerate(sayfa_modeller):
        gercek_idx = baslangic + i
        satir.append([InlineKeyboardButton(f"📱 {model}", callback_data=f'tfn_s_{gercek_idx}')])

    nav = []
    if sayfa > 0:
        nav.append(InlineKeyboardButton("⬅️ Önceki", callback_data=f'tfn_p_{mid}_{sayfa - 1}'))
    if sayfa < toplam_sayfa - 1:
        nav.append(InlineKeyboardButton("Sonraki ➡️", callback_data=f'tfn_p_{mid}_{sayfa + 1}'))
    if nav:
        satir.append(nav)
    satir.append([InlineKeyboardButton("📱 Tüm Markalar", callback_data='menu_telefon_fiyatlari')])

    await query.edit_message_text(
        f"{mdata['emoji']} **{mdata['ad']} — Model Listesi**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 Sayfa {sayfa + 1}/{toplam_sayfa} · Toplam {toplam} model\n\n"
        f"Bir model seçin:",
        reply_markup=InlineKeyboardMarkup(satir),
        parse_mode='Markdown'
    )


def fiyat_getir(telefon_adi: str, marka_adi: str = '') -> str:
    """Gürcistan telefon fiyat veritabanından fiyat getirir."""
    # Direkt arama
    if telefon_adi in FIYAT_GE_DB:
        return f"💰 **{FIYAT_GE_DB[telefon_adi]}** _(Gürcistan piyasası)_"
    # Marka adıyla birleşik arama
    tam = f"{marka_adi} {telefon_adi}".strip()
    if tam in FIYAT_GE_DB:
        return f"💰 **{FIYAT_GE_DB[tam]}** _(Gürcistan piyasası)_"
    # Kısmi eşleşme
    for k, v in FIYAT_GE_DB.items():
        if telefon_adi.lower() in k.lower() or k.lower() in telefon_adi.lower():
            return f"💰 **{v}** _(Gürcistan piyasası — yaklaşık)_"
    sorgu = urllib.parse.quote(telefon_adi)
    return (
        f"💰 **Fiyat bilgisi mevcut değil**\n"
        f"🔍 [Zoommer.ge]({f'https://zoommer.ge/search?q={sorgu}'}) · "
        f"[Alta.ge]({f'https://alta.ge/search?term={sorgu}'}) · "
        f"[MyMarket.ge]({f'https://www.mymarket.ge/en/search/?query={sorgu}'})"
    )


async def log_kanali_gonder(bot, update, ek_bilgi: str = "", kategori: str = "", komut: str = ""):
    try:
        user = update.effective_user
        msg  = update.effective_message
        chat = update.effective_chat
        if not user or not msg:
            return

        # ── Kullanıcı Bilgileri ──
        ad   = html.escape(user.full_name or "—")
        uid  = user.id
        tiklanabilir_ad = f'<a href="tg://user?id={uid}">{ad}</a>'
        kullanici_bilgi = f'@{html.escape(user.username)}' if user.username else f'<code>{uid}</code>'
        dil_kodu  = user.language_code or "—"
        is_bot    = "🤖 Evet" if user.is_bot else "👤 Hayır"
        is_premium = "💎 Evet" if getattr(user, 'is_premium', False) else "—"

        # ── Sohbet / Chat Bilgileri ──
        chat_id   = chat.id if chat else "—"
        chat_tip  = chat.type if chat else "—"
        chat_tip_emoji = {"private": "💬", "group": "👥", "supergroup": "👥", "channel": "📢"}.get(chat_tip, "❓")
        chat_adi  = html.escape(chat.title or chat.full_name or "—") if chat else "—"

        # ── Mesaj Meta ──
        msg_id    = msg.message_id
        zaman     = datetime.datetime.now(TR_SAAT).strftime('%d.%m.%Y %H:%M:%S')

        # ── Log Metni ──
        log_metin = (
            f"🔔 <b>YENİ AKTİVİTE — AZRxGUARD</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Ad:</b> {tiklanabilir_ad}\n"
            f"🆔 <b>ID:</b> <code>{uid}</code>\n"
            f"📱 <b>Kullanıcı:</b> {kullanici_bilgi}\n"
            f"🌐 <b>Dil:</b> <code>{dil_kodu}</code>  |  🤖 Bot: {is_bot}  |  💎 Premium: {is_premium}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{chat_tip_emoji} <b>Sohbet:</b> {chat_adi}\n"
            f"🏠 <b>Chat ID:</b> <code>{chat_id}</code>  |  <b>Tip:</b> {chat_tip}\n"
            f"📩 <b>Mesaj ID:</b> <code>{msg_id}</code>\n"
        )

        if kategori:
            log_metin += f"🗂️ <b>Kategori:</b> {html.escape(str(kategori))}\n"
        if komut:
            log_metin += f"⚡ <b>Komut:</b> <code>{html.escape(str(komut))}</code>\n"

        # Alıntı / Yanıtlanan mesaj
        if msg.reply_to_message:
            r = msg.reply_to_message
            ruid = r.from_user.id if r.from_user else "?"
            rname = html.escape(r.from_user.full_name or "?") if r.from_user else "?"
            log_metin += f"↩️ <b>Yanıtladığı:</b> <a href='tg://user?id={ruid}'>{rname}</a> (msg: <code>{r.message_id}</code>)\n"

        # İletilen mesaj bilgisi (PTB v22 — forward_origin kullanır)
        if msg.forward_origin:
            fo = msg.forward_origin
            if hasattr(fo, 'sender_user') and fo.sender_user:
                ff_id   = fo.sender_user.id
                ff_name = html.escape(fo.sender_user.full_name or '?')
                log_metin += f"🔁 <b>İletilen:</b> <a href='tg://user?id={ff_id}'>{ff_name}</a>\n"
            elif hasattr(fo, 'sender_user_name') and fo.sender_user_name:
                log_metin += f"🔁 <b>İletilen:</b> {html.escape(fo.sender_user_name)} (gizli kullanıcı)\n"
            elif hasattr(fo, 'chat') and fo.chat:
                log_metin += f"🔁 <b>İletilen Kanal:</b> {html.escape(fo.chat.title or '?')} (<code>{fo.chat.id}</code>)\n"
            elif hasattr(fo, 'broadcaster_user') and fo.broadcaster_user:
                ff_id   = fo.broadcaster_user.id
                ff_name = html.escape(fo.broadcaster_user.full_name or '?')
                log_metin += f"🔁 <b>İletilen Kanal:</b> <a href='tg://user?id={ff_id}'>{ff_name}</a>\n"

        # Medya tipi
        medya_tipler = []
        if msg.photo: medya_tipler.append("📷 Fotoğraf")
        if msg.video: medya_tipler.append("🎬 Video")
        if msg.document: medya_tipler.append(f"📄 Dosya ({html.escape(msg.document.file_name or '?')})")
        if msg.voice: medya_tipler.append("🎙️ Ses Notu")
        if msg.audio: medya_tipler.append("🎵 Ses")
        if msg.sticker: medya_tipler.append(f"🎭 Sticker ({msg.sticker.emoji or '?'})")
        if msg.animation: medya_tipler.append("🖼️ GIF")
        if msg.video_note: medya_tipler.append("📹 Video Not")
        if msg.location: medya_tipler.append("📍 Konum")
        if msg.contact: medya_tipler.append("👤 Kişi")
        if msg.poll: medya_tipler.append("📊 Anket")
        if medya_tipler:
            log_metin += f"📦 <b>Medya:</b> {', '.join(medya_tipler)}\n"

        # Mesaj içeriği — sınırsız
        if ek_bilgi:
            ek_str = html.escape(str(ek_bilgi))
            # Telegram mesaj limiti 4096, büyük içerikleri böl
            log_metin += f"📝 <b>Bilgi:</b> {ek_str[:3800]}\n"
            if len(ek_str) > 3800:
                log_metin += f"   <i>... ({len(ek_str)} karakter toplam)</i>\n"
        if msg.text and not komut:
            metin_str = html.escape(msg.text)
            log_metin += f"💬 <b>Mesaj ({len(msg.text)} kr):</b> {metin_str[:3000]}\n"
            if len(msg.text) > 3000:
                log_metin += f"   <i>... ({len(msg.text)} karakter toplam, kesildi)</i>\n"
        if msg.caption:
            log_metin += f"📝 <b>Açıklama:</b> {html.escape(msg.caption[:1000])}\n"

        log_metin += f"⏰ <b>Zaman:</b> {zaman}"

        # Log kanalına gönder (Telegram 4096 karakter limiti)
        if len(log_metin) > 4096:
            log_metin = log_metin[:4090] + "\n[...]"
        await bot.send_message(LOG_KANAL_ID, log_metin, parse_mode='HTML', disable_web_page_preview=True)

        # Medya içeren mesajları ilet
        if msg.photo or msg.video or msg.document or msg.voice or msg.audio or msg.sticker or msg.animation or msg.video_note:
            try:
                await bot.forward_message(LOG_KANAL_ID, msg.chat_id, msg.message_id)
            except Exception:
                pass

        # Dosya logu — tam içerik sınırsız
        logger.debug(
            f"LOG | uid={uid} | chat={chat_id} | tip={chat_tip} | "
            f"komut={komut or '—'} | kategori={kategori or '—'} | "
            f"bilgi={str(ek_bilgi)[:200] if ek_bilgi else '—'}"
        )

    except Exception as e:
        logger.warning(f"Log kanalı hatası: {e}")


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

def guvenli_hesapla(ifade: str, lang: str = 'tr') -> str:
    L = LANG_DATA.get(lang, LANG_DATA['tr'])
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
            f"🧮 **{L.get('out_hesap_title','HESAP MAKİNESİ')}**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 **{L.get('out_hesap_ifade','İfade')}:** `{html.escape(ifade)}`\n"
            f"📤 **{L.get('out_hesap_sonuc','Sonuç')}:** `{sonuc_str}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _sin, cos, sqrt, log, pi, e, factorial_"
        )
    except ZeroDivisionError:
        return "❌ **Sıfıra bölme hatası!**"
    except (ValueError, OverflowError) as e:
        return f"❌ **Matematiksel hata:** `{str(e)[:80]}`"
    except Exception:
        return "❌ **Geçersiz ifade!** Örnek: `2**10` veya `sqrt(144)` veya `sin(pi/2)`"

def hash_uret(metin: str, lang: str = 'tr') -> str:
    L = LANG_DATA.get(lang, LANG_DATA['tr'])
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
        f"🔐 **{L.get('out_hash_title','HASH ÜRETİCİ')}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 **{L.get('out_hash_metin','Metin')}:** `{html.escape(ozet)}`\n"
        f"📊 **{L.get('out_hash_uzunluk','Uzunluk')}:** `{len(metin)} {L.get('out_hash_karakter','karakter')}`\n\n"
        f"🔸 **MD5:**\n`{md5_h}`\n\n"
        f"🔸 **SHA-1:**\n`{sha1_h}`\n\n"
        f"🔸 **SHA-256:**\n`{sha256_h}`\n\n"
        f"🔸 **SHA-512:**\n`{sha512_h}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _AZRxGUARD Hash Engine_"
    )

def base64_islem(metin: str, lang: str = 'tr') -> str:
    L = LANG_DATA.get(lang, LANG_DATA['tr'])
    metin = metin.strip()
    parts = metin.split(None, 1)
    if len(parts) < 2:
        return "❌ **Format:** `encode metin` veya `decode bWV0aW4=`"
    mod, icerik = parts[0].lower(), parts[1]
    try:
        if mod in ('encode', 'enc', 'e'):
            sonuc = b64lib.b64encode(icerik.encode('utf-8')).decode('ascii')
            return (
                f"🔒 **{L.get('out_b64_enc','BASE64 ENCODE')}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📥 **{L.get('out_b64_giris','Giriş')}:** `{html.escape(icerik[:100])}`\n\n"
                f"📤 **{L.get('out_b64_sonuc','Sonuç')}:**\n`{sonuc}`"
            )
        elif mod in ('decode', 'dec', 'd'):
            padding = 4 - len(icerik) % 4
            if padding != 4:
                icerik += '=' * padding
            sonuc = b64lib.b64decode(icerik).decode('utf-8', errors='replace')
            return (
                f"🔓 **{L.get('out_b64_dec','BASE64 DECODE')}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📥 **{L.get('out_b64_giris','Giriş')}:** `{icerik[:80]}`\n\n"
                f"📤 **{L.get('out_b64_sonuc','Sonuç')}:**\n`{html.escape(sonuc[:500])}`"
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
    "💡 _\"Tumca da tumca — gürcü kalbinde yer tutar.\"_\n— Gürcü Atasözü",
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
    "💡 _\"Işığa giden yol, önce karanlıktan geçer.\"_\n— Gürcü Atasözü",
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

async def hava_durumu_getir(sehir: str, lang: str = 'tr') -> str:
    L = LANG_DATA.get(lang, LANG_DATA['tr'])
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
        loc = sehir.strip() + (f", {country}" if country else "")
        return (
            f"{icon} **{L.get('out_hava_title','HAVA DURUMU')}**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📍 **{L.get('out_hava_konum','Konum')}:** {loc}\n\n"
            f"🌡️ **{L.get('out_hava_sicaklik','Sıcaklık')}:** `{temp_c}°C`\n"
            f"🤔 **{L.get('out_hava_hissedilen','Hissedilen')}:** `{feels_like}°C`\n"
            f"💧 **{L.get('out_hava_nem','Nem')}:** `%{humidity}`\n"
            f"💨 **{L.get('out_hava_ruzgar','Rüzgar')}:** `{windspeed} km/h`\n"
            f"🌡 **{L.get('out_hava_basinc','Basınç')}:** `{pressure} hPa`\n"
            f"☁️ **{L.get('out_hava_durum','Durum')}:** {desc}\n"
            f"🌞 **{L.get('out_hava_uv','UV Endeksi')}:** `{uv}`\n"
            f"👁️ **{L.get('out_hava_gorus','Görüş')}:** `{visibility} km`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _{L.get('out_hava_servis','AZRxGUARD Hava Servisi')}_"
        )
    except Exception as e:
        logger.error(f"Hava durumu hatası: {e}")
        return "❌ Hava servisi şu an erişilemiyor. Lütfen şehri İngilizce yaz.\nÖrnek: `Istanbul`, `Baku`, `Moscow`"

async def doviz_cevir(metin: str, lang: str = 'tr') -> str:
    L = LANG_DATA.get(lang, LANG_DATA['tr'])
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
            f"💱 **{L.get('out_doviz_title','DÖVİZ ÇEVİRİCİ')}**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 **{L.get('out_doviz_giris','Giriş')}:** `{miktar:,.2f} {kfrom}`\n"
            f"📤 **{L.get('out_doviz_sonuc','Sonuç')}:** `{sonuc_miktar:,.4f} {kto}`\n"
            f"📊 **{L.get('out_doviz_kur','Kur')}:** `1 {kfrom} = {sonuc:,.4f} {kto}`\n\n"
            f"📅 **{L.get('out_doviz_guncelleme','Güncelleme')}:** `{tarih}`\n"
            f"🌐 **{L.get('out_doviz_kaynak','Kaynak')}:** Open Exchange Rates\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _{L.get('out_doviz_servis','AZRxGUARD Döviz Servisi')}_"
        )
    except Exception as e:
        logger.error(f"Döviz hatası: {e}")
        return "❌ Döviz servisi şu an erişilemiyor. Lütfen sonra tekrar dene."

def dunya_saati(lang: str = 'tr') -> str:
    L = LANG_DATA.get(lang, LANG_DATA['tr'])
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
    metin = f"🕐 **{L.get('out_saat_title','DÜNYA SAATİ')}**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    metin += f"🌐 **UTC:** `{simdi_utc.strftime('%H:%M')}` — `{simdi_utc.strftime('%d.%m.%Y')}`\n\n"
    for isim, tz in sehirler:
        simdi = datetime.datetime.now(tz)
        metin += f"{isim}: `{simdi.strftime('%H:%M')}` _{simdi.strftime('%d.%m')}_\n"
    metin += f"\n━━━━━━━━━━━━━━━━━━━━━━\n🤖 _{L.get('out_saat_servis','AZRxGUARD Zaman Servisi')}_"
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
                'Gardabani': ['Gardabani', 'Ponichala', 'Soganluq', 'Vaziani'],
                'Marneuli': ['Marneuli', 'Sadaxlı', 'Qızılajlo', 'Muğanlı', 'Sabirkənd', 'Kosalar', 'Baydar', 'Tamarisi', 'Şülavəri', 'Dalis Mta', 'Karakilis', 'Algeti', 'Ulaşhlo', 'Kasumlo'],
                'Bolnisi': ['Bolnisi', 'Dmanisi', 'Kazreti', 'Dashbulagi', 'Başkənd', 'Sarvan'],
                'Tetritskaro': ['Tetritskaro', 'Algeti', 'Kldeisi', 'Manglisi', 'Tsalka yolu'],
                'Tsalka': ['Tsalka', 'Bediani', 'Dariali', 'Trialeti', 'Patara Tsalka'],
            },
            'Marneuli': {
                'Marneuli Şəhər': ['Marneuli', 'Böyük Marneuli', 'Kiçik Marneuli', 'Marneulis Sənaye'],
                'Sadaxlı': ['Sadaxlı', 'Ağbulaq', 'Qaçağan', 'Corablar', 'Hacıkənd'],
                'Ulaşhlo-Kasumlo': ['Ulaşhlo', 'Kasumlo', 'Qızılajlo', 'Kepenekçi', 'Avranlo'],
                'Muğanlı-Sabirkənd': ['Muğanlı', 'Sabirkənd', 'Kosalar', 'Bəhrəmtəpə'],
                'Baydar-Tamarisi': ['Baydar', 'Tamarisi', 'Şülavəri', 'Dalis Mta', 'Algeti'],
                'Karakilis-Bolnisi': ['Karakilis', 'Bolnisi Khevi', 'Orjonikidze', 'Sarvan'],
            },
            'Gardabani': {
                'Gardabani Merkez': ['Gardabani', 'Ponichala', 'Soğanlıq'],
                'Vaziani': ['Vaziani', 'Norio', 'Eldari', 'Samgori', 'Akhali Samgori'],
                'Krasnogorsk': ['Krasnogorsk', 'Nazarlevani', 'Patardzeuli'],
            },
            'Gori': {
                'Gori Merkez': ['Gori', 'Akhaldaba', 'Kvakhvreli', 'Variani', 'Skra'],
                'Kareli': ['Kareli', 'Ruisi', 'Ateni', 'Surami', 'Agara'],
                'Kaspi': ['Kaspi', 'Agara', 'Tsinari', 'Skulani', 'Khashuri'],
                'Khashuri': ['Khashuri', 'Surami', 'Kvishkheti', 'Agara', 'Tsikhisjvari'],
            },
            'Borjomi': {
                'Borjomi Merkez': ['Borjomi', 'Likani', 'Tsagveri', 'Abastumani', 'Vale'],
                'Bakuriani': ['Bakuriani', 'Kokhta', 'Tba', 'Didveli', 'Mitarbi'],
                'Aspindza': ['Aspindza', 'Adigeni', 'Zarzma', 'Vale'],
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
            'Marneuli Rayonu': [
                'Marneuli', 'Sadaxlı', 'Ulaşhlo', 'Kasumlo', 'Ağbulaq',
                'Qızılajlo', 'Qaçağan', 'Muğanlı', 'Sabirkənd', 'Kosalar',
                'Baydar', 'Tamarisi', 'Şülavəri', 'Dalis Mta',
                'Karakilis', 'Algeti', 'Bolnisi Khevi', 'Avranlo', 'Kepenekçi',
                'Corablar', 'Hacıkənd', 'Bəhrəmtəpə', 'Sarvan', 'Orjonikidze',
            ],
            'Gardabani Rayonu': [
                'Gardabani', 'Soğanlıq', 'Ponichala', 'Krasnogorsk',
                'Akhali Samgori', 'Norio', 'Eldari', 'Nazarlevani',
                'Vaziani', 'Patardzeuli', 'Kvemo Ponichala', 'Samgori',
            ],
            'Bolnisi Rayonu': [
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
            'Akhalkalaki Rayonu': [
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
            # Yeni üyeyi /atag için kaydet (botlar hariç)
            if not yeni_uye.is_bot:
                grup_uye_ekle(chat_member_update.chat.id, yeni_uye)
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
    strings = fs(context, user_id, lang)
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

async def ip_tam_analiz_yap(ip_adresi: str, lang: str = 'tr') -> str:
    L = LANG_DATA.get(lang, LANG_DATA['tr'])
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
    # Gizlilik — proxycheck.io + ip-api.com
    pc_type   = str(proxycheck.get('type', '')).lower()
    pc_vpn    = str(proxycheck.get('vpn', 'no')).lower() in ('yes', 'true', '1')
    pc_risk   = proxycheck.get('risk', None)
    is_vpn    = pc_vpn or (ipapi.get('proxy', False) and 'datacenter' not in pc_type)
    is_proxy  = 'proxy' in pc_type
    is_tor    = 'tor' in pc_type

    evet  = L.get('out_ip_evet',  '✅ Evet')
    hayir = L.get('out_ip_hayir', '❌ Hayır')
    vpn_str   = evet if is_vpn   else hayir
    proxy_str = evet if is_proxy else hayir
    tor_str   = evet if is_tor   else hayir

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
        risk_str = f"🔴 %{risk_sayi} ({L.get('out_ip_risk_yuksek','Yüksek Risk')})"
    elif risk_sayi >= 40:
        risk_str = f"🟡 %{risk_sayi} ({L.get('out_ip_risk_orta','Orta Risk')})"
    else:
        risk_str = f"🟢 %{risk_sayi} ({L.get('out_ip_risk_dusuk','Düşük Risk')})"

    mobil_str = L.get('out_ip_mobil_evet', '📱 Evet') if ipapi.get('mobile', False) else hayir
    dc_label  = L.get('out_ip_dc', "VERİ MERKEZİ IP'si!")
    dc_uyari  = f"  ⚠️ *[{dc_label}]*" if hosting else ""
    asn_str   = f"`{asn_raw}` ({asn_adi}){dc_uyari}"

    # Portlar
    if acik_portlar:
        port_str = ", ".join([f"{p} ({PORT_ADLARI[p]})" for p in acik_portlar])
    else:
        port_str = L.get('out_ip_port_yok', 'Açık port bulunamadı')

    return (
        f"🛡️ **{L.get('out_ip_title','IP Detaylı Güvenlik Analizi')}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 **{L.get('out_ip_sorgu','Sorgu')}:** `{gercek_ip}`\n\n"
        f"📍 **{L.get('out_ip_konum_bilgi','Konum Bilgisi')}**\n"
        f"🏳️ **{L.get('out_ip_ulke','Ülke')}:** {ulke}\n"
        f"🏙️ **{L.get('out_ip_bolge','Bölge')}:** {bolge}\n"
        f"🕐 **{L.get('out_ip_saat','Saat Dilimi')}:** `{saat_dilimi}`\n\n"
        f"🔌 **{L.get('out_ip_ag_bilgi','Ağ Bilgisi')}**\n"
        f"🌐 **{L.get('out_ip_inet','İnternet IP')}:** `{gercek_ip}`\n"
        f"🏢 **{L.get('out_ip_isp','İnternet İsmi (ISP)')}:** {isp}\n"
        f"🏛️ **{L.get('out_ip_org','Organizasyon')}:** {org}\n"
        f"📡 **{L.get('out_ip_asn','Altyapı (ASN)')}:** {asn_str}\n"
        f"📱 **{L.get('out_ip_mobil','Mobil Hat')}:** {mobil_str}\n"
        f"🏷️ **{L.get('out_ip_ptr','Ters DNS (PTR)')}:** `{ptr}`\n\n"
        f"🕵️ **{L.get('out_ip_gizlilik','Gizlilik & Tehdit Durumu')}**\n"
        f"VPN: {vpn_str}  |  Proxy: {proxy_str}  |  Tor: {tor_str}\n"
        f"⚠️ **{L.get('out_ip_tehdit','Tehdit Skoru')}:** {risk_str}\n\n"
        f"🔓 **{L.get('out_ip_portlar','Açık Portlar')}:** `{port_str}`\n\n"
        f"🤖 _{L.get('out_ip_servis','AZRxGUARD Güvenlik Analizi')}_"
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
    lang = get_lang(context, update.effective_user.id)
    bekle = await update.effective_message.reply_text(
        f"🔍 `{ip_adresi}` analiz ediliyor...\n_Bu işlem birkaç saniye sürebilir._",
        parse_mode='Markdown'
    )
    try:
        rapor = await ip_tam_analiz_yap(ip_adresi, lang)
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

# ═══════════════════════════════════════════════════════════════
# 📦 APK-OBB-CONFİG SİSTEMİ
# ═══════════════════════════════════════════════════════════════
_APK_DOSYALAR_YOL = 'apk_dosyalar.json'
_apk_yukleme_oturum: dict = {}          # {chat_id: {'adim': ..., 'isim': ..., 'aciklama': ...}}


def apk_dosyalari_yukle() -> dict:
    try:
        with open(_APK_DOSYALAR_YOL, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def apk_dosyalari_kaydet(data: dict):
    with open(_APK_DOSYALAR_YOL, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def _apk_kanal_isle(context: ContextTypes.DEFAULT_TYPE, cp):
    """APK kanalındaki mesajları ve komutları işler."""
    metin = (cp.text or cp.caption or '').strip()
    komut = metin.split()[0].lower().split('@')[0] if metin else ''

    # ── Komutlar ────────────────────────────────────────────
    if komut in ('/yükle', '/yukle', '/y\u00fckle'):
        _apk_yukleme_oturum[_APK_KANAL_ID] = {'adim': 'isim_bekliyor'}
        await cp.reply_text(
            "📦 **APK-OBB-CONFİG YÜKLEME**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Dosya için bir **isim** girin:\n"
            "_(Bu isim sadece hafızada kalır, /sil komutuyla silersiniz)_\n\n"
            "_İptal: /iptal_",
            parse_mode='Markdown'
        )
        return

    if komut in ('/sil',):
        _apk_yukleme_oturum[_APK_KANAL_ID] = {'adim': 'sil_isim_bekliyor'}
        await cp.reply_text(
            "🗑 **DOSYA SİL**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Silmek istediğiniz dosyanın **ismini** yazın:\n\n"
            "_İptal: /iptal_",
            parse_mode='Markdown'
        )
        return

    if komut in ('/dosyalarım', '/dosyalarim'):
        dosyalar = apk_dosyalari_yukle()
        if not dosyalar:
            await cp.reply_text("📭 Henüz hiç dosya yüklenmemiş.")
            return
        bot_username = context.bot.username
        satirlar = ["📦 **YÜKLENEN DOSYALAR**\n━━━━━━━━━━━━━━━━━━━━━━\n"]
        for i, (uid, bilgi) in enumerate(dosyalar.items(), 1):
            link = f"https://t.me/{bot_username}?start=apk_{uid}"
            satirlar.append(
                f"**{i}.** `{bilgi['isim']}`\n"
                f"   📅 {bilgi['tarih']}\n"
                f"   🔗 {link}\n"
            )
        await cp.reply_text('\n'.join(satirlar), parse_mode='Markdown', disable_web_page_preview=True)
        return

    if komut in ('/info', '/komutlar', '/yardim'):
        await cp.reply_text(
            "📦 **APK-OBB-CONFİG — KANAL KOMUTLARI**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📤 `/yükle` — Yeni dosya yükle\n"
            "   ↳ İsim → Açıklama → Dosya → Link\n\n"
            "🗑 `/sil` — Dosya sil (ismiyle)\n"
            "   ↳ İsim yaz → tamamen silinir\n\n"
            "📋 `/dosyalarım` — Tüm dosyaları listele\n"
            "   ↳ İsim + tarih + indirme linki\n\n"
            "ℹ️ `/info` — Bu yardım mesajı\n\n"
            "❌ `/iptal` — Aktif işlemi iptal et\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ **Desteklenen uzantılar:**\n"
            "`apk · obb · zip · rar · 7z · jar`\n"
            "`config · cfg · ini · xml · json · lua`\n"
            "`txt · dat · bin · pak · so · dex`\n"
            "`tar · gz · bz2 · xz · zz · lz4`\n"
            "`yaml · toml · db · sqlite · bak`\n"
            "`patch · mod · unity3d · asset · vpk`",
            parse_mode='Markdown'
        )
        return

    if komut == '/iptal':
        if _APK_KANAL_ID in _apk_yukleme_oturum:
            _apk_yukleme_oturum.pop(_APK_KANAL_ID)
            await cp.reply_text("✅ İşlem iptal edildi.")
        return

    # ── Durum makinesi ───────────────────────────────────────
    oturum = _apk_yukleme_oturum.get(_APK_KANAL_ID)
    if not oturum:
        return

    adim = oturum.get('adim')

    if adim == 'isim_bekliyor':
        if not metin or metin.startswith('/'):
            await cp.reply_text("❌ İsim boş olamaz! Tekrar yazın:")
            return
        oturum['isim'] = metin
        oturum['adim'] = 'aciklama_bekliyor'
        await cp.reply_text(
            f"✅ **İsim kaydedildi:** `{metin}`\n\n"
            f"📝 Şimdi **açıklamayı** girin:\n"
            f"_(Kullanıcılar bu açıklamayı görecek)_",
            parse_mode='Markdown'
        )

    elif adim == 'aciklama_bekliyor':
        if not metin or metin.startswith('/'):
            await cp.reply_text("❌ Açıklama boş olamaz! Tekrar yazın:")
            return
        oturum['aciklama'] = metin
        oturum['adim'] = 'dosya_bekliyor'
        await cp.reply_text(
            f"✅ **Açıklama kaydedildi.**\n\n"
            f"📁 Şimdi **dosyayı gönderin:**",
            parse_mode='Markdown'
        )

    elif adim == 'dosya_bekliyor':
        _GECERLI_UZANTILAR = {
            # Oyun / Android
            '.apk', '.obb', '.xapk', '.apks', '.aab', '.dex', '.odex', '.vdex', '.so', '.jar',
            # Arşiv
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.zz', '.z', '.lz4',
            # Konfig / Veri
            '.config', '.cfg', '.ini', '.xml', '.json', '.yaml', '.yml', '.toml',
            '.txt', '.dat', '.db', '.sqlite', '.sqlite3', '.pak', '.bin', '.bak',
            # Script / Kod
            '.lua', '.js', '.py', '.sh', '.bat', '.cs', '.java',
            # Diğer
            '.patch', '.diff', '.mod', '.vpk', '.unity3d', '.asset',
        }
        # Dosya tipini tespit et
        file_id = None
        file_type = None
        dosya_adi = ''
        if cp.document:
            dosya_adi = (cp.document.file_name or '').lower()
            ext = '.' + dosya_adi.rsplit('.', 1)[-1] if '.' in dosya_adi else ''
            if ext not in _GECERLI_UZANTILAR:
                await cp.reply_text(
                    f"❌ **Geçersiz dosya türü:** `{ext or 'bilinmiyor'}`\n\n"
                    f"✅ Kabul edilen türler:\n`apk · obb · zip · rar · jar · config · tar · gz · zz`",
                    parse_mode='Markdown'
                )
                return
            file_id = cp.document.file_id
            file_type = 'document'

        if not file_id:
            await cp.reply_text(
                "❌ Dosya algılanamadı veya desteklenmiyor!\n\n"
                "✅ Kabul edilen türler:\n`apk · obb · zip · rar · jar · config · tar · gz · zz`",
                parse_mode='Markdown'
            )
            return

        # Benzersiz UUID oluştur ve kaydet
        dosya_uuid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=14))
        dosyalar = apk_dosyalari_yukle()
        tarih = datetime.datetime.now(TR_SAAT).strftime('%d.%m.%Y %H:%M')
        dosyalar[dosya_uuid] = {
            'isim': oturum['isim'],
            'aciklama': oturum['aciklama'],
            'file_id': file_id,
            'file_type': file_type,
            'tarih': tarih
        }
        apk_dosyalari_kaydet(dosyalar)

        # Linki oluştur
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start=apk_{dosya_uuid}"

        _apk_yukleme_oturum.pop(_APK_KANAL_ID, None)

        await cp.reply_text(
            f"✅ **DOSYA KAYDEDİLDİ!**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📦 **İsim:** `{oturum['isim']}`\n"
            f"📝 **Açıklama:** {oturum['aciklama']}\n"
            f"📅 **Tarih:** {tarih}\n\n"
            f"🔗 **Yönlendirme Linki:**\n`{link}`\n\n"
            f"_Bu linki kanala at — tıklayanlar dosyayı doğrudan alır!_",
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    elif adim == 'sil_isim_bekliyor':
        if not metin or metin.startswith('/'):
            await cp.reply_text("❌ İsim boş olamaz! Tekrar yazın:")
            return
        dosyalar = apk_dosyalari_yukle()
        silindi = False
        for uid, bilgi in list(dosyalar.items()):
            if bilgi['isim'].lower() == metin.lower():
                del dosyalar[uid]
                apk_dosyalari_kaydet(dosyalar)
                silindi = True
                break
        _apk_yukleme_oturum.pop(_APK_KANAL_ID, None)
        if silindi:
            await cp.reply_text(f"✅ `{metin}` isimli dosya tamamen silindi.", parse_mode='Markdown')
        else:
            await cp.reply_text(f"❌ `{metin}` isimli dosya bulunamadı.\n/dosyalarım ile mevcut dosyaları görün.", parse_mode='Markdown')


# ═══════════════════════════════════════════════════════════════
# 👥 GRUP ÜYE TAKİP SİSTEMİ  (/atag için)
# ═══════════════════════════════════════════════════════════════
_GRUP_UYELER_YOL = 'grup_uyeler.json'

def grup_uyeleri_yukle() -> dict:
    try:
        with open(_GRUP_UYELER_YOL, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def grup_uyeleri_kaydet(data: dict):
    try:
        with open(_GRUP_UYELER_YOL, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

def grup_uye_ekle(chat_id: int, user):
    """Gelen mesajdan kullanıcıyı gruba kaydet."""
    if not user or user.is_bot:
        return
    veriler = grup_uyeleri_yukle()
    cid = str(chat_id)
    uid = str(user.id)
    if cid not in veriler:
        veriler[cid] = {}
    veriler[cid][uid] = {
        'isim': user.first_name or '',
        'kullanici_adi': user.username or ''
    }
    grup_uyeleri_kaydet(veriler)


async def atag_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gruptaki TÜM üyeleri (adminler + kullanıcılar + botlar) etiketler. Sadece gruplarda çalışır."""
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not chat or chat.type not in ('group', 'supergroup'):
        await msg.reply_text("⚠️ Bu komut sadece gruplarda çalışır.")
        return

    # Admin kontrolü
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_idler = {a.user.id for a in admins}
    except Exception:
        admins = []
        admin_idler = set()

    if user.id not in admin_idler:
        await msg.reply_text("⛔ Bu komutu sadece grup yöneticileri kullanabilir.")
        return

    ek_mesaj = ' '.join(context.args) if context.args else ''

    # Tüm etiketleri topla: önce adminler (botlar dahil), sonra takip edilen üyeler
    eklenen_idler: set = set()
    etiketler: list = []

    # 1) Adminler ve botlar
    for a in admins:
        u = a.user
        eklenen_idler.add(u.id)
        if u.username:
            etiketler.append(f"@{u.username}")
        else:
            etiketler.append(f"<a href='tg://user?id={u.id}'>{html.escape(u.first_name or '?')}</a>")

    # 2) Takip edilen tüm üyeler (sınır yok)
    veriler = grup_uyeleri_yukle()
    uyeler = veriler.get(str(chat.id), {})
    for uid_str, bilgi in uyeler.items():
        try:
            uid_int = int(uid_str)
        except ValueError:
            continue
        if uid_int in eklenen_idler:
            continue
        eklenen_idler.add(uid_int)
        if bilgi.get('kullanici_adi'):
            etiketler.append(f"@{bilgi['kullanici_adi']}")
        else:
            isim = html.escape(bilgi.get('isim', '?') or '?')
            etiketler.append(f"<a href='tg://user?id={uid_str}'>{isim}</a>")

    if not etiketler:
        await msg.reply_text("📭 Henüz etiketlenecek üye bulunamadı.")
        return

    baslik = f"📢 {ek_mesaj}\n\n" if ek_mesaj else "📢\n\n"

    # 4096 karakter sınırı — gerekirse parçalara böl
    async def _gonder_parca(parca_etiketler: list, ilk: bool):
        on = baslik if ilk else ""
        metin = on + " ".join(parca_etiketler)
        await msg.reply_text(metin, parse_mode='HTML')

    parca: list = []
    parca_uzunluk = len(baslik)
    ilk_parca = True
    for e in etiketler:
        eklenecek = len(e) + 1
        if parca_uzunluk + eklenecek > 4000 and parca:
            await _gonder_parca(parca, ilk_parca)
            ilk_parca = False
            parca = [e]
            parca_uzunluk = eklenecek
        else:
            parca.append(e)
            parca_uzunluk += eklenecek
    if parca:
        await _gonder_parca(parca, ilk_parca)


async def grup_ve_kanal_mesaj_yonet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        channel_post = update.channel_post
        # ── APK-OBB-CONFİG yükleme kanalı — her zaman önce işle ──
        if channel_post.chat_id == _APK_KANAL_ID:
            await _apk_kanal_isle(context, channel_post)
            return
        # ──────────────────────────────────────────────────────────

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

        # Üye takibi — gruplarda mesaj atan herkesi kaydet
        if update.message.chat.type in ('group', 'supergroup') and update.message.from_user:
            grup_uye_ekle(update.message.chat_id, update.message.from_user)
            # Mesaj sayacı — istatistik için
            try:
                import tracking_store as _ts
                usr = update.message.from_user
                _ts.stats_artir(
                    update.message.chat_id, usr.id,
                    usr.username or '', usr.full_name or ''
                )
            except Exception:
                pass

        # Gece modu: ZAMANLI_KANAL_ID grubundaki mesajları sil (admin mesajlarına dokunma)
        if update.message.chat_id == ZAMANLI_KANAL_ID and gece_modu_aktif_mi():
            # Adminlerin gece modunda da mesaj atabilmesi için admin kontrolü
            _is_admin = False
            try:
                _uye = await context.bot.get_chat_member(ZAMANLI_KANAL_ID, update.message.from_user.id)
                _is_admin = _uye.status in ('administrator', 'creator')
            except Exception:
                pass
            if not _is_admin:
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
async def _bot_baslat_animasyon(update, context, user_id, lang):
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
    fid = get_font(context, user_id)
    await mesaj.edit_text(ft(LANG_DATA[lang]['welcome'], context, user_id), reply_markup=ana_menu_klavye(lang, fid), parse_mode='Markdown')


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

    # ── APK deep link kontrolü ────────────────────────────────
    if context.args and context.args[0].startswith('apk_'):
        dosya_uuid = context.args[0][4:]
        dosyalar = apk_dosyalari_yukle()
        if dosya_uuid in dosyalar:
            bilgi = dosyalar[dosya_uuid]
            geri_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data='go_home')]])
            caption_metin = f"📦 {bilgi['aciklama']}"
            try:
                ft_map = {
                    'document': context.bot.send_document,
                    'photo':    context.bot.send_photo,
                    'video':    context.bot.send_video,
                    'audio':    context.bot.send_audio,
                }
                send_fn = ft_map.get(bilgi.get('file_type', 'document'), context.bot.send_document)
                kwarg_key = bilgi.get('file_type', 'document')
                await send_fn(
                    chat_id=user_id,
                    **{kwarg_key: bilgi['file_id']},
                    caption=caption_metin,
                    reply_markup=geri_kb
                )
            except Exception as apk_err:
                logger.error(f"APK dosya gönderme hatası: {apk_err}")
                await update.message.reply_text("❌ Dosya gönderilirken hata oluştu.", reply_markup=geri_kb)
        else:
            await update.message.reply_text("❌ Bu link geçersiz veya dosya silinmiş.")
        return
    # ─────────────────────────────────────────────────────────

    try:
        await log_kanali_gonder(context.bot, update, "📲 /start komutu")
    except Exception:
        pass

    await _bot_baslat_animasyon(update, context, user_id, lang)

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang = get_lang(context, user_id)
    strings = fs(context, user_id, lang)
    await query.answer()

    # ── Her buton basışını logla ──────────────────────────────
    _SESSIZ_CALLBACKLER = {'noop', 'go_home', 'bot_yazi_tipi', 'menu_lang', 'menu_bot_ayarlari'}
    if query.data not in _SESSIZ_CALLBACKLER:
        try:
            # Callback verisinden okunabilir buton adı üret
            _cb_etiket = {
                'menu_fun': '🎮 Eğlence Menüsü', 'menu_admin': '👑 Admin', 'menu_siber_guvenlik': '🛡️ Siber Güvenlik',
                'menu_azr_special': '⭐ AZR Özel', 'menu_pro_araclar': '⚡ Pro Araçlar',
                'menu_video_olusturucu': '🎬 Video Editör', 'menu_telefon_fiyatlari': '📱 Telefon Fiyatları',
                'menu_ip_sorgu': '🌐 IP Sorgu', 'menu_hatirlat': '⏰ Hatırlatıcı',
                'pro_hesap': '🧮 Hesap Makinesi', 'pro_hash': '🔐 Hash Üretici',
                'pro_hava': '🌍 Hava Durumu', 'pro_doviz': '💱 Döviz Kuru',
                'pro_saat': '🕐 Dünya Saati', 'pro_b64': '🔒 Base64',
                'pro_sifre': '🔑 Şifre Üretici', 'pro_wiki': '🌐 Wikipedia',
                'pro_not': '📝 Not Defteri', 'pro_gunsozu': '💡 Günün Sözü',
                'pro_birim': '📐 Birim Çevir', 'pro_sans': '🎱 Şans Topu',
                'pro20_ping': '🏓 Ping', 'pro20_renk': '🎨 Renk Çevir',
                'pro20_metin': '📊 Metin Analiz', 'pro20_rastgele': '🎲 Rastgele',
                'pro20_sifrele': '🔠 Şifrele', 'pro20_bmi': '💪 BMI',
                'pro20_yuzde': '💯 Yüzde', 'r20_sayi': '🔢 Rastgele Sayı',
                'r20_para': '🪙 Para Yüzü', 'r20_zar6': '🎲 Zar d6', 'r20_zar20': '🎲 Zar d20',
            }.get(query.data) or f"📲 {query.data}"
            await log_kanali_gonder(context.bot, update, komut=_cb_etiket)
        except Exception:
            pass
    # ─────────────────────────────────────────────────────────

    if not await kanal_takip_kontrol(update, context, user_id, lang):
        return

    if query.data == 'menu_bot_ayarlari':
        ayarlar_klavye = [
            [InlineKeyboardButton(strings['btn_lang'], callback_data='menu_lang')],
            [InlineKeyboardButton(strings.get('btn_yazi_tipi', '🔤 BOT YAZI TİPİ'), callback_data='bot_yazi_tipi')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(
            ft(strings.get('bot_ayarlari_welcome', '⚙️ **BOT AYARLARI**\n\nBir ayar seçin:'), context, user_id),
            reply_markup=InlineKeyboardMarkup(ayarlar_klavye),
            parse_mode='Markdown'
        )
    elif query.data == 'bot_yazi_tipi':
        aktif_font = get_font(context, user_id)
        font_satirlari = []
        for font_id, preview in YAZI_TIPLERI:
            isaretli = " ✅" if font_id == aktif_font else ""
            font_satirlari.append([InlineKeyboardButton(f"{preview}{isaretli}", callback_data=f'set_font_{font_id}')])
        font_satirlari.append([InlineKeyboardButton(strings['btn_back'], callback_data='menu_bot_ayarlari')])
        await query.edit_message_text(
            strings.get('yazi_tipi_welcome', '🔤 **BOT YAZI TİPİ**\n\nBir yazı tipi seçin:'),
            reply_markup=InlineKeyboardMarkup(font_satirlari),
            parse_mode='Markdown'
        )
    elif query.data.startswith('set_font_'):
        font_id = query.data[9:]
        if font_id not in YAZI_TIPI_HARITASI and font_id not in ('strikethrough', 'underline'):
            await query.answer('❌ Geçersiz yazı tipi!', show_alert=True)
            return
        if 'font' not in context.bot_data:
            context.bot_data['font'] = {}
        context.bot_data['font'][user_id] = font_id
        ornek = font_donustur('AZRxGUARD - Merhaba!', font_id)
        geri_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton('🔤 Başka Yazı Tipi', callback_data='bot_yazi_tipi')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_bot_ayarlari')]
        ])
        await query.edit_message_text(
            f"{strings.get('font_changed', '✅ Yazı tipi değiştirildi!')}\n\n"
            f"🔤 **Örnek:** {ornek}",
            reply_markup=geri_klavye,
            parse_mode='Markdown'
        )
    elif query.data == 'menu_lang':
        dil_klavye = [
            [InlineKeyboardButton("🇹🇷 Türkçe", callback_data='set_lang_tr'), InlineKeyboardButton("🇦🇿 Azərbaycanca", callback_data='set_lang_az')],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang_ru'), InlineKeyboardButton("🇬🇧 English", callback_data='set_lang_en')],
            [InlineKeyboardButton("🇩🇪 Deutsch", callback_data='set_lang_de'), InlineKeyboardButton("🇬🇪 ქართული", callback_data='set_lang_ka')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_bot_ayarlari')]
        ]
        await query.edit_message_text(strings['lang_select'], reply_markup=InlineKeyboardMarkup(dil_klavye), parse_mode='Markdown')
    elif query.data.startswith('set_lang_'):
        yeni_dil = query.data.split('_')[-1]
        if 'lang' not in context.bot_data:
            context.bot_data['lang'] = {}
        context.bot_data['lang'][user_id] = yeni_dil
        fid = get_font(context, user_id)
        yeni_strings = FontStrings(LANG_DATA[yeni_dil], fid)
        await query.edit_message_text(
            f"{LANG_DATA[yeni_dil]['lang_changed']}\n\n{yeni_strings['welcome']}",
            reply_markup=ana_menu_klavye(yeni_dil, fid),
            parse_mode='Markdown'
        )
    elif query.data == 'menu_admin':
        context.user_data['durum'] = 'admin_mesaj_bekliyor'
        await query.edit_message_text(strings['ask_admin_msg'], parse_mode='Markdown')
    elif query.data == 'menu_fun':
        context.user_data['mevcut_kategori'] = '🎮 Eğlence'
        fun_klavye = [
            [InlineKeyboardButton('🔮 AKİNATÖR', callback_data='eglence_akinator')],
            [InlineKeyboardButton(strings['btn_roll_dice'], callback_data='roll_dice'),
             InlineKeyboardButton(strings.get('btn_sans_arac', '🎱 Şans Topu'), callback_data='pro_sans')],
            [InlineKeyboardButton(strings.get('btn_oyun_tkmk', '✊ Taş-Kağıt-Makas'), callback_data='oyun_tkmk')],
            [InlineKeyboardButton(strings.get('btn_oyun_sayi', '🔢 Sayı Tahmin'), callback_data='oyun_sayi_baslat')],
            [InlineKeyboardButton('🪙 Para At', callback_data='eglence_para_at'),
             InlineKeyboardButton('🎯 Rus Ruleti', callback_data='eglence_rulet')],
            [InlineKeyboardButton('🔮 Kehanet', callback_data='eglence_kehanet'),
             InlineKeyboardButton('🎲 Rastgele', callback_data='pro20_rastgele')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ]
        await query.edit_message_text(
            "🎮 **EĞLENce MENüSü**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔮 Akinatör · 🎲 Zar · 🎱 Şans Topu · ✊ TKM\n"
            "🔢 Sayı Tahmin · 🪙 Para At · 🎯 Rus Ruleti\n"
            "🔮 Kehanet · 🎲 Rastgele",
            reply_markup=InlineKeyboardMarkup(fun_klavye),
            parse_mode='Markdown'
        )
    elif query.data == 'menu_ip_sorgu':
        context.user_data['mevcut_kategori'] = '🛡️ Siber Güvenlik › IP Sorgu'
        ip_klavye = [
            [
                InlineKeyboardButton(strings.get('btn_ip', '🌐 IP Sorgula'), callback_data='menu_ip'),
                InlineKeyboardButton('🛡️ IP Analiz', callback_data='menu_ip_analiz')
            ],
            [InlineKeyboardButton('📡 IP Al (Link İzleyici)', callback_data='menu_iplogger')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_siber_guvenlik')]
        ]
        await query.edit_message_text(
            strings.get('ip_sorgu_welcome', '🌐 **IP Sorgu Menüsü**\n\nAşağıdan sorgu türünü seçin:'),
            reply_markup=InlineKeyboardMarkup(ip_klavye), parse_mode='Markdown'
        )
    elif query.data == 'menu_iplogger':
        context.user_data['mevcut_kategori'] = '🛡️ Siber Güvenlik › IP Al'
        await log_kanali_gonder(context.bot, update, kategori='🛡️ Siber Güvenlik', komut='📡 IP Al (Link İzleyici)')
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_ip_sorgu')]])
        context.user_data['durum'] = 'iplogger_bekliyor'
        await query.edit_message_text(
            "📡 **IP AL — LİNK İZLEYİCİ**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Bir sosyal medya veya video linki gönder:\n\n"
            "📌 _Örnek:_\n"
            "`https://www.tiktok.com/@kullanici/video/...`\n"
            "`https://www.instagram.com/p/...`\n"
            "`https://www.youtube.com/watch?v=...`\n\n"
            "Bot sana özel bir izleme linki üretecek\\.\n"
            "Linke tıklayan kişinin IP bilgileri buraya gelecek\\.",
            reply_markup=geri,
            parse_mode='MarkdownV2'
        )
    elif query.data == 'menu_azr_special':
        context.user_data['mevcut_kategori'] = '⭐ AZR Özel'
        azr_klavye = [
            [InlineKeyboardButton(strings['btn_stats'], callback_data='show_inline_stats')],
            [InlineKeyboardButton(strings['btn_meid'], callback_data='show_meid')],
            [InlineKeyboardButton(strings.get('btn_hatirlat', '⏰ Hatırlatıcı'), callback_data='menu_hatirlat')],
            [InlineKeyboardButton('🤖 INFO', callback_data='azr_bot_info')],
            [InlineKeyboardButton('🏓 Ping', callback_data='pro20_ping')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(strings['azr_welcome'], reply_markup=InlineKeyboardMarkup(azr_klavye), parse_mode='Markdown')
    elif query.data == 'azr_bot_info':
        su_an = datetime.datetime.now(AZ_SAAT)
        bilgi = (
            f"🤖 **AZRxGUARD — BOT BİLGİSİ**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📛 **Bot Adı:** AZRxGUARD\n"
            f"👑 **Kurucu / Owner:** MAQA\n"
            f"📅 **Kuruluş Tarihi:** Ocak 2024\n"
            f"⚡ **Versiyon:** 2.0 *(Büyük Güncelleme)*\n"
            f"🌍 **Desteklenen Diller:** 🇹🇷 TR · 🇦🇿 AZ · 🇷🇺 RU · 🇬🇧 EN · 🇩🇪 DE · 🇬🇪 KA\n\n"
            f"⏰ **Şu An:** {su_an.strftime('%H:%M:%S')}\n"
            f"📆 **Bugün:** {su_an.strftime('%d.%m.%Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔧 **Özellikler:**\n"
            f"✅ 🎬 Video Editör — 10 güçlü efekt\n"
            f"✅ 🛡️ Siber Güvenlik — IP Analiz, TG Panel, Hunter\n"
            f"✅ ⚡ PRO Araçlar — Hesap, Hash, Hava, Döviz vb.\n"
            f"✅ 📱 Telefon Fiyatları — 100+ model, ₾ GEL (Gürcistan Pazarı)\n"
            f"✅ 🎮 Eğlence — Zar, TKM, Sayı Tahmin\n"
            f"✅ 🌍 6 Dil Desteği\n"
            f"✅ 📝 Not Defteri & Hatırlatıcı\n"
            f"✅ 📊 Canlı İstatistik Sistemi\n"
            f"✅ 🔒 Kanal Üyelik Koruması\n"
            f"✅ 🌙 Gece Modu (22:00 — 08:00)\n"
            f"✅ 📋 Log Sistemi\n"
            f"✅ 🤖 AI Entegrasyonu\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Bu bot MAQA tarafından sevgiyle yapıldı!_ ❤️\n"
            f"📢 Kanal: @azrXmaqa"
        )
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_azr_special')]])
        await query.edit_message_text(bilgi, reply_markup=geri_klavye, parse_mode='Markdown')
    elif query.data == 'show_inline_stats':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='📊 İstatistikler')
        rapor_metni = istatistik_raporu_hazirla(context)
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_azr_special')]])
        await query.edit_message_text(text=rapor_metni, reply_markup=geri_klavye, parse_mode='Markdown')
    elif query.data == 'show_meid':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='📲 Cihaz Bilgisi (MEID)')
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
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🌐 IP Sorgulama')
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_ip_sorgu')]])
        context.user_data['durum'] = 'ip_bekliyor'
        await query.edit_message_text(
            strings.get('ip_ask', '🌐 **IP Sorgulama**\n\nSorgulamak istediğiniz IP adresini yazın:\nÖrnek: `8.8.8.8`'),
            reply_markup=geri_klavye, parse_mode='Markdown'
        )
    elif query.data == 'menu_ip_analiz':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🛡️ IP Güvenlik Analizi')
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_ip_sorgu')]])
        context.user_data['durum'] = 'ip_analiz_bekliyor'
        await query.edit_message_text(
            "🛡️ **IP Güvenlik Analizi**\n\nAnaliz etmek istediğiniz IP adresini yazın:\nÖrnek: `185.220.101.1`",
            reply_markup=geri_klavye, parse_mode='Markdown'
        )
    elif query.data == 'roll_dice':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🎲 Zar At')
        await query.message.delete()
        await query.message.chat.send_dice(emoji='🎲')
    elif query.data == 'menu_panel':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🔍 TG Paneli')
        geri_klavye = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_siber_guvenlik')]])
        context.user_data['durum'] = 'panel_sorgu_bekliyor'
        await query.edit_message_text(
            strings.get('panel_welcome', '🔍 **PANEL**\n\n@kullaniciadi veya ID yaz:'),
            reply_markup=geri_klavye,
            parse_mode='Markdown'
        )
    elif query.data == 'menu_guvenli_sorgu':
        gs_klavye = [
            [InlineKeyboardButton(strings.get('btn_username_checker', '🔎 Platform Kontrolü'), callback_data='menu_username_checker')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_siber_guvenlik')]
        ]
        await query.edit_message_text(
            strings.get('guvenli_sorgu_welcome', '🕵️ **USERNAME HUNTER**\n\nKullanıcı adını 14 platformda tara:'),
            reply_markup=InlineKeyboardMarkup(gs_klavye),
            parse_mode='Markdown'
        )
    elif query.data == 'menu_siber_guvenlik':
        context.user_data['mevcut_kategori'] = '🛡️ Siber Güvenlik'
        siber_klavye = [
            [InlineKeyboardButton(strings.get('btn_ip_sorgu', '🌐 IP Sorgu'), callback_data='menu_ip_sorgu'),
             InlineKeyboardButton('📋 Tg Kanalı Info', callback_data='menu_panel')],
            [InlineKeyboardButton(strings.get('btn_guvenli_sorgu', '🕵️ Username Hunter'), callback_data='menu_guvenli_sorgu'),
             InlineKeyboardButton(strings.get('btn_sifre_guc', '🔐 Şifre Güç Testi'), callback_data='siber_sifre_guc')],
            [InlineKeyboardButton('🔍 Şifre Sızıntı', callback_data='menu_sifre_pwned'),
             InlineKeyboardButton('📱 Operatör Sorgula', callback_data='menu_operator')],
            [InlineKeyboardButton('🔒 Base64', callback_data='pro_b64'),
             InlineKeyboardButton('🔠 Şifrele', callback_data='pro20_sifrele')],
            [InlineKeyboardButton('🔑 Şifre Üretici', callback_data='pro_sifre'),
             InlineKeyboardButton('🔐 Hash Üretici', callback_data='pro_hash')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ]
        await query.edit_message_text(
            strings.get('siber_guvenlik_welcome', '🛡️ **SİBER GÜVENLİK**\n\nAraçlardan birini seçin:'),
            reply_markup=InlineKeyboardMarkup(siber_klavye),
            parse_mode='Markdown'
        )
    elif query.data == 'siber_sifre_guc':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🔐 Şifre Güç Testi')
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_siber_guvenlik')]])
        context.user_data['durum'] = 'sifre_guc_bekliyor'
        await query.edit_message_text(
            "🔐 **Şifre Güç Testi**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Test etmek istediğin şifreyi yaz:\n"
            "_(Şifren sadece sana görünür, hiçbir yerde saklanmaz)_",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'menu_sifre_pwned':
        await log_kanali_gonder(context.bot, update, kategori='🛡️ Siber Güvenlik', komut='🔍 Şifre Sızıntı')
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_siber_guvenlik')]])
        context.user_data['durum'] = 'sifre_pwned_bekliyor'
        await query.edit_message_text(
            "🔍 **SIZDIRILMIŞ ŞİFRE KONTROLÜ**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Kontrol etmek istediğin şifreyi yaz:\n\n"
            "🔒 _Şifren SHA-1 hash'lenerek kontrol edilir._\n"
            "_Tam şifre hiçbir sunucuya gönderilmez (k-anonymity)._",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'menu_operator':
        await log_kanali_gonder(context.bot, update, kategori='🛡️ Siber Güvenlik', komut='📱 Operatör Sorgula')
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_siber_guvenlik')]])
        context.user_data['durum'] = 'operator_bekliyor'
        await query.edit_message_text(
            "📱 **OPERATÖR SORGULAMA**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Gürcistan telefon numarasını yaz:\n\n"
            "📌 _Örnekler:_\n"
            "`0591234567`\n"
            "`+995591234567`",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'oyun_tkmk':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='✊ Taş-Kağıt-Makas')
        klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("🪨 Taş", callback_data='tkmk_tas'),
             InlineKeyboardButton("📄 Kağıt", callback_data='tkmk_kagit'),
             InlineKeyboardButton("✂️ Makas", callback_data='tkmk_makas')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_fun')]
        ])
        await query.edit_message_text(
            "✊ **TAŞ-KAĞIT-MAKAS**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\nSeçimini yap!",
            reply_markup=klavye, parse_mode='Markdown'
        )
    elif query.data in ('tkmk_tas', 'tkmk_kagit', 'tkmk_makas'):
        secimler = {'tkmk_tas': '🪨 Taş', 'tkmk_kagit': '📄 Kağıt', 'tkmk_makas': '✂️ Makas'}
        kazanan = {'tkmk_tas': 'tkmk_makas', 'tkmk_kagit': 'tkmk_tas', 'tkmk_makas': 'tkmk_kagit'}
        kullanici = query.data
        bot_sec = random.choice(list(secimler.keys()))
        kullanici_ad = secimler[kullanici]
        bot_ad = secimler[bot_sec]
        if kullanici == bot_sec:
            sonuc = "🤝 **Berabere!**"
        elif kazanan[kullanici] == bot_sec:
            sonuc = "🏆 **Kazandın!**"
        else:
            sonuc = "💀 **Kaybettin!**"
        klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Tekrar Oyna", callback_data='oyun_tkmk')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_fun')]
        ])
        await query.edit_message_text(
            f"✊ **TAŞ-KAĞIT-MAKAS**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 Sen: **{kullanici_ad}**\n"
            f"🤖 Bot: **{bot_ad}**\n\n{sonuc}",
            reply_markup=klavye, parse_mode='Markdown'
        )
    elif query.data == 'oyun_sayi_baslat':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🔢 Sayı Tahmin Oyunu')
        gizli = random.randint(1, 100)
        context.user_data['sayi_oyun'] = {'gizli': gizli, 'deneme': 0}
        context.user_data['durum'] = 'sayi_tahmin_bekliyor'
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Oyunu Bitir", callback_data='menu_fun')]])
        await query.edit_message_text(
            "🔢 **SAYI TAHMİN OYUNU**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "1 ile 100 arasında bir sayı seçtim! 🎯\n\n"
            "Tahminini mesaj olarak yaz:",
            reply_markup=geri, parse_mode='Markdown'
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
        context.user_data['mevcut_kategori'] = '⚡ Pro Araçlar'
        pro_klavye = [
            [InlineKeyboardButton('🏠 Kişisel Kullanım', callback_data='menu_kisisel_kullanim')],
            [InlineKeyboardButton('🛡️ Siber Güvenlik', callback_data='menu_siber_guvenlik'),
             InlineKeyboardButton('🎮 Eğlence', callback_data='menu_fun')],
            [InlineKeyboardButton('🌐 Wikipedia', callback_data='pro_wiki'),
             InlineKeyboardButton('📱 QR Kod', callback_data='sa_qr')],
            [InlineKeyboardButton('🌐 URL Kısalt', callback_data='sa_url'),
             InlineKeyboardButton('🎭 Sahte Kimlik', callback_data='sa_kimlik')],
            [InlineKeyboardButton('📊 Metin Analiz', callback_data='pro20_metin'),
             InlineKeyboardButton('💡 Günün Sözü', callback_data='pro_gunsozu')],
            [InlineKeyboardButton('📱 Telefon Fiyatları', callback_data='menu_telefon_fiyatlari')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(
            "⚡ **PRO ARAÇLAR MERKEZİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\nKategori veya araç seçin:",
            reply_markup=InlineKeyboardMarkup(pro_klavye),
            parse_mode='Markdown'
        )
    elif query.data == 'menu_kisisel_kullanim':
        context.user_data['mevcut_kategori'] = '🏠 Kişisel Kullanım'
        kis_klavye = [
            [InlineKeyboardButton(strings.get('btn_hesap_arac', '🧮 Hesap Makinesi'), callback_data='pro_hesap'),
             InlineKeyboardButton(strings.get('btn_hava_arac', '🌍 Hava Durumu'), callback_data='pro_hava')],
            [InlineKeyboardButton(strings.get('btn_saat_arac', '🕐 Dünya Saati'), callback_data='pro_saat'),
             InlineKeyboardButton(strings.get('btn_not_arac', '📝 Not Defteri'), callback_data='pro_not')],
            [InlineKeyboardButton(strings.get('btn_doviz_arac', '💱 Döviz Kuru'), callback_data='pro_doviz'),
             InlineKeyboardButton('💯 Yüzde', callback_data='pro20_yuzde')],
            [InlineKeyboardButton('💪 BMI', callback_data='pro20_bmi'),
             InlineKeyboardButton(strings.get('btn_birim_arac', '📐 Birim Çeviri'), callback_data='pro_birim')],
            [InlineKeyboardButton('📅 Yaş/Tarih', callback_data='sa_tarih'),
             InlineKeyboardButton('🔤 İsim Fontu', callback_data='pro_isim_fontu')],
            [InlineKeyboardButton('🎨 Renk Çevir', callback_data='pro20_renk')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ]
        await query.edit_message_text(
            "🏠 **KİŞİSEL KULLANIM**\n━━━━━━━━━━━━━━━━━━━━━━\n\nBir araç seçin:",
            reply_markup=InlineKeyboardMarkup(kis_klavye),
            parse_mode='Markdown'
        )
    elif query.data == 'pro_hesap':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🧮 Hesap Makinesi')
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        context.user_data['durum'] = 'hesap_bekliyor'
        await query.edit_message_text(strings.get('hesap_ask', '🧮 Matematik ifadesi girin:'), reply_markup=geri, parse_mode='Markdown')
    elif query.data == 'pro_hash':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🔐 Hash Üretici')
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        context.user_data['durum'] = 'hash_bekliyor'
        await query.edit_message_text(strings.get('hash_ask', '🔐 Hashlenecek metni girin:'), reply_markup=geri, parse_mode='Markdown')
    elif query.data == 'pro_hava':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🌍 Hava Durumu')
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
        bekle_msg = await query.message.reply_text(f"🌍 `{html.escape(lokasyon)}` hava durumu getiriliyor...", parse_mode='Markdown')
        sonuc = await hava_durumu_getir(lokasyon, lang)
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
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='💱 Döviz Kuru')
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
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🕐 Dünya Saati')
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yenile", callback_data='pro_saat')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        await query.edit_message_text(dunya_saati(lang), reply_markup=geri, parse_mode='Markdown')
    elif query.data == 'pro_b64':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🔒 Base64 Encode/Decode')
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        context.user_data['durum'] = 'b64_bekliyor'
        await query.edit_message_text(strings.get('b64_ask', '🔒 encode metin / decode bWV0aW4='), reply_markup=geri, parse_mode='Markdown')
    elif query.data == 'pro_sifre':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🔑 Şifre Üretici')
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
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🌐 Wikipedia Arama')
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
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='📝 Not Defteri')
        context.user_data['durum'] = None
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
                not_metni += f"{i}. {not_[:80]}\n"
            await query.edit_message_text(
                not_metni,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Not Ekle", callback_data='not_ekle'),
                     InlineKeyboardButton("🗑️ Not Sil", callback_data='not_sil_menu')],
                    *not_klavye_geri
                ]),
                parse_mode='Markdown'
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
                not_metni += f"{i}. {n[:80]}\n"
            await query.edit_message_text(
                not_metni,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Not Ekle", callback_data='not_ekle'),
                     InlineKeyboardButton("🗑️ Not Sil", callback_data='not_sil_menu')],
                    [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
                ]),
                parse_mode='Markdown'
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
    # ── 🆕 AZRxGUARD 2.0 ARAÇLAR ──────────────────────────────
    elif query.data == 'pro20_ping':
        await query.answer("🏓 Ölçülüyor...", show_alert=False)
        import time as _time
        t = _time.time()
        gecikme = (_time.time() - t) * 1000
        await query.edit_message_text(
            f"🏓 **Pong!**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚡ **Gecikme:** `{gecikme:.1f} ms`\n"
            f"🟢 **Bot Durumu:** Aktif & Çalışıyor\n"
            f"🕐 **Saat (TR):** `{datetime.datetime.now(TR_SAAT).strftime('%H:%M:%S')}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n_AZRxGUARD 2.0_",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data='menu_pro_araclar')]]),
            parse_mode='Markdown'
        )
    elif query.data == 'pro20_renk':
        context.user_data['durum'] = 'renk_bekliyor'
        await query.edit_message_text(
            "🎨 **RENK DÖNÜŞTÜRÜCÜ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Renk girin:\n\n"
            "• **HEX:** `#FF5733`\n"
            "• **RGB:** `255 87 51` _(3 sayı boşlukla)_\n\n"
            "_Çıkmak için /iptal yazın_",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_pro_araclar')]]),
            parse_mode='Markdown'
        )
    elif query.data == 'pro20_metin':
        context.user_data['durum'] = 'metin_analiz_bekliyor'
        await query.edit_message_text(
            "📊 **METİN ANALİZÖRÜ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Analiz etmek istediğiniz metni yazın:\n\n"
            "_Çıkmak için /iptal yazın_",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_pro_araclar')]]),
            parse_mode='Markdown'
        )
    elif query.data == 'pro20_rastgele':
        await query.edit_message_text(
            "🎲 **RASTGELE ARAÇLAR**\n━━━━━━━━━━━━━━━━━━━━━━\n\nNe yapmak istersiniz?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔢 Sayı Üret (1–100)", callback_data='r20_sayi'),
                 InlineKeyboardButton("🪙 Para Yüzü", callback_data='r20_para')],
                [InlineKeyboardButton("🎲 Zar At (d6)", callback_data='r20_zar6'),
                 InlineKeyboardButton("🎲 Zar At (d20)", callback_data='r20_zar20')],
                [InlineKeyboardButton("⬅️ Geri", callback_data='menu_pro_araclar')]
            ]),
            parse_mode='Markdown'
        )
    elif query.data == 'r20_sayi':
        sonuc = random.randint(1, 100)
        await query.edit_message_text(
            f"🔢 **RASTGELE SAYI (1–100)**\n━━━━━━━━━━━━━━━━━━━━━━\n\n🎯 **Sonuç: `{sonuc}`**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Tekrar", callback_data='r20_sayi'),
                 InlineKeyboardButton("⬅️ Geri", callback_data='pro20_rastgele')]
            ]),
            parse_mode='Markdown'
        )
    elif query.data == 'r20_para':
        sonuc = random.choice(['🟡 **YAZI**', '🔵 **TURA**'])
        await query.edit_message_text(
            f"🪙 **PARA ATIŞI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n💫 **Sonuç: {sonuc}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Tekrar", callback_data='r20_para'),
                 InlineKeyboardButton("⬅️ Geri", callback_data='pro20_rastgele')]
            ]),
            parse_mode='Markdown'
        )
    elif query.data == 'r20_zar6':
        sonuc = random.randint(1, 6)
        await query.edit_message_text(
            f"🎲 **ZAR ATIŞI (d6)**\n━━━━━━━━━━━━━━━━━━━━━━\n\n🎯 **Sonuç: `{sonuc}`**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Tekrar", callback_data='r20_zar6'),
                 InlineKeyboardButton("⬅️ Geri", callback_data='pro20_rastgele')]
            ]),
            parse_mode='Markdown'
        )
    elif query.data == 'r20_zar20':
        sonuc = random.randint(1, 20)
        await query.edit_message_text(
            f"🎲 **ZAR ATIŞI (d20)**\n━━━━━━━━━━━━━━━━━━━━━━\n\n🎯 **Sonuç: `{sonuc}`**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Tekrar", callback_data='r20_zar20'),
                 InlineKeyboardButton("⬅️ Geri", callback_data='pro20_rastgele')]
            ]),
            parse_mode='Markdown'
        )
    elif query.data == 'pro20_sifrele':
        context.user_data['durum'] = 'sifrele_bekliyor'
        await query.edit_message_text(
            "🔠 **ŞİFRELEME ARAÇLARI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Şifreleme türü ve metni girin:\n\n"
            "• `rot13 Merhaba` — ROT-13\n"
            "• `ters Merhaba` — Ters çevir\n"
            "• `morse SOS` — Morse kodu\n"
            "• `caesar 3 Merhaba` — Caesar (kaydırma)\n\n"
            "_Çıkmak için /iptal yazın_",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_pro_araclar')]]),
            parse_mode='Markdown'
        )
    elif query.data == 'pro20_bmi':
        context.user_data['durum'] = 'bmi_bekliyor'
        await query.edit_message_text(
            "💪 **BMI HESAPLAYICI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Boy (cm) ve kiloyu (kg) boşlukla girin:\n\n"
            "Örnek: `175 70`\n\n"
            "_Çıkmak için /iptal yazın_",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_pro_araclar')]]),
            parse_mode='Markdown'
        )
    elif query.data == 'pro20_yuzde':
        context.user_data['durum'] = 'yuzde_bekliyor'
        await query.edit_message_text(
            "💯 **YÜZDE HESAPLAYICI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Hesaplamak istediğiniz işlemi girin:\n\n"
            "• `%20 500` — 500'ün %20'si\n"
            "• `75 150` — 75, 150'nin %kaçı?\n"
            "• `artis 200 250` — % artış\n"
            "• `azalis 300 240` — % azalış\n\n"
            "_Çıkmak için /iptal yazın_",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_pro_araclar')]]),
            parse_mode='Markdown'
        )
    elif query.data == 'pro_isim_fontu':
        context.user_data['durum'] = 'isim_fontu_bekliyor'
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        await query.edit_message_text(
            "🔤 **İSİM FONTU**\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "İsmini veya istediğin metni yaz, bot sana **50+ farklı font stiliyle** göstersin!\n\n"
            "Örnek: `MAQA` veya `Ahmet`",
            reply_markup=geri, parse_mode='Markdown'
        )

    # ── END 2.0 ARAÇLAR ────────────────────────────────────────
    elif query.data == 'eglence_para_at':
        sonuc = random.choice(['🟡 **YAZI!**', '🔵 **TURA!**'])
        klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton('🔄 Tekrar At', callback_data='eglence_para_at')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_fun')]
        ])
        await query.edit_message_text(
            f"🪙 **PARA ATIŞI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n💫 Sonuç: {sonuc}",
            reply_markup=klavye, parse_mode='Markdown'
        )
    elif query.data == 'eglence_rulet':
        if random.randint(1, 6) == 1:
            desc = "💥 **BANG!**\n_Şanssız bir ruhsun..._"
        else:
            desc = "😮‍💨 **KLIK!**\n_Bu sefer şansın yaver gitti!_"
        klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton('🔄 Tekrar', callback_data='eglence_rulet')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_fun')]
        ])
        await query.edit_message_text(
            f"🎯 **RUS RULETİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n{desc}",
            reply_markup=klavye, parse_mode='Markdown'
        )
    elif query.data == 'eglence_kehanet':
        kehanetler = [
            "✨ Büyük bir fırsat kapında seni bekliyor!",
            "⚠️ Bugün önemli kararlar almaktan kaçın.",
            "💫 Eski bir arkadaşından haber alacaksın.",
            "🌟 Başarı çok yakın, vazgeçme!",
            "🌊 Değişim rüzgarları esiyor, hazır ol.",
            "🍀 Şans bugün seninle — bir şans dene!",
            "🔮 Gizem içinde bir cevap yatıyor.",
            "💡 Aklındaki fikir düşündüğünden daha değerli.",
            "🌙 Geceleri daha çok çalışman gerekiyor.",
            "☀️ Sabah güzel haberler gelecek.",
            "🦋 Küçük bir değişim büyük farklar yaratır.",
            "🎭 Masken düşüyor, gerçek yüzün ortaya çıkıyor.",
            "🏆 Bugün şansını denemek için iyi bir gün.",
            "🎯 Hedefine çok yakınsın, biraz daha sabret.",
            "💎 Değerini bil, kimse seni küçümseyemez.",
        ]
        klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton('🔮 Yeni Kehanet', callback_data='eglence_kehanet')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_fun')]
        ])
        await query.edit_message_text(
            f"🔮 **KEHANET**\n━━━━━━━━━━━━━━━━━━━━━━\n\n{random.choice(kehanetler)}",
            reply_markup=klavye, parse_mode='Markdown'
        )
    # ── 🔮 AKİNATÖR CALLBACK'LERİ ─────────────────────────────
    elif query.data == 'eglence_akinator':
        await query.answer()
        aki_intro_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 BAŞLA!", callback_data='aki_baslat')],
            [InlineKeyboardButton("⬅️ Geri", callback_data='menu_fun')]
        ])
        karsilama_caption = (
            "🔮 *AKİNATÖR'E HOŞ GELDİN!*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🧞 *Ben aklındaki karakteri tahmin edeceğim!*\n\n"
            "💡 Gerçek, hayali ya da herkesçe tanınan\n"
            "herhangi bir karakter düşünebilirsin.\n\n"
            "🎯 Sorularıma dürüstçe cevap ver,\n"
            "ben gerisini hallederim! 😏\n\n"
            "👇 Hazırsan başlayalım!"
        )
        try:
            with open(_AKINATOR_IMG_YOL, 'rb') as _f:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=_f,
                    caption=karsilama_caption,
                    reply_markup=aki_intro_klavye,
                    parse_mode='Markdown'
                )
        except Exception:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=karsilama_caption,
                reply_markup=aki_intro_klavye,
                parse_mode='Markdown'
            )
    elif query.data == 'aki_baslat':
        await query.answer()
        await _aki_play_baslat_callback(query, context)
    elif query.data.startswith('aki_play_'):
        await _aki_cevap_callback(query, context)
    elif query.data == 'aki_win_y':
        await _aki_win_callback(query, context, True)
    elif query.data == 'aki_win_n':
        await _aki_win_callback(query, context, False)
    # ──────────────────────────────────────────────────────────
    elif query.data == 'menu_ai':
        context.user_data['mevcut_kategori'] = '🤖 AI Asistan'
        context.user_data['durum'] = 'ai_sohbet_bekliyor'
        gecmis_sayi = len(context.user_data.get('ai_gecmis', []))
        ai_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton('🗑️ Geçmişi Temizle', callback_data='ai_gecmis_sil')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ])
        await query.edit_message_text(
            f"🤖 **AI ASİSTAN — Gemini 2.0 Flash**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Merhaba! Sana nasıl yardımcı olabilirim? 😊\n\n"
            f"Herhangi bir soru sorabilirsin. Mesajını yaz ve gönder!\n\n"
            f"📊 Sohbet geçmişi: `{gecmis_sayi}` mesaj\n"
            f"_/iptal ile durumu sıfırlayabilirsin_",
            reply_markup=ai_klavye, parse_mode='Markdown'
        )
    elif query.data == 'ai_gecmis_sil':
        context.user_data['ai_gecmis'] = []
        context.user_data['durum'] = 'ai_sohbet_bekliyor'
        ai_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton('🗑️ Geçmişi Temizle', callback_data='ai_gecmis_sil')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ])
        await query.edit_message_text(
            "🤖 **AI ASİSTAN**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Sohbet geçmişi temizlendi!\n\n"
            "Yeni sorunuzu yazabilirsiniz:",
            reply_markup=ai_klavye, parse_mode='Markdown'
        )
    elif query.data == 'menu_video_indir':
        context.user_data['mevcut_kategori'] = '📥 Video İndir'
        context.user_data['durum'] = 'vid_indir_url_bekliyor'
        vid_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ])
        await query.edit_message_text(
            "📥 **VİDEO İNDİRİCİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎬 Desteklenen platformlar:\n"
            "▸ YouTube · TikTok · Instagram\n"
            "▸ Twitter/X · Facebook · Dailymotion\n"
            "▸ Reddit · Pinterest · Snapchat\n"
            "▸ ve 1000+ platform!\n\n"
            "📎 **Video linkini şimdi gönder:**\n"
            "_Sonra Video veya Sadece Ses seçimi yapacaksın._\n\n"
            "_/iptal ile çıkabilirsin_",
            reply_markup=vid_klavye, parse_mode='Markdown'
        )
    elif query.data == 'vid_dl_video':
        url = context.user_data.pop('vid_indir_url', None)
        if not url:
            await query.answer("❌ URL bulunamadı, tekrar deneyin.", show_alert=True)
            return
        bekle_msg = await query.edit_message_text(
            "⏳ **Video indiriliyor...**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 `{url[:60]}...`\n\n_Bu işlem 30-60 saniye sürebilir._",
            parse_mode='Markdown'
        )
        await _vid_indir_ve_gonder(update, context, url, mod='video', bekle_msg=bekle_msg)
    elif query.data == 'vid_dl_ses':
        url = context.user_data.pop('vid_indir_url', None)
        if not url:
            await query.answer("❌ URL bulunamadı, tekrar deneyin.", show_alert=True)
            return
        bekle_msg = await query.edit_message_text(
            "⏳ **Ses indiriliyor...**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 `{url[:60]}...`\n\n_Bu işlem 30-60 saniye sürebilir._",
            parse_mode='Markdown'
        )
        await _vid_indir_ve_gonder(update, context, url, mod='ses', bekle_msg=bekle_msg)
    elif query.data == 'pro_sans':
        kat = context.user_data.pop('mevcut_kategori', '') or ''
        await log_kanali_gonder(context.bot, update, kategori=kat, komut='🎱 Şans Topu')
        await query.edit_message_text(
            sans_cevap_getir(),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎱 Tekrar Sor", callback_data='pro_sans')],
                [InlineKeyboardButton(strings['btn_back'], callback_data='menu_fun')]
            ]),
            parse_mode='Markdown'
        )

    elif query.data == 'menu_video_olusturucu':
        context.user_data['mevcut_kategori'] = '🎬 Video Oluşturucu'
        vo_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Yazı Ekle", callback_data='vyo_baslat'),
             InlineKeyboardButton("✂️ Video Kırp", callback_data='ved_kirp_baslat')],
            [InlineKeyboardButton("⚡ Hız Değiştir", callback_data='ved_hiz_baslat'),
             InlineKeyboardButton("🔄 Döndür", callback_data='ved_don_baslat')],
            [InlineKeyboardButton("🎵 Ses Çıkar", callback_data='ved_ses_baslat'),
             InlineKeyboardButton("🔇 Sessizleştir", callback_data='ved_sessiz_baslat')],
            [InlineKeyboardButton("📸 Kare Al", callback_data='ved_kare_baslat'),
             InlineKeyboardButton("🎞️ GIF Yap", callback_data='ved_gif_baslat')],
            [InlineKeyboardButton("📐 Boyutlandır", callback_data='ved_boyut_baslat'),
             InlineKeyboardButton("🎨 Filtre Uygula", callback_data='ved_filtre_baslat')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ])
        vo_metin = (
            "🎬 **VİDEO EDİTÖR — MONTAJ MERKEZİ**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 **10 Güçlü Özellik:**\n"
            "✂️ Kırp  •  ⚡ Hız  •  🔄 Döndür  •  🎵 Ses Çıkar\n"
            "🔇 Sessiz  •  📸 Kare Al  •  🎞️ GIF  •  📐 Boyut\n"
            "🎨 Filtre  •  🎬 Yazı Ekle\n\n"
            "_Bir özellik seçin ve videoyu gönderin!_"
        )
        try:
            await query.edit_message_text(vo_metin, reply_markup=vo_klavye, parse_mode='Markdown')
        except Exception:
            await query.message.reply_text(vo_metin, reply_markup=vo_klavye, parse_mode='Markdown')
            try:
                await query.message.delete()
            except Exception:
                pass
    elif query.data == 'ved_kirp_baslat':
        context.user_data['durum'] = 'ved_kirp_video_bekle'
        context.user_data['ved'] = {}
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await query.edit_message_text(
            "✂️ **VİDEO KIRPMA**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📹 Kırpmak istediğin **videoyu gönder:**\n\n"
            "⚠️ _Maks 49 MB — MP4, MOV, AVI_",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'ved_hiz_baslat':
        context.user_data['durum'] = 'ved_hiz_video_bekle'
        context.user_data['ved'] = {}
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await query.edit_message_text(
            "⚡ **HIZ DEĞİŞTİRME**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📹 Hızını değiştirmek istediğin **videoyu gönder:**\n\n"
            "⚠️ _Maks 49 MB — MP4, MOV, AVI_",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'ved_don_baslat':
        context.user_data['durum'] = 'ved_don_video_bekle'
        context.user_data['ved'] = {}
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await query.edit_message_text(
            "🔄 **VİDEO DÖNDÜRME**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📹 Döndürmek istediğin **videoyu gönder:**\n\n"
            "⚠️ _Maks 49 MB — MP4, MOV, AVI_",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'ved_ses_baslat':
        context.user_data['durum'] = 'ved_ses_video_bekle'
        context.user_data['ved'] = {}
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await query.edit_message_text(
            "🎵 **SES ÇIKARMA**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📹 Sesini çıkarmak istediğin **videoyu gönder:**\n\n"
            "✅ _Video otomatik MP3'e çevrilir_\n"
            "⚠️ _Maks 49 MB_",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'ved_sessiz_baslat':
        context.user_data['durum'] = 'ved_sessiz_video_bekle'
        context.user_data['ved'] = {}
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await query.edit_message_text(
            "🔇 **VİDEO SESSİZLEŞTİRME**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📹 Sesini kesmek istediğin **videoyu gönder:**\n\n"
            "✅ _Sesin tamamı kaldırılır_\n"
            "⚠️ _Maks 49 MB_",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'ved_kare_baslat':
        context.user_data['durum'] = 'ved_kare_video_bekle'
        context.user_data['ved'] = {}
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await query.edit_message_text(
            "📸 **KARE ALMA (THUMBNAIL)**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📹 Kare almak istediğin **videoyu gönder:**\n\n"
            "✅ _İstediğin saniyeden yüksek kaliteli fotoğraf_\n"
            "⚠️ _Maks 49 MB_",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'ved_gif_baslat':
        context.user_data['durum'] = 'ved_gif_video_bekle'
        context.user_data['ved'] = {}
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await query.edit_message_text(
            "🎞️ **VİDEO → GIF**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📹 GIF'e çevirmek istediğin **videoyu gönder:**\n\n"
            "✅ _İlk 6 saniye otomatik GIF'e dönüştürülür_\n"
            "⚠️ _Maks 49 MB_",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'ved_boyut_baslat':
        context.user_data['durum'] = 'ved_boyut_video_bekle'
        context.user_data['ved'] = {}
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await query.edit_message_text(
            "📐 **VİDEO BOYUTLANDIRMA**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📹 Boyutunu değiştirmek istediğin **videoyu gönder:**\n\n"
            "⚠️ _Maks 49 MB — MP4, MOV, AVI_",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'ved_filtre_baslat':
        context.user_data['durum'] = 'ved_filtre_video_bekle'
        context.user_data['ved'] = {}
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await query.edit_message_text(
            "🎨 **VİDEO FİLTRE**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📹 Filtre uygulamak istediğin **videoyu gönder:**\n\n"
            "⚠️ _Maks 49 MB — MP4, MOV, AVI_",
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data.startswith('ved_hiz_sec_'):
        hiz = query.data.replace('ved_hiz_sec_', '')
        hiz_str = hiz.replace('_', '.')
        video_path = context.user_data.get('ved', {}).get('video_path', '')
        if not video_path:
            await query.edit_message_text("❌ Video bulunamadı. Tekrar deneyin.", parse_mode='Markdown')
            return
        islem_msg = await query.edit_message_text(f"⚡ **Video {hiz_str}x hıza getiriliyor...**\n_Bu işlem biraz sürebilir._", parse_mode='Markdown')
        try:
            import subprocess as _sp, os as _os
            cikis = video_path.replace('.mp4', f'_hiz_{hiz}.mp4')
            hiz_val = float(hiz_str)
            pts = round(1 / hiz_val, 4)
            # atempo filtresi yalnızca 0.5-2.0 arasını destekler; daha yüksek için zincirle
            if hiz_val > 2.0:
                atempo_str = 'atempo=2.0,atempo=' + str(round(hiz_val / 2.0, 6)).rstrip('0').rstrip('.')
            elif hiz_val < 0.5:
                atempo_str = 'atempo=0.5,atempo=' + str(round(hiz_val / 0.5, 6)).rstrip('0').rstrip('.')
            else:
                atempo_str = f'atempo={hiz_val}'
            # Ses akışı var mı kontrol et
            _probe = await asyncio.to_thread(lambda: _sp.run(
                ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                 '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', video_path],
                capture_output=True, text=True, timeout=15
            ))
            has_audio = 'audio' in (_probe.stdout or '')
            if has_audio:
                cmd = ['ffmpeg', '-i', video_path,
                       '-filter_complex', f'[0:v]setpts={pts}*PTS[v];[0:a]{atempo_str}[a]',
                       '-map', '[v]', '-map', '[a]',
                       '-c:v', 'libx264', '-preset', 'fast', '-c:a', 'aac',
                       cikis, '-y']
            else:
                cmd = ['ffmpeg', '-i', video_path,
                       '-vf', f'setpts={pts}*PTS',
                       '-an', '-c:v', 'libx264', '-preset', 'fast',
                       cikis, '-y']
            result = await asyncio.to_thread(lambda: _sp.run(cmd, capture_output=True, timeout=180))
            if result.returncode != 0 or not _os.path.exists(cikis):
                raise Exception("FFmpeg başarısız")
            with open(cikis, 'rb') as vf:
                await update.effective_chat.send_video(
                    video=vf,
                    caption=f"✅ **Video {hiz_str}x hıza getirildi!**\n_AZRxGUARD Video Editör_ 🎬",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Video Editör", callback_data='menu_video_olusturucu'), InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')]])
                )
            await islem_msg.delete()
            for f in [video_path, cikis]:
                try: _os.remove(f)
                except: pass
        except Exception as e:
            logger.error(f"Hız hatası: {e}")
            await islem_msg.edit_text("❌ İşlem başarısız. Farklı bir video deneyin.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Tekrar", callback_data='ved_hiz_baslat'), InlineKeyboardButton("🏠", callback_data='go_home')]]))
    elif query.data.startswith('ved_don_sec_'):
        derece = query.data.replace('ved_don_sec_', '')
        video_path = context.user_data.get('ved', {}).get('video_path', '')
        if not video_path:
            await query.edit_message_text("❌ Video bulunamadı.", parse_mode='Markdown')
            return
        islem_msg = await query.edit_message_text(f"🔄 **Video {derece}° döndürülüyor...**", parse_mode='Markdown')
        try:
            import subprocess as _sp, os as _os
            transpoze_map = {'90': 'transpose=1', '180': 'transpose=1,transpose=1', '270': 'transpose=2'}
            filtre = transpoze_map.get(derece, 'transpose=1')
            cikis = video_path.replace('.mp4', f'_don_{derece}.mp4')
            cmd = ['ffmpeg', '-i', video_path, '-vf', filtre, '-c:a', 'copy', cikis, '-y']
            result = await asyncio.to_thread(lambda: _sp.run(cmd, capture_output=True, timeout=180))
            if result.returncode != 0 or not _os.path.exists(cikis):
                raise Exception("FFmpeg başarısız")
            with open(cikis, 'rb') as vf:
                await update.effective_chat.send_video(
                    video=vf,
                    caption=f"✅ **Video {derece}° döndürüldü!**\n_AZRxGUARD Video Editör_ 🎬",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Video Editör", callback_data='menu_video_olusturucu'), InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')]])
                )
            await islem_msg.delete()
            for f in [video_path, cikis]:
                try: _os.remove(f)
                except: pass
        except Exception as e:
            logger.error(f"Döndürme hatası: {e}")
            await islem_msg.edit_text("❌ İşlem başarısız.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Tekrar", callback_data='ved_don_baslat'), InlineKeyboardButton("🏠", callback_data='go_home')]]))
    elif query.data.startswith('ved_boyut_sec_'):
        boyut = query.data.replace('ved_boyut_sec_', '')
        video_path = context.user_data.get('ved', {}).get('video_path', '')
        if not video_path:
            await query.edit_message_text("❌ Video bulunamadı.", parse_mode='Markdown')
            return
        islem_msg = await query.edit_message_text(f"📐 **Video {boyut}p yapılıyor...**", parse_mode='Markdown')
        try:
            import subprocess as _sp, os as _os
            boyut_map = {'1080': '1920:1080', '720': '1280:720', '480': '854:480', '360': '640:360'}
            scale = boyut_map.get(boyut, '1280:720')
            cikis = video_path.replace('.mp4', f'_{boyut}p.mp4')
            cmd = ['ffmpeg', '-i', video_path, '-vf',
                   f'scale={scale}:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2',
                   '-c:a', 'copy', cikis, '-y']
            result = await asyncio.to_thread(lambda: _sp.run(cmd, capture_output=True, timeout=180))
            if result.returncode != 0 or not _os.path.exists(cikis):
                raise Exception("FFmpeg başarısız")
            with open(cikis, 'rb') as vf:
                await update.effective_chat.send_video(
                    video=vf,
                    caption=f"✅ **Video {boyut}p boyutlandırıldı!**\n_AZRxGUARD Video Editör_ 🎬",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Video Editör", callback_data='menu_video_olusturucu'), InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')]])
                )
            await islem_msg.delete()
            for f in [video_path, cikis]:
                try: _os.remove(f)
                except: pass
        except Exception as e:
            logger.error(f"Boyut hatası: {e}")
            await islem_msg.edit_text("❌ İşlem başarısız.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Tekrar", callback_data='ved_boyut_baslat'), InlineKeyboardButton("🏠", callback_data='go_home')]]))
    elif query.data.startswith('ved_filtre_sec_'):
        filtre_adi = query.data.replace('ved_filtre_sec_', '')
        video_path = context.user_data.get('ved', {}).get('video_path', '')
        if not video_path:
            await query.edit_message_text("❌ Video bulunamadı.", parse_mode='Markdown')
            return
        filtre_map = {
            'bw': ('⬛ Siyah-Beyaz', 'hue=s=0'),
            'sepia': ('🟫 Sepia', 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131'),
            'parlak': ('☀️ Parlak', 'eq=brightness=0.06:saturation=1.4:contrast=1.1'),
            'karanlik': ('🌑 Karanlık', 'eq=brightness=-0.12:saturation=0.7'),
            'vintage': ('🎞️ Vintage', 'curves=vintage'),
        }
        filtre_bilgi = filtre_map.get(filtre_adi, ('Filtre', 'hue=s=0'))
        filtre_ad, filtre_str = filtre_bilgi
        islem_msg = await query.edit_message_text(f"🎨 **{filtre_ad} filtresi uygulanıyor...**", parse_mode='Markdown')
        try:
            import subprocess as _sp, os as _os
            cikis = video_path.replace('.mp4', f'_filtre_{filtre_adi}.mp4')
            cmd = ['ffmpeg', '-i', video_path, '-vf', filtre_str, '-c:a', 'copy', cikis, '-y']
            result = await asyncio.to_thread(lambda: _sp.run(cmd, capture_output=True, timeout=180))
            if result.returncode != 0 or not _os.path.exists(cikis):
                raise Exception("FFmpeg başarısız")
            with open(cikis, 'rb') as vf:
                await update.effective_chat.send_video(
                    video=vf,
                    caption=f"✅ **{filtre_ad} filtresi uygulandı!**\n_AZRxGUARD Video Editör_ 🎨",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Video Editör", callback_data='menu_video_olusturucu'), InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')]])
                )
            await islem_msg.delete()
            for f in [video_path, cikis]:
                try: _os.remove(f)
                except: pass
        except Exception as e:
            logger.error(f"Filtre hatası: {e}")
            await islem_msg.edit_text("❌ İşlem başarısız.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Tekrar", callback_data='ved_filtre_baslat'), InlineKeyboardButton("🏠", callback_data='go_home')]]))
    elif query.data == 'vyo_baslat':
        context.user_data['durum'] = 'vyo_video_bekle'
        context.user_data['vyo'] = {}
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await query.edit_message_text(
            "🎬 **VİDEO YAZI EKLEME**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📹 **LÜTFEN FİLİGRAN EKLEMEK İSTEDİĞİNİZ VİDEOYU ATIN**\n\n"
            "⚠️ _Desteklenen formatlar: MP4, MOV, AVI, MKV_\n"
            "⚠️ _Maksimum boyut: 49 MB_",
            reply_markup=geri,
            parse_mode='Markdown'
        )
    elif query.data.startswith('vyo_boyut_'):
        boyut_kod = query.data.replace('vyo_boyut_', '')
        boyut_map = {'kucuk': 28, 'orta': 48, 'buyuk': 70, 'dev': 96}
        boyut_adi_map = {'kucuk': '🔡 Küçük', 'orta': '🔤 Orta', 'buyuk': '🔠 Büyük', 'dev': '💬 Dev'}
        context.user_data.setdefault('vyo', {})['boyut'] = boyut_map.get(boyut_kod, 48)
        boyut_adi = boyut_adi_map.get(boyut_kod, 'Orta')
        konum_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("↗️ SAĞ YUKARI", callback_data='vyo_konum_sag_yukari'),
             InlineKeyboardButton("↖️ SOL YUKARI", callback_data='vyo_konum_sol_yukari')],
            [InlineKeyboardButton("↘️ SAĞ AŞAĞI", callback_data='vyo_konum_sag_asagi'),
             InlineKeyboardButton("↙️ SOL AŞAĞI", callback_data='vyo_konum_sol_asagi')],
            [InlineKeyboardButton("🎯 VİDEO ORTASI", callback_data='vyo_konum_orta')],
            [InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]
        ])
        await query.edit_message_text(
            f"🎬 **VİDEO YAZI EKLEME**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Boyut: **{boyut_adi}**\n\n"
            "📍 **Yazının konumunu seçin:**",
            reply_markup=konum_klavye,
            parse_mode='Markdown'
        )
    elif query.data.startswith('vyo_konum_'):
        konum = query.data.replace('vyo_konum_', '')
        context.user_data.setdefault('vyo', {})['konum'] = konum
        konum_adi = {
            'sag_yukari': '📍 Sağ Yukarı', 'sol_yukari': '📍 Sol Yukarı',
            'sag_asagi': '📍 Sağ Aşağı', 'sol_asagi': '📍 Sol Aşağı',
            'orta': '📍 Video Ortası'
        }.get(konum, konum)
        stil_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("👻 HAYALET YAZI", callback_data='vyo_stil_hayalet'),
             InlineKeyboardButton("✍️ NORMAL YAZI", callback_data='vyo_stil_normal')],
            [InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]
        ])
        await query.edit_message_text(
            f"🎬 **VİDEO YAZI EKLEME**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Konum: **{konum_adi}**\n\n"
            "🖊️ **Yazı stilini seçin:**",
            reply_markup=stil_klavye,
            parse_mode='Markdown'
        )
    elif query.data.startswith('vyo_stil_'):
        stil = query.data.replace('vyo_stil_', '')
        context.user_data.setdefault('vyo', {})['stil'] = stil
        stil_adi = '👻 Hayalet Yazı' if stil == 'hayalet' else '✍️ Normal Yazı'
        renk_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔴 Kırmızı", callback_data='vyo_renk_kirmizi'),
             InlineKeyboardButton("🟠 Turuncu", callback_data='vyo_renk_turuncu'),
             InlineKeyboardButton("🟡 Sarı", callback_data='vyo_renk_sari')],
            [InlineKeyboardButton("🟢 Yeşil", callback_data='vyo_renk_yesil'),
             InlineKeyboardButton("🔵 Mavi", callback_data='vyo_renk_mavi'),
             InlineKeyboardButton("🟣 Mor", callback_data='vyo_renk_mor')],
            [InlineKeyboardButton("🟤 Kahve", callback_data='vyo_renk_kahve'),
             InlineKeyboardButton("⚫ Siyah", callback_data='vyo_renk_siyah'),
             InlineKeyboardButton("⚪ Beyaz", callback_data='vyo_renk_beyaz')],
            [InlineKeyboardButton("🩷 Pembe", callback_data='vyo_renk_pembe'),
             InlineKeyboardButton("🩵 Cyan", callback_data='vyo_renk_cyan'),
             InlineKeyboardButton("🩶 Gri", callback_data='vyo_renk_gri')],
            [InlineKeyboardButton("🥇 Altın", callback_data='vyo_renk_altin'),
             InlineKeyboardButton("🩻 Gümüş", callback_data='vyo_renk_gumus'),
             InlineKeyboardButton("🟦 Lacivert", callback_data='vyo_renk_lacivert')],
            [InlineKeyboardButton("🌈 RENKSİN", callback_data='vyo_renk_renksin')],
            [InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]
        ])
        await query.edit_message_text(
            f"🎬 **VİDEO YAZI EKLEME**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Stil: **{stil_adi}**\n\n"
            "🎨 **Yazı rengini seçin:**",
            reply_markup=renk_klavye,
            parse_mode='Markdown'
        )
    elif query.data.startswith('vyo_renk_'):
        renk = query.data.replace('vyo_renk_', '')
        vyo = context.user_data.get('vyo', {})
        vyo['renk'] = renk
        context.user_data['vyo'] = vyo
        context.user_data['durum'] = None

        video_fid = vyo.get('video_fid')
        yazi = vyo.get('yazi', '')
        konum = vyo.get('konum', 'orta')
        stil = vyo.get('stil', 'normal')

        if not video_fid or not yazi:
            await query.edit_message_text("❌ Bir hata oluştu. Lütfen tekrar deneyin.", parse_mode='Markdown')
            return

        renk_adi = {
            'kirmizi':'🔴 Kırmızı','turuncu':'🟠 Turuncu','sari':'🟡 Sarı',
            'yesil':'🟢 Yeşil','mavi':'🔵 Mavi','mor':'🟣 Mor',
            'kahve':'🟤 Kahve','siyah':'⚫ Siyah','beyaz':'⚪ Beyaz',
            'pembe':'🩷 Pembe','cyan':'🩵 Cyan','gri':'🩶 Gri',
            'altin':'🥇 Altın','gumus':'🩻 Gümüş','lacivert':'🟦 Lacivert',
            'renksin':'🌈 Renksin'
        }.get(renk, renk)

        islem_msg = await query.edit_message_text(
            f"⚙️ **Video işleniyor...**\n\n"
            f"🎨 Renk: {renk_adi}\n"
            "⏳ Lütfen bekleyin...",
            parse_mode='Markdown'
        )
        try:
            dosya = await context.bot.get_file(video_fid)
            import tempfile, os as _os
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_in:
                giris_yolu = tmp_in.name
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_out:
                cikti_yolu = tmp_out.name

            await dosya.download_to_drive(giris_yolu)
            boyut = vyo.get('boyut', 52)
            basari = await asyncio.to_thread(vyo_ffmpeg_yazi_ekle, giris_yolu, cikti_yolu, yazi, konum, stil, renk, boyut)

            if basari and _os.path.getsize(cikti_yolu) > 0:
                with open(cikti_yolu, 'rb') as vf:
                    await update.effective_chat.send_video(
                        video=vf,
                        caption="✅ **Yazı başarıyla eklendi!**\n\n"
                                f"📝 Yazı: `{html.escape(yazi)}`\n"
                                f"🎨 Renk: {renk_adi}",
                        parse_mode='Markdown'
                    )
                await islem_msg.edit_text(
                    "✅ **Video hazır!** Yukarıda görebilirsiniz.\n\n"
                    "Yeni bir video için /start diyebilirsiniz.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🎬 Yeni Video", callback_data='vyo_baslat'),
                        InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')
                    ]]),
                    parse_mode='Markdown'
                )
            else:
                await islem_msg.edit_text(
                    "❌ **Video işlenirken hata oluştu.**\n"
                    "Lütfen farklı bir video deneyin.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Tekrar Dene", callback_data='vyo_baslat'),
                        InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')
                    ]]),
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"VYO ffmpeg hatası: {e}")
            await islem_msg.edit_text(
                "❌ **Bir hata oluştu.** Lütfen tekrar deneyin.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Tekrar Dene", callback_data='vyo_baslat'),
                    InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')
                ]]),
                parse_mode='Markdown'
            )
        finally:
            for p in [giris_yolu, cikti_yolu]:
                try:
                    _os.unlink(p)
                except Exception:
                    pass

    # ─────────────────────────────────────────────────────────────
    # 📱 TELEFON FİYATLARI KATEGORİSİ
    # ─────────────────────────────────────────────────────────────
    elif query.data == 'menu_telefon_fiyatlari':
        context.user_data['mevcut_kategori'] = '📱 Telefon Fiyatları'
        satir = []
        markalar = list(TELEFON_VERITABANI.items())
        for i in range(0, len(markalar), 2):
            sut = []
            for mid, mdata in markalar[i:i+2]:
                sut.append(InlineKeyboardButton(f"{mdata['emoji']} {mdata['ad']}", callback_data=f'tfn_m_{mid}'))
            satir.append(sut)
        satir.append([InlineKeyboardButton(strings['btn_back'], callback_data='go_home')])
        await query.edit_message_text(
            "📱 **TELEFON FİYATLARI**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🏪 **Zoommer.ge** güncel fiyatları\n"
            "📊 Özellikler + Oyun FPS verileri\n\n"
            "Marka seçin:",
            reply_markup=InlineKeyboardMarkup(satir),
            parse_mode='Markdown'
        )

    elif query.data.startswith('tfn_m_'):
        mid = query.data[6:]
        if mid not in TELEFON_VERITABANI:
            await query.answer("❌ Marka bulunamadı", show_alert=True)
            return
        mdata = TELEFON_VERITABANI[mid]
        modeller = mdata['modeller']
        context.user_data['tfn_liste'] = modeller
        context.user_data['tfn_marka'] = mid
        await _tfn_sayfa_goster(query, context, mid, 0)

    elif query.data.startswith('tfn_p_'):
        parca = query.data[6:].rsplit('_', 1)
        if len(parca) != 2:
            return
        mid, sayfa_str = parca[0], parca[1]
        try:
            sayfa = int(sayfa_str)
        except Exception:
            sayfa = 0
        await _tfn_sayfa_goster(query, context, mid, sayfa)

    elif query.data.startswith('tfn_s_'):
        idx_str = query.data[6:]
        try:
            idx = int(idx_str)
        except Exception:
            await query.answer("❌ Hata", show_alert=True)
            return
        liste = context.user_data.get('tfn_liste', [])
        mid = context.user_data.get('tfn_marka', '')
        if idx >= len(liste):
            await query.answer("❌ Model bulunamadı", show_alert=True)
            return
        telefon_adi = liste[idx]
        marka_adi = TELEFON_VERITABANI.get(mid, {}).get('ad', '')
        tam_ad = f"{marka_adi} {telefon_adi}" if not telefon_adi.lower().startswith(marka_adi.lower().split()[0].lower()) else telefon_adi
        fiyat_str = fiyat_getir(tam_ad, marka_adi)
        specs = TELEFON_SPECS_DB.get(tam_ad) or TELEFON_SPECS_DB.get(telefon_adi)
        fps_data = TELEFON_FPS_DB.get(tam_ad) or TELEFON_FPS_DB.get(telefon_adi)

        metin = f"📱 **{html.escape(tam_ad)}**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        metin += f"🏷️ **FİYAT:**\n{fiyat_str}\n\n"
        metin += f"━━━━━━━━━━━━━━━━━━━━━━\n"

        if specs:
            metin += f"⚙️ **TEKNİK ÖZELLİKLER:**\n"
            metin += f"• 5G: {'✅ Var' if specs.get('5g') else '❌ Yok'}\n"
            metin += f"• RAM: {specs.get('ram', '—')}\n"
            metin += f"• Depolama: {specs.get('depolama', '—')}\n"
            metin += f"• SIM: {specs.get('sim', '—')} slot\n"
            metin += f"• İşlemci: {specs.get('islemci', '—')}\n"
            metin += f"• Batarya: {specs.get('batarya', '—')}\n"
            metin += f"• Ekran: {specs.get('ekran', '—')}\n"
            metin += f"• Kamera: {specs.get('kamera', '—')}\n"
            metin += f"• OS: {specs.get('os', '—')}\n"
            metin += f"• Çıkış: {specs.get('cikis', '—')}\n"
            metin += f"• IMEI: Çift ({'Dual SIM' if specs.get('sim', 1) >= 2 else 'Tek SIM'})\n"
        else:
            metin += f"⚙️ **TEKNİK ÖZELLİKLER:**\n"
            metin += f"_Detaylı spec bilgisi için Zoommer.ge'yi ziyaret edin_\n"

        metin += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"

        if fps_data:
            metin += f"🎮 **OYUN PERFORMANSI:**\n"
            metin += f"• 🔫 PUBG Mobile: **{fps_data['pubg'][0]}** — {fps_data['pubg'][1]}\n"
            metin += f"• 🎖️ COD Mobile: **{fps_data['cod'][0]}** — {fps_data['cod'][1]}\n"
            metin += f"• 🌸 Genshin Impact: **{fps_data['genshin'][0]}** — {fps_data['genshin'][1]}\n"
            metin += f"• 🔥 Free Fire: **{fps_data['ff'][0]}** — {fps_data['ff'][1]}\n"
        else:
            metin += f"🎮 **OYUN PERFORMANSI:**\n"
            metin += f"• 🔫 PUBG Mobile: _(Cihaza göre değişir)_\n"
            metin += f"• 🎖️ COD Mobile: _(Cihaza göre değişir)_\n"
            metin += f"• 🌸 Genshin Impact: _(Cihaza göre değişir)_\n"
            metin += f"• 🔥 Free Fire: _(Cihaza göre değişir)_\n"

        sorgu = urllib.parse.quote(tam_ad)
        metin += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
        metin += f"🛒 [Zoommer.ge'de İncele](https://zoommer.ge/search?q={sorgu})"

        geri_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"⬅️ {TELEFON_VERITABANI.get(mid, {}).get('ad', 'Geri')}", callback_data=f'tfn_m_{mid}')],
            [InlineKeyboardButton("📱 Tüm Markalar", callback_data='menu_telefon_fiyatlari')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')],
        ])
        try:
            await query.edit_message_text(metin, reply_markup=geri_klavye, parse_mode='Markdown', disable_web_page_preview=True)
        except Exception:
            await query.edit_message_text(metin[:4096], reply_markup=geri_klavye, parse_mode='Markdown', disable_web_page_preview=True)

    elif query.data == 'menu_apk_obb':
        dosyalar = apk_dosyalari_yukle()
        if not dosyalar:
            _apk_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data='go_home')]])
            _apk_txt = "📦 **APK-OBB-CONFİG**\n━━━━━━━━━━━━━━━━━━━━━━\n\n📭 Henüz hiç dosya yüklenmemiş."
        else:
            _apk_satirlar = []
            for uid, bilgi in dosyalar.items():
                _apk_satirlar.append([InlineKeyboardButton(f"📦 {bilgi['isim']}", callback_data=f'apk_dl_{uid}')])
            _apk_satirlar.append([InlineKeyboardButton("⬅️ Geri", callback_data='go_home')])
            _apk_kb = InlineKeyboardMarkup(_apk_satirlar)
            _apk_txt = (
                f"📦 **APK-OBB-CONFİG**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📁 **{len(dosyalar)} dosya mevcut.**\n"
                f"İndirmek istediğin dosyayı seç:"
            )
        try:
            await query.edit_message_text(_apk_txt, reply_markup=_apk_kb, parse_mode='Markdown')
        except Exception:
            try:
                await query.message.reply_text(_apk_txt, reply_markup=_apk_kb, parse_mode='Markdown')
                await query.message.delete()
            except Exception:
                await query.message.reply_text(_apk_txt, reply_markup=_apk_kb, parse_mode='Markdown')

    elif query.data.startswith('apk_dl_'):
        dosya_uuid = query.data[7:]
        dosyalar = apk_dosyalari_yukle()
        if dosya_uuid not in dosyalar:
            await query.answer("❌ Dosya bulunamadı!", show_alert=True)
        else:
            bilgi = dosyalar[dosya_uuid]
            geri_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data='menu_apk_obb')]])
            caption_metin = f"📦 {bilgi['aciklama']}"
            try:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=bilgi['file_id'],
                    caption=caption_metin,
                    reply_markup=geri_kb
                )
                await query.answer("✅ Dosya gönderiliyor...")
            except Exception as apk_dl_err:
                logger.error(f"APK menü indirme hatası: {apk_dl_err}")
                await query.answer("❌ Gönderim hatası!", show_alert=True)

    elif query.data == 'menu_sohbet_araclari':
        context.user_data['mevcut_kategori'] = '💬 Sohbet Araçları'
        sa_klavye = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(strings.get('btn_sa_qr', '📱 QR Kod'), callback_data='sa_qr'),
                InlineKeyboardButton(strings.get('btn_sa_url', '🌐 URL Kısalt'), callback_data='sa_url'),
            ],
            [
                InlineKeyboardButton(strings.get('btn_sa_kimlik', '🎭 Sahte Kimlik'), callback_data='sa_kimlik'),
                InlineKeyboardButton(strings.get('btn_sa_tarih', '📅 Yaş/Tarih'), callback_data='sa_tarih'),
            ],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')],
        ])
        await query.edit_message_text(
            ft(strings.get('sohbet_araclari_welcome', '💬 **SOHBET ARAÇLARI**\n\nBir araç seç:'), context, user_id),
            reply_markup=sa_klavye, parse_mode='Markdown'
        )
    elif query.data == 'sa_qr':
        context.user_data['durum'] = 'sa_qr_bekliyor'
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        await query.edit_message_text(
            ft(strings.get('sa_qr_ask', '📱 QR kod için metin girin:'), context, user_id),
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'sa_url':
        context.user_data['durum'] = 'sa_url_bekliyor'
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        await query.edit_message_text(
            ft(strings.get('sa_url_ask', '🌐 URL girin:'), context, user_id),
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'sa_kimlik':
        kimlik = sahte_kimlik_uret(lang)
        yeni_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton('🔄 Yeni Kimlik', callback_data='sa_kimlik')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')],
        ])
        await query.edit_message_text(kimlik, reply_markup=yeni_klavye, parse_mode='HTML')
    elif query.data == 'sa_tarih':
        context.user_data['durum'] = 'sa_tarih_bekliyor'
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]])
        await query.edit_message_text(
            ft(strings.get('sa_tarih_ask', '📅 Doğum tarihinizi girin (GG.AA.YYYY):'), context, user_id),
            reply_markup=geri, parse_mode='Markdown'
        )
    elif query.data == 'menu_araba':
        context.user_data['mevcut_kategori'] = '🚗 Araba Menüsü'
        araba_klavye = [
            [InlineKeyboardButton('🔍 Şasi No (VIN) Sorgula', callback_data='menu_araba_sasi')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='go_home')]
        ]
        await query.edit_message_text(
            "🚗 *ARABA MENÜSÜ*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 *Şasi No (VIN)* — 17 haneli VIN gir, detaylı araç raporu al",
            reply_markup=InlineKeyboardMarkup(araba_klavye),
            parse_mode='Markdown'
        )
    elif query.data == 'menu_araba_sasi':
        context.user_data['mevcut_kategori'] = '🚗 Araba Menüsü'
        context.user_data['durum'] = 'sasi_bekliyor'
        await log_kanali_gonder(context.bot, update, kategori='🚗 Araba Menüsü', komut='🔍 Şasi No Sorgula')
        geri = InlineKeyboardMarkup([[InlineKeyboardButton(strings['btn_back'], callback_data='menu_araba')]])
        await query.edit_message_text(
            "🔍 **ŞASİ NO (VIN) SORGULAMA**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Araç şasi numarasını (17 karakter) girin:\n\n"
            "📌 _Örnek: `WBA5A5C54FD520774`_",
            reply_markup=geri,
            parse_mode='Markdown'
        )
    elif query.data == 'go_home':
        context.user_data['durum'] = None
        context.user_data['mevcut_kategori'] = None
        fid = get_font(context, user_id)
        metin = ft(LANG_DATA[lang]['welcome'], context, user_id)
        klavye = ana_menu_klavye(lang, fid)
        try:
            await query.edit_message_text(metin, reply_markup=klavye, parse_mode='Markdown')
        except Exception:
            await query.message.reply_text(metin, reply_markup=klavye, parse_mode='Markdown')
            try:
                await query.message.delete()
            except Exception:
                pass

# ══════════════════════════════════════════════════════════════
# 🚗 ARABA MENÜSÜ — VIN / ŞASİ NO SORGULAMA
# ══════════════════════════════════════════════════════════════

async def vin_bilgi_al(sasi_no: str) -> dict:
    sasi_no = sasi_no.strip().upper()
    GECERSIZ = {"gecerli": False, "marka": "", "model": "", "yil": "",
                "rapor": "❌ **Geçersiz Şasi Numarası!**\n\nReis, şasi numarasını eksik veya yanlış girdin, kontrol et!\n\n📌 Şasi no tam 17 karakter olmalı ve I, O, Q harfleri içermemeli."}
    if len(sasi_no) != 17 or not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', sasi_no):
        return GECERSIZ
    try:
        loop = asyncio.get_event_loop()
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{sasi_no}?format=json"
        response = await loop.run_in_executor(None, lambda: http_requests.get(url, timeout=10))
        data = response.json()

        def g(key, default='—'):
            for item in data.get('Results', []):
                if item.get('Variable') == key:
                    v = (item.get('Value') or '').strip()
                    if v and v not in ('Not Applicable', '0', 'null', 'None', ''):
                        for ch in ('_', '*', '`', '[', ']', '\\'):
                            v = v.replace(ch, ' ')
                        return v.strip() or default
            return default

        marka   = g('Make');  model = g('Model');  yil = g('Model Year')

        def temiz(val, maks=80):
            for ch in ('_', '*', '`', '[', ']', '\\'):
                val = val.replace(ch, ' ')
            return val.strip()[:maks]

        def yildiz(val):
            try:
                n = int(val)
                return '⭐' * n + '☆' * (5 - n)
            except Exception:
                return '—'

        # --- Güvenlik Puanları ---
        safety = {}
        try:
            if marka != '—' and model != '—' and yil != '—':
                sr_list_url = (f"https://api.nhtsa.gov/SafetyRatings/modelyear/{yil}"
                               f"/make/{urllib.parse.quote(marka)}/model/{urllib.parse.quote(model)}")
                sr_list = await loop.run_in_executor(None, lambda: http_requests.get(sr_list_url, timeout=6).json())
                vehicles = sr_list.get('Results', [])
                if vehicles:
                    vid = vehicles[0].get('VehicleId')
                    sr_url = f"https://api.nhtsa.gov/SafetyRatings/VehicleId/{vid}"
                    sr_data = await loop.run_in_executor(None, lambda: http_requests.get(sr_url, timeout=6).json())
                    r = sr_data.get('Results', [{}])[0] if sr_data.get('Results') else {}
                    safety = {
                        'genel':    r.get('OverallRating', ''),
                        'on':       r.get('OverallFrontCrashRating', ''),
                        'yan':      r.get('OverallSideCrashRating', ''),
                        'devrilme': r.get('RolloverRating', ''),
                    }
        except Exception:
            pass

        # --- Geri çağırma (Recalls) ---
        recalls_sayi = 0
        recalls_satirlar = []
        try:
            if marka != '—' and model != '—' and yil != '—':
                rc_url = (f"https://api.nhtsa.gov/recalls/recallsByVehicle"
                          f"?make={urllib.parse.quote(marka)}&model={urllib.parse.quote(model)}&modelYear={yil}")
                rc = await loop.run_in_executor(None, lambda: http_requests.get(rc_url, timeout=8).json())
                recalls = rc.get('results', [])
                recalls_sayi = len(recalls)
                for rec in recalls[:5]:
                    comp        = temiz(rec.get('Component') or '', 60)
                    consequence = temiz(rec.get('Consequence') or '', 90)
                    if comp:
                        line = f"  🔸 {comp}"
                        if consequence:
                            line += f"\n     ↳ {consequence}"
                        recalls_satirlar.append(line)
        except Exception:
            pass

        # --- Şikayetler + Kategoriler ---
        sikayet_sayi = 0
        sikayet_kategoriler = {}
        CAT_TR = {
            'ENGINE': 'Motor', 'FUEL SYSTEM': 'Yakıt Sistemi', 'BRAKES': 'Fren',
            'STEERING': 'Direksiyon', 'ELECTRICAL SYSTEM': 'Elektrik',
            'TRANSMISSION': 'Şanzıman', 'SUSPENSION': 'Süspansiyon',
            'AIRBAG': 'Hava Yastığı', 'POWER TRAIN': 'Güç Aktarımı',
            'STRUCTURE': 'Kasa', 'TIRES': 'Lastik', 'VISIBILITY': 'Görüş',
            'VEHICLE SPEED CONTROL': 'Hız Kontrolü', 'SEAT BELTS': 'Emniyet Kemeri',
            'EXTERIOR LIGHTING': 'Dış Aydınlatma', 'SERVICE BRAKES': 'Servis Freni',
            'PARKING BRAKE': 'El Freni',
        }
        try:
            if marka != '—' and model != '—' and yil != '—':
                cmp_url = (f"https://api.nhtsa.gov/complaints/complaintsByVehicle"
                           f"?make={urllib.parse.quote(marka)}&model={urllib.parse.quote(model)}&modelYear={yil}")
                cmp = await loop.run_in_executor(None, lambda: http_requests.get(cmp_url, timeout=8).json())
                complaints_list = cmp.get('results', [])
                sikayet_sayi = cmp.get('count', 0) or len(complaints_list)
                for c in complaints_list:
                    raw_comp = (c.get('components') or c.get('component') or '').upper()
                    cat_raw = raw_comp.split(':')[0].split(',')[0].strip()
                    cat_tr = cat_raw
                    for k, v in CAT_TR.items():
                        if k in cat_raw:
                            cat_tr = v
                            break
                    if cat_tr:
                        sikayet_kategoriler[cat_tr] = sikayet_kategoriler.get(cat_tr, 0) + 1
        except Exception:
            pass

        YAKIT_TR = {
            'gasoline': 'Benzin', 'petrol': 'Benzin', 'diesel': 'Dizel',
            'electric': 'Elektrik', 'flex': 'Flex Yakıt',
            'natural gas': 'Doğal Gaz', 'hydrogen': 'Hidrojen',
            'plug-in hybrid': 'Plug-in Hibrit', 'hybrid': 'Hibrit',
        }
        CEKIS_TR = {
            'front-wheel drive': 'Önden Çekiş (FWD)',
            'rear-wheel drive': 'Arkadan İtiş (RWD)',
            'all-wheel drive': 'Dört Çeker (AWD)',
            '4wd': '4x4', '4-wheel drive': '4x4',
            'awd': 'Dört Çeker (AWD)', 'fwd': 'Önden Çekiş (FWD)',
            'rwd': 'Arkadan İtiş (RWD)',
        }
        VITES_TR = {
            'automatic': 'Otomatik', 'manual': 'Manuel', 'cvt': 'CVT',
            'semi-automatic': 'Yarı Otomatik', 'dual-clutch': 'Çift Kavramalı (DCT)',
        }
        KASA_TR = {
            'sedan': 'Sedan', 'saloon': 'Sedan', 'hatchback': 'Hatchback',
            'sport utility vehicle': 'SUV', 'suv': 'SUV',
            'pickup': 'Pikap', 'convertible': 'Cabrio', 'cabriolet': 'Cabrio',
            'coupe': 'Coupe', 'van': 'Van', 'minivan': 'Minivan',
            'wagon': 'Station Wagon', 'truck': 'Kamyonet',
            'crossover': 'Crossover',
        }

        def tr(val, sozluk):
            if val == '—':
                return val
            key = val.lower().strip()
            for k, v in sozluk.items():
                if k in key:
                    return v
            return val

        uretici  = g('Manufacturer Name')
        mensei   = g('Country of Origin')
        fabrika_ulke = g('Plant Country')
        mensei_goster = mensei if mensei != '—' else fabrika_ulke

        motor_l  = g('Displacement (L)')
        silindir = g('Engine Number of Cylinders')
        hp_min   = g('Engine Brake (hp) From'); hp_max = g('Engine Brake (hp) To')
        hp       = hp_min if hp_min != '—' else hp_max
        yakit    = tr(g('Fuel Type - Primary'), YAKIT_TR)
        cekis    = tr(g('Drive Type'), CEKIS_TR)
        vites    = tr(g('Transmission Style'), VITES_TR)
        govde    = tr(g('Body Class'), KASA_TR)
        kapi     = g('Doors')

        def s(label, val):
            return f"{label} {val}\n" if val and val != '—' else ''

        rapor  = f"🚗 *ŞASİ NO RAPORU*\n"
        rapor += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        rapor += f"🔑 Şasi: `{sasi_no}`\n\n"

        # Araç kimliği
        rapor += f"🚗 *{marka} {model}* ({yil})\n"
        rapor += s("🏭 Üretici:", uretici)
        rapor += s("🌍 Menşei:", mensei_goster)
        rapor += "\n"

        # Motor & teknik
        motor_str = f"{motor_l}L" if motor_l != '—' else ''
        if silindir != '—':
            motor_str += f" — {silindir} Silindir"
        if hp != '—':
            motor_str += f" — {hp} HP (At Gücü)"
        if motor_str:
            rapor += f"⚙️ Motor: {motor_str.strip(' —')}\n"
        rapor += s("⛽ Yakıt:", yakit)
        rapor += s("🔄 Çekiş:", cekis)
        rapor += s("⚙️ Vites:", vites)
        rapor += s("🚘 Kasa:", govde + (f" — {kapi} Kapı" if kapi != '—' else ''))
        rapor += "\n"

        # Güvenlik Puanları
        if any(v for v in safety.values()):
            rapor += f"🛡️ *NHTSA Güvenlik Puanları*\n"
            if safety.get('genel'):
                rapor += f"  Genel:       {yildiz(safety['genel'])}\n"
            if safety.get('on'):
                rapor += f"  Ön Çarpışma: {yildiz(safety['on'])}\n"
            if safety.get('yan'):
                rapor += f"  Yan Çarpışma:{yildiz(safety['yan'])}\n"
            if safety.get('devrilme'):
                rapor += f"  Devrilme:    {yildiz(safety['devrilme'])}\n"
            rapor += "\n"

        # Geri çağırmalar
        kaza_icon = "🚨" if recalls_sayi > 0 else "✅"
        rapor += f"{kaza_icon} *Geri Çağırma (Recall):* {recalls_sayi} kayıt\n"
        if recalls_satirlar:
            rapor += '\n'.join(recalls_satirlar) + '\n'
        rapor += "\n"

        # Şikayet kategorileri
        sikayet_icon = "⚠️" if sikayet_sayi > 10 else ("🔶" if sikayet_sayi > 0 else "✅")
        rapor += f"{sikayet_icon} *NHTSA Şikayetleri:* {sikayet_sayi} kayıt\n"
        if sikayet_kategoriler:
            top = sorted(sikayet_kategoriler.items(), key=lambda x: -x[1])[:5]
            for kat, say in top:
                rapor += f"  • {kat}: {say}\n"

        rapor += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📡 _NHTSA vPIC + Safety Ratings_"

        return {"gecerli": True, "marka": marka, "model": model, "yil": yil, "rapor": rapor}
    except Exception as e:
        logger.error(f"VIN bilgi alma hatası: {e}")
        return {"gecerli": False, "marka": "", "model": "", "yil": "",
                "rapor": "❌ Sorgulama sırasında bir hata oluştu. Lütfen tekrar dene."}


async def vin_sasi_sorgula(sasi_no: str) -> str:
    return (await vin_bilgi_al(sasi_no))["rapor"]


async def _vin_gonder(mesaj, sasi_no: str):
    geri = InlineKeyboardMarkup([
        [InlineKeyboardButton('🔍 Yeni VIN Sorgula', callback_data='menu_araba_sasi')],
        [InlineKeyboardButton('🚗 Araba Menüsü', callback_data='menu_araba')]
    ])
    sonuc = await vin_bilgi_al(sasi_no)
    await mesaj.reply_text(sonuc["rapor"], parse_mode='Markdown', reply_markup=geri)


async def sasi_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        sasi_no = args[0].strip()
        bekle = await update.message.reply_text("🔍 _Sorgulanıyor..._", parse_mode='Markdown')
        await bekle.delete()
        await _vin_gonder(update.message, sasi_no)
    else:
        context.user_data['durum'] = 'sasi_bekliyor'
        geri = InlineKeyboardMarkup([[InlineKeyboardButton('🚗 Araba Menüsü', callback_data='menu_araba')]])
        await update.message.reply_text(
            "🔍 **ŞASİ NO (VIN) SORGULAMA**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Araç şasi numarasını (17 karakter) girin:\n\n"
            "📌 _Örnek: `WBA5A5C54FD520774`_",
            reply_markup=geri,
            parse_mode='Markdown'
        )



# ══════════════════════════════════════════════════════════════
# 📧 EMAIL SIZINTI / 🔍 ŞİFRE SIZINTI / 📱 OPERATÖR / 📸 SCREENSHOT / 👥 GRUP STAT
# ══════════════════════════════════════════════════════════════

import hashlib as _hashlib

# Gürcistan operatör prefix tablosu (+995)
_OPERATOR_TABLO = {
    # Geocell / Silknet
    '511': 'Geocell / Silknet', '514': 'Geocell / Silknet', '515': 'Geocell / Silknet',
    '551': 'Geocell / Silknet', '555': 'Geocell / Silknet', '557': 'Geocell / Silknet', '558': 'Geocell / Silknet',
    '571': 'Geocell / Silknet', '574': 'Geocell / Silknet', '577': 'Geocell / Silknet',
    '591': 'Geocell / Silknet', '592': 'Geocell / Silknet', '593': 'Geocell / Silknet', '596': 'Geocell / Silknet',
    # Magti
    '568': 'Magti', '569': 'Magti', '598': 'Magti',
    '790': 'Magti', '791': 'Magti', '793': 'Magti', '774': 'Magti',
    # Beeline Georgia
    '595': 'Beeline Georgia', '597': 'Beeline Georgia', '599': 'Beeline Georgia',
    # MagtiCom / Veon
    '561': 'MagtiCom', '562': 'MagtiCom', '563': 'MagtiCom', '564': 'MagtiCom',
}

_OPERATOR_EMOJI = {
    'Geocell / Silknet': '🟠', 'Magti': '🔵',
    'Beeline Georgia': '🟡', 'MagtiCom': '🟣',
}


def operator_sorgula_func(numara_ham: str) -> str:
    numara = re.sub(r'\D', '', numara_ham).lstrip('0')
    if numara.startswith('995'):
        numara = numara[3:]
    if len(numara) != 9 or numara[0] not in ('5', '7'):
        return (
            "❌ **Geçersiz Numara**\n\n"
            "Gürcistan formatında gir:\n"
            "`0591234567` veya `+995591234567`"
        )
    prefix = numara[:3]
    operator = _OPERATOR_TABLO.get(prefix, 'Bilinmiyor')
    emoji = _OPERATOR_EMOJI.get(operator, '📱')
    return (
        f"📱 **OPERATÖR SORGULAMA**\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📞 **Numara:** `+995 {numara[:3]} {numara[3:6]} {numara[6:]}`\n"
        f"{emoji} **Operatör:** {operator}\n"
        f"🇬🇪 **Ülke:** Gürcistan\n\n"
        f"_Sonuç prefix tablosuna göredir._"
    )


async def sifre_pwned_kontrol(sifre: str) -> tuple:
    sha1 = _hashlib.sha1(sifre.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        loop = asyncio.get_event_loop()
        r = await loop.run_in_executor(
            None,
            lambda: http_requests.get(
                f'https://api.pwnedpasswords.com/range/{prefix}',
                headers={'Add-Padding': 'true'},
                timeout=8
            )
        )
        for line in r.text.splitlines():
            parts = line.split(':')
            if len(parts) == 2 and parts[0] == suffix:
                return True, int(parts[1])
        return False, 0
    except Exception as e:
        logger.debug(f"HIBP şifre: {e}")
        return None, 0


async def email_sizinti_kontrol(email: str) -> str:
    return "⚠️ Bu özellik kaldırıldı."


async def istatistik_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import tracking_store as _ts
    chat = update.effective_chat
    if chat.type not in ('group', 'supergroup'):
        await update.message.reply_text("❌ Bu komut yalnızca gruplarda çalışır.")
        return
    satirlar = _ts.stats_getir(chat.id, limit=10)
    toplam = _ts.stats_toplam(chat.id)
    if not satirlar:
        await update.message.reply_text("📊 Henüz mesaj istatistiği yok.")
        return
    liste = ""
    madalyalar = ['🥇', '🥈', '🥉']
    for i, (uid, username, full_name, count) in enumerate(satirlar):
        rozet = madalyalar[i] if i < 3 else f"{i+1}."
        isim = f"@{username}" if username else (full_name or str(uid))
        liste += f"{rozet} {isim} — **{count:,}** mesaj\n"
    await update.message.reply_text(
        f"📊 **GRUP MESAJ SIRALAMAСИ**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 {chat.title or 'Grup'}\n\n"
        f"{liste}\n"
        f"📨 Toplam: **{toplam:,}** mesaj",
        parse_mode='Markdown'
    )


async def gunluk_istatistik_job(context: ContextTypes.DEFAULT_TYPE):
    """Her gün 00:00'da (Gürcistan saati UTC+4) tüm gruplara şık günlük skor tablosu gönderir."""
    import tracking_store as _ts
    import datetime as _dt

    dun_dt = _dt.date.today() - _dt.timedelta(days=1)
    dun = dun_dt.isoformat()
    aylar = {
        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
        5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
        9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
    }
    gunler = {
        0: 'Pazartesi', 1: 'Salı', 2: 'Çarşamba', 3: 'Perşembe',
        4: 'Cuma', 5: 'Cumartesi', 6: 'Pazar'
    }
    gun_adi = gunler[dun_dt.weekday()]
    ay_adi = aylar[dun_dt.month]
    dun_goster = f"{dun_dt.day} {ay_adi} {dun_dt.year}"

    gruplar = _ts.stats_tum_gruplar()
    for group_id in gruplar:
        try:
            gunluk = _ts.daily_stats_getir(group_id, tarih=dun, limit=10)
            if not gunluk:
                continue

            toplam_mesaj = sum(row[3] for row in gunluk)
            rozet_listesi = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

            liste = ""
            for i, (uid, username, full_name, count) in enumerate(gunluk):
                rozet = rozet_listesi[i] if i < len(rozet_listesi) else f"#{i+1}"
                isim = f"@{username}" if username else (full_name or str(uid))
                yuzde = (count / toplam_mesaj * 100) if toplam_mesaj else 0
                dolu = int(yuzde / 10)
                bar = '█' * dolu + '░' * (10 - dolu)
                liste += f"{rozet} **{isim}**\n    `{bar}` **{count:,}** _{yuzde:.0f}%_\n"

            kazanan = gunluk[0]
            kazanan_isim = f"@{kazanan[1]}" if kazanan[1] else (kazanan[2] or str(kazanan[0]))

            mesaj = (
                f"╔════════════════════════╗\n"
                f"║  🏆  GÜNLÜK SKOR TABLOSU  🏆  ║\n"
                f"╚════════════════════════╝\n\n"
                f"📅 **{gun_adi}, {dun_goster}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👑 **Günün Şampiyonu:**\n"
                f"🌟 {kazanan_isim} — **{kazanan[3]:,}** mesaj ile zirvede!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 **TAM SIRALAMA**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{liste}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📨 Toplam: **{toplam_mesaj:,}** mesaj\n"
                f"👥 Aktif üye: **{len(gunluk)}** kişi\n\n"
                f"⚡ _AZRxGUARD · Her gün 00:00 · 🇬🇪 Gürcistan Saati_"
            )

            await context.bot.send_message(
                chat_id=group_id,
                text=mesaj,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.debug(f"Günlük skor tablosu gönderme hatası (grup {group_id}): {e}")


# ══════════════════════════════════════════════════════════════
# 🤖 AI ASİSTAN — GEMINI 2.0 FLASH
# ══════════════════════════════════════════════════════════════

_tg_ai_gecmis: dict = {}

async def gemini_yanit_tg(user_id: int, soru: str) -> str:
    try:
        from google import genai
        from google.genai import types
        gecmis = _tg_ai_gecmis.get(user_id, [])
        gecmis.append({"role": "user", "parts": [{"text": soru}]})
        if len(gecmis) > 20:
            gecmis = gecmis[-20:]
        def call_api():
            client = genai.Client()
            system_prompt = (
                "Sen AZRxGUARD botunun yapay zeka asistanısın. "
                "Gürcüce, Türkçe, Rusça, Azerbaycan Türkçesi ve diğer dillerde yardımcı olabilirsin. "
                "Gürcistan odaklı sorularda öncelikle Gürcüce veya Türkçe yanıt veriyorsun. "
                "Samimi, yardımsever ve kısa cevaplar veriyorsun. "
                "Markdown kullanabilirsin."
            )
            contents = []
            for m in gecmis:
                contents.append(types.Content(
                    role=m["role"],
                    parts=[types.Part.from_text(text=m["parts"][0]["text"])]
                ))
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
            _tg_ai_gecmis[user_id] = gecmis[-20:]
        return yanit or "❌ AI yanıt üretemedi."
    except Exception as e:
        logger.error(f"Gemini TG hatası: {e}")
        return f"❌ AI servisi şu an erişilemiyor.\n`{str(e)[:100]}`"


# ══════════════════════════════════════════════════════════════
# 📥 VİDEO İNDİRİCİ — YT-DLP (İZOLE SİSTEM)
# ══════════════════════════════════════════════════════════════

async def _vid_indir_ve_gonder(update: Update, context, url: str, mod: str, bekle_msg=None):
    tmp_dir = None
    try:
        import yt_dlp
        import os as _os
        tmp_dir = tempfile.mkdtemp(prefix='azr_vid_')
        cikis_path = _os.path.join(tmp_dir, '%(title)s.%(ext)s')

        if mod == 'ses':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': cikis_path,
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'socket_timeout': 30,
            }
        else:
            ydl_opts = {
                'format': 'best[filesize<50M]/best',
                'outtmpl': cikis_path,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
            }

        def indir():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info

        info = await asyncio.to_thread(indir)

        dosyalar = [_os.path.join(tmp_dir, f) for f in _os.listdir(tmp_dir)]
        if not dosyalar:
            raise Exception("Dosya indirilemedi")

        dosya_yolu = max(dosyalar, key=lambda f: _os.path.getsize(f))
        boyut_mb = _os.path.getsize(dosya_yolu) / 1024 / 1024
        baslik = (info.get('title', 'video') if info else 'video')[:50]
        platform = (info.get('extractor_key', '') if info else '').lower()

        if boyut_mb > 49:
            geri_kl = InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Ana Menü', callback_data='go_home')]])
            if bekle_msg:
                await bekle_msg.edit_text(
                    f"❌ **Dosya çok büyük!**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📦 Boyut: `{boyut_mb:.1f} MB` (Limit: 50 MB)\n\n"
                    f"Lütfen daha kısa bir video deneyin.",
                    reply_markup=geri_kl, parse_mode='Markdown'
                )
            return

        caption = (
            f"{'🎵' if mod == 'ses' else '🎬'} **{baslik}**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 Boyut: `{boyut_mb:.1f} MB`\n"
            f"_İndirildi: AZRxGUARD 📥_"
        )
        geri_kl = InlineKeyboardMarkup([
            [InlineKeyboardButton('📥 Yeni İndir', callback_data='menu_video_indir'),
             InlineKeyboardButton('🏠 Ana Menü', callback_data='go_home')]
        ])

        with open(dosya_yolu, 'rb') as f:
            if mod == 'ses':
                await update.effective_chat.send_audio(
                    audio=f, caption=caption, parse_mode='Markdown', reply_markup=geri_kl
                )
            else:
                await update.effective_chat.send_video(
                    video=f, caption=caption, parse_mode='Markdown', reply_markup=geri_kl,
                    supports_streaming=True
                )

        if bekle_msg:
            try:
                await bekle_msg.delete()
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Video indirici hatası: {e}")
        hata_mesaji = str(e)
        if 'Unsupported URL' in hata_mesaji or 'No video formats' in hata_mesaji:
            mesaj = "❌ Bu URL desteklenmiyor.\nYouTube, TikTok, Instagram linki gönder."
        elif 'Private' in hata_mesaji or 'login' in hata_mesaji.lower():
            mesaj = "❌ Bu video gizli/şifre korumalı, indirilemiyor."
        elif 'Too large' in hata_mesaji or '50M' in hata_mesaji:
            mesaj = "❌ Video çok büyük (50 MB üstü)."
        else:
            mesaj = f"❌ İndirme başarısız.\n`{hata_mesaji[:120]}`"
        geri_kl = InlineKeyboardMarkup([[InlineKeyboardButton('🔄 Tekrar Dene', callback_data='menu_video_indir')]])
        if bekle_msg:
            await bekle_msg.edit_text(mesaj, reply_markup=geri_kl, parse_mode='Markdown')
        else:
            await update.effective_chat.send_message(mesaj, reply_markup=geri_kl, parse_mode='Markdown')
    finally:
        if tmp_dir:
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass


async def gelen_mesajlari_yonet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(context, user_id)
    strings = fs(context, user_id, lang)
    if not await kanal_takip_kontrol(update, context, user_id, lang):
        return

    try:
        await log_kanali_gonder(context.bot, update)
    except Exception:
        pass

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
            fid = get_font(context, user_id)
            await update.message.reply_text(strings['msg_sent'], parse_mode='Markdown')
            await update.message.reply_text(
                ft(LANG_DATA[lang]['welcome'], context, user_id),
                reply_markup=ana_menu_klavye(lang, fid),
                parse_mode='Markdown'
            )
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
            rapor = await ip_tam_analiz_yap(ip_adresi, lang)
            await bekle.edit_text(rapor, parse_mode='Markdown', disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"IP analiz menü hatası: {e}")
            await bekle.edit_text("❌ Analiz sırasında bir hata oluştu.")
        return

    if context.user_data.get('durum') == 'iplogger_bekliyor':
        context.user_data['durum'] = None
        raw = update.message.text.strip()
        if not raw.startswith('http'):
            await update.message.reply_text(
                "❌ Geçersiz link. `https://` ile başlayan bir link gönder.",
                parse_mode='Markdown'
            )
            return
        import secrets as _sec
        import tracking_store as _ts
        token = _sec.token_urlsafe(10)
        chat_id = update.effective_chat.id
        _ts.save(token, raw, chat_id)
        domain = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
        izleme_linki = f"https://{domain}/track/{token}"
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton('📡 Yeni Link Oluştur', callback_data='menu_iplogger')],
            [InlineKeyboardButton('🔙 IP Sorgu', callback_data='menu_ip_sorgu')]
        ])
        await update.message.reply_text(
            f"✅ *İzleme linki oluşturuldu\\!*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📎 Aşağıdaki linki paylaş:\n\n"
            f"`{izleme_linki}`\n\n"
            f"👆 Bu linke tıklayan kişi orijinal içeriğe ulaşır\\.\n"
            f"IP bilgileri anında bu sohbete gelir\\.\n\n"
            f"🔗 _Hedef:_ `{raw[:60]}{'...' if len(raw)>60 else ''}`",
            reply_markup=geri,
            parse_mode='MarkdownV2'
        )
        return

    if context.user_data.get('durum') == 'sifre_pwned_bekliyor':
        context.user_data['durum'] = None
        sifre = update.message.text.strip()
        bekle = await update.message.reply_text("🔍 _Kontrol ediliyor..._", parse_mode='Markdown')
        try:
            sonuc = await sifre_pwned_kontrol(sifre)
        except Exception as e:
            sonuc = f"❌ Hata: {e}"
        await bekle.edit_text(sonuc, parse_mode='Markdown')
        return

    if context.user_data.get('durum') == 'operator_bekliyor':
        context.user_data['durum'] = None
        numara = update.message.text.strip()
        bekle = await update.message.reply_text("🔍 _Sorgulanıyor..._", parse_mode='Markdown')
        try:
            sonuc = operator_sorgula_func(numara)
        except Exception as e:
            sonuc = f"❌ Hata: {e}"
        await bekle.edit_text(sonuc, parse_mode='Markdown')
        return

    if context.user_data.get('durum') == 'sasi_bekliyor':
        context.user_data['durum'] = None
        sasi_no = update.message.text.strip()
        bekle = await update.message.reply_text("🔍 _Sorgulanıyor..._", parse_mode='Markdown')
        await bekle.delete()
        await _vin_gonder(update.message, sasi_no)
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
        sonuc = guvenli_hesapla(ifade, lang)
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yeni Hesap", callback_data='pro_hesap')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_pro_araclar')]
        ])
        await update.message.reply_text(sonuc, parse_mode='Markdown', reply_markup=geri)
        return

    if context.user_data.get('durum') == 'hash_bekliyor':
        context.user_data['durum'] = None
        metin = update.message.text.strip()
        sonuc = hash_uret(metin, lang)
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
        sonuc = await hava_durumu_getir(sehir, lang)
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
        sonuc = await doviz_cevir(f"{miktar_str} {from_kur} {to_kur}", lang)
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
        sonuc = await hava_durumu_getir(lokasyon, lang)
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
        sonuc = base64_islem(metin, lang)
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

    if context.user_data.get('durum') == 'sifre_guc_bekliyor':
        context.user_data['durum'] = None
        sifre = update.message.text.strip()
        puan = 0
        notlar = []
        if len(sifre) >= 8: puan += 1
        else: notlar.append("❌ En az 8 karakter olmalı")
        if len(sifre) >= 12: puan += 1
        if any(c.islower() for c in sifre): puan += 1
        else: notlar.append("❌ Küçük harf ekle")
        if any(c.isupper() for c in sifre): puan += 1
        else: notlar.append("❌ Büyük harf ekle")
        if any(c.isdigit() for c in sifre): puan += 1
        else: notlar.append("❌ Rakam ekle")
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in sifre): puan += 1
        else: notlar.append("❌ Özel karakter ekle (!@#$...)")
        if len(sifre) >= 16: puan += 1
        seviye = ['💀 Çok Zayıf','🔴 Zayıf','🟠 Orta','🟡 İyi','🟢 Güçlü','💪 Çok Güçlü','🛡️ Mükemmel'][min(puan,6)]
        bar = '█' * puan + '░' * (7-puan)
        rapor = (f"🔐 **ŞİFRE GÜÇ ANALİZİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                 f"📊 Güç: **{seviye}**\n"
                 f"📈 Puan: `{bar}` {puan}/7\n"
                 f"📏 Uzunluk: {len(sifre)} karakter\n")
        if notlar:
            rapor += "\n**İyileştirmeler:**\n" + "\n".join(notlar)
        else:
            rapor += "\n✅ Harika şifre!"
        klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Tekrar Test", callback_data='siber_sifre_guc')],
            [InlineKeyboardButton(strings['btn_back'], callback_data='menu_siber_guvenlik')]
        ])
        await update.message.reply_text(rapor, parse_mode='Markdown', reply_markup=klavye)
        return

    if context.user_data.get('durum') == 'sayi_tahmin_bekliyor':
        oyun = context.user_data.get('sayi_oyun', {})
        gizli = oyun.get('gizli', 50)
        deneme = oyun.get('deneme', 0) + 1
        context.user_data['sayi_oyun']['deneme'] = deneme
        try:
            tahmin = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text("❌ Lütfen sadece bir sayı yaz (1-100)!")
            return
        if tahmin == gizli:
            context.user_data['durum'] = None
            klavye = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Tekrar Oyna", callback_data='oyun_sayi_baslat')],
                [InlineKeyboardButton(strings['btn_back'], callback_data='menu_fun')]
            ])
            await update.message.reply_text(
                f"🎉 **TEBRİKLER!** `{gizli}` sayısını {deneme} denemede buldun!",
                parse_mode='Markdown', reply_markup=klavye
            )
        elif deneme >= 10:
            context.user_data['durum'] = None
            klavye = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Tekrar Oyna", callback_data='oyun_sayi_baslat')],
                [InlineKeyboardButton(strings['btn_back'], callback_data='menu_fun')]
            ])
            await update.message.reply_text(
                f"😢 **Hakkın bitti!** Doğru sayı **{gizli}** idi.",
                parse_mode='Markdown', reply_markup=klavye
            )
        else:
            ipucu = "⬆️ Daha büyük!" if tahmin < gizli else "⬇️ Daha küçük!"
            kalan = 10 - deneme
            await update.message.reply_text(
                f"{ipucu}\n🎯 {deneme}. deneme · {kalan} hak kaldı"
            )
        return

    # ── 🆕 2.0 ARAÇLAR — GİRİŞ HANDLER'LARI ─────────────────
    if context.user_data.get('durum') == 'renk_bekliyor':
        context.user_data['durum'] = None
        girdi = update.message.text.strip()
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("🎨 Tekrar", callback_data='pro20_renk'),
                                       InlineKeyboardButton("⬅️ Geri", callback_data='menu_pro_araclar')]])
        r = g = b = None
        hex_str = None
        parcalar = girdi.split()
        if girdi.startswith('#') or (len(girdi.lstrip('#')) in (3, 6) and all(c in '0123456789abcdefABCDEF' for c in girdi.lstrip('#'))):
            res = _hex_to_rgb(girdi)
            if res:
                r, g, b = res
                h_raw = girdi.lstrip('#').upper()
                hex_str = ''.join(c*2 for c in h_raw) if len(h_raw) == 3 else h_raw
        elif len(parcalar) == 3:
            try:
                r, g, b = int(parcalar[0]), int(parcalar[1]), int(parcalar[2])
                if not all(0 <= x <= 255 for x in (r, g, b)): raise ValueError
                hex_str = f"{r:02X}{g:02X}{b:02X}"
            except ValueError:
                await update.message.reply_text("❌ RGB değerleri 0-255 arasında olmalı!", reply_markup=geri, parse_mode='Markdown')
                return
        if r is None:
            await update.message.reply_text("❌ Geçersiz format!\nÖrnek: `#FF5733` veya `255 87 51`", reply_markup=geri, parse_mode='Markdown')
            return
        h, s, lv = _rgb_to_hsl(r, g, b)
        if   r > 180 and g < 100 and b < 100: ton = "🔴 Kırmızı tonu"
        elif r < 100 and g > 150 and b < 100: ton = "🟢 Yeşil tonu"
        elif r < 100 and g < 100 and b > 150: ton = "🔵 Mavi tonu"
        elif r > 200 and g > 200 and b < 80:  ton = "🟡 Sarı tonu"
        elif r > 200 and g > 100 and b < 80:  ton = "🟠 Turuncu tonu"
        elif r > 100 and g < 80  and b > 150: ton = "🟣 Mor tonu"
        elif r > 200 and g > 200 and b > 200: ton = "⬜ Beyaz / Açık"
        elif r < 60  and g < 60  and b < 60:  ton = "⬛ Siyah / Koyu"
        else: ton = "🎨 Karma renk"
        await update.message.reply_text(
            f"🎨 **RENK ANALİZİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔷 **HEX:** `#{hex_str}`\n"
            f"🔴🟢🔵 **RGB:** `rgb({r}, {g}, {b})`\n"
            f"🌈 **HSL:** `hsl({h}°, {s}%, {lv}%)`\n\n"
            f"🎯 **Renk Tonu:** {ton}",
            reply_markup=geri, parse_mode='Markdown'
        )
        return

    if context.user_data.get('durum') == 'metin_analiz_bekliyor':
        context.user_data['durum'] = None
        metin = update.message.text.strip()
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("📊 Tekrar", callback_data='pro20_metin'),
                                       InlineKeyboardButton("⬅️ Geri", callback_data='menu_pro_araclar')]])
        kelimeler   = metin.split()
        satir_sayi  = len(metin.splitlines())
        karakter    = len(metin)
        bosluksuz   = len(metin.replace(' ', '').replace('\n', ''))
        kelime_sayi = len(kelimeler)
        freq = {}
        for k in kelimeler:
            k2 = k.lower().strip('.,!?;:()[]{}"\'-')
            if len(k2) > 2: freq[k2] = freq.get(k2, 0) + 1
        en_sik = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
        en_sik_str = '\n'.join(f"  `{k}` → {v}x" for k, v in en_sik) if en_sik else "  —"
        ort_uzunluk = sum(len(k) for k in kelimeler) / max(kelime_sayi, 1)
        okuma_sn = (kelime_sayi / 200) * 60
        okuma_str = f"{int(okuma_sn)} saniye" if okuma_sn < 60 else f"{okuma_sn/60:.1f} dakika"
        await update.message.reply_text(
            f"📊 **METİN ANALİZİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔤 **Karakter:** `{karakter}` (boşluksuz: `{bosluksuz}`)\n"
            f"📝 **Kelime:** `{kelime_sayi}`\n"
            f"📄 **Satır:** `{satir_sayi}`\n"
            f"📏 **Ort. Kelime Uzunluğu:** `{ort_uzunluk:.1f}`\n"
            f"⏱️ **Tahmini Okuma:** `{okuma_str}`\n\n"
            f"🔝 **En Sık Kelimeler:**\n{en_sik_str}",
            reply_markup=geri, parse_mode='Markdown'
        )
        return

    if context.user_data.get('durum') == 'sifrele_bekliyor':
        context.user_data['durum'] = None
        girdi = update.message.text.strip()
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("🔠 Tekrar", callback_data='pro20_sifrele'),
                                       InlineKeyboardButton("⬅️ Geri", callback_data='menu_pro_araclar')]])
        parcalar = girdi.split(None, 2)
        mod = parcalar[0].lower() if parcalar else ''
        if mod == 'rot13':
            metin = ' '.join(parcalar[1:]) if len(parcalar) > 1 else ''
            if not metin:
                await update.message.reply_text("❌ Metin eksik! Örnek: `rot13 Merhaba`", reply_markup=geri, parse_mode='Markdown')
                return
            await update.message.reply_text(
                f"🔄 **ROT-13**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📥 **Giriş:** `{html.escape(metin)}`\n"
                f"📤 **ROT-13:** `{html.escape(_caesar(metin, 13))}`",
                reply_markup=geri, parse_mode='Markdown'
            )
        elif mod == 'ters':
            metin = ' '.join(parcalar[1:]) if len(parcalar) > 1 else ''
            if not metin:
                await update.message.reply_text("❌ Metin eksik! Örnek: `ters Merhaba`", reply_markup=geri, parse_mode='Markdown')
                return
            await update.message.reply_text(
                f"🔃 **METİN TERSİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📥 **Giriş:** `{html.escape(metin)}`\n"
                f"📤 **Ters:** `{html.escape(metin[::-1])}`",
                reply_markup=geri, parse_mode='Markdown'
            )
        elif mod == 'morse':
            metin = ' '.join(parcalar[1:]).upper() if len(parcalar) > 1 else ''
            if not metin:
                await update.message.reply_text("❌ Metin eksik! Örnek: `morse SOS`", reply_markup=geri, parse_mode='Markdown')
                return
            morse = ' '.join(_MORSE.get(c, '?') for c in metin)
            await update.message.reply_text(
                f"📡 **MORSE KODU**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📥 **Giriş:** `{html.escape(metin)}`\n"
                f"📤 **Morse:**\n`{morse}`",
                reply_markup=geri, parse_mode='Markdown'
            )
        elif mod == 'caesar':
            try:
                n = int(parcalar[1])
                metin = parcalar[2] if len(parcalar) > 2 else ''
                if not metin: raise ValueError
                await update.message.reply_text(
                    f"🔠 **CAESAR ŞİFRE**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📥 **Giriş:** `{html.escape(metin)}`\n"
                    f"🔢 **Kaydırma:** `{n}`\n\n"
                    f"🔒 **Şifreli:** `{html.escape(_caesar(metin, n))}`\n"
                    f"🔓 **Çözülmüş:** `{html.escape(_caesar(metin, -n))}`",
                    reply_markup=geri, parse_mode='Markdown'
                )
            except Exception:
                await update.message.reply_text("❌ Format: `caesar 3 Merhaba`", reply_markup=geri, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "❌ Tanınmayan mod!\n`rot13` · `ters` · `morse` · `caesar`",
                reply_markup=geri, parse_mode='Markdown'
            )
        return

    if context.user_data.get('durum') == 'bmi_bekliyor':
        context.user_data['durum'] = None
        girdi = update.message.text.strip().split()
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("💪 Tekrar", callback_data='pro20_bmi'),
                                       InlineKeyboardButton("⬅️ Geri", callback_data='menu_pro_araclar')]])
        try:
            boy, kilo = float(girdi[0]), float(girdi[1])
            if not (50 <= boy <= 300 and 10 <= kilo <= 500): raise ValueError
            boy_m = boy / 100
            bmi = kilo / (boy_m ** 2)
            if   bmi < 18.5: durum_bmi = "🔵 Zayıf";       tavsiye = "Daha fazla kalori ve güç antrenmanı önerilir."
            elif bmi < 25:   durum_bmi = "🟢 Normal";       tavsiye = "Harika! Mevcut yaşam tarzını sürdür."
            elif bmi < 30:   durum_bmi = "🟡 Fazla Kilolu"; tavsiye = "Hafif egzersiz ve dengeli beslenme önerilir."
            elif bmi < 35:   durum_bmi = "🟠 Obez I";       tavsiye = "Düzenli egzersiz ve diyet programı önerilir."
            else:             durum_bmi = "🔴 Obez II+";     tavsiye = "Bir sağlık uzmanıyla görüşmeniz önerilir."
            ideal_alt = 18.5 * (boy_m ** 2)
            ideal_ust = 24.9 * (boy_m ** 2)
            await update.message.reply_text(
                f"💪 **BMI ANALİZİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📏 **Boy:** `{boy} cm`  |  ⚖️ **Kilo:** `{kilo} kg`\n"
                f"📊 **BMI:** **`{bmi:.1f}`**\n\n"
                f"🏷️ **Durum:** {durum_bmi}\n"
                f"💡 **Tavsiye:** _{tavsiye}_\n\n"
                f"🎯 **İdeal Kilo:** `{ideal_alt:.1f} — {ideal_ust:.1f} kg`\n\n"
                f"⚠️ _Yalnızca bilgilendirme amaçlıdır._",
                reply_markup=geri, parse_mode='Markdown'
            )
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Format: `175 70` (boy cm · kilo kg)", reply_markup=geri, parse_mode='Markdown')
        return

    if context.user_data.get('durum') == 'yuzde_bekliyor':
        context.user_data['durum'] = None
        girdi = update.message.text.strip().split()
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("💯 Tekrar", callback_data='pro20_yuzde'),
                                       InlineKeyboardButton("⬅️ Geri", callback_data='menu_pro_araclar')]])
        try:
            mod = girdi[0].lower()
            if mod in ('artis', 'artış'):
                a, b = float(girdi[1]), float(girdi[2])
                oran = ((b - a) / a) * 100
                emoji = "📈" if oran >= 0 else "📉"
                await update.message.reply_text(
                    f"💯 **YÜZDE DEĞİŞİM**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🔢 `{a}` → `{b}`\n{emoji} **Değişim:** `{oran:+.2f}%`",
                    reply_markup=geri, parse_mode='Markdown'
                )
            elif mod in ('azalis', 'azalış'):
                a, b = float(girdi[1]), float(girdi[2])
                oran = ((a - b) / a) * 100
                await update.message.reply_text(
                    f"💯 **YÜZDE DEĞİŞİM**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🔢 `{a}` → `{b}`\n📉 **Azalış:** `{oran:.2f}%`",
                    reply_markup=geri, parse_mode='Markdown'
                )
            elif '%' in mod:
                yv = float(mod.replace('%', ''))
                sayi = float(girdi[1])
                sonuc = (yv / 100) * sayi
                await update.message.reply_text(
                    f"💯 **YÜZDE HESABI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📥 `{sayi}`'nin `%{yv}`'i = **`{sonuc:.4g}`**",
                    reply_markup=geri, parse_mode='Markdown'
                )
            else:
                parca, toplam = float(girdi[0]), float(girdi[1])
                oran = (parca / toplam) * 100
                await update.message.reply_text(
                    f"💯 **YÜZDE HESABI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📥 `{parca}`, `{toplam}`'nin → **`%{oran:.2f}`**",
                    reply_markup=geri, parse_mode='Markdown'
                )
        except (ValueError, IndexError, ZeroDivisionError):
            await update.message.reply_text(
                "❌ Geçersiz format!\nÖrnek: `%20 500` · `75 150` · `artis 200 250`",
                reply_markup=geri, parse_mode='Markdown'
            )
        return
    # ── END 2.0 ARAÇLAR GİRİŞ HANDLER'LARI ───────────────────

    # ── 🤖 AI ASİSTAN HANDLER ─────────────────────────────────
    if context.user_data.get('durum') == 'ai_sohbet_bekliyor':
        soru = (update.message.text or '').strip()
        if not soru:
            return
        bekleme = await update.message.reply_text("🤖 _Düşünüyor..._", parse_mode='Markdown')
        yanit = await gemini_yanit_tg(user_id, soru)
        ai_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton('🗑️ Geçmişi Temizle', callback_data='ai_gecmis_sil')],
            [InlineKeyboardButton('🏠 Ana Menü', callback_data='go_home')]
        ])
        try:
            await bekleme.edit_text(
                f"🤖 **AI ASİSTAN**\n━━━━━━━━━━━━━━━━━━━━━━\n\n{yanit}",
                reply_markup=ai_klavye,
                parse_mode='Markdown'
            )
        except Exception:
            await bekleme.edit_text(yanit, reply_markup=ai_klavye)
        return

    # ── 📥 VİDEO İNDİRİCİ HANDLER (İZOLE) ────────────────────
    if context.user_data.get('durum') == 'vid_indir_url_bekliyor':
        url = (update.message.text or '').strip()
        if not url:
            return
        if not (url.startswith('http://') or url.startswith('https://')):
            await update.message.reply_text(
                "❌ Geçersiz link! `http://` veya `https://` ile başlayan bir URL gönder.",
                parse_mode='Markdown'
            )
            return
        context.user_data['vid_indir_url'] = url
        context.user_data['durum'] = None
        format_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton('📹 Video İndir', callback_data='vid_dl_video'),
             InlineKeyboardButton('🎵 Sadece Ses (MP3)', callback_data='vid_dl_ses')],
            [InlineKeyboardButton('❌ İptal', callback_data='go_home')]
        ])
        await update.message.reply_text(
            f"🔗 **Link alındı!**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"`{url[:80]}{'...' if len(url) > 80 else ''}`\n\n"
            f"**Ne indirmek istersin?**",
            reply_markup=format_klavye,
            parse_mode='Markdown'
        )
        return

    # ── ✂️ VİDEO EDİTÖR — METİN GİRİŞ HANDLERS ──────────────
    if context.user_data.get('durum') == 'ved_kirp_sure_bekle':
        sure_gir = (update.message.text or '').strip()
        try:
            parcalar = sure_gir.replace(',', '.').split('-')
            if len(parcalar) != 2:
                raise ValueError("Format yanlış")
            basla = float(parcalar[0].strip())
            bitis_s = float(parcalar[1].strip())
            if bitis_s <= basla:
                raise ValueError("Bitiş başlangıçtan büyük olmalı")
        except Exception:
            await update.message.reply_text("❌ **Hatalı format!**\n\nÖrnek: `5-30` (5. saniyeden 30. saniyeye kırp)", parse_mode='Markdown')
            return
        video_path = context.user_data.get('ved', {}).get('video_path', '')
        if not video_path:
            await update.message.reply_text("❌ Video bulunamadı. Tekrar deneyin.", parse_mode='Markdown')
            return
        context.user_data['durum'] = None
        bekle = await update.message.reply_text(f"✂️ **Video {basla}s - {bitis_s}s arasında kırpılıyor...**", parse_mode='Markdown')
        try:
            import subprocess as _sp, os as _os
            sure = bitis_s - basla
            cikis = video_path.replace('.mp4', '_kirp.mp4')
            cmd = ['ffmpeg', '-i', video_path, '-ss', str(basla), '-t', str(sure), '-c', 'copy', cikis, '-y']
            result = await asyncio.to_thread(lambda: _sp.run(cmd, capture_output=True, timeout=120))
            if result.returncode != 0 or not _os.path.exists(cikis):
                raise Exception("FFmpeg başarısız")
            with open(cikis, 'rb') as vf:
                await update.effective_chat.send_video(
                    video=vf,
                    caption=f"✅ **Video kırpıldı!** ({basla}s → {bitis_s}s)\n_AZRxGUARD Video Editör_ ✂️",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Video Editör", callback_data='menu_video_olusturucu'), InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')]])
                )
            await bekle.delete()
            for f in [video_path, cikis]:
                try: _os.remove(f)
                except: pass
        except Exception as e:
            logger.error(f"Kırpma hatası: {e}")
            await bekle.edit_text("❌ Kırpma başarısız. Farklı bir video veya zaman aralığı deneyin.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Tekrar", callback_data='ved_kirp_baslat'), InlineKeyboardButton("🏠", callback_data='go_home')]]))
        return

    if context.user_data.get('durum') == 'ved_kare_sure_bekle':
        sure_gir = (update.message.text or '').strip()
        try:
            saniye = float(sure_gir.replace(',', '.'))
        except Exception:
            await update.message.reply_text("❌ Lütfen bir saniye değeri girin (Örnek: `5` veya `10.5`)", parse_mode='Markdown')
            return
        video_path = context.user_data.get('ved', {}).get('video_path', '')
        if not video_path:
            await update.message.reply_text("❌ Video bulunamadı.", parse_mode='Markdown')
            return
        context.user_data['durum'] = None
        bekle = await update.message.reply_text(f"📸 **{saniye}. saniyeden kare alınıyor...**", parse_mode='Markdown')
        try:
            import subprocess as _sp, os as _os
            cikis = video_path.replace('.mp4', '_kare.jpg')
            cmd = ['ffmpeg', '-i', video_path, '-ss', str(saniye), '-frames:v', '1', '-q:v', '2', cikis, '-y']
            result = await asyncio.to_thread(lambda: _sp.run(cmd, capture_output=True, timeout=60))
            if result.returncode != 0 or not _os.path.exists(cikis):
                raise Exception("FFmpeg başarısız")
            with open(cikis, 'rb') as pf:
                await update.effective_chat.send_photo(
                    photo=pf,
                    caption=f"✅ **Kare alındı!** ({saniye}. saniye)\n_AZRxGUARD Video Editör_ 📸",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Video Editör", callback_data='menu_video_olusturucu'), InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')]])
                )
            await bekle.delete()
            for f in [video_path, cikis]:
                try: _os.remove(f)
                except: pass
        except Exception as e:
            logger.error(f"Kare alma hatası: {e}")
            await bekle.edit_text("❌ Kare alma başarısız.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Tekrar", callback_data='ved_kare_baslat'), InlineKeyboardButton("🏠", callback_data='go_home')]]))
        return

    # ── 🎬 VİDEO YAZI EKLEME — YAZI GİRİŞ ────────────────────
    if context.user_data.get('durum') == 'vyo_yazi_bekle':
        yazi = (update.message.text or '').strip()
        if not yazi:
            await update.message.reply_text("❌ Lütfen geçerli bir yazı girin.")
            return
        context.user_data.setdefault('vyo', {})['yazi'] = yazi
        context.user_data['durum'] = None
        boyut_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔡 Küçük", callback_data='vyo_boyut_kucuk'),
             InlineKeyboardButton("🔤 Orta", callback_data='vyo_boyut_orta'),
             InlineKeyboardButton("🔠 Büyük", callback_data='vyo_boyut_buyuk'),
             InlineKeyboardButton("💬 Dev", callback_data='vyo_boyut_dev')],
            [InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]
        ])
        await update.message.reply_text(
            f"✅ **Yazı alındı:** `{html.escape(yazi)}`\n\n"
            "🔡 **Yazı boyutunu seçin:**",
            reply_markup=boyut_klavye,
            parse_mode='Markdown'
        )
        return

    # ─── 💬 SOHBET ARAÇLARI STATE'LERİ ───
    if context.user_data.get('durum') == 'sa_qr_bekliyor':
        context.user_data['durum'] = None
        metin = (update.message.text or '').strip()
        if not metin:
            await update.message.reply_text("❌ Boş metin gönderilemez.")
            return
        bekle = await update.message.reply_text("⏳ QR kod oluşturuluyor...")
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton('🔄 Yeni QR', callback_data='sa_qr')],
            [InlineKeyboardButton('⬅️ Geri', callback_data='menu_pro_araclar')],
        ])
        await bekle.delete()
        await qr_url_gonder(context.bot, update.effective_chat.id, metin, reply_markup=geri)
        return

    if context.user_data.get('durum') == 'sa_url_bekliyor':
        context.user_data['durum'] = None
        url_girdisi = (update.message.text or '').strip()
        if not url_girdisi.startswith('http'):
            url_girdisi = 'https://' + url_girdisi
        bekle = await update.message.reply_text("⏳ URL kısaltılıyor...")
        try:
            encoded = urllib.parse.quote(url_girdisi, safe='')
            r = await asyncio.to_thread(
                lambda: http_requests.get(
                    f"https://tinyurl.com/api-create.php?url={encoded}", timeout=8
                )
            )
            kisaltilmis = r.text.strip() if r.status_code == 200 and r.text.startswith('http') else url_girdisi
        except Exception:
            kisaltilmis = url_girdisi
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton('🔄 Başka URL Kısalt', callback_data='sa_url')],
            [InlineKeyboardButton('⬅️ Geri', callback_data='menu_pro_araclar')],
        ])
        await bekle.edit_text(
            f"🌐 <b>URL KISALTILDI!</b>\n\n"
            f"📎 Orijinal:\n<code>{html.escape(url_girdisi[:120])}</code>\n\n"
            f"✅ Kısa link:\n<b>{html.escape(kisaltilmis)}</b>",
            reply_markup=geri, parse_mode='HTML'
        )
        return

    if context.user_data.get('durum') == 'sa_tarih_bekliyor':
        context.user_data['durum'] = None
        tarih_str = (update.message.text or '').strip()
        geri = InlineKeyboardMarkup([
            [InlineKeyboardButton('🔄 Tekrar Hesapla', callback_data='sa_tarih')],
            [InlineKeyboardButton('⬅️ Geri', callback_data='menu_pro_araclar')],
        ])
        try:
            parca = tarih_str.replace('/', '.').replace('-', '.').split('.')
            gun, ay, yil = int(parca[0]), int(parca[1]), int(parca[2])
            dogum = datetime.date(yil, ay, gun)
            bugun = datetime.date.today()
            if dogum > bugun:
                raise ValueError("Gelecek tarih")
            delta = bugun - dogum
            yas = bugun.year - dogum.year - ((bugun.month, bugun.day) < (dogum.month, dogum.day))
            sonraki_dogum = dogum.replace(year=bugun.year)
            if sonraki_dogum < bugun:
                sonraki_dogum = dogum.replace(year=bugun.year + 1)
            kalan = (sonraki_dogum - bugun).days
            toplam_ay = yas * 12 + (bugun.month - dogum.month)
            await update.message.reply_text(
                f"📅 <b>YAŞ / TARİH HESAPLAYICI</b>\n\n"
                f"🎂 Doğum Tarihi: <b>{gun:02d}.{ay:02d}.{yil}</b>\n"
                f"📆 Bugün: <b>{bugun.strftime('%d.%m.%Y')}</b>\n\n"
                f"🎯 <b>Yaşın: {yas}</b>\n"
                f"📊 Toplam ay: <b>{toplam_ay}</b>\n"
                f"📊 Toplam gün: <b>{delta.days:,}</b>\n"
                f"🎊 Doğum gününe <b>{kalan}</b> gün kaldı!",
                reply_markup=geri, parse_mode='HTML'
            )
        except Exception:
            await update.message.reply_text(
                "❌ Geçersiz format! GG.AA.YYYY şeklinde girin.\nÖrnek: `15.03.1995`",
                reply_markup=geri, parse_mode='Markdown'
            )
        return

    if context.user_data.get('durum') == 'isim_fontu_bekliyor':
        context.user_data['durum'] = None
        girdi = (update.message.text or '').strip()
        if not girdi:
            await update.message.reply_text("❌ Boş metin gönderilemez!")
            return
        if len(girdi) > 500:
            await update.message.reply_text("❌ Metin en fazla 500 karakter olabilir.")
            return
        satirlar = [f"🔤 <b>İSİM FONTU</b> — <code>{html.escape(girdi)}</code>\n{'─'*22}"]
        for i, (stil_id, stil_adi) in enumerate(_ISIM_FONTU_LISTESI, 1):
            try:
                donusmus = _isim_fontu_uygula(girdi, stil_id)
            except Exception:
                donusmus = girdi
            satirlar.append(f"{i:02d}. {donusmus}  <i>— {stil_adi}</i>")
        satirlar.append(f"{'─'*22}\n📋 <i>Beğendiğin fontu kopyalayabilirsin!</i>")
        geri_klavye = InlineKeyboardMarkup([
            [InlineKeyboardButton('🔄 Yeni Metin', callback_data='pro_isim_fontu')],
            [InlineKeyboardButton('⬅️ Geri', callback_data='menu_pro_araclar')],
        ])
        # Unicode matematik harfleri Telegram'da 2 UTF-16 birimi sayılır.
        # Güvenli bölme: UTF-16 uzunluğunu gerçek hesapla, maks 3000 birim/mesaj.
        def _utf16(s: str) -> int:
            return sum(2 if ord(c) > 0xFFFF else 1 for c in s)
        MAX_UTF16 = 3000
        parcalar: list[list[str]] = [[]]
        parca_uzun = 0
        for satir in satirlar:
            satir_utf16 = _utf16(satir) + 1  # +1 newline
            if parca_uzun + satir_utf16 > MAX_UTF16 and parcalar[-1]:
                parcalar.append([])
                parca_uzun = 0
            parcalar[-1].append(satir)
            parca_uzun += satir_utf16
        for idx, parca in enumerate(parcalar):
            metin = '\n'.join(parca)
            klavye = geri_klavye if idx == len(parcalar) - 1 else None
            await update.message.reply_text(metin, reply_markup=klavye, parse_mode='HTML')
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
                "🇬🇪 Gürcistan: saat *22:00*'de grup kapanacak\n"
                "🇦🇿 Azərbaycan: saat *23:00*\\-da qrup bağlanacaq\n\n"
                "Tekrar açılış / Yenidən açılış:\n"
                "🇬🇪 *08:00* \\| 🇦🇿 *09:00* 💤"
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
    lang = get_lang(context, update.effective_user.id)
    sonuc = hash_uret(metin, lang)
    await update.effective_message.reply_text(sonuc, parse_mode='Markdown')

async def hava_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "🌍 **Hava Durumu**\n\nKullanım: `/hava Istanbul`\nÖrnek: `/hava Baku` veya `/hava Moscow`",
            parse_mode='Markdown'
        )
        return
    sehir = ' '.join(context.args)
    lang = get_lang(context, update.effective_user.id)
    bekle = await update.effective_message.reply_text(f"🌍 `{html.escape(sehir)}` sorgulanıyor...", parse_mode='Markdown')
    sonuc = await hava_durumu_getir(sehir, lang)
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
    lang = get_lang(context, update.effective_user.id)
    bekle = await update.effective_message.reply_text("💱 Kur bilgisi getiriliyor...", parse_mode='Markdown')
    sonuc = await doviz_cevir(metin, lang)
    try:
        await bekle.edit_text(sonuc, parse_mode='Markdown')
    except Exception:
        await bekle.edit_text(sonuc)

async def saat_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context, update.effective_user.id)
    sonuc = dunya_saati(lang)
    await update.effective_message.reply_text(sonuc, parse_mode='Markdown')

async def b64_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "🔒 **Base64 Aracı**\n\nKullanım:\n`/b64 encode metin`\n`/b64 decode bWV0aW4=`",
            parse_mode='Markdown'
        )
        return
    metin = ' '.join(context.args)
    lang = get_lang(context, update.effective_user.id)
    sonuc = base64_islem(metin, lang)
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


def vyo_ffmpeg_yazi_ekle(giris: str, cikti: str, yazi: str, konum: str, stil: str, renk: str, boyut: int = 52) -> bool:
    import subprocess as _sp
    konum_map = {
        'sag_yukari': 'x=w-tw-30:y=30',
        'sol_yukari': 'x=30:y=30',
        'sag_asagi':  'x=w-tw-30:y=h-th-30',
        'sol_asagi':  'x=30:y=h-th-30',
        'orta':       'x=(w-tw)/2:y=(h-th)/2',
    }
    renk_map = {
        'kirmizi': 'red',   'turuncu': 'orange',  'sari':    'yellow',
        'yesil':   'green', 'mavi':    'blue',     'mor':     'purple',
        'kahve':   'brown', 'siyah':   'black',    'beyaz':   'white',
        'pembe':   'pink',  'cyan':    'cyan',      'gri':    'gray',
        'altin':   'gold',  'gumus':   'silver',   'lacivert':'navy',
    }
    alpha_yazi  = '0.38' if stil == 'hayalet' else '1.0'
    alpha_border = '0.25' if stil == 'hayalet' else '0.85'
    xy = konum_map.get(konum, 'x=(w-tw)/2:y=(h-th)/2')
    yazi_esc = yazi.replace('\\', '\\\\').replace("'", "\\'").replace(':', '\\:').replace('%', '\\%')
    if renk == 'renksin':
        pi = '3.14159'
        fc_expr = (
            "fontcolor_expr='0x"
            "%{eif\\:255*(0.5+0.5*sin(2*" + pi + "*t/3+0))\\:x\\:2}"
            "%{eif\\:255*(0.5+0.5*sin(2*" + pi + "*t/3+2.094))\\:x\\:2}"
            "%{eif\\:255*(0.5+0.5*sin(2*" + pi + "*t/3+4.189))\\:x\\:2}'"
        )
        drawtext = (
            f"drawtext=text='{yazi_esc}':fontsize={boyut}:{fc_expr}:{xy}"
            f":borderw=3:bordercolor=black@{alpha_border}"
        )
    else:
        fontcolor = renk_map.get(renk, 'white')
        drawtext = (
            f"drawtext=text='{yazi_esc}':fontsize={boyut}:fontcolor={fontcolor}@{alpha_yazi}"
            f":{xy}:borderw=3:bordercolor=black@{alpha_border}"
        )
    cmd = ['ffmpeg', '-i', giris, '-vf', drawtext, '-codec:a', 'copy', '-preset', 'fast', '-y', cikti]
    try:
        r = _sp.run(cmd, capture_output=True, timeout=180)
        return r.returncode == 0
    except Exception:
        return False


async def medya_mesaj_yonet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await kanal_takip_kontrol(update, context, user_id, get_lang(context, user_id)):
        return
    durum = context.user_data.get('durum', '')
    mesaj = update.message
    if not mesaj:
        return

    try:
        await log_kanali_gonder(context.bot, update, f"📹 Video/Medya — durum: {durum or 'serbest'}")
    except Exception:
        pass

    def _video_al(mesaj):
        return mesaj.video or (mesaj.document if mesaj.document and mesaj.document.mime_type and mesaj.document.mime_type.startswith('video/') else None)

    VED_STATES = {
        'ved_kirp_video_bekle', 'ved_hiz_video_bekle', 'ved_don_video_bekle',
        'ved_ses_video_bekle', 'ved_sessiz_video_bekle', 'ved_kare_video_bekle',
        'ved_gif_video_bekle', 'ved_boyut_video_bekle', 'ved_filtre_video_bekle'
    }

    if durum in VED_STATES:
        video = _video_al(mesaj)
        if not video:
            await mesaj.reply_text("❌ Lütfen bir **video** gönderin (fotoğraf değil).", parse_mode='Markdown')
            return
        boyut = getattr(video, 'file_size', 0) or 0
        if boyut > 49 * 1024 * 1024:
            await mesaj.reply_text("❌ Video 49 MB'den büyük. Daha küçük bir video gönderin.")
            return
        bekle_msg = await mesaj.reply_text("⬇️ **Video indiriliyor...**", parse_mode='Markdown')
        try:
            import tempfile, os as _os, subprocess as _sp
            dosya = await context.bot.get_file(video.file_id)
            tmp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            tmp_path = tmp_video.name
            tmp_video.close()
            await dosya.download_to_drive(tmp_path)
            context.user_data.setdefault('ved', {})['video_path'] = tmp_path
        except Exception as e:
            logger.error(f"Video indirme hatası: {e}")
            await bekle_msg.edit_text("❌ Video indirilemedi. Tekrar deneyin.")
            return

        if durum == 'ved_kirp_video_bekle':
            context.user_data['durum'] = 'ved_kirp_sure_bekle'
            await bekle_msg.edit_text(
                "✅ **Video alındı!**\n\n"
                "✂️ **Kırpma aralığını gir:**\n\n"
                "Örnek: `5-30` _(5. saniyeden 30. saniyeye)_",
                parse_mode='Markdown'
            )
        elif durum == 'ved_hiz_video_bekle':
            context.user_data['durum'] = None
            hiz_klavye = InlineKeyboardMarkup([
                [InlineKeyboardButton("🐢 0.5x Yavaş", callback_data='ved_hiz_sec_0_5'),
                 InlineKeyboardButton("⚡ 1.5x Hızlı", callback_data='ved_hiz_sec_1_5')],
                [InlineKeyboardButton("🚀 2x Süper Hızlı", callback_data='ved_hiz_sec_2_0'),
                 InlineKeyboardButton("🐇 3x Ultra", callback_data='ved_hiz_sec_3_0')],
                [InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]
            ])
            await bekle_msg.edit_text(
                "✅ **Video alındı!**\n\n⚡ **Hız seçin:**",
                reply_markup=hiz_klavye, parse_mode='Markdown'
            )
        elif durum == 'ved_don_video_bekle':
            context.user_data['durum'] = None
            don_klavye = InlineKeyboardMarkup([
                [InlineKeyboardButton("↪️ 90° Sağa", callback_data='ved_don_sec_90'),
                 InlineKeyboardButton("🔄 180°", callback_data='ved_don_sec_180')],
                [InlineKeyboardButton("↩️ 270° Sola", callback_data='ved_don_sec_270')],
                [InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]
            ])
            await bekle_msg.edit_text(
                "✅ **Video alındı!**\n\n🔄 **Döndürme açısı seçin:**",
                reply_markup=don_klavye, parse_mode='Markdown'
            )
        elif durum == 'ved_ses_video_bekle':
            context.user_data['durum'] = None
            video_path = context.user_data.get('ved', {}).get('video_path', '')
            await bekle_msg.edit_text("🎵 **Ses çıkarılıyor...**", parse_mode='Markdown')
            try:
                cikis = video_path.replace('.mp4', '_ses.mp3')
                cmd = ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'mp3', '-q:a', '2', cikis, '-y']
                result = await asyncio.to_thread(lambda: _sp.run(cmd, capture_output=True, timeout=120))
                if result.returncode != 0 or not _os.path.exists(cikis):
                    raise Exception("FFmpeg başarısız")
                with open(cikis, 'rb') as af:
                    await update.effective_chat.send_audio(
                        audio=af,
                        caption="✅ **Ses çıkarıldı!**\n_AZRxGUARD Video Editör_ 🎵",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Video Editör", callback_data='menu_video_olusturucu'), InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')]])
                    )
                await bekle_msg.delete()
                for f in [video_path, cikis]:
                    try: _os.remove(f)
                    except: pass
            except Exception as e:
                logger.error(f"Ses çıkarma hatası: {e}")
                await bekle_msg.edit_text("❌ Ses çıkarılamadı.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Tekrar", callback_data='ved_ses_baslat'), InlineKeyboardButton("🏠", callback_data='go_home')]]))
        elif durum == 'ved_sessiz_video_bekle':
            context.user_data['durum'] = None
            video_path = context.user_data.get('ved', {}).get('video_path', '')
            await bekle_msg.edit_text("🔇 **Video sessizleştiriliyor...**", parse_mode='Markdown')
            try:
                cikis = video_path.replace('.mp4', '_sessiz.mp4')
                cmd = ['ffmpeg', '-i', video_path, '-an', '-c:v', 'copy', cikis, '-y']
                result = await asyncio.to_thread(lambda: _sp.run(cmd, capture_output=True, timeout=120))
                if result.returncode != 0 or not _os.path.exists(cikis):
                    raise Exception("FFmpeg başarısız")
                with open(cikis, 'rb') as vf:
                    await update.effective_chat.send_video(
                        video=vf,
                        caption="✅ **Video sessizleştirildi!**\n_AZRxGUARD Video Editör_ 🔇",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Video Editör", callback_data='menu_video_olusturucu'), InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')]])
                    )
                await bekle_msg.delete()
                for f in [video_path, cikis]:
                    try: _os.remove(f)
                    except: pass
            except Exception as e:
                logger.error(f"Sessizleştirme hatası: {e}")
                await bekle_msg.edit_text("❌ Sessizleştirme başarısız.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Tekrar", callback_data='ved_sessiz_baslat'), InlineKeyboardButton("🏠", callback_data='go_home')]]))
        elif durum == 'ved_kare_video_bekle':
            context.user_data['durum'] = 'ved_kare_sure_bekle'
            await bekle_msg.edit_text(
                "✅ **Video alındı!**\n\n"
                "📸 **Hangi saniyeden kare almak istiyorsun?**\n\n"
                "Örnek: `5` veya `10.5`",
                parse_mode='Markdown'
            )
        elif durum == 'ved_gif_video_bekle':
            context.user_data['durum'] = None
            video_path = context.user_data.get('ved', {}).get('video_path', '')
            await bekle_msg.edit_text("🎞️ **GIF oluşturuluyor... (İlk 6 saniye)**", parse_mode='Markdown')
            try:
                cikis = video_path.replace('.mp4', '.gif')
                palette = video_path.replace('.mp4', '_palette.png')
                cmd1 = ['ffmpeg', '-i', video_path, '-t', '6', '-vf', 'fps=10,scale=480:-1:flags=lanczos,palettegen', palette, '-y']
                cmd2 = ['ffmpeg', '-i', video_path, '-i', palette, '-t', '6', '-filter_complex', 'fps=10,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse', cikis, '-y']
                await asyncio.to_thread(lambda: _sp.run(cmd1, capture_output=True, timeout=60))
                result = await asyncio.to_thread(lambda: _sp.run(cmd2, capture_output=True, timeout=120))
                if result.returncode != 0 or not _os.path.exists(cikis):
                    raise Exception("FFmpeg başarısız")
                with open(cikis, 'rb') as gf:
                    await update.effective_chat.send_animation(
                        animation=gf,
                        caption="✅ **GIF hazır!** 🎞️\n_AZRxGUARD Video Editör_",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Video Editör", callback_data='menu_video_olusturucu'), InlineKeyboardButton("🏠 Ana Menü", callback_data='go_home')]])
                    )
                await bekle_msg.delete()
                for f in [video_path, cikis, palette]:
                    try: _os.remove(f)
                    except: pass
            except Exception as e:
                logger.error(f"GIF hatası: {e}")
                await bekle_msg.edit_text("❌ GIF oluşturulamadı. Daha kısa bir video deneyin.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Tekrar", callback_data='ved_gif_baslat'), InlineKeyboardButton("🏠", callback_data='go_home')]]))
        elif durum == 'ved_boyut_video_bekle':
            context.user_data['durum'] = None
            boyut_klavye = InlineKeyboardMarkup([
                [InlineKeyboardButton("🖥️ 1080p (Full HD)", callback_data='ved_boyut_sec_1080'),
                 InlineKeyboardButton("📺 720p (HD)", callback_data='ved_boyut_sec_720')],
                [InlineKeyboardButton("📱 480p", callback_data='ved_boyut_sec_480'),
                 InlineKeyboardButton("📻 360p", callback_data='ved_boyut_sec_360')],
                [InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]
            ])
            await bekle_msg.edit_text(
                "✅ **Video alındı!**\n\n📐 **Çıktı çözünürlüğünü seçin:**",
                reply_markup=boyut_klavye, parse_mode='Markdown'
            )
        elif durum == 'ved_filtre_video_bekle':
            context.user_data['durum'] = None
            filtre_klavye = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬛ Siyah-Beyaz", callback_data='ved_filtre_sec_bw'),
                 InlineKeyboardButton("🟫 Sepia", callback_data='ved_filtre_sec_sepia')],
                [InlineKeyboardButton("☀️ Parlak", callback_data='ved_filtre_sec_parlak'),
                 InlineKeyboardButton("🌑 Karanlık", callback_data='ved_filtre_sec_karanlik')],
                [InlineKeyboardButton("🎞️ Vintage", callback_data='ved_filtre_sec_vintage')],
                [InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]
            ])
            await bekle_msg.edit_text(
                "✅ **Video alındı!**\n\n🎨 **Filtre seçin:**",
                reply_markup=filtre_klavye, parse_mode='Markdown'
            )
        return

    if durum == 'vyo_video_bekle':
        video = _video_al(mesaj)
        if not video:
            await mesaj.reply_text("❌ Lütfen bir **video** gönderin (fotoğraf değil).\nTekrar deneyin veya /start yazın.", parse_mode='Markdown')
            return
        boyut = getattr(video, 'file_size', 0) or 0
        if boyut > 49 * 1024 * 1024:
            await mesaj.reply_text("❌ Video çok büyük! Maksimum 49 MB gönderin.")
            return
        context.user_data.setdefault('vyo', {})['video_fid'] = video.file_id
        context.user_data['durum'] = 'vyo_yazi_bekle'
        geri = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data='menu_video_olusturucu')]])
        await mesaj.reply_text(
            "✅ **Video alındı!**\n\n"
            "✍️ **LÜTFEN EKLEMEK İSTEDİĞİNİZ ŞEYİ YAZIN**\n\n"
            "_Örnek: AZRxGUARD, Merhaba Dünya, © 2025_",
            reply_markup=geri,
            parse_mode='Markdown'
        )
        return


async def diger_medya_log_yonet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await kanal_takip_kontrol(update, context, user_id, get_lang(context, user_id)):
        return
    mesaj = update.message
    if not mesaj:
        return

    tur = (
        "📸 Fotoğraf" if mesaj.photo else
        "🎙️ Ses Notu" if mesaj.voice else
        "🎵 Müzik" if mesaj.audio else
        "📄 Döküman" if mesaj.document else
        "🎭 Sticker" if mesaj.sticker else
        "🎞️ GIF/Animasyon" if mesaj.animation else
        "🎥 Video Not" if mesaj.video_note else
        "📦 Medya"
    )
    try:
        await log_kanali_gonder(context.bot, update, tur)
    except Exception:
        pass


async def ai_sifirla_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['durum'] = None
    lang = get_lang(context, update.effective_user.id)
    sifirlama_mesajlari = {
        'tr': "✅ Durum sıfırlandı. /start ile devam edebilirsin.",
        'az': "✅ Vəziyyət sıfırlandı. /start ilə davam edə bilərsən.",
        'ru': "✅ Состояние сброшено. Продолжай с /start.",
        'en': "✅ State reset. Continue with /start.",
        'de': "✅ Zustand zurückgesetzt. Weiter mit /start.",
        'ka': "✅ მდგომარეობა გადაყენდა. გააგრძელე /start-ით.",
    }
    await update.message.reply_text(
        sifirlama_mesajlari.get(lang, sifirlama_mesajlari['tr']),
        parse_mode='Markdown'
    )


# ══════════════════════════════════════════════════════
# 🆕 AZRxGUARD 2.0 — YENİ KOMUTLAR
# ══════════════════════════════════════════════════════

# --- 🏓 PING ---
async def ping_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    baslangic = datetime.datetime.now()
    msg = await update.message.reply_text("🏓 Ölçülüyor...")
    gecikme = (datetime.datetime.now() - baslangic).total_seconds() * 1000
    await msg.edit_text(
        f"🏓 **Pong!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚡ **Gecikme:** `{gecikme:.1f} ms`\n"
        f"🟢 **Bot Durumu:** Aktif & Çalışıyor\n"
        f"🕐 **Saat (TR):** `{datetime.datetime.now(TR_SAAT).strftime('%H:%M:%S')}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_AZRxGUARD 2.0_",
        parse_mode='Markdown'
    )

# --- 🎨 RENK DÖNÜŞTÜRÜCÜ ---
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
    cmax, cmin = max(r, g, b), min(r, g, b)
    delta = cmax - cmin
    l = (cmax + cmin) / 2
    if delta == 0:
        h = s = 0.0
    else:
        s = delta / (1 - abs(2*l - 1))
        if cmax == r:   h = 60 * (((g - b) / delta) % 6)
        elif cmax == g: h = 60 * ((b - r) / delta + 2)
        else:           h = 60 * ((r - g) / delta + 4)
    return round(h), round(s*100), round(l*100)

async def renk_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🎨 **Renk Dönüştürücü**\n\n"
            "**Kullanım:**\n"
            "`/renk #FF5733` — HEX → RGB + HSL\n"
            "`/renk 255 87 51` — RGB → HEX + HSL\n\n"
            "**Örnek:** `/renk #1a2b3c` veya `/renk 255 0 128`",
            parse_mode='Markdown'
        )
        return
    girdi = ' '.join(context.args).strip()
    r = g = b = None
    hex_str = None
    if girdi.startswith('#') or (len(girdi.lstrip('#')) in (3, 6) and all(c in '0123456789abcdefABCDEF' for c in girdi.lstrip('#'))):
        res = _hex_to_rgb(girdi)
        if res:
            r, g, b = res
            h_raw = girdi.lstrip('#').upper()
            hex_str = ''.join(c*2 for c in h_raw) if len(h_raw) == 3 else h_raw
    elif len(context.args) == 3:
        try:
            r, g, b = int(context.args[0]), int(context.args[1]), int(context.args[2])
            if not all(0 <= x <= 255 for x in (r, g, b)):
                raise ValueError
            hex_str = f"{r:02X}{g:02X}{b:02X}"
        except ValueError:
            await update.message.reply_text("❌ RGB değerleri 0-255 arasında olmalı!", parse_mode='Markdown')
            return
    if r is None:
        await update.message.reply_text("❌ Geçersiz format!\n`/renk #FF5733` veya `/renk 255 87 51`", parse_mode='Markdown')
        return
    h, s, lv = _rgb_to_hsl(r, g, b)
    if   r > 180 and g < 100 and b < 100: ton = "🔴 Kırmızı tonu"
    elif r < 100 and g > 150 and b < 100: ton = "🟢 Yeşil tonu"
    elif r < 100 and g < 100 and b > 150: ton = "🔵 Mavi tonu"
    elif r > 200 and g > 200 and b < 80:  ton = "🟡 Sarı tonu"
    elif r > 200 and g > 100 and b < 80:  ton = "🟠 Turuncu tonu"
    elif r > 100 and g < 80  and b > 150: ton = "🟣 Mor tonu"
    elif r > 200 and g > 200 and b > 200: ton = "⬜ Beyaz / Açık"
    elif r < 60  and g < 60  and b < 60:  ton = "⬛ Siyah / Koyu"
    else: ton = "🎨 Karma renk"
    await update.message.reply_text(
        f"🎨 **RENK ANALİZİ**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔷 **HEX:** `#{hex_str}`\n"
        f"🔴🟢🔵 **RGB:** `rgb({r}, {g}, {b})`\n"
        f"🌈 **HSL:** `hsl({h}°, {s}%, {lv}%)`\n\n"
        f"🎯 **Renk Tonu:** {ton}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_AZRxGUARD 2.0 Renk Motoru_",
        parse_mode='Markdown'
    )

# --- 📊 METİN ANALİZÖRÜ ---
async def metin_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    metin = None
    if msg.reply_to_message and msg.reply_to_message.text:
        metin = msg.reply_to_message.text
    elif context.args:
        metin = ' '.join(context.args)
    if not metin:
        await msg.reply_text(
            "📊 **Metin Analizörü**\n\n"
            "Bir mesajı **yanıtlayarak** `/metin` yaz\n"
            "veya: `/metin Analiz edilecek metin`",
            parse_mode='Markdown'
        )
        return
    kelimeler   = metin.split()
    satirlar    = metin.splitlines()
    karakter    = len(metin)
    bosluksuz   = len(metin.replace(' ', '').replace('\n', ''))
    kelime_sayi = len(kelimeler)
    satir_sayi  = len(satirlar)
    freq = {}
    for k in kelimeler:
        k2 = k.lower().strip('.,!?;:()[]{}"\'-')
        if len(k2) > 2:
            freq[k2] = freq.get(k2, 0) + 1
    en_sik = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
    en_sik_str = '\n'.join(f"  `{k}` → {v}x" for k, v in en_sik) if en_sik else "  —"
    ort_uzunluk = sum(len(k) for k in kelimeler) / max(kelime_sayi, 1)
    okuma_sn = (kelime_sayi / 200) * 60
    okuma_str = f"{int(okuma_sn)} saniye" if okuma_sn < 60 else f"{okuma_sn/60:.1f} dakika"
    await msg.reply_text(
        f"📊 **METİN ANALİZİ**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔤 **Karakter:** `{karakter}` (boşluksuz: `{bosluksuz}`)\n"
        f"📝 **Kelime:** `{kelime_sayi}`\n"
        f"📄 **Satır:** `{satir_sayi}`\n"
        f"📏 **Ort. Kelime Uzunluğu:** `{ort_uzunluk:.1f}`\n"
        f"⏱️ **Tahmini Okuma:** `{okuma_str}`\n\n"
        f"🔝 **En Sık Kelimeler:**\n{en_sik_str}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_AZRxGUARD 2.0 Metin Motoru_",
        parse_mode='Markdown'
    )

# --- 🎲 RASTGELE ARAÇLAR ---
async def rastgele_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🎲 **Rastgele Araçlar**\n\n"
            "`/rastgele sayi 1 100` — Sayı üret\n"
            "`/rastgele zar` — 1d6 zar at\n"
            "`/rastgele zar 2 20` — 2×d20 zar\n"
            "`/rastgele para` — Yazı / Tura\n"
            "`/rastgele sec elma muz çilek` — Listeden seç",
            parse_mode='Markdown'
        )
        return
    mod = context.args[0].lower()
    if mod in ('sayi', 'sayı', 'number'):
        try:
            alt = int(context.args[1]) if len(context.args) > 1 else 1
            ust = int(context.args[2]) if len(context.args) > 2 else 100
            if alt >= ust: raise ValueError
            sonuc = random.randint(alt, ust)
            await update.message.reply_text(
                f"🎲 **RASTGELE SAYI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔢 **Aralık:** `{alt}` — `{ust}`\n"
                f"🎯 **Sonuç:** **`{sonuc}`**\n\n━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Kullanım: `/rastgele sayi 1 100`", parse_mode='Markdown')
    elif mod in ('zar', 'dice'):
        try:
            adet = min(int(context.args[1]) if len(context.args) > 1 else 1, 20)
            yuze = min(int(context.args[2]) if len(context.args) > 2 else 6, 1000)
            if adet < 1 or yuze < 2: raise ValueError
            atislar = [random.randint(1, yuze) for _ in range(adet)]
            toplam  = sum(atislar)
            atislar_str = ' + '.join(f'`{a}`' for a in atislar)
            await update.message.reply_text(
                f"🎲 **ZAR ATIŞI — {adet}d{yuze}**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📊 **Sonuçlar:** {atislar_str}\n"
                f"✨ **Toplam:** **`{toplam}`**\n\n━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Kullanım: `/rastgele zar 2 6`", parse_mode='Markdown')
    elif mod in ('para', 'coin'):
        sonuc = random.choice(['🟡 **YAZI**', '🔵 **TURA**'])
        await update.message.reply_text(
            f"🪙 **PARA ATIŞI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💫 **Sonuç:** {sonuc}\n\n━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )
    elif mod in ('sec', 'seç', 'pick'):
        secenekler = context.args[1:]
        if len(secenekler) < 2:
            await update.message.reply_text("❌ En az 2 seçenek gir! Örnek: `/rastgele sec elma muz çilek`", parse_mode='Markdown')
            return
        secilen = random.choice(secenekler)
        await update.message.reply_text(
            f"🎯 **RASTGELE SEÇİM**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📋 **Seçenekler:** {' · '.join(f'`{s}`' for s in secenekler)}\n"
            f"✨ **Seçilen:** **`{secilen}`**\n\n━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Geçersiz mod! `/rastgele` yazarak yardım al.", parse_mode='Markdown')

# --- 🔠 ŞİFRELEME ARAÇLARI ---
_MORSE = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....',
    'I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-',
    'R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....',
    '6':'-....','7':'--...','8':'---..','9':'----.', ' ':'/'
}

def _caesar(metin: str, n: int) -> str:
    return ''.join(
        chr((ord(c) - (ord('A') if c.isupper() else ord('a')) + n) % 26 + (ord('A') if c.isupper() else ord('a')))
        if c.isalpha() else c
        for c in metin
    )

async def sifrele_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🔠 **Şifreleme Araçları**\n\n"
            "`/sifrele caesar 13 metin` — Caesar şifre\n"
            "`/sifrele rot13 metin` — ROT-13\n"
            "`/sifrele ters metin` — Ters çevir\n"
            "`/sifrele morse metin` — Morse kodu\n\n"
            "**Örnek:** `/sifrele caesar 3 Merhaba`",
            parse_mode='Markdown'
        )
        return
    mod = context.args[0].lower()
    if mod == 'caesar':
        try:
            n = int(context.args[1])
            metin = ' '.join(context.args[2:])
            if not metin: raise ValueError
            await update.message.reply_text(
                f"🔠 **CAESAR ŞİFRE**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📥 **Giriş:** `{html.escape(metin)}`\n"
                f"🔢 **Kaydırma:** `{n}`\n\n"
                f"🔒 **Şifreli:** `{html.escape(_caesar(metin, n))}`\n"
                f"🔓 **Çözülmüş (-{n}):** `{html.escape(_caesar(metin, -n))}`\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Kullanım: `/sifrele caesar 13 Merhaba`", parse_mode='Markdown')
    elif mod == 'rot13':
        metin = ' '.join(context.args[1:])
        if not metin:
            await update.message.reply_text("❌ Metin gir!", parse_mode='Markdown')
            return
        await update.message.reply_text(
            f"🔄 **ROT-13**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 **Giriş:** `{html.escape(metin)}`\n"
            f"📤 **ROT-13:** `{html.escape(_caesar(metin, 13))}`\n\n"
            f"💡 _Tekrar aynı komutla geri alınır_\n━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )
    elif mod == 'ters':
        metin = ' '.join(context.args[1:])
        if not metin:
            await update.message.reply_text("❌ Metin gir!", parse_mode='Markdown')
            return
        await update.message.reply_text(
            f"🔃 **METİN TERSİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 **Giriş:** `{html.escape(metin)}`\n"
            f"📤 **Ters:** `{html.escape(metin[::-1])}`\n\n━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )
    elif mod == 'morse':
        metin = ' '.join(context.args[1:]).upper()
        if not metin:
            await update.message.reply_text("❌ Metin gir!", parse_mode='Markdown')
            return
        morse = ' '.join(_MORSE.get(c, '?') for c in metin)
        await update.message.reply_text(
            f"📡 **MORSE KODU**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 **Giriş:** `{html.escape(metin)}`\n"
            f"📤 **Morse:**\n`{morse}`\n\n━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Geçersiz mod! `/sifrele` yazarak yardım al.", parse_mode='Markdown')

# --- 💪 BMI HESAPLAYICI ---
async def bmi_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "💪 **BMI Hesaplayıcı**\n\n"
            "**Kullanım:** `/bmi <boy_cm> <kilo_kg>`\n"
            "**Örnek:** `/bmi 175 70`",
            parse_mode='Markdown'
        )
        return
    try:
        boy, kilo = float(context.args[0]), float(context.args[1])
        if not (50 <= boy <= 300 and 10 <= kilo <= 500):
            await update.message.reply_text("❌ Geçersiz değer! Boy: 50-300 cm, Kilo: 10-500 kg")
            return
        boy_m = boy / 100
        bmi   = kilo / (boy_m ** 2)
        if   bmi < 18.5: durum = "🔵 Zayıf"; tavsiye = "Daha fazla kalori ve güç antrenmanı önerilir."
        elif bmi < 25:   durum = "🟢 Normal"; tavsiye = "Mevcut yaşam tarzını sürdür. Harika!"
        elif bmi < 30:   durum = "🟡 Fazla Kilolu"; tavsiye = "Hafif egzersiz ve dengeli beslenme önerilir."
        elif bmi < 35:   durum = "🟠 Obez I"; tavsiye = "Düzenli egzersiz ve diyet programı önerilir."
        else:            durum = "🔴 Obez II+"; tavsiye = "Bir sağlık uzmanıyla görüşmeniz önerilir."
        ideal_alt = 18.5 * (boy_m ** 2)
        ideal_ust = 24.9 * (boy_m ** 2)
        await update.message.reply_text(
            f"💪 **BMI ANALİZİ**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📏 **Boy:** `{boy} cm`  |  ⚖️ **Kilo:** `{kilo} kg`\n"
            f"📊 **BMI:** **`{bmi:.1f}`**\n\n"
            f"🏷️ **Durum:** {durum}\n"
            f"💡 **Tavsiye:** _{tavsiye}_\n\n"
            f"🎯 **İdeal Kilo Aralığı:** `{ideal_alt:.1f} — {ideal_ust:.1f} kg`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ _Yalnızca bilgilendirme amaçlıdır._",
            parse_mode='Markdown'
        )
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Kullanım: `/bmi 175 70`", parse_mode='Markdown')

# --- 💯 YÜZDE HESAPLAYICI ---
async def yuzde_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "💯 **Yüzde Hesaplayıcı**\n\n"
            "`/yuzde 20% 500` — 500'ün %20'si\n"
            "`/yuzde 75 150` — 75, 150'nin %kaçı?\n"
            "`/yuzde artis 200 250` — % artış\n"
            "`/yuzde azalis 300 240` — % azalış\n\n"
            "**Örnek:** `/yuzde 15% 1200`",
            parse_mode='Markdown'
        )
        return
    try:
        mod = context.args[0].lower()
        if mod in ('artis', 'artış'):
            a, b = float(context.args[1]), float(context.args[2])
            oran = ((b - a) / a) * 100
            emoji = "📈" if oran >= 0 else "📉"
            await update.message.reply_text(
                f"💯 **YÜZDE DEĞİŞİM**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔢 `{a}` → `{b}`\n"
                f"{emoji} **Değişim:** `{oran:+.2f}%`\n\n━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
        elif mod in ('azalis', 'azalış'):
            a, b = float(context.args[1]), float(context.args[2])
            oran = ((a - b) / a) * 100
            await update.message.reply_text(
                f"💯 **YÜZDE DEĞİŞİM**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔢 `{a}` → `{b}`\n"
                f"📉 **Azalış:** `{oran:.2f}%`\n\n━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
        elif '%' in mod:
            yv = float(mod.replace('%', ''))
            sayi = float(context.args[1])
            sonuc = (yv / 100) * sayi
            await update.message.reply_text(
                f"💯 **YÜZDE HESABI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📥 `{sayi}`'nin `%{yv}`'i = **`{sonuc:.4g}`**\n\n━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
        else:
            parca, toplam = float(context.args[0]), float(context.args[1])
            oran = (parca / toplam) * 100
            await update.message.reply_text(
                f"💯 **YÜZDE HESABI**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📥 `{parca}`, `{toplam}`'nin → **`%{oran:.2f}`**\n\n━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
    except (ValueError, IndexError, ZeroDivisionError):
        await update.message.reply_text("❌ Geçersiz format! `/yuzde` yazarak yardım al.", parse_mode='Markdown')

async def sifre_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uzunluk = 16
    if context.args:
        try:
            uzunluk = max(8, min(64, int(context.args[0])))
        except ValueError:
            pass
    sifre = sifre_uret(uzunluk)
    await update.message.reply_text(
        f"🔑 **Güvenli Şifre**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"`{sifre}`\n\n"
        f"📏 Uzunluk: **{uzunluk}** karakter\n"
        f"✅ Büyük/küçük harf, rakam, sembol\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Farklı uzunluk: `/sifre 32`",
        parse_mode='Markdown'
    )

async def kimlik_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kimlik = sahte_kimlik_uret()
    await update.message.reply_text(kimlik, parse_mode='Markdown')

async def kisalt_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🔗 **URL Kısaltıcı**\n\nKullanım: `/kisalt https://ornek.com/uzun-link`",
            parse_mode='Markdown'
        )
        return
    url = context.args[0]
    sonuc = await url_kisalt(url)
    await update.message.reply_text(sonuc, parse_mode='Markdown')

async def wiki_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🌐 **Wikipedia**\n\nKullanım: `/wiki Python programlama`",
            parse_mode='Markdown'
        )
        return
    sorgu = ' '.join(context.args)
    sonuc = await wikipedia_ara(sorgu)
    await update.message.reply_text(sonuc, parse_mode='Markdown')

# ══════════════════════════════════════════════════════
# 💬 SOHBET ARAÇLARI & 🛡️ GRUP YÖNETİMİ — AZRxGUARD v3.0
# ══════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────────
# 🛡️ GRUP YÖNETİM ARAÇLARI — Ban / Kick / Mute / Warn / Temizle
# ─────────────────────────────────────────────────────────────

_UYARI_DOSYASI = "grup_uyarilari.json"

def _uyari_yukle() -> dict:
    try:
        with open(_UYARI_DOSYASI, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _uyari_kaydet(veri: dict) -> None:
    try:
        with open(_UYARI_DOSYASI, 'w', encoding='utf-8') as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Uyarı kaydedilemedi: {e}")

async def _admin_mi(update: Update, context) -> bool:
    """Komutu kullanan kişi admin/creator mi? Anonim adminleri de destekler."""
    user = update.effective_user
    if not user:
        return False
    # Anonim admin — Telegram'da admin mesajları grup adıyla görünebilir
    if getattr(user, 'is_anonymous', False):
        return True
    try:
        uye = await context.bot.get_chat_member(update.effective_chat.id, user.id)
        return uye.status in ('administrator', 'creator')
    except Exception:
        # get_chat_member başarısız olursa (gizlilik ayarı vs.) işlemi Telegram API'ye bırak
        return True

async def _hedef_al(update: Update, context) -> tuple:
    """(user_id, display_name) döndürür. Reply veya @mention veya ID'den alır."""
    msg = update.effective_message
    # 1) Reply
    if msg.reply_to_message and msg.reply_to_message.from_user:
        u = msg.reply_to_message.from_user
        return u.id, f"<a href='tg://user?id={u.id}'>{html.escape(u.first_name or str(u.id))}</a>"
    # 2) @mention veya sayısal ID argümanı
    if context.args:
        arg = context.args[0]
        try:
            uid = int(arg)
            return uid, f"<code>{uid}</code>"
        except ValueError:
            username = arg.lstrip('@')
            # Önce grup üyeleri içinde ara
            try:
                uye = await context.bot.get_chat_member(update.effective_chat.id, f"@{username}")
                u = uye.user
                return u.id, f"<a href='tg://user?id={u.id}'>{html.escape(u.first_name or username)}</a>"
            except Exception:
                pass
            # Grup üyeleri içinde bulunamazsa Telegram global arama
            try:
                chat = await context.bot.get_chat(f"@{username}")
                isim = getattr(chat, 'first_name', None) or getattr(chat, 'title', None) or username
                return chat.id, f"<a href='tg://user?id={chat.id}'>{html.escape(isim)}</a>"
            except Exception:
                return None, None
    return None, None

def _sure_cozumle(arg: str) -> int | None:
    """'30d'→1800, '2s'→7200, '1g'→86400 saniye döndürür. None=sonsuza dek."""
    if not arg:
        return None
    arg = arg.strip().lower()
    m = re.match(r'^(\d+)([dsgh]?)$', arg)
    if not m:
        return None
    sayi, birim = int(m.group(1)), m.group(2)
    if birim == 'd':
        return sayi * 60
    elif birim == 's':
        return sayi * 3600
    elif birim == 'g':
        return sayi * 86400
    elif birim == 'h':
        return sayi * 3600
    else:
        return sayi * 60

async def ban_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ('group', 'supergroup'):
        return
    if not await _admin_mi(update, context):
        await update.message.reply_text("❌ Bu komut sadece adminler içindir.")
        return
    uid, display = await _hedef_al(update, context)
    if not uid:
        await update.message.reply_text(
            "❌ <b>Kullanıcı bulunamadı!</b>\n\n"
            "💡 <b>Kullanım:</b>\n"
            "• Kişinin mesajına <b>yanıt ver</b> → <code>/ban [sebep]</code>\n"
            "• Kullanıcı adıyla → <code>/ban @kullanici [sebep]</code>\n"
            "• ID ile → <code>/ban 123456789</code>\n\n"
            "⚠️ <i>@username yoksa mesaja yanıt vererek kullan!</i>",
            parse_mode='HTML'
        )
        return
    # Reply ile kullanıldıysa tüm args sebep, mention ile kullanıldıysa args[1:] sebep
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        sebep = html.escape(' '.join(context.args)) if context.args else "Sebep belirtilmedi"
    else:
        sebep = html.escape(' '.join(context.args[1:])) if len(context.args) > 1 else "Sebep belirtilmedi"
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, uid)
        await update.message.reply_text(
            f"🔨 <b>BANLANDI!</b>\n\n👤 Kullanıcı: {display}\n🆔 ID: <code>{uid}</code>\n📝 Sebep: {sebep}",
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ban işlemi başarısız: <code>{html.escape(str(e))}</code>", parse_mode='HTML')

async def unban_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ('group', 'supergroup'):
        return
    if not await _admin_mi(update, context):
        await update.message.reply_text("❌ Bu komut sadece adminler içindir.")
        return
    uid, display = await _hedef_al(update, context)
    if not uid:
        await update.message.reply_text(
            "❌ <b>Kullanıcı bulunamadı!</b>\n\n"
            "💡 Mesaja yanıt ver → <code>/unban</code>\n"
            "veya → <code>/unban @kullanici</code>",
            parse_mode='HTML'
        )
        return
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, uid, only_if_banned=True)
        await update.message.reply_text(
            f"✅ <b>BAN KALDIRILDI!</b>\n\n👤 Kullanıcı: {display}\n🆔 ID: <code>{uid}</code>",
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Unban başarısız: <code>{html.escape(str(e))}</code>", parse_mode='HTML')

async def kick_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ('group', 'supergroup'):
        return
    if not await _admin_mi(update, context):
        await update.message.reply_text("❌ Bu komut sadece adminler içindir.")
        return
    uid, display = await _hedef_al(update, context)
    if not uid:
        await update.message.reply_text(
            "❌ <b>Kullanıcı bulunamadı!</b>\n\n"
            "💡 Mesaja yanıt ver → <code>/kick</code>\n"
            "veya → <code>/kick @kullanici</code>\n\n"
            "⚠️ <i>@username yoksa mesaja yanıt vererek kullan!</i>",
            parse_mode='HTML'
        )
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, uid)
        await context.bot.unban_chat_member(update.effective_chat.id, uid)
        await update.message.reply_text(
            f"👢 <b>GRUPTAN ATILDI!</b>\n\n👤 Kullanıcı: {display}\n🆔 ID: <code>{uid}</code>\n_(Tekrar katılabilir)_",
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Kick başarısız: <code>{html.escape(str(e))}</code>", parse_mode='HTML')

async def mute_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ('group', 'supergroup'):
        return
    if not await _admin_mi(update, context):
        await update.message.reply_text("❌ Bu komut sadece adminler içindir.")
        return
    uid, display = await _hedef_al(update, context)
    if not uid:
        await update.message.reply_text(
            "❌ <b>Kullanıcı bulunamadı!</b>\n\n"
            "💡 Mesaja yanıt ver → <code>/mute [süre]</code>\n"
            "veya → <code>/mute @kullanici [süre]</code>\n\n"
            "⏱ <b>Süre örnekleri:</b>\n"
            "• <code>30d</code> = 30 dakika\n"
            "• <code>2s</code> = 2 saat\n"
            "• <code>1g</code> = 1 gün\n"
            "• Süre yazmazsan = süresiz\n\n"
            "⚠️ <i>@username yoksa mesaja yanıt vererek kullan!</i>",
            parse_mode='HTML'
        )
        return
    sure_arg = None
    if context.args:
        son = context.args[-1]
        if re.match(r'^\d+[dsgh]?$', son):
            sure_arg = son
    saniye = _sure_cozumle(sure_arg) if sure_arg else None
    until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=saniye) if saniye else None
    sure_metin = sure_arg if sure_arg else "Süresiz"
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, uid,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        await update.message.reply_text(
            f"🔇 <b>SESSİZE ALINDI!</b>\n\n👤 Kullanıcı: {display}\n⏱️ Süre: {sure_metin}",
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Mute başarısız: <code>{html.escape(str(e))}</code>", parse_mode='HTML')

async def unmute_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ('group', 'supergroup'):
        return
    if not await _admin_mi(update, context):
        await update.message.reply_text("❌ Bu komut sadece adminler içindir.")
        return
    uid, display = await _hedef_al(update, context)
    if not uid:
        await update.message.reply_text(
            "❌ <b>Kullanıcı bulunamadı!</b>\n\n"
            "💡 Mesaja yanıt ver → <code>/unmute</code>\n"
            "veya → <code>/unmute @kullanici</code>",
            parse_mode='HTML'
        )
        return
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, uid,
            permissions=ChatPermissions(
                can_send_messages=True, can_send_audios=True,
                can_send_documents=True, can_send_photos=True,
                can_send_videos=True, can_send_video_notes=True,
                can_send_voice_notes=True, can_send_polls=True,
                can_send_other_messages=True, can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(
            f"🔊 <b>SESİ AÇILDI!</b>\n\n👤 Kullanıcı: {display}",
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Unmute başarısız: <code>{html.escape(str(e))}</code>", parse_mode='HTML')

async def warn_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ('group', 'supergroup'):
        return
    if not await _admin_mi(update, context):
        await update.message.reply_text("❌ Bu komut sadece adminler içindir.")
        return
    uid, display = await _hedef_al(update, context)
    if not uid:
        await update.message.reply_text(
            "❌ <b>Kullanıcı bulunamadı!</b>\n\n"
            "💡 Mesaja yanıt ver → <code>/warn [sebep]</code>\n"
            "veya → <code>/warn @kullanici [sebep]</code>\n\n"
            "⚠️ <i>Sebep yazmak zorunlu değil! 3 uyarıda otomatik ban.</i>",
            parse_mode='HTML'
        )
        return
    ck = str(update.effective_chat.id)
    uk = str(uid)
    sebep_args = context.args[1:] if context.args and not update.message.reply_to_message else context.args
    sebep = html.escape(' '.join(sebep_args)) if sebep_args else "Sebep belirtilmedi"
    veri = _uyari_yukle()
    veri.setdefault(ck, {}).setdefault(uk, [])
    veri[ck][uk].append({'sebep': sebep, 'tarih': datetime.datetime.now().strftime('%d.%m.%Y %H:%M')})
    _uyari_kaydet(veri)
    sayi = len(veri[ck][uk])
    if sayi >= 3:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, uid)
            veri[ck][uk] = []
            _uyari_kaydet(veri)
            await update.message.reply_text(
                f"🔨 <b>3. UYARI — OTOMATIK BAN!</b>\n\n👤 Kullanıcı: {display}\n"
                f"📝 Son sebep: {sebep}\n⚠️ 3 uyarı dolunca sistem otomatik ban uyguladı.",
                parse_mode='HTML'
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ 3 uyarı doldu ama ban başarısız: <code>{html.escape(str(e))}</code>", parse_mode='HTML')
    else:
        await update.message.reply_text(
            f"⚠️ <b>UYARI VERİLDİ! ({sayi}/3)</b>\n\n👤 Kullanıcı: {display}\n📝 Sebep: {sebep}\n"
            f"{'⚠️ Bir daha uyarılırsa ban!' if sayi == 2 else ''}",
            parse_mode='HTML'
        )

async def uyarilar_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ('group', 'supergroup'):
        return
    if not await _admin_mi(update, context):
        await update.message.reply_text("❌ Bu komut sadece adminler içindir.")
        return
    uid, display = await _hedef_al(update, context)
    ck = str(update.effective_chat.id)
    veri = _uyari_yukle()
    if uid:
        uk = str(uid)
        uyarilar = veri.get(ck, {}).get(uk, [])
        if not uyarilar:
            await update.message.reply_text(f"✅ {display} için kayıtlı uyarı yok.", parse_mode='HTML')
        else:
            metin = f"⚠️ <b>Uyarı Listesi:</b> {display}\n\n"
            for i, u in enumerate(uyarilar, 1):
                metin += f"{i}. 📝 {u.get('sebep','?')} — {u.get('tarih','?')}\n"
            metin += f"\nToplam: {len(uyarilar)}/3"
            await update.message.reply_text(metin, parse_mode='HTML')
    else:
        grup_uyarilari = veri.get(ck, {})
        if not grup_uyarilari:
            await update.message.reply_text("✅ Bu grupta kayıtlı uyarı yok.")
            return
        metin = "⚠️ <b>Grup Uyarı Özeti:</b>\n\n"
        for uk2, liste in grup_uyarilari.items():
            if liste:
                metin += f"👤 ID <code>{uk2}</code>: {len(liste)} uyarı\n"
        await update.message.reply_text(metin, parse_mode='HTML')

async def temizle_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ('group', 'supergroup'):
        return
    if not await _admin_mi(update, context):
        await update.message.reply_text("❌ Bu komut sadece adminler içindir.")
        return
    try:
        n = int(context.args[0]) if context.args else 10
        n = max(1, min(n, 100))
    except (ValueError, IndexError):
        n = 10
    cmd_id = update.message.message_id
    # Sadece komutun ÖNÜNDEKI n mesajı sil, komut mesajını da dahil et
    # cmd_id+1'den YUKARI doğru HİÇ silme — kullanıcının yeni mesajlarına dokunma
    silinecekler = list(range(cmd_id, cmd_id - n - 1, -1))
    silindi = 0
    for mid in silinecekler:
        try:
            await context.bot.delete_message(update.effective_chat.id, mid)
            silindi += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    # Onay mesajı gönder — otomatik SİLME YOK, sabit kalıyor
    await update.effective_chat.send_message(
        f"🗑️ <b>{silindi} mesaj temizlendi.</b> ✅", parse_mode='HTML'
    )

# ─────────────────────────────────────────────────────────────
# 💬 SOHBET ARAÇLARI — QR Kod / URL Kısalt / Sahte Kimlik / Şans
# ─────────────────────────────────────────────────────────────

_SOHBET_TR_ISIMLER = [
    ("Giorgi","Beridze"),("Davit","Kvaratskhelia"),("Luka","Chikvanaia"),("Sandro","Mgeladze"),
    ("Irakli","Tabatadze"),("Levan","Kobiashvili"),("Tornike","Shengelia"),("Beka","Vekua"),
    ("Nika","Tsiklauri"),("Mikheil","Salukvadze"),("Zura","Daraselia"),("Shota","Arveladze"),
    ("Nino","Burjanadze"),("Mariam","Tsimakuridze"),("Ana","Dolidze"),("Ketevan","Maisuradze"),
    ("Tamar","Chikovanı"),("Natia","Gelashvili"),("Salome","Zurabishvili"),("Elene","Khoshtaria"),
]
_SOHBET_AZ_ISIMLER = [
    ("Əli","Həsənov"),("Rəşad","Məmmədov"),("Nicat","Əliyev"),("Tural","İsmayılov"),
    ("Kamran","Hüseynov"),("Elçin","Quliyev"),("Anar","Babayev"),("Müşfiq","Rəhimov"),
    ("Günay","Xəlilova"),("Sevinc","Məmmədzadə"),("Lalə","Əsgərova"),("Aytən","Nəsirov"),
]
_SOHBET_SEHIRLER_TR = ["Tiflis","Batum","Kutaisi","Rustavi","Zugdidi","Gori","Poti","Telavi","Akhaltsikhe","Ozurgeti"]
_SOHBET_SEHIRLER_AZ = ["Bakı","Gəncə","Sumqayıt","Mingəçevir","Naxçıvan","Lənkəran","Şəki","Şirvan"]
_SOHBET_MESLEKLER = [
    "Yazılım Geliştirici","Grafik Tasarımcı","Öğretmen","Mühendis","Doktor",
    "Muhasebeci","Pazarlama Uzmanı","Gazeteci","Mimar","Hemşire",
    "Eczacı","Avukat","Fotoğrafçı","Müzisyen","Girişimci",
]

def sahte_kimlik_uret(lang: str = 'tr') -> str:
    isimler = _SOHBET_AZ_ISIMLER if lang == 'az' else _SOHBET_TR_ISIMLER
    sehirler = _SOHBET_SEHIRLER_AZ if lang == 'az' else _SOHBET_SEHIRLER_TR
    ad, soyad = random.choice(isimler)
    sehir = random.choice(sehirler)
    yas = random.randint(18, 55)
    meslek = random.choice(_SOHBET_MESLEKLER)
    telefon = f"+9{random.choice(['0','4'])}{random.randint(100,999)}{random.randint(100,999)}{random.randint(10,99)}{random.randint(10,99)}"
    email_ad = f"{ad.lower().replace('ş','s').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ı','i').replace('ç','c').replace('ə','e').replace('ğ','g')}"
    email = f"{email_ad}{random.randint(10,99)}@{'gmail' if random.random()>0.5 else 'hotmail'}.com"
    return (
        f"🎭 <b>SAHTE KİMLİK</b>\n\n"
        f"👤 Ad Soyad: <b>{ad} {soyad}</b>\n"
        f"🎂 Yaş: <b>{yas}</b>\n"
        f"🏙️ Şehir: <b>{sehir}</b>\n"
        f"💼 Meslek: <b>{meslek}</b>\n"
        f"📞 Telefon: <code>{telefon}</code>\n"
        f"📧 E-posta: <code>{email}</code>\n\n"
        f"<i>⚠️ Bu kimlik tamamen sahte ve rastgele üretilmiştir!</i>"
    )

async def qr_url_gonder(bot, chat_id: int, metin: str, reply_markup=None) -> None:
    encoded = urllib.parse.quote(metin, safe='')
    url = f"https://api.qrserver.com/v1/create-qr-code/?data={encoded}&size=400x400&margin=10&format=png"
    try:
        r = http_requests.get(url, timeout=10)
        if r.status_code == 200:
            import io
            foto = io.BytesIO(r.content)
            foto.name = "qr.png"
            await bot.send_photo(
                chat_id=chat_id,
                photo=foto,
                caption=f"📱 <b>QR KOD</b>\n\n<code>{html.escape(metin[:100])}</code>",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        else:
            await bot.send_message(chat_id, "❌ QR kod oluşturulamadı.", reply_markup=reply_markup)
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Hata: {html.escape(str(e))}", reply_markup=reply_markup)

async def url_kisalt(url: str) -> str:
    try:
        encoded = urllib.parse.quote(url, safe='')
        r = http_requests.get(f"https://tinyurl.com/api-create.php?url={encoded}", timeout=8)
        if r.status_code == 200 and r.text.startswith('http'):
            return r.text.strip()
    except Exception:
        pass
    return url

# ══════════════════════════════════════════════════════════════
# 🔮 AKİNATÖR OYUN MOTORU  (akinator AsyncAkinator — repo: advnpzn/Akinator-Bot)
# ══════════════════════════════════════════════════════════════

_AKINATOR_IMG_YOL = "attached_assets/IMG_20260622_144754_1782125326168.png"

_AKI_PLAY_KLAVYE = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ Evet",             callback_data="aki_play_0"),
        InlineKeyboardButton("❌ Hayır",            callback_data="aki_play_1"),
        InlineKeyboardButton("🤷 Bilmiyorum",       callback_data="aki_play_2"),
    ],
    [
        InlineKeyboardButton("🟡 Muhtemelen",       callback_data="aki_play_3"),
        InlineKeyboardButton("🟠 Muhtemelen Değil", callback_data="aki_play_4"),
    ],
    [
        InlineKeyboardButton("⬅️ Geri",             callback_data="aki_play_5"),
        InlineKeyboardButton("🏳️ Bırak",            callback_data="aki_play_quit"),
    ],
])

_AKI_WIN_KLAVYE = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ Evet, bildin!",    callback_data="aki_win_y"),
        InlineKeyboardButton("❌ Yanıltın!",        callback_data="aki_win_n"),
    ]
])

# 0=Evet 1=Hayır 2=Bilmiyorum 3=Muhtemelen 4=Muhtemelen Değil
_AKI_CEVAP_STR = {
    "0": "yes",
    "1": "no",
    "2": "idk",
    "3": "probably",
    "4": "probably not",
}

_AKI_KARSILAMA = (
    "🔮 *AKİNATÖR'E HOŞ GELDİN!*\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "🧞 *Ben aklındaki karakteri tahmin edeceğim!*\n\n"
    "💡 Gerçek, hayali ya da herkesçe tanınan\n"
    "herhangi bir karakter düşünebilirsin.\n\n"
    "🎯 Sorularıma dürüstçe cevap ver,\n"
    "ben gerisini hallederim! 😏\n\n"
    "👇 Hazırsan *BAŞLA* butonuna bas!"
)


async def akinator_baslat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/akinator komutu — özel ve grup sohbetlerde çalışır."""
    aki_intro_klavye = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 BAŞLA!", callback_data="aki_baslat")],
    ])
    try:
        with open(_AKINATOR_IMG_YOL, "rb") as _f:
            await update.effective_message.reply_photo(
                photo=_f,
                caption=_AKI_KARSILAMA,
                reply_markup=aki_intro_klavye,
                parse_mode="Markdown",
            )
    except Exception:
        await update.effective_message.reply_text(
            _AKI_KARSILAMA,
            reply_markup=aki_intro_klavye,
            parse_mode="Markdown",
        )


async def _aki_play_baslat_callback(query, context):
    """BAŞLA butonuna basıldığında — AsyncAkinator ile oyun başlatır."""
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    context.user_data.pop(f"aki_{user_id}", None)
    context.user_data.pop(f"aki_msg_{user_id}", None)

    if not AKINATOR_YUKLU:
        await query.answer("❌ Akinator şu an kullanılamıyor!", show_alert=True)
        return

    try:
        await query.edit_message_caption(
            caption="⏳ *Akinator uyanıyor... Bağlanıyor!*",
            parse_mode="Markdown",
        )
    except Exception:
        pass

    try:
        aki = _AsyncAkinator()
        try:
            await aki.start_game(language="tr", child_mode=False)
        except Exception:
            aki = _AsyncAkinator()
            await aki.start_game(language="en", child_mode=False)

        context.user_data[f"aki_{user_id}"] = aki

        dolu = int((aki.progression or 0) / 10)
        bar  = "🟦" * dolu + "⬜" * (10 - dolu)
        soru_metni = (
            f"🔮 *AKİNATÖR* | Soru 1\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"❓ *{aki.question}*\n\n"
            f"📊 {bar} `0%`"
        )

        try:
            soru_msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=aki.akitude_url,
                caption=soru_metni,
                reply_markup=_AKI_PLAY_KLAVYE,
                parse_mode="Markdown",
            )
        except Exception:
            soru_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=soru_metni,
                reply_markup=_AKI_PLAY_KLAVYE,
                parse_mode="Markdown",
            )

        context.user_data[f"aki_msg_{user_id}"] = soru_msg.message_id

        try:
            await query.edit_message_caption(
                caption="🔮 *AKİNATÖR*\n\n🧞 _Oyun başladı! Aşağıdaki sorulara cevap ver._",
                parse_mode="Markdown",
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Akinator başlatma hatası: {e}")
        try:
            await query.edit_message_caption(
                caption=(
                    "❌ *Akinator bağlanamadı!*\n\n"
                    "Sunucu geçici olarak erişilemez.\n"
                    "Lütfen daha sonra tekrar dene."
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Tekrar Dene", callback_data="aki_baslat")],
                    [InlineKeyboardButton("⬅️ Geri",        callback_data="menu_fun")],
                ]),
            )
        except Exception:
            pass


async def _aki_raw_answer(aki, answer_id: int) -> bool:
    """Raw HTTP POST — library'nin bozuk __handler'ını bypass eder. True=kazandı."""
    url = f"https://{aki.language}.akinator.com/answer"
    data = {
        "step": aki.step,
        "progression": aki.progression,
        "sid": 1,
        "cm": "false",
        "answer": answer_id,
        "step_last_proposition": getattr(aki, "step_last_proposition", "") or "",
        "session": aki.session_id,
        "signature": aki.signature,
    }
    resp = await aki.session.post(url, data=data)
    resp.raise_for_status()
    j = resp.json()

    if j.get("completion") in ("KO - TIMEOUT", "KO"):
        raise RuntimeError("Session timed out")

    if "id_proposition" in j:
        aki.win = True
        aki.id_proposition   = j.get("id_proposition", "")
        aki.name_proposition  = j.get("name_proposition", "")
        aki.description_proposition = j.get("description_proposition", "")
        aki.photo            = j.get("photo", "")
        aki.pseudo           = j.get("pseudo", "")
        aki.progression      = float(j.get("progression", aki.progression))
        aki.step             = int(j.get("step", aki.step))
    else:
        aki.win        = False
        aki.step       = int(j.get("step", aki.step))
        aki.progression = float(j.get("progression", aki.progression))
        aki.question   = j.get("question", aki.question)
    return aki.win


async def _aki_raw_back(aki) -> None:
    """Raw HTTP POST cancel_answer — library'nin back() metodunu bypass eder."""
    if aki.step == 0:
        raise Exception("Daha geri gidemezsin")
    url = f"https://{aki.language}.akinator.com/cancel_answer"
    data = {
        "step": aki.step,
        "progression": aki.progression,
        "sid": 1,
        "cm": "false",
        "session": aki.session_id,
        "signature": aki.signature,
    }
    resp = await aki.session.post(url, data=data)
    resp.raise_for_status()
    j = resp.json()
    aki.win        = False
    aki.step       = int(j.get("step", aki.step))
    aki.progression = float(j.get("progression", aki.progression))
    aki.question   = j.get("question", aki.question)


async def _aki_cevap_callback(query, context):
    """aki_play_0/1/2/3/4/5/quit — Evet/Hayır/Geri/Bırak butonları."""
    user_id = query.from_user.id
    aki: _AsyncAkinator = context.user_data.get(f"aki_{user_id}")

    if not aki:
        await query.answer("❌ Aktif oyun yok! /akinator ile başlat.", show_alert=True)
        return

    await query.answer()
    a        = query.data.split("_")[-1]   # 0/1/2/3/4/5/quit
    chat_id  = query.message.chat_id
    msg_id   = query.message.message_id

    if a == "quit":
        context.user_data.pop(f"aki_{user_id}", None)
        context.user_data.pop(f"aki_msg_{user_id}", None)
        bitti = "🏳️ *Oyun sona erdirildi.*\n\nYeni oyun için /akinator yaz."
        try:
            await query.edit_message_caption(caption=bitti, parse_mode="Markdown", reply_markup=None)
        except Exception:
            try:
                await query.edit_message_text(bitti, parse_mode="Markdown", reply_markup=None)
            except Exception:
                pass
        return

    try:
        if a == "5":
            try:
                await _aki_raw_back(aki)
            except Exception:
                await query.answer("⚠️ Daha geri gidemezsin!", show_alert=True)
                return
        else:
            # 0=Evet 1=Hayır 2=Bilmiyorum 3=Muhtemelen 4=Muhtemelen Değil
            await _aki_raw_answer(aki, int(a))

        if aki.win:
            dolu = int((aki.progression or 100) / 10)
            bar  = "🟦" * dolu + "⬜" * (10 - dolu)
            isim = aki.name_proposition or "???"
            acik = (aki.description_proposition or "")[:180]
            tahmin_metni = (
                f"🧞 *REİS, BULDUM!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎯 *{isim}*\n"
                f"📝 _{acik}_\n\n"
                f"📊 {bar} `{aki.progression:.0f}%`\n\n"
                f"🔮 _Doğru tahmin ettim mi?_"
            )
            foto = aki.photo
            if foto:
                try:
                    await context.bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=msg_id,
                        media=InputMediaPhoto(
                            media=foto,
                            caption=tahmin_metni,
                            parse_mode="Markdown",
                        ),
                        reply_markup=_AKI_WIN_KLAVYE,
                    )
                    return
                except Exception:
                    pass
            try:
                await context.bot.edit_message_caption(
                    chat_id=chat_id, message_id=msg_id,
                    caption=tahmin_metni, reply_markup=_AKI_WIN_KLAVYE, parse_mode="Markdown",
                )
            except Exception:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id, message_id=msg_id,
                        text=tahmin_metni, reply_markup=_AKI_WIN_KLAVYE, parse_mode="Markdown",
                    )
                except Exception:
                    await context.bot.send_message(
                        chat_id=chat_id, text=tahmin_metni,
                        reply_markup=_AKI_WIN_KLAVYE, parse_mode="Markdown",
                    )
        else:
            dolu = int((aki.progression or 0) / 10)
            bar  = "🟦" * dolu + "⬜" * (10 - dolu)
            soru_metni = (
                f"🔮 *AKİNATÖR* | Soru {aki.step + 1}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"❓ *{aki.question}*\n\n"
                f"📊 {bar} `{aki.progression:.0f}%`"
            )
            akitude = getattr(aki, "akitude_url", None) or f"https://{aki.language}.akinator.com/assets/img/akitudes_670x1096/defi.png"
            try:
                await context.bot.edit_message_media(
                    chat_id=chat_id, message_id=msg_id,
                    media=InputMediaPhoto(media=akitude, caption=soru_metni, parse_mode="Markdown"),
                    reply_markup=_AKI_PLAY_KLAVYE,
                )
            except Exception:
                try:
                    await context.bot.edit_message_caption(
                        chat_id=chat_id, message_id=msg_id,
                        caption=soru_metni, reply_markup=_AKI_PLAY_KLAVYE, parse_mode="Markdown",
                    )
                except Exception:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=chat_id, message_id=msg_id,
                            text=soru_metni, reply_markup=_AKI_PLAY_KLAVYE, parse_mode="Markdown",
                        )
                    except Exception:
                        pass

    except Exception as e:
        err = str(e).lower()
        logger.error(f"Akinator cevap hatası: {e}")
        context.user_data.pop(f"aki_{user_id}", None)
        context.user_data.pop(f"aki_msg_{user_id}", None)
        if "timed out" in err or "timeout" in err:
            msg = "⌛ *Oturum zaman aşımına uğradı!*\n\n/akinator ile yeni oyun başlat."
        else:
            msg = "❌ *Bağlantı hatası!*\n\n/akinator ile yeni oyun başlat."
        try:
            await context.bot.edit_message_caption(
                chat_id=chat_id, message_id=msg_id,
                caption=msg, parse_mode="Markdown", reply_markup=None,
            )
        except Exception:
            pass


async def _aki_win_callback(query, context, dogru: bool):
    """aki_win_y / aki_win_n — Doğru/Yanlış tahmin sonucu."""
    user_id = query.from_user.id
    context.user_data.pop(f"aki_{user_id}", None)
    context.user_data.pop(f"aki_msg_{user_id}", None)

    if dogru:
        await query.answer("🎉 Tekrar kazandım! 😎", show_alert=True)
        ek = "\n\n✅ *Doğru tahmin! Akinator kazandı!* 🏆\n/akinator ile yeni oyun başlat."
    else:
        await query.answer("😅 Bu sefer yanıldım! Kazandın!", show_alert=True)
        ek = "\n\n❌ *Yanıldım! Sen kazandın!* 🎊\n/akinator ile yeni oyun başlat."

    try:
        mevcut = query.message.caption or query.message.text or ""
        if query.message.caption is not None:
            await query.edit_message_caption(
                caption=mevcut + ek,
                parse_mode="Markdown",
                reply_markup=None,
            )
        else:
            await query.edit_message_text(
                mevcut + ek,
                parse_mode="Markdown",
                reply_markup=None,
            )
    except Exception:
        pass


# ══════════════════════════════════════════════════════

def main():
    uyanik_tut()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("stats", stats_komut_tetikleyici, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("meid", meid_komutu))
    application.add_handler(CommandHandler("ip", ip_basit_komutu))
    application.add_handler(CommandHandler("ip_analiz", ip_komutu))
    application.add_handler(CommandHandler("sasi", sasi_komutu))
    application.add_handler(CommandHandler("hatirlat", hatirlat_komutu))
    # ⚡ PRO ARAÇLAR — Hızlı komutlar
    application.add_handler(CommandHandler("hesap", hesap_komutu))
    application.add_handler(CommandHandler("hash", hash_komutu))
    application.add_handler(CommandHandler("hava", hava_komutu))
    application.add_handler(CommandHandler("kur", kur_komutu))
    application.add_handler(CommandHandler("saat", saat_komutu))
    application.add_handler(CommandHandler("b64", b64_komutu))
    application.add_handler(CommandHandler("id", id_komutu))
    application.add_handler(CommandHandler("sifirla", ai_sifirla_komutu))
    # ⚡ AZRxGUARD 2.0 — Yeni Komutlar
    application.add_handler(CommandHandler("ping", ping_komutu))
    application.add_handler(CommandHandler("renk", renk_komutu))
    application.add_handler(CommandHandler("metin", metin_komutu))
    application.add_handler(CommandHandler("rastgele", rastgele_komutu))
    application.add_handler(CommandHandler("sifrele", sifrele_komutu))
    application.add_handler(CommandHandler("bmi", bmi_komutu))
    application.add_handler(CommandHandler("yuzde", yuzde_komutu))
    application.add_handler(CommandHandler("sifre", sifre_komutu))
    application.add_handler(CommandHandler("kimlik", kimlik_komutu))
    application.add_handler(CommandHandler("kisalt", kisalt_komutu))
    application.add_handler(CommandHandler("wiki", wiki_komutu))
    application.add_handler(CommandHandler("atag", atag_komutu, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("istatistik", istatistik_komutu, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("akinator", akinator_baslat_cmd))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, gelen_mesajlari_yonet))
    # 🛡️ GRUP YÖNETİM KOMUTLARI
    application.add_handler(CommandHandler("ban", ban_komutu, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("unban", unban_komutu, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("kick", kick_komutu, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("mute", mute_komutu, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("unmute", unmute_komutu, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("warn", warn_komutu, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("uyarilar", uyarilar_komutu, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("temizle", temizle_komutu, filters=filters.ChatType.GROUPS))
    application.add_handler(MessageHandler((filters.VIDEO | filters.Document.VIDEO | filters.Document.MimeType("video/mp4") | filters.Document.MimeType("video/quicktime") | filters.Document.MimeType("video/x-msvideo")) & filters.ChatType.PRIVATE, medya_mesaj_yonet))
    application.add_handler(MessageHandler((filters.PHOTO | filters.VOICE | filters.AUDIO | filters.Document.ALL | filters.Sticker.ALL | filters.ANIMATION | filters.VIDEO_NOTE) & filters.ChatType.PRIVATE, diger_medya_log_yonet))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, kanala_veya_gruba_yeni_uye_katildi))
    application.add_handler(MessageHandler((filters.ChatType.GROUPS | filters.ChatType.CHANNEL) & filters.ALL, grup_ve_kanal_mesaj_yonet))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, filigran_ekle), group=-1)

    # --- ZAMANLI GÖREVLER ---
    jq = application.job_queue

    # 00:00 — Günlük mesaj istatistiği (Gürcistan saati UTC+4)
    _GE_SAAT = datetime.timezone(datetime.timedelta(hours=4))
    jq.run_daily(
        callback=gunluk_istatistik_job,
        time=datetime.time(hour=0, minute=0, second=0, tzinfo=_GE_SAAT),
        name="gunluk_istatistik"
    )

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

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error("Güncelleme sırasında hata oluştu:", exc_info=context.error)
        if isinstance(context.error, Exception):
            err_str = str(context.error)
            if 'Message is not modified' in err_str or 'Query is too old' in err_str:
                return  # Sessizce geç
            if 'Forbidden: bot was blocked' in err_str or 'Chat not found' in err_str:
                return  # Sessizce geç
        try:
            if update and hasattr(update, 'effective_message') and update.effective_message:
                await update.effective_message.reply_text("⚠️ Bir hata oluştu. Lütfen tekrar deneyin.")
        except Exception:
            pass

    application.add_error_handler(error_handler)

    # ── Bot başladığında gece modu durumunu düzelt ─────────────
    async def baslangic_gece_modu_kontrol(app):
        """Bot restart olduğunda grup kilidi kalmışsa anında açar."""
        if not gece_modu_aktif_mi():
            try:
                await app.bot.set_chat_permissions(
                    chat_id=ZAMANLI_KANAL_ID,
                    permissions=ChatPermissions(
                        can_send_messages=True, can_send_audios=True,
                        can_send_documents=True, can_send_photos=True,
                        can_send_videos=True, can_send_video_notes=True,
                        can_send_voice_notes=True, can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                        can_invite_users=True
                    )
                )
                logger.info("Başlangıç: Gece modu değil — grup izinleri açıldı.")
            except Exception as e:
                logger.warning(f"Başlangıç gece modu kontrol hatası: {e}")
        else:
            logger.info("Başlangıç: Gece modu aktif — grup kilitli kalıyor.")

    async def baslangic_komut_listesi(app):
        await baslangic_gece_modu_kontrol(app)
        # Grup komutları görünür yap
        try:
            grup_komutlari = [
                BotCommand("atag", "Herkesi etiketle — /atag mesajın"),
                BotCommand("ban", "Kullanıcı/bot ban — /ban @user"),
                BotCommand("unban", "Ban kaldır — /unban @user"),
                BotCommand("kick", "Gruptan at — /kick @user"),
                BotCommand("mute", "Sustur — /mute @user 30d/2s/1g"),
                BotCommand("unmute", "Sesi aç — /unmute @user"),
                BotCommand("warn", "Uyarı ver — /warn @user sebep"),
                BotCommand("uyarilar", "Uyarıları gör — /uyarilar @user"),
                BotCommand("temizle", "Mesaj sil — /temizle 20"),
            ]
            await app.bot.set_my_commands(grup_komutlari, scope=BotCommandScopeAllGroupChats())
            logger.info("Grup komut listesi ayarlandı.")
        except Exception as e:
            logger.warning(f"Grup komut listesi ayarlanamadı: {e}")

    application.post_init = baslangic_komut_listesi

    logger.info("AZRxGUARD Sistemi Sorunsuz Başlatıldı...")

    # ── Çift Başlı Asenkron Motor ─────────────────────────────────────────────
    # Telegram ve Discord botları birbirini kilitlemeden aynı anda çalışır.
    # Birinin çökmesi diğerini durdurmaz.
    async def _telegram_calistir():
        """PTB'nin async API'siyle polling başlatır ve sonsuza dek çalışır."""
        try:
            async with application:
                # Önceki oturumu / webhook'u temizle (Conflict önleme)
                try:
                    await application.bot.delete_webhook(drop_pending_updates=True)
                    await application.bot.get_updates(offset=-1, timeout=0)
                except Exception:
                    pass
                await asyncio.sleep(2)   # eski bağlantının Telegram tarafında kapanması için
                await application.start()
                await application.updater.start_polling(
                    allowed_updates=["message", "callback_query", "channel_post", "chat_member"],
                    drop_pending_updates=True
                )
                logger.info("Telegram polling aktif.")
                # Sonsuz bekleme — process SIGTERM alana kadar çalışır
                await asyncio.get_event_loop().create_future()
        except asyncio.CancelledError:
            logger.info("Telegram botu durduruldu.")
        except Exception as e:
            logger.error(f"Telegram botu beklenmedik hata: {e}", exc_info=True)

    async def _discord_calistir():
        """Discord botunu güvenli şekilde başlatır; çökerse Telegram etkilenmez."""
        try:
            from discord_bot import run_discord
            await run_discord()
        except asyncio.CancelledError:
            logger.info("Discord botu durduruldu.")
        except Exception as e:
            logger.error(f"Discord task hatası: {e}", exc_info=True)

    async def _cift_basli_motor():
        tg_task = asyncio.create_task(_telegram_calistir(), name="telegram")
        dc_task = asyncio.create_task(_discord_calistir(), name="discord")
        await asyncio.gather(tg_task, dc_task, return_exceptions=True)

    asyncio.run(_cift_basli_motor())


if __name__ == '__main__':
    main()
