import asyncio
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("obsidianki-mcp-direct")

@mcp.tool()
async def generate_flashcards(query: str) -> str:
    """Generate flashcards using obsidianki with the --mcp flag (skips approval prompts). Runs until completion or 60s timeout.

    Args:
        query: The query/topic for flashcard generation
    """
    # mcp.logger.info(f"Running obsidianki with query: {query}")

    try:
        # Run obsidianki with --mcp flag to skip approval
        process = await asyncio.create_subprocess_exec(
            "obsidianki",
            "--mcp",
            "-q",
            query,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for completion with 60s timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60.0
            )

            output = stdout.decode().strip()
            error = stderr.decode().strip()

            result = []
            if output:
                result.append(f"Output:\n{output}")
            if error:
                result.append(f"Errors:\n{error}")

            result.append(f"\nExit code: {process.returncode}")

            return "\n\n".join(result) if result else "No output"

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return "Error: Process timed out after 60 seconds"

    except Exception as e:
        # mcp.logger.error(f"Error running obsidianki: {e}")
        return f"Error: {str(e)}"
