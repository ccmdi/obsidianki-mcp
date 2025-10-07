# Obsidianki MCP Server

MCP server for generating flashcards using [obsidianki](https://github.com/ccmdi/obsidianki).

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [obsidianki](https://github.com/ccmdi/obsidianki) installed and available in PATH, >= 0.7

## Installation

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "obsidianki-mcp": {
      "command": "uvx",
      "args": ["obsidianki-mcp"]
    }
  }
}
```

## Usage

The server provides one tool: `generate_flashcards`

### Parameters

- `notes` (optional): List of note patterns to process
  - Examples: `["frontend/*"]`, `["docs/*.md:3"]`
  - Supports glob patterns with optional sampling using `:N` suffix
- `cards` (optional): Number of flashcards to generate (recommend 3-6)
- `query` (optional): Query/topic for generating content from chat
- `deck` (optional): Deck name (defaults to your default deck)
- `use_schema` (optional): Use existing cards from deck to match format