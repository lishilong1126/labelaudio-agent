
import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_client.mcp_client import create_mcp_client

async def manual_import():
    print("🚀 Starting Manual Import Fix...")
    
    # 1. Connect to Label Studio Server
    client = await create_mcp_client(servers=["label_studio_server"])
    
    project_title = "Final_Acceptance_Project_Fixed"
    # Audio URL from the user request
    audio_url = "https://shilong-test.oss-cn-beijing.aliyuncs.com/DB_0528_0011_01_2_A_0003.wav?Expires=1765048679&OSSAccessKeyId=TMP.3KnFwd6kF79GN4hDxRzyWRrQNZd9VWYWy1Acd11vr1RCp246vwqmGaddiKc9VG2BmQfsoBVhCBL9KXaBpktUvBpANfSh9q&Signature=ujgxnhnYJtO0ogVSbdC%2Bc9EPxYU%3D"
    
    # The actual file path found in tmp_results
    analysis_file = "/Users/bytedance/Downloads/dev/labelaudio-agent/tmp_results/paraformer_result_b6237f4b44584d2fb33dccfbe5a59b5a.json"
    
    # Super Audio Template
    super_template = """<View>
  <Audio name="audio" value="$audio" zoom="true" hotkey="ctrl+enter" />
  <Header value="Transcription" />
  <TextArea name="transcription" toName="audio" rows="4" editable="true" maxSubmissions="1" />
  <Header value="Speaker Diarization" />
  <Labels name="speaker" toName="audio" choice="multiple">
    <Label value="Speaker 0" background="#FF0000" />
    <Label value="Speaker 1" background="#00FF00" />
    <Label value="Speaker 2" background="#0000FF" />
  </Labels>
  <Header value="Audio Events" />
  <Labels name="events" toName="audio" choice="multiple">
    <Label value="Music" background="#FFA500" />
    <Label value="Noise" background="#808080" />
    <Label value="Laughter" background="#FFC0CB" />
  </Labels>
</View>"""

    try:
        # 2. Get Tools
        print("🛠️  Fetching tools...")
        tools = await client.get_tools()
        tool_map = {t.name: t for t in tools}
        
        if "create_project" not in tool_map:
            print("❌ Tool 'create_project' not found!")
            return

        # 3. Create Project
        print(f"📝 Creating project '{project_title}'...")
        create_project_tool = tool_map["create_project"]
        result = await create_project_tool.ainvoke({
            "title": project_title, 
            "description": "Manually fixed import of audio analysis",
            "label_config": super_template
        })
        print(f"Create Result: {result}")
        
        # Robust ID extraction
        project_id = None
        import json
        
        # Check if result is already a dict
        if isinstance(result, dict) and "data" in result:
             project_id = result["data"].get("id")
        # Check if it's a string, try parsing as JSON
        elif isinstance(result, str):
            try:
                data = json.loads(result)
                if "data" in data:
                    project_id = data["data"].get("id")
            except:
                pass
        
        # Fallback to regex if needed (matching "id": 13)
        if not project_id:
            import re
            match = re.search(r'"id":\s*(\d+)', str(result))
            if match:
                project_id = int(match.group(1))

        if project_id:
            print(f"✅ Project ID: {project_id}")
            
            # 4. Import Data
            if "import_paraformer_analysis" in tool_map:
                print(f"📤 Importing analysis from {analysis_file}...")
                import_tool = tool_map["import_paraformer_analysis"]
                import_result = await import_tool.ainvoke({
                    "project_id": project_id,
                    "audio_url": audio_url,
                    "analysis_data": analysis_file
                })
                print(f"Import Result: {import_result}")
            else:
                print("❌ Tool 'import_paraformer_analysis' not found!")
        else:
            print("❌ Failed to get Project ID")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # client might not have aclose, use cleanup if needed or ignore
        pass

if __name__ == "__main__":
    asyncio.run(manual_import())
