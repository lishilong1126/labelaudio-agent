"""
Functional Test for Audio Agent (MCP Mode)
==========================================
This script tests the audio_agent.py by running it as a subprocess.
Prerequisites:
1. mcp-qwen-analyze-audio.py MUST be running in a separate terminal.
2. DASHSCOPE_API_KEY and OPENAI_API_KEY must be set.
"""

import os
import sys
import subprocess
import time

# Sample Audio URL
TEST_AUDIO_URL = "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"

def run_agent_process(task_description):
    print(f"\n{'='*50}")
    print(f"🧪 Testing Task: {task_description}")
    print(f"{'='*50}")
    
    cmd = [
        sys.executable, 
        "audio_agent.py", 
        TEST_AUDIO_URL, 
        task_description
    ]
    
    try:
        # Run the agent script
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60  # Timeout after 60 seconds
        )
        
        if result.returncode == 0:
            print("✅ Output:")
            print(result.stdout)
            return True
        else:
            print("❌ Failed with error:")
            print(result.stderr)
            print(result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timed out! Agent took too long.")
        return False
    except Exception as e:
        print(f"❌ Error running process: {e}")
        return False

def main():
    print("🚀 Starting Audio Agent Functional Tests (MCP Mode)")
    print("⚠️  Ensure 'python mcp-qwen-analyze-audio.py' is running on port 8000!")
    
    # Check if port 8000 is open (simple check)
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8000))
    sock.close()
    
    if result != 0:
        print("\n❌ Error: MCP Server does not seem to be running on port 8000.")
        print("Please run: python mcp-qwen-analyze-audio.py")
        return

    # Test 1: Transcription
    run_agent_process("Transcribe this audio")
    
    # Test 2: Speaker Analysis
    run_agent_process("Analyze the speaker")

if __name__ == "__main__":
    main()
