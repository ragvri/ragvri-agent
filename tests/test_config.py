"""Tests for config module."""

import os
from unittest.mock import patch

import pytest

from chatbot.config import Config


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_model(self):
        config = Config()
        assert config.model == "deepseek-chat"

    def test_default_max_history(self):
        config = Config()
        assert config.max_history == 50

    def test_default_system_prompt(self):
        config = Config()
        assert "helpful" in config.system_prompt.lower()


class TestConfigFromEnv:
    """Test loading config from environment variables."""

    def test_loads_deepseek_config(self):
        env = {
            "DEFAULT_MODEL": "deepseek-chat",
            "DEEPSEEK_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env):
            config = Config.from_env()
            assert config.model == "deepseek-chat"
            assert config.api_key == "test-key"
            assert "deepseek" in config.base_url

    def test_loads_mimo_config(self):
        with patch.dict(os.environ, {"DEFAULT_MODEL": "mimo-v2.5", "MIMO_API_KEY": "mimo-key"}):
            config = Config.from_env()
            assert config.model == "xiaomi_mimo/mimo-v2.5"  # Prefix added for litellm
            assert config.api_key == "mimo-key"

    def test_raises_on_missing_api_key(self):
        with patch.dict(os.environ, {"DEFAULT_MODEL": "deepseek-chat"}, clear=True):
            os.environ.pop("DEEPSEEK_API_KEY", None)
            with pytest.raises(ValueError, match="No API key"):
                Config.from_env()

    def test_defaults_to_deepseek(self):
        # Clear all env vars and don't load .env
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("DEFAULT_MODEL", None)
            os.environ.pop("DEEPSEEK_API_KEY", None)
            os.environ.pop("MIMO_API_KEY", None)
            # Patch load_dotenv to prevent .env file from loading
            with patch("chatbot.config.load_dotenv"), pytest.raises(ValueError):
                Config.from_env()
