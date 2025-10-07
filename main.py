import asyncio
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("obsidianki-mcp-direct")

@mcp.prompt()
def instructions() -> str:
    """Instructions for using the flashcard generation tool"""
    return """If the user does not specify a topic, default to generating flashcards about the user's notes (no query). If there is an active chat and the user says something like "can you generate flashcards about that", then use the query mode.
    
    When you successfully generate flashcards using the generate_flashcards tool, always:

1. Tell the user how many flashcards were created
2. Summarize what topics/content the flashcards cover
3. Let them know the flashcards have been added to their Anki deck

Example: "I've created 5 flashcards about Python list comprehensions and added them to your deck. The cards cover syntax, use cases, and common patterns."
"""

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
        notes: Note patterns to process (e.g., ["frontend/*", "docs/*.md:3"]). Supports glob patterns with optional sampling using :N suffix. You can leave this blank if the user does not specify.
        cards: Number of flashcards to generate (number of cards to generate, recommend 3-6 if set)
        query: Optional query/topic for generating content from chat. Important for generating new content rather than from existing notes.
        deck: Optional deck name (defaults to user's default deck)
        use_schema: If true, uses existing cards from the deck to match specific card format (--use-schema flag)
    """
    try:
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
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()