import json
import os
from datetime import datetime
import random
import string
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class HistoryLogger:
    def __init__(self, log_dir='logs'):
        # Generate session ID with timestamp and 4 random digits
        timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        random_suffix = ''.join(random.choices(string.digits, k=4))
        self.session_id = f"{timestamp}-{random_suffix}"
        
        self.log_dir = Path(log_dir) / self.session_id
        self.screenshots_dir = self.log_dir / 'screenshots'
        
        # Create directory structure
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging files
        self.history_file = self.log_dir / 'history.json'
        self.app_log_file = self.log_dir / 'app.log'
        self.logs = []
        
        # Create history file if it doesn't exist
        if not self.history_file.exists():
            with open(self.history_file, 'w') as f:
                json.dump([], f)
        
        # Configure logging
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

    def log_action(self, action_type, content):
        """Log specialized history actions"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'action_type': action_type,
            'content': content
        }
        self.logs.append(log_entry)
        self._write_to_file()

    def _write_to_file(self):
        """Write history logs to JSON file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.logs, f, indent=4)

    @property
    def session_path(self) -> Path:
        """Get the base path for this session's logs"""
        return self.log_dir

class TokenTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.input_token_cost_per_million = 3.0  # $3 per 1M tokens
        self.output_token_cost_per_million = 15.0  # $15 per 1M tokens

    def track_usage(self, input_tokens: int, output_tokens: int) -> None:
        # Calculate costs for current iteration
        input_cost = (input_tokens / 1_000_000) * self.input_token_cost_per_million
        output_cost = (output_tokens / 1_000_000) * self.output_token_cost_per_million
        
        # Update totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        total_input_cost = (self.total_input_tokens / 1_000_000) * self.input_token_cost_per_million
        total_output_cost = (self.total_output_tokens / 1_000_000) * self.output_token_cost_per_million
        
        # Log current iteration and totals
        logger.info(f"Current: input_tokens={input_tokens} (${input_cost:.4f}), output_tokens={output_tokens} (${output_cost:.4f})")
        logger.info(f"Total: input_tokens={self.total_input_tokens} (${total_input_cost:.4f}), output_tokens={self.total_output_tokens} (${total_output_cost:.4f})")