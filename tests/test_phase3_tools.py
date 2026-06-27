"""Tests for Phase 3 tools: code execution and file operations."""

import os
import tempfile

from chatbot.tools.code_executor import python_executor_tool
from chatbot.tools.file_ops import file_editor_tool, file_reader_tool, file_writer_tool
from chatbot.tools.shell import shell_executor_tool


class TestPythonExecutor:
    """Test Python code execution."""

    def test_basic_execution(self):
        assert python_executor_tool.function is not None
        result = python_executor_tool.function("print(2 + 2)")
        assert "4" in result

    def test_multiline_code(self):
        code = """
x = 10
y = 20
print(x + y)
"""
        assert python_executor_tool.function is not None
        result = python_executor_tool.function(code)
        assert "30" in result

    def test_captures_output(self):
        code = "print('Hello, World!')"
        assert python_executor_tool.function is not None
        result = python_executor_tool.function(code)
        assert "Hello, World!" in result

    def test_handles_syntax_error(self):
        assert python_executor_tool.function is not None
        result = python_executor_tool.function("def foo(")
        assert "Error" in result or "SyntaxError" in result

    def test_handles_runtime_error(self):
        assert python_executor_tool.function is not None
        result = python_executor_tool.function("1/0")
        assert "Error" in result

    def test_returns_string(self):
        assert python_executor_tool.function is not None
        result = python_executor_tool.function("x = 42")
        assert isinstance(result, str)


class TestFileReader:
    """Test file reading."""

    def test_read_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            assert file_reader_tool.function is not None
            result = file_reader_tool.function(temp_path)
            assert "Hello, World!" in result
        finally:
            os.unlink(temp_path)

    def test_read_nonexistent_file(self):
        assert file_reader_tool.function is not None
        result = file_reader_tool.function("/nonexistent/file.txt")
        assert "Error" in result

    def test_returns_string(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            assert file_reader_tool.function is not None
            result = file_reader_tool.function(temp_path)
            assert isinstance(result, str)
        finally:
            os.unlink(temp_path)


class TestFileWriter:
    """Test file writing."""

    def test_write_new_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            assert file_writer_tool.function is not None
            file_writer_tool.function(path, "Hello, World!")
            assert os.path.exists(path)
            with open(path) as f:
                assert f.read() == "Hello, World!"

    def test_write_returns_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            assert file_writer_tool.function is not None
            result = file_writer_tool.function(path, "content")
            assert "success" in result.lower() or "written" in result.lower()

    def test_write_creates_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subdir", "test.txt")
            assert file_writer_tool.function is not None
            file_writer_tool.function(path, "content")
            assert os.path.exists(path)


class TestFileEditor:
    """Test file editing (targeted replacement)."""

    def test_edit_simple_replacement(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            assert file_editor_tool.function is not None
            result = file_editor_tool.function(temp_path, "World", "Python")
            assert "success" in result.lower() or "edited" in result.lower()
            with open(temp_path) as f:
                assert f.read() == "Hello, Python!"
        finally:
            os.unlink(temp_path)

    def test_edit_multiline_replacement(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo():\n    return 1\n")
            temp_path = f.name

        try:
            old = "def foo():\n    return 1"
            new = "def bar():\n    return 42"
            assert file_editor_tool.function is not None
            file_editor_tool.function(temp_path, old, new)
            with open(temp_path) as f:
                content = f.read()
            assert "def bar()" in content
            assert "return 42" in content
        finally:
            os.unlink(temp_path)

    def test_edit_nonexistent_file(self):
        assert file_editor_tool.function is not None
        result = file_editor_tool.function("/nonexistent/file.txt", "old", "new")
        assert "Error" in result

    def test_edit_text_not_found(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            assert file_editor_tool.function is not None
            result = file_editor_tool.function(temp_path, "not in file", "replacement")
            assert "Error" in result
            assert "not found" in result.lower()
        finally:
            os.unlink(temp_path)

    def test_edit_text_not_unique(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("foo and foo")
            temp_path = f.name

        try:
            assert file_editor_tool.function is not None
            result = file_editor_tool.function(temp_path, "foo", "bar")
            assert "Error" in result
            assert "2 times" in result or "appears" in result
        finally:
            os.unlink(temp_path)

    def test_edit_only_first_occurrence(self):
        """When text is unique, only that one occurrence is replaced."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("alpha beta gamma")
            temp_path = f.name

        try:
            assert file_editor_tool.function is not None
            file_editor_tool.function(temp_path, "beta", "BETA")
            with open(temp_path) as f:
                assert f.read() == "alpha BETA gamma"
        finally:
            os.unlink(temp_path)


class TestShellExecutor:
    """Test shell command execution."""

    def test_basic_command(self):
        assert shell_executor_tool.function is not None
        result = shell_executor_tool.function("echo hello")
        assert "hello" in result

    def test_captures_stdout(self):
        assert shell_executor_tool.function is not None
        result = shell_executor_tool.function("echo 'test output'")
        assert "test output" in result

    def test_handles_error_command(self):
        assert shell_executor_tool.function is not None
        result = shell_executor_tool.function("ls /nonexistent_directory")
        assert "Error" in result or "No such file" in result or "error" in result.lower()

    def test_returns_string(self):
        assert shell_executor_tool.function is not None
        result = shell_executor_tool.function("echo test")
        assert isinstance(result, str)
