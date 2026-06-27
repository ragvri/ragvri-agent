# ragvri-agent

A coding agent built from scratch in Python — not to ship a product, but to **learn by building**.

The goal of this project was to understand how agentic coding assistants (like Claude Code, Cursor, etc.) actually work under the hood. Instead of reading about it, I built one step by step.

I used [pi](https://github.com/nicholasgriffintn/pi) (an AI coding agent) as a pair programming partner throughout. Every decision was discussed, every tradeoff was grappled with, and every feature was built with tests. This was deliberate learning — not vibe coding.

---

## What It Does

A terminal-based coding assistant that can:
- Chat with an LLM (MiMo v2.5, DeepSeek, or any litellm-supported provider)
- Call tools — calculator, Python executor, file read/write, shell commands, web fetching
- Connect to external MCP servers (e.g., GitHub's MCP server for repo/issue/PR operations)
- Use skills — the model decides when to activate a skill, no manual toggling
- Stream responses in real-time with thinking tokens visible

---

## How It Was Built

The project followed **tracer bullet development** — each phase delivered a working end-to-end slice before moving to the next. Every phase was test-driven.

| Phase | What We Built | Key Concept |
|-------|--------------|-------------|
| **1. Tracer Bullet** | Basic chat with an LLM | Chat agent = while loop + message history |
| **2. Tool Calling** | LLM can request tool executions | JSON Schema tool definitions, tool_call_id linking |
| **3. Specific Tools** | Code executor, file ops, shell | Concrete capabilities that make the agent useful |
| **4. MCP Integration** | Connect to external MCP servers | MCP transparency — external tools look like local ones to the LLM |
| **5. Skills System** | Model-managed skills | Skills catalog in system prompt, model calls `use_skill()` when needed |
| **6. Modern Agent** | Streaming, thinking tokens, status bar | Async event loop, Rich Live + Group for real-time terminal UI |

---

## Tech Stack

- **Python 3.11+**
- **litellm** — provider-agnostic LLM calls
- **rich** — terminal UI (streaming panels, status bar, markdown rendering)
- **mcp** — Model Context Protocol SDK
- **uv** — package manager
- **ruff** — linting and formatting
- **pytest** — 132 tests

---

## Running It

```bash
# Clone and set up
git clone https://github.com/ragvri/ragvri-agent.git
cd ragvri-agent
uv sync

# Set your API key
cp .env.example .env
# Edit .env with your MIMO_API_KEY

# Run
uv run python -m chatbot
```

### Try It Out

```
You: What is 42 * 17?
You: Read the file chatbot/core.py and explain how it works
You: Run `ls -la` in the current directory
You: /mcp @modelcontextprotocol/server-github   # connect GitHub MCP
You: Search for popular Python repos on GitHub
You: /skills                                      # see available skills
```

---

## Project Structure

```
chatbot/
├── __main__.py          # Entry point
├── cli.py               # Terminal UI + streaming + status bar
├── config.py            # Settings, API keys, model info
├── core.py              # ChatBot orchestrator (async)
├── llm.py               # litellm wrapper
├── mcp_client.py        # MCP protocol client
├── memory.py            # Conversation history
├── skill.py             # Skill loading + lookup
├── tool_registry.py     # Tool registration system
└── tools/               # Built-in tools
    ├── calculator.py
    ├── code_executor.py
    ├── datetime_tool.py
    ├── fetch_url.py
    ├── file_ops.py
    └── shell.py
skills/                  # Agent skills (SKILL.md standard)
tests/                   # 132 passing tests
```

---

## Key Design Decisions

| Decision | Why |
|----------|-----|
| Full async architecture | MCP sessions need a single event loop |
| Model-managed skills | Matches how modern agents work — model decides, not the user |
| `drop_params` + `allowed_openai_params` | Forces tool definitions through to providers litellm doesn't natively support |
| Streaming via `acompletion(stream=True)` | Real-time output, thinking tokens visible |
| Tracer bullet approach | Always had a working system at every stage |

---

## What I Learned

The full learning journal is in [`learning.md`](learning.md), but the biggest takeaways:

1. **An agent is just a loop.** Send messages to LLM, check if it wants a tool, execute it, repeat.
2. **MCP is just tool routing.** External tools get registered locally — the LLM never knows the difference.
3. **Async is non-negotiable** once you have MCP in the mix.
4. **Streaming is a translation layer.** Raw LLM events get renamed and routed to the UI.
5. **Model-managed skills are the modern pattern.** No `/activate` — the model reads the catalog and decides.

---

## License

Personal project — not licensed for distribution.
