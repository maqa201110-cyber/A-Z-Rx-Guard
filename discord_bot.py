"""
AZRxGUARD — Discord Şubesi
Telegram botundaki APK/OBB/Config sistemiyle aynı apk_dosyalar.json'u okur.
Telegram handler'larına hiç dokunmaz; sadece Discord'a paralel hizmet verir.
"""

import asyncio
import json
import logging
import os

import discord
from discord import app_commands

logger = logging.getLogger(__name__)

# ── Paylaşımlı veri dosyası (Telegram ile aynı) ──────────────────────────────
_APK_DOSYALAR_YOL = 'apk_dosyalar.json'


def apk_dosyalari_yukle() -> dict:
    try:
        with open(_APK_DOSYALAR_YOL, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ── Renk sabitleri ────────────────────────────────────────────────────────────
RENK_ANA   = 0x5865F2   # Discord blueviolet
RENK_YESIL = 0x57F287
RENK_KIRMIZI = 0xED4245


# ══════════════════════════════════════════════════════════════════════════════
# View: Tek dosya detay ekranı (Geri butonu dahil)
# ══════════════════════════════════════════════════════════════════════════════
class APKDosyaView(discord.ui.View):
    def __init__(self, uid: str, bilgi: dict, tg_username: str):
        super().__init__(timeout=300)
        self.uid = uid
        self.bilgi = bilgi
        tg_link = f"https://t.me/{tg_username}?start=apk_{uid}"
        self.add_item(discord.ui.Button(
            label="📥 Telegram'dan İndir",
            url=tg_link,
            style=discord.ButtonStyle.link
        ))

    @discord.ui.button(label="⬅️ Listeye Dön", style=discord.ButtonStyle.secondary, row=1)
    async def geri_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        dosyalar = apk_dosyalari_yukle()
        embed, view = apk_liste_embed_view(dosyalar)
        await interaction.response.edit_message(embed=embed, view=view)


# ══════════════════════════════════════════════════════════════════════════════
# View: Dosya listesi (her dosya için bir buton, max 25)
# ══════════════════════════════════════════════════════════════════════════════
class APKListeView(discord.ui.View):
    def __init__(self, dosyalar: dict):
        super().__init__(timeout=300)
        # Discord bir View'da maksimum 25 bileşen destekler
        for uid, bilgi in list(dosyalar.items())[:24]:
            btn = APKSecimButonu(uid=uid, bilgi=bilgi)
            self.add_item(btn)

    @discord.ui.button(label="🔄 Yenile", style=discord.ButtonStyle.secondary, row=4)
    async def yenile_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        dosyalar = apk_dosyalari_yukle()
        embed, view = apk_liste_embed_view(dosyalar)
        await interaction.response.edit_message(embed=embed, view=view)


class APKSecimButonu(discord.ui.Button):
    def __init__(self, uid: str, bilgi: dict):
        isim = bilgi.get('isim', 'Dosya')[:75]
        super().__init__(
            label=f"📦 {isim}",
            style=discord.ButtonStyle.primary,
            custom_id=f"apk_sec_{uid}"
        )
        self.uid = uid
        self.bilgi = bilgi

    async def callback(self, interaction: discord.Interaction):
        bilgi = self.bilgi
        tg_botname = os.environ.get('TG_BOT_USERNAME', 'AzrXguard_bot')
        embed = discord.Embed(
            title=f"📦 {bilgi.get('isim', '?')}",
            description=bilgi.get('aciklama', '_Açıklama yok_'),
            color=RENK_YESIL
        )
        embed.add_field(name="📅 Yükleme Tarihi", value=bilgi.get('tarih', '—'), inline=True)
        embed.add_field(name="🔗 Kaynak", value="Telegram Kanalı", inline=True)
        embed.set_footer(text="Dosyayı indirmek için aşağıdaki Telegram butonuna bas.")
        view = APKDosyaView(uid=self.uid, bilgi=bilgi, tg_username=tg_botname)
        await interaction.response.edit_message(embed=embed, view=view)


def apk_liste_embed_view(dosyalar: dict):
    if not dosyalar:
        embed = discord.Embed(
            title="📦 APK-OBB-CONFİG",
            description="📭 Henüz hiç dosya yüklenmemiş.\nTelegram kanalından `/yükle` komutuyla dosya ekleyebilirsin.",
            color=RENK_KIRMIZI
        )
        return embed, discord.ui.View()

    embed = discord.Embed(
        title="📦 APK-OBB-CONFİG",
        description=(
            f"📁 **{len(dosyalar)} dosya mevcut.**\n"
            "İndirmek istediğin dosyayı seçmek için bir butona bas:"
        ),
        color=RENK_ANA
    )
    embed.set_footer(text="Dosyalar Telegram kanalından yönetilir • AZRxGUARD")
    view = APKListeView(dosyalar)
    return embed, view


# ══════════════════════════════════════════════════════════════════════════════
# Discord İstemcisi + Slash Komutları
# ══════════════════════════════════════════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True

discord_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(discord_client)


@discord_client.event
async def on_ready():
    await tree.sync()
    logger.info(f"Discord botu hazır → {discord_client.user} (ID: {discord_client.user.id})")


# ── /apk — Dosya listesi paneli ───────────────────────────────────────────────
@tree.command(name="apk", description="APK-OBB-CONFİG dosya listesini göster")
async def apk_komutu(interaction: discord.Interaction):
    dosyalar = apk_dosyalari_yukle()
    embed, view = apk_liste_embed_view(dosyalar)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ── /bilgi — Bot hakkında ─────────────────────────────────────────────────────
@tree.command(name="bilgi", description="AZRxGUARD Discord botu hakkında")
async def bilgi_komutu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ AZRxGUARD — Discord Şubesi",
        description=(
            "Bu bot, Telegram tabanlı **AZRxGUARD** sisteminin Discord uzantısıdır.\n\n"
            "**Paylaşımlı Özellikler:**\n"
            "• 📦 APK / OBB / Config dosya paneli\n"
            "• 🔄 Telegram'a yüklenen dosyalar anında burada da görünür\n\n"
            "**Komutlar:**\n"
            "`/apk` — Dosya listesi ve indirme paneli\n"
            "`/bilgi` — Bu mesaj"
        ),
        color=RENK_ANA
    )
    embed.set_footer(text="𝑴𝑨𝑫𝑬 𝑩𝒀 ➣ M̶A̶Q̶A̶💎 | 𝑶𝑾𝑵𝑬𝑹 • azrXmaqa")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Ana coroutine (main'den çağrılır) ─────────────────────────────────────────
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
