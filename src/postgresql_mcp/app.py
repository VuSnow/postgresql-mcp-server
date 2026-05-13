from fastmcp import FastMCP

mcp = FastMCP(
    name="PostgreSQL MCP Server",
    instructions=(
        "You are a PostgreSQL assistant. Use the available tools to help users "
        "interact with their PostgreSQL databases — querying data, inspecting "
        "schema structure, and managing database operations."
    ),
)
