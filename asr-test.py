import os
import dashscope
from fastmcp import FastMCP

# --- 1. 环境准备与配置 ---
# 强烈建议通过环境变量设置您的API密钥，而不是硬编码在代码中。
# 在您的终端中运行: export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxx"
try:
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    if not dashscope.api_key:
        raise ValueError("未找到环境变量 DASHSCOPE_API_KEY，请确保已正确设置。")
except ValueError as e:
    print(e)
    # 在无法获取API Key时退出程序，避免后续报错
    exit()

# --- 2. 创建 FastMCP 服务器实例 ---
# 为您的MCP服务器提供一个描述性的名称和介绍
mcp = FastMCP(
    "Audio Understanding Server",
    "一个集成了通义千问Qwen-Audio模型的MCP服务器，提供强大的音频理解能力，可作为AI Agent的工具使用。"
)

# --- 3. 定义音频理解工具 ---
@mcp.tool
def analyze_audio(audio_url: str, question: str = "这段音频在说什么？请进行详细分析。") -> str:
    """
    使用通义千问Qwen-Audio模型分析给定的音频URL。

    该工具可以实现多种功能，例如：
    - 语音识别与分析: 转录文本、分析说话人性别、年龄、口音、情绪等。
    - 音频问答: 根据音频内容回答特定问题。
    - 语音聊天: 在不提供具体问题时，对音频内容进行综合回应。

    :param audio_url: 【必需】要分析的音频文件的公开可访问URL。例如: 'https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3'
    :param question: 【可选】针对音频提出的具体问题。如果留空，将执行默认的综合分析。
                     例如: '说话者是男是女？情绪怎么样？' 或 '“阿里”这个词出现在什么时间点？'
    :return: 一个包含模型分析结果的字符串。
    """
    print(f"接收到任务：分析音频 URL: {audio_url}，问题: {question}")
    try:
        # 构建发送给通义千问模型的输入消息
        messages = [
            {
                "role": "user",
                "content": [
                    {"audio": audio_url},
                    {"text": question}
                ]
            }
        ]

        # 调用模型 API
        response = dashscope.MultiModalConversation.call(
            model="qwen-audio-turbo", # 您也可以使用 qwen-audio-large
            messages=messages,
            result_format="message"
        )

        # 检查响应状态并提取结果
        if response.status_code == 200:
            content = response["output"]["choices"][0]["message"]["content"]
            # content 是一个列表，我们提取其中的文本部分
            text_response = ""
            for item in content:
                if "text" in item:
                    text_response += item["text"]
            
            print(f"模型返回结果: {text_response}")
            return text_response
        else:
            # 如果API调用失败，返回错误信息
            error_message = f"API 调用失败，状态码: {response.status_code}, 错误信息: {response.message}"
            print(error_message)
            return error_message

    except Exception as e:
        # 捕获其他潜在的异常
        error_message = f"处理音频时发生未知错误: {e}"
        print(error_message)
        return error_message

# --- 4. 启动 MCP 服务器 ---
if __name__ == "__main__":
    print("="*50)
    print("音频理解 MCP 服务器即将启动...")
    print("您可以通过 http://127.0.0.1:8000/tools/analyze_audio 与其交互。")
    print("确保您的 DASHSCOPE_API_KEY 环境变量已正确设置！")
    print("="*50)
    
    # 运行服务器，使用 SSE (Server-Sent Events) 传输协议
    mcp.run(transport="sse", host="127.0.0.1", port=8000)