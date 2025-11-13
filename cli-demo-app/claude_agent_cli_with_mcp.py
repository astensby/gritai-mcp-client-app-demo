#!/usr/bin/env python3
"""
Interactive CLI with External MCP Server Integration

A demo CLI application that connects to external MCP servers via stdio.
Demonstrates integration with:
- Built-in Claude Agent tools (Read, Write, Grep, Glob)
- External MCP servers (filesystem, custom Python servers)

Prerequisites:
    npm install -g @modelcontextprotocol/server-filesystem
"""

import anyio
import sys
from pathlib import Path
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import FormattedText


# ANSI color codes for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'


# Custom prompt style
prompt_style = Style.from_dict({
    'prompt': '#00aa00 bold',
})


def print_banner():
    """Print welcome banner with MCP info"""
    banner = f"""
{Colors.CYAN}{'='*70}
{Colors.BOLD}  🤖 Claude Agent Interactive CLI + External MCP Server
{Colors.END}{Colors.CYAN}  Built with Claude Agent SDK
{Colors.MAGENTA}  🔌 Connected to external MCP server via stdio
{Colors.END}{Colors.CYAN}  Type /help for commands, /quit to exit
{'='*70}{Colors.END}
"""
    print(banner)


def print_help():
    """Print help information"""
    help_text = f"""
{Colors.YELLOW}Available Commands:{Colors.END}

  {Colors.GREEN}/help{Colors.END}       Show this help message
  {Colors.GREEN}/clear{Colors.END}      Clear conversation history and start fresh
  {Colors.GREEN}/quit{Colors.END}       Exit the CLI (or use Ctrl+C)
  {Colors.GREEN}/history{Colors.END}    Show conversation summary
  {Colors.GREEN}/tools{Colors.END}      List available tools (built-in + MCP)

{Colors.YELLOW}Tips:{Colors.END}
  • Claude has access to built-in tools (Read, Write, Grep, Glob)
  • {Colors.MAGENTA}PLUS external MCP servers:{Colors.END}
    - {Colors.MAGENTA}filesystem{Colors.END} - File operations (list_directory, read_file, etc.)
    - {Colors.MAGENTA}police-incidents{Colors.END} - Norwegian Police incidents API
  • Try asking: "What are the latest police incidents in Norway?"
  • Try asking: "List files in the current directory"
  • Try asking: "What tools do you have available?"
  • Use arrow keys to navigate command history
  • Press Ctrl+C to interrupt Claude mid-response
"""
    print(help_text)


def print_error(error_msg: str):
    """Print error message"""
    print(f"{Colors.RED}✗ Error: {error_msg}{Colors.END}")


