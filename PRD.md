# Chatbot Agent - Product Requirements Document

## Overview
Build an agentic chatbot in Python that evolves from a simple CLI chat interface to a full-featured coding assistant (similar to Claude Code).

## North Star
Build a terminal-based agentic coding assistant that can:
- Have natural conversations
- Execute code and work with files
- Use tools intelligently
- Eventually support MCP protocol and skills

---

## Development Approach

### Tracer Bullet (Vertical Slices)
Build vertical slices, each one working end-to-end. No horizontal layering — each feature is complete and testable before moving on.

### Test-Driven Development (TDD)
Write tests **first**, watch them fail, then write the minimum code to make them pass. This ensures:
- Every module is testable by design
- We understand expected behavior before implementing
- Refactoring is safe (tests catch regressions)
- Documentation through tests

**TDD Cycle:** Red → Green → Refactor
1. **Red:** Write a failing test
2. **Green:** Write minimal code to pass
3. **Refactor:** Clean up without breaking tests

---

## Design Decisions

### Decisions Made (And Why)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Language** | Python | User proficiency |
| **Development approach** | Tracer bullet + TDD | Vertical slices, testable from day one |
| **LLM abstraction** | litellm | Provider-agnostic, works with DeepSeek/Mimo/OpenAI |
| **LLM providers** | DeepSeek, Mimo | User has API keys for both |
| **Memory** | In-memory list | Simplest to understand, easy to upgrade later |
| **Interface** | Terminal CLI | Zero setup, focus on logic, can add web UI later |
| **Package manager** | uv | Fast, modern, replaces pip |
| **Linter/formatter** | ruff | Replaces flake8+black+isort, very fast |
| **Type checker** | ty | Modern, from Astral (ruff creators) |
| **Terminal UI** | rich | Beautiful output, markdown rendering |
| **Config** | python-dotenv + dataclass | Secure secrets, type-safe config |
| **Project structure** | Modular files | One responsibility per file, easy to navigate |

### Decisions Against (And Why)

| Rejected Alternative | Why We Didn't Choose It |
|---------------------|------------------------|
| **LangChain** | Too much "magic", harder to understand fundamentals. Better for Phase 4+ if needed. |
| **LlamaIndex** | Specialized for RAG, not general agent building. |
| **Raw `openai` library** | Provider-locked. litellm wraps it with same API style. |
| **Flask/FastAPI (Phase 1)** | Adds complexity. CLI is simpler for learning core concepts. |
| **Streamlit/Gradio** | Adds UI complexity. CLI keeps focus on chatbot logic. |
| **SQLite (Phase 1)** | Premature optimization. In-memory is simpler for learning. |
| **Sliding window memory** | Premature. Full history works fine for learning. We'll add this in Phase 2. |
| **pip + requirements.txt** | uv is faster and more reliable. Modern tooling. |
| **mypy** | ty is newer, faster, from the ruff team. |
| **Single-file script** | Hard to maintain and test. Modular is better for learning. |
| **Discord/Telegram bot** | Adds platform complexity. CLI is universal. |

---

## Phases

### Phase 1: Tracer Bullet (Basic Chat)
**Goal:** Get a working chatbot that remembers context

| Feature | Details |
|---------|---------|
| LLM Integration | litellm with DeepSeek/Mimo |
| Memory | In-memory message list |
| Interface | Terminal CLI |
| Tools | None |
| Testing | Unit tests for memory, config; integration test for LLM |

**Files:**
- `config.py` — Settings, API keys, model selection
- `llm.py` — LLM provider abstraction
- `memory.py` — Conversation memory
- `core.py` — Chat loop logic
- `cli.py` — Terminal UI

**Tests:**
- `test_config.py` — Config loads from env, validates required fields
- `test_memory.py` — Messages added correctly, trimming works, system prompt preserved
- `test_llm.py` — LLM returns response (mocked)
- `test_core.py` — ChatBot.send() orchestrates correctly (mocked LLM)

