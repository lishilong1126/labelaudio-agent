#!/bin/bash

# ==========================================
# Audio Agent 启动与测试脚本
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
# 查找并杀死旧的 MCP Server 进程
OLD_MCP_PIDS=$(ps aux | grep '[m]cp-qwen-analyze-audio.py' | awk '{print $2}')
if [ ! -z "$OLD_MCP_PIDS" ]; then
    echo "发现旧的 MCP Server 进程: $OLD_MCP_PIDS"
    kill $OLD_MCP_PIDS 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 已清理旧的 MCP Server 进程${NC}"
fi

# 查找并杀死旧的 Paraformer Server 进程
OLD_PARA_PIDS=$(ps aux | grep '[m]cp-paraformer-trans-audio.py' | awk '{print $2}')
if [ ! -z "$OLD_PARA_PIDS" ]; then
    echo "发现旧的 Paraformer Server 进程: $OLD_PARA_PIDS"
    kill $OLD_PARA_PIDS 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 已清理旧的 Paraformer Server 进程${NC}"
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

echo -e "${GREEN}✅ 清理完成${NC}"
echo ""

echo -e "${GREEN}🚀 正在启动 MCP Servers...${NC}"

# 1. 后台启动 MCP Server
python3 mcp-qwen-analyze-audio.py > server_qwen.log 2>&1 &
QWEN_PID=$!

python3 mcp-paraformer-trans-audio.py > server_para.log 2>&1 &
PARA_PID=$!

echo "Qwen Server PID: $QWEN_PID"
echo "Paraformer Server PID: $PARA_PID"
echo "正在等待服务器启动 (5秒)..."
sleep 5

# 检查服务器是否存活
if ! ps -p $QWEN_PID > /dev/null; then
    echo -e "${RED}❌ Qwen Server 启动失败，请检查 server_qwen.log${NC}"
    kill $PARA_PID 2>/dev/null
    exit 1
fi

if ! ps -p $PARA_PID > /dev/null; then
    echo -e "${RED}❌ Paraformer Server 启动失败，请检查 server_para.log${NC}"
    kill $QWEN_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✅ 所有 MCP Servers 已在后台运行${NC}"

# 2. 运行功能测试
echo -e "\n${GREEN}🧪 开始运行功能测试 (functional_test.py)...${NC}"
echo "=================================================="

# 运行测试脚本
python3 functional_test.py

TEST_EXIT_CODE=$?

# 3. 清理工作
echo -e "\n=================================================="
echo -e "${YELLOW}🧹 正在停止 MCP Servers...${NC}"
kill $QWEN_PID $PARA_PID

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 测试全部通过！${NC}"
else
    echo -e "${RED}❌ 测试失败 (Exit Code: $TEST_EXIT_CODE)${NC}"
fi

exit $TEST_EXIT_CODE
