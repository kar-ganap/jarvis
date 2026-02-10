from __future__ import annotations

import structlog

from jarvis.monitoring.metrics import MESSAGE_COUNT, TOOL_INVOCATION_COUNT

log = structlog.get_logger()


def collect_usage_stats() -> dict:
    """Read Prometheus counter values for channels and tools."""
    channels: dict[str, float] = {}
    tools: dict[str, float] = {}

    # Collect message counts by channel
    for metric in MESSAGE_COUNT.collect():
        for sample in metric.samples:
            if sample.name == "jarvis_messages_total":
                channel = sample.labels.get("channel", "unknown")
                direction = sample.labels.get("direction", "")
                if direction == "inbound":
                    channels[channel] = channels.get(channel, 0) + sample.value

    # Collect tool invocation counts
    for metric in TOOL_INVOCATION_COUNT.collect():
        for sample in metric.samples:
            if sample.name == "jarvis_tool_invocations_total":
                tool_name = sample.labels.get("tool_name", "unknown")
                tools[tool_name] = tools.get(tool_name, 0) + sample.value

    return {"channels": channels, "tools": tools}


def build_usage_summary(stats: dict) -> str:
    """Format stats into human-readable summary for memory block."""
    lines = []

    channels = stats.get("channels", {})
    if channels:
        sorted_channels = sorted(channels.items(), key=lambda x: x[1], reverse=True)
        top = sorted_channels[:3]
        channel_parts = [f"{name} ({int(count)})" for name, count in top]
        lines.append(f"Most active channels: {', '.join(channel_parts)}")

    tools = stats.get("tools", {})
    if tools:
        sorted_tools = sorted(tools.items(), key=lambda x: x[1], reverse=True)
        top = sorted_tools[:5]
        tool_parts = [f"{name} ({int(count)})" for name, count in top]
        lines.append(f"Most used tools: {', '.join(tool_parts)}")

    if not lines:
        return "No usage data collected yet."

    return "\n".join(lines)


async def update_human_block(
    letta_client, agent_id: str, summary: str,
) -> None:
    """Append usage insights to the human memory block."""
    page = letta_client.agents.blocks.list(agent_id=agent_id)
    blocks = page.items if hasattr(page, "items") else page
    human_block = None
    for block in blocks:
        if block.label == "human":
            human_block = block
            break

    if not human_block:
        log.warning("learning.no_human_block", agent_id=agent_id)
        return

    # Update or append USAGE PATTERNS section
    current = human_block.value
    marker = "\nUSAGE PATTERNS:"
    if marker in current:
        # Replace existing section
        before = current[: current.index(marker)]
        new_value = f"{before}{marker}\n{summary}"
    else:
        new_value = f"{current}{marker}\n{summary}"

    # Keep under 500 chars to avoid block size issues
    if len(new_value) > 2000:
        new_value = new_value[:2000]

    letta_client.blocks.update(
        block_id=human_block.id,
        value=new_value,
    )
    log.info("learning.updated_human_block", agent_id=agent_id)


async def run_learning_cycle(letta_client, agent_id: str) -> None:
    """Full learning cycle: collect → summarize → update."""
    stats = collect_usage_stats()
    summary = build_usage_summary(stats)
    if summary == "No usage data collected yet.":
        log.info("learning.skipped", reason="no data")
        return
    await update_human_block(letta_client, agent_id, summary)
