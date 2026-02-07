import fs from "fs";
import {
  makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} from "@whiskeysockets/baileys";
import pino from "pino";
import qrcode from "qrcode-terminal";

const logger = pino({ level: "warn" });

const WEBHOOK_URL =
  process.env.WHATSAPP_WEBHOOK_URL ||
  "http://host.docker.internal:9100/whatsapp/inbound";
const AUTH_DIR = process.env.WHATSAPP_AUTH_DIR || "./auth_data";

let socket = null;
let connected = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 60000;

function getReconnectDelay() {
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
  reconnectAttempts++;
  return delay;
}

async function createSession() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  const sock = makeWASocket({
    version,
    auth: state,
    logger,
    printQRInTerminal: false,
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log("\n--- Scan this QR code with WhatsApp ---");
      qrcode.generate(qr, { small: true });
      console.log("---------------------------------------\n");
    }

    if (connection === "open") {
      connected = true;
      reconnectAttempts = 0;
      console.log("[bridge] Connected to WhatsApp");
    }

    if (connection === "close") {
      connected = false;
      const statusCode =
        lastDisconnect?.error?.output?.statusCode;
      const loggedOut = statusCode === DisconnectReason.loggedOut;

      if (loggedOut) {
        console.log("[bridge] Logged out — clearing auth and requesting new QR");
        // Clear contents of auth dir (not the dir itself — Docker volume mount)
        for (const file of fs.readdirSync(AUTH_DIR)) {
          fs.rmSync(`${AUTH_DIR}/${file}`, { recursive: true, force: true });
        }
        reconnectAttempts = 0;
        setTimeout(() => createSession(), 2000);
        return;
      }

      const delay = getReconnectDelay();
      console.log(`[bridge] Disconnected (code=${statusCode}), reconnecting in ${delay}ms`);
      setTimeout(() => createSession(), delay);
    }
  });

  sock.ev.on("messages.upsert", async ({ messages }) => {
    for (const msg of messages) {
      if (msg.key.fromMe) continue;

      const messageType = Object.keys(msg.message || {})[0];
      if (!messageType) continue;

      // Skip protocol, reaction, poll messages
      if (
        messageType === "protocolMessage" ||
        messageType === "reactionMessage" ||
        messageType === "pollUpdateMessage"
      ) {
        continue;
      }

      // Extract text content
      let text = null;
      if (messageType === "conversation") {
        text = msg.message.conversation;
      } else if (messageType === "extendedTextMessage") {
        text = msg.message.extendedTextMessage.text;
      } else if (msg.message[messageType]?.caption) {
        // Media with caption
        text = `[media: ${messageType}] ${msg.message[messageType].caption}`;
      }

      if (!text) continue;

      const senderJid = msg.key.remoteJid;
      const isGroup = senderJid.endsWith("@g.us");
      const sender = isGroup ? msg.key.participant : senderJid;
      const pushName = msg.pushName || "Unknown";
      const isStatus = senderJid === "status@broadcast";

      const payload = {
        sender,
        chat_jid: senderJid,
        push_name: pushName,
        text,
        is_group: isGroup,
        is_status: isStatus,
        message_id: msg.key.id,
      };

      try {
        await fetch(WEBHOOK_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } catch (err) {
        console.error("[bridge] Webhook POST failed:", err.message);
      }
    }
  });

  socket = sock;
  return sock;
}

function getSocket() {
  return socket;
}

function isConnected() {
  return connected;
}

export { createSession, getSocket, isConnected };
