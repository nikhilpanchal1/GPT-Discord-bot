from dotenv import load_dotenv
import os
import discord
import aiohttp
from app.ai_model.openai import get_ai_response
from app.ai_model.gemini import get_gemini_response
from app.storage.conversation_storage import conversation_storage
from app.utils.file_utils import FileProcessor

load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_processor = FileProcessor()

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        print(f'Bot is ready. Active conversations: {conversation_storage.get_conversation_count()}')
    
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
            conversation_storage.clear_conversation(user_id, channel_id)
            await message.channel.send("🧹 Conversation history cleared!")
            return
        
        if content.lower() in ['/help', '/commands']:
            help_text = """
🤖 **Available Commands:**

**AI Models:**
• `/gpt <message>` - Chat with GPT-4o
• `/gemini <message>` - Chat with Gemini Flash

**File Analysis:**
• Upload images, PDFs, or text files with your message
• Supports: JPG, PNG, GIF, PDF, TXT files (max 50MB)

**Conversation:**
• `/clear` or `/reset` - Clear conversation history
• `/help` - Show this help message

**Features:**
✅ Maintains conversation context per user/channel
✅ Multimodal analysis (images, documents)
✅ Automatic file processing
✅ Smart content extraction

Just upload a file and ask a question to analyze it!
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
        
        for prefix, (name, func) in model_map.items():
            if content.startswith(prefix):
                command = prefix
                user_input = content[len(prefix):].strip()
                model_name = name
                model_function = func
                break

        # If no command but there are attachments, default to GPT
        if not command and message.attachments:
            command = '/gpt'
            user_input = content if content else "Please analyze this file."
            model_name = 'gpt'
            model_function = get_ai_response

        if not command:
            return

        # Ensure we have valid values (type safety)
        if model_name is None or model_function is None:
            return

        # Handle empty input
        if not user_input and not message.attachments:
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

                # Get conversation history
                conversation_history = conversation_storage.get_conversation_history(user_id, channel_id, max_messages=15)
                
                # Store user message
                conversation_storage.add_message(user_id, channel_id, 'user', user_input, model_name)
                
                # Get AI response
                bot_response = model_function(
                    prompt=user_input,
                    conversation_history=conversation_history,
                    file_info=file_info
                )
                
                # Store assistant response
                conversation_storage.add_message(user_id, channel_id, 'assistant', bot_response, model_name)
                
                # Send response (split if too long)
                if len(bot_response) > 2000:
                    # Split long messages
                    for i in range(0, len(bot_response), 1900):
                        chunk = bot_response[i:i+1900]
                        if i == 0:
                            await message.channel.send(f"🤖 **{model_name.upper()}:** {chunk}")
                        else:
                            await message.channel.send(chunk)
                else:
                    await message.channel.send(f"🤖 **{model_name.upper()}:** {bot_response}")
                
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
