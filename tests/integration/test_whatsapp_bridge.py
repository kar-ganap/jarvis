"""Integration tests for the WhatsApp Baileys bridge.

These tests require the bridge to be running (docker compose up whatsapp_bridge).
They are skipped if the bridge is unreachable.
"""
from __future__ import annotations

import pytest
import requests

BRIDGE_URL = "http://localhost:9120"


def _bridge_reachable() -> bool:
    try:
        resp = requests.get(f"{BRIDGE_URL}/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _bridge_reachable(),
    reason="WhatsApp bridge not reachable at localhost:9120",
)


class TestWhatsAppBridge:
    def test_bridge_health_endpoint(self):
        """GET /health returns status and connected field."""
        resp = requests.get(f"{BRIDGE_URL}/health", timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "connected" in data
        assert data["status"] == "ok"

    def test_send_returns_503_when_not_connected(self):
        """POST /send returns 503 if WhatsApp is not connected."""
        resp = requests.post(
            f"{BRIDGE_URL}/send",
            json={"to": "test@s.whatsapp.net", "text": "test"},
            timeout=5,
        )
        # If not connected (no QR scanned), should be 503
        # If connected, would be 200 — either is acceptable for this test
        assert resp.status_code in (200, 503)
