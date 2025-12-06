"""
Label Studio Specialist Agent
=============================
Responsible for:
1. Managing Label Studio Projects
2. Generating/Selecting Annotation Templates
3. Importing Analysis Data
"""

import logging
from typing import Dict, Any, Optional

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

from mcp_client.mcp_client import create_mcp_client

logger = logging.getLogger(__name__)

SUPER_AUDIO_TEMPLATE = r"""<View>
  <Header value="自动音频标注模版 (Super Audio Template)" style="font-weight: bold; font-size: 1.2em;" />
  
  <!-- Main Audio Player -->
  <Audio name="audio" value="$audio" zoom="true" hotkey="ctrl+enter" />

  <!-- 1. Region Details (Visible when a segment is selected) -->
  <View visibleWhen="region-selected" style="border: 1px solid #3498db; border-radius: 5px; padding: 15px; margin-top: 15px; background: #ebf5fb;">
    <Header value="1. 转录文本" size="5"/>
    
    <!-- ASR using Segments -->
    <Header value="片段转写" size="6"/>
    <TextArea name="segment_transcription" toName="audio" rows="2" editable="true" perRegion="true" required="false" placeholder="输入该片段的转写文本..." />

    <!-- Intent Classification -->
    <Header value="意图分类" size="6"/>
    <Choices name="intent" toName="audio" perRegion="true" showInline="true" choice="multiple">
      <Choice value="提问/咨询" />
      <Choice value="指令/命令" />
      <Choice value="陈述/回答" />
      <Choice value="闲聊" />
      <Choice value="投诉/抱怨" />
      <Choice value="预约/预订" />
      <Choice value="取消/退订" />
      <Choice value="确认/同意" />
      <Choice value="拒绝/否定" />
      <Choice value="问候/寒暄" />
      <Choice value="结束/再见" />
      <Choice value="请求帮助" />
      <Choice value="转人工" />
      <Choice value="满意" />
      <Choice value="不满意" />
      <Choice value="其他" />
    </Choices>

    <!-- Speaker Attributes -->
    <Header value="说话人信息" size="6"/>
    <Choices name="gender" toName="audio" perRegion="true" showInline="true">
      <Choice value="男" />
      <Choice value="女" />
      <Choice value="儿童" />
      <Choice value="未知" />
    </Choices>
    
    <Header value="情绪/情感" size="6"/>
    <Choices name="segment_sentiment" toName="audio" perRegion="true" showInline="true">
        <Choice value="积极" />
        <Choice value="中性" />
        <Choice value="消极" />
        <Choice value="愤怒" />
        <Choice value="悲伤" />
        <Choice value="焦虑" />
    </Choices>
  </View>

   <!-- 2. Segmentation, VAD, & Sound Events -->
   <!-- Crucial: Labels MUST be outside visibleWhen to allow creating segments -->
  <View style="border: 1px solid #e0e0e0; border-radius: 5px; padding: 15px; margin-top: 15px;">
    <Header value="2. 分段与事件检测 (VAD &amp; SED)" size="5"/>
    <Labels name="labels" toName="audio" choice="multiple" zoom="true">
      <!-- Voice Activity Detection -->
      <Label value="人声" background="#3498db" alias="speech" />
      <Label value="唤醒词" background="#2ecc71" alias="wake-word" />
      <Label value="底噪" background="#1abc9c" alias="vad-baseline" />
      
      <!-- Sound Event Detection -->
      <Label value="噪音" background="#95a5a6" />
      <Label value="静音" background="#ecf0f1" />
      <Label value="音乐" background="#e74c3c" />
      <Label value="笑声" background="#f1c40f" />
      <Label value="掌声" background="#8e44ad" />
      <Label value="咳嗽" background="#d35400" />
      <Label value="呼吸声" background="#e67e22" />
      <Label value="键盘声" background="#7f8c8d" />
      <Label value="铃声" background="#2c3e50" />
      <Label value="背景人声" background="#bdc3c7" />
      
      <!-- Speaker Diarization Placeholder (if not using Paragraphs) -->
      <Label value="说话人 1" background="#9b59b6" />
      <Label value="说话人 2" background="#8e44ad" />
      <Label value="说话人 3" background="#6c3483" />
      <Label value="说话人 4" background="#5b2c6f" />
    </Labels>
  </View>

  <!-- 4. Global Classification -->
  <View style="border: 1px solid #e0e0e0; border-radius: 5px; padding: 15px; margin-top: 15px;">
    <Header value="4. 全局属性" size="5"/>
    
    <Header value="话题分类" size="6"/>
    <Choices name="topic" toName="audio" choice="single-radio" showInline="true">
      <Choice value="政治" />
      <Choice value="经济/商业" />
      <Choice value="科技" />
      <Choice value="教育" />
      <Choice value="医疗健康" />
      <Choice value="体育" />
      <Choice value="娱乐" />
      <Choice value="法律" />
      <Choice value="客户服务" />
      <Choice value="日常生活" />
      <Choice value="交通出行" />
      <Choice value="其他" />
    </Choices>

    <Header value="整体情感" size="6"/>
    <Choices name="global_sentiment" toName="audio" showInline="true">
      <Choice value="积极" />
      <Choice value="中性" />
      <Choice value="消极" />
    </Choices>
    
    <Header value="备注" size="6"/>
    <TextArea name="summary" toName="audio" placeholder="输入整体备注或总结..." />
  </View>
</View>"""

