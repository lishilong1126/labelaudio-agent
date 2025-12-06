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
# Logger is configured in config.py
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 导入 Agent 配置和创建函数
from agents.orchestrator import create_master_agent
from config import Config, MCP_SERVER_URL, MCP_PARAFORMER_URL
from mcp_client.agent_logger import AgentExecutionLogger

# Global variables
agent = None
clients = [] # Now a list of clients

async def initialize_agent():
    """Initialize the Multi-Agent System"""
    global agent, clients
    
    if agent is not None:
        return "✅ Master Agent already initialized"
    
    try:
        # Create Master Agent (which creates sub-agents)
        agent, clients = await create_master_agent()
        
        if not agent:
            return "❌ Error: Could not create Master Agent."
            
        return f"✅ Master Agent Initialized! System ready with Audio & Annotation specialists."
        
    except Exception as e:
        return f"❌ Initialization Failed: {str(e)}"

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

async def import_to_label_studio_async(audio_url: str, agent_output: str):
    """异步导入到 Label Studio
    
    Args:
        audio_url: 音频文件 URL
        agent_output: Audio Agent 的分析结果（需要从中提取转写文本）
    """
    if not audio_url or not audio_url.strip():
        return "❌ 请提供音频 URL"
    
    if not agent_output or not agent_output.strip():
        return "❌ 请先进行音频分析"
    
    # 从 agent_output 中提取转写文本
    transcription = extract_transcription(agent_output)
    
    if not transcription:
        return "❌ 无法从分析结果中提取转写文本"
        
    try:
        logger.info("=" * 80)
        logger.info("🚀 开始导入到 Label Studio")
        logger.info(f"📝 音频 URL: {audio_url}")
        logger.info(f"📝 提取的转写文本: {transcription}")
        
        # Prepare task for Master Agent
        task = f"Create a new Label Studio project for this audio ({audio_url}) and import the following transcription: {transcription}"
        
        logger.info(f"📤 Sending import task to Master Agent: {task}")
        
        # Determine which agent to use (Master Agent)
        if not agent:
             await initialize_agent()
             
        response = await agent.ainvoke({"messages": [("user", task)]})
        result = response["messages"][-1].content
        
        logger.info("✅ 导入完成")
        logger.info("=" * 80)
        return result
    except Exception as e:
        logger.error(f"❌ 导入失败: {str(e)}")
        return f"❌ 导入失败: {str(e)}"

def extract_transcription(agent_output: str) -> str:
    """从 Agent 输出中提取纯转写文本
    
    支持多种输出格式的解析
    """
    import re
    
    # 尝试从常见格式中提取
    # 格式1: "完整文本：" 或 "转写文本："后的引号内容
    patterns = [
        r'["\u201c\u300c]([^"\u201d\u300d]+)["\u201d\u300d]',  # 各种引号格式
        r'完整文本[：:]\s*[`\*]*([^`\*\n]+)[`\*]*',
        r'转写文本[：:]\s*[`\*]*([^`\*\n]+)[`\*]*',
        r'转录结果[：:]\s*[`\*]*([^`\*\n]+)[`\*]*',
        r'文本[：:]\s*[`\*]*([^`\*\n]+)[`\*]*',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, agent_output)
        if match:
            text = match.group(1).strip()
            # 清理 markdown 格式
            text = re.sub(r'[`\*\n]', '', text).strip()
            if text and len(text) > 1:  # 避免匹配到单个字符
                return text
    
    # 如果没有匹配到，尝试查找代码块中的内容
    code_block_match = re.search(r'```\s*\n?([^`]+)\n?```', agent_output)
    if code_block_match:
        text = code_block_match.group(1).strip()
        # 只取第一行（可能是转写结果）
        first_line = text.split('\n')[0].strip()
        if first_line and not first_line.startswith('#'):
            return first_line
    
    # 如果输出很短，可能本身就是转写结果
    if len(agent_output) < 200 and not agent_output.startswith('#'):
        return agent_output.strip()
    
    return ""

def import_to_label_studio(audio_url: str, transcription: str):
    """同步导入包装器"""
    return asyncio.run(import_to_label_studio_async(audio_url, transcription))


