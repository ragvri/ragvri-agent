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
| Basic chat | ✅ | LLM integration via litellm (Mimo/DeepSeek) |
| Tool calling | ✅ | LLM can request tool calls, we execute and return results |
| Built-in tools | ✅ | Calculator, datetime, Python executor, file read/write, shell |
| MCP integration | ✅ | Connect to external MCP servers (GitHub server working!) |
| Skills system | ✅ | Agent Skills standard (agentskills.io) — prompt + tools bundles |
| Pre-commit hooks | ✅ | Ruff lint + format on every commit |
| Learning journal | ✅ | Documented learnings in `learning.md` |

### Test Status: 113 passing

---

## 🛠️ Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Language | Python 3.11+ | User proficiency |
| LLM library | litellm | Provider-agnostic (works with Mimo, DeepSeek, OpenAI) |
| LLM provider | Mimo (mimo-v2.5) | User's primary provider |
| Package manager | uv | Fast, modern |
| Linter | ruff | Replaces flake8+black+isort |
| Type checker | ty | From Astral (ruff creators) |
| Terminal UI | rich | Beautiful CLI output |
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
│   ├── cli.py               # Terminal UI (async) + handle_command()
│   ├── config.py            # Settings, API keys from .env
│   ├── core.py              # ChatBot orchestrator (async)
│   ├── llm.py               # litellm wrapper with TypedDict
│   ├── mcp_client.py        # MCP protocol client
│   ├── memory.py            # Conversation history
│   ├── skill.py             # Skill dataclass + load_skills() + find_skill()
│   ├── tool_registry.py     # Tool registration system
│   └── tools/
│       ├── calculator.py    # Math expressions
│       ├── code_executor.py # Python code execution
│       ├── datetime_tool.py # Current date/time
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
├── tests/                   # 113 tests passing
├── learning.md              # User's learning journal
├── PRD.md                   # Product requirements document
├── README.md
├── pyproject.toml
├── .pre-commit-config.yaml  # Ruff lint + format hooks
└── .env                     # API keys (gitignored)
```

---

## 🔑 Key Learnings (from learning.md)

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

### 6. Skills — Ephemeral Application
The most important design pattern: **the system prompt in memory is never modified.** When `send()` runs, it copies memory, prepends skill instructions to the copy, sends to LLM, then discards the copy. This means:
- Deactivation is just `self.active_skill = None` — nothing to undo
- Multiple skills can be swapped without corrupting memory
- The base personality is always preserved
- This is the standard approach (pi, Claude Code, Agent Skills spec)

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
d07241e fix: MCP tool execution - async event loop issue
f2f6f5f feat: Support environment variables for MCP servers
9acc92e docs: Update learning journal with MCP transparency insight
6ceb190 refactor: Make Tool.function optional for MCP tools
c9b8da9 docs: Update learning journal with MCP details
9a8108e (dropped) fix: MCP tool execution - run async in new thread
a3e234c (dropped) fix: Improve CLI async handling for MCP
845e39d feat: Add filesystem MCP server
db5bb9b feat: Phase 4 - MCP Integration
...
2d59632 feat: Phase 1 - Tracer Bullet (Basic Chat)
```

---

## 🚀 Future Work

### Phase 5: Polish & Enhancements (Partially Complete)
- [x] Skills system (Agent Skills standard)
- [x] Pre-commit hooks (ruff lint + format)
- [ ] Streaming responses (real-time output)
- [ ] Persistent memory (SQLite/vector store)
- [ ] Configuration files (YAML/TOML)
- [ ] Better error handling
- [ ] Rate limiting for API calls

### Skills Enhancements
- [ ] Auto-discover skills from project and user directories (pi-style)
- [ ] Model-activated skills (LLM decides when to use a skill, not just slash commands)
- [ ] Skill descriptions in system prompt catalog (for model discovery)
- [ ] `/skills` command to show descriptions and active state
- [ ] More skills: refactor, test-writer, documentation

### Potential Enhancements
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
   export GITHUB_TOKEN=<your-token>
   uv run python -m chatbot
   ```

2. **Try the skills:**
   ```
   You: /skills
   You: /activate code-review
   You: Review chatbot/skill.py
   You: /deactivate
   ```

3. **Connect to GitHub MCP:**
   ```
   You: /mcp @modelcontextprotocol/server-github
   You: Search for popular Python repos
   ```

4. **Read the learning journal:**
   - `learning.md` — All key learnings documented

5. **Run tests:**
   ```bash
   uv run pytest -v
   ```

6. **Check code quality:**
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
| Tool.function optional | None for MCP | MCP tools execute via protocol |
| Skills format | Agent Skills standard (agentskills.io) | Same format as pi, Claude Code |
| Skills storage | Project-root `skills/` directory | User-facing content, not source code |
| Skill architecture | Functions + dataclass, no manager class | Simple, testable, follows KISS |
| System prompt | Ephemeral application (copy, don't modify) | Enables clean deactivation |
| allowed-tools | Filter tools, not just restrict LLM | LLM can't see tools it can't use |
| Pre-commit | ruff lint + format | Same tool in two contexts (auto + agent) |

---

*Document created: 2026-06-24*
*Last updated: 2026-06-25*
*Total commits: 15+*
*Tests passing: 113*
