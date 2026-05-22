import postgresql_mcp.tools.connection 
import postgresql_mcp.tools.metadata  
import postgresql_mcp.tools.read  
from postgresql_mcp.server import mcp  

def main():
    """Entry point for running the server."""
    mcp.run()

if __name__ == "__main__":
    main()
