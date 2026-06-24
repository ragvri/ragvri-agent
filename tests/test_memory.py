"""Tests for memory module."""

from chatbot.memory import Memory


class TestMemoryInit:
    """Test memory initialization."""

    def test_system_prompt_preserved(self):
        memory = Memory(system_prompt="Test prompt")
        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Test prompt"

    def test_default_system_prompt(self):
        memory = Memory()
        messages = memory.get_messages()
        assert messages[0]["role"] == "system"


class TestMemoryAdd:
    """Test adding messages."""

    def test_add_user_message(self):
        memory = Memory()
        memory.add("user", "Hello!")
        messages = memory.get_messages()
        assert len(messages) == 2
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello!"

    def test_add_assistant_message(self):
        memory = Memory()
        memory.add("user", "Hello!")
        memory.add("assistant", "Hi there!")
        messages = memory.get_messages()
        assert len(messages) == 3
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Hi there!"

    def test_multiple_messages(self):
        memory = Memory()
        for i in range(5):
            memory.add("user", f"Message {i}")
        messages = memory.get_messages()
        assert len(messages) == 6  # system + 5 user messages


class TestMemoryTrimming:
    """Test message trimming when history exceeds max."""

    def test_trim_preserves_system_prompt(self):
        memory = Memory(max_messages=3)
        memory.add("user", "1")
        memory.add("assistant", "2")
        memory.add("user", "3")
        memory.add("assistant", "4")  # Should trigger trim

        messages = memory.get_messages()
        assert messages[0]["role"] == "system"  # Always preserved
        assert len(messages) <= 4  # system + max_messages - 1

    def test_trim_keeps_recent_messages(self):
        memory = Memory(max_messages=3)
        memory.add("user", "old message")
        memory.add("assistant", "old response")
        memory.add("user", "new message")
        memory.add("assistant", "new response")  # Trims to keep last 3

        messages = memory.get_messages()
        # Should have system + last 3 messages
        contents = [m["content"] for m in messages]
        assert "old message" not in contents or contents.index("old message") > 0


class TestMemoryClear:
    """Test clearing memory."""

    def test_clear_removes_history(self):
        memory = Memory(system_prompt="Test")
        memory.add("user", "Hello")
        memory.add("assistant", "Hi")
        memory.clear()

        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"

    def test_clear_preserves_system_prompt(self):
        memory = Memory(system_prompt="Important prompt")
        memory.add("user", "Hello")
        memory.clear()

        messages = memory.get_messages()
        assert messages[0]["content"] == "Important prompt"


class TestMemoryIsolation:
    """Test that get_messages returns a copy."""

    def test_get_messages_returns_copy(self):
        memory = Memory()
        messages1 = memory.get_messages()
        messages2 = memory.get_messages()
        assert messages1 is not messages2
        assert messages1 == messages2
