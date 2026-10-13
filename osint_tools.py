"""Passive, public-source OSINT lookups for AZRxGUARD."""

from __future__ import annotations

import ipaddress
import json
import html
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit

import requests


_USER_AGENT = "AZRxGUARD-OSINT/3.0"
_REQUEST_TIMEOUT = (3.05, 8)
_MAX_RESPONSE_BYTES = 500_000
_CACHE_TTL_SECONDS = 300
_CACHE: dict[str, tuple[float, str]] = {}
_CACHE_LOCK = threading.Lock()
_URLSCAN_LOCK = threading.Lock()
_URLSCAN_LAST_REQUEST = 0.0
_URLSCAN_MIN_INTERVAL = 3.0
_WIKIPEDIA_LOCK = threading.Lock()
_WIKIPEDIA_LAST_REQUEST = 0.0
_WIKIPEDIA_MIN_INTERVAL = 1.0
_LOCAL_SUFFIXES = (".localhost", ".local", ".test", ".invalid", ".example", ".internal", ".onion")


class OsintInputError(ValueError):
    """Input is not a valid public domain, URL, or IP address."""


class _SourceError(RuntimeError):
    """A public data source did not return usable data."""


def _json_get(url: str, params: dict | None = None, accept: str = "application/json"):
    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": _USER_AGENT, "Accept": accept},
        timeout=_REQUEST_TIMEOUT,
        stream=True,
    )
    try:
        if response.status_code >= 400:
            raise _SourceError(f"HTTP {response.status_code}")
        declared_size = response.headers.get("Content-Length")
        if declared_size and int(declared_size) > _MAX_RESPONSE_BYTES:
            raise _SourceError("Yanıt boyutu sınırı aşıldı")
        chunks = []
        size = 0
        for chunk in response.iter_content(chunk_size=16_384):
            if not chunk:
                continue
            size += len(chunk)
            if size > _MAX_RESPONSE_BYTES:
                raise _SourceError("Yanıt boyutu sınırı aşıldı")
            chunks.append(chunk)
        try:
            return json.loads(b"".join(chunks).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _SourceError("Kaynak geçerli JSON döndürmedi") from exc
    finally:
        response.close()


def _normalize_host(raw: str, *, allow_ip: bool = False) -> str:
    value = (raw or "").strip()
    if not value or len(value) > 2048 or any(ord(char) < 32 for char in value):
        raise OsintInputError("Geçerli bir domain veya URL yaz.")

    candidate = value if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value) else f"https://{value}"
    try:
        parsed = urlsplit(candidate)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            raise OsintInputError("Yalnızca http:// veya https:// adresi ya da domain kabul edilir.")
        if parsed.username or parsed.password:
            raise OsintInputError("Kullanıcı adı veya parola içeren linkler kabul edilmez.")
        if parsed.port not in (None, 80, 443):
            raise OsintInputError("Özel port numaraları kabul edilmez.")
        host = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, OsintInputError):
            raise
        raise OsintInputError("Domain veya URL biçimi geçersiz.") from exc

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        if not allow_ip:
            raise OsintInputError("Bu bir IP adresi. IP Araştır seçeneğini kullan.")
        if not address.is_global:
            raise OsintInputError("Yalnızca herkese açık IP adresleri kabul edilir.")
        return str(address)

    if (
        len(host) > 253
        or "." not in host
        or host == "localhost"
        or host.endswith(_LOCAL_SUFFIXES)
    ):
        raise OsintInputError("Yalnızca herkese açık domainler kabul edilir.")
    labels = host.split(".")
    if any(
        not label
        or len(label) > 63
        or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
        for label in labels
    ):
        raise OsintInputError("Domain biçimi geçersiz.")
    if len(labels[-1]) < 2:
        raise OsintInputError("Domain uzantısı geçersiz.")
    return host


def normalize_domain(raw: str) -> str:
    """Return a public domain hostname; never accepts IP literals or local names."""
    return _normalize_host(raw, allow_ip=False)


