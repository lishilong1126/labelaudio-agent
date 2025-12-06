# 项目名称：一个基于多智能体技术的语音数据自动标注系统

这是一个基于 **Deep Agents** 框架构建的生产级 **智能音频标注 Multi-Agent System (MAS)**。它采用分层架构，通过 **Model Context Protocol (MCP)** 协议，将 LLM 的编排能力与专业的音频处理能力解耦，实现了高效、自动化的语音数据标注流水线。

## 🏗️ 重构设计与架构方案

我们将单体 Agent 重构为 **多智能体协作架构 (Multi-Agent Collaboration)**，主要包含三个核心角色：

### 1. 智能编排 (Master Agent / Brain)
**职责**: 系统的"大脑"，负责任务规划、拆解与分发。
*   **核心逻辑**: 解析用户自然语言指令 -> 生成有向无环图 (DAG) 任务链 -> 调度专家 Agent 并行/串行执行。
*   **实现细节**:
    *   **Intent Routing**: 识别需要"分析"还是"标注"任务。
    *   **Context Management**: 维护全局状态，确保 `Audio URL` 和 `Result Path` 在不同 Agent 间准确传递。

### 2. 音频专家 (Perception Agent)
**职责**: 系统的"感知器官"，专注于提取音频中的多维信息。
*   **集成模型**:
    *   **ASR**: 集成 Paraformer-v2，提供高精度长语音转写。
    *   **Diarization**: 自动区分多个说话人 (Speaker 0, 1...)。
    *   **Audio Understanding**: 集成 Qwen-Audio，检测非语音事件 (笑声、音乐、噪音)。
*   **关键实现**:
    *   **Long Audio Handling**: 自动切分长音频，避免超时。
    *   **Pass-by-Reference**: 针对大模型分析产生的超大 JSON (500KB+)，采用"存盘返回路径"模式，而非"返回文本"，彻底解决了 LLM 上下文限制问题。

### 3. 标注专家 (Action Agent)
**职责**: 系统的"执行手"，负责与 Label Studio 交互。
*   **能力**:
    *   **Dynamic Templating**: 根据任务类型（语音 vs 音乐）动态生成 XML 标注模板。
    *   **Smart Mapping**: 将标准化的分析结果（JSON）映射为 Label Studio 的特定格式（Regions, Labels, TextAreas）。
    *   **Dependency Injection**: 通过 MCP 工具直接调用 Label Studio API，实现项目创建与数据导入。

## 💡 核心实现思路

### 1. 模型上下文协议 (MCP) 的深度应用
我们不仅仅将 MCP 用作工具调用接口，更是将其作为 **系统模块化的标准**：
*   **工具解耦**: 所有的原子能力（如 `transcribe`, `create_project`）都封装为独立的 MCP Server。Agent 只需通过标准协议调用，无需关心底层是 Python 函数还是 HTTP 请求。
*   **热插拔**: 可以随时新增一个 "Music Analysis MCP Server"，而无需修改 Master Agent 的核心代码。

### 2. 引用传递 (Pass-by-Reference) 机制
为了解决多智能体协作中"数据搬运"导致的 Token 消耗和上下文溢出问题，我们设计了引用传递机制：
*   **Producer (Audio Agent)**: 分析完成后，将结果序列化为 JSON 文件存储在本地 `/tmp_results/`，仅向 Master Agent 返回绝对路径。
*   **Consumer (Annotation Agent)**: 在指令中接收文件路径。其工具 `import_task(file_path)` 支持直接读取本地文件进行处理，**严禁** Agent 尝试读取文件内容到上下文中。

### 3. 一体化与模块化的平衡
*   **统一入口**: 虽然内部是多 Agent 协作，但对外通过 `main.py` 提供统一的 Gradio 界面和 CLI 接口。
*   **配置中心**: 所有 Agent 共享 `config.py` 和 `.env` 配置，确保环境一致性。

## 🛠️ 快速上手

### 环境要求
*   Python 3.11+
*   Label Studio 
*   API Keys (DashScope, OpenAI/Volcengine)

### 启动系统
推荐使用一键启动脚本，它会自动拉起所有 MCP Servers 和前端界面：

```bash
chmod +x run_ui.sh
./run_ui.sh
```
访问地址: **http://localhost:7860**

## 📂 项目结构
*   `agents/`: Agent 角色定义
    *   `orchestrator.py`: 编排者
    *   `audio_specialist.py`: 音频专家
    *   `annotation_specialist.py`: 标注专家
*   `mcp_servers/`: 原子能力实现
    *   `mcp-qwen...`: 音频理解服务
    *   `mcp-paraformer...`: 转写服务
    *   `mcp-labelstudio...`: 标注平台服务
*   `mcp_client/`: 统一连接层
*   `tmp_results/`: 数据交换区

## 📄 许可证
MIT License
