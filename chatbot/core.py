"""Core chat loop — where the magic happens."""

from chatbot.config import Config
from chatbot.llm import chat
from chatbot.memory import Memory


class ChatBot:
    """The main chatbot orchestrator.

    This class ties together:
    - Config (settings)
    - Memory (conversation history)
    - LLM (the brain)

    The flow is simple:
    1. User sends a message
    2. We add it to memory
    3. We send the full history to the LLM
    4. We get a response and add it to memory
    5. We return the response
    """

    def __init__(self, config: Config | None = None):
        self.config = config or Config.from_env()
        self.memory = Memory(
            system_prompt=self.config.system_prompt,
            max_messages=self.config.max_history,
        )

    def send(self, user_message: str) -> str:
        """Process a user message and return the assistant's response."""
        # Add user message to memory
        self.memory.add("user", user_message)

        # Get response from LLM
        response = chat(
            messages=self.memory.get_messages(),
            model=self.config.model,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )

        # Add assistant response to memory
        self.memory.add("assistant", response)

        return response

    def reset(self) -> None:
        """Clear conversation history."""
        self.memory.clear()