def normalize_public_ip(raw: str) -> str:
    value = (raw or "").strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise OsintInputError("Geçerli bir IPv4 veya IPv6 adresi yaz.") from exc
    if not address.is_global:
        raise OsintInputError("Yalnızca herkese açık IP adresleri kabul edilir.")
    return str(address)


def normalize_gmail(raw: str) -> str:
    value = (raw or "").strip()
    if not value or len(value) > 254 or any(char.isspace() or ord(char) < 32 for char in value):
        raise OsintInputError("Gmail adresini boşluksuz biçimde yaz.")
    if value.count("@") != 1:
        raise OsintInputError("E-posta biçimi geçersiz. Örnek: adın@gmail.com")
    local, domain = value.rsplit("@", 1)
    domain = domain.lower()
    if domain not in {"gmail.com", "googlemail.com"}:
        raise OsintInputError("Yalnızca @gmail.com veya @googlemail.com adresleri kabul edilir.")
    if (
        not local
        or len(local) > 64
        or not re.fullmatch(r"[A-Za-z0-9.+]+", local)
        or local.startswith(".")
        or local.endswith(".")
        or ".." in local
    ):
        raise OsintInputError("Gmail adresinin kullanıcı adı bölümü geçersiz görünüyor.")
    return domain


def normalize_name_query(raw: str) -> str:
    value = " ".join((raw or "").strip().split())
    if (
        len(value) < 2
        or len(value) > 80
        or any(ord(char) < 32 for char in value)
        or not any(char.isalpha() for char in value)
        or any(not (char.isalnum() or char in " .,'’&()-") for char in value)
    ):
        raise OsintInputError("2–80 karakterlik bir kişi, marka veya şirket adı yaz.")
    return value


def _safe_source(fn, *args, **kwargs) -> dict:
    try:
        return {"ok": True, "data": fn(*args, **kwargs)}
    except _SourceError as exc:
        return {"ok": False, "error": str(exc)}
    except requests.Timeout:
        return {"ok": False, "error": "zaman aşımı"}
    except requests.RequestException:
        return {"ok": False, "error": "bağlantı kurulamadı"}
    except Exception:
        return {"ok": False, "error": "yanıt işlenemedi"}


def _rdap_domain(domain: str):
    return _json_get(
        f"https://rdap.org/domain/{quote(domain, safe='.-')}",
        accept="application/rdap+json, application/json",
    )


def _dns_lookup(name: str, record_type: str):
    return _json_get(
        "https://dns.google/resolve",
        params={"name": name, "type": record_type},
        accept="application/dns-json",
    )


def _certificates(domain: str, limit: int = 10):
    return _json_get(
        "https://api.certspotter.com/v1/issuances",
        params={
            "domain": domain,
            "include_subdomains": "true",
            "match_wildcards": "true",
            "expand": "dns_names",
            "limit": min(max(int(limit), 1), 100),
        },
    )


def _urlscan_search(domain: str):
    return _urlscan_query(f"page.domain:{domain}")


def _urlscan_ip_search(address: str):
    value = f'"{address}"' if ":" in address else address
    return _urlscan_query(f"page.ip:{value}")


def _urlscan_query(query: str):
    global _URLSCAN_LAST_REQUEST
    with _URLSCAN_LOCK:
        wait = _URLSCAN_MIN_INTERVAL - (time.monotonic() - _URLSCAN_LAST_REQUEST)
        if wait > 0:
            time.sleep(wait)
        _URLSCAN_LAST_REQUEST = time.monotonic()
    return _json_get(
        "https://urlscan.io/api/v1/search/",
        params={"q": query, "size": 5},
    )


def _rdap_ip(address: str):
    return _json_get(
        f"https://rdap.org/ip/{quote(address, safe='.:')}",
        accept="application/rdap+json, application/json",
    )


def _ripestat_network(address: str):
    return _json_get(
        "https://stat.ripe.net/data/network-info/data.json",
        params={"resource": address},
    )


