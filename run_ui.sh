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
    # 允许使用 Token 进行 API 认证 (Label Studio 新版默认禁用)
    export LABEL_STUDIO_DISABLE_LEGACY_TOKEN_AUTH=false
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
OLD_MCP_PIDS=$(ps aux | grep '[m]cp_servers/mcp-qwen-analyze-audio.py' | awk '{print $2}')
if [ ! -z "$OLD_MCP_PIDS" ]; then
    echo "发现旧的 MCP Server 进程: $OLD_MCP_PIDS"
    kill $OLD_MCP_PIDS 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 已清理旧的 MCP Server 进程${NC}"
fi
# 查找并杀死旧的 MCP Server 进程
OLD_MCP_PIDS=$(ps aux | grep '[m]cp_servers/mcp-qwen-analyze-audio.py' | awk '{print $2}')
if [ ! -z "$OLD_MCP_PIDS" ]; then
    echo "发现旧的 MCP Server 进程: $OLD_MCP_PIDS"
    kill $OLD_MCP_PIDS 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 已清理旧的 MCP Server 进程${NC}"
fi

# 查找并杀死旧的 Paraformer Server 进程
OLD_PARA_PIDS=$(ps aux | grep '[m]cp_servers/mcp-paraformer-trans-audio.py' | awk '{print $2}')
if [ ! -z "$OLD_PARA_PIDS" ]; then
    echo "发现旧的 Paraformer Server 进程: $OLD_PARA_PIDS"
    kill $OLD_PARA_PIDS 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 已清理旧的 Paraformer Server 进程${NC}"
fi

# 查找并杀死旧的 Label Studio MCP Server 进程
OLD_LS_PIDS=$(ps aux | grep '[m]cp_servers/mcp-labelstudio.py' | awk '{print $2}')
if [ ! -z "$OLD_LS_PIDS" ]; then
    echo "发现旧的 Label Studio MCP Server 进程: $OLD_LS_PIDS"
    kill $OLD_LS_PIDS 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 已清理旧的 Label Studio MCP Server 进程${NC}"
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
    sleep 1
fi

if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 8001 被占用，尝试释放...${NC}"
    lsof -ti:8001 | xargs kill -9 2>/dev/null
    sleep 1
fi

if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 8002 被占用，尝试释放...${NC}"
    lsof -ti:8002 | xargs kill -9 2>/dev/null
    sleep 1
fi

if lsof -Pi :7860 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 7860 被占用，尝试释放...${NC}"
    lsof -ti:7860 | xargs kill -9 2>/dev/null
    sleep 1
fi

echo -e "${GREEN}✅ 清理完成${NC}"
echo ""

echo -e "${GREEN}🚀 正在启动 MCP Servers...${NC}"

# 0. 检查并启动 Label Studio
if ! lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Label Studio 未运行 (端口 8080 空闲)${NC}"
    echo -e "${GREEN}🚀 正在启动 Label Studio...${NC}"
    label-studio start --port 8080 --no-browser > label_studio.log 2>&1 &
    LS_APP_PID=$!
    echo "Label Studio PID: $LS_APP_PID"
    echo "⏳ 等待 Label Studio 启动 (10秒)..."
    sleep 10
else
    echo -e "${GREEN}✅ Label Studio 已在运行 (端口 8080)${NC}"
fi

# 启动 MCP Server (Qwen Audio)
echo -e "${YELLOW}🚀 正在启动 MCP Servers...${NC}"

# 检查 Server 是否已经在运行
if pgrep -f "mcp_servers/mcp-qwen-analyze-audio.py" > /dev/null; then
    echo -e "${GREEN}✅ MCP Server 已经在运行${NC}"
else
    python3 mcp_servers/mcp-qwen-analyze-audio.py > logs/server_qwen.log 2>&1 &
    QWEN_PID=$!
    echo $QWEN_PID > .mcp_server.pid
    echo -e "Qwen Server PID: $QWEN_PID"
fi

# 启动 Paraformer Server
if pgrep -f "mcp_servers/mcp-paraformer-trans-audio.py" > /dev/null; then
    echo -e "${GREEN}✅ Paraformer Server 已经在运行${NC}"
else
    python3 mcp_servers/mcp-paraformer-trans-audio.py > logs/server_para.log 2>&1 &
    PARA_PID=$!
    echo $PARA_PID > .paraformer_server.pid
    echo -e "Paraformer Server PID: $PARA_PID"
fi

# 启动 Label Studio MCP Server
if pgrep -f "mcp_servers/mcp-labelstudio.py" > /dev/null; then
    echo -e "${GREEN}✅ Label Studio MCP Server 已经在运行${NC}"
else
    python3 mcp_servers/mcp-labelstudio.py > logs/server_labelstudio.log 2>&1 &
    LS_PID=$!
    echo $LS_PID > .ls_mcp_server.pid
    echo -e "Label Studio Server PID: $LS_PID"
fi
echo "正在等待服务器启动 (5秒)..."
sleep 5

# 检查服务器是否存活
# 检查服务器是否存活
if ! ps -p $QWEN_PID > /dev/null; then
    echo -e "${RED}❌ Qwen Server 启动失败，请检查 logs/server_qwen.log${NC}"
    kill $PARA_PID 2>/dev/null
    exit 1
fi

if ! ps -p $PARA_PID > /dev/null; then
    echo -e "${RED}❌ Paraformer Server 启动失败，请检查 logs/server_para.log${NC}"
    kill $QWEN_PID 2>/dev/null
    exit 1
fi

if ! ps -p $LS_PID > /dev/null; then
    echo -e "${RED}❌ Label Studio Server 启动失败，请检查 server_labelstudio.log${NC}"
    kill $QWEN_PID $PARA_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✅ 所有 MCP Servers 已在后台运行${NC}"

# 2. 启动 Gradio UI
echo -e "\n${GREEN}🎨 正在启动 Gradio UI...${NC}"
echo "=================================================="
echo "访问地址: http://localhost:7860"
echo "=================================================="

# 捕获 Ctrl+C 信号
# 捕获 Ctrl+C 信号
trap "echo -e '\n${YELLOW}🧹 正在停止服务...${NC}'; kill $QWEN_PID $PARA_PID $LS_PID $LS_APP_PID 2>/dev/null; exit" INT

# 启动 Gradio UI（前台运行）
python3 main.py

# 如果 Gradio 退出，清理 MCP Server
echo -e "\n${YELLOW}🧹 正在停止 MCP Server...${NC}"
echo -e "\n${YELLOW}🧹 正在停止 MCP Servers...${NC}"
kill $QWEN_PID $PARA_PID $LS_PID $LS_APP_PID 2>/dev/null
