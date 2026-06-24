"""Configuration management for the chatbot."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    """Chatbot configuration loaded from environment variables."""

    # LLM settings
    model: str = "deepseek-chat"
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"

    # Chat settings
    system_prompt: str = "You are a helpful AI assistant."
    max_history: int = 50

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables.

        Reads .env file and selects the appropriate API key
        based on the configured model.
        """
        load_dotenv()

        model = os.getenv("DEFAULT_MODEL", "deepseek-chat")

        # Select API key and base URL based on provider
        # litellm needs provider prefix: "deepseek/model" or "openai/model"
        if "deepseek" in model.lower():
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            base_url = "https://api.deepseek.com"
            # litellm native support - no prefix needed
        elif "mimo" in model.lower():
            api_key = os.getenv("MIMO_API_KEY", "")
            base_url = "https://api.xiaomimimo.com/v1"
            # OpenAI-compatible endpoint - add prefix
            if not model.startswith("openai/"):
                model = f"openai/{model}"
        else:
            api_key = os.getenv("OPENAI_API_KEY", "")
            base_url = "https://api.openai.com/v1"

        if not api_key:
            raise ValueError(f"No API key found for model '{model}'. Check your .env file.")

        return cls(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