def _ripestat_asn(asn: str):
    return _json_get(
        "https://stat.ripe.net/data/as-overview/data.json",
        params={"resource": f"AS{asn}"},
    )


def _dns_ptr(address: str):
    reverse_name = ipaddress.ip_address(address).reverse_pointer
    return _dns_lookup(reverse_name, "PTR")


def _wikipedia_search(language: str, name: str):
    global _WIKIPEDIA_LAST_REQUEST
    with _WIKIPEDIA_LOCK:
        wait = _WIKIPEDIA_MIN_INTERVAL - (time.monotonic() - _WIKIPEDIA_LAST_REQUEST)
        if wait > 0:
            time.sleep(wait)
        _WIKIPEDIA_LAST_REQUEST = time.monotonic()
    return _json_get(
        f"https://{language}.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": f'"{name}"',
            "srlimit": 10,
            "format": "json",
            "utf8": 1,
        },
    )


def _name_title_matches(name: str, title: str) -> bool:
    def terms(value: str) -> set[str]:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        unaccented = "".join(char for char in decomposed if not unicodedata.combining(char))
        return set(re.findall(r"[^\W_]+", unaccented, flags=re.UNICODE))

    name_terms = terms(name)
    return len(name_terms) <= 1 or name_terms.issubset(terms(title))


def _cache_get_or_create(key: str, builder) -> str:
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(key)
        if cached and now - cached[0] < _CACHE_TTL_SECONDS:
            return cached[1]
    result = builder()
    with _CACHE_LOCK:
        expired_keys = [
            cache_key for cache_key, (created, _) in _CACHE.items()
            if time.monotonic() - created >= _CACHE_TTL_SECONDS
        ]
        for cache_key in expired_keys:
            _CACHE.pop(cache_key, None)
        if len(_CACHE) >= 256:
            oldest_key = min(_CACHE, key=lambda cache_key: _CACHE[cache_key][0])
            _CACHE.pop(oldest_key, None)
        _CACHE[key] = (time.monotonic(), result)
    return result


def _vcard_name(entity: dict) -> str | None:
    vcard = entity.get("vcardArray")
    if not isinstance(vcard, list) or len(vcard) < 2 or not isinstance(vcard[1], list):
        return None
    for row in vcard[1]:
        if isinstance(row, list) and len(row) > 3 and row[0] == "fn":
            return str(row[3])[:100]
    return None


def _domain_registration(payload: dict) -> list[str]:
    lines = []
    entities = payload.get("entities")
    if not isinstance(entities, list):
        entities = []
    registrar = next(
        (
            _vcard_name(entity) or entity.get("handle")
            for entity in entities
            if isinstance(entity, dict) and "registrar" in (entity.get("roles") or [])
        ),
        None,
    )
    if registrar:
        lines.append(f"• Kayıt operatörü: {str(registrar)[:100]}")
    events = payload.get("events")
    for event in events if isinstance(events, list) else []:
        if not isinstance(event, dict):
            continue
        action = str(event.get("eventAction", "")).lower()
        event_date = str(event.get("eventDate", ""))[:10]
        label = {"registration": "Kayıt tarihi", "expiration": "Bitiş tarihi", "last changed": "Son değişiklik"}.get(action)
        if label and event_date:
            lines.append(f"• {label}: {event_date}")
    statuses = payload.get("status", [])
    if isinstance(statuses, list) and statuses:
        lines.append(f"• RDAP durumu: {', '.join(str(status) for status in statuses[:4])}")
    nameserver_data = payload.get("nameservers")
    nameservers = [
        str(server.get("ldhName", "")).rstrip(".").lower()
        for server in (nameserver_data if isinstance(nameserver_data, list) else [])
        if isinstance(server, dict) and server.get("ldhName")
    ]
    if nameservers:
        lines.append(f"• Nameserver: {', '.join(nameservers[:4])}")
    secure_dns = payload.get("secureDNS")
    if isinstance(secure_dns, dict) and "delegationSigned" in secure_dns:
        lines.append(f"• DNSSEC: {'Açık' if secure_dns['delegationSigned'] else 'Kapalı'}")
    return lines or ["• Kayıt bulundu; özet alanları kaynakta mevcut değil."]


