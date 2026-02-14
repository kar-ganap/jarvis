from __future__ import annotations


class TestReadFile:
    def test_returns_content(self, tmp_path, monkeypatch):
        from jarvis.tools.file_ops import read_file

        monkeypatch.setenv("HOME", str(tmp_path))
        f = tmp_path / "test.txt"
        f.write_text("hello world")

        result = read_file(str(f))
        assert result == "hello world"

    def test_not_found(self, tmp_path, monkeypatch):
        from jarvis.tools.file_ops import read_file

        monkeypatch.setenv("HOME", str(tmp_path))
        result = read_file(str(tmp_path / "nonexistent_12345.txt"))
        assert "ERROR" in result
        assert "not found" in result.lower()

    def test_truncates_large_file(self, tmp_path, monkeypatch):
        from jarvis.tools.file_ops import read_file

        monkeypatch.setenv("HOME", str(tmp_path))
        f = tmp_path / "big.txt"
        content = "x" * 15000
        f.write_text(content)

        result = read_file(str(f))
        assert len(result) < 15000
        assert "TRUNCATED" in result
        assert "15000" in result


class TestWriteFile:
    def test_creates_file(self, tmp_path, monkeypatch):
        from jarvis.tools.file_ops import write_file

        monkeypatch.setenv("HOME", str(tmp_path))
        path = str(tmp_path / "out.txt")
        result = write_file(path, "hello")

        assert "OK" in result
        assert "5 chars" in result
        with open(path) as f:
            assert f.read() == "hello"

    def test_creates_parent_dirs(self, tmp_path, monkeypatch):
        from jarvis.tools.file_ops import write_file

        monkeypatch.setenv("HOME", str(tmp_path))
        path = str(tmp_path / "sub" / "dir" / "file.txt")
        result = write_file(path, "nested")

        assert "OK" in result
        with open(path) as f:
            assert f.read() == "nested"


class TestPathSandbox:
    def test_read_home_dir_ok(self, tmp_path, monkeypatch):
        from jarvis.tools.file_ops import read_file

        monkeypatch.setenv("HOME", str(tmp_path))
        (tmp_path / "test.txt").write_text("ok")
        result = read_file(str(tmp_path / "test.txt"))
        assert result == "ok"

    def test_read_outside_home_blocked(self, monkeypatch, tmp_path):
        from jarvis.tools.file_ops import read_file

        monkeypatch.setenv("HOME", str(tmp_path))
        result = read_file("/etc/passwd")
        assert "BLOCKED" in result

    def test_write_outside_home_blocked(self, monkeypatch, tmp_path):
        from jarvis.tools.file_ops import write_file

        monkeypatch.setenv("HOME", str(tmp_path))
        result = write_file("/etc/evil.txt", "pwned")
        assert "BLOCKED" in result

    def test_traversal_blocked(self, tmp_path, monkeypatch):
        from jarvis.tools.file_ops import read_file

        monkeypatch.setenv("HOME", str(tmp_path))
        result = read_file("../../etc/passwd")
        assert "BLOCKED" in result


class TestListDirectory:
    def test_lists_contents(self, tmp_path, monkeypatch):
        from jarvis.tools.file_ops import list_directory

        monkeypatch.setenv("HOME", str(tmp_path))
        (tmp_path / "file.txt").touch()
        (tmp_path / "subdir").mkdir()

        result = list_directory(str(tmp_path))
        assert "file.txt" in result
        assert "subdir/" in result

    def test_caps_at_100(self, tmp_path, monkeypatch):
        from jarvis.tools.file_ops import list_directory

        monkeypatch.setenv("HOME", str(tmp_path))
        for i in range(120):
            (tmp_path / f"file_{i:03d}.txt").touch()

        result = list_directory(str(tmp_path))
        assert "120 items" in result
        assert "and 20 more" in result
