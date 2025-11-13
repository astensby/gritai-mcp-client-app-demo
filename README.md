# MCP Client App - Demo Project

A demo project showcasing different ways to integrate MCP (Model Context Protocol) servers in Client Host Applications. This project includes both a Gradio web interface and a CLI application.

## Features

- **Gradio Web App** - Interactive web interface with Anthropic API + FastMCP integration
- **CLI Application** - Command-line interface using Claude Agent SDK with external MCP servers
- **MCP Server Demo** - Example Python MCP server exposing Norwegian Police Incidents API
- Clean, minimal codebase suitable for learning and demonstrations

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Anthropic API key
- Node.js (for CLI demo with filesystem MCP server)

## Setup

### 1. Configure API Key

Copy the example environment file and add your Anthropic API key:

```bash
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. (Optional) Install Filesystem MCP Server

For the CLI demo, install the Node.js filesystem MCP server:

```bash
npm install -g @modelcontextprotocol/server-filesystem
```

## Demo Applications

### Gradio Web App

A web-based chat interface using FastMCP to connect to MCP servers.

**Run:**
```bash
cd gradio-demo-app
uv run python app.py
```

The Gradio interface will launch in your browser (typically at `http://127.0.0.1:7860`).

**Features:**
- Interactive chat interface
- FastMCP client integration
- Real-time tool calling with MCP servers

### CLI Application

An interactive command-line interface using Claude Agent SDK with external MCP server support.

**Run:**
```bash
cd cli-demo-app
uv run python claude_agent_cli_with_mcp.py
```

**Features:**
- Interactive CLI with command history
- Built-in Claude Agent tools (Read, Write, Grep, Glob)
- External MCP server integration (filesystem, custom Python servers)
- Automatic server lifecycle management

**CLI Commands:**
- `/help` - Show available commands
- `/tools` - List available tools
- `/clear` - Clear conversation history
- `/quit` - Exit the CLI

## Example Prompts

Try these prompts in either demo:

- "What are the latest police incidents in Norway?"
- "Show me police incidents in Oslo"
- "Are there any recent incidents in Bergen?"
- "What tools do you have available?"

## Project Structure

```
mcp-client-app-ndc/
├── gradio-demo-app/
│   └── app.py              # Gradio web app with FastMCP integration
├── cli-demo-app/
│   └── claude_agent_cli_with_mcp.py  # CLI app with Claude Agent SDK
├── demoserver/
│   └── public_api_server.py  # Example MCP server (Norwegian Police incidents)
├── pyproject.toml          # Project configuration with dependencies
├── requirements.txt        # Alternative dependency list
└── .env.example            # Environment variables template
```

## MCP Server

The project includes a demo MCP server at `demoserver/public_api_server.py` that connects to the Norwegian Police Incidents API.

**Exposed Tools:**
- `latest_incidents()` - Get 10 latest Norwegian police incidents
- `incidents_by_municipality(municipality)` - Get incidents for specific municipality (e.g., "Oslo", "Bergen")

Both demo applications connect to this local MCP server automatically.

## Technologies Used

- **Anthropic API** - Claude AI models
- **FastMCP** - FastMCP client library for MCP protocol
- **Claude Agent SDK** - SDK for building Claude-powered applications
- **Gradio** - Web UI framework
- **prompt-toolkit** - CLI interface library
- **python-dotenv** - Environment variable management