def _answer_values(payload: dict) -> list[str]:
    if payload.get("Status") not in (0, None):
        return []
    values = []
    answers = payload.get("Answer")
    for answer in answers if isinstance(answers, list) else []:
        if not isinstance(answer, dict):
            continue
        data = str(answer.get("data", "")).strip().strip('"')
        if data and data not in values:
            values.append(data[:180])
    return values[:4]


def _cert_domains(payload, requested_domain: str) -> tuple[int, list[str]]:
    names = set()
    certificate_count = 0
    if not isinstance(payload, list):
        return 0, []
    for certificate in payload:
        if not isinstance(certificate, dict):
            continue
        certificate_count += 1
        raw_names = certificate.get("dns_names")
        for raw_name in raw_names if isinstance(raw_names, list) else []:
            name = str(raw_name).lower().rstrip(".")
            normalized = name.removeprefix("*.")
            if normalized == requested_domain or normalized.endswith(f".{requested_domain}"):
                names.add(name)
    return certificate_count, sorted(names)


def _urlscan_summary(payload: dict, domain: str) -> list[str]:
    if not isinstance(payload, dict):
        return ["• urlscan arşiv yanıtı beklenen biçimde değil; güvenlik sonucu çıkarılamaz."]
    results = payload.get("results", [])
    matching = []
    for result in results if isinstance(results, list) else []:
        if not isinstance(result, dict):
            continue
        page = result.get("page") or {}
        if not isinstance(page, dict):
            continue
        host = str(page.get("domain") or page.get("apexDomain") or "").lower().rstrip(".")
        if host == domain or host.endswith(f".{domain}"):
            matching.append(result)

    if not matching:
        return ["• urlscan arşivi: Eşleşen herkese açık tarama bulunamadı. Bu, domainin güvenli olduğunu kanıtlamaz."]

    lines = [f"• urlscan arşivi: {len(matching)} herkese açık eski kayıt bulundu."]
    flagged = [result for result in matching if _urlscan_has_malicious_label(result)]
    if flagged:
        lines.append(f"⚠️ {len(flagged)} arşiv kaydında zararlı/oltalama etiketi var; bu eski kayıt güncel durumun kesin kanıtı değildir.")
    else:
        lines.append("• Dönen kayıtlarda açık bir zararlı etiketi yok. Bu, güvenli olduğu anlamına gelmez.")

    lines.extend(_urlscan_record_lines(matching))
    return lines


def _urlscan_ip_summary(payload: dict, address: str) -> list[str]:
    if not isinstance(payload, dict):
        return ["• urlscan arşiv yanıtı beklenen biçimde değil; güvenlik sonucu çıkarılamaz."]
    results = payload.get("results", [])
    matching = []
    for result in results if isinstance(results, list) else []:
        if not isinstance(result, dict):
            continue
        page = result.get("page") or {}
        if not isinstance(page, dict):
            continue
        if str(page.get("ip", "")) == address:
            matching.append(result)
    if not matching:
        return ["• urlscan arşivi: Bu IP ile eşleşen herkese açık eski tarama bulunamadı; bu, IP'nin güvenli olduğunu kanıtlamaz."]

    flagged = [result for result in matching if _urlscan_has_malicious_label(result)]
    lines = [f"• urlscan arşivi: IP ile eşleşen {len(matching)} herkese açık eski kayıt bulundu."]
    if flagged:
        lines.append(f"⚠️ {len(flagged)} arşiv kaydında zararlı/oltalama etiketi var; kayıtlar eski olabilir.")
    else:
        lines.append("• Dönen kayıtlarda açık bir zararlı etiketi yok. Bu, güvenli olduğu anlamına gelmez.")
    lines.extend(_urlscan_record_lines(matching))
    return lines


