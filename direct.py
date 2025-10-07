import asyncio
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("obsidianki-mcp-direct")

@mcp.tool()
async def generate_flashcards(
    notes: Optional[list] = None,
    cards: Optional[int] = None,
    query: Optional[str] = None,
    deck: Optional[str] = None,
    use_schema: bool = False
) -> str:
    """Generate flashcards using obsidianki.

    Args:
        notes: Note patterns to process (e.g., ["frontend/*", "docs/*.md:3"]). Supports glob patterns with optional sampling using :N suffix.
        cards: Number of flashcards to generate (number of cards to generate, recommend 3-6 if set)
        query: Optional query/topic for generating content from chat. Important for generating new content rather than from existing notes.
        deck: Optional deck name (defaults to user's default deck)
        use_schema: If true, uses existing cards from the deck to match specific card format (--use-schema flag)
    """
    try:
        # Build command
        cmd = ["obsidianki", "--mcp"]

        if cards is not None:
            cmd.extend(["--cards", str(cards)])

        if query:
            cmd.extend(["-q", query])

        if notes:
            for note_pattern in notes:
                cmd.extend(["--notes", note_pattern])

        if deck:
            cmd.extend(["--deck", deck])

        if use_schema:
            cmd.append("--use-schema")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
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
                if decoded:
                    output_lines.append(decoded)

        async def read_error():
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                decoded = line.decode().strip()
                if decoded:
                    output_lines.append(decoded)

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

if __name__ == "__main__":
    mcp.run()