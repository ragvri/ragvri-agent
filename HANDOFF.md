# Session Handoff Document

## Session Date: 2026-06-24 to 2026-06-25

---

## 🎯 Aim

**Teach the user how to build an agentic chatbot from scratch**, specifically a coding assistant similar to Claude Code.

The approach was:
- **Tracer bullet development** — build vertical slices, each one working end-to-end
- **Test-driven development (TDD)** — tests first, then implementation
- **Pair programming** — collaborative learning style
- **Learning opportunities** — exercises after each phase to solidify understanding

---

## 📊 What We Built

A fully functional agentic chatbot in Python with:

| Feature | Status | Description |
|---------|--------|-------------|
| Basic chat | ✅ | LLM integration via litellm (MiMo/DeepSeek) |
| Tool calling | ✅ | LLM can request tool calls, we execute and return results |
| Built-in tools | ✅ | Calculator, datetime, Python executor, file read/write, shell |
| Internet access | ✅ | `fetch_url` tool — fetches web pages via curl |
| MCP integration | ✅ | Connect to external MCP servers (GitHub server working!) |
| Skills system | ✅ | Model-managed skills (no activate/deactivate) |
| Streaming | ✅ | Real-time token-by-token output via litellm acompletion |
| Thinking tokens | ✅ | Shows model reasoning in dimmed panel above response |
| Status bar | ✅ | Model, directory, tokens used/available, current action |
| Dynamic model info | ✅ | Auto-discovers context window from litellm/API/defaults |
| Pre-commit hooks | ✅ | Ruff lint + format on every commit |
| Learning journal | ✅ | Documented learnings in `learning.md` |

### Test Status: 132 passing

---

## 🛠️ Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Language | Python 3.11+ | User proficiency |
| LLM library | litellm | Provider-agnostic (works with MiMo, DeepSeek, OpenAI) |
| LLM provider | MiMo v2.5 (xiaomi_mimo) | User's primary provider — 1M context window |
| Package manager | uv | Fast, modern |
| Linter | ruff | Replaces flake8+black+isort |
| Type checker | ty | From Astral (ruff creators) |
| Terminal UI | rich | Beautiful CLI output — Panel, Live, Group, Markdown, Table |
| MCP SDK | mcp (official) | Standard protocol |
| YAML parsing | pyyaml | For skill frontmatter |
| Pre-commit | pre-commit | Automated code quality |

---

## 📁 Project Structure

```
/Users/raghavjindal/code/chatbot/
├── chatbot/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli.py               # Terminal UI (async) + streaming + status bar
│   ├── config.py            # Settings, API keys, dynamic model info
│   ├── core.py              # ChatBot orchestrator (async, send + send_stream)
│   ├── llm.py               # litellm wrapper — chat() + chat_stream()
│   ├── mcp_client.py        # MCP protocol client
│   ├── memory.py            # Conversation history
│   ├── skill.py             # Skill dataclass + load_skills() + find_skill()
│   ├── tool_registry.py     # Tool registration system
│   └── tools/
│       ├── calculator.py    # Math expressions
│       ├── code_executor.py # Python code execution
│       ├── datetime_tool.py # Current date/time
│       ├── fetch_url.py     # Web page fetching (curl + HTML stripping)
│       ├── file_ops.py      # File read/write
│       ├── mcp_test_server.py # Example MCP server
│       └── shell.py         # Shell commands
├── skills/                  # Agent Skills (agentskills.io standard)
│   ├── code-review/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── lint.sh
│   ├── debugger/
│   │   └── SKILL.md
│   └── explainer/
│       └── SKILL.md
├── tests/                   # 132 tests passing
├── learning.md              # User's learning journal
├── PRD.md                   # Product requirements document
├── README.md
├── pyproject.toml
├── .pre-commit-config.yaml  # Ruff lint + format hooks
└── .env                     # API keys (gitignored)
```

---

## 🔑 Key Learnings

### 1. Chat Agent = While Loop + Message History
The LLM is stateless. We maintain a Python list of messages and send the full history each time.

### 2. Tool Calling Flow
- Register tools with name, description, parameters (JSON Schema)
- Send tool definitions to LLM with every message
- LLM decides whether to call a tool or respond directly
- If tool call: execute tool, send result back to LLM
- LLM formats the final response for the user

### 3. tool_call_id
Needed when the LLM calls the same tool multiple times with different arguments. Links each call to its specific result.

### 4. MCP Transparency
MCP tools get registered as local tools in our registry. The LLM doesn't know the difference — it just sees names and descriptions. The routing to external servers happens in `_execute_tool()`.

### 5. Async Event Loop Issue
MCP sessions are bound to a specific event loop. Can't use them across different loops/threads. Solution: make the entire ChatBot async.

### 6. Model-Managed Skills (New Pattern)
The most important design pattern from this session: **skills are model-managed, not user-activated.**

How it works:
- System prompt includes a catalog of available skills (name + description)
- Model decides when to use a skill → calls `use_skill(name)` tool
- Tool returns full SKILL.md instructions as a tool result
- Model follows those instructions for that turn
- No `/activate` or `/deactivate` needed

