#!/bin/bash

# ==========================================
# Gradio UI 启动脚本
# ==========================================

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 加载 .env 文件
if [ -f .env ]; then
    echo -e "${GREEN}📄 正在加载 .env 环境变量...${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}⚠️  未找到 .env 文件，将使用当前系统环境变量${NC}"
fi

# 检查必要的环境变量
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo -e "${RED}❌ 错误: 未设置 DASHSCOPE_API_KEY 环境变量${NC}"
    echo "请运行: export DASHSCOPE_API_KEY='your_key'"
    exit 1
fi

if [ -z "$LLM_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  警告: 未设置 LLM_API_KEY 或 OPENAI_API_KEY${NC}"
    echo "Agent 可能无法进行推理规划。"
fi

# ==========================================
# 清理旧进程
# ==========================================
echo -e "${YELLOW}🧹 正在检查并清理旧进程...${NC}"

# 查找并杀死旧的 MCP Server 进程
OLD_MCP_PIDS=$(ps aux | grep '[m]cp-qwen-analyze-audio.py' | awk '{print $2}')
if [ ! -z "$OLD_MCP_PIDS" ]; then
    echo "发现旧的 MCP Server 进程: $OLD_MCP_PIDS"
    kill $OLD_MCP_PIDS 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 已清理旧的 MCP Server 进程${NC}"
fi

# 查找并杀死旧的 Gradio UI 进程
OLD_GRADIO_PIDS=$(ps aux | grep '[g]radio_ui.py' | awk '{print $2}')
if [ ! -z "$OLD_GRADIO_PIDS" ]; then
    echo "发现旧的 Gradio UI 进程: $OLD_GRADIO_PIDS"
    kill $OLD_GRADIO_PIDS 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 已清理旧的 Gradio UI 进程${NC}"
fi

# 检查端口占用
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 8000 被占用，尝试释放...${NC}"
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

if lsof -Pi :7860 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 7860 被占用，尝试释放...${NC}"
    lsof -ti:7860 | xargs kill -9 2>/dev/null
    sleep 1
fi

echo -e "${GREEN}✅ 清理完成${NC}"
echo ""

echo -e "${GREEN}🚀 正在启动 MCP Server (mcp-qwen-analyze-audio.py)...${NC}"

# 1. 后台启动 MCP Server
python3 mcp-qwen-analyze-audio.py > server.log 2>&1 &
SERVER_PID=$!

echo "MCP Server PID: $SERVER_PID"
echo "正在等待服务器启动 (5秒)..."
sleep 5

# 检查服务器是否存活
if ! ps -p $SERVER_PID > /dev/null; then
    echo -e "${RED}❌ MCP Server 启动失败，请检查 server.log${NC}"
    exit 1
fi

echo -e "${GREEN}✅ MCP Server 已在后台运行${NC}"

# 2. 启动 Gradio UI
echo -e "\n${GREEN}🎨 正在启动 Gradio UI...${NC}"
echo "=================================================="
echo "访问地址: http://localhost:7860"
echo "=================================================="

# 捕获 Ctrl+C 信号
trap "echo -e '\n${YELLOW}🧹 正在停止服务...${NC}'; kill $SERVER_PID; exit" INT

# 启动 Gradio UI（前台运行）
python3 gradio_ui.py

# 如果 Gradio 退出，清理 MCP Server
echo -e "\n${YELLOW}🧹 正在停止 MCP Server...${NC}"
kill $SERVER_PID
