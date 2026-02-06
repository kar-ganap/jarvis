#!/usr/bin/env python3
"""Create the Jarvis agent and send a test message."""
from __future__ import annotations

import os

import httpx
from letta_client import Letta

from jarvis.agent.factory import get_or_create_agent
from jarvis.settings import load_settings
from jarvis.utils.logging import setup_logging


def _ensure_google_provider(base_url: str) -> None:
    """Register Google/Gemini provider if GOOGLE_API_KEY is set and not yet registered."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return

    # Check if already registered
    resp = httpx.get(f"{base_url}/v1/providers/")
    providers = resp.json()
    if any(p.get("provider_type") == "google_ai" for p in providers):
        return

    print("Registering Google/Gemini provider ...")
    httpx.post(
        f"{base_url}/v1/providers/",
        json={"name": "google", "api_key": api_key, "provider_type": "google_ai"},
    )


def main() -> None:
    setup_logging()
    settings = load_settings()

    print(f"Connecting to Letta at {settings.letta.base_url} ...")
    client = Letta(base_url=settings.letta.base_url)

    _ensure_google_provider(settings.letta.base_url)

    print(f"Creating/retrieving agent '{settings.agent.name}' ...")
    agent = get_or_create_agent(client, settings)
    print(f"Agent ID: {agent.id}")

    # Show memory blocks
    blocks = client.agents.blocks.list(agent_id=agent.id)
    for block in blocks:
        print(f"  [{block.label}] {len(block.value)}/{block.limit} chars")

    # Send a test message
    print("\nSending test message ...")
    response = client.agents.messages.create(
        agent_id=agent.id,
        messages=[{"role": "user", "content": "Hello, introduce yourself briefly."}],
    )

    for msg in response.messages:
        if msg.message_type == "assistant_message":
            print(f"\nJarvis: {msg.content}")


if __name__ == "__main__":
    main()
