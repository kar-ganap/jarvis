import express from "express";
import { createSession } from "./session.js";
import routes from "./routes.js";

const PORT = parseInt(process.env.WHATSAPP_BRIDGE_PORT || "9120", 10);

const app = express();
app.use(express.json({ limit: "10mb" }));
app.use("/", routes);

app.listen(PORT, () => {
  console.log(`[bridge] HTTP server listening on port ${PORT}`);
  createSession().catch((err) => {
    console.error("[bridge] Failed to create session:", err);
  });
});
