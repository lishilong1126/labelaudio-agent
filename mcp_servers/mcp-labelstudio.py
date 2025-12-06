"""
Label Studio MCP Server
=======================
Provides tools to interact with Label Studio via MCP.
Uses the official SDK for reliable authentication.
"""

import os
import logging
import json
import random
import string
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP
from dotenv import load_dotenv
from label_studio_sdk.client import LabelStudio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Config:
    API_KEY = os.getenv("LABEL_STUDIO_API_KEY")  # JWT refresh token  
    LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL", "http://localhost:8080")
    HOST = "127.0.0.1"
    PORT = int(os.getenv("MCP_LABELSTUDIO_PORT", 8002))

# Initialize SDK client (handles token refresh automatically)
_sdk_client: Optional[LabelStudio] = None

def get_sdk_client() -> LabelStudio:
    """Get or create SDK client."""
    global _sdk_client
    if _sdk_client is None:
        logger.info(f"🔌 Connecting to Label Studio at {Config.LABEL_STUDIO_URL}")
        _sdk_client = LabelStudio(
            base_url=Config.LABEL_STUDIO_URL,
            api_key=Config.API_KEY
        )
    return _sdk_client

# Initialize FastMCP
mcp = FastMCP("Label Studio Server")

@mcp.tool()
def create_project(title: str, description: str = "", label_config: str = "") -> str:
    """
    Create a new project in Label Studio.
    
    Args:
        title: Project title
        description: Project description
        label_config: Optional custom XML configuration. If not provided, a default simple audio template is used.
    """
    logger.info(f"📝 Creating project: {title}")
    
    try:
        client = get_sdk_client()
        
        # Default template if none provided
        if not label_config:
            label_config = '''<View>
              <Audio name="audio" value="$audio" zoom="true" hotkey="ctrl+enter" />
              <Header value="Transcription" />
              <TextArea name="transcription" toName="audio" rows="4" editable="true" maxSubmissions="1" />
            </View>'''
            logger.info("ℹ️ Using default Label Studio template")
        else:
            logger.info("🎨 Using custom Label Studio template")
        
        project = client.projects.create(
            title=title,
            description=description,
            label_config=label_config
        )
        
        # Convert to dict
        project_data = project.model_dump() if hasattr(project, "model_dump") else {
            "id": project.id,
            "title": project.title
        }
        
        return json.dumps({
            "success": True,
            "task_type": "create_project",
            "data": project_data
        }, default=str, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Failed to create project: {e}")
        return json.dumps({
            "success": False,
            "error": {"type": "CreateProjectError", "message": str(e)}
        })

@mcp.tool()
def get_projects() -> str:
    """Get list of projects."""
    logger.info("📋 Fetching projects...")
    
    try:
        client = get_sdk_client()
        projects = list(client.projects.list())
        
        projects_data = []
        for p in projects:
            projects_data.append({
                "id": p.id,
                "title": p.title
            })
            
        return json.dumps({
            "success": True,
            "task_type": "get_projects",
            "data": projects_data
        }, default=str, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch projects: {e}")
        return json.dumps({
            "success": False,
            "error": {"type": "GetProjectsError", "message": str(e)}
        })

@mcp.tool()
def import_task(project_id: int, audio_url: str, transcription: str) -> str:
    """Import a task (audio + transcription) into a project."""
    logger.info(f"📥 Importing task to project {project_id}...")
    
    try:
        client = get_sdk_client()
        
        task_data = [{
            "data": {
                "audio": audio_url,
                "transcription": transcription
            }
        }]
        
        result = client.projects.import_tasks(
            id=project_id,
            request=task_data
        )
        
        # Convert result
        result_data = result.model_dump() if hasattr(result, "model_dump") else {
            "task_count": getattr(result, "task_count", 1)
        }
            
        return json.dumps({
            "success": True,
            "task_type": "import_task",
            "data": result_data
        }, default=str, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Failed to import task: {e}")
        return json.dumps({
            "success": False,
            "error": {"type": "ImportTaskError", "message": str(e)}
        })

def _generate_id(length=10):
    """Generate a random ID for Label Studio result items."""
    chars = string.ascii_letters + string.digits + "-_"
    return ''.join(random.choice(chars) for _ in range(length))


def process_paraformer_analysis(project_id: int, audio_url: str, sentences: List[Dict]) -> str:
    """Core logic to process Paraformer analysis and import to Label Studio."""
    try:
        client = get_sdk_client()
        results = []
        
        # 1. ADD SEGMENT ANNOTATIONS
        for sentence in sentences:
            # Paraformer uses "begin_time" and "end_time" in milliseconds
            # Standard sentences might use "start"/"end"
            # We try both
            
            raw_start = sentence.get("begin_time", sentence.get("start", 0))
            raw_end = sentence.get("end_time", sentence.get("end", 0))
            
            # Convert ms to seconds
            # If value > 1000, assumes it is ms (Paraformer default)
            # If value is small float, assumes it is seconds
            start = float(raw_start) / 1000.0 if float(raw_start) > 1000 else float(raw_start)
            end = float(raw_end) / 1000.0 if float(raw_end) > 1000 else float(raw_end)

            text = sentence.get("text", "")
            speaker_id = sentence.get("speaker_id", 0) 
            
            # Fallback for invalid duration
            if end <= start:
                end = start + 2.0 
                
            seg_id = _generate_id()
            
            # A. Labels (Speech) - The Main Region
            # Note: "labels" control defines the region duration.
            results.append({
                "id": seg_id,
                "from_name": "labels",
                "to_name": "audio",
                "type": "labels",
                "origin": "manual",
                "value": {
                    "start": start,
                    "end": end,
                    "channel": 0,
                    "labels": ["人声"] # Map 'speech' to '人声' as per actual config
                }
            })
            
            # B. Transcription (Linked to same seg_id)
            results.append({
                "id": seg_id,
                "from_name": "segment_transcription",
                "to_name": "audio",
                "type": "textarea",
                "origin": "manual",
                "value": {
                    "start": start,
                    "end": end,
                    "channel": 0,
                    "text": [text]
                }
            })
            
            # C. Speaker (Linked to same seg_id)
            # Map speaker_id to "speaker X"
            # Actual config supports "speaker 0" to "speaker 2", default to "speaker 0" if out of range
            safe_spk_id = speaker_id if speaker_id is not None else 0
            if safe_spk_id > 2: 
                safe_spk_id = 0 # Fallback for template limit
                
            spk_val = f"speaker {safe_spk_id}"
            results.append({
                "id": seg_id,
                "from_name": "speaker",
                "to_name": "audio",
                "type": "choices",
                "origin": "manual",
                "value": {
                    "start": start,
                    "end": end,
                    "channel": 0,
                    "choices": [spk_val]
                }
            })
            
            # D. Gender (Linked to same seg_id)
            results.append({
                "id": seg_id,
                "from_name": "gender",
                "to_name": "audio",
                "type": "choices",
                "origin": "manual",
                "value": {
                    "start": start,
                    "end": end,
                    "channel": 0,
                    "choices": ["未知"]
                }
            })
            
            # E. Segment Sentiment (Linked to same seg_id)
            results.append({
                "id": seg_id,
                "from_name": "segment_sentiment",
                "to_name": "audio",
                "type": "choices",
                "origin": "manual",
                "value": {
                    "start": start,
                    "end": end,
                    "channel": 0,
                    "choices": ["中性"]
                }
            })
            
            # F. Sound Event (Linked to same seg_id)
            # Default to "单说话人" for detailed speech segments
            results.append({
                "id": seg_id,
                "from_name": "sound event",
                "to_name": "audio",
                "type": "choices",
                "origin": "manual",
                "value": {
                    "start": start,
                    "end": end,
                    "channel": 0,
                    "choices": ["单说话人"]
                }
            })

        # 2. ADD GLOBAL ATTRIBUTES
        results.append({
            "id": _generate_id(),
            "from_name": "topic",
            "to_name": "audio",
            "type": "choices",
            "origin": "manual",
            "value": {
                "choices": ["日常生活"]
            }
        })
        
        results.append({
            "id": _generate_id(),
            "from_name": "global_sentiment",
            "to_name": "audio",
            "type": "choices",
            "origin": "manual",
            "value": {
                "choices": ["中性"]
            }
        })

        # Construct Task Payload
        task_payload = {
            "data": {
                "audio": audio_url
            },
            "annotations": [{
                "result": results
            }]
        }
        
        import_resp = client.projects.import_tasks(
            id=project_id,
            request=[task_payload]
        )
        
        return json.dumps({
            "success": True, 
            "task_type": "import_paraformer_analysis",
            "imported_count": len(import_resp) if isinstance(import_resp, list) else 1
        }, default=str)

    except Exception as e:
        logger.error(f"❌ Failed to import analysis: {e}")
        return json.dumps({
            "success": False,
            "error": {"type": "ImportAnalysisError", "message": str(e)}
        })

@mcp.tool()
def import_paraformer_analysis(project_id: int, audio_url: str, analysis_data: str) -> str:
    """
    Import Paraformer analysis results as a pre-annotated task.
    
    Args:
        project_id: The Label Studio project ID.
        audio_url: The URL of the audio file.
        analysis_data: JSON string OR absolute file path containing the Paraformer result.
                       Passing a file path is recommended for large results to avoid context overflow.
    """
    # Parse analysis data
    if isinstance(analysis_data, str):
        # Clean path string (remove quotes, whitespace, potential markdown)
        clean_path = analysis_data.strip().strip("'\"`").replace("\n", "")
        
        # 1. Check if it's a file path
        if len(clean_path) < 1024 and os.path.exists(clean_path):
            logger.info(f"📂 Reading analysis data from file: {clean_path}")
            try:
                with open(clean_path, 'r', encoding='utf-8') as f:
                    sentences = json.load(f)
            except Exception as e:
                logger.error(f"❌ Failed to read analysis file: {e}")
                return json.dumps({"success": False, "error": f"Failed to read analysis file: {str(e)}"})
        
        # 2. Try parsing as JSON string (backward compatibility) or if file not found
        else:
            # If it looks like a path but wasn't found, return specific error
            if clean_path.startswith("/") and len(clean_path) < 1024:
                 return json.dumps({"success": False, "error": f"Error: File '{clean_path}' not found"})
                 
            try:
                sentences = json.loads(analysis_data)
            except json.JSONDecodeError:
                return json.dumps({"success": False, "error": "Invalid JSON format"})
    else:
        sentences = analysis_data

    # Handle standard paraformer structure or simplified list or lightweight response
    if isinstance(sentences, dict):
        # Case: Lightweight response with file path
        if "full_result_path" in sentences:
            path = sentences["full_result_path"]
            logger.info(f"📂 Found reference to file in input dict: {path}")
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        loaded_data = json.load(f)
                    # Use the loaded data as sentences (it should be the full result dict)
                    sentences = loaded_data
                except Exception as e:
                     return json.dumps({"success": False, "error": f"Failed to read referenced file '{path}': {str(e)}"})
            else:
                 return json.dumps({"success": False, "error": f"Referenced file not found: {path}"})
        
        # Now handle the dict (either original or loaded from file)
        if "sentences" in sentences:
            sentences = sentences["sentences"]
            
    # If we loaded from file, `sentences` is likely the full output dict
    if isinstance(sentences, dict) and "sentences" in sentences:
         sentences = sentences["sentences"]
            
    # If we loaded from file, `sentences` is likely the full output dict
    if isinstance(sentences, dict) and "sentences" in sentences:
         sentences = sentences["sentences"]
         
    if not isinstance(sentences, list):
            return json.dumps({"success": False, "error": "analysis_data must be a list of sentences or dict with 'sentences' key"})
            
    return process_paraformer_analysis(project_id, audio_url, sentences)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🏷️ Label Studio MCP Server")
    logger.info("=" * 60)
    logger.info(f"📡 Server: http://{Config.HOST}:{Config.PORT}")
    logger.info(f"🔗 Label Studio: {Config.LABEL_STUDIO_URL}")
    logger.info("✅ Starting server...")
    
    try:
        mcp.run(transport="sse", host=Config.HOST, port=Config.PORT)
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        import sys
        sys.exit(1)
