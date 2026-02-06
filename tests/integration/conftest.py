import pytest


def pytest_collection_modifyitems(config, items):
    """Auto-skip integration tests when Letta server is unreachable."""
    from jarvis.settings import load_settings

    try:
        from letta_client import Letta

        settings = load_settings()
        client = Letta(base_url=settings.letta.base_url, timeout=5)
        client.agents.list(limit=1)
    except Exception:
        skip_marker = pytest.mark.skip(reason="Letta server not reachable")
        for item in items:
            item.add_marker(skip_marker)


@pytest.fixture()
def letta_client():
    """Create a real Letta client connected to the running server."""
    from letta_client import Letta

    from jarvis.settings import load_settings

    settings = load_settings()
    return Letta(base_url=settings.letta.base_url)


@pytest.fixture()
def integration_settings():
    """Load real settings for integration tests."""
    from jarvis.settings import load_settings

    return load_settings()