def print_success(success_msg: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {success_msg}{Colors.END}")


def print_info(info_msg: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {info_msg}{Colors.END}")


def print_mcp_info(mcp_msg: str):
    """Print MCP-related message"""
    print(f"{Colors.MAGENTA}🔌 MCP: {mcp_msg}{Colors.END}")


async def handle_conversation(client: ClaudeSDKClient, user_input: str) -> bool:
    """
    Handle a conversation turn with Claude.

    Args:
        client: The Claude SDK client
        user_input: User's message

    Returns:
        bool: True if conversation should continue, False to exit
    """
    # Check for commands
    if user_input.startswith('/'):
        command = user_input.lower().strip()

        if command == '/help':
            print_help()
            return True

        elif command == '/quit' or command == '/exit':
            print_info("Goodbye! 👋")
            return False

        elif command == '/clear':
            print_info("Conversation cleared. Starting fresh!")
            return True

        elif command == '/history':
            print_info("Conversation history is maintained throughout this session")
            return True

        elif command == '/tools':
            print_info("Available tools:")
            print(f"  {Colors.GREEN}Built-in:{Colors.END} Read, Write, Grep, Glob, Bash")
            print(f"  {Colors.MAGENTA}MCP Servers:{Colors.END}")
            print(f"    • {Colors.MAGENTA}filesystem{Colors.END} - File operations (list_directory, read_file, etc.)")
            print(f"    • {Colors.MAGENTA}police-incidents{Colors.END} - Norwegian Police incidents API")
            print(f"        - latest_incidents(): Get 10 latest police incidents")
            print(f"        - incidents_by_municipality(municipality): Get incidents for specific municipality")
            print(f"\n  {Colors.CYAN}Tip:{Colors.END} Ask Claude 'What tools do you have?' for detailed descriptions")
            return True

        else:
            print_error(f"Unknown command: {command}")
            print_info("Type /help for available commands")
            return True

    # Send message to Claude
    try:
        await client.query(user_input)

        # Receive and display response
        print(f"\n{Colors.BLUE}Claude:{Colors.END} ", end="", flush=True)

        async for message in client.receive_response():
            # Handle different message types
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        # Text response
                        print(block.text, end="", flush=True)
                    elif hasattr(block, 'name'):
                        # Tool use
                        tool_name = block.name
                        # Highlight MCP tools differently
                        if tool_name.startswith('mcp__'):
                            print(f"\n{Colors.MAGENTA}[Using MCP tool: {tool_name}]{Colors.END}")
                        else:
                            print(f"\n{Colors.YELLOW}[Using tool: {tool_name}]{Colors.END}")

        print()  # Newline after response

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠ Interrupted by user{Colors.END}")

    except Exception as e:
        print_error(f"Conversation error: {e}")

    return True


def create_mcp_server_config():
    """
    Configure MCP servers for the CLI.
    
    Returns a dictionary mapping server names to their configurations.
    Tools will be exposed as: mcp__<server_name>__<tool_name>
    """
    # Get the project root directory (two levels up from this file)
    project_root = Path(__file__).parent.parent
    
    # Node.js filesystem server
    mcp_filesystem_server = {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(Path.cwd())
        ]
    }

    # Local Python MCP server - Norwegian Police Incidents API
    mcp_police_incidents_server = {
        "command": "python3",
        "args": [str(project_root / "demoserver" / "public_api_server.py")],
        "env": {
            "PYTHONUNBUFFERED": "1",
        }
    }

    return {
        "filesystem": mcp_filesystem_server,
        "police-incidents": mcp_police_incidents_server,
    }


async def interactive_cli():
    """
    Main interactive CLI loop with MCP server integration
    """
    # Setup prompt with history
    history_file = Path.home() / '.claude_agent_history'
    session = PromptSession(history=FileHistory(str(history_file)))

    options = ClaudeAgentOptions(
        system_prompt="""You are a helpful AI assistant in an interactive CLI.
        Be concise but informative. Format code with markdown.
        You have access to:
        - Built-in file tools (Read, Write, Grep, Glob)
        - MCP filesystem server (mcp__filesystem__*) - Standard file operations
        - MCP police-incidents server (mcp__police-incidents__*) - Norwegian Police incidents API
          * latest_incidents(): Get the 10 latest police incidents in Norway
          * incidents_by_municipality(municipality): Get incidents for a specific municipality

        Use the appropriate tools to help users. When asked about available tools,
        list all tools you have access to with their descriptions.""",
        max_turns=20,
        allowed_tools=['Read', 'Write', 'Grep', 'Glob'],
        cwd=str(Path.cwd()),
        mcp_servers=create_mcp_server_config(),
        permission_mode='bypassPermissions'
    )

    print_info("Connecting to Claude...")
    print_mcp_info("Starting external MCP server(s)...")

    try:
        async with ClaudeSDKClient(options=options) as client:
            print_success("Connected to Claude!")
            print_mcp_info("External MCP servers ready!")
            print_mcp_info("  • filesystem server (Node.js)")
            print_mcp_info("  • police-incidents server (Norwegian Police incidents API)")
            print_info("You can now use both built-in and MCP server tools.\n")

            while True:
                try:
                    # Get user input with enhanced prompt
                    user_input = await session.prompt_async(
                        FormattedText([
                            ('class:prompt', '\nYou: '),
                        ]),
                        style=prompt_style
                    )

                    # Skip empty input
                    if not user_input.strip():
                        continue

                    # Handle the conversation
                    should_continue = await handle_conversation(client, user_input)

                    if not should_continue:
                        break

                except KeyboardInterrupt:
                    # User pressed Ctrl+C
                    print(f"\n{Colors.YELLOW}Press Ctrl+C again to exit, or type /quit{Colors.END}")
                    continue

                except EOFError:
                    # End of input (Ctrl+D)
                    print_info("\nGoodbye! 👋")
                    break

    except Exception as e:
        print_error(f"Failed to initialize Claude or MCP servers: {e}")
        print_info("Make sure the MCP servers are installed and accessible:")
        print_info("  • Filesystem: npm install -g @modelcontextprotocol/server-filesystem")
        print_info("  • Police-incidents: Check that demoserver/public_api_server.py exists")
        return

    print_mcp_info("External MCP servers shut down cleanly")


async def run_with_startup_message():
    """
    Run CLI with optional startup message
    """
    print_banner()

    # Check for command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("Usage: python claude_agent_cli_with_mcp.py")
            print("\nStarts an interactive chat session with Claude Agent + External MCP Server.")
            print("\nPrerequisites:")
            print("  npm install -g @modelcontextprotocol/server-filesystem")
            print("\nOptions:")
            print("  -h, --help    Show this help message")
            return

    # Show help on first run
    first_run_marker = Path.home() / '.claude_agent_cli_mcp_first_run'
    if not first_run_marker.exists():
        print_help()
        first_run_marker.write_text("1")
        print_info("This help message won't show again. Use /help to see it anytime.\n")

    # Start interactive session
    await interactive_cli()


def main():
    """Entry point"""
    print("\n" + "█"*70)
    print("  🔌 EXTERNAL MCP SERVER INTEGRATION DEMO")
    print("  • Connects to stdio-based MCP servers")
    print("  • Active servers:")
    print("    - filesystem (Node.js)")
    print("    - police-incidents (Norwegian Police incidents API)")
    print("  • Automatic server lifecycle management")
    print("  • Combines built-in + external tools")
    print("█"*70 + "\n")

    try:
        anyio.run(run_with_startup_message)
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}Goodbye! 👋{Colors.END}")
    except Exception as e:
        print_error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
