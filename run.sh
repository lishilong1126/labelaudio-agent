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

# 2. 运行功能测试
echo -e "\n${GREEN}🧪 开始运行功能测试 (functional_test.py)...${NC}"
echo "=================================================="

# 运行测试脚本
python3 functional_test.py

TEST_EXIT_CODE=$?

# 3. 清理工作
echo -e "\n=================================================="
echo -e "${YELLOW}🧹 正在停止 MCP Server...${NC}"
kill $SERVER_PID

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 测试全部通过！${NC}"
else
    echo -e "${RED}❌ 测试失败 (Exit Code: $TEST_EXIT_CODE)${NC}"
fi

exit $TEST_EXIT_CODE
