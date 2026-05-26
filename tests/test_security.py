"""Unit tests for security module."""

import os
from pathlib import Path

from mcp_yield_shell.config import Config
from mcp_yield_shell.security import build_env, redact_text, resolve_cwd, validate_command


class TestValidateCommand:
    def test_no_rules_allows_all(self):
        config = Config()
        assert validate_command(config, "rm -rf /") is None

    def test_deny_regex_rejects(self, monkeypatch):
        monkeypatch.setenv("YIELD_SHELL_DENY_COMMAND_REGEX", r"rm\s+-rf")
        config = Config()
        error = validate_command(config, "rm -rf /")
        assert error is not None
        assert "denied" in error.lower()

    def test_deny_regex_allows_non_matching(self, monkeypatch):
        monkeypatch.setenv("YIELD_SHELL_DENY_COMMAND_REGEX", r"rm\s+-rf")
        config = Config()
        assert validate_command(config, "ls -la") is None

    def test_allow_regex_rejects_non_matching(self, monkeypatch):
        monkeypatch.setenv("YIELD_SHELL_ALLOW_COMMAND_REGEX", r"^git\s+")
        config = Config()
        error = validate_command(config, "ls -la")
        assert error is not None
        assert "not allowed" in error.lower()

    def test_allow_regex_allows_matching(self, monkeypatch):
        monkeypatch.setenv("YIELD_SHELL_ALLOW_COMMAND_REGEX", r"^git\s+")
        config = Config()
        assert validate_command(config, "git status") is None


class TestResolveCwd:
    def test_default_cwd(self):
        config = Config()
        path, error = resolve_cwd(config, None)
        assert error is None
        assert path == str(Path(os.getcwd()).resolve())

    def test_explicit_cwd(self):
        config = Config()
        path, error = resolve_cwd(config, "/tmp")
        assert error is None
        assert "/tmp" in path

    def test_cwd_under_allowed_root(self, monkeypatch):
        monkeypatch.setenv("YIELD_SHELL_ALLOWED_CWDS", "/tmp")
        config = Config()
        path, error = resolve_cwd(config, "/tmp")
        assert error is None

    def test_cwd_not_under_allowed_root(self, monkeypatch):
        monkeypatch.setenv("YIELD_SHELL_ALLOWED_CWDS", "/tmp")
        config = Config()
        path, error = resolve_cwd(config, "/etc")
        assert error is not None
        assert "not under allowed roots" in error


class TestBuildEnv:
    def test_overlay_merges(self):
        config = Config()
        env = build_env(config, {"MY_VAR": "hello"})
        assert env["MY_VAR"] == "hello"

    def test_overlay_overrides(self, monkeypatch):
        monkeypatch.setenv("PATH", "/usr/bin")
        config = Config()
        env = build_env(config, {"PATH": "/custom"})
        assert env["PATH"] == "/custom"

    def test_no_overlay_preserves_parent(self):
        config = Config()
        env = build_env(config, None)
        assert "PATH" in env


class TestRedactText:
    def test_redacts_matching_env_values(self, monkeypatch):
        monkeypatch.setenv("MY_SECRET", "secretvalue123")
        config = Config()
        result = redact_text(config, "output with secretvalue123 inside")
        assert "[REDACTED:MY_SECRET]" in result
        assert "secretvalue123" not in result

    def test_preserves_non_matching(self, monkeypatch):
        monkeypatch.setenv("MY_NORMAL_VAR", "normalvalue")
        config = Config()
        result = redact_text(config, "output with normalvalue inside")
        assert result == "output with normalvalue inside"

    def test_default_regex_matches_token(self):
        config = Config()
        assert config.redact_env_regex.search("API_TOKEN")
        assert config.redact_env_regex.search("PRIVATE_KEY")
