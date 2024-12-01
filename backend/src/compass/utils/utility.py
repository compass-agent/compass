import json
import os
from datetime import datetime
import random
import string
from pathlib import Path

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
        
        self.log_file = self.log_dir / 'logs.json'
        self.logs = []

    def log_action(self, action_type, content):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'action_type': action_type,
            'content': content
        }
        self.logs.append(log_entry)
        self._write_to_file()

    def _write_to_file(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.logs, f, indent=4)

    @property
    def session_path(self) -> Path:
        """Get the base path for this session's logs"""
        return self.log_dir