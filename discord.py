import discord
import openai

client = discord.Client()
openai.api_key = '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'

conversation_history = []

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('/gpt'):
        text = message.content[5:]
        conversation_history.append({"role": "user", "content": text})
        response = openai.ChatCompletion.create(
            model="gpt-4.0-turbo",
            messages=conversation_history
        )
        conversation_history.append({"role": "assistant", "content": response['choices'][0]['message']['content']})
        await message.channel.send(response['choices'][0]['message']['content'])

    elif message.content.startswith('/gpt clean'):
        conversation_history.clear()

client.run('MTExMDI5MzAyMDA0NzMzMTMzOA.GG_tbu.ydt-LiQ-TMGaa0wSn9pSON7efNbScYgH3JORF4')

