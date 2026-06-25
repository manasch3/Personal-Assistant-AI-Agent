import sys

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from agent import get_response

console = Console()

# ---------------------------------------------------------------------------
# Main chat loop
# ---------------------------------------------------------------------------

def main() -> None:
    console.print()
    console.rule("[bold cyan]Kiro — Personal AI Assistant[/bold cyan]")
    console.print("  Type [bold green]exit[/bold green] or [bold green]quit[/bold green] to end the session.", justify="center")
    console.print()

    history = {"messages": []}

    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                console.print("\n[bold cyan]Goodbye![/bold cyan]\n")
                sys.exit(0)

            try:
                with console.status("[cyan]Kiro is thinking...[/cyan]", spinner="dots"):
                    result = get_response(user_input, history)

                console.print()
                
                # Print the reply beautifully using Rich's Markdown
                markdown_reply = Markdown(result["reply"])
                
                if result["tools"]:
                    tool_list = ", ".join(result["tools"])
                    console.print(Panel(
                        markdown_reply, 
                        title="[bold cyan]Kiro[/bold cyan]", 
                        title_align="left",
                        border_style="cyan", 
                        subtitle=f"[yellow]Tools used: {tool_list}[/yellow]", 
                        subtitle_align="right"
                    ))
                else:
                    console.print(Panel(
                        markdown_reply, 
                        title="[bold cyan]Kiro[/bold cyan]", 
                        title_align="left",
                        border_style="cyan"
                    ))
                
                console.print()

                # Only update history on a successful round-trip.
                history = result["history"]

            except Exception as exc:
                console.print(f"\n[bold yellow]  Something went wrong: {exc}[/bold yellow]")
                console.print("[bold yellow]  Conversation preserved — keep chatting.\n[/bold yellow]")

        except KeyboardInterrupt:
            console.print("\n[bold cyan]Goodbye![/bold cyan]\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
