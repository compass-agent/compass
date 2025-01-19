from typing import Union, Any, List, Dict
from compass.types.agent import SystemMessage, HumanMessage, AIMessage, ToolResult
from compass.utils.utility import HistoryLogger
import logging
import json
from copy import deepcopy

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

    def _remove_old_screenshots(self, messages: List[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]], images_to_keep: int | None = 1) -> List[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]]:
        """Remove all but the final `images_to_keep` tool_result images"""
        if images_to_keep is None:
            return messages
            
        image_count = 0
        for msg in reversed(messages):  # Process messages in reverse to keep most recent
            if isinstance(msg, ToolResult) and msg.image:
                if image_count >= images_to_keep:
                    msg.image = None
                image_count += 1
                
        return messages

    def _filter_tool_pairs(self, messages: List[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]], offset: int = 10) -> List[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]]:
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
                isinstance(current, AIMessage) 
                and current.tool_calls is not None 
                and len(current.tool_calls) > 0
            )
            
            if not is_tool_use:
                filtered.append(current)
                i += 1
                continue
            # TODO: QAE: Check if this is sufficient. Currently it is expecting the tool result comes right after the tool use
            if i + 1 < len(messages):
                next_msg = messages[i + 1]
                is_tool_result = (
                    isinstance(next_msg, ToolResult) 
                    and next_msg.tool_call_id is not None
                    and any(tc.tool_call_id == next_msg.tool_call_id for tc in current.tool_calls)
                )
                
                if is_tool_result:
                    i += 2  # Skip both tool use and result
                else:
                    filtered.append(current)
                    i += 1
            else:
                filtered.append(current)
                i += 1
            
        return filtered

    def _truncate_tool_results(self, messages: List[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]], max_chars: int = 50, offset: int = 4) -> List[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]]:
        """Truncate text content in tool_results that are older than the offset"""
        if offset >= len(messages):
            return messages
        messages_to_process = len(messages) - offset
        for i in range(messages_to_process):
            msg = messages[i]
            if isinstance(msg, ToolResult) and msg.text and len(msg.text) > max_chars:
                msg.text = msg.text[:max_chars] + "..."

        return messages

    def optimize_messages(self, messages: List[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]]) -> List[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]]:
        """Apply all message optimization strategies"""
        messages_copy = deepcopy(messages)
        messages_copy = self._remove_old_screenshots(messages_copy)
        messages_copy = self._filter_tool_pairs(messages_copy)
        messages_copy = self._truncate_tool_results(messages_copy)
        return messages_copy