import json
import os
from datetime import datetime
import random
import string
from pathlib import Path
import logging
from typing import Optional
from functools import wraps
from time import time
import asyncio  # Import asyncio to check for coroutine functions

logger = logging.getLogger(__name__)

def log_execution_time(logger):
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            # Async wrapper
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time()
                start_datetime = datetime.now()
                
                result = await func(*args, **kwargs)  # Await the async function
                
                end_time = time()
                end_datetime = datetime.now()
                
                execution_time_ms = (end_time - start_time) * 1000
                start_formatted = start_datetime.strftime('%M:%S.%f')[:-3]
                end_formatted = end_datetime.strftime('%M:%S.%f')[:-3]
                
                logger.info(
                    f"Method {func.__name__} took {execution_time_ms:.2f}ms "
                    f"between times {start_formatted} to {end_formatted}"
                )
                
                return result
            return wrapper
        else:
            # Sync wrapper
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time()
                start_datetime = datetime.now()
                
                result = func(*args, **kwargs)
                
                end_time = time()
                end_datetime = datetime.now()
                
                execution_time_ms = (end_time - start_time) * 1000
                start_formatted = start_datetime.strftime('%M:%S.%f')[:-3]
                end_formatted = end_datetime.strftime('%M:%S.%f')[:-3]
                
                logger.info(
                    f"Method {func.__name__} took {execution_time_ms:.2f}ms "
                    f"between times {start_formatted} to {end_formatted}"
                )
                
                return result
            return wrapper
    return decorator

class HistoryLogger:
    def __init__(self, log_dir='logs'):
        timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        random_suffix = ''.join(random.choices(string.digits, k=4))
        self.session_id = f"{timestamp}-{random_suffix}"
        
        self.log_dir = Path(log_dir) / self.session_id
        self.screenshots_dir = self.log_dir / 'screenshots'
        self.prompts_dir = self.log_dir / 'llm_prompt'
        
        # Create all necessary directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.log_dir / 'history.json'
        self.app_log_file = self.log_dir / 'app.log'
        self.logs = []
        
        SessionManager.set_history_tracker(self)
        self._configure_logging()

    def _configure_logging(self):
        """Configure both file and console logging"""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File handler
        file_handler = logging.FileHandler(self.app_log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Configure specific loggers
        engineio_logger = logging.getLogger('engineio.server')
        engineio_logger.setLevel(logging.WARNING)

        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.WARNING)

    @property
    def session_path(self) -> Path:
        """Get the base path for this session's logs"""
        return self.log_dir

    def save_messages(self, message: dict, filename: str) -> None:
        """Save a single message to a JSON file in the session directory"""
        messages_file = self.log_dir / f'{filename}.json'
        try:
            with open(messages_file, 'w') as f:
                json.dump(message, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save message: {e}")

    @staticmethod
    def get_timestamp_filename() -> str:
        """Generate a filename-safe timestamp in mm:ss:ms format"""
        now = datetime.now()
        return now.strftime('%M_%S_%f')[:9]  # Gets MM_SS_xxx format

class TokenTracker:
    def __init__(self):
        # Initialize counters for different types of tokens
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_creation_input_tokens = 0
        self.total_cache_read_input_tokens = 0
        
        # Cost rates (per million tokens)
        self.input_token_cost_per_million = 3.0  # $3 per 1M tokens
        self.output_token_cost_per_million = 15.0  # $15 per 1M tokens
        self.cache_creation_cost_per_million = 3.75  # $3.75 per 1M tokens
        self.cache_read_cost_per_million = 0.30  # $0.30 per 1M tokens

    def track_usage(self, 
                   input_tokens: int, 
                   output_tokens: int,
                   cache_creation_input_tokens: int = 0,
                   cache_read_input_tokens: int = 0) -> None:
        # Calculate costs for current iteration
        input_cost = (input_tokens / 1_000_000) * self.input_token_cost_per_million
        output_cost = (output_tokens / 1_000_000) * self.output_token_cost_per_million
        cache_creation_cost = (cache_creation_input_tokens / 1_000_000) * self.cache_creation_cost_per_million
        cache_read_cost = (cache_read_input_tokens / 1_000_000) * self.cache_read_cost_per_million
        
        # Calculate total cost for current iteration
        current_total_cost = input_cost + output_cost + cache_creation_cost + cache_read_cost
        
        # Update totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cache_creation_input_tokens += cache_creation_input_tokens
        self.total_cache_read_input_tokens += cache_read_input_tokens
        
        # Calculate total costs
        total_input_cost = (self.total_input_tokens / 1_000_000) * self.input_token_cost_per_million
        total_output_cost = (self.total_output_tokens / 1_000_000) * self.output_token_cost_per_million
        total_cache_creation_cost = (self.total_cache_creation_input_tokens / 1_000_000) * self.cache_creation_cost_per_million
        total_cache_read_cost = (self.total_cache_read_input_tokens / 1_000_000) * self.cache_read_cost_per_million
        
        # Calculate cumulative total cost
        cumulative_total_cost = total_input_cost + total_output_cost + total_cache_creation_cost + total_cache_read_cost
        
        # Log current iteration and totals
        logger.info(
            f"Current Usage:\n"
            f"  Input Tokens: {input_tokens} (${input_cost:.4f})\n"
            f"  Output Tokens: {output_tokens} (${output_cost:.4f})\n"
            f"  Cache Creation Tokens: {cache_creation_input_tokens} (${cache_creation_cost:.4f})\n"
            f"  Cache Read Tokens: {cache_read_input_tokens} (${cache_read_cost:.4f})\n"
            f"  Total Cost: ${current_total_cost:.4f}"
        )
        logger.info(
            f"Total Usage:\n"
            f"  Input Tokens: {self.total_input_tokens} (${total_input_cost:.4f})\n"
            f"  Output Tokens: {self.total_output_tokens} (${total_output_cost:.4f})\n"
            f"  Cache Creation Tokens: {self.total_cache_creation_input_tokens} (${total_cache_creation_cost:.4f})\n"
            f"  Cache Read Tokens: {self.total_cache_read_input_tokens} (${total_cache_read_cost:.4f})\n"
            f"  Cumulative Total Cost: ${cumulative_total_cost:.4f}"
        )

class SessionManager:
    _instance = None
    _history_tracker = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_history_tracker(cls, history_tracker: HistoryLogger):
        cls._history_tracker = history_tracker

    @classmethod
    def get_history_tracker(cls) -> Optional[HistoryLogger]:
        return cls._history_tracker