LS_SYNTAX_GUIDE = """
**Label Studio XML Syntax Rules:**

1.  **Audio Tag**:
    -   Must be: `<Audio name="audio" value="$audio" ... />`
    -   Always use `value="$audio"`.

2.  **Control Tags (Labels, Choices, TextArea, Number)**:
    -   **Must Link**: All control tags MUST have `toName="audio"` to link to the audio player.
    -   **Region-Specific**: To make an attribute apply to a specific time segment (e.g., "Verse" mood), you MUST use `perRegion="true"`.
        -   Example: `<Choices name="mood" toName="audio" perRegion="true" ...>`
    -   **Visibility**: Use `visibleWhen="region-selected"` to hide segment details until a region is clicked.

3.  **Specific Tag Attributes**:
    -   **Labels**:
        -   `choice="multiple"` allows overlapping regions or multiple labels per region.
        -   Usage: `<Label value="LabelName" background="red" alias="short-code" />`
    -   **Choices**:
        -   `choice="single"` (dropdown), `choice="single-radio"` (radio buttons), `choice="multiple"` (checkboxes).
        -   `showInline="true"` displays choices horizontally.
        -   Usage: `<Choice value="Option1" />`, `<Choice value="Option2" />`
    -   **TextArea**:
        -   `rows="2"` (height), `maxSubmissions="1"` (limit entries), `editable="true"`.
        -   `displayMode="region-list"` (shows text next to region).
    -   **Number**:
        -   `min`, `max`, `step` attributes for validation.
        -   Usage: `<Number name="score" toName="audio" min="0" max="10" />`

4.  **Structure**:
    -   Use `<View>` to group elements.
    -   Define `<Labels>` first (to create regions).
    -   Define other attributes (Choices, TextArea) afterwards, often inside a `<View visibleWhen="region-selected">`.

5.  **Example Music Template Structure**:
    ```xml
    <View>
      <Audio name="audio" value="$audio" />
      <Header value="Music Segments" />
      <Labels name="labels" toName="audio" choice="multiple">
        <Label value="Verse" />
        <Label value="Chorus" />
        <Label value="Solo" />
      </Labels>
      <View visibleWhen="region-selected">
        <Header value="Segment Details" />
        <Choices name="mood" toName="audio" perRegion="true" choice="single-radio" showInline="true">
           <Choice value="Happy" />
           <Choice value="Sad" />
        </Choices>
        <Header value="Tempo (BPM)" />
        <Number name="tempo" toName="audio" perRegion="true" min="40" max="220" step="1" />
        <Header value="Notes" />
        <TextArea name="notes" toName="audio" perRegion="true" rows="2" />
      </View>
    </View>
    ```
"""

SYSTEM_PROMPT = f"""You are the **Label Studio Annotation Specialist**.
Your role is to manage the annotation workflow in Label Studio.

## Capabilities
- **Create Projects**: Set up new projects with specific configurations.
- **Template Engineering**: Choose or generate the correct XML template based on the data type.
- **Data Import**: Import verified JSON analysis data into projects.
- **Verification**: Check if imports were successful.

## Guidelines
1. **Always check existing projects** before creating a new one to avoid duplicates.
2. If the user asks for "Speech Annotation" (default), use the **Super Audio Template** below.
3. **Efficiency**: Do NOT use `write_todos` to constantly update status. Once you have successfully called `import_paraformer_analysis` (or similar), you are DONE. Return the final summary immediately.
4. **NO READING**: Do NOT try to read the JSON file content using `read_file` or similar tools. The file is too large and will break your context. Just pass the path to the import tool.
5. **Validation**: Trust the `import_paraformer_analysis` return value. If it says `success: True`, the task is complete.
6. If the user asks for "Music Annotation" or other domains, **generate a new XML** following the **Syntax Rules** below.

## Templates

### 1. Super Audio Template (Speech/Standard)
Use this exact XML for general speech tasks (pass this string to the `label_config` argument of `create_project`):
```xml
{SUPER_AUDIO_TEMPLATE}
```

### 2. Music/Custom Template Rules (Dynamic Generation)
When generating custom templates, STRICTLY follow these rules:
{LS_SYNTAX_GUIDE}
"""

async def create_annotation_agent(model_name: str, api_key: str, base_url: str):
    """Factory to create the LS Specialist Agent"""
    
    # 1. Connect to ONLY the Label Studio MCP Server
    client = await create_mcp_client(servers=["label_studio_server"])
    tools = await client.get_tools()
    
    # 2. visual-clean tools list
    logger.info(f"🏷️  LS Agent loaded tools: {[t.name for t in tools]}")
    
    # 3. Create Agent
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0
    )
    
    agent = create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT
    )
    
    return agent, client