This is how modern coding agents (pi, Claude Code) work — the model decides what skills to use, not the user.

### 7. Streaming Architecture
Events flow through a translation layer:

```
LLM (delta.tool_calls, delta.content)
  → chat_stream (yields raw events: tool_call_start, text, thinking, usage)
    → send_stream (renames to: tool_start, text, thinking, usage)
      → CLI (updates status bar, renders Live display)
```

Key insight: **update data → re-render**. `status.set_action()` changes the string, `live.update()` redraws the screen.

### 8. Rich Live + Group Pattern
For persistent status bar with streaming content:
- `Group(content_panel, status_bar)` stacks renderables vertically
- `Live` context redraws the group on every `live.update()` call
- Status bar always visible at bottom, content streams above it

### 9. Token Usage in Streaming
Most providers don't include usage in streaming chunks. Solutions:
- `stream_options={"include_usage": True}` forces some providers to include it
- Fallback: check `response.usage` after stream ends
- Some providers (like MiMo) only report usage in the final chunk

### 10. Thinking/Reasoning Tokens
Models that support "deep thinking" (MiMo v2.5, DeepSeek-R1) return reasoning in:
- `delta.reasoning_content` (DeepSeek format)
- `delta.thinking` (other providers)

We check both fields and yield `{"type": "thinking", "content": ...}` events.

---

## 🧰 Skills Used (pi skills, not chatbot skills)

| Skill | When Used |
|-------|-----------|
| **grill-me** | Beginning — interviewed user about design decisions |
| **learning-opportunities** | After each phase — exercises to solidify understanding |
| **context-mode** | Throughout — for processing large outputs |

---

## 🔌 MCP Server Status

### Working: GitHub MCP Server
```bash
export GITHUB_TOKEN=<token>
uv run python -m chatbot

You: /mcp @modelcontextprotocol/server-github
You: Search for github/github-mcp-server
```

**26 tools available:** search_repositories, create_issue, get_file_contents, list_issues, create_pull_request, etc.

**Response time:** ~11 seconds (LLM + GitHub API)

### Available but not tested:
- `@modelcontextprotocol/server-brave-search` — Web search (needs API key)
- `@modelcontextprotocol/server-postgres` — Database queries (needs connection string)

---

## 📋 Git History

```
08d0a69 feat: Modern agent architecture - streaming, thinking, status bar
3fbc5e6 feat: Phase 5 - Skills system (Agent Skills standard)
c803538 docs: Add session handoff document
d07241e fix: MCP tool execution - async event loop issue
f2f6f5f feat: Support environment variables for MCP servers
...
2d59632 feat: Phase 1 - Tracer Bullet (Basic Chat)
```

---

## 🚀 Future Work

### Potential Enhancements
- [ ] Persistent memory (SQLite/vector store)
- [ ] Add more MCP servers (Brave Search, PostgreSQL)
- [ ] Implement RAG (retrieval-augmented generation)
- [ ] Add conversation export/import
- [ ] Build a web UI (Streamlit or FastAPI)
- [ ] Add authentication for multi-user support

### Code Quality
- [ ] Add integration tests for MCP flow
- [ ] Improve async cleanup (cosmetic MCP warnings)
- [ ] Add type stubs for MCP library

---

## 🎓 How to Continue Learning

1. **Run the chatbot:**
   ```bash
   export MIMO_API_KEY=<your-key>
   uv run python -m chatbot
   ```

2. **Try the skills:**
   ```
   You: /skills
   You: /skill code-review
   You: Review chatbot/skill.py
   ```

3. **Connect to GitHub MCP:**
   ```
   You: /mcp @modelcontextprotocol/server-github
   You: Search for popular Python repos
   ```

4. **Test streaming and thinking:**
   ```
   You: Explain how async/await works in Python
   (Watch the thinking panel appear above the response)
   ```

5. **Read the learning journal:**
   - `learning.md` — All key learnings documented

6. **Run tests:**
   ```bash
   uv run pytest -v
   ```

7. **Check code quality:**
   ```bash
   uv run ruff check .
   uv run ty check .
   ```

---

## 📝 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tracer bullet | Vertical slices | Always have working system |
| TDD | Tests first | Understand behavior before coding |
| litellm | Provider-agnostic | Works with any LLM |
| Async ChatBot | Full async | MCP tools need same event loop |
| Model-managed skills | use_skill() tool | Modern agent pattern (pi, Claude Code) |
| Skills catalog in system prompt | Auto-generated | Model sees all skills, decides what to use |
| No activate/deactivate | Model decides | Cleaner UX, matches modern agents |
| Streaming | acompletion + stream=True | Real-time output |
| Thinking tokens | Persist above response | User sees model reasoning |
| Status bar | Rich Group + Live | Persistent, updates in real-time |
| drop_params + allowed_openai_params | Force tools through | MiMo supports tools but litellm doesn't know |
| Dynamic model info | litellm DB → API → defaults | Correct context window for any provider |
| fetch_url | curl + HTML stripping | Simple internet access |

---

*Document created: 2026-06-24*
*Last updated: 2026-06-25*
*Total commits: 16*
*Tests passing: 132*
