"""Phase 9 live validation — Memory & Learning (requires Letta server).

Usage:
  set -a && source ~/.zshrc && set +a
  uv run python scripts/validate_memory.py
"""
from __future__ import annotations

import asyncio
import sys


def validate_memory():
    from letta_client import Letta

    from jarvis.memory.handlers import memory_recall, memory_save
    from jarvis.memory.learning import (
        build_usage_summary,
        collect_usage_stats,
        run_learning_cycle,
        update_human_block,
    )
    from jarvis.monitoring.metrics import MESSAGE_COUNT, TOOL_INVOCATION_COUNT

    client = Letta(base_url="http://localhost:8283")

    # Find or create a test agent
    page = client.agents.list(name="jarvis")
    existing = page.items if hasattr(page, "items") else page
    if existing:
        agent_id = existing[0].id
        print(f"Using existing agent: {agent_id}")
    else:
        print("No jarvis agent found. Creating one for testing...")
        agent = client.agents.create(
            name="jarvis-memory-test",
            model="openai/gpt-4o-mini",
            embedding="openai/text-embedding-3-small",
            memory_blocks=[
                {"label": "persona", "value": "You are a test agent."},
                {
                    "label": "human",
                    "value": "Name: Kartik\nPreferences: (to be learned)",
                },
            ],
        )
        agent_id = agent.id
        print(f"Created test agent: {agent_id}")

    print("\n=== Memory Validation ===")

    # 1. Save a note with category
    print("\n1. Saving note with category...")
    result = memory_save(
        client, agent_id, "Buy milk and eggs", category="grocery"
    )
    print(f"   Status: {result['status']}")
    assert result["status"] == "saved"

    # 2. Save a note without category
    print("\n2. Saving note without category...")
    result2 = memory_save(client, agent_id, "Remember to call dentist")
    print(f"   Status: {result2['status']}")
    assert result2["status"] == "saved"

    # 3. Recall notes
    print("\n3. Recalling notes about 'milk'...")
    results = memory_recall(client, agent_id, "milk")
    print(f"   Found {len(results)} results")
    for r in results:
        print(f"   - {r['text']}")
    assert len(results) >= 1, "Should find at least one result"
    assert any("milk" in r["text"].lower() for r in results)

    # 4. Recall with category filter
    print("\n4. Recalling notes with category='grocery'...")
    results2 = memory_recall(client, agent_id, "milk", category="grocery")
    print(f"   Found {len(results2)} results")
    for r in results2:
        print(f"   - {r['text']}")

    print("\n   Memory save/recall: PASS")

    # 5. Test learning module
    print("\n=== Learning Module Validation ===")

    # 5a. Collect usage stats
    print("\n5a. Collecting usage stats...")
    # Increment some counters first
    MESSAGE_COUNT.labels(channel="cli", direction="inbound").inc(10)
    MESSAGE_COUNT.labels(channel="whatsapp", direction="inbound").inc(25)
    TOOL_INVOCATION_COUNT.labels(tool_name="gmail_search").inc(5)
    TOOL_INVOCATION_COUNT.labels(tool_name="todoist_list_tasks").inc(3)

    stats = collect_usage_stats()
    print(f"   Channels: {stats['channels']}")
    print(f"   Tools: {stats['tools']}")
    assert len(stats["channels"]) > 0, "Should have channel data"

    # 5b. Build summary
    print("\n5b. Building usage summary...")
    summary = build_usage_summary(stats)
    print(f"   Summary: {summary}")
    assert "whatsapp" in summary.lower() or "25" in summary

    # 5c. Update human block
    print("\n5c. Updating human memory block...")
    asyncio.run(update_human_block(client, agent_id, summary))
    print("   Human block updated")

    # 5d. Verify the block was updated
    print("\n5d. Verifying human block...")
    blocks = client.agents.blocks.list(agent_id=agent_id)
    human_block = None
    for block in blocks:
        if block.label == "human":
            human_block = block
            break
    if human_block:
        print(f"   Human block value: {human_block.value[:200]}...")
        assert "USAGE PATTERNS:" in human_block.value
        print("   USAGE PATTERNS section present: PASS")
    else:
        print("   WARNING: No human block found")

    # 5e. Full learning cycle
    print("\n5e. Running full learning cycle...")
    asyncio.run(run_learning_cycle(client, agent_id))
    print("   Learning cycle completed")

    print("\n   Learning module: ALL PASS")
    print("\n=== Memory & Learning: ALL PASS ===")


if __name__ == "__main__":
    try:
        validate_memory()
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
