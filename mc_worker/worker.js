/**
 * AZRxGUARD — Minecraft AFK Bot Worker
 * Spawned as a subprocess by bot.py.
 * Communication: JSON lines on stdout (events to Python).
 *                JSON lines on stdin  (commands from Python).
 */

const mineflayer = require('mineflayer');

const [,, host, portStr, username] = process.argv;
const port = parseInt(portStr, 10) || 25565;

if (!host || !username) {
  process.stdout.write(JSON.stringify({ event: 'error', message: 'Eksik argümanlar: host ve username gerekli.' }) + '\n');
  process.exit(1);
}

let bot = null;

function emit(obj) {
  try {
    process.stdout.write(JSON.stringify(obj) + '\n');
  } catch (_) {}
}

function createBot() {
  try {
    bot = mineflayer.createBot({
      host,
      port,
      username,
      version: false,
      auth: 'offline',
      hideErrors: false,
      checkTimeoutInterval: 30000,
      defaultChatPatterns: true,
    });
  } catch (err) {
    emit({ event: 'error', message: err.message });
    process.exit(1);
  }

  bot.on('spawn', () => {
    emit({ event: 'connected', host, port, username });
  });

  bot.on('chat', (senderName, message) => {
    const lower = message.toLowerCase();
    // TPA komutunu otomatik reddet
    if (lower.includes('tpa') || lower.includes('/tpa')) {
      try { bot.chat('/tpa deny'); } catch (_) {}
      try { bot.chat('/tpdeny'); } catch (_) {}
      emit({ event: 'tpa_rejected', from: senderName, message });
    }
  });

  bot.on('message', (jsonMsg) => {
    try {
      const text = jsonMsg.toString();
      const lower = text.toLowerCase();
      if (lower.includes('tpa') && lower.includes(username.toLowerCase())) {
        try { bot.chat('/tpa deny'); } catch (_) {}
        try { bot.chat('/tpdeny'); } catch (_) {}
        emit({ event: 'tpa_rejected', text });
      }
    } catch (_) {}
  });

  bot.on('kicked', (reason) => {
    let reasonStr = reason;
    try {
      const parsed = JSON.parse(reason);
      reasonStr = parsed.text || parsed.translate || reason;
    } catch (_) {}
    emit({ event: 'kicked', reason: String(reasonStr).slice(0, 300) });
    process.exit(1);
  });

  bot.on('error', (err) => {
    emit({ event: 'error', message: err.message || String(err) });
    process.exit(1);
  });

  bot.on('end', (reason) => {
    emit({ event: 'disconnected', reason: reason || 'Bağlantı kapandı' });
    process.exit(0);
  });
}

// Stdin'den Python'dan komut al
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

process.on('SIGTERM', () => {
  if (bot) { try { bot.quit(); } catch (_) {} }
  process.exit(0);
});

process.on('SIGINT', () => {
  if (bot) { try { bot.quit(); } catch (_) {} }
  process.exit(0);
});

createBot();
