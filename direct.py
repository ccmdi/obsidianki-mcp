import asyncio
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("obsidianki-mcp-direct")

@mcp.tool()
async def generate_flashcards(query: str) -> str:
    """Generate flashcards using obsidianki with the --mcp flag (skips approval prompts). Runs until completion or 180s timeout.

    Args:
        query: The query/topic for flashcard generation
    """
    try:
        # Run obsidianki with --mcp flag to skip approval
        cmd = ["obsidianki", "--mcp", "-q", query, "--cards", "1"]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE  # Provide stdin to prevent hanging on input
        )

        # Close stdin immediately so it doesn't wait for input
        process.stdin.close()

        output_lines = []

        async def read_output():
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded = line.decode().strip()
                output_lines.append(f"[STDOUT] {decoded}")

        async def read_error():
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                decoded = line.decode().strip()
                output_lines.append(f"[STDERR] {decoded}")

        # Start reading tasks
        read_task = asyncio.create_task(read_output())
        error_task = asyncio.create_task(read_error())

        # Wait for process to complete with timeout
        try:
            await asyncio.wait_for(process.wait(), timeout=60.0)
            await read_task
            await error_task

            result = "\n".join(output_lines) if output_lines else "No output"
            return f"{result}\n\nProcess completed with exit code: {process.returncode}"

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            result = "\n".join(output_lines) if output_lines else "No output captured"
            return f"TIMEOUT after 60s\n\nOutput before timeout:\n{result}"

    except Exception as e:
        # mcp.logger.error(f"Error running obsidianki: {e}")
        return f"Error: {str(e)}"
