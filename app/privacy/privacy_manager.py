import os
import json
import threading
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from cryptography.fernet import Fernet


class PrivacyManager:
    """Handles privacy-focused conversation management with encrypted, in-memory caching.

    - Encryption key is provided via environment variable BOT_ENCRYPTION_KEY
    - User privacy preferences persist to user_privacy.json in project root
    - Cached context is encrypted and kept only in-memory with a short expiry
    """

    def __init__(self, cache_expiry_hours: int = 2):
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.temp_cache: Dict[str, Dict] = {}
        self.cache_expiry = timedelta(hours=cache_expiry_hours)
        self.user_preferences = self._load_user_preferences()
        self.lock = threading.Lock()

    def _get_or_create_encryption_key(self) -> bytes:
        """Generate or load encryption key (stored in environment)."""
        key = os.getenv('BOT_ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key().decode()
            print("⚠️  IMPORTANT: Add this to your .env file:")
            print(f'BOT_ENCRYPTION_KEY="{key}"')
            print("Without this key, cached conversations cannot be decrypted!")
        return key.encode() if isinstance(key, str) else key

    def _load_user_preferences(self) -> dict:
        """Load user privacy preferences."""
        try:
            if os.path.exists('user_privacy.json'):
                with open('user_privacy.json', 'r', encoding='utf-8') as handle:
                    return json.load(handle)
        except Exception as error:
            print(f"Error loading privacy preferences: {error}")
        return {}

    def _save_user_preferences(self) -> None:
        """Save user privacy preferences."""
        try:
            with open('user_privacy.json', 'w', encoding='utf-8') as handle:
                json.dump(self.user_preferences, handle, indent=2, ensure_ascii=False)
        except Exception as error:
            print(f"Error saving privacy preferences: {error}")

    def user_consents_to_caching(self, user_id: str) -> bool:
        """Check if user has consented to conversation caching."""
        return self.user_preferences.get(user_id, {}).get('allow_caching', False)

    def set_user_privacy_preference(self, user_id: str, allow_caching: bool) -> None:
        """Set user's privacy preference."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        self.user_preferences[user_id]['allow_caching'] = allow_caching
        self.user_preferences[user_id]['updated_at'] = datetime.now().isoformat()
        self._save_user_preferences()

    def _create_cache_key(self, user_id: str, channel_id: str) -> str:
        """Create hashed cache key (no personal info in key)."""
        combined = f"{user_id}:{channel_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def cache_context_temporarily(self, user_id: str, channel_id: str, context: Dict) -> None:
        """Cache context temporarily in encrypted memory."""
        if not self.user_consents_to_caching(user_id):
            return

        cache_key = self._create_cache_key(user_id, channel_id)

        context_json = json.dumps(context)
        encrypted_context = self.fernet.encrypt(context_json.encode())

        with self.lock:
            self.temp_cache[cache_key] = {
                'data': encrypted_context,
                'expires_at': datetime.now() + self.cache_expiry,
                'user_hash': hashlib.sha256(user_id.encode()).hexdigest()[:8],
            }

    def get_cached_context(self, user_id: str, channel_id: str) -> Optional[Dict]:
        """Retrieve and decrypt cached context if available."""
        if not self.user_consents_to_caching(user_id):
            return None

        cache_key = self._create_cache_key(user_id, channel_id)

        with self.lock:
            if cache_key not in self.temp_cache:
                return None

            cached_item = self.temp_cache[cache_key]

            if datetime.now() > cached_item['expires_at']:
                del self.temp_cache[cache_key]
                return None

            try:
                decrypted_json = self.fernet.decrypt(cached_item['data']).decode()
                return json.loads(decrypted_json)
            except Exception as error:
                print(f"Error decrypting cached context: {error}")
                del self.temp_cache[cache_key]
                return None

    def clear_user_cache(self, user_id: str) -> None:
        """Clear all cached data for a user."""
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
        with self.lock:
            keys_to_remove = [
                key for key, value in self.temp_cache.items()
                if value.get('user_hash') == user_hash
            ]
            for key in keys_to_remove:
                del self.temp_cache[key]

    def cleanup_expired_cache(self) -> None:
        """Remove expired cache entries."""
        current_time = datetime.now()
        with self.lock:
            expired_keys = [
                key for key, value in self.temp_cache.items()
                if current_time > value['expires_at']
            ]
            for key in expired_keys:
                del self.temp_cache[key]
            if expired_keys:
                print(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")


