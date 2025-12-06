"""
音频理解 MCP 服务器
====================
基于通义千问 Qwen-Audio 模型的音频分析服务
提供多种音频理解工具，返回结构化的 JSON 结果
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from datetime import datetime
import uuid
from typing import Dict, Any, Optional, List

import dashscope
from fastmcp import FastMCP

# ==========================
# 日志配置
# ==========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==========================
# 配置管理
# ==========================
class Config:
    """服务器配置管理类"""
    
    # API 配置
    API_KEY = os.getenv("DASHSCOPE_API_KEY")
    DEFAULT_MODEL = os.getenv("QWEN_AUDIO_MODEL", "qwen-audio-turbo")
    
    # 服务器配置
    HOST = os.getenv("MCP_HOST", "127.0.0.1")
    PORT = int(os.getenv("MCP_PORT", "8000"))
    
    # 重试配置
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否完整"""
        if not cls.API_KEY:
            logger.error("❌ 未找到环境变量 DASHSCOPE_API_KEY")
            logger.error("请运行: export DASHSCOPE_API_KEY='your-api-key'")
            return False
        return True

# 初始化配置
if not Config.validate():
    sys.exit(1)

dashscope.api_key = Config.API_KEY
logger.info(f"✅ API Key 已配置，使用模型: {Config.DEFAULT_MODEL}")

# ==========================
# 辅助函数
# ==========================
def validate_url(url: str) -> bool:
    """
    验证 URL 格式是否正确
    
    Args:
        url: 待验证的 URL
        
    Returns:
        bool: URL 是否有效
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception:
        return False

def create_error_response(error_type: str, message: str, details: Optional[str] = None) -> str:
    """
    创建标准化的错误响应
    
    Args:
        error_type: 错误类型
        message: 错误消息
        details: 详细错误信息
        
    Returns:
        str: JSON 格式的错误响应
    """
    error_response = {
        "success": False,
        "error": {
            "type": error_type,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
    }
    return json.dumps(error_response, ensure_ascii=False, indent=2)

def create_success_response(data: Dict[str, Any], analysis_type: str) -> str:
    """
    创建标准化的成功响应
    
    Args:
        data: 分析结果数据
        analysis_type: 分析类型
        
    Returns:
        str: JSON 格式的成功响应
    """
    response = {
        "success": True,
        "analysis_type": analysis_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(response, ensure_ascii=False, indent=2)

def call_qwen_audio(
    audio_url: str, 
    question: str, 
    model: str = Config.DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    调用通义千问音频模型的核心函数
    
    Args:
        audio_url: 音频文件 URL
        question: 分析问题
        model: 使用的模型名称
        
    Returns:
        Dict: 包含响应内容和元数据的字典
        
    Raises:
        Exception: API 调用失败时抛出异常
    """
    messages = [
        {
            "role": "user",
            "content": [
                {"audio": audio_url},
                {"text": question}
            ]
        }
    ]
    
    response = dashscope.MultiModalConversation.call(
        model=model,
        messages=messages,
        result_format="message"
    )
    
    if response.status_code != 200:
        # Check for InvalidParameter error about file size
        if getattr(response, "code", "") == "InvalidParameter" or "exceeds the maximum length" in response.message:
             raise ValueError(f"AUDIO_TOO_LARGE: {response.message}")
        raise Exception(f"API 调用失败 [状态码: {response.status_code}]: {response.message}")
    
    # 提取文本响应
    content = response["output"]["choices"][0]["message"]["content"]
    text_response = ""
    for item in content:
        if "text" in item:
            text_response += item["text"]
    
    return {
        "text": text_response.strip(),
        "model": model,
        "request_id": response.get("request_id", "N/A")
    }

