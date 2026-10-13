"""Beginner-friendly, offline content for AZRxGUARD's Koruma Merkezi."""

ACCOUNT_CHECKLISTS = {
    "tg": {
        "name": "Telegram",
        "items": (
            (
                "İki adımlı doğrulamayı aç",
                "Ayarlar → Gizlilik ve Güvenlik → İki Adımlı Doğrulama bölümünü kontrol et.",
            ),
            (
                "Açık oturumları gözden geçir",
                "Ayarlar → Cihazlar bölümünde tanımadığın oturumları kapat.",
            ),
            (
                "Telefon numarası gizliliğini ayarla",
                "Gizlilik ve Güvenlik bölümünde numaranı kimlerin görebileceğini seç.",
            ),
            (
                "Uygulama kilidi kullan",
                "Telefonunun ekran kilidini ve Telegram uygulama kilidini etkinleştir.",
            ),
        ),
    },
    "instagram": {
        "name": "Instagram",
        "items": (
            (
                "İki faktörlü doğrulamayı aç",
                "Hesaplar Merkezi → Şifre ve güvenlik bölümünden iki faktörlü doğrulamayı etkinleştir.",
            ),
            (
                "Giriş hareketlerini kontrol et",
                "Tanımadığın cihaz veya konum görürsen oturumu kapat ve parolanı değiştir.",
            ),
            (
                "Kurtarma bilgilerini güncel tut",
                "E-posta ve telefon bilgilerinin sana ait ve erişilebilir olduğunu kontrol et.",
            ),
            (
                "Bağlı uygulamaları gözden geçir",
                "Tanımadığın uygulamaların hesaba erişimini kaldır.",
            ),
        ),
    },
    "gmail": {
        "name": "Gmail / Google",
        "items": (
            (
                "İki Adımlı Doğrulamayı aç",
                "Google Hesabı → Güvenlik bölümünden iki adımlı doğrulamayı etkinleştir.",
            ),
            (
                "Cihazlarını ve son etkinlikleri incele",
                "Tanımadığın cihazlardan çıkış yap ve şüpheli etkinliği Google'a bildir.",
            ),
            (
                "Kurtarma bilgilerini güncelle",
                "Kurtarma e-postası ve telefonunun güncel olduğundan emin ol.",
            ),
            (
                "Üçüncü taraf erişimlerini kontrol et",
                "Tanımadığın uygulama ve hizmetlerin Google hesabına erişimini kaldır.",
            ),
        ),
    },
}

EMERGENCY_GUIDES = {
    "account_hacked": {
        "title": "Hesabıma başkası girdi",
        "steps": (
            "Güvendiğin bir cihazdan uygulamanın veya servisin resmî uygulamasını aç.",
            "Hesaba erişebiliyorsan parolanı değiştir ve tanımadığın oturumları kapat.",
            "E-posta hesabını da güvene al; aynı parolayı kullandığın yerlerde farklı parola belirle.",
            "İki adımlı doğrulamayı aç ve kurtarma bilgilerini kontrol et.",
            "Erişimin yoksa yalnızca servisin resmî hesap kurtarma sayfasını kullan.",
            "Destek olduğunu söyleyip parola veya giriş kodu isteyen kişilere güvenme.",
        ),
    },
    "suspicious_login": {
        "title": "Şüpheli giriş bildirimi aldım",
        "steps": (
            "Bildirimin içindeki linke basma; uygulamayı kendin aç.",
            "Güvenlik veya cihazlar bölümünden girişin sana ait olup olmadığını kontrol et.",
            "Sana ait değilse o oturumu kapat ve parolanı resmî uygulamadan değiştir.",
            "İki adımlı doğrulamayı etkinleştir ve kurtarma bilgilerini gözden geçir.",
            "Giriş kodunu veya doğrulama kodunu kimseyle paylaşma.",
        ),
    },
    "shared_secret": {
        "title": "Linke girdim veya kodumu paylaştım",
        "steps": (
            "Şüpheli sayfayı kapat; tekrar açma ve oraya yeni bilgi girme.",
            "Hesaba hâlâ erişebiliyorsan resmî uygulamadan parolanı hemen değiştir.",
            "Tanımadığın oturumları kapat, iki adımlı doğrulamayı aç ve kurtarma bilgilerini kontrol et.",
            "Aynı parolayı başka yerde kullandıysan oralarda da değiştir.",
            "Banka veya kart bilgisi verdiysen bankanı kartının arkasındaki resmî numaradan ara.",
            "Sana gelen giriş kodlarını kimseye iletme; destek ekibi de bu kodu istememelidir.",
        ),
    },
    "lost_device": {
        "title": "Telefonum kayboldu",
        "steps": (
            "Başka bir cihazdan telefonun resmî bulma hizmetini açıp kilitle veya konumunu kontrol et.",
            "Operatörünle resmî kanaldan iletişime geçip SIM kartını geçici olarak kapattır.",
            "E-posta ve mesajlaşma hesaplarındaki tanımadığın oturumları kapat.",
            "Cihaz ekran kilidini veya hesap parolalarını bilen biri olabileceğini düşünüyorsan değiştir.",
            "Cihazı geri getirme vaadiyle senden para veya doğrulama kodu isteyenlere bilgi verme.",
        ),
    },
}

