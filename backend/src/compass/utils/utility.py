import json
import os
from datetime import datetime
import uuid

class JSONLogger:
    def __init__(self, log_dir='logs'):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.session_id = str(uuid.uuid4())
        self.log_file = os.path.join(self.log_dir, f'session_{self.session_id}.json')
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