def _urlscan_has_malicious_label(result: dict) -> bool:
    labels = result.get("labels") or []
    label_text = " ".join(
        str(label.get("label", "")) if isinstance(label, dict) else str(label)
        for label in labels
    ).lower()
    verdicts = result.get("verdicts") or {}
    malicious = any(
        isinstance(verdict, dict) and verdict.get("malicious") is True
        for verdict in verdicts.values()
    ) if isinstance(verdicts, dict) else False
    return malicious or any(word in label_text for word in ("malicious", "phishing", "malware"))


def _urlscan_record_lines(results: list[dict]) -> list[str]:
    lines = []
    for result in results[:2]:
        task = result.get("task") or {}
        if not isinstance(task, dict):
            continue
        scan_id = str(task.get("uuid", ""))
        scanned_at = str(task.get("time", ""))[:16].replace("T", " ")
        if scan_id and re.fullmatch(r"[a-fA-F0-9-]{20,40}", scan_id):
            lines.append(f"  └ Kayıt {scanned_at or 'tarihsiz'}: https://urlscan.io/result/{scan_id}/")
    return lines


def _domain_report_uncached(domain: str) -> str:
    source_names = ("rdap", "A", "AAAA", "MX", "NS", "certificates", "urlscan")
    jobs = {
        "rdap": (_rdap_domain, (domain,)),
        "A": (_dns_lookup, (domain, "A")),
        "AAAA": (_dns_lookup, (domain, "AAAA")),
        "MX": (_dns_lookup, (domain, "MX")),
        "NS": (_dns_lookup, (domain, "NS")),
        "certificates": (_certificates, (domain,)),
        "urlscan": (_urlscan_search, (domain,)),
    }
    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = {
            name: pool.submit(_safe_source, function, *args)
            for name, (function, args) in jobs.items()
        }
        results = {name: future.result() for name, future in futures.items()}

    checked = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "🔎 OSINT — DOMAIN RAPORU",
        f"Hedef: {domain}",
        f"Kontrol: {checked}",
        "Yöntem: Pasif araştırma; hedef siteye bağlantı veya güvenlik taraması yapılmadı.",
        "",
        "📋 KAYIT BİLGİSİ (RDAP)",
    ]
    rdap = results["rdap"]
    if rdap["ok"]:
        lines.extend(_domain_registration(rdap["data"]))
    else:
        lines.append(f"⚠️ RDAP kaynağına ulaşılamadı ({rdap['error']}).")

    lines.extend(["", "🌐 DNS KAYITLARI (Google Public DNS)"])
    for record_type in ("A", "AAAA", "MX", "NS"):
        result = results[record_type]
        if not result["ok"]:
            lines.append(f"• {record_type}: Kaynak geçici olarak erişilemiyor ({result['error']}).")
            continue
        values = _answer_values(result["data"])
        if record_type == "MX" and values == ["0 ."]:
            summary = "Posta sunucusu tanımlı değil (Null MX)"
        else:
            summary = ", ".join(values) if values else "Kayıt bulunamadı."
        lines.append(f"• {record_type}: {summary}")

    lines.extend(["", "🔐 SERTİFİKA ŞEFFAFLIĞI (Cert Spotter)"])
    certificates = results["certificates"]
    if certificates["ok"]:
        count, names = _cert_domains(certificates["data"], domain)
        lines.append(f"• Sonuç kümesinde {count} sertifika kaydı incelendi.")
        if names:
            lines.append(f"• Sertifikalarda görülen adlar: {', '.join(names[:8])}")
        else:
            lines.append("• İlgili sertifikalarda ek domain adı bulunamadı.")
        lines.append("• Sertifika kaydı, sitenin şu anda çalıştığını göstermez.")
    else:
        lines.append(f"⚠️ Sertifika kaynağına ulaşılamadı ({certificates['error']}).")

    lines.extend(["", "🚩 HERKESE AÇIK TARAMA ARŞİVİ (urlscan)"])
    urlscan = results["urlscan"]
    if urlscan["ok"]:
        lines.extend(_urlscan_summary(urlscan["data"], domain))
    else:
        lines.append(f"⚠️ urlscan kaynağına ulaşılamadı ({urlscan['error']}).")

    lines.extend([
        "",
        "Kaynaklar:",
        f"• RDAP: https://rdap.org/domain/{domain}",
        f"• DNS: https://dns.google/query?name={quote(domain)}",
        f"• Sertifikalar: https://api.certspotter.com/v1/issuances?domain={quote(domain)}",
        f"• urlscan arşivi: https://urlscan.io/search/#search={quote('domain:' + domain)}",
        "",
        "Not: Kamu kayıtları eksik veya eski olabilir; tek başına kesin güvenlik kararı değildir.",
    ])
    return "\n".join(lines)[:3800]