SCAM_QUIZ = (
    {
        "question": "Bir mesaj “Hesabın kapanacak, giriş kodunu hemen gönder” diyor. Ne yaparsın?",
        "options": (
            "Kodu mesajla gönderirim.",
            "Kodu paylaşmam; uygulamayı kendim açıp kontrol ederim.",
            "Mesajı arkadaşlarıma da iletirim.",
        ),
        "answer": 1,
        "explanation": "Giriş kodunu kimseyle paylaşma. Hesap durumunu yalnızca resmî uygulamayı kendin açarak kontrol et.",
    },
    {
        "question": "Beklemediğin bir kargo mesajı küçük bir ücret için kart bilgisi isteyen link gönderiyor. Ne yaparsın?",
        "options": (
            "Linkte kart bilgilerimi girerim.",
            "Mesajdaki numarayı ararım.",
            "Resmî uygulama veya siteden kendim kontrol ederim.",
        ),
        "answer": 2,
        "explanation": "Beklenmedik ödeme linklerine güvenme. Adresi kendin yazarak resmî hizmetten kontrol et.",
    },
    {
        "question": "Arkadaşının hesabından acil para isteyen bir mesaj geldi. En güvenli adım nedir?",
        "options": (
            "Başka bildiğim yoldan arkadaşımı arayıp doğrularım.",
            "Mesaj acele ettirdiği için hemen gönderirim.",
            "Ondan giriş kodunu isterim.",
        ),
        "answer": 0,
        "explanation": "Ele geçirilmiş hesaplardan para istenebilir. Para göndermeden önce başka bir iletişim yoluyla doğrula.",
    },
    {
        "question": "Bir giriş sayfası, hesabını korumak için parolanı ve doğrulama kodunu istiyor. Ne yaparsın?",
        "options": (
            "Sayfa düzgün görünüyorsa bilgileri girerim.",
            "Sayfayı kapatır, servisin resmî uygulamasını kendim açarım.",
            "Kodu başka bir kişiye kontrol etmesi için gönderirim.",
        ),
        "answer": 1,
        "explanation": "Sahte sayfalar gerçek gibi görünebilir. Parolanı ve kodunu yalnızca resmî uygulama veya doğru adres olduğundan emin olduğun sayfada kullan.",
    },
    {
        "question": "Bir mesajdaki linki açtın ve parolanı girdin. İlk ne yapmalısın?",
        "options": (
            "Aynı sayfadan tekrar giriş yaparım.",
            "Bir süre beklerim.",
            "Resmî uygulamadan parolayı değiştiririm.",
        ),
        "answer": 2,
        "explanation": "Parolanı hemen resmî uygulama veya siteden değiştir, tanımadığın oturumları kapat ve aynı parolayı başka yerde kullandıysan onları da güncelle.",
    },
)


def checklist_report(platform: str, completed_indices) -> str:
    checklist = ACCOUNT_CHECKLISTS[platform]
    items = checklist["items"]
    completed = {
        index
        for index in completed_indices
        if isinstance(index, int) and 0 <= index < len(items)
    }
    lines = [
        f"🛡️ {checklist['name'].upper()} — HESAP KONTROLÜ",
        "",
        "Bu liste kendi kontrolün içindir. Bot hesap ayarlarını otomatik göremez.",
        "Bir maddeye dokunarak durumunu işaretle veya işaretini kaldır.",
        "",
    ]
    for index, (title, details) in enumerate(items):
        status = "✅ Kontrol ettim" if index in completed else "⬜ Henüz kontrol etmedim"
        lines.extend([f"{index + 1}. {title} — {status}", f"   {details}"])
    lines.extend([
        "",
        f"İlerleme: {len(completed)}/{len(items)} madde işaretlendi.",
        "Ayar menülerinin adı uygulama sürümüne göre biraz değişebilir.",
        "Şifreni veya doğrulama kodunu buraya yazma.",
    ])
    return "\n".join(lines)


def emergency_report(guide_id: str) -> str:
    guide = EMERGENCY_GUIDES[guide_id]
    lines = [f"🆘 {guide['title'].upper()}", ""]
    lines.extend(f"{index}. {step}" for index, step in enumerate(guide["steps"], start=1))
    lines.extend([
        "",
        "Yalnızca resmî uygulama ve destek kanallarını kullan. Parolanı veya doğrulama kodunu kimseye verme.",
    ])
    return "\n".join(lines)
