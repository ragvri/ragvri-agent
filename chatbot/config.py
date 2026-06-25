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

    # Token tracking
    context_window: int = 128000  # Default, will be updated from API
    max_output_tokens: int = 8192

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
            # Xiaomi MiMo - use xiaomi_mimo prefix for litellm
            if not model.startswith("xiaomi_mimo/"):
                model = f"xiaomi_mimo/{model}"
        else:
            api_key = os.getenv("OPENAI_API_KEY", "")
            base_url = "https://api.openai.com/v1"

        if not api_key:
            raise ValueError(f"No API key found for model '{model}'. Check your .env file.")

        config = cls(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

        # Try to get model info from litellm or API
        config._load_model_info()

        return config

    def _load_model_info(self) -> None:
        """Load model info (context window, max output) from litellm or API."""
        # First, try litellm's built-in model info
        try:
            import litellm

            info = litellm.get_model_info(self.model)
            if info.get("max_input_tokens"):
                self.context_window = info["max_input_tokens"]
            if info.get("max_output_tokens"):
                self.max_output_tokens = info["max_output_tokens"]
            return
        except Exception:
            pass

        # Second, try querying the provider's /v1/models endpoint
        try:
            import httpx

            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = httpx.get(f"{self.base_url}/models", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])

                # Find our model in the list
                model_id = self.model.split("/")[-1]
                for m in models:
                    m_id = m.get("id", "")
                    if m_id == model_id or m_id == self.model:
                        # Check for context_window field
                        if "context_window" in m:
                            self.context_window = m["context_window"]
                        elif "max_context_length" in m:
                            self.context_window = m["max_context_length"]
                        break
        except Exception:
            pass

        # Third, use well-known defaults for models we know
        known_models = {
            "mimo-v2.5-pro": (1_000_000, 128_000),
            "mimo-v2.5": (1_000_000, 128_000),
            "mimo-v2-pro": (1_000_000, 128_000),
            "mimo-v2-flash": (1_000_000, 128_000),
            "deepseek-chat": (131_072, 8_192),
            "deepseek-coder": (131_072, 8_192),
            "deepseek-reasoner": (131_072, 8_192),
            "gpt-4": (8_192, 4_096),
            "gpt-4-turbo": (128_000, 4_096),
            "gpt-4o": (128_000, 16_384),
            "gpt-4o-mini": (128_000, 16_384),
            "claude-3-opus": (200_000, 4_096),
            "claude-3-sonnet": (200_000, 4_096),
            "claude-3-haiku": (200_000, 4_096),
        }

        model_short = self.model.split("/")[-1] if "/" in self.model else self.model
        if model_short in known_models:
            self.context_window, self.max_output_tokens = known_models[model_short]
