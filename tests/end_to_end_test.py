"""
End-to-End Test Script
======================
Demonstrates the full workflow:
1. Audio Agent: Transcribes audio using Paraformer.
2. Label Studio Agent: Imports the audio and transcription into Label Studio.
"""

import asyncio
import os
import sys
import logging
from audio_agent import create_agent_executor
from label_studio_agent import run_label_studio_agent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("e2e_test")

AUDIO_URL = "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"

async def run_test():
    logger.info("🚀 Starting End-to-End Test")
    
    # ---------------------------------------------------------
    # Step 1: Audio Agent - Transcription
    # ---------------------------------------------------------
    logger.info("\n" + "="*50)
    logger.info("🎧 Step 1: Audio Agent - Transcription")
    logger.info("="*50)
    
    agent, client, tools = await create_agent_executor()
    if not agent:
        logger.error("❌ Failed to create Audio Agent")
        return

    try:
        # Define the task
        task = f"Transcribe this audio using Paraformer: {AUDIO_URL}. Only return the transcription text."
        
        logger.info(f"📨 Sending task to Audio Agent: {task}")
        response = await agent.ainvoke({"messages": [("user", task)]})
        
        # Extract transcription from response
        # This assumes the agent returns the text in the last message
        transcription = response["messages"][-1].content
        logger.info(f"📝 Transcription Result: {transcription}")
        
    except Exception as e:
        logger.error(f"❌ Audio Agent failed: {e}")
        return
    finally:
        if hasattr(client, "aclose"):
            await client.aclose()

    # ---------------------------------------------------------
    # Step 2: Label Studio Agent - Import
    # ---------------------------------------------------------
    logger.info("\n" + "="*50)
    logger.info("🏷️ Step 2: Label Studio Agent - Import")
    logger.info("="*50)
    
    try:
        await run_label_studio_agent(AUDIO_URL, transcription)
        logger.info("✅ Label Studio Agent finished successfully")
    except Exception as e:
        logger.error(f"❌ Label Studio Agent failed: {e}")
        return

    logger.info("\n" + "="*50)
    logger.info("🎉 End-to-End Test Completed Successfully!")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(run_test())
