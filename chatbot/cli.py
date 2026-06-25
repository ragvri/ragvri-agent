"""Terminal user interface for the chatbot with streaming and persistent status bar."""

import asyncio
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from chatbot.core import ChatBot

console = Console()

BANNER = """
[bold cyan]🤖 Chatbot Agent[/bold cyan]
[dim]Type your messages below. Commands:[/dim]
[dim]  /quit       - Exit the chat[/dim]
[dim]  /reset      - Clear conversation history[/dim]
[dim]  /clear      - Clear the screen[/dim]
[dim]  /tools      - List available tools[/dim]
[dim]  /skills     - List available skills[/dim]
[dim]  /skill      - Pick and use a skill[/dim]
[dim]  /mcp        - Show connected MCP servers[/dim]
[dim]  ESC         - Interrupt current response[/dim]
"""


class StatusBar:
    """Persistent status bar at the bottom of the terminal.

    Shows: model, directory, tokens used, current action.
    """

    def __init__(self, model: str, cwd: str, context_window: int):
        self.model = model
        self.cwd = cwd
        self.context_window = context_window
        self.tokens_used = 0
        self.current_action = "Ready"

    def update_tokens(self, prompt_tokens: int, completion_tokens: int):
        """Update token usage."""
        self.tokens_used += prompt_tokens + completion_tokens

    def set_action(self, action: str):
        """Update the current action."""
        self.current_action = action

    def render(self) -> Table:
        """Render the status bar as a Rich Table."""
        table = Table(
            show_header=False,
            show_edge=False,
            box=None,
            padding=(0, 1),
            expand=True,
        )
        table.add_column(style="cyan", ratio=1)
        table.add_column(style="green", ratio=1)
        table.add_column(style="yellow", ratio=1)
        table.add_column(style="magenta", ratio=1)

        # Shorten cwd for display
        display_cwd = self.cwd
        if len(display_cwd) > 30:
            display_cwd = "..." + display_cwd[-27:]

        # Format token display
        token_pct = (self.tokens_used / self.context_window * 100) if self.context_window else 0
        token_display = f"{self.tokens_used:,} / {self.context_window:,} ({token_pct:.0f}%)"

        table.add_row(
            f"🤖 {self.model}",
            f"📁 {display_cwd}",
            f"🪙 {token_display}",
            f"⚡ {self.current_action}",
        )

        return table


