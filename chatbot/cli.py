"""Terminal user interface for the chatbot."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from chatbot.core import ChatBot

console = Console()

BANNER = """
[bold cyan]🤖 Chatbot Agent[/bold cyan]
[dim]Type your messages below. Commands:[/dim]
[dim]  /quit  - Exit the chat[/dim]
[dim]  /reset - Clear conversation history[/dim]
[dim]  /clear - Clear the screen[/dim]
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
                command = user_input.lower()
                if command == "/quit" or command == "/exit":
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
