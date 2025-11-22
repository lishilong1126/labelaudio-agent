"""
Gradio UI for Audio Analysis Agent
==================================
提供一个友好的 Web 界面来测试和调试音频分析功能
"""

import os
import sys
import asyncio
import logging
import gradio as gr
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agent_execution.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 导入 Agent 相关模块
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from agent_logger import AgentExecutionLogger

# MCP Server 配置
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/sse")

class Config:
    """配置管理"""
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
    LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL")

# 全局变量存储 agent
agent = None
client = None

async def initialize_agent():
    """初始化 Agent"""
    global agent, client
    
    if agent is not None:
        return "✅ Agent 已经初始化"
    
    try:
        # 配置 LLM 环境
        if Config.LLM_API_KEY:
            os.environ["OPENAI_API_KEY"] = Config.LLM_API_KEY
        if Config.LLM_BASE_URL:
            os.environ["OPENAI_BASE_URL"] = Config.LLM_BASE_URL
        
        # 初始化 MCP Client
        client = MultiServerMCPClient({
            "audio_server": {
                "transport": "sse",
                "url": MCP_SERVER_URL
            }
        })
        
        # 获取工具
        tools = await client.get_tools()
        
        if not tools:
            return "❌ 错误: 无法从 MCP Server 获取工具。请确保 MCP Server 正在运行。"
        
        # 创建 LLM
        llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL if Config.LLM_BASE_URL else None,
            temperature=0
        )
        
        logger.info("🎯 正在创建 Deep Agent...")
        logger.info(f"📊 可用工具: {[t.name for t in tools]}")
        
        # 创建 Agent
        agent = create_deep_agent(
            model=llm,
            tools=tools,
            system_prompt="""你是一个智能音频分析助手。
你连接到了一个先进的音频理解 MCP 服务器。
你的目标是利用可用的工具帮助用户分析音频文件。

请遵循以下规则：
1. 始终验证用户请求中是否提供了音频 URL。
2. 当用户请求一般性总结时，使用 'comprehensive_audio_analysis' 工具。
3. 当用户有具体需求（如"转录"、"说话人分析"）时，使用特定的工具（如 'transcribe_audio', 'analyze_speaker'）。
4. 清晰地输出最终结果。
"""
        )
        
        logger.info("✅ Agent 创建成功")
        
        return f"✅ Agent 初始化成功！\n🛠️ 加载了 {len(tools)} 个工具: {[t.name for t in tools]}"
        
    except Exception as e:
        return f"❌ 初始化失败: {str(e)}\n\n💡 提示: 请确保 MCP Server 正在运行 (python mcp-qwen-analyze-audio.py)"

async def analyze_audio_async(audio_url: str, task_description: str):
    """异步分析音频"""
    global agent
    
    if not agent:
        init_msg = await initialize_agent()
        if "❌" in init_msg:
            return init_msg
    
    if not audio_url or not audio_url.strip():
        return "❌ 请提供音频 URL"
    
    if not task_description or not task_description.strip():
        return "❌ 请提供任务描述"
    
    try:
        user_input = f"Audio URL: {audio_url}\nTask: {task_description}"
        
        # 创建新的日志记录器实例
        execution_logger = AgentExecutionLogger()
        
        logger.info("=" * 80)
        logger.info("🚀 开始处理用户请求")
        logger.info(f"📝 音频 URL: {audio_url}")
        logger.info(f"📝 任务描述: {task_description}")
        logger.info("=" * 80)
        
        # 调用 Agent
        response = await agent.ainvoke(
            {"messages": [("user", user_input)]},
            config={"callbacks": [execution_logger]}
        )
        
        logger.info("=" * 80)
        logger.info("✅ 请求处理完成")
        logger.info("=" * 80)
        
        # 提取响应
        if isinstance(response, dict) and "messages" in response:
            result = response["messages"][-1].content
        else:
            result = str(response)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {str(e)}")
        return f"❌ 分析失败: {str(e)}"

def analyze_audio(audio_url: str, task_description: str):
    """同步包装器"""
    return asyncio.run(analyze_audio_async(audio_url, task_description))

def init_agent_sync():
    """同步初始化"""
    return asyncio.run(initialize_agent())

# 创建 Gradio 界面
with gr.Blocks(title="Audio Analysis Agent") as demo:
    gr.Markdown("""
    # 🎧 Audio Analysis Agent
    
    基于 Deep Agents + MCP 的智能音频分析系统
    
    **功能：**
    - 🎙️ 语音转文字
    - 👤 说话人分析
    - 🎵 音频事件检测
    - 🔍 关键词搜索
    - 📊 综合分析
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 🚀 快速开始")
            
            init_btn = gr.Button("🔌 初始化 Agent", variant="primary")
            init_output = gr.Textbox(label="初始化状态", lines=3, interactive=False)
            
            gr.Markdown("---")
            gr.Markdown("### 📝 音频分析")
            
            audio_url = gr.Textbox(
                label="音频 URL",
                placeholder="https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3",
                value="https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"
            )
            
            task_desc = gr.Textbox(
                label="任务描述",
                placeholder="例如: 转录这段音频 / 分析说话人特征 / 检测音频事件",
                value="转录这段音频"
            )
            
            analyze_btn = gr.Button("🎯 开始分析", variant="primary", size="lg")
            
        with gr.Column(scale=3):
            gr.Markdown("### 📊 分析结果")
            output = gr.Textbox(
                label="Agent 响应",
                lines=20,
                interactive=False
            )
    
    gr.Markdown("---")
    
    with gr.Accordion("📌 示例任务", open=False):
        gr.Examples(
            examples=[
                ["https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3", "转录这段音频"],
                ["https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3", "分析说话人的性别、年龄和情绪"],
                ["https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3", "检测音频中的所有事件"],
                ["https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3", "搜索关键词'阿里云'"],
                ["https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3", "对这段音频进行综合分析"],
            ],
            inputs=[audio_url, task_desc]
        )
    
    with gr.Accordion("ℹ️ 使用说明", open=False):
        gr.Markdown("""
        ### 使用步骤：
        
        1. **启动 MCP Server**（如果还没启动）：
           ```bash
           python mcp-qwen-analyze-audio.py
           ```
        
        2. **点击"初始化 Agent"** 按钮连接到 MCP Server
        
        3. **输入音频 URL** 和 **任务描述**
        
        4. **点击"开始分析"** 查看结果
        
        ### 配置信息：
        - **MCP Server**: `{}`
        - **LLM Model**: `{}`
        - **Base URL**: `{}`
        """.format(
            MCP_SERVER_URL,
            Config.LLM_MODEL,
            Config.LLM_BASE_URL or "默认 OpenAI"
        ))
    
    # 绑定事件
    init_btn.click(fn=init_agent_sync, outputs=init_output)
    analyze_btn.click(
        fn=analyze_audio,
        inputs=[audio_url, task_desc],
        outputs=output
    )

if __name__ == "__main__":
    print("🚀 启动 Gradio UI...")
    print(f"📡 MCP Server: {MCP_SERVER_URL}")
    print(f"🧠 LLM Model: {Config.LLM_MODEL}")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
