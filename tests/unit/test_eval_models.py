from pathlib import Path


class TestEvalScenario:
    def test_parses_minimal_scenario(self) -> None:
        from jarvis.evals.models import EvalScenario

        s = EvalScenario(id="test", prompt="hello", expected_tools=["gmail_search"])
        assert s.id == "test"
        assert s.expected_tools == ["gmail_search"]
        assert s.tags == []
        assert s.quality_criteria == ""

    def test_parses_full_scenario(self) -> None:
        from jarvis.evals.models import EvalScenario

        s = EvalScenario(
            id="full",
            prompt="Search my email",
            expected_tools=["gmail_search"],
            expected_substring="found",
            quality_criteria="Relevant results",
            tags=["gmail", "search"],
        )
        assert s.expected_substring == "found"
        assert s.quality_criteria == "Relevant results"
        assert s.tags == ["gmail", "search"]


class TestEvalLoader:
    def test_loads_golden_set(self) -> None:
        from jarvis.evals.loader import load_scenarios

        scenarios = load_scenarios()
        assert len(scenarios) == 20
        ids = [s.id for s in scenarios]
        assert "gmail_search" in ids
        assert "chat_no_tools" in ids

    def test_filters_by_tag(self, tmp_path: Path) -> None:
        from jarvis.evals.loader import load_scenarios

        yaml_content = """
scenarios:
  - id: s1
    prompt: "test1"
    expected_tools: [tool_a]
    tags: [gmail]
  - id: s2
    prompt: "test2"
    expected_tools: [tool_b]
    tags: [calendar]
  - id: s3
    prompt: "test3"
    expected_tools: [tool_c]
    tags: [gmail, calendar]
"""
        p = tmp_path / "test_scenarios.yaml"
        p.write_text(yaml_content)

        result = load_scenarios(path=p, tags=["gmail"])
        assert len(result) == 2
        assert {s.id for s in result} == {"s1", "s3"}
