# Chatbot Agent

An agentic chatbot built in Python with litellm.

## Tech Stack

- **Python 3.11+**
- **litellm** — Provider-agnostic LLM library
- **rich** — Beautiful terminal output
- **ruff** — Linting and formatting
- **ty** — Type checking
- **uv** — Package management

## Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run the chatbot
uv run python -m chatbot.cli
```

## Development

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run ty check .
```

## Project Structure

```
chatbot/
├── chatbot/
│   ├── __init__.py
│   ├── config.py      # Settings, API keys
│   ├── llm.py         # LLM wrapper
│   ├── memory.py      # Conversation memory
│   ├── core.py        # Chat loop
│   └── cli.py         # Terminal UI
├── pyproject.toml
├── .env
├── .gitignore
└── README.md
```

## Roadmap

See [PRD.md](PRD.md) for the full development plan.