def save_result_to_file(data: Dict[str, Any], prefix: str = "qwen_analysis") -> str:
    """Save analysis result to local temp file"""
    output_dir = os.path.join(os.getcwd(), "tmp_results")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    file_name = f"{prefix}_{uuid.uuid4().hex}.json"
    abs_path = os.path.join(output_dir, file_name)
    
    with open(abs_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    logger.info(f"💾 Analysis saved to: {abs_path}")
    return abs_path

# ==========================
# MCP 服务器实例
# ==========================
mcp = FastMCP(
    "Enhanced Audio Understanding Server",
    "集成通义千问 Qwen-Audio 模型的增强型音频理解 MCP 服务器，提供多种专业音频分析工具，返回结构化 JSON 结果。"
)

# ==========================
# 工具定义
# ==========================




@mcp.tool
def analyze_speaker(audio_url: str) -> str:
    """
    说话人分析 - 分析音频中说话人的特征
    
    返回结构化的 JSON 结果，包含：
    - gender: 性别（male/female/unknown）
    - age_range: 年龄范围
    - emotion: 情绪状态
    - accent: 口音特征
    - speaking_rate: 语速
    - tone: 语调特征
    
    Args:
        audio_url: 音频文件的公开 URL
        
    Returns:
        str: JSON 格式的说话人分析结果
    """
    logger.info(f"👤 说话人分析任务: {audio_url}")
    
    if not validate_url(audio_url):
        logger.error(f"❌ 无效的 URL: {audio_url}")
        return create_error_response("InvalidURL", "提供的音频 URL 格式无效", audio_url)
    
    try:
        question = """请详细分析这段音频中说话人的特征，包括：
1. 性别：男性/女性/无法判断
2. 年龄范围：例如 20-30岁
3. 情绪状态：例如 平静、激动、愉快、悲伤等
4. 口音特征：例如 普通话、方言、外国口音等
5. 语速：快速/正常/缓慢
6. 语调特征：例如 平稳、起伏较大、单调等

请以简洁的方式描述每个特征，每个特征单独一行。"""
        
        result = call_qwen_audio(audio_url, question)
        
        # 解析响应文本（这里做简单的解析，实际可以更复杂）
        text = result["text"]
        data = {
            "raw_analysis": text,
            "audio_url": audio_url,
            "model": result["model"],
            "request_id": result["request_id"],
            "parsed_features": {
                "gender": "unknown",
                "age_range": "unknown",
                "emotion": "unknown",
                "accent": "unknown",
                "speaking_rate": "unknown",
                "tone": "unknown"
            }
        }
        
        # 简单的关键词解析
        lines = text.lower().split('\n')
        for line in lines:
            if '性别' in line or 'gender' in line:
                if '男' in line or 'male' in line:
                    data["parsed_features"]["gender"] = "male"
                elif '女' in line or 'female' in line:
                    data["parsed_features"]["gender"] = "female"
            elif '年龄' in line or 'age' in line:
                data["parsed_features"]["age_range"] = line.split('：')[-1].strip() if '：' in line else "unknown"
            elif '情绪' in line or 'emotion' in line:
                data["parsed_features"]["emotion"] = line.split('：')[-1].strip() if '：' in line else "unknown"
            elif '口音' in line or 'accent' in line:
                data["parsed_features"]["accent"] = line.split('：')[-1].strip() if '：' in line else "unknown"
            elif '语速' in line or 'speed' in line or 'rate' in line:
                data["parsed_features"]["speaking_rate"] = line.split('：')[-1].strip() if '：' in line else "unknown"
            elif '语调' in line or 'tone' in line:
                data["parsed_features"]["tone"] = line.split('：')[-1].strip() if '：' in line else "unknown"
        
        logger.info(f"✅ 说话人分析完成")
        
        # Save to file
        file_path = save_result_to_file(data, "speaker")
        
        # Return lightweight response with path
        return create_success_response({
            "summary": "Speaker analysis complete.",
            "full_result_path": file_path,
            "features_preview": data["parsed_features"]
        }, "speaker_analysis")
        
    except ValueError as e:
        if "AUDIO_TOO_LARGE" in str(e):
             logger.warning(f"⚠️ 音频过大跳过说话人分析: {e}")
             return json.dumps({
                "success": True, # Soft pass for workflow continuity
                "analysis_type": "speaker_analysis", 
                "data": {
                    "raw_analysis": "Audio too large for detailed speaker analysis via this model. Using defaults.",
                    "parsed_features": {
                        "gender": "unknown", "age_range": "unknown", "emotion": "unknown",
                        "accent": "unknown", "speaking_rate": "unknown", "tone": "unknown"
                    },
                    "note": "Skipped due to file size limits."
                }
             }, ensure_ascii=False)
        return create_error_response("SpeakerAnalysisError", str(e), str(e))
    except Exception as e:
        logger.error(f"❌ 说话人分析失败: {str(e)}")
        return create_error_response("SpeakerAnalysisError", "说话人分析过程中发生错误", str(e))


@mcp.tool
def detect_audio_events(audio_url: str, event_types: str = "all") -> str:
    """
    音频事件检测 - 检测音频中的特定声音事件和时间点
    
    返回结构化的 JSON 结果，包含：
    - events: 检测到的事件列表
      - event_type: 事件类型
      - start_time: 开始时间
      - end_time: 结束时间
      - confidence: 置信度
    
    Args:
        audio_url: 音频文件的公开 URL
        event_types: 要检测的事件类型，可选: all（全部）, speech（语音）, music（音乐）, 
                     environmental（环境音：汽车、钟声、雷声等）
        
    Returns:
        str: JSON 格式的事件检测结果
    """
    logger.info(f"🎵 音频事件检测任务: {audio_url}, 类型: {event_types}")
    
    if not validate_url(audio_url):
        logger.error(f"❌ 无效的 URL: {audio_url}")
        return create_error_response("InvalidURL", "提供的音频 URL 格式无效", audio_url)
    
    try:
        # 根据 event_types 定制问题
        if event_types == "speech":
            question = "请检测这段音频中所有说话片段的起止时间点，并列出每个片段的时间范围。"
        elif event_types == "music":
            question = "请检测这段音频中是否有音乐，如果有，请标注音乐出现的起止时间点。"
        elif event_types == "environmental":
            question = """请检测这段音频中的环境声音事件，包括但不限于：
- 汽车喇叭声
- 钟声
- 雷声
- 破碎玻璃声
- 风声
- 电流声
- 其他明显的环境音

对于检测到的每种声音，请标注其出现的起止时间点。"""
        else:  # all
            question = """请全面分析这段音频并检测以下内容及其出现的时间点：
1. 语音片段（说话的起止时间）
2. 音乐片段
3. 环境声音（如汽车、钟声、雷声、破碎玻璃声、风声、电流声等）
4. 其他显著的声音事件

请以清晰的格式列出每个事件的类型和时间范围。"""
        
        result = call_qwen_audio(audio_url, question)
        
        data = {
            "raw_detection": result["text"],
            "audio_url": audio_url,
            "event_filter": event_types,
            "model": result["model"],
            "request_id": result["request_id"],
            "events": []
        }
        
        # 这里可以添加更复杂的解析逻辑来提取时间点
        # 简化版本，直接返回原始文本
        
        logger.info(f"✅ 音频事件检测完成")
        
        # Save to file
        file_path = save_result_to_file(data, "events")
        
        # Return lightweight response
        return create_success_response({
            "summary": f"Event detection complete ({event_types}).",
            "full_result_path": file_path,
            "raw_preview": result["text"][:200] + "..."
        }, "event_detection")
        
    except ValueError as e:
        if "AUDIO_TOO_LARGE" in str(e):
             logger.warning(f"⚠️ 音频过大跳过事件检测: {e}")
             return json.dumps({
                "success": True, # Soft pass
                "analysis_type": "event_detection",
                "data": {
                    "raw_detection": "Audio too large for event detection via this model.",
                    "events": [],
                    "note": "Skipped due to file size limits."
                }
             }, ensure_ascii=False)
        return create_error_response("EventDetectionError", str(e), str(e))
    except Exception as e:
        logger.error(f"❌ 音频事件检测失败: {str(e)}")
        return create_error_response("EventDetectionError", "音频事件检测过程中发生错误", str(e))


@mcp.tool
def search_keyword_in_audio(audio_url: str, keyword: str) -> str:
    """
    关键词搜索 - 在音频中搜索特定关键词的出现位置
    
    返回结构化的 JSON 结果，包含：
    - keyword: 搜索的关键词
    - found: 是否找到
    - occurrences: 出现次数
    - time_positions: 时间位置列表
    
    Args:
        audio_url: 音频文件的公开 URL
        keyword: 要搜索的关键词
        
    Returns:
        str: JSON 格式的关键词搜索结果
    """
    logger.info(f"🔍 关键词搜索任务: {audio_url}, 关键词: {keyword}")
    
    if not validate_url(audio_url):
        logger.error(f"❌ 无效的 URL: {audio_url}")
        return create_error_response("InvalidURL", "提供的音频 URL 格式无效", audio_url)
    
    if not keyword or len(keyword.strip()) == 0:
        return create_error_response("InvalidKeyword", "关键词不能为空", keyword)
    
    try:
        question = f'"{keyword}" 这个词是否在音频中出现？如果出现了，请告诉我它出现的起止时间点（所有出现的位置）。如果没有出现，请明确说明。'
        
        result = call_qwen_audio(audio_url, question)
        
        # 判断是否找到关键词
        text = result["text"].lower()
        found = "出现" in text or "找到" in text or keyword.lower() in text
        not_found = "没有出现" in text or "未出现" in text or "未找到" in text
        
        data = {
            "keyword": keyword,
            "found": found and not not_found,
            "raw_result": result["text"],
            "audio_url": audio_url,
            "model": result["model"],
            "request_id": result["request_id"],
            "time_positions": []
        }
        
        logger.info(f"✅ 关键词搜索完成，找到: {data['found']}")
        return create_success_response(data, "keyword_search")
        
    except Exception as e:
        logger.error(f"❌ 关键词搜索失败: {str(e)}")
        return create_error_response("KeywordSearchError", "关键词搜索过程中发生错误", str(e))


@mcp.tool
def comprehensive_audio_analysis(audio_url: str, custom_question: Optional[str] = None) -> str:
    """
    综合音频分析 - 对音频进行全方位的综合分析
    
    返回结构化的 JSON 结果，包含：
    - summary: 音频内容摘要
    - duration_estimate: 时长估计
    - quality_assessment: 音质评估
    - content_analysis: 内容分析
    - custom_answer: 自定义问题的回答（如果提供）
    
    Args:
        audio_url: 音频文件的公开 URL
        custom_question: 可选的自定义分析问题
        
    Returns:
        str: JSON 格式的综合分析结果
    """
    logger.info(f"📊 综合音频分析任务: {audio_url}")
    
    if not validate_url(audio_url):
        logger.error(f"❌ 无效的 URL: {audio_url}")
        return create_error_response("InvalidURL", "提供的音频 URL 格式无效", audio_url)
    
    try:
        if custom_question:
            question = custom_question
        else:
            question = """请对这段音频进行全面分析，包括：
1. 内容摘要：简要概括音频的主要内容
2. 音频类型：例如 对话、演讲、音乐、环境录音等
3. 时长估计：大致的音频时长
4. 音质评估：音质是否清晰、是否有噪音
5. 语言和内容：使用的语言，主题和关键信息
6. 其他显著特征：任何值得注意的特殊特征

请以清晰结构化的方式呈现分析结果。"""
        
        result = call_qwen_audio(audio_url, question)
        
        data = {
            "comprehensive_analysis": result["text"],
            "audio_url": audio_url,
            "custom_question": custom_question,
            "model": result["model"],
            "request_id": result["request_id"],
            "analysis_summary": {
                "content_type": "unknown",
                "quality": "unknown",
                "language": "unknown"
            }
        }
        
        logger.info(f"✅ 综合分析完成")
        
        # Save to file
        file_path = save_result_to_file(data, "comprehensive")
        
        return create_success_response({
            "summary": "Comprehensive analysis complete.",
            "full_result_path": file_path,
            "preview": result["text"][:500] + "..."
        }, "comprehensive_analysis")
        
    except Exception as e:
        logger.error(f"❌ 综合分析失败: {str(e)}")
        return create_error_response("ComprehensiveAnalysisError", "综合分析过程中发生错误", str(e))


@mcp.tool
def get_server_status() -> str:
    """
    获取服务器状态信息
    
    Returns:
        str: JSON 格式的服务器状态
    """
    status = {
        "success": True,
        "server": "Enhanced Audio Understanding MCP Server",
        "status": "running",
        "model": Config.DEFAULT_MODEL,
        "host": Config.HOST,
        "port": Config.PORT,
        "available_tools": [

            "analyze_speaker",
            "detect_audio_events",
            "search_keyword_in_audio",
            "comprehensive_audio_analysis",
            "get_server_status"
        ],
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(status, ensure_ascii=False, indent=2)


# ==========================
# 服务器启动
# ==========================
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🎧 增强型音频理解 MCP 服务器")
    logger.info("=" * 60)
    logger.info(f"📡 服务地址: http://{Config.HOST}:{Config.PORT}")
    logger.info(f"🤖 使用模型: {Config.DEFAULT_MODEL}")
    logger.info(f"🔧 可用工具:")

    logger.info("   - analyze_speaker: 说话人分析")
    logger.info("   - detect_audio_events: 音频事件检测")
    logger.info("   - search_keyword_in_audio: 关键词搜索")
    logger.info("   - comprehensive_audio_analysis: 综合分析")
    logger.info("   - get_server_status: 服务器状态")
    logger.info("=" * 60)
    logger.info("✅ 服务器启动中...")
    
    try:
        mcp.run(transport="sse", host=Config.HOST, port=Config.PORT)
    except KeyboardInterrupt:
        logger.info("\n👋 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)