**Success criteria:**
- [x] All tests pass (28 total)
- [x] User can type messages and get responses
- [x] Chatbot remembers conversation history
- [x] Can switch between providers (DeepSeek/Mimo)

---

### Phase 2: Tool Calling
**Goal:** Agent can call external tools via function calling

| Feature | Details |
|---------|---------|
| Tool framework | litellm function calling |
| Initial tools | Calculator, datetime |
| Tool selection | LLM decides which tool to use |

**Tests:**
- Tool registration and discovery
- LLM requests correct tool
- Tool execution and result feeding

**Success criteria:**
- [x] All tests pass (50 total)
- [x] LLM can request tool calls
- [x] Tools execute and return results
- [x] Results are fed back to LLM

**Key learnings:**
- OpenAI function calling format (`type: function`, `function: {name, description, parameters}`)
- `tool_call_id` must be included when returning tool results
- Tool calling loop needs max iterations to prevent infinite loops

---

### Phase 3: Specific Tools
**Goal:** Agent can work with code and files

| Tool | Purpose |
|------|---------|
| Python executor | Run Python code |
| File reader | Read local files |
| File writer | Write/create files |
| Shell executor | Run shell commands |

**Tests:**
- Each tool executes correctly
- Error handling for failed executions
- Output capture and formatting

**Success criteria:**
- [x] All tests pass (68 total)
- [x] Can execute Python and return output
- [x] Can read and write files
- [x] Can run shell commands

**Key learnings:**
- Subprocess execution for code isolation
- File operations with pathlib
- Shell command execution with timeout
- Error handling for all operations

---

### Phase 4: MCP Integration
**Goal:** Tools follow the Model Context Protocol standard

| Feature | Details |
|---------|---------|
| MCP client | Connect to MCP servers |
| MCP servers | Filesystem, code execution |
| Standard protocol | Tool discovery and invocation |

**Tests:**
- MCP server connection
- Tool discovery
- Tool invocation via protocol

**Success criteria:**
- [ ] All tests pass
- [ ] Can connect to MCP servers
- [ ] Tools are discovered automatically
- [ ] Works with existing MCP ecosystem

---

### Phase 5: Skills & Polish
**Goal:** Pre-built capabilities and production features

| Feature | Details |
|---------|---------|
| Skills | Reusable tool bundles |
| Streaming | Real-time response streaming |
| Persistent memory | SQLite/vector store |
| Configuration | YAML/TOML config files |

**Tests:**
- Skill loading and execution
- Streaming response handling
- Persistent memory CRUD

---

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | User proficiency, modern features |
| Package manager | uv | Fast, modern, replaces pip |
| LLM library | litellm | Provider-agnostic |
| Providers | DeepSeek, Mimo | User has API keys |
| Config | python-dotenv | Secure API key storage |
| Terminal | rich | Beautiful CLI output |
| Linter/formatter | ruff | Fast, replaces flake8+black+isort |
| Type checker | ty | Modern, from Astral |
| Testing | pytest | Industry standard, great fixtures |

---

## Project Structure

```
chatbot/
├── chatbot/
│   ├── __init__.py
│   ├── __main__.py      # Entry point
│   ├── config.py        # Settings, API keys
│   ├── llm.py           # LLM wrapper
│   ├── memory.py        # Conversation memory
│   ├── core.py          # Chat loop
│   └── cli.py           # Terminal UI
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_memory.py
│   ├── test_llm.py
│   └── test_core.py
├── pyproject.toml
├── .env
├── .gitignore
├── PRD.md
└── README.md
```

---

## Learning Objectives

By completing this project, you will understand:
1. How LLM message formatting works
2. How conversation memory is managed
3. How function calling / tool use works
4. How agents make decisions about tool usage
5. How MCP protocol standardizes tool connections
6. How to build production-quality chat interfaces
7. How TDD drives clean, testable design

---

*Last updated: 2026-06-23*
