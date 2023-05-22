from dotenv import load_dotenv
import os
import discord
from app.chatgpt_ai.openai import chatgpt_response

load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
    
    async def on_message(self, message):
        print(message.content)
        if message.author == self.user: #preventing self talk
            return
        command, user_input = None, None
    
        for text in ['/gpt', 'gpt3']:
            if message.content.startswith(text):
                command = message.content.split(' ')[0]
                user_input = message.content.replace(text, '')
                print(command, user_input)
                
        if command == '/gpt' or command == '/gpt3':
            bot_response = chatgpt_response(prompt = user_input)
            await message.channel.send(f"Answer:{bot_response}")

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
