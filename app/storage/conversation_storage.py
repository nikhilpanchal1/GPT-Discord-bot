import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
import threading


class ConversationStorage:
    """Enhanced conversation storage with better memory management"""

    def __init__(self, storage_file: str = "conversations.json"):
        self.storage_file = storage_file
        self.conversations: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.max_messages_per_conversation = 20
        self.conversation_retention_days = 7
        self.load_conversations()

    def load_conversations(self) -> None:
        """Load conversations from file with error handling"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as file_handle:
                    data = json.load(file_handle)
                    self.conversations = data
                    self.cleanup_old_conversations()
            else:
                self.conversations = {}
        except Exception as error:
            print(f"Error loading conversations: {error}")
            self.conversations = {}

    def save_conversations(self) -> None:
        """Save conversations to file with error handling"""
        try:
            with self.lock:
                with open(self.storage_file, 'w', encoding='utf-8') as file_handle:
                    json.dump(self.conversations, file_handle, indent=2, ensure_ascii=False)
        except Exception as error:
            print(f"Error saving conversations: {error}")

    def cleanup_old_conversations(self) -> None:
        """Remove old conversations based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=self.conversation_retention_days)
        cutoff_timestamp = cutoff_date.isoformat()

        keys_to_remove: List[str] = []
        for key, conversation in self.conversations.items():
            if conversation.get('messages'):
                # Check the last message timestamp
                last_message = conversation['messages'][-1]
                if last_message.get('timestamp', '') < cutoff_timestamp:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.conversations[key]

        if keys_to_remove:
            print(f"Cleaned up {len(keys_to_remove)} old conversations")
            self.save_conversations()

    def get_conversation_key(self, user_id: str, channel_id: str) -> str:
        """Generate conversation key"""
        return f"{user_id}:{channel_id}"

    def get_conversation_history(self, user_id: str, channel_id: str) -> List[Dict]:
        """Get conversation history for a user in a specific channel"""
        key = self.get_conversation_key(user_id, channel_id)

        if key not in self.conversations:
            return []

        conversation = self.conversations[key]
        messages = conversation.get('messages', [])

        # Return only the message content and role for AI processing
        return [
            {
                'role': message['role'],
                'content': message['content'],
                'timestamp': message['timestamp']
            }
            for message in messages
        ]

    def add_message(self, user_id: str, channel_id: str, role: str, content: str) -> None:
        """Add a message to conversation history"""
        key = self.get_conversation_key(user_id, channel_id)
        current_time = datetime.now().isoformat()

        if key not in self.conversations:
            self.conversations[key] = {
                'user_id': user_id,
                'channel_id': channel_id,
                'created_at': current_time,
                'last_activity': current_time,
                'messages': []
            }

        # Add new message
        message = {
            'role': role,
            'content': content[:2000],  # Truncate very long messages
            'timestamp': current_time
        }

        self.conversations[key]['messages'].append(message)
        self.conversations[key]['last_activity'] = current_time

        # Trim conversation if too long
        if len(self.conversations[key]['messages']) > self.max_messages_per_conversation:
            # Keep the most recent messages
            self.conversations[key]['messages'] = self.conversations[key]['messages'][-self.max_messages_per_conversation:]

        # Save to file
        self.save_conversations()

    def clear_conversation(self, user_id: str, channel_id: str) -> None:
        """Clear conversation history for a specific user/channel"""
        key = self.get_conversation_key(user_id, channel_id)

        if key in self.conversations:
            del self.conversations[key]
            self.save_conversations()

    def get_conversation_stats(self) -> Dict:
        """Get statistics about stored conversations"""
        total_conversations = len(self.conversations)
        total_messages = sum(len(conv.get('messages', [])) for conv in self.conversations.values())

        # Count active conversations (activity in last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        cutoff_timestamp = cutoff.isoformat()

        active_conversations = sum(
            1 for conv in self.conversations.values()
            if conv.get('last_activity', '') > cutoff_timestamp
        )

        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'active_conversations_24h': active_conversations
        }


