# Learning Journal

My learnings from building an agentic chatbot from scratch.

---

## 1. What is a Chat Agent?

A chat agent is basically a **while loop with an LLM** where we keep adding previous messages to the context of the LLM.

```
while True:
    user_input = get_input()
    messages.append({"role": "user", "content": user_input})
    
    response = llm.send(messages)
    messages.append({"role": "assistant", "content": response})
    
    display(response)
```

The LLM is **stateless** — it has no memory between calls. We provide all the context every single time by sending the full message history.

**Key insight:** The "memory" is just a Python list that we manage ourselves.

---

## 2. How Tool Calling Works

We register tools in a specific format with:
- **name** — What the tool is called
- **description** — What the tool does (the LLM reads this to decide when to use it)
- **parameters** — JSON Schema defining what arguments the tool accepts

For every single message, these tool definitions are added as part of the message sent to the LLM. The LLM then decides, depending on the context, whether it needs to call a tool or can respond directly.

### The Tool Calling Flow

```
User: "What is 15 * 23?"
    ↓
[User message] + [Tool definitions] → LLM
    ↓
LLM: "I should call calculator(expression='15*23')"
    ↓
We execute the tool → get result "345"
    ↓
[All messages] + [Tool result] → LLM
    ↓
LLM: "15 × 23 = 345" (formatted nicely for user)
```

**Key insight:** The LLM doesn't execute tools — it *requests* tool calls. We execute them and send the results back.

### Simple Tools We Built

| Tool | What it does |
|------|--------------|
| `calculator` | Evaluate math expressions |
| `get_current_datetime` | Get current date/time |
| `python_executor` | Run Python code in a subprocess |
| `file_reader` | Read file contents |
| `file_writer` | Write content to files |
| `shell_executor` | Run shell commands |

---

## 3. Why `tool_call_id` Matters

When the LLM calls multiple tools at once, we need to know which result belongs to which call. The `tool_call_id` links them:

```
LLM calls:
  - calculator (id="call_abc") → "345"
  - datetime (id="call_xyz") → "2026-06-24"

Without ID: "345" and "2026-06-24" — which is which?
With ID:    "call_abc → 345" and "call_xyz → 2026-06-24" — clear!
```

**Key insight:** The ID is needed when the same tool is called multiple times with different arguments.

---

## 4. Test-Driven Development (TDD)

We followed TDD throughout:

1. **Red:** Write a failing test first
2. **Green:** Write minimal code to make it pass
3. **Refactor:** Clean up the code

This ensures every module is testable by design and we understand expected behavior before implementing.

---

## 5. The Tracer Bullet Approach

Instead of building horizontally (all config, then all memory, then all LLM), we built **vertically** — each phase is a complete, working end-to-end feature.

```
Phase 1: Basic chat (working!)
Phase 2: + Tool calling (working!)
Phase 3: + Code/file tools (working!)
Phase 4: + MCP integration (working!)
Phase 5: + Skills & polish (future)
```

Each phase builds on the previous one, and we always have a working system.

---

## 6. MCP (Model Context Protocol)

MCP is a **standard protocol** for connecting tools to LLMs. Instead of building tools directly into the chatbot, we can connect to external MCP servers that provide tools.

### How MCP Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Chatbot   │ ──▶ │  MCP Client │ ──▶ │  MCP Server     │
│  (our app)  │     │             │     │ (npm package)   │
└─────────────┘     └─────────────┘     └─────────────────┘
                           │                     │
                           │  1. Connect (stdio) │
                           │ ──────────────────▶ │
                           │                     │
                           │  2. list_tools      │
                           │ ──────────────────▶ │
                           │                     │
                           │  3. [tools list]    │
                           │ ◀────────────────── │
                           │                     │
                           │  4. call_tool       │
                           │ ──────────────────▶ │
                           │                     │
                           │  5. [result]        │
                           │ ◀────────────────── │
