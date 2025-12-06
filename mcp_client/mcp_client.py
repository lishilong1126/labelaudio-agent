"""
Core MCP Client Utility
=======================
Centralized MCP client management for the Multi-Agent System.
Connects to external MCP servers using SSE.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Default URLs
DEFAULT_AUDIO_SERVER_URL = "http://127.0.0.1:8000/sse"
DEFAULT_PARAFORMER_URL = "http://127.0.0.1:8001/sse"
DEFAULT_LABELSTUDIO_URL = "http://127.0.0.1:8002/sse"

def get_server_config() -> Dict[str, Dict[str, str]]:
    """Get server configuration from environment variables"""
    return {
        "audio_server": {
            "transport": "sse",
            "url": os.getenv("MCP_SERVER_URL", DEFAULT_AUDIO_SERVER_URL)
        },
        "paraformer_server": {
            "transport": "sse",
            "url": os.getenv("MCP_PARAFORMER_URL", DEFAULT_PARAFORMER_URL)
        },
        "label_studio_server": {
            "transport": "sse",
            "url": os.getenv("MCP_LABELSTUDIO_URL", DEFAULT_LABELSTUDIO_URL)
        }
    }

async def create_mcp_client(servers: Optional[List[str]] = None) -> MultiServerMCPClient:
    """
    Create a MultiServerMCPClient connected to specified servers.
    
    Args:
        servers: List of server names to connect to. 
                 Options: ['audio_server', 'paraformer_server', 'label_studio_server']
                 If None, connects to ALL available servers.
    """
    full_config = get_server_config()
    
    if servers:
        # Filter config to only requested servers
        config = {k: v for k, v in full_config.items() if k in servers}
    else:
        config = full_config
        
    logger.info(f"🔌 Connecting to MCP Servers: {list(config.keys())}")
    
    try:
        client = MultiServerMCPClient(config)
        # Verify connection by fetching tools immediately? 
        # Usually lazy, but let's just return the client.
        return client
    except Exception as e:
        logger.error(f"❌ Failed to create MCP client: {e}")
        raise e
