"""Terminal user interface for the chatbot."""

import asyncio
import os

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from chatbot.core import ChatBot

console = Console()

BANNER = """
[bold cyan]🤖 Chatbot Agent[/bold cyan]
[dim]Type your messages below. Commands:[/dim]
[dim]  /quit    - Exit the chat[/dim]
[dim]  /reset   - Clear conversation history[/dim]
[dim]  /clear   - Clear the screen[/dim]
[dim]  /tools   - List available tools[/dim]
[dim]  /mcp     - Connect to MCP server[/dim]
"""


def run() -> None:
    """Run the chatbot in the terminal."""
    console.print(BANNER)

    bot = ChatBot()

    while True:
        try:
            # Get user input
            user_input = console.input("[bold green]You:[/bold green] ").strip()

            # Handle empty input
            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()

                if command in ("/quit", "/exit"):
                    console.print("[dim]Goodbye![/dim]")
                    break
                elif command == "/reset":
                    bot.reset()
                    console.print("[dim]Conversation reset.[/dim]")
                    continue
                elif command == "/clear":
                    console.clear()
                    console.print(BANNER)
                    continue
                elif command == "/tools":
                    # List available tools
                    tools = bot.get_all_tool_definitions()
                    if tools:
                        console.print("[bold]Available tools:[/bold]")
                        for t in tools:
                            name = t["function"]["name"]
                            desc = t["function"]["description"][:60]
                            console.print(f"  • [cyan]{name}[/cyan]: {desc}...")
                    else:
                        console.print("[dim]No tools available.[/dim]")
                    continue
                elif command == "/mcp":
                    # Connect to MCP server
                    if len(parts) < 2:
                        console.print("[yellow]Usage: /mcp <server_script.py>[/yellow]")
                        continue
                    server_script = parts[1]
                    console.print(f"[dim]Connecting to MCP server: {server_script}...[/dim]")
                    try:
                        # Pass environment variables for known servers
                        env = None
                        if "github" in server_script.lower():
                            github_token = os.environ.get("GITHUB_TOKEN")
                            if github_token:
                                env = {"GITHUB_TOKEN": github_token}
                                console.print("[dim]Using GITHUB_TOKEN from environment[/dim]")
                            else:
                                console.print("[yellow]Warning: GITHUB_TOKEN not set[/yellow]")
                        
                        tools = asyncio.run(bot.connect_mcp_server(server_script, env=env))
                        console.print(f"[green]Connected! Added {len(tools)} tools:[/green]")
                        for name in tools:
                            console.print(f"  • [cyan]{name}[/cyan]")
                    except Exception as e:
                        console.print(f"[red]Error connecting to MCP server: {e}[/red]")
                    continue
                else:
                    console.print(f"[yellow]Unknown command: {command}[/yellow]")
                    continue

            # Get response from bot
            with console.status("[dim]Thinking...[/dim]"):
                response = bot.send(user_input)

            # Display response as markdown
            console.print()
            console.print(Panel(Markdown(response), title="🤖 Assistant", border_style="cyan"))
            console.print()

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    run()
