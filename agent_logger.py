"""
Custom Callback Handler for Deep Agent
======================================
记录 Agent 执行过程中的详细日志
"""

import logging
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)

class AgentExecutionLogger(BaseCallbackHandler):
    """自定义回调处理器，用于记录 Agent 执行的详细过程"""
    
    def __init__(self):
        self.step_count = 0
        self.tool_calls = []
        
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """LLM 开始调用时"""
        logger.info("=" * 80)
        logger.info("🧠 LLM 推理开始")
        logger.info(f"📝 Prompt 长度: {len(prompts[0]) if prompts else 0} 字符")
        
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 调用结束时"""
        if response.generations:
            content = response.generations[0][0].text
            logger.info(f"💭 LLM 响应: {content[:200]}..." if len(content) > 200 else f"💭 LLM 响应: {content}")
        logger.info("✅ LLM 推理完成")
        
    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any,
    ) -> None:
        """Chat Model 开始时"""
        self.step_count += 1
        logger.info("=" * 80)
        logger.info(f"🤖 Agent 步骤 #{self.step_count}")
        logger.info(f"📨 消息数量: {len(messages[0]) if messages else 0}")
        
        # 记录最后一条用户消息
        if messages and messages[0]:
            last_msg = messages[0][-1]
            logger.info(f"👤 用户输入: {last_msg.content[:100]}...")
            
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """工具调用开始时"""
        tool_name = serialized.get("name", "Unknown")
        logger.info("-" * 80)
        logger.info(f"🔧 工具调用: {tool_name}")
        logger.info(f"📥 输入参数: {input_str[:200]}...")
        
        self.tool_calls.append({
            "tool": tool_name,
            "input": input_str,
            "step": self.step_count
        })
        
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """工具调用结束时"""
        logger.info(f"📤 工具输出: {output[:200]}..." if len(output) > 200 else f"📤 工具输出: {output}")
        logger.info("✅ 工具执行完成")
        
    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """工具调用出错时"""
        logger.error(f"❌ 工具执行失败: {str(error)}")
        
    def on_agent_action(self, action, **kwargs: Any) -> None:
        """Agent 决定执行动作时"""
        logger.info("=" * 80)
        logger.info("🎯 Agent 决策")
        logger.info(f"🔍 意图识别: 调用工具 '{action.tool}'")
        logger.info(f"📋 任务规划: {action.tool_input}")
        
    def on_agent_finish(self, finish, **kwargs: Any) -> None:
        """Agent 完成执行时"""
        logger.info("=" * 80)
        logger.info("🏁 Agent 执行完成")
        logger.info(f"📊 总步骤数: {self.step_count}")
        logger.info(f"🔧 工具调用次数: {len(self.tool_calls)}")
        
        if self.tool_calls:
            logger.info("📝 工具调用摘要:")
            for i, call in enumerate(self.tool_calls, 1):
                logger.info(f"  {i}. {call['tool']} (步骤 #{call['step']})")
                
        logger.info(f"✨ 最终输出: {finish.return_values.get('output', 'N/A')[:200]}...")
        logger.info("=" * 80)
        
        # 重置计数器
        self.step_count = 0
        self.tool_calls = []
        
    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Chain 开始时"""
        logger.info("🔗 执行链开始")
        
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Chain 结束时"""
        logger.info("🔗 执行链完成")
