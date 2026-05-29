"""Unit tests for configuration parsing."""

import os

from mcp_yieldshell.config import Config


class TestConfigDefaults:
    def test_default_cwd(self):
        config = Config()
        assert config.default_cwd == os.getcwd()

    def test_default_max_output_bytes(self):
        config = Config()
        assert config.max_output_bytes == 20000

    def test_default_max_processes(self):
        config = Config()
        assert config.max_processes == 50

    def test_default_yield_ms(self):
        config = Config()
        assert config.default_yield_ms == 5000

    def test_default_max_yield_ms(self):
        config = Config()
        assert config.max_yield_ms == 300000

    def test_default_timeout_ms(self):
        config = Config()
        assert config.default_timeout_ms == 0

    def test_empty_allowed_cwds(self):
        config = Config()
        assert config.allowed_cwd_roots == []

    def test_none_deny_regex(self):
        config = Config()
        assert config.deny_command_regex is None

    def test_none_allow_regex(self):
        config = Config()
        assert config.allow_command_regex is None

    def test_default_redact_regex(self):
        config = Config()
        assert config.redact_env_regex is not None
        assert config.redact_env_regex.search("MY_TOKEN")
        assert config.redact_env_regex.search("API_KEY")
        assert config.redact_env_regex.search("MY_SECRET")
        assert config.redact_env_regex.search("DB_PASSWORD")


class TestConfigFromEnv:
    def test_custom_max_output_bytes(self, monkeypatch):
        monkeypatch.setenv("YIELDSHELL_MAX_OUTPUT_BYTES", "5000")
        config = Config()
        assert config.max_output_bytes == 5000

    def test_custom_max_processes(self, monkeypatch):
        monkeypatch.setenv("YIELDSHELL_MAX_PROCESSES", "10")
        config = Config()
        assert config.max_processes == 10

    def test_custom_default_yield_ms(self, monkeypatch):
        monkeypatch.setenv("YIELDSHELL_DEFAULT_YIELD_MS", "2000")
        config = Config()
        assert config.default_yield_ms == 2000

    def test_deny_command_regex(self, monkeypatch):
        monkeypatch.setenv("YIELDSHELL_DENY_COMMAND_REGEX", r"rm\s+-rf")
        config = Config()
        assert config.deny_command_regex is not None
        assert config.deny_command_regex.search("rm -rf /")
        assert not config.deny_command_regex.search("ls -la")

    def test_allow_command_regex(self, monkeypatch):
        monkeypatch.setenv("YIELDSHELL_ALLOW_COMMAND_REGEX", r"^git\s+")
        config = Config()
        assert config.allow_command_regex is not None
        assert config.allow_command_regex.search("git status")
        assert not config.allow_command_regex.search("ls -la")

    def test_allowed_cwds(self, monkeypatch):
        monkeypatch.setenv("YIELDSHELL_ALLOWED_CWDS", "/tmp:/home")
        config = Config()
        assert len(config.allowed_cwd_roots) == 2

    def test_invalid_int_uses_default(self, monkeypatch):
        monkeypatch.setenv("YIELDSHELL_MAX_PROCESSES", "abc")
        config = Config()
        assert config.max_processes == 50
