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

### 方式一：Gradio Web UI (推荐)

使用友好的 Web 界面进行测试和调试：

```bash
chmod +x run_ui.sh
./run_ui.sh
```

然后在浏览器中访问：`http://localhost:7860`

### 方式二：一键启动 (命令行测试)

使用提供的脚本自动启动 MCP Server 并运行测试：

```bash
chmod +x run.sh
./run.sh
```

### 方式三：手动运行

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
*   `gradio_ui.py`: **Gradio Web UI**，提供友好的网页界面。
*   `agent_logger.py`: **日志记录器**，记录 Agent 执行的详细过程。
*   `functional_test.py`: 功能测试脚本。
*   `run.sh`: 命令行测试启动脚本。
*   `run_ui.sh`: Web UI 启动脚本。
*   `requirements.txt`: 项目依赖列表。
*   `agent_execution.log`: **执行日志文件**，记录所有 Agent 的执行细节。

## 📊 日志记录

系统会自动记录 Agent 执行过程中的详细信息，包括：

*   **🧠 意图分析**: Agent 如何理解用户请求
*   **📋 任务规划**: Agent 决定调用哪些工具
*   **🔧 工具调用**: 每个工具的输入参数和输出结果
*   **💭 推理过程**: LLM 的思考和决策过程
*   **📊 执行摘要**: 总步骤数、工具调用次数等统计信息

**查看日志：**
```bash
# 实时查看日志
tail -f agent_execution.log

# 查看最近的日志
tail -100 agent_execution.log
```

**日志示例：**
```
================================================================================
🚀 开始处理用户请求
📝 音频 URL: https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3
📝 任务描述: 转录这段音频
================================================================================
🤖 Agent 步骤 #1
📨 消息数量: 1
👤 用户输入: Audio URL: https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3...
================================================================================
🎯 Agent 决策
🔍 意图识别: 调用工具 'transcribe_audio'
📋 任务规划: {'audio_url': 'https://...', 'language': 'auto'}
--------------------------------------------------------------------------------
🔧 工具调用: transcribe_audio
📥 输入参数: {'audio_url': 'https://...', 'language': 'auto'}
📤 工具输出: {"transcript": "欢迎使用阿里云", ...}
✅ 工具执行完成
================================================================================
🏁 Agent 执行完成
📊 总步骤数: 1
🔧 工具调用次数: 1
📝 工具调用摘要:
  1. transcribe_audio (步骤 #1)
✨ 最终输出: 音频转录完成！以下是转录结果...
================================================================================
```


## 🔗 技术栈

*   **Framework**: [Deep Agents](https://github.com/deep-agents) (基于 LangGraph)
*   **Protocol**: [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
*   **UI**: [Gradio](https://gradio.app/) - 友好的 Web 界面
*   **Models**: 
    *   Reasoning: GPT-4o / DeepSeek V3
    *   Audio: Qwen-Audio-Turbo

## 💻 环境要求

*   **Python**: 3.11+ (推荐使用 Conda 环境)
*   **操作系统**: macOS / Linux / Windows
*   **依赖**: 见 `requirements.txt`

**推荐使用 Conda 环境：**
```bash
# 创建环境
conda create -n labelaudio-agent python=3.11 -y
conda activate labelaudio-agent

# 安装依赖
pip install -r requirements.txt
```

## 🎯 使用示例

### Gradio Web UI

1. 启动服务：`./run_ui.sh`
2. 访问 `http://localhost:7860`
3. 点击"初始化 Agent"
4. 输入音频 URL 和任务描述
5. 点击"开始分析"查看结果

**支持的任务类型：**
- "转录这段音频"
- "分析说话人的性别、年龄和情绪"
- "检测音频中的所有事件"
- "搜索关键词'阿里云'"
- "对这段音频进行综合分析"

### 命令行模式

```bash
# 启动 MCP Server
python3 mcp-qwen-analyze-audio.py &

# 运行 Agent
python3 audio_agent.py "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3" "转录这段音频"
```

## 🐛 故障排除

### 1. 端口被占用

**错误**: `address already in use`

**解决方案**: 
```bash
# 查找占用端口的进程
lsof -ti:8000  # MCP Server
lsof -ti:7860  # Gradio UI

# 杀死进程
kill -9 <PID>

# 或者使用脚本自动清理（已内置）
./run_ui.sh  # 脚本会自动清理旧进程
```

### 2. MCP Server 连接失败

**错误**: `无法从 MCP Server 获取工具`

**解决方案**:
1. 确保 MCP Server 正在运行：`ps aux | grep mcp-qwen`
2. 检查端口 8000 是否可访问：`curl http://localhost:8000/sse`
3. 查看 MCP Server 日志：`tail -f server.log`

### 3. API Key 错误

**错误**: `DASHSCOPE_API_KEY not found` 或 `LLM_API_KEY not found`

**解决方案**:
1. 检查 `.env` 文件是否存在并配置正确
2. 确保环境变量已加载：`echo $DASHSCOPE_API_KEY`
3. 重新运行脚本以加载环境变量

### 4. Python 版本不兼容

**错误**: `Requires-Python >=3.11`

**解决方案**:
```bash
# 检查 Python 版本
python3 --version

# 使用 Conda 创建 3.11 环境
conda create -n labelaudio-agent python=3.11 -y
conda activate labelaudio-agent
pip install -r requirements.txt
```

## 📝 开发说明

### 添加新工具

1. 在 `mcp-qwen-analyze-audio.py` 中定义新工具
2. 使用 `@mcp.tool()` 装饰器注册
3. Agent 会自动发现并使用新工具

### 自定义日志

修改 `agent_logger.py` 中的 `AgentExecutionLogger` 类来自定义日志格式和内容。

### 更换 LLM 模型

在 `.env` 文件中修改：
```bash
LLM_MODEL="gpt-4o"  # 或其他模型
LLM_BASE_URL="https://api.openai.com/v1"  # 或其他兼容 OpenAI API 的服务
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请提交 Issue 或联系项目维护者。