def _subdomains_report_uncached(domain: str) -> str:
    result = _safe_source(_certificates, domain, limit=100)
    checked = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "🔎 OSINT — ALT SİTE RAPORU",
        f"Ana domain: {domain}",
        f"Kontrol: {checked}",
        "Yöntem: Herkese açık sertifika kayıtları; DNS brute force veya aktif tarama yapılmadı.",
        "",
        "🔐 SERTİFİKA ŞEFFAFLIĞI (Cert Spotter)",
    ]
    if not result["ok"]:
        lines.append(f"⚠️ Sertifika kaynağına ulaşılamadı ({result['error']}).")
    else:
        certificate_count, names = _cert_domains(result["data"], domain)
        concrete_names = [
            name for name in names
            if not name.startswith("*.") and name != domain
        ]
        wildcard_names = [name for name in names if name.startswith("*.")]
        lines.append(f"• {certificate_count} kamuya açık sertifika kaydı incelendi.")
        if concrete_names:
            lines.append(f"• {len(concrete_names)} farklı alt domain adı bulundu:")
            lines.extend(f"  └ {name}" for name in concrete_names[:30])
            if len(concrete_names) > 30:
                lines.append(f"  └ ... ve {len(concrete_names) - 30} başka ad")
        else:
            lines.append("• Bu kayıtlarda belirli bir alt domain adı bulunamadı.")
        if wildcard_names:
            lines.append(f"• Genel wildcard kaydı: {', '.join(wildcard_names[:5])}")
        lines.append("• Sertifika geçmişi eksik/eski olabilir; bir adresin şu an açık olduğunu göstermez.")

    lines.extend([
        "",
        f"Kaynak: https://api.certspotter.com/v1/issuances?domain={quote(domain)}",
        "Not: Yalnızca sahibi olduğun veya inceleme yetkin olan domainlerde kullan.",
    ])
    return "\n".join(lines)[:3500]


def inspect_domain(raw: str) -> str:
    domain = normalize_domain(raw)
    return _cache_get_or_create(f"domain:{domain}", lambda: _domain_report_uncached(domain))


def inspect_subdomains(raw: str) -> str:
    domain = normalize_domain(raw)
    return _cache_get_or_create(
        f"subdomains:{domain}",
        lambda: _subdomains_report_uncached(domain),
    )


def inspect_gmail(raw: str) -> str:
    domain = normalize_gmail(raw)

    def build_report():
        result = _safe_source(_dns_lookup, domain, "MX")
        checked = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "📧 GMAIL ADRES KONTROLÜ",
            f"Kontrol: {checked}",
            "• Yazdığın adresin biçimi temel Gmail kurallarına uyuyor.",
            f"• Posta sunucusu kontrolü: {domain} MX kayıtları",
        ]
        if result["ok"]:
            values = _answer_values(result["data"])
            lines.append(f"  └ {', '.join(values) if values else 'MX kaydı bulunamadı.'}")
        else:
            lines.append(f"  └ DNS kaynağına ulaşılamadı ({result['error']}).")
        lines.extend([
            "",
            "Bu kontrol hesabın gerçekten var olduğunu, kime ait olduğunu veya sızıntıda bulunup bulunmadığını göstermez.",
            "Gizlilik: Tam e-posta adresi dış kaynağa gönderilmez; yalnızca Gmail domaininin MX kaydı sorgulanır.",
            "Kaynak: https://dns.google/query?name=" + quote(domain) + "&type=MX",
        ])
        return "\n".join(lines)

    return _cache_get_or_create(f"gmail-mx:{domain}", build_report)


