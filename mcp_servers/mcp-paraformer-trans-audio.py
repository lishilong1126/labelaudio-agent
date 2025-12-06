"""
Paraformer 语音转写 MCP 服务器 (Enhanced)
=========================================
基于通义实验室 Paraformer-v2 模型的语音转写服务
提供高精度语音识别能力，支持多种语言和方言

功能特性:
- 高精度语音转写 (支持中/英/日/韩/德/法/俄/粤语)
- 说话人分离 (自动识别多个说话人)
- 词级时间戳 (精确到每个词的起止时间)
- 去除语气词 (可选)
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from datetime import datetime
from http import HTTPStatus
import requests
import tempfile
import uuid

import dashscope
from dashscope.audio.asr import Transcription
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
    API_KEY = os.getenv("DASHSCOPE_API_KEY")
    MODEL = "paraformer-v2"
    HOST = os.getenv("MCP_HOST", "127.0.0.1")
    PORT = int(os.getenv("MCP_PARAFORMER_PORT", "8001"))
    
    # 支持的语言列表
    SUPPORTED_LANGUAGES = {
        "zh": "中文（含方言）",
        "en": "英文",
        "ja": "日语",
        "ko": "韩语",
        "yue": "粤语",
        "de": "德语",
        "fr": "法语",
        "ru": "俄语"
    }
    
    # Text truncation limit to prevent LLM context overflow
    MAX_TEXT_LENGTH = 25000
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.API_KEY:
            logger.error("❌ 未找到环境变量 DASHSCOPE_API_KEY")
            return False
        return True

# 初始化配置
if not Config.validate():
    sys.exit(1)

dashscope.api_key = Config.API_KEY
logger.info(f"✅ API Key 已配置，使用模型: {Config.MODEL}")

# ==========================
# 辅助函数
# ==========================
def validate_url(url: str) -> bool:
    """验证 URL 格式"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception:
        return False

def create_error_response(error_type: str, message: str, details: Optional[str] = None) -> str:
    """创建错误响应"""
    return json.dumps({
        "success": False,
        "error": {"type": error_type, "message": message, "details": details}
    }, ensure_ascii=False)

def create_success_response(data: Dict[str, Any], task_type: str) -> str:
    """创建成功响应"""
    return json.dumps({
        "success": True,
        "task_type": task_type,
        "data": data
    }, ensure_ascii=False)

def fetch_transcription_result(result_url: str) -> Optional[Dict]:
    """下载并解析转写结果 JSON"""
    try:
        response = requests.get(result_url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"❌ 获取结果失败: {e}")
        return None

