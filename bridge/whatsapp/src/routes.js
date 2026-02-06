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

export default router;
