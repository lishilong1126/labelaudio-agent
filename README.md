# Audio Analysis Agent (Deep Agents + MCP)

这是一个基于 **Deep Agents** 框架构建的智能音频分析 Agent。它通过 **Model Context Protocol (MCP)** 连接到底层的音频理解服务（基于通义千问 Qwen-Audio），能够根据用户的自然语言指令完成复杂的音频分析任务。

## 🌟 核心特性

*   **双层架构**：
    *   **大脑**：支持 OpenAI GPT-4o 或 **火山引擎 DeepSeek V3**，负责任务规划和工具选择。
    *   **感知**：基于 Qwen-Audio 的 MCP Server，提供专业的音频理解能力。
*   **MCP 集成**：Agent 作为 MCP Client，动态加载 Server 端的工具，解耦了控制逻辑与工具实现。
*   **多功能工具箱**：
    *   🎙️ **语音转文字** (Transcription)
    *   👤 **说话人分析** (Speaker Analysis: 性别/情绪/年龄/语调)
    *   🎵 **事件检测** (Event Detection: 音乐/环境音/语音片段)
    *   🔍 **关键词搜索** (Keyword Search)
    *   📊 **综合分析** (Comprehensive Summary)

## 🛠️ 安装与配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境变量配置

你需要设置以下环境变量来激活服务：

```bash
# 1. 通义千问 API Key (用于音频理解)
export DASHSCOPE_API_KEY="sk-xxxxxxxx"

# 2. 大模型配置 (用于 Agent 大脑)
# 选项 A: 使用 OpenAI
export OPENAI_API_KEY="sk-xxxxxxxx"

# 选项 B: 使用火山引擎 (DeepSeek)
export LLM_PROVIDER="openai"  # 保持为 openai 以兼容协议
export LLM_API_KEY="你的火山引擎API_KEY"
export LLM_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
export LLM_MODEL="ep-202406xxxxxx-xxxxx" # 你的 Endpoint ID
```

## 🚀 快速开始

### 方式一：一键启动 (推荐)

使用提供的脚本自动启动 MCP Server 并运行测试：

```bash
chmod +x run.sh
./run.sh
```

### 方式二：手动运行

1.  **启动 MCP Server** (终端 1):
    ```bash
    python3 mcp-qwen-analyze-audio.py
    ```

2.  **运行 Agent** (终端 2):
    ```bash
    # 交互模式
    python3 audio_agent.py

    # 命令行模式
    python3 audio_agent.py "https://example.com/audio.mp3" "分析一下说话人的情绪"
    ```

## 📂 项目结构

*   `audio_agent.py`: **Agent 核心代码** (MCP Client)，负责规划和调用工具。
*   `mcp-qwen-analyze-audio.py`: **MCP Server**，封装了 Qwen-Audio 的原子能力。
*   `functional_test.py`: 功能测试脚本。
*   `run.sh`: 一键启动与测试脚本。
*   `requirements.txt`: 项目依赖列表。

## 🔗 技术栈

*   **Framework**: [Deep Agents](https://github.com/deep-agents) (基于 LangGraph)
*   **Protocol**: [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
*   **Models**: 
    *   Reasoning: GPT-4o / DeepSeek V3
    *   Audio: Qwen-Audio-Turbo