def handle_command(user_input: str, bot: ChatBot) -> bool:
    """Handle a slash command. Returns True if the command was handled.

    Args:
        user_input: The raw user input (e.g., "/skill code-review")
        bot: The ChatBot instance

    Returns:
        True if the command was recognized and handled
    """
    parts = user_input.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if command in ("/quit", "/exit"):
        console.print("[dim]Goodbye![/dim]")
        raise SystemExit(0)

    if command == "/reset":
        bot.reset()
        console.print("[dim]Conversation reset.[/dim]")
        return True

    if command == "/clear":
        console.clear()
        console.print(BANNER)
        return True

    if command == "/tools":
        tools = bot.get_all_tool_definitions()
        if tools:
            console.print("[bold]Available tools:[/bold]")
            for t in tools:
                name = t["function"]["name"]
                desc = t["function"]["description"][:80]
                console.print(f"  • [cyan]{name}[/cyan]: {desc}")
        else:
            console.print("[dim]No tools available.[/dim]")
        return True

    if command == "/skills":
        if not bot.skills:
            console.print("[dim]No skills available. Add skills to the skills/ directory.[/dim]")
            return True
        console.print("[bold]Available skills:[/bold]")
        for skill in bot.skills:
            console.print(f"  • [cyan]{skill.name}[/cyan]: {skill.description}")
        console.print()
        console.print("[dim]Use /skill <name> to pick a skill, or just ask.[/dim]")
        return True

    if command == "/skill":
        if not bot.skills:
            console.print("[dim]No skills available. Add skills to the skills/ directory.[/dim]")
            return True

        if arg:
            # Direct skill selection: /skill code-review
            skill = next((s for s in bot.skills if s.name == arg), None)
            if skill:
                console.print(f"[green]Using skill: {skill.name}[/green]")
                console.print(f"  [dim]{skill.description}[/dim]")
                return True
            else:
                console.print(f"[red]Skill not found: {arg}[/red]")
                available = ", ".join(s.name for s in bot.skills)
                console.print(f"  [dim]Available: {available}[/dim]")
                return True

        # Interactive skill selection
        console.print("[bold]Pick a skill:[/bold]")
        for i, skill in enumerate(bot.skills, 1):
            console.print(f"  [cyan]{i}[/cyan]. {skill.name}: {skill.description}")
        console.print()

        try:
            choice = console.input("[bold green]Enter number (or name):[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            return True

        if not choice:
            return True

        # Try as number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(bot.skills):
                skill = bot.skills[idx]
                console.print(f"[green]Using skill: {skill.name}[/green]")
                console.print(f"  [dim]{skill.description}[/dim]")
                return True
            else:
                console.print(f"[red]Invalid number: {choice}[/red]")
                return True
        except ValueError:
            pass

        # Try as name
        skill = next((s for s in bot.skills if s.name == choice), None)
        if skill:
            console.print(f"[green]Using skill: {skill.name}[/green]")
            console.print(f"  [dim]{skill.description}[/dim]")
            return True

        console.print(f"[red]Unknown skill: {choice}[/red]")
        return True

    if command == "/mcp":
        # Show connected MCP servers and their tools
        if not bot.mcp_client.is_connected:
            console.print("[dim]No MCP servers connected.[/dim]")
            console.print()
            console.print("[dim]Connect with: /mcp <server>[/dim]")
            console.print("[dim]Example: /mcp @modelcontextprotocol/server-github[/dim]")
            return True

        console.print("[bold]Connected MCP server:[/bold]")
        for name in bot.mcp_client.tool_names:
            tool = bot.mcp_client.get_tool(name)
            desc = tool.description[:60] if tool else ""
            console.print(f"  • [cyan]{name}[/cyan]: {desc}")
        return True

    console.print(f"[yellow]Unknown command: {command}[/yellow]")
    return True


async def run_streaming(bot: ChatBot, user_input: str, status: StatusBar) -> None:
    """Run a streaming response with persistent status bar.

    Args:
        bot: The ChatBot instance
        user_input: The user's message
        status: The persistent status bar
    """
    from rich.console import Group

    text_buffer = ""
    thinking_buffer = ""

    # Set up keyboard input for ESC detection
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    def check_interrupt():
        """Check if ESC was pressed (non-blocking)."""
        try:
            tty.setcbreak(fd)
            if select.select([sys.stdin], [], [], 0.0)[0]:
                ch = sys.stdin.read(1)
                if ch == "\x1b":  # ESC key
                    return True
        except Exception:
            pass
        return False

    def make_renderable(thinking=None, response=None):
        """Create a renderable with thinking, response, and status bar.

        Thinking appears in a dimmed section above the response.
        """
        parts = []
        if thinking:
            parts.append(
                Panel(
                    Markdown(thinking),
                    title="🧠 Thinking",
                    border_style="dim",
                    style="dim",
                )
            )
        if response:
            parts.append(
                Panel(
                    response,
                    title="🤖 Assistant",
                    border_style="cyan",
                )
            )
        elif not thinking:
            parts.append(
                Panel(
                    "[dim]Thinking...[/dim]",
                    title="🤖 Assistant",
                    border_style="dim",
                )
            )
        # Combine content with status bar
        return Group(*parts, status.render())

    try:
        # Set terminal to cbreak mode for immediate key detection
        tty.setcbreak(fd)

        with Live(
            make_renderable(),
            console=console,
            refresh_per_second=15,
            vertical_overflow="ellipsis",
        ) as live:
            # Start the stream
            async for event in bot.send_stream(user_input):
                # Check for ESC interrupt
                if check_interrupt():
                    status.set_action("⚠️ Interrupted")
                    live.update(
                        make_renderable(
                            thinking=thinking_buffer or None,
                            response=Markdown(text_buffer)
                            if text_buffer
                            else "[dim]Interrupted[/dim]",
                        )
                    )
                    break

                if event["type"] == "text":
                    text_buffer += event["content"]
                    status.set_action("💬 Responding")
                    live.update(
                        make_renderable(
                            thinking=thinking_buffer or None,
                            response=Markdown(text_buffer),
                        )
                    )

                elif event["type"] == "tool_start":
                    tool_name = event.get("name", "unknown")
                    status.set_action(f"🔧 {tool_name}")
                    live.update(
                        make_renderable(
                            thinking=thinking_buffer or None,
                            response=Markdown(text_buffer) if text_buffer else None,
                        )
                    )

                elif event["type"] == "tool_end":
                    tool_name = event.get("name", "unknown")
                    status.set_action(f"✅ {tool_name}")
                    live.update(
                        make_renderable(
                            thinking=thinking_buffer or None,
                            response=Markdown(text_buffer) if text_buffer else None,
                        )
                    )

                elif event["type"] == "thinking":
                    thinking_buffer += event.get("content", "")
                    status.set_action("🧠 Thinking")
                    live.update(make_renderable(thinking=thinking_buffer))

                elif event["type"] == "usage":
                    prompt_tokens = event.get("prompt_tokens", 0)
                    completion_tokens = event.get("completion_tokens", 0)
                    status.update_tokens(prompt_tokens, completion_tokens)
                    live.update(
                        make_renderable(
                            thinking=thinking_buffer or None,
                            response=Markdown(text_buffer) if text_buffer else None,
                        )
                    )

                elif event["type"] == "done":
                    final_content = event.get("content", text_buffer)
                    status.set_action("Ready")
                    if final_content:
                        live.update(
                            make_renderable(
                                thinking=thinking_buffer or None,
                                response=Markdown(final_content),
                            )
                        )
                    break

    finally:
        # Restore terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        status.set_action("Ready")


async def run_async() -> None:
    """Run the chatbot asynchronously."""
    console.print(BANNER)

    bot = ChatBot(skills_dir=Path("skills"))

    # Initialize status bar
    model_display = bot.config.model.replace("openai/", "").replace("deepseek/", "")
    status = StatusBar(
        model=model_display,
        cwd=str(Path.cwd()),
        context_window=bot.config.context_window,
    )

    # Render initial status bar
    console.print(status.render())

    while True:
        try:
            # Get user input (run in executor to avoid blocking)
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, lambda: console.input("[bold green]You:[/bold green] ").strip()
            )

            # Handle empty input
            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                command = user_input.split(maxsplit=1)[0].lower()
                if command == "/mcp":
                    # MCP connection needs async handling
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        # No argument — show connected servers
                        handle_command(user_input, bot)
                        continue
                    server_script = parts[1]
                    console.print(f"[dim]Connecting to MCP server: {server_script}...[/dim]")
                    try:
                        env = None
                        if "github" in server_script.lower():
                            github_token = os.environ.get("GITHUB_TOKEN")
                            if github_token:
                                env = {"GITHUB_TOKEN": github_token}
                                console.print("[dim]Using GITHUB_TOKEN from environment[/dim]")
                            else:
                                console.print("[yellow]Warning: GITHUB_TOKEN not set[/yellow]")
                        tools = await bot.connect_mcp_server(server_script, env=env)
                        console.print(f"[green]Connected! Added {len(tools)} tools:[/green]")
                        for name in tools:
                            console.print(f"  • [cyan]{name}[/cyan]")
                    except Exception as e:
                        console.print(f"[red]Error connecting to MCP server: {e}[/red]")
                    continue

                handle_command(user_input, bot)
                continue

            # Run streaming response with ESC interrupt
            await run_streaming(bot, user_input, status)

        except (KeyboardInterrupt, SystemExit):
            console.print("\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def run() -> None:
    """Run the chatbot in the terminal."""
    asyncio.run(run_async())


if __name__ == "__main__":
    run()
