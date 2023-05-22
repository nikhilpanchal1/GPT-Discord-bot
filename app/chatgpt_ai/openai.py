from dotenv import load_dotenv
import openai
import os

load_dotenv()

openai.api_key = os.getenv('CHATGPT_APIKEY')

def chatgpt_response(prompt):
    response = openai.Completion.create(
        model = "text-davinci-003",
        prompt = prompt,
        temperature = 1.3,
        max_tokens = 2048
    )
    response_dict = response.get("choices")
    if response_dict and len(response_dict) > 0:
        prompt_response = response_dict[0].get("text")
    return prompt_response