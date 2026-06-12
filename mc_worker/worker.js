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

function out(obj) {
  try { process.stdout.write(JSON.stringify(obj) + '\n'); } catch (_) {}
}

// version: false → sunucuya TEK ping at, sürümü otomatik öğren, TEK bağlantı kur
const bot = mineflayer.createBot({
  host,
  port,
  username,
  version: false,   // Otomatik sürüm tespiti (tek ping + tek bağlantı)
  auth: 'offline',
  hideErrors: true,
  checkTimeoutInterval: 30000,
});

// ── Bağlantı kuruldu ──────────────────────────────────────────
bot.once('spawn', () => {
  out({ event: 'connected', host, port, username, version: String(bot.version || '') });

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

// ── Atıldı ────────────────────────────────────────────────────
bot.once('kicked', (reason) => {
  let r = reason;
  try {
    const p = JSON.parse(reason);
    r = p.text || p.translate || p.extra?.[0]?.text || reason;
  } catch (_) {}
  out({ event: 'kicked', reason: String(r).replace(/"/g, '').slice(0, 300) });
  process.exit(1);
});

// ── Hata ──────────────────────────────────────────────────────
bot.once('error', (err) => {
  out({ event: 'error', message: String(err.message || err).slice(0, 300) });
  process.exit(1);
});

// ── Bağlantı kesildi ──────────────────────────────────────────
bot.once('end', (reason) => {
  out({ event: 'disconnected', reason: reason || 'Bağlantı kapandı' });
  process.exit(0);
});

// ── Stdin — Python'dan komutlar ───────────────────────────────
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
        try { bot.quit('Kullanıcı durdurdu'); } catch (_) {}
        process.exit(0);
      } else if (cmd.cmd === 'chat') {
        try { bot.chat(cmd.text); } catch (_) {}
      }
    } catch (_) {}
  }
});

process.on('SIGTERM', () => { try { bot.quit(); } catch (_) {} process.exit(0); });
process.on('SIGINT',  () => { try { bot.quit(); } catch (_) {} process.exit(0); });
