import postgresql_mcp.tools.connection 
import postgresql_mcp.tools.metadata  
import postgresql_mcp.tools.read  

from postgresql_mcp.server import mcp, configs

# Write tools only registered when ENABLE_WRITE_TOOLS=true
if configs.enable_write_tools:
    import postgresql_mcp.tools.create  
    import postgresql_mcp.tools.update  
    import postgresql_mcp.tools.delete  

def main():
    """Entry point for running the server."""
    mcp.run()

if __name__ == "__main__":
    main()
