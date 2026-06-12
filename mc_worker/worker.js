/**
 * AZRxGUARD — Minecraft Java AFK Bot Worker
 * Subprocess: bot.py → node worker.js <host> <port> <username>
 * Protokol: JSON satırları stdout üzerinden
 */

const mineflayer = require('mineflayer');

const [,, host, portStr, username] = process.argv;
const port = parseInt(portStr, 10) || 25565;

if (!host || !username) {
  out({ event: 'error', message: 'Eksik argüman: host ve username gerekli.' });
  process.exit(1);
}

// Mineflayer'ın desteklediği sürümler — otomatik algılama başarısız olunca sırayla denenir
const FALLBACK = [
  '1.21.11', '1.21.9', '1.21.8', '1.21.7', '1.21.6',
  '1.21.5', '1.21.4', '1.21.3', '1.21.2', '1.21.1',
  '1.21', '1.20.6', '1.20.4', '1.20.1',
  '1.19.4', '1.19.2', '1.18.2', '1.17.1', '1.16.5',
];

let bot        = null;
let connected  = false;
let fbIndex    = -1;   // -1 = auto-detect, 0+ = FALLBACK[fbIndex]

function out(obj) {
  try { process.stdout.write(JSON.stringify(obj) + '\n'); } catch (_) {}
}

function nextVersion() {
  return fbIndex < 0 ? false : FALLBACK[fbIndex];
}

function tryConnect() {
  if (bot) {
    // Eski bot nesnesini temizle
    try { bot.removeAllListeners(); } catch (_) {}
    bot = null;
  }

  const ver = nextVersion();

  try {
    bot = mineflayer.createBot({
      host, port, username,
      version: ver,
      auth: 'offline',
      hideErrors: true,
      checkTimeoutInterval: 30000,
    });
  } catch (err) {
    // Geçersiz sürüm string'i — sessizce bir sonrakine geç
    fbIndex++;
    if (fbIndex < FALLBACK.length) { setImmediate(tryConnect); return; }
    out({ event: 'error', message: `Desteklenen hiçbir sürümle bağlanılamadı: ${err.message}` });
    process.exit(1);
  }

  // ── Bağlantı kuruldu ──────────────────────────────
  bot.once('spawn', () => {
    connected = true;
    out({ event: 'connected', host, port, username, version: bot.version || String(ver) });

    // TPA otomatik ret — oyuncu sohbeti
    bot.on('chat', (sender, message) => {
      if (message.toLowerCase().includes('tpa')) {
        try { bot.chat('/tpa deny'); } catch (_) {}
        try { bot.chat('/tpdeny');   } catch (_) {}
        out({ event: 'tpa_rejected', from: sender });
      }
    });

    // TPA otomatik ret — sistem mesajları
    bot.on('message', (json) => {
      try {
        const t = json.toString().toLowerCase();
        if (t.includes('tpa') && t.includes(username.toLowerCase())) {
          try { bot.chat('/tpa deny'); } catch (_) {}
          try { bot.chat('/tpdeny');   } catch (_) {}
        }
      } catch (_) {}
    });
  });

  // ── Atıldı ───────────────────────────────────────
  bot.once('kicked', (reason) => {
    let r = reason;
    try { r = JSON.parse(reason).text || JSON.parse(reason).translate || reason; } catch (_) {}
    out({ event: 'kicked', reason: String(r).slice(0, 300) });
    process.exit(1);
  });

  // ── Hata ─────────────────────────────────────────
  bot.once('error', (err) => {
    const msg = String(err.message || err);

    // Bağlantı kurulmamışsa ve sürüm/protokol hatasıysa → sessizce sonrakini dene
    if (!connected) {
      const isVerErr = /version|protocol|unsupported|invalid|handshak/i.test(msg);
      if (isVerErr || fbIndex < 0) {
        fbIndex++;
        if (fbIndex < FALLBACK.length) {
          setTimeout(tryConnect, 300);
          return;
        }
      }
    }

    out({ event: 'error', message: msg.slice(0, 300) });
    process.exit(1);
  });

  // ── Bağlantı kesildi ─────────────────────────────
  bot.once('end', (reason) => {
    if (!connected) return; // error handler devreye girdi
    out({ event: 'disconnected', reason: reason || 'Bağlantı kapandı' });
    process.exit(0);
  });
}

// ── Stdin — Python'dan komutlar ───────────────────
let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  buf += chunk;
  let i;
  while ((i = buf.indexOf('\n')) !== -1) {
    const line = buf.slice(0, i).trim();
    buf = buf.slice(i + 1);
    if (!line) continue;
    try {
      const cmd = JSON.parse(line);
      if (cmd.cmd === 'quit') {
        if (bot) { try { bot.quit('Kullanıcı durdurdu'); } catch (_) {} }
        process.exit(0);
      } else if (cmd.cmd === 'chat' && bot) {
        try { bot.chat(cmd.text); } catch (_) {}
      }
    } catch (_) {}
  }
});

process.on('SIGTERM', () => { if (bot) { try { bot.quit(); } catch (_) {} } process.exit(0); });
process.on('SIGINT',  () => { if (bot) { try { bot.quit(); } catch (_) {} } process.exit(0); });

// İlk deneme: auto-detect (version: false)
tryConnect();
