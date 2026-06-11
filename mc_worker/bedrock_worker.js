/**
 * AZRxGUARD — Minecraft Bedrock AFK Bot Worker
 * Uses bedrock-protocol to connect to Bedrock Edition servers.
 * Communication: JSON lines on stdout (events) / stdin (commands).
 */

const bedrock = require('bedrock-protocol');

const [,, host, portStr, username] = process.argv;
const port = parseInt(portStr, 10) || 19132;

if (!host || !username) {
  process.stdout.write(JSON.stringify({ event: 'error', message: 'Eksik argümanlar: host ve username gerekli.' }) + '\n');
  process.exit(1);
}

function emit(obj) {
  try {
    process.stdout.write(JSON.stringify(obj) + '\n');
  } catch (_) {}
}

let client = null;

function createClient() {
  try {
    client = bedrock.createClient({
      host,
      port,
      username,
      offline: true,
      skipPing: false,
    });
  } catch (err) {
    emit({ event: 'error', message: err.message || String(err) });
    process.exit(1);
  }

  client.on('spawn', () => {
    emit({ event: 'connected', host, port, username });
  });

  // Bedrock sohbet okuma
  client.on('text', (packet) => {
    try {
      const msg = (packet.message || packet.parameters?.join(' ') || '').toLowerCase();
      if (msg.includes('tpa')) {
        // Bedrock'ta tpa red komutu gönder
        try {
          client.queue('command_request', {
            command: '/tpa deny',
            internal: false,
            version: 52,
          });
        } catch (_) {}
        emit({ event: 'tpa_rejected', message: msg });
      }
    } catch (_) {}
  });

  client.on('kick', (reason) => {
    let reasonStr = reason;
    try { reasonStr = JSON.parse(reason)?.message || reason; } catch (_) {}
    emit({ event: 'kicked', reason: String(reasonStr).slice(0, 300) });
    process.exit(1);
  });

  client.on('error', (err) => {
    emit({ event: 'error', message: err.message || String(err) });
    process.exit(1);
  });

  client.on('close', () => {
    emit({ event: 'disconnected', reason: 'Bağlantı kapandı' });
    process.exit(0);
  });
}

// Stdin komutları
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
        if (client) { try { client.close(); } catch (_) {} }
        process.exit(0);
      }
    } catch (_) {}
  }
});

process.on('SIGTERM', () => { if (client) { try { client.close(); } catch (_) {} } process.exit(0); });
process.on('SIGINT',  () => { if (client) { try { client.close(); } catch (_) {} } process.exit(0); });

createClient();
