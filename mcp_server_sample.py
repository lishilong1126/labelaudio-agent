import os
import asyncio
from dotenv import load_dotenv
# 调整导入路径
from fastmcp import Client, FastMCP
from fastmcp.client.transports import SSETransport
import json

transport = SSETransport(
    url="https://api.example.com/sse",
    headers={"Authorization": "Bearer token"}
)
client = Client(transport)

# 后续配置代码不变...
load_dotenv()

transport = SSETransport(
    url="https://dashscope.aliyuncs.com/api/v1/mcps/SpeechToText/sse",
    headers={"Authorization":os.getenv("DASHSCOPE_API_KEY")}
)

mcp_client = Client(transport)
async def call_tool(name: str):
    async with mcp_client:
        tools = await mcp_client.list_tools()
        for tool in tools:
            print(f"Tool: {tool.name}")
            print(f"Description: {tool.description}")
            if tool.inputSchema:
                 try:
                     formatted = json.dumps(tool.inputSchema, ensure_ascii=False, indent=2, default=str)
                 except Exception:
                     formatted = str(tool.inputSchema)
                 print("Parameters:")
                 print(formatted)
        # Access tags and other metadata
            if hasattr(tool, 'meta') and tool.meta:
                 fastmcp_meta = tool.meta.get('_fastmcp', {})
                 print(f"Tags: {fastmcp_meta.get('tags', [])}")
asyncio.run(call_tool("Ford"))