def inspect_name(raw: str) -> str:
    name = normalize_name_query(raw)
    with ThreadPoolExecutor(max_workers=2) as pool:
        searches = {
            language: pool.submit(_safe_source, _wikipedia_search, language, name)
            for language in ("tr", "en")
        }
        results = {language: future.result() for language, future in searches.items()}

    checked = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "📚 İSİM / MARKA ARAŞTIRMASI",
        f"Aranan ifade: {name}",
        f"Kontrol: {checked}",
        "Kaynak kapsamı: Türkçe ve İngilizce Wikipedia'nın herkese açık makale başlıkları.",
        "Bu arama kimlik doğrulamaz ve özel kişi bilgisi/iletişim bilgisi toplamaz.",
        "",
    ]
    any_result = False
    for language, label in (("tr", "Türkçe"), ("en", "İngilizce")):
        result = results[language]
        lines.append(f"🔎 {label} Wikipedia")
        if not result["ok"]:
            lines.append(f"• Kaynağa ulaşılamadı ({result['error']}).")
            continue
        payload = result["data"]
        search_data = payload.get("query", {}) if isinstance(payload, dict) else {}
        matches = search_data.get("search", []) if isinstance(search_data, dict) else []
        if not isinstance(matches, list) or not matches:
            lines.append("• Eşleşen kamuya açık makale bulunamadı.")
            continue
        shown = 0
        for match in matches:
            if not isinstance(match, dict) or not match.get("title"):
                continue
            title = html.unescape(re.sub(r"<[^>]*>", "", str(match["title"])))[:180]
            if not _name_title_matches(name, title):
                continue
            page_path = quote(str(match["title"]).replace(" ", "_"), safe="()_-")
            lines.append(f"• {title}: https://{language}.wikipedia.org/wiki/{page_path}")
            any_result = True
            shown += 1
            if shown >= 5:
                break
        if shown == 0:
            lines.append("• İsimle eşleşen makale başlığı bulunamadı.")
    if not any_result:
        lines.extend(["", "Bu iki aramada sonuç çıkmaması, kişi veya markanın internette bulunmadığını kanıtlamaz."])
    lines.extend([
        "",
        "Gizlilik: Aranan ifade Wikipedia'nın arama servisine gönderilir. Eşleşmeler yalnızca olası kamuya açık makalelerdir; aynı isimli kişiler karıştırılabilir.",
    ])
    return "\n".join(lines)[:3500]


def inspect_url(raw: str) -> str:
    domain = normalize_domain(raw)
    report = inspect_domain(domain)
    return (
        "🔗 LINK OSINT\n"
        f"Gönderilen linkin alan adı: {domain}\n"
        "Linkin yolu ve parametreleri paylaşılmadı; sayfa açılmadı. "
        "Yalnızca bu alan adına ait pasif kamu kayıtları incelendi.\n\n"
        f"{report}"
    )[:3800]


