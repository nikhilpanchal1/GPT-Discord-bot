from dotenv import load_dotenv
import os
import discord
import aiohttp
import asyncio
import functools
from app.ai_model.openai import get_ai_response
from app.ai_model.gemini import get_gemini_response
from app.utils.file_utils import FileProcessor

load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_processor = FileProcessor()

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        print(f'Bot is ready. Sarcasm mode is optional! 🔥')
    
    async def fetch_recent_discord_messages(self, channel, limit=20):
        """Fetch recent messages and identify the ongoing conversation thread"""
        try:
            raw_messages = []
            async for message in channel.history(limit=limit, oldest_first=False):
                # Skip bot's own messages and system messages
                if message.author == self.user or message.type != discord.MessageType.default:
                    continue
                
                if message.content.strip():  # Only include messages with actual content
                    raw_messages.append({
                        'timestamp': message.created_at,
                        'author': message.author.display_name or message.author.name,
                        'content': message.content.strip()
                    })
            
            if not raw_messages:
                return [], "english"
            
            # Reverse to get chronological order (oldest first)
            raw_messages.reverse()
            
            # Analyze language patterns across all messages
            language_style = await self.analyze_language_style(raw_messages)
            
            # Format messages with timestamps for AI analysis
            formatted_messages = []
            for msg in raw_messages:
                time_str = msg['timestamp'].strftime("%H:%M")
                formatted_messages.append(f"[{time_str}] {msg['author']}: {msg['content']}")
            
            # Debug output to console
            if DEBUG_MODE:
                print("\n" + "="*60)
                print("🔍 SARCASM MODE - CONTEXT ANALYSIS")
                print("="*60)
                print(f"📊 Total messages fetched: {len(raw_messages)}")
                print(f"🌐 Language analysis result: {language_style.upper()}")
                print(f"📋 Context messages being used: {len(formatted_messages)}")
                print("\n📱 DISCORD MESSAGES IN CONTEXT:")
                print("-" * 40)
                for i, msg in enumerate(formatted_messages, 1):
                    print(f"{i:2d}. {msg}")
                print("-" * 40)
                language_display = {
                    "english": "English-only",
                    "hinglish": "Hinglish (English + Hindi words)",
                    "romanized_hindi": "Romanized Hindi"
                }.get(language_style, "English-only")
                print(f"🎯 Language instruction will be: {language_display}")
                print("📝 AI will determine which messages are relevant to current conversation")
                print("="*60 + "\n")
            
            return formatted_messages, language_style
            
        except Exception as e:
            print(f"Error fetching Discord messages: {e}")
            return [], "english"

    async def analyze_language_style(self, messages):
        """Use AI to analyze conversation language patterns"""
        if not messages:
            return "english"
        
        # Prepare sample messages for AI analysis
        sample_messages = []
        for msg in messages[-8:]:  # Last 8 messages for context
            sample_messages.append(f"{msg['author']}: {msg['content']}")
        
        conversation_sample = "\n".join(sample_messages)
        
        # AI language analysis prompt
        analysis_prompt = f"""Analyze the language style of this Discord conversation and categorize it:

CONVERSATION SAMPLE:
{conversation_sample}

LANGUAGE CATEGORIES:
1. **english** - Pure English conversation (e.g., "Let's play at 8:30", "That's awesome dude")
2. **hinglish** - English mixed with Hindi words (e.g., "Let's play yaar", "That's bohot cool bhai")  
3. **romanized_hindi** - Hindi expressed in English letters (e.g., "Kya kar rahe ho", "Khel lo abhi")

Look for patterns like:
- Hindi words: yaar, bhai, kya, hai, nahi, dekho, chalo, etc.
- Romanized Hindi: sentence structures that are Hindi but written in English
- Code-switching between languages within sentences

Reply with ONLY ONE WORD: either "english", "hinglish", or "romanized_hindi" """

        try:
            # Use Gemini for quick language analysis
            from app.ai_model.gemini import get_gemini_response
            
            language_result = get_gemini_response(
                prompt=analysis_prompt,
                conversation_history=[]
            ).strip().lower()
            
            # Validate the response
            valid_responses = ['english', 'hinglish', 'romanized_hindi']
            if language_result in valid_responses:
                result = language_result
            else:
                result = "english"  # Default fallback
            
            if DEBUG_MODE:
                print(f"🔤 AI LANGUAGE ANALYSIS:")
                print(f"   Sample messages analyzed: {len(sample_messages)}")
                print(f"   AI analysis result: {result.upper()}")
                print(f"   ✅ Language mode determined by AI pattern recognition")
            
            return result
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Language analysis failed: {e}")
                print(f"   Falling back to: ENGLISH")
            return "english"

    def create_sarcasm_prompt(self, user_input, recent_discord_data):
        """Create a sarcastic prompt focused on recent Discord conversation"""
        
        # Unpack the data (messages, language_style)
        if isinstance(recent_discord_data, tuple):
            recent_discord_messages, language_style = recent_discord_data
        else:
            recent_discord_messages, language_style = recent_discord_data or [], "english"
        
        # Build context from recent Discord messages
        discord_context = ""
        if recent_discord_messages:
            discord_context = "\n".join(recent_discord_messages)
        
        # Determine language instruction based on AI analysis
        if language_style == "hinglish":
            language_instruction = "Use Hinglish (English mixed with Hindi words like 'yaar', 'bhai', 'kya') to match the conversation vibe."
        elif language_style == "romanized_hindi":
            language_instruction = "Use romanized Hindi (Hindi words written in English letters) to match their style. Feel free to use phrases like 'kya kar rahe ho', 'chalo', 'dekho', etc."
        else:  # english
            language_instruction = "Keep it in pure English to match the conversation style."
        
        # Handle different sarcasm scenarios
        if user_input.strip():
            # User provided additional context/question
            sarcasm_prompt = f"""You're a sarcastic friend in this Discord chat. Make a witty, sarcastic comment about: "{user_input}"

ONGOING CONVERSATION THREAD:
{discord_context if discord_context else "Nothing much happening..."}

Reply with one sarcastic line that contributes to this active discussion. {language_instruction} Be funny and edgy."""
        else:
            # Just "/gemini S" - comment on recent conversation thread
            sarcasm_prompt = f"""You're about to jump into this Discord chat with maximum sarcastic energy. First, analyze the messages below and identify the CURRENT/ONGOING conversation thread based on timestamps and content relevance. Ignore old/irrelevant messages and focus on the most recent active discussion.

RESPONSE STYLE OPTIONS:
1. **The Sarcastic Jab** - Sharp, witty roast that cuts deep but stays funny
2. **The Meme Reference** - Pop culture or internet meme callback that's perfectly timed  

RECENT DISCORD MESSAGES (with timestamps):
{discord_context if discord_context else "Dead silence... absolutely riveting content here."}

Analyze the timestamps and content to identify the current conversation thread. Focus on the most recent, relevant messages. Then drop ONE perfect sarcastic line that contributes to what's actually happening in the active discussion. {language_instruction} Be edgy, fearless, and hilariously contextual. Don't explain your analysis - just deliver the perfect comeback. think like - What is a funny reply to this conversation? And reply like that, only reply with what's meant for the message If possible, roast one of the users in the conversation or make a joke about the conversation. Dont be afraid of being edgy or offensive" """

        # Debug output for the final prompt
        if DEBUG_MODE:
            print("🤖 FINAL SARCASM PROMPT GENERATED:")
            print("-" * 50)
            print(sarcasm_prompt[:500] + "..." if len(sarcasm_prompt) > 500 else sarcasm_prompt)
            print("-" * 50)
            print(f"💬 User input: '{user_input}' | Language mode: {language_style}")
            print("🚀 Sending to AI model for sarcastic response...\n")

        return sarcasm_prompt

    async def on_message(self, message):
        print(f"Message from {message.author}: {message.content}")
        
        # Prevent self-talk
        if message.author == self.user:
            return

        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        content = message.content.strip()
        
        # Handle special commands
        if content.lower() in ['/clear', '/reset']:
            await message.channel.send("🧹 Fresh start! Ready for more sarcastic conversations! 🔥")
            return
        
        if content.lower() in ['/help', '/commands']:
            help_text = """
🤖 **Available Commands:**

**AI Models:**
• `/gpt <message>` - Chat with GPT-4o
• `/gemini <message>` - Chat with Gemini Flash
• `/gemini S <message>` - Chat with Gemini in SARCASM MODE 🔥

**File Analysis:**
• Upload images, PDFs, or text files with `/gpt` or `/gemini` commands
• Supports: JPG, PNG, GIF, PDF, TXT files (max 50MB)

**Conversation:**
• `/clear` or `/reset` - Clear conversation history
• `/help` - Show this help message

**Features:**
✅ Maintains conversation context per user/channel
✅ Multimodal analysis (images, documents)
✅ File processing with explicit commands
✅ Smart content extraction
✅ Sarcasm mode for maximum wit and edge

Use `/gpt` or `/gemini` with your file uploads for analysis!
            """
            await message.channel.send(help_text)
            return
        
        # Parse command and model selection
        model_map = {
            '/gpt': ('gpt', get_ai_response),
            'gpt3': ('gpt', get_ai_response),  # Legacy support
            '/gemini': ('gemini', get_gemini_response)
        }

        command = None
        user_input = None
        model_name = None
        model_function = None
        sarcasm_mode = False
        
        # Check for sarcasm mode first
        if content.startswith('/gemini S'):
            command = '/gemini'
            user_input = content[9:].strip()  # Remove '/gemini S' prefix
            model_name = 'gemini'
            model_function = get_gemini_response
            sarcasm_mode = True
        else:
            # Regular command parsing
            for prefix, (name, func) in model_map.items():
                if content.startswith(prefix):
                    command = prefix
                    user_input = content[len(prefix):].strip()
                    model_name = name
                    model_function = func
                    break

        if not command:
            return

        # Ensure we have valid values (type safety)
        if model_name is None or model_function is None:
            return

        # Handle empty input - allow sarcasm mode to proceed without input
        if not user_input and not message.attachments and not sarcasm_mode:
            await message.channel.send(f"Please provide a prompt after the `{command}` command or upload a file to analyze.")
            return
        
        # Ensure user_input is not None
        if user_input is None:
            user_input = "Please analyze this file." if message.attachments else ""

        # Show typing indicator
        async with message.channel.typing():
            try:
                # Process attachments
                file_info = None
                if message.attachments:
                    attachment = message.attachments[0]  # Process first attachment
                    
                    # Download file
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as response:
                            if response.status == 200:
                                file_data = await response.read()
                                file_info = await self.file_processor.process_file(attachment.filename, file_data)
                                
                                if not file_info.get('success'):
                                    await message.channel.send(f"❌ Error processing file: {file_info.get('error', 'Unknown error')}")
                                    return
                                
                                # Enhance prompt with file information
                                if file_info.get('type') == 'document':
                                    user_input = self.file_processor.create_multimodal_prompt(user_input, file_info)
                                else:
                                    # For images, let the AI model handle the multimodal content directly
                                    pass
                                    
                                await message.channel.send(f"📎 File processed: {attachment.filename} ({file_info.get('type', 'unknown')} format)")
                            else:
                                await message.channel.send(f"❌ Failed to download attachment: HTTP {response.status}")
                                return

                # Handle sarcasm mode
                if sarcasm_mode:
                    if DEBUG_MODE:
                        print(f"\n🔥 SARCASM MODE ACTIVATED by {message.author.display_name}")
                        print(f"📍 Channel: #{message.channel.name} | User input: '{user_input}'")
                    
                    # Fetch recent Discord messages and language analysis
                    recent_discord_data = await self.fetch_recent_discord_messages(message.channel)
                    
                    # Create sarcastic prompt
                    sarcastic_prompt = self.create_sarcasm_prompt(user_input, recent_discord_data)
                    
                    # Get sarcastic response
                    bot_response = model_function(
                        prompt=sarcastic_prompt,
                        conversation_history=[],  # No stored conversation history
                        file_info=file_info
                    )
                    
                    # Debug output for AI response
                    if DEBUG_MODE:
                        print("✅ AI SARCASTIC RESPONSE RECEIVED:")
                        print("-" * 50)
                        print(f"💬 Response: {bot_response}")
                        print("-" * 50)
                        print("📤 Sending to Discord channel...\n")
                    
                    # Add sarcasm indicator to model name
                    display_model_name = f"{model_name.upper()} SARCASM MODE 🔥"
                else:
                    if DEBUG_MODE:
                        print(f"\n🤖 REGULAR MODE ACTIVATED by {message.author.display_name}")
                        print(f"📍 Channel: #{message.channel.name} | Model: {model_name.upper()}")
                        print(f"💬 User input: '{user_input}'")
                        if file_info and file_info.get('success'):
                            print(f"📎 File attached: {file_info.get('type', 'unknown')} format")
                    
                    # Get AI response normally
                    bot_response = model_function(
                        prompt=user_input,
                        conversation_history=[],  # No stored conversation history
                        file_info=file_info
                    )
                    
                    # Debug output for AI response
                    if DEBUG_MODE:
                        print("✅ AI RESPONSE RECEIVED:")
                        print("-" * 50)
                        print(f"💬 Response: {bot_response}")
                        print("-" * 50)
                        print("📤 Sending to Discord channel...\n")
                    
                    display_model_name = model_name.upper()
                
                # Send response (split if too long)
                if len(bot_response) > 2000:
                    # Split long messages
                    for i in range(0, len(bot_response), 1900):
                        chunk = bot_response[i:i+1900]
                        if i == 0:
                            await message.channel.send(f"🤖 **{display_model_name}:** {chunk}")
                        else:
                            await message.channel.send(chunk)
                else:
                    await message.channel.send(f"🤖 **{display_model_name}:** {bot_response}")
                
                # File analysis confirmation
                if file_info and file_info.get('success'):
                    file_type = file_info.get('type', 'file')
                    if file_type == 'image':
                        await message.add_reaction('🖼️')
                    elif file_type == 'document':
                        await message.add_reaction('📄')
                    else:
                        await message.add_reaction('📎')

            except Exception as e:
                error_msg = f"❌ Error processing request: {str(e)}"
                print(f"Error in on_message: {e}")
                await message.channel.send(error_msg)

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
