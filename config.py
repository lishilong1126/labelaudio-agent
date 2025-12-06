"""
Configuration & Environment Setup
=================================
Centralized configuration for the LabelAudio Agent system.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/agent_execution.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# MCP Server URLs
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/sse")
MCP_PARAFORMER_URL = os.getenv("MCP_PARAFORMER_URL", "http://127.0.0.1:8001/sse")
MCP_LABELSTUDIO_URL = os.getenv("MCP_LABELSTUDIO_URL", "http://127.0.0.1:8002/sse")

class Config:
    """Configuration management"""
    
    # LLM Configuration
    # Supported: OpenAI or compatible (Volcengine, Deepseek)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o") 
    LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL")
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.LLM_API_KEY:
            logger.warning("⚠️ LLM_API_KEY (or OPENAI_API_KEY) not found. Agent logic might fail.")
        return True
