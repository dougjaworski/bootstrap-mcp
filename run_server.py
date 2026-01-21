"""Entry point for Bootstrap MCP Server."""

import logging
import sys

from src.server import initialize_server, mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    logger.info("Starting Bootstrap MCP Server initialization")

    # Initialize the server (clone repo, build index)
    if not initialize_server():
        logger.error("Server initialization failed")
        sys.exit(1)

    logger.info("Bootstrap MCP Server initialized successfully")
    logger.info("Server is ready to accept connections")


if __name__ == "__main__":
    main()
