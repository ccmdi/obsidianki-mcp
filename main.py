import asyncio
import logging
from typing import Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("obsidianki-mcp")

app = Server("obsidianki-mcp")

# Store active subprocess
active_process: Optional[asyncio.subprocess.Process] = None
pending_output: list[str] = []

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="run_obsidianki",
            description="Run obsidianki command with arguments. Creates a persistent subprocess for the duration of flashcard creation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cards": {
                        "type": "integer",
                        "description": "Number of flashcards to create"
                    },
                    "additional_args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional command line arguments"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="respond_to_obsidianki",
            description="Send a response (Y/n) to an active obsidianki prompt",
            inputSchema={
                "type": "object",
                "properties": {
                    "response": {
                        "type": "string",
                        "description": "User response to send to obsidianki (e.g., 'Y', 'n', 'yes', 'no')"
                    }
                },
                "required": ["response"]
            }
        ),
        Tool(
            name="get_obsidianki_output",
            description="Get any pending output from the active obsidianki process",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="stop_obsidianki",
            description="Stop the active obsidianki process",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

async def read_stream(stream, output_list):
    """Read from stream and accumulate output"""
    while True:
        line = await stream.readline()
        if not line:
            break
        decoded = line.decode().strip()
        if decoded:
            output_list.append(decoded)
            logger.info(f"Output: {decoded}")

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    global active_process, pending_output

    if name == "run_obsidianki":
        if active_process and active_process.returncode is None:
            return [TextContent(
                type="text",
                text="Error: An obsidianki process is already running. Use stop_obsidianki first or respond_to_obsidianki to interact with it."
            )]

        # Build command
        cmd = ["obsidianki"]
        if "cards" in arguments:
            cmd.extend(["--cards", str(arguments["cards"])])
        if "additional_args" in arguments:
            cmd.extend(arguments["additional_args"])

        logger.info(f"Starting: {' '.join(cmd)}")

        # Start subprocess with stdin/stdout/stderr
        active_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        pending_output = []

        # Start background tasks to read output
        asyncio.create_task(read_stream(active_process.stdout, pending_output))
        asyncio.create_task(read_stream(active_process.stderr, pending_output))

        # Wait a moment for initial output
        await asyncio.sleep(0.5)

        output = "\n".join(pending_output)
        pending_output.clear()

        return [TextContent(
            type="text",
            text=f"Started obsidianki process (PID: {active_process.pid})\n\nOutput:\n{output}"
        )]

    elif name == "respond_to_obsidianki":
        if not active_process or active_process.returncode is not None:
            return [TextContent(
                type="text",
                text="Error: No active obsidianki process. Start one with run_obsidianki first."
            )]

        response = arguments["response"].strip()
        logger.info(f"Sending response: {response}")

        # Write response to stdin
        active_process.stdin.write(f"{response}\n".encode())
        await active_process.stdin.drain()

        # Wait for output
        await asyncio.sleep(0.5)

        output = "\n".join(pending_output)
        pending_output.clear()

        if active_process.returncode is not None:
            return [TextContent(
                type="text",
                text=f"Response sent. Process completed.\n\nOutput:\n{output}"
            )]

        return [TextContent(
            type="text",
            text=f"Response sent.\n\nOutput:\n{output}"
        )]

    elif name == "get_obsidianki_output":
        if not active_process:
            return [TextContent(
                type="text",
                text="No active obsidianki process."
            )]

        await asyncio.sleep(0.3)

        output = "\n".join(pending_output)
        pending_output.clear()

        status = "running" if active_process.returncode is None else f"completed (exit code: {active_process.returncode})"

        return [TextContent(
            type="text",
            text=f"Process status: {status}\n\nOutput:\n{output if output else '(no new output)'}"
        )]

    elif name == "stop_obsidianki":
        if not active_process or active_process.returncode is not None:
            return [TextContent(
                type="text",
                text="No active obsidianki process to stop."
            )]

        active_process.terminate()
        await active_process.wait()

        return [TextContent(
            type="text",
            text=f"Obsidianki process stopped (exit code: {active_process.returncode})"
        )]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
