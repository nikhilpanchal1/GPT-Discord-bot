import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import threading

class ConversationStorage:
    def __init__(self, storage_file: str = "conversations.json", max_history: int = 20, cleanup_days: int = 7):
        """
        Initialize conversation storage.
        
        Args:
            storage_file: Path to JSON file for persistence
            max_history: Maximum number of messages to keep per conversation
            cleanup_days: Days after which to cleanup old conversations
        """
        self.storage_file = storage_file
        self.max_history = max_history
        self.cleanup_days = cleanup_days
        self.conversations: Dict[str, List[Dict]] = {}
        self.lock = threading.Lock()
        self.load_conversations()
    
    def _get_conversation_key(self, user_id: str, channel_id: str) -> str:
        """Generate unique key for user-channel combination."""
        return f"{user_id}_{channel_id}"
    
    def load_conversations(self):
        """Load conversations from JSON file."""
        with self.lock:
            if os.path.exists(self.storage_file):
                try:
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.conversations = data.get('conversations', {})
                        self._cleanup_old_conversations()
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading conversations: {e}")
                    self.conversations = {}
    
    def save_conversations(self):
        """Save conversations to JSON file."""
        with self.lock:
            try:
                data = {
                    'conversations': self.conversations,
                    'last_updated': datetime.now().isoformat()
                }
                os.makedirs(os.path.dirname(self.storage_file) if os.path.dirname(self.storage_file) else '.', exist_ok=True)
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except IOError as e:
                print(f"Error saving conversations: {e}")
    
    def add_message(self, user_id: str, channel_id: str, role: str, content: str, model: str = "unknown"):
        """Add a message to the conversation history."""
        key = self._get_conversation_key(user_id, channel_id)
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'model': model
        }
        
        with self.lock:
            if key not in self.conversations:
                self.conversations[key] = []
            
            self.conversations[key].append(message)
            
            # Keep only the most recent messages
            if len(self.conversations[key]) > self.max_history:
                self.conversations[key] = self.conversations[key][-self.max_history:]
        
        self.save_conversations()
    
    def get_conversation_history(self, user_id: str, channel_id: str, max_messages: Optional[int] = None) -> List[Dict]:
        """Get conversation history for a user in a channel."""
        key = self._get_conversation_key(user_id, channel_id)
        
        with self.lock:
            history = self.conversations.get(key, [])
            if max_messages:
                history = history[-max_messages:]
            return history.copy()
    
    def clear_conversation(self, user_id: str, channel_id: str):
        """Clear conversation history for a user in a channel."""
        key = self._get_conversation_key(user_id, channel_id)
        
        with self.lock:
            if key in self.conversations:
                del self.conversations[key]
        
        self.save_conversations()
    
    def _cleanup_old_conversations(self):
        """Remove conversations older than cleanup_days."""
        cutoff_date = datetime.now() - timedelta(days=self.cleanup_days)
        
        keys_to_remove = []
        for key, messages in self.conversations.items():
            if messages:
                last_message_time = datetime.fromisoformat(messages[-1]['timestamp'])
                if last_message_time < cutoff_date:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.conversations[key]
    
    def get_conversation_count(self) -> int:
        """Get total number of active conversations."""
        with self.lock:
            return len(self.conversations)

# Global instance
conversation_storage = ConversationStorage() 