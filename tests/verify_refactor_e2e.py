
import asyncio
import os
import sys

# Add project root to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from agents.orchestrator import create_master_agent
from config import Config
from mcp_client.agent_logger import AgentExecutionLogger

# Load env
load_dotenv()

async def run_verification():
    print("🚀 Starting Refactor Verification Test...")
    
    # User inputs
    audio_url = "https://shilong-test.oss-cn-beijing.aliyuncs.com/DB_0528_0011_01_2_A_0003.wav?Expires=1765056363&OSSAccessKeyId=TMP.3KnFwd6kF79GN4hDxRzyWRrQNZd9VWYWy1Acd11vr1RCp246vwqmGaddiKc9VG2BmQfsoBVhCBL9KXaBpktUvBpANfSh9q&Signature=54euKF3xI8HlZj29spcJXPAKGrs%3D"
    task_description = "请帮我对这调音频进行分析标注 ，文字转录 音频片段起止时间 说话人 音频事件 等内容；并最终将结果导入到Labelstudio中"
    
    full_prompt = f"Audio URL: {audio_url}\nTask: {task_description}"
    
    print(f"📝 Task: {task_description}")
    print(f"🔗 Audio: {audio_url}")
    
    try:
        # 1. Initialize Master Agent
        print("\n🔧 Initializing Master Agent...")
        agent, clients = await create_master_agent()
        
        if not agent:
            print("❌ Failed to create agent.")
            return

        # 2. Run Agent
        print("\n🏃 running agent.ainvoke...")
        execution_logger = AgentExecutionLogger()
        
        response = await agent.ainvoke(
            {"messages": [("user", full_prompt)]},
            config={"callbacks": [execution_logger]}
        )
        
        # 3. Print Result
        print("\n✅ Execution Complete.")
        print("-" * 50)
        if isinstance(response, dict) and "messages" in response:
            print(response["messages"][-1].content)
        else:
            print(response)
        print("-" * 50)
        
        # Cleanup
        for client in clients:
            if hasattr(client, "aclose"):
                await client.aclose()
                
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_verification())