async def process_pipeline_async(audio_url: str, project_title: str):
    """
    一键全流程处理：音频分析 -> 项目创建 -> 数据导入
    """
    global agent
    
    if not agent:
        init_msg = await initialize_agent()
        if "❌" in init_msg:
            return init_msg
            
    if not audio_url or not audio_url.strip():
        return "❌ 请提供音频 URL"
        
    if not project_title or not project_title.strip():
        project_title = f"Project_{os.urandom(4).hex()}"
        
    try:
        # Construct a holistic task prompt
        task_prompt = f"""
        Please perform a COMPLETE end-to-end processing pipeline for this audio:
        Audio URL: {audio_url}
        
        Steps:
        1. Analyze the audio using Paraformer (for transcription & diarization) and Qwen (for event detection).
        2. Create a NEW Label Studio project named '{project_title}' using the 'Super Audio Template'.
        3. Import the analysis results into this new project.
        
        Execute all steps and report the final result.
        """
        
        execution_logger = AgentExecutionLogger()
        logger.info(f"🚀 Starting Full Pipeline for: {project_title}")
        
        response = await agent.ainvoke(
            {"messages": [("user", task_prompt)]},
            config={"callbacks": [execution_logger]}
        )
        
        if isinstance(response, dict) and "messages" in response:
            result = response["messages"][-1].content
        else:
            result = str(response)
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        return f"❌ Pipeline failed: {e}"

def process_pipeline(audio_url: str, project_title: str):
    return asyncio.run(process_pipeline_async(audio_url, project_title))

# 创建 Gradio 界面
with gr.Blocks(title="Audio Analysis Agent") as demo:
    gr.Markdown("""
    # 🎧 Audio Analysis Agent (End-to-End)
    
    **智能语音标注系统**：输入音频链接，一键完成转写、说话人分离、事件检测并导入 Label Studio。
    """)
    
    with gr.Tabs():
        # --- Tab 1: One-Click Pipeline (New Refactor) ---
        with gr.TabItem("🚀 一键全流程 (One-Click Pipeline)"):
            gr.Markdown("### 🌟 核心功能：直接生成标注项目")
            with gr.Row():
                with gr.Column(scale=1):
                    p_audio_url = gr.Textbox(
                        label="音频链接 (URL)", 
                        placeholder="https://...", 
                        value="https://shilong-test.oss-cn-beijing.aliyuncs.com/DB_0528_0011_01_2_A_0003.wav?Expires=1765059547&OSSAccessKeyId=TMP.3KnFwd6kF79GN4hDxRzyWRrQNZd9VWYWy1Acd11vr1RCp246vwqmGaddiKc9VG2BmQfsoBVhCBL9KXaBpktUvBpANfSh9q&Signature=PoB6jSscoBlTOQX8ZnVocS9rWlk%3D"
                    )
                    p_project_title = gr.Textbox(
                        label="项目名称 (Project Name)", 
                        placeholder="Enter project name...", 
                        value="Meeting_Analysis_17min_Test"
                    )
                    p_run_btn = gr.Button("🚀 执行全流程 (Run)", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    p_output = gr.Textbox(label="执行日志", lines=15, interactive=False)
            
            # Example for the user's specific request
            gr.Examples(
                examples=[
                    [
                        "https://shilong-test.oss-cn-beijing.aliyuncs.com/DB_0528_0011_01_2_A_0003.wav?Expires=1765059547&OSSAccessKeyId=TMP.3KnFwd6kF79GN4hDxRzyWRrQNZd9VWYWy1Acd11vr1RCp246vwqmGaddiKc9VG2BmQfsoBVhCBL9KXaBpktUvBpANfSh9q&Signature=PoB6jSscoBlTOQX8ZnVocS9rWlk%3D", 
                        "Final_Acceptance_Test_17min"
                    ]
                ],
                inputs=[p_audio_url, p_project_title],
                label="测试用例 (17min Audio)"
            )

        # --- Tab 2: Manual / Debug Mode (Original) ---
        with gr.TabItem("🛠️ 手动/调试模式 (Debug)"):
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
                    
                    gr.Markdown("### 🏷️ Label Studio 导入")
                    with gr.Row():
                        import_btn = gr.Button("📤 导入到 Label Studio", variant="secondary")
                    
                    import_output = gr.Textbox(
                        label="导入状态",
                        lines=3,
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
                   python mcp-paraformer-trans-audio.py
                   ```
                
                2. **点击"初始化 Agent"** 按钮连接到 MCP Server
                
                3. **输入音频 URL** 和 **任务描述**
                
                4. **点击"开始分析"** 查看结果
                
                ### 配置信息：
                - **Qwen Server**: `{}`
                - **Paraformer Server**: `{}`
                - **LLM Model**: `{}`
                - **Base URL**: `{}`
                """.format(
                    MCP_SERVER_URL,
                    MCP_PARAFORMER_URL,
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
            
            import_btn.click(
                fn=import_to_label_studio,
                inputs=[audio_url, output],
                outputs=import_output
            )

    # Bind Tab 1 Event
    p_run_btn.click(
        fn=process_pipeline,
        inputs=[p_audio_url, p_project_title],
        outputs=p_output
    )

if __name__ == "__main__":
    print("🚀 启动 Gradio UI (Refactored)...")
    print(f"📡 Services: Qwen={MCP_SERVER_URL}, Paraformer={MCP_PARAFORMER_URL}")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
