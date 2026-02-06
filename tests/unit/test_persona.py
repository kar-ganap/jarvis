class TestBuildPersonaBlock:
    def test_default_name(self) -> None:
        from jarvis.agent.persona import build_persona_block

        text = build_persona_block()
        assert "Jarvis" in text

    def test_custom_name(self) -> None:
        from jarvis.agent.persona import build_persona_block

        text = build_persona_block(agent_name="Friday")
        assert "Friday" in text

    def test_not_empty(self) -> None:
        from jarvis.agent.persona import build_persona_block

        text = build_persona_block()
        assert len(text) > 100


class TestBuildHumanBlock:
    def test_default_name(self) -> None:
        from jarvis.agent.persona import build_human_block

        text = build_human_block()
        assert "User" in text

    def test_custom_name(self) -> None:
        from jarvis.agent.persona import build_human_block

        text = build_human_block(user_name="Kartik")
        assert "Kartik" in text

    def test_not_empty(self) -> None:
        from jarvis.agent.persona import build_human_block

        text = build_human_block()
        assert len(text) > 0
