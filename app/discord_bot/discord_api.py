from dotenv import load_dotenv
import os
import asyncio
import discord
import aiohttp
from app.ai_model.openai import get_ai_response
from app.ai_model.gemini import get_gemini_response
from app.utils.file_utils import FileProcessor
from app.privacy.privacy_manager import PrivacyManager

load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
PRIVACY_MODE = os.getenv('PRIVACY_MODE', 'strict').lower()  # strict, balanced, permissive

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_processor = FileProcessor()
        self.privacy_manager = PrivacyManager()

    async def on_ready(self):
        print(f'🔐 Privacy-Enhanced Bot logged in as {self.user}!')
        print(f'Privacy Mode: {PRIVACY_MODE.upper()}')
        print(f'Encryption: {"Enabled" if hasattr(self.privacy_manager, "fernet") else "Disabled"}')
        # Start periodic cleanup for expired cache
        asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self):
        """Periodic cleanup of expired cache and temporary data"""
        while True:
            await asyncio.sleep(300)
            self.privacy_manager.cleanup_expired_cache()
    
    async def get_conversation_context(self, user_id: str, channel, max_messages: int = 20):
        """Get conversation context with privacy protection.

        - Uses encrypted in-memory cache if user consents
        - Otherwise fetches directly from Discord API with privacy safeguards
        """
        cached_context = self.privacy_manager.get_cached_context(user_id, str(channel.id))
        if cached_context:
            if DEBUG_MODE:
                print("🔓 Using encrypted cached context")
            return self._parse_cached_context(cached_context)

        return await self._fetch_discord_context(user_id, channel, max_messages)

    async def _fetch_discord_context(self, user_id: str, channel, max_messages: int):
        """Fetch context from Discord API with privacy safeguards."""
        try:
            raw_messages = []
            message_count = 0

            async for message in channel.history(limit=max_messages * 2, oldest_first=False):
                if message.author == self.user:
                    continue
                if message.type != discord.MessageType.default:
                    continue
                if not message.content.strip() or message.content.startswith('/'):
                    continue

                author_name = message.author.display_name or message.author.name
                if PRIVACY_MODE == 'strict':
                    author_name = f"User{hash(str(message.author.id)) % 100:02d}"

                raw_messages.append({
                    'timestamp': message.created_at,
                    'author': author_name,
                    'content': message.content.strip(),
                    'author_id': str(message.author.id),
                })

                message_count += 1
                if message_count >= max_messages:
                    break

            if not raw_messages:
                return [], "english", []

            raw_messages.reverse()

            language_style = await self._analyze_language_patterns(raw_messages[-6:])

            participants = list(set(msg['author'] for msg in raw_messages))

            formatted_messages = []
            for msg in raw_messages:
                time_str = msg['timestamp'].strftime("%H:%M")
                formatted_messages.append(f"[{time_str}] {msg['author']}: {msg['content']}")

            context_data = {
                'messages': formatted_messages,
                'language': language_style,
                'participants': participants,
                'cached_at': os.getenv('NOW_TS') or '',
            }

            self.privacy_manager.cache_context_temporarily(user_id, str(channel.id), context_data)

            if DEBUG_MODE:
                print(f"📡 Fetched {len(raw_messages)} messages from Discord API")
                print(f"🔒 Privacy mode: {PRIVACY_MODE}")

            return formatted_messages, language_style, participants

        except Exception as error:
            print(f"Error fetching Discord context: {error}")
            return [], "english", []

    def _parse_cached_context(self, cached_data: dict):
        return (
            cached_data.get('messages', []),
            cached_data.get('language', 'english'),
            cached_data.get('participants', []),
        )

    async def _analyze_language_patterns(self, messages):
        """Privacy-safe language analysis using anonymized text sample."""
        if not messages:
            return "english"

        sample_text = ""
        for msg in messages:
            content = msg['content']
            # Basic anonymization - remove mentions and links
            import re
            content = re.sub(r'<[@#][!&]?\d+>', '[mention]', content)
            content = re.sub(r'https?://\S+', '[link]', content)
            sample_text += f"{content} "

        analysis_prompt = f"""Analyze language patterns in this text sample:

TEXT: {sample_text[:500]}

Identify the primary language pattern:
- english: Pure English
- hinglish: English mixed with Hindi words  
- romanized_hindi: Hindi written in English letters

Consider common Hindi words like: yaar, bhai, kya, hai, nahi, chalo, dekho, etc.

Respond with only: english, hinglish, or romanized_hindi"""

        try:
            result = get_gemini_response(analysis_prompt, [])
            result_lower = result.strip().lower()
            return result_lower if result_lower in ['english', 'hinglish', 'romanized_hindi'] else 'english'
        except Exception:
            return "english"

    def create_privacy_safe_sarcasm_prompt(self, user_input: str, message_author: str, context_data):
        """Create sarcasm prompt with privacy protection."""
        formatted_messages, language_style, participants = context_data

        safe_participants = [p for p in participants if p != message_author]

        recent_context = formatted_messages[-8:] if formatted_messages else []
        context_text = "\n".join(recent_context)

        language_instructions = {
            "hinglish": "Use Hinglish naturally (English + Hindi words like 'yaar', 'bhai').",
            "romanized_hindi": "Use romanized Hindi style.",
            "english": "Use English with modern slang and expressions.",
        }

        if user_input.strip():
            prompt = f"""Jump into this chat with sarcastic wit about: "{user_input}"

RECENT CONTEXT:
{context_text}

GUIDELINES:
- Target the topic "{user_input}" or conversation themes
- Participants available for light roasting: {', '.join(safe_participants) if safe_participants else 'the situation'}  
- NEVER target: {message_author} (they requested the sarcasm)
- {language_instructions.get(language_style, language_instructions['english'])}
- Keep it playful, not harsh
- One sharp, contextual line

Deliver your sarcastic take:"""
        else:
            prompt = f"""Analyze this Discord conversation and jump in with perfect sarcastic timing:

RECENT CONVERSATION:
{context_text}

PARTICIPANTS: {', '.join(safe_participants) if safe_participants else 'various people'}
REQUESTER: {message_author} (don't roast them!)

SARCASM OPTIONS:
1. Mock something said in recent conversation
2. Playfully roast a participant's comment  
3. Make fun of the situation/topic
4. Reference conversation patterns

STYLE: {language_instructions.get(language_style, language_instructions['english'])}

Drop one perfectly timed sarcastic line:"""

        return prompt

    async def handle_privacy_command(self, message, args):
        """Handle privacy-related commands."""
        user_id = str(message.author.id)

        if not args:
            allows_caching = self.privacy_manager.user_consents_to_caching(user_id)
            cache_status = "✅ Enabled" if allows_caching else "❌ Disabled"

            privacy_info = f"""🔐 **Your Privacy Settings:**

**Conversation Caching:** {cache_status}
**Privacy Mode:** {PRIVACY_MODE.upper()}
**Data Encryption:** ✅ Enabled
**Cache Duration:** 2 hours max (in-memory only)

**Commands:**
• `/privacy allow` - Enable encrypted caching (faster responses)
• `/privacy deny` - Disable all caching (slower, more private)  
• `/privacy clear` - Clear all your cached data
• `/privacy info` - Show this information

**How it works:**
- Bot reads recent Discord messages for context
- With caching: Temporarily encrypts & stores context (2h max)
- Without caching: Fetches fresh context each time (slower)
- Personal identifiers are anonymized in strict mode"""

            await message.channel.send(privacy_info)

        elif args[0] == 'allow':
            self.privacy_manager.set_user_privacy_preference(user_id, True)
            await message.channel.send("✅ Encrypted caching enabled. Responses will be faster!")

        elif args[0] == 'deny':
            self.privacy_manager.set_user_privacy_preference(user_id, False)
            self.privacy_manager.clear_user_cache(user_id)
            await message.channel.send("❌ Caching disabled. All your data cleared. Responses may be slower.")

        elif args[0] == 'clear':
            self.privacy_manager.clear_user_cache(user_id)
            await message.channel.send("🧹 All your cached data has been cleared!")

        else:
            await message.channel.send("Invalid privacy command. Use `/privacy` to see options.")

    async def on_message(self, message):
        if DEBUG_MODE:
            print(f"📨 Message from {message.author}: {message.content[:100]}...")

        # Prevent self-talk
        if message.author == self.user:
            return

        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        content = message.content.strip()

        # Privacy command handling
        if content.startswith('/privacy'):
            args = content.split()[1:] if len(content.split()) > 1 else []
            await self.handle_privacy_command(message, args)
            return

        # Handle clear/reset command (privacy-safe)
        if content.lower() in ['/clear', '/reset']:
            self.privacy_manager.clear_user_cache(user_id)
            await message.channel.send("🧹 Your data cleared! Ready for fresh conversations.")
            return

        if content.lower() in ['/help', '/commands']:
            help_text = """🤖 **Enhanced AI Discord Bot Commands:**

**Chat Models:**
• `/gpt <message>` - GPT-4o conversation with memory
• `/gemini <message>` - Gemini conversation with memory
• `/gemini S [message]` - SARCASM MODE 🔥 (roasts chat, not you!)

**File Analysis:**
• Upload + `/gpt` or `/gemini` - Smart multimodal analysis
• Supports: Images, PDFs, text files (50MB max)

**Memory & Utils:**
• `/clear` - Reset conversation memory
• `/help` - Show this menu

**Features:**
✅ Persistent conversation memory per user/channel
✅ Advanced file processing with context
✅ Smart sarcasm that targets chat content
✅ Multi-language support (English/Hinglish/Hindi)"""

            await message.channel.send(help_text)
            return

        # Command parsing
        model_map = {
            '/gpt': ('gpt', get_ai_response),
            '/gemini': ('gemini', get_gemini_response),
        }

        command = None
        user_input = None
        model_name = None
        model_function = None
        sarcasm_mode = False

        # Check for sarcasm mode
        if content.startswith('/gemini S'):
            command = '/gemini'
            user_input = content[9:].strip()
            model_name = 'gemini'
            model_function = get_gemini_response
            sarcasm_mode = True
        else:
            for prefix, (name, func) in model_map.items():
                if content.startswith(prefix):
                    command = prefix
                    user_input = content[len(prefix):].strip()
                    model_name = name
                    model_function = func
                    break

        if not command:
            return

        if not user_input and not message.attachments and not sarcasm_mode:
            await message.channel.send(f"💡 Please provide a message after `{command}` or upload a file to analyze.")
            return

        if user_input is None:
            user_input = ""

        async with message.channel.typing():
            try:
                file_info = None
                if message.attachments:
                    attachment = message.attachments[0]

                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as response:
                            if response.status == 200:
                                file_data = await response.read()
                                file_info = await self.file_processor.process_file(attachment.filename, file_data)

                                if not file_info.get('success'):
                                    await message.channel.send(f"❌ File processing failed: {file_info.get('error', 'Unknown error')}")
                                    return

                                await message.channel.send(f"📎 Processed: {attachment.filename} • {file_info.get('type', 'unknown').title()} format")
                            else:
                                await message.channel.send(f"❌ Download failed: HTTP {response.status}")
                                return

                # Get privacy-safe context
                context_data = await self.get_conversation_context(user_id, message.channel)

                if sarcasm_mode:
                    if DEBUG_MODE:
                        print(f"🔥 SARCASM MODE: {message.author.display_name} in #{message.channel.name}")

                    prompt = self.create_privacy_safe_sarcasm_prompt(
                        user_input,
                        message.author.display_name or message.author.name,
                        context_data,
                    )
                    bot_response = model_function(prompt, [], file_info)
                    display_model = f"{model_name.upper()} SARCASM 🔥"
                else:
                    if DEBUG_MODE:
                        print(f"🤖 REGULAR MODE: {message.author.display_name} using {model_name.upper()}")

                    formatted_messages, _, _ = context_data
                    # Convert formatted context to a simple conversation history (privacy-safe)
                    conversation_history = []
                    for line in formatted_messages[-6:]:
                        if '] ' in line:
                            author_part = line.split('] ', 1)[1]
                            if ': ' in author_part:
                                _author, content_part = author_part.split(': ', 1)
                                conversation_history.append({'role': 'user', 'content': content_part})

                    bot_response = model_function(user_input, conversation_history, file_info)
                    display_model = model_name.upper()

                await self.send_response(message.channel, bot_response, display_model)

                if file_info and file_info.get('success'):
                    reactions = {
                        'image': '🖼️',
                        'document': '📄',
                    }
                    reaction = reactions.get(file_info.get('type'), '📎')
                    await message.add_reaction(reaction)

            except Exception as error:
                error_msg = f"❌ Something went wrong: {str(error)}"
                print(f"Error in message processing: {error}")
                await message.channel.send(error_msg)

    async def send_response(self, channel, response: str, model_name: str):
        """Enhanced response sending with better formatting"""
        if len(response) <= 1900:  # Leave room for model name
            await channel.send(f"🤖 **{model_name}:** {response}")
        else:
            chunks = []
            current_chunk = ""
            paragraphs = response.split('\n\n')

            for para in paragraphs:
                if len(current_chunk + para) < 1800:
                    current_chunk += para + '\n\n'
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para + '\n\n'

            if current_chunk:
                chunks.append(current_chunk.strip())

            for index, chunk in enumerate(chunks):
                if index == 0:
                    await channel.send(f"🤖 **{model_name}:** {chunk}")
                else:
                    await channel.send(chunk)

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
