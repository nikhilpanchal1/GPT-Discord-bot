from dotenv import load_dotenv
import os
import discord
import openai

load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')
openai_api_key = os.getenv('CHATGPT_APIKEY')

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
    
    async def on_message(self, message):
        print(message.content)
        if message.author == self.user: #preventing self talk
            return
        command, user_input = None, None
    
        for text in ['/gpt', '/gpt4', 'gpt3']:
            if message.content.startswith(text):
                command = message.content.split(' ')[0]
                user_input = message.content.replace(text, '')
                print(command, user_input)
                
        if command == '/gpt' or command == '/gpt4' or command == '/gpt3':
            bot_response = chatgpt_response(prompt = user_input)
            await message.channel.send(f"Answer:{bot_response}")

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)


# client = discord.Client()
# openai.api_key = 'YOUR_OPENAI_API_KEY_HERE '

# conversation_history = []

# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return

#     if message.content.startswith('/gpt'):
#         text = message.content[5:]
#         conversation_history.append({"role": "user", "content": text})
#         response = openai.ChatCompletion.create(
#             model="gpt-4.0-turbo",
#             messages=conversation_history
#         )
#         conversation_history.append({"role": "assistant", "content": response['choices'][0]['message']['content']})
#         await message.channel.send(response['choices'][0]['message']['content'])

#     elif message.content.startswith('/gpt clean'):
#         conversation_history.clear()

# client.run('YOUR_DISCORD_BOT_TOKEN_HERE ')

