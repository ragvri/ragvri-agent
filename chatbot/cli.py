"""Terminal user interface for the chatbot."""

import asyncio
import os
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

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
[dim]  /activate   - Activate a skill (e.g., /activate code-review)[/dim]
[dim]  /deactivate - Deactivate the current skill[/dim]
[dim]  /mcp        - Connect to MCP server[/dim]
"""


def handle_command(user_input: str, bot: ChatBot) -> bool:
    """Handle a slash command. Returns True if the command was handled.

    Args:
        user_input: The raw user input (e.g., "/activate code-review")
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
                desc = t["function"]["description"][:60]
                console.print(f"  • [cyan]{name}[/cyan]: {desc}...")
        else:
            console.print("[dim]No tools available.[/dim]")
        return True

    if command == "/skills":
        if not bot.skills:
            console.print("[dim]No skills available. Add skills to the skills/ directory.[/dim]")
            return True
        console.print("[bold]Available skills:[/bold]")
        for skill in bot.skills:
            is_active = bot.active_skill and bot.active_skill.name == skill.name
            active = " [green](active)[/green]" if is_active else ""
            console.print(f"  • [cyan]{skill.name}[/cyan]: {skill.description}{active}")
        return True

    if command == "/activate":
        if not arg:
            console.print("[yellow]Usage: /activate <skill-name>[/yellow]")
            return True
        if bot.activate_skill(arg) and bot.active_skill is not None:
            skill = bot.active_skill
            console.print(f"[green]Activated skill: {skill.name}[/green]")
            console.print(f"  [dim]{skill.description}[/dim]")
            if skill.allowed_tools:
                console.print(f"  [dim]Tools: {', '.join(skill.allowed_tools)}[/dim]")
            else:
                console.print("  [dim]Tools: all[/dim]")
        else:
            console.print(f"[red]Skill not found: {arg}[/red]")
            if bot.skills:
                available = ", ".join(s.name for s in bot.skills)
                console.print(f"  [dim]Available: {available}[/dim]")
        return True

    if command == "/deactivate":
        if bot.active_skill:
            name = bot.active_skill.name
            bot.deactivate_skill()
            console.print(f"[dim]Deactivated skill: {name}[/dim]")
        else:
            console.print("[dim]No skill is currently active.[/dim]")
        return True

    if command == "/mcp":
        # MCP is handled in the async loop — this is a passthrough
        return False

    console.print(f"[yellow]Unknown command: {command}[/yellow]")
    return True


async def run_async() -> None:
    """Run the chatbot asynchronously."""
    console.print(BANNER)

    bot = ChatBot(skills_dir=Path("skills"))

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
                    # MCP needs async handling
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        console.print("[yellow]Usage: /mcp <server_script>[/yellow]")
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

            # Get response from bot
            with console.status("[dim]Thinking...[/dim]"):
                response = await bot.send(user_input)

            # Display response as markdown
            console.print()
            console.print(Panel(Markdown(response), title="🤖 Assistant", border_style="cyan"))
            console.print()

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