```

### Key Insights

- MCP uses **async/await** for non-blocking I/O
- Servers communicate via **stdio** (stdin/stdout)
- Tools are discovered via `list_tools()` endpoint
- Tool execution returns `TextContent` objects
- The protocol **standardizes** tool format across ecosystems
- npm packages can be MCP servers (e.g., `@modelcontextprotocol/server-github`)

### MCP Tools Are Transparent to the LLM

**This was a key surprise:** MCP tools get registered as local tools in our registry. The LLM doesn't know the difference — it just sees names and descriptions.

```
┌─────────────────────────────────────────────────────────┐
│                    LLM's View                            │
│                                                         │
│  Available tools:                                       │
│  • calculator          (built-in)                       │
│  • get_current_datetime (built-in)                      │
│  • python_executor     (built-in)                       │
│  • greet               (MCP server)     ← Looks same!  │
│  • add                 (MCP server)     ← Looks same!  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               _execute_tool()                           │
│                                                         │
│  if mcp_client.get_tool(name):  # Is it MCP?           │
│      mcp_client.execute_tool()  # → External server     │
│  else:                                                  │
│      tool_registry.execute()    # → Local function      │
└─────────────────────────────────────────────────────────┘
```

**Key insight:** The routing to external servers happens transparently in `_execute_tool()`. The LLM just sees tools — it doesn't care where they run.

### When to Use MCP vs Built-in Tools

| Use MCP When | Use Built-in When |
|--------------|-------------------|
| External services (GitHub, Slack, Jira) | Simple operations (file read, calc) |
| Sharing tools across apps | Self-contained functionality |
| Community tools available | Performance critical |

---

## 7. Agent Skills — Giving Your Bot Specialized Knowledge

Skills are a way to give your chatbot **focused expertise** for specific tasks. Instead of one general-purpose assistant, you can activate specialized "modes" that change how the LLM behaves.

### What is a Skill?

A skill is a **directory** containing a `SKILL.md` file with:
- **YAML frontmatter** — metadata (name, description, allowed-tools)
- **Markdown body** — instructions that guide the LLM

```
skills/
├── code-review/
│   ├── SKILL.md
│   └── scripts/
│       └── lint.sh
├── debugger/
│   └── SKILL.md
└── explainer/
    └── SKILL.md
```

This follows the [Agent Skills standard](https://agentskills.io) — the same format used by pi, Claude Code, and other coding agents.

### How Skills Change LLM Behavior

When a skill is activated, two things change:

1. **System prompt** — Skill instructions are prepended to the base system prompt
2. **Available tools** — Filtered to only those listed in `allowed-tools`

```
Normal mode:
  System: "You are a helpful assistant."
  Tools: [calculator, datetime, python, shell, file_read, file_write]

Code-review mode:
  System: "You are a helpful assistant.\n\nYou are a senior code reviewer..."
  Tools: [shell_executor, file_reader]  ← Only these two!
```

**Key insight:** The `allowed-tools` field is from the Agent Skills spec. It's a space-separated list of tool names. If not specified, all tools are available.

### The Skill Loading Flow

```
1. At startup: ChatBot scans skills/ directory
2. For each subdirectory with SKILL.md:
   a. Parse YAML frontmatter → metadata
   b. Read markdown body → instructions
   c. Create Skill object
3. When user types /activate code-review:
   a. Find skill by name (linear search in memory, no file I/O)
   b. Set self.active_skill = skill (just a flag, nothing else)
4. When send() is called:
   a. Copy memory into a temporary list
   b. Prepend skill instructions to the COPY's system prompt
   c. Filter tools by allowed-tools
   d. Send the copy to the LLM
   e. Throw the copy away
```

### Ephemeral Application — The Key Design Pattern

This is the most important thing to understand about skills: **the system prompt in memory is never modified.**

When `send()` runs, it builds a temporary copy of messages and adds the skill instructions to the copy. The original memory stays clean:

```
Memory (permanent):     "You are a helpful AI assistant."

send() call 1:
  → builds copy:       "You are a helpful AI assistant.\n\nYou are a senior code reviewer..."
  → sends to LLM
  → copy discarded

send() call 2:
  → builds copy:       "You are a helpful AI assistant.\n\nYou are a senior code reviewer..."
  → sends to LLM
  → copy discarded
```

**Why this matters:** If we modified the original memory, deactivating the skill would be impossible — the original system prompt would be gone. By applying the skill ephemerally:
- Deactivation is just `self.active_skill = None` — nothing to undo
- Multiple skills can be swapped without corrupting memory
- The base personality is always preserved

This is the standard approach used by pi, Claude Code, and the [Agent Skills spec](https://agentskills.io). The spec calls this "progressive disclosure" — skill content is loaded into context on demand, not permanently stored.

### Slash Commands for Skills

Users interact with skills via slash commands:
- `/skills` — List available skills
- `/activate <name>` — Activate a skill
- `/deactivate` — Go back to normal mode

### Why Skills Matter

Skills demonstrate a key pattern in AI agents: **prompt engineering as configuration**. Instead of hard-coding behavior, you write markdown instructions that the LLM follows. This is:
- **Portable** — Works across different LLMs
- **Readable** — Non-engineers can edit skills
- **Composable** — Mix and match skills for different tasks

---

## 8. Pre-commit Hooks — Automated Code Quality

Pre-commit hooks run checks **before every git commit**. This catches issues early and keeps code consistent.

### How It Works

```
git commit -m "add feature"
    ↓
pre-commit hook runs:
  1. ruff check (lint)
  2. ruff format (formatting)
    ↓
If any check fails → commit is blocked
If all pass → commit succeeds
```

### Configuration (.pre-commit-config.yaml)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0
    hooks:
      - id: ruff        # lint
        args: [--fix]
      - id: ruff-format # format
```

**Key insight:** The same tool (ruff) can be used in two contexts:
1. **Pre-commit** — Automated, runs on every commit
2. **Code-review skill** — Agent-guided, the LLM decides when to run it

---

*Last updated: 2026-06-25*