def save_result_to_file(data: Dict[str, Any]) -> str:
    """Save full result to local temp file and return absolute path"""
    # Use local directory to ensure persistence and accessibility
    output_dir = os.path.join(os.getcwd(), "tmp_results")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    file_name = f"paraformer_result_{uuid.uuid4().hex}.json"
    abs_path = os.path.join(output_dir, file_name)
    
    with open(abs_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    logger.info(f"💾 Full result saved to: {abs_path}")
    return abs_path

def extract_result_data(raw_output) -> Dict:
    """从 SDK 响应中提取结果数据"""
    
    # Handle dict-like access (JSON response)
    if isinstance(raw_output, dict):
        if "results" in raw_output and raw_output["results"]:
            result = raw_output["results"][0]
            if "transcription_url" in result:
                return {"transcription_url": result["transcription_url"], "status": result.get("subtask_status")}
                
    # Handle object-like access (SDK objects)
    elif hasattr(raw_output, 'results') and raw_output.results:
        result = raw_output.results[0]
        if hasattr(result, 'transcription_url'):
            return {"transcription_url": result.transcription_url, "status": result.subtask_status}
            
    return {}

# ==========================
# MCP 服务器实例
# ==========================
mcp = FastMCP(
    "Paraformer Transcription Server",
    "基于 Paraformer-v2 的高精度语音转写服务，支持多语种识别、说话人分离、词级时间戳"
)

# ==========================
# 工具定义
# ==========================

@mcp.tool
def transcribe_audio(
    audio_url: str,
    language: str = "zh",
    enable_diarization: bool = False,
    speaker_count: Optional[int] = None,
    enable_timestamp_alignment: bool = False,
    remove_disfluency: bool = False
) -> str:
    """
    高精度语音转写 (Paraformer-v2)
    
    Args:
        audio_url: 音频文件 URL
        language: 语言代码 (zh/en/ja/ko/yue/de/fr/ru)
        enable_diarization: 启用说话人分离 (识别不同说话人)
        speaker_count: 说话人数量提示 (2-100，仅在 enable_diarization=True 时有效)
        enable_timestamp_alignment: 启用时间戳校准 (更精确的时间戳)
        remove_disfluency: 去除语气词 (如"嗯"、"啊"等)
    
    Returns:
        JSON 格式的转写结果，包含文本、时间戳、说话人信息
    """
    logger.info(f"📝 转写任务: {audio_url[:50]}... | 语言: {language} | 分离说话人: {enable_diarization}")
    
    if not validate_url(audio_url):
        return create_error_response("InvalidURL", "无效的音频 URL")
    
    try:
        # 构建请求参数
        params = {
            "model": Config.MODEL,
            "file_urls": [audio_url],
            "language_hints": [language],
            "diarization_enabled": enable_diarization,
            "timestamp_alignment_enabled": enable_timestamp_alignment,
            "disfluency_removal_enabled": remove_disfluency
        }
        
        if enable_diarization and speaker_count and 2 <= speaker_count <= 100:
            params["speaker_count"] = speaker_count
        
        # 提交任务
        logger.info("🚀 提交转写任务...")
        task_response = Transcription.async_call(**params)
        task_id = task_response.output.task_id
        logger.info(f"✅ 任务已提交: {task_id}")
        
        # 等待完成
        logger.info("⏳ 等待转写...")
        result = Transcription.wait(task=task_id)
        
        if result.status_code != HTTPStatus.OK:
            return create_error_response("TaskFailed", f"转写失败: {result.message}")
        
        # 提取结果
        result_info = extract_result_data(result.output)
        if not result_info.get("transcription_url"):
            return create_error_response("NoResult", "未获取到转写结果")
        
        # 获取详细结果
        detail = fetch_transcription_result(result_info["transcription_url"])
        if not detail:
            return create_error_response("FetchFailed", "无法获取转写详情")
        
        # 解析并构建响应
        output = parse_transcription_detail(detail, enable_diarization)
        output["audio_url"] = audio_url
        output["language"] = language
        
        # Truncate text if too long
        if len(output["text"]) > Config.MAX_TEXT_LENGTH:
             output["text"] = output["text"][:Config.MAX_TEXT_LENGTH] + f"... (truncated, total: {len(output['text'])})"
        
        # Save full result to file
        full_result_path = save_result_to_file(output)
        
        # Create lightweight response
        response_data = {
            "text_preview": output["text"], # Already truncated or full
            "full_result_path": full_result_path,
            "duration_ms": output.get("duration_ms", 0),
            "speaker_count": len(output.get("speakers", {})) if "speakers" in output else 0
        }

        logger.info(f"✅ 转写完成: {output.get('text', '')[:50]}...")
        return create_success_response(response_data, "transcription")
        
    except Exception as e:
        logger.error(f"❌ 转写异常: {e}")
        return create_error_response("ProcessingError", str(e))


def parse_transcription_detail(data: Dict, include_speakers: bool = False) -> Dict:
    """解析转写结果详情"""
    result = {
        "text": "",
        "duration_ms": 0,
        "sentences": [],
        "words": []
    }
    
    # 音频属性
    if "properties" in data:
        props = data["properties"]
        result["duration_ms"] = props.get("original_duration_in_milliseconds", 0)
        result["sample_rate"] = props.get("original_sampling_rate", 0)
        result["channels"] = props.get("channels", [0])
    
    # 转写内容
    if "transcripts" in data and data["transcripts"]:
        transcript = data["transcripts"][0]
        result["text"] = transcript.get("text", "")
        result["content_duration_ms"] = transcript.get("content_duration_in_milliseconds", 0)
        
        # 句子级数据
        sentences = transcript.get("sentences", [])
        for sent in sentences:
            sent_data = {
                "id": sent.get("sentence_id", 0),
                "text": sent.get("text", ""),
                "begin_time": sent.get("begin_time", 0),
                "end_time": sent.get("end_time", 0)
            }
            if include_speakers and "speaker_id" in sent:
                sent_data["speaker_id"] = sent["speaker_id"]
            result["sentences"].append(sent_data)
            
            # 词级数据
            for word in sent.get("words", []):
                word_data = {
                    "text": word.get("text", ""),
                    "begin_time": word.get("begin_time", 0),
                    "end_time": word.get("end_time", 0),
                    "punctuation": word.get("punctuation", "")
                }
                result["words"].append(word_data)
    
    return result


@mcp.tool
def transcribe_with_speakers(audio_url: str, speaker_count: Optional[int] = None) -> str:
    """
    多说话人语音转写 (自动分离不同说话人)
    
    适用于会议、对话、访谈等多人场景
    
    Args:
        audio_url: 音频文件 URL
        speaker_count: 预估说话人数量 (可选，2-100)
    
    Returns:
        带说话人标签的转写结果: [Speaker 0]: xxx [Speaker 1]: yyy
    """
    logger.info(f"🎙️ 多说话人转写: {audio_url[:50]}...")
    
    if not validate_url(audio_url):
        return create_error_response("InvalidURL", "无效的音频 URL")
    
    try:
        params = {
            "model": Config.MODEL,
            "file_urls": [audio_url],
            "language_hints": ["zh"],
            "diarization_enabled": True
        }
        if speaker_count and 2 <= speaker_count <= 100:
            params["speaker_count"] = speaker_count
        
        task_response = Transcription.async_call(**params)
        result = Transcription.wait(task=task_response.output.task_id)
        
        if result.status_code != HTTPStatus.OK:
            return create_error_response("TaskFailed", f"转写失败: {result.message}")
        
        result_info = extract_result_data(result.output)
        detail = fetch_transcription_result(result_info.get("transcription_url", ""))
        if not detail:
            return create_error_response("FetchFailed", "无法获取转写详情")
        
        # 构建带说话人标签的文本
        output = {"audio_url": audio_url, "speakers": {}, "text_with_speakers": ""}
        lines = []
        
        if "transcripts" in detail and detail["transcripts"]:
            for sent in detail["transcripts"][0].get("sentences", []):
                speaker_id = sent.get("speaker_id", 0)
                text = sent.get("text", "")
                lines.append(f"[Speaker {speaker_id}]: {text}")
                
                # 统计说话人
                if speaker_id not in output["speakers"]:
                    output["speakers"][speaker_id] = {"sentence_count": 0, "texts": []}
                output["speakers"][speaker_id]["sentence_count"] += 1
                output["speakers"][speaker_id]["texts"].append(text)
        
        output["text_with_speakers"] = "\n".join(lines)
        
        # Truncate if too long
        if len(output["text_with_speakers"]) > Config.MAX_TEXT_LENGTH:
            output["text_with_speakers"] = output["text_with_speakers"][:Config.MAX_TEXT_LENGTH] + f"... (truncated, total: {len(output['text_with_speakers'])})"
            
        output["speaker_count"] = len(output["speakers"])
        
        # Save full result to file
        full_result_path = save_result_to_file(output)
        
        # Create lightweight response
        response_data = {
            "text_with_speakers_preview": output["text_with_speakers"],
            "full_result_path": full_result_path,
            "speaker_count": output["speaker_count"]
        }
        
        logger.info(f"✅ 识别到 {output['speaker_count']} 个说话人")
        return create_success_response(response_data, "speaker_transcription")
        
    except Exception as e:
        logger.error(f"❌ 转写异常: {e}")
        return create_error_response("ProcessingError", str(e))


@mcp.tool
def get_word_timestamps(audio_url: str, language: str = "zh") -> str:
    """
    获取词级时间戳 (用于字幕生成)
    
    返回每个词的精确起止时间，可用于:
    - 字幕生成
    - 音视频剪辑
    - 语音高亮同步
    
    Args:
        audio_url: 音频文件 URL
        language: 语言代码 (zh/en/ja/ko)
    
    Returns:
        词级时间戳列表: [{word, begin_time, end_time}, ...]
    """
    logger.info(f"⏱️ 获取词级时间戳: {audio_url[:50]}...")
    
    if not validate_url(audio_url):
        return create_error_response("InvalidURL", "无效的音频 URL")
    
    try:
        params = {
            "model": Config.MODEL,
            "file_urls": [audio_url],
            "language_hints": [language],
            "timestamp_alignment_enabled": True
        }
        
        task_response = Transcription.async_call(**params)
        result = Transcription.wait(task=task_response.output.task_id)
        
        if result.status_code != HTTPStatus.OK:
            return create_error_response("TaskFailed", f"转写失败: {result.message}")
        
        result_info = extract_result_data(result.output)
        if not result_info.get("transcription_url"):
            return create_error_response("NoResult", "未获取到转写结果")

        detail = fetch_transcription_result(result_info["transcription_url"])
        if not detail:
            return create_error_response("FetchFailed", "无法获取转写详情")
        
        # 提取词级时间戳
        words = []
        full_text = ""
        
        if "transcripts" in detail and detail["transcripts"]:
            transcript = detail["transcripts"][0]
            full_text = transcript.get("text", "")
            
            for sent in transcript.get("sentences", []):
                for word in sent.get("words", []):
                    words.append({
                        "text": word.get("text", ""),
                        "begin_time": word.get("begin_time", 0),
                        "end_time": word.get("end_time", 0),
                        "punctuation": word.get("punctuation", "")
                    })
        
        output = {
            "audio_url": audio_url,
            "text": full_text,
            "word_count": len(words),
            "words": words
        }
        
        # Save full result to file
        full_result_path = save_result_to_file(output)
        
        # Lightweight response
        response_data = {
            "text_preview": full_text[:Config.MAX_TEXT_LENGTH], # Preview only
            "word_count": len(words),
            "full_result_path": full_result_path
        }
        
        logger.info(f"✅ 获取到 {len(words)} 个词的时间戳")
        return create_success_response(response_data, "word_timestamps")
        
    except Exception as e:
        logger.error(f"❌ 获取时间戳异常: {e}")
        return create_error_response("ProcessingError", str(e))


@mcp.tool
def transcribe_simple(audio_url: str) -> str:
    """
    快速转写 (仅返回文本)
    
    最简模式，只返回转写文本，不含时间戳等额外信息
    适用于只需要文本内容的场景
    
    Args:
        audio_url: 音频文件 URL
    
    Returns:
        纯转写文本
    """
    logger.info(f"🚀 快速转写: {audio_url[:50]}...")
    
    if not validate_url(audio_url):
        return create_error_response("InvalidURL", "无效的音频 URL")
    
    try:
        task_response = Transcription.async_call(
            model=Config.MODEL,
            file_urls=[audio_url],
            language_hints=["zh"]
        )
        result = Transcription.wait(task=task_response.output.task_id)
        
        if result.status_code != HTTPStatus.OK:
            return create_error_response("TaskFailed", f"转写失败: {result.message}")
        
        result_info = extract_result_data(result.output)
        if not result_info.get("transcription_url"):
            return create_error_response("NoResult", "未获取到转写结果")

        detail = fetch_transcription_result(result_info["transcription_url"])
        
        if not detail:
            return create_error_response("FetchFailed", "无法获取转写详情")
        
        text = ""
        duration_ms = 0
        
        if "transcripts" in detail and detail["transcripts"]:
            text = detail["transcripts"][0].get("text", "")
        if "properties" in detail:
            duration_ms = detail["properties"].get("original_duration_in_milliseconds", 0)
        
        output = {
            "text": text,
            "duration_ms": duration_ms,
            "audio_url": audio_url
        }
        
        # Truncate text if too long
        if len(output["text"]) > Config.MAX_TEXT_LENGTH:
             output["text"] = output["text"][:Config.MAX_TEXT_LENGTH] + f"... (truncated, total: {len(output['text'])})"
        
        logger.info(f"✅ 快速转写完成: {text[:30]}...")
        return create_success_response(output, "simple_transcription")
        
    except Exception as e:
        logger.error(f"❌ 转写异常: {e}")
        return create_error_response("ProcessingError", str(e))


@mcp.tool
def get_server_status() -> str:
    """获取服务器状态"""
    return json.dumps({
        "success": True,
        "server": "Paraformer MCP Server (Enhanced)",
        "status": "running",
        "model": Config.MODEL,
        "supported_languages": Config.SUPPORTED_LANGUAGES,
        "tools": [
            "transcribe_audio - 完整转写（支持说话人分离、时间戳）",
            "transcribe_with_speakers - 多说话人转写",
            "get_word_timestamps - 词级时间戳",
            "transcribe_simple - 快速转写（仅文本）"
        ]
    }, ensure_ascii=False, indent=2)


# ==========================
# 服务器启动
# ==========================
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🎧 Paraformer 语音转写 MCP 服务器 (Enhanced)")
    logger.info("=" * 60)
    logger.info(f"📡 服务地址: http://{Config.HOST}:{Config.PORT}")
    logger.info(f"🤖 使用模型: {Config.MODEL}")
    logger.info("🛠️ 可用工具:")
    logger.info("   - transcribe_audio: 完整转写")
    logger.info("   - transcribe_with_speakers: 说话人分离")
    logger.info("   - get_word_timestamps: 词级时间戳")
    logger.info("   - transcribe_simple: 快速转写")
    logger.info("✅ 服务器启动中...")
    
    try:
        mcp.run(transport="sse", host=Config.HOST, port=Config.PORT)
    except KeyboardInterrupt:
        logger.info("\n👋 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)