def _ip_report_uncached(address: str) -> str:
    with ThreadPoolExecutor(max_workers=4) as pool:
        rdap_future = pool.submit(_safe_source, _rdap_ip, address)
        ripe_future = pool.submit(_safe_source, _ripestat_network, address)
        ptr_future = pool.submit(_safe_source, _dns_ptr, address)
        urlscan_future = pool.submit(_safe_source, _urlscan_ip_search, address)
        rdap = rdap_future.result()
        ripe = ripe_future.result()
        ptr = ptr_future.result()
        urlscan = urlscan_future.result()

    ripe_response = ripe.get("data") if ripe["ok"] else {}
    ripe_data = ripe_response.get("data", {}) if isinstance(ripe_response, dict) else {}
    if not isinstance(ripe_data, dict):
        ripe_data = {}
    raw_asns = ripe_data.get("asns")
    asns = [
        str(asn) for asn in (raw_asns if isinstance(raw_asns, list) else [])
        if str(asn).isdigit()
    ][:3]
    as_overviews = []
    if asns:
        with ThreadPoolExecutor(max_workers=3) as pool:
            as_overviews = list(pool.map(lambda asn: _safe_source(_ripestat_asn, asn), asns))

    rdap_data = rdap.get("data", {}) if rdap["ok"] else {}
    if not isinstance(rdap_data, dict):
        rdap_data = {}
    ptr_names = _answer_values(ptr.get("data", {})) if ptr["ok"] else []
    checked = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "🔎 OSINT — IP RAPORU",
        f"Hedef: {address}",
        f"Kontrol: {checked}",
        "Yöntem: Pasif kayıt ve DNS sorguları; hedef IP'ye bağlantı/port taraması yapılmadı.",
        "",
        "📋 IP KAYIT BİLGİSİ (RDAP)",
    ]
    if rdap["ok"]:
        for label, key in (
            ("Ağ adı", "name"),
            ("Kayıt kimliği", "handle"),
            ("Ülke kodu", "country"),
            ("Başlangıç IP", "startAddress"),
            ("Bitiş IP", "endAddress"),
        ):
            value = rdap_data.get(key)
            if value:
                lines.append(f"• {label}: {str(value)[:140]}")
        if not any(key in rdap_data for key in ("name", "handle", "country", "startAddress", "endAddress")):
            lines.append("• Kayıt bulundu; özet alanları kaynakta mevcut değil.")
    else:
        lines.append(f"⚠️ RDAP kaynağına ulaşılamadı ({rdap['error']}).")

    lines.extend(["", "📡 YÖNLENDİRME / ASN (RIPEstat)"])
    if ripe["ok"]:
        prefix = ripe_data.get("prefix")
        if prefix:
            lines.append(f"• Ağ öneki: {str(prefix)[:100]}")
        if asns:
            lines.append(f"• ASN: {', '.join('AS' + asn for asn in asns)}")
            for asn, result in zip(asns, as_overviews):
                overview = result.get("data") if result["ok"] else None
                overview_data = overview.get("data", {}) if isinstance(overview, dict) else {}
                holder = overview_data.get("holder") if isinstance(overview_data, dict) else None
                if holder:
                    lines.append(f"  └ AS{asn} sahibi: {str(holder)[:120]}")
        else:
            lines.append("• Yönlendirme verisinde ASN bulunamadı.")
    else:
        lines.append(f"⚠️ RIPEstat kaynağına ulaşılamadı ({ripe['error']}).")

    lines.extend(["", "↩️ TERS DNS"])
    if ptr["ok"]:
        lines.append(f"• PTR: {', '.join(ptr_names) if ptr_names else 'Kayıt bulunamadı.'}")
    else:
        lines.append(f"⚠️ Ters DNS kaynağına ulaşılamadı ({ptr['error']}).")

    lines.extend(["", "🚩 HERKESE AÇIK TARAMA ARŞİVİ (urlscan)"])
    if urlscan["ok"]:
        lines.extend(_urlscan_ip_summary(urlscan["data"], address))
    else:
        lines.append(f"⚠️ urlscan kaynağına ulaşılamadı ({urlscan['error']}).")

    lines.extend([
        "",
        "Kaynaklar:",
        f"• RDAP: https://rdap.org/ip/{quote(address, safe='.:')}",
        f"• RIPEstat: https://stat.ripe.net/{quote(address, safe='.:')}",
        "• Ters DNS: https://dns.google/",
        f"• urlscan arşivi: https://urlscan.io/search/#search={quote('page.ip:' + address)}",
        "",
        "Not: IP kayıtları ağ sağlayıcısını gösterir; tek başına kişi veya kesin konum tespiti değildir.",
    ])
    return "\n".join(lines)[:3800]


def inspect_ip(raw: str) -> str:
    address = normalize_public_ip(raw)
    return _cache_get_or_create(f"ip:{address}", lambda: _ip_report_uncached(address))
