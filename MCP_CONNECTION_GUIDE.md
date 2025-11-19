# MCP 服务器连接指南

## 问题解决：405 Method Not Allowed

您遇到的 `405 Method Not Allowed` 错误是因为之前的代码使用了错误的传输协议。

### 已修复的问题

**修改前：**
```python
mcp.run(transport="http", host=Config.HOST, port=Config.PORT)
```

**修改后：**
```python
mcp.run(transport="sse", host=Config.HOST, port=Config.PORT)
```

## 如何连接 MCP Inspector

### 1. 启动服务器

```bash
# 确保已设置环境变量
export DASHSCOPE_API_KEY="your-api-key-here"

# 启动服务器
python mcp-qwen-analyze-audio.py
```

服务器将在 `http://127.0.0.1:8000` 上启动。

### 2. 使用 MCP Inspector 连接

#### 方法 A: 使用 SSE 传输（推荐，已修复）

在 MCP Inspector 中：
- **Transport Type**: 选择 `SSE (Server-Sent Events)`
- **URL**: `http://127.0.0.1:8000/sse`

#### 方法 B: 使用 Stdio 传输（本地开发）

如果您想使用 stdio 传输：

1. 修改启动代码：
```python
mcp.run(transport="stdio")
```

2. 在 MCP Inspector 或 Claude Desktop 的配置中添加：
```json
{
  "mcpServers": {
    "audio-understanding": {
      "command": "python",
      "args": ["/path/to/mcp-qwen-analyze-audio.py"]
    }
  }
}
```

### 3. 验证连接

连接成功后，您应该能看到以下工具：

1. **transcribe_audio** - 语音转文字
2. **analyze_speaker** - 说话人分析
3. **detect_audio_events** - 音频事件检测
4. **search_keyword_in_audio** - 关键词搜索
5. **comprehensive_audio_analysis** - 综合分析
6. **get_server_status** - 服务器状态

### 4. 测试工具

尝试调用 `get_server_status` 工具来验证连接：

```json
{}
```

应该返回类似以下的 JSON 响应：
```json
{
  "success": true,
  "server": "Enhanced Audio Understanding MCP Server",
  "status": "running",
  "model": "qwen-audio-turbo",
  "host": "127.0.0.1",
  "port": 8000,
  "available_tools": [...],
  "timestamp": "2025-11-08T19:28:00.000000"
}
```

## 常见问题

### Q: 仍然遇到 405 错误？
**A:** 请确保：
1. 已重启服务器
2. 使用的是最新版本的代码（transport="sse"）
3. 在 MCP Inspector 中使用正确的连接地址：`http://127.0.0.1:8000/sse`

### Q: 无法找到 /sse 端点？
**A:** 确认 FastMCP 版本是否支持 SSE 传输。如果不支持，可以尝试：
```bash
pip install --upgrade fastmcp
```

### Q: 连接超时？
**A:** 检查：
1. 服务器是否正在运行
2. 端口 8000 是否被其他程序占用
3. 防火墙设置是否阻止了连接

## 环境变量配置

### 必需的环境变量

```bash
export DASHSCOPE_API_KEY="your-dashscope-api-key"
```

### 可选的环境变量

```bash
# 使用的模型（默认：qwen-audio-turbo）
export QWEN_AUDIO_MODEL="qwen-audio-turbo"

# 服务器主机（默认：127.0.0.1）
export MCP_HOST="127.0.0.1"

# 服务器端口（默认：8000）
export MCP_PORT="8000"

# 最大重试次数（默认：3）
export MAX_RETRIES="3"

# 重试延迟秒数（默认：1.0）
export RETRY_DELAY="1.0"
```

## Claude Desktop 集成

如果您想在 Claude Desktop 中使用此 MCP 服务器：

### MacOS/Linux

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "qwen-audio": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-qwen-analyze-audio.py"],
      "env": {
        "DASHSCOPE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Windows

编辑 `%APPDATA%\Claude\claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "qwen-audio": {
      "command": "python",
      "args": ["C:\\path\\to\\mcp-qwen-analyze-audio.py"],
      "env": {
        "DASHSCOPE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

重启 Claude Desktop 后，音频分析工具将可用。

## 示例使用

### 示例 1: 语音转文字

```json
{
  "audio_url": "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3",
  "language": "zh"
}
```

### 示例 2: 说话人分析

```json
{
  "audio_url": "https://example.com/audio.mp3"
}
```

### 示例 3: 关键词搜索

```json
{
  "audio_url": "https://example.com/audio.mp3",
  "keyword": "阿里"
}
```

## 日志查看

服务器日志保存在 `audio_mcp_server.log` 文件中，可以用于调试：

```bash
tail -f audio_mcp_server.log
```

## 获取帮助

如果遇到问题：
1. 检查日志文件 `audio_mcp_server.log`
2. 确认环境变量已正确设置
3. 验证 API Key 是否有效
4. 确保网络连接正常
