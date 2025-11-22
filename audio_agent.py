"""
Audio Analysis Agent using Deep Agents Framework & MCP
======================================================
This agent uses the deep_agents framework and connects to an external 
MCP server (mcp-qwen-analyze-audio.py) to perform audio analysis.

It does NOT implement tools locally but fetches them via the Model Context Protocol.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, Optional, List

# Third-party imports
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import SSEConnection

# Load environment variables from .env file
load_dotenv()

# ==========================
# Configuration & Setup
# ==========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agent_execution.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 导入自定义回调处理器
from agent_logger import AgentExecutionLogger

# MCP Server Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/sse")

class Config:
    """Configuration management"""
    
    # LLM Configuration
    # 支持 OpenAI 或 兼容 OpenAI 协议的厂商（如火山引擎 Volcengine）
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o") # 如果用火山引擎，修改为如 "deepseek-v3-240615"
    LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL") # 火山引擎通常为 https://ark.cn-beijing.volces.com/api/v3
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.LLM_API_KEY:
            logger.warning("⚠️ LLM_API_KEY (or OPENAI_API_KEY) not found. Agent logic might fail.")
        return True

# ==========================
# Agent Logic
# ==========================

async def run_agent_interactive():
    """
    Main async entry point to run the agent.
    It connects to the MCP server, loads tools, and processes user input.
    """
    print("🎧 Audio Analysis Agent (MCP Client Mode)")
    print("=========================================")
    print(f"📡 Connecting to MCP Server at: {MCP_SERVER_URL}")
    
    # Configure LLM Environment for Deep Agents / LangChain
    if Config.LLM_API_KEY:
        os.environ["OPENAI_API_KEY"] = Config.LLM_API_KEY
    if Config.LLM_BASE_URL:
        os.environ["OPENAI_BASE_URL"] = Config.LLM_BASE_URL
        
    print(f"🧠 LLM Model: {Config.LLM_MODEL}")
    if Config.LLM_BASE_URL:
        print(f"🔗 LLM Base URL: {Config.LLM_BASE_URL}")
    
    # Initialize MCP Client
    client = MultiServerMCPClient({
        "audio_server": {
            "transport": "sse",
            "url": MCP_SERVER_URL
        }
    })
    
    try:
        # No explicit connect needed with new API, get_tools handles it?
        # Or maybe we need to wait for connection?
        # The error message said: tools = await client.get_tools()
        
        # Get tools converted to LangChain format
        tools = await client.get_tools()
        logger.info(f"🛠️  Loaded {len(tools)} tools from server: {[t.name for t in tools]}")
        
        if not tools:
            logger.error("❌ No tools found. Check server status.")
            # Close client if needed, though MultiServerMCPClient might not need explicit close if not used as context manager
            # But let's check if we need to close individual connections. 
            # The adapters library usually manages this.
            return

        # Create the Deep Agent
        # We need to create a ChatOpenAI instance with custom base_url for Volcengine
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL if Config.LLM_BASE_URL else None,
            temperature=0
        )
        
        logger.info("🎯 正在创建 Deep Agent...")
        logger.info(f"📊 可用工具: {[t.name for t in tools]}")
        
        agent = create_deep_agent(
            model=llm,
            tools=tools,
            system_prompt="""你是一个智能音频分析助手。
你连接到了一个先进的音频理解 MCP 服务器。
你的目标是利用可用的工具帮助用户分析音频文件。

请遵循以下规则：
1. 始终验证用户请求中是否提供了音频 URL。
2. 当用户请求一般性总结时，使用 'comprehensive_audio_analysis' 工具。
3. 当用户有具体需求（如“转录”、“说话人分析”）时，使用特定的工具（如 'transcribe_audio', 'analyze_speaker'）。
4. 清晰地输出最终结果。
"""
        )
        
        logger.info("✅ Agent 创建成功")
        
        # Get User Input
        if len(sys.argv) > 1:
            user_input = " ".join(sys.argv[1:])
        else:
            audio_url = input("\nEnter Audio URL: ").strip()
            if not audio_url:
                print("URL is required.")
                return
            task_desc = input("Enter Task Description: ").strip()
            user_input = f"Audio URL: {audio_url}\nTask: {task_desc}"
        
        print(f"\n🚀 Processing Request...\n")
        
        logger.info("=" * 80)
        logger.info("🚀 开始处理用户请求")
        logger.info(f"📝 用户输入: {user_input}")
        logger.info("=" * 80)
        
        # 创建日志记录器用于本次请求
        execution_logger = AgentExecutionLogger()
        
        # Invoke the agent
        response = await agent.ainvoke(
            {"messages": [("user", user_input)]},
            config={"callbacks": [execution_logger]}
        )
        
        logger.info("=" * 80)
        logger.info("✅ 请求处理完成")
        logger.info("=" * 80)
        
        print("\n✅ Agent Response:")
        if isinstance(response, dict) and "messages" in response:
            print(response["messages"][-1].content)
        else:
            print(response)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print("\n💡 Tip: Is the MCP server running? Run 'python mcp-qwen-analyze-audio.py' in another terminal.")
    finally:
        # Clean up connections if method exists
        if hasattr(client, "close"):
            await client.close()
        elif hasattr(client, "aclose"):
            await client.aclose()

if __name__ == "__main__":
    Config.validate()
    try:
        asyncio.run(run_agent_interactive())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
