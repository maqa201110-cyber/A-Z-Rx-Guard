/**
 * AZRxGUARD — Minecraft AFK Bot Worker (Java Edition)
 * Spawned as a subprocess by bot.py.
 * Communication: JSON lines on stdout (events to Python).
 *                JSON lines on stdin  (commands from Python).
 *
 * Sürüm stratejisi:
 *   1. version:false → sunucuya ping at, sürümü otomatik öğren
 *   2. Ping başarısızsa FALLBACK_VERSIONS sırasıyla dene
 */

const mineflayer = require('mineflayer');

const [,, host, portStr, username] = process.argv;
const port = parseInt(portStr, 10) || 25565;

// Deneme sırası: en yaygın/yeni sürümler önce
const FALLBACK_VERSIONS = [
  '1.21.1', '1.21', '1.20.4', '1.20.1', '1.20',
  '1.19.4', '1.19.2', '1.18.2', '1.17.1', '1.16.5',
];

if (!host || host.trim().length < 2 || !username) {
  process.stdout.write(JSON.stringify({ event: 'error', message: 'Eksik argümanlar: host ve username gerekli.' }) + '\n');
  process.exit(1);
}

let bot = null;
let connected = false;
let attemptIndex = -1; // -1 = auto-detect, 0+ = fallback

function emit(obj) {
  try { process.stdout.write(JSON.stringify(obj) + '\n'); } catch (_) {}
}

function isVersionError(msg) {
  const s = String(msg).toLowerCase();
  return s.includes('version') || s.includes('protocol') || s.includes('unsupported')
      || s.includes('ping') || s.includes('handshak');
}

function currentVersion() {
  return attemptIndex < 0 ? false : FALLBACK_VERSIONS[attemptIndex];
}

function tryConnect() {
  const ver = currentVersion();
  emit({ event: 'debug', message: `Bağlanıyor: ${host}:${port} sürüm=${ver === false ? 'auto' : ver}` });

  let b;
  try {
    b = mineflayer.createBot({
      host,
      port,
      username,
      version: ver,
      auth: 'offline',
      hideErrors: true,
      checkTimeoutInterval: 30000,
      defaultChatPatterns: true,
    });
  } catch (err) {
    emit({ event: 'error', message: `Bot oluşturulamadı: ${err.message}` });
    process.exit(1);
  }

  bot = b;

  b.once('spawn', () => {
    connected = true;
    emit({ event: 'connected', host, port, username, version: b.version || ver });

    // TPA otomatik red — chat
    b.on('chat', (senderName, message) => {
      const lower = message.toLowerCase();
      if (lower.includes('tpa') || lower.includes('/tpa')) {
        try { b.chat('/tpa deny'); } catch (_) {}
        try { b.chat('/tpdeny'); } catch (_) {}
        emit({ event: 'tpa_rejected', from: senderName, message });
      }
    });

    // TPA otomatik red — sunucu mesajları
    b.on('message', (jsonMsg) => {
      try {
        const text = jsonMsg.toString();
        const lower = text.toLowerCase();
        if (lower.includes('tpa') && lower.includes(username.toLowerCase())) {
          try { b.chat('/tpa deny'); } catch (_) {}
          try { b.chat('/tpdeny'); } catch (_) {}
          emit({ event: 'tpa_rejected', text });
        }
      } catch (_) {}
    });
  });

  b.once('kicked', (reason) => {
    let reasonStr = reason;
    try {
      const parsed = JSON.parse(reason);
      reasonStr = parsed.text || parsed.translate || reason;
    } catch (_) {}
    emit({ event: 'kicked', reason: String(reasonStr).slice(0, 300) });
    process.exit(1);
  });

  b.once('error', (err) => {
    const msg = err.message || String(err);
    if (!connected && isVersionError(msg)) {
      // Sürüm uyumsuzluğu → sonraki fallback'i dene
      attemptIndex++;
      if (attemptIndex < FALLBACK_VERSIONS.length) {
        emit({ event: 'debug', message: `Sürüm hatası (${msg.slice(0,80)}), ${FALLBACK_VERSIONS[attemptIndex]} deneniyor...` });
        setTimeout(tryConnect, 500);
        return;
      }
    }
    emit({ event: 'error', message: msg });
    process.exit(1);
  });

  b.once('end', (reason) => {
    if (!connected) return; // error handler halleder
    emit({ event: 'disconnected', reason: reason || 'Bağlantı kapandı' });
    process.exit(0);
  });
}

// Stdin — Python'dan komut al
let stdinBuf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  stdinBuf += chunk;
  let idx;
  while ((idx = stdinBuf.indexOf('\n')) !== -1) {
    const line = stdinBuf.slice(0, idx).trim();
    stdinBuf = stdinBuf.slice(idx + 1);
    if (!line) continue;
    try {
      const msg = JSON.parse(line);
      if (msg.cmd === 'quit') {
        if (bot) { try { bot.quit('Kullanıcı tarafından durduruldu'); } catch (_) {} }
        process.exit(0);
      } else if (msg.cmd === 'chat' && bot) {
        try { bot.chat(msg.text); } catch (_) {}
      } else if (msg.cmd === 'gamemode' && bot) {
        try { bot.chat(`/gamemode ${msg.mode}`); } catch (_) {}
      }
    } catch (_) {}
  }
});

process.on('SIGTERM', () => { if (bot) { try { bot.quit(); } catch (_) {} } process.exit(0); });
process.on('SIGINT',  () => { if (bot) { try { bot.quit(); } catch (_) {} } process.exit(0); });

// İlk deneme: auto-detect
tryConnect();
