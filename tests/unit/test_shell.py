from __future__ import annotations


class TestExecuteShellCommand:
    def test_returns_stdout(self):
        from jarvis.tools.shell import execute_shell_command

        result = execute_shell_command("echo hello")
        assert "hello" in result
        assert "EXIT CODE: 0" in result

    def test_returns_stderr(self):
        from jarvis.tools.shell import execute_shell_command

        result = execute_shell_command("ls /nonexistent_path_12345")
        assert "STDERR:" in result
        assert "EXIT CODE:" in result
        # exit code should be non-zero
        assert "EXIT CODE: 0" not in result

    def test_filters_sensitive_env(self, monkeypatch):
        from jarvis.tools.shell import execute_shell_command

        monkeypatch.setenv("MY_API_KEY", "supersecret")
        monkeypatch.setenv("SAFE_VAR", "visible")

        result = execute_shell_command("env")
        assert "supersecret" not in result
        assert "visible" in result

    def test_timeout(self):
        from jarvis.tools.shell import execute_shell_command

        result = execute_shell_command("sleep 60")
        # Should return a timeout indication, not hang for 60s
        assert "timed out" in result.lower() or "timeout" in result.lower()

    def test_custom_workdir(self, tmp_path):
        from jarvis.tools.shell import execute_shell_command

        result = execute_shell_command("pwd", workdir=str(tmp_path))
        assert str(tmp_path) in result
