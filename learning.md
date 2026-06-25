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
Phase 4: + MCP integration (next)
Phase 5: + Skills & polish (future)
```

Each phase builds on the previous one, and we always have a working system.

---

*Last updated: 2026-06-24*
