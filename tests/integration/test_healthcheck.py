def test_letta_server_reachable(letta_client) -> None:
    """Verify the Letta server is up and responding to API calls."""
    page = letta_client.agents.list(limit=1)
    # If we got here without exception, the server is reachable
    assert hasattr(page, "items")
