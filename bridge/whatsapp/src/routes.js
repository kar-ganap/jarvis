import { Router } from "express";
import { getSocket, isConnected } from "./session.js";

const router = Router();

router.get("/health", (_req, res) => {
  res.json({ status: "ok", connected: isConnected() });
});

router.post("/send", async (req, res) => {
  const sock = getSocket();
  if (!sock || !isConnected()) {
    return res.status(503).json({ error: "not connected" });
  }

  const { to, text } = req.body;
  if (!to || !text) {
    return res.status(400).json({ error: "missing 'to' or 'text'" });
  }

  try {
    const result = await sock.sendMessage(to, { text });
    res.json({ status: "sent", id: result.key.id });
  } catch (err) {
    console.error("[bridge] Send failed:", err.message);
    res.status(500).json({ error: err.message });
  }
});

router.post("/send-audio", async (req, res) => {
  const sock = getSocket();
  if (!sock || !isConnected()) {
    return res.status(503).json({ error: "not connected" });
  }

  const { to, audio_base64, mime_type, text } = req.body;
  if (!to || !audio_base64) {
    return res.status(400).json({ error: "missing 'to' or 'audio_base64'" });
  }

  try {
    const audioBuffer = Buffer.from(audio_base64, "base64");
    const audioResult = await sock.sendMessage(to, {
      audio: audioBuffer,
      mimetype: mime_type || "audio/mpeg",
      ptt: true,
    });

    // Optionally send text as a separate message
    let textResult = null;
    if (text) {
      textResult = await sock.sendMessage(to, { text });
    }

    res.json({
      status: "sent",
      audio_id: audioResult.key.id,
      text_id: textResult?.key?.id || null,
    });
  } catch (err) {
    console.error("[bridge] Send audio failed:", err.message);
    res.status(500).json({ error: err.message });
  }
});

export default router;
