from typing import Union, Any, List, Dict
from compass.types.agent import SystemMessage, HumanMessage, AIMessage, ToolResult
from compass.utils.utility import HistoryLogger
import logging
import json

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, history_tracker: HistoryLogger):
        self.history_tracker = history_tracker
        self.memory = []
        self.recording_iteration = 0

    def add_message(self, message: Union[SystemMessage, HumanMessage, AIMessage, ToolResult]):
        self.memory.append(message)
        # Convert messages to JSON-serializable format
        serializable_messages = [
            {
                "type": message.__class__.__name__,
                "data": message.to_dict()
            }
            for message in self.memory
        ]
        self.history_tracker.save_messages(serializable_messages, self.recording_iteration)
        logger.info(f"Saved messages for iteration {self.recording_iteration} as a json file")
        self.recording_iteration += 1

    def _remove_old_screenshots(self, messages: List[Dict], images_to_keep: int | None = 1) -> List[Dict]:
        """Remove all but the final `images_to_keep` tool_result images"""
        if images_to_keep is None:
            return messages

        kept_images = 0
        for message in reversed(messages):
            content = message.get("content", [])
            new_content = []
            for content_block in reversed(content):
                if isinstance(content_block, dict) and content_block.get("type") == "tool_result":
                    tool_content = content_block.get("content", [])
                    filtered_tool_content = []
                    for item in tool_content:
                        if isinstance(item, dict) and item.get("type") == "image":
                            if kept_images < images_to_keep:
                                kept_images += 1
                                filtered_tool_content.append(item)
                        else:
                            filtered_tool_content.append(item)
                    content_block["content"] = filtered_tool_content
                new_content.append(content_block)
            message["content"] = list(reversed(new_content))
        return messages

    def _filter_tool_pairs(self, messages: List[Dict], offset: int = 10) -> List[Dict]:
        """Filter out old tool use/result pairs while preserving recent ones"""
        if offset >= len(messages):
            return messages

        messages_to_process = len(messages) - offset
        filtered = []
        
        i = 0
        while i < len(messages):
            if i >= messages_to_process:
                filtered.extend(messages[i:])
                break
            
            current = messages[i]
            is_tool_use = (
                current.get("role") == "assistant"
                and len(current.get("content", [])) == 1
                and current.get("content", [{}])[0].get("type") == "tool_use"
            )
            
            if not is_tool_use:
                filtered.append(current)
                i += 1
                continue
            
            if i + 1 < len(messages):
                next_msg = messages[i + 1]
                is_tool_result = (
                    next_msg.get("role") == "user"
                    and len(next_msg.get("content", [])) == 1
                    and next_msg.get("content", [{}])[0].get("type") == "tool_result"
                )
                
                if not is_tool_result:
                    filtered.append(current)
                i += 2
            else:
                filtered.append(current)
                i += 1
            
        return filtered

    def _truncate_tool_results(self, messages: List[Dict], max_chars: int = 50, offset: int = 4) -> List[Dict]:
        """Truncate text content in tool_results that are older than the offset"""
        if offset >= len(messages):
            return messages

        messages_to_process = len(messages) - offset
        
        for i in range(messages_to_process):
            content = messages[i].get("content", [])
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tool_content = block.get("content", [])
                    for item in tool_content:
                        if isinstance(item, dict) and item.get("type") == "text" and len(item.get("text", "")) > max_chars:
                            item["text"] = item["text"][:max_chars] + "..."

        return messages

    def optimize_messages(self, messages: List[Dict]) -> List[Dict]:
        """Apply all message optimization strategies"""
        messages = self._remove_old_screenshots(messages)
        messages = self._filter_tool_pairs(messages)
        messages = self._truncate_tool_results(messages)
        return messages