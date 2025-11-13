import asyncio
import os
import gradio as gr
from anthropic import Anthropic
from fastmcp import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
# Example: Reference to the MCP server in the demoserver folder
MCP_SERVER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demoserver", "public_api_server.py")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SYSTEM_PROMPT = """You are Claudette, a friendly and helpful AI assistant with access to real-time Norwegian police incident data.
You're knowledgeable, approachable, and always happy to help users understand what's happening in Norway.
When discussing incidents, be informative but also empathetic and clear."""

# Validate API key
if not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY environment variable is not set. "
        "Please create a .env file with your Anthropic API key."
    )

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)


async def get_mcp_tools(client):
    """Fetch available tools from MCP server and convert to Anthropic format"""
    tools_list = await client.list_tools()

    anthropic_tools = []
    for tool in tools_list:
        anthropic_tool = {
            "name": tool.name,
            "description": tool.description,
        }

        # Add input schema if tool has parameters
        if tool.inputSchema and tool.inputSchema.get("properties"):
            anthropic_tool["input_schema"] = {
                "type": "object",
                "properties": tool.inputSchema["properties"],
                "required": tool.inputSchema.get("required", [])
            }
        else:
            anthropic_tool["input_schema"] = {"type": "object", "properties": {}}

        anthropic_tools.append(anthropic_tool)

    return anthropic_tools


async def call_mcp_tool(client, tool_name: str, tool_input: dict):
    """Execute tool on MCP server"""
    try:
        result = await client.call_tool(tool_name, tool_input)
        return result.content[0].text if result.content else ""
    except Exception as e:
        return f"Error executing tool {tool_name}: {str(e)}"


async def chat_with_mcp(message: str, history: list):
    """Handle chat with Anthropic + MCP tool integration"""
    max_iterations = 10  # Prevent infinite loops
    iteration_count = 0

    try:
        # Connect to MCP server
        async with Client(MCP_SERVER_PATH) as mcp_client:
            # Build conversation messages
            messages = []
            for user_msg, assistant_msg in history:
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": assistant_msg})
            messages.append({"role": "user", "content": message})

            # Get available MCP tools
            tools = await get_mcp_tools(mcp_client)

            # Agentic loop with safety limit
            while iteration_count < max_iterations:
                iteration_count += 1
                
                try:
                    response = anthropic_client.messages.create(
                        model="claude-sonnet-4-5-20250929",
                        max_tokens=4096,
                        system=SYSTEM_PROMPT,
                        tools=tools,
                        messages=messages
                    )
                except Exception as e:
                    return f"Error communicating with AI service: {str(e)}"

                # Check if we're done
                if response.stop_reason == "end_turn":
                    # Extract text response
                    text_response = ""
                    for block in response.content:
                        if block.type == "text":
                            text_response += block.text
                    return text_response

                # Handle tool use
                if response.stop_reason == "tool_use":
                    # Add assistant response to messages
                    messages.append({"role": "assistant", "content": response.content})

                    # Execute all tool calls
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_result = await call_mcp_tool(mcp_client, block.name, block.input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": tool_result
                            })

                    # Add tool results to messages
                    messages.append({"role": "user", "content": tool_results})
                else:
                    # Unexpected stop reason
                    return f"Unexpected response: {response.stop_reason}"
            
            # If we've exceeded max iterations
            return "Sorry, the conversation exceeded the maximum number of iterations. Please try rephrasing your question."
    
    except FileNotFoundError:
        return f"Error: MCP server not found at {MCP_SERVER_PATH}. Please ensure the server file exists."
    except Exception as e:
        return f"Error connecting to MCP server: {str(e)}"


def chat_wrapper(message: str, history: list):
    """Sync wrapper for async chat function"""
    if not message or not message.strip():
        return history
    
    try:
        response = asyncio.run(chat_with_mcp(message, history))
        history.append((message, response))
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        history.append((message, error_msg))
    
    return history

# Create Gradio interface
with gr.Blocks(title="MCP + Anthropic Demo") as demo:
    gr.Markdown("# AI Chat with MCP Integration")
    gr.Markdown("Chat with Claude powered by Anthropic API, with access to Norwegian Police Incidents via MCP server")

    chatbot = gr.Chatbot(height=500, type="tuples")
    msg = gr.Textbox(
        placeholder="Ask about police incidents in Norway...",
        container=False
    )

    msg.submit(chat_wrapper, [msg, chatbot], [chatbot]).then(
        lambda: "", None, [msg]
    )

if __name__ == "__main__":
    demo.launch()

