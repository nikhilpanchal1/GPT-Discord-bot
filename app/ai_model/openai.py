from dotenv import load_dotenv
from openai import OpenAI
import os
from typing import List, Dict, Optional

load_dotenv()

client = OpenAI(api_key=os.getenv('CHATGPT_APIKEY'))

def get_ai_response(prompt: str, conversation_history: Optional[List[Dict]] = None, file_info: Optional[Dict] = None) -> str:
    """
    Get response from OpenAI GPT model with conversation history and multimodal support.
    
    Args:
        prompt: User's current prompt
        conversation_history: Previous conversation messages
        file_info: Processed file information for multimodal input
    
    Returns:
        AI response string
    """
    if not os.getenv('CHATGPT_APIKEY'):
        return "CHATGPT_APIKEY not found in environment."
    
    try:
        # Build messages array
        messages = []
        
        # Add conversation history (excluding the most recent assistant message to avoid duplication)
        if conversation_history:
            for msg in conversation_history:
                if msg['role'] in ['user', 'assistant', 'system']:
                    messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
        
        # Prepare current message content
        current_content = []
        
        # Add text prompt
        current_content.append({
            "type": "text",
            "text": prompt
        })
        
        # Add image if provided
        if file_info and file_info.get('success') and file_info.get('type') == 'image':
            current_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{file_info['mime_type']};base64,{file_info['base64_data']}",
                    "detail": "high"
                }
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": current_content if len(current_content) > 1 else prompt
        })
        
        # Choose appropriate model based on content
        model = "gpt-4o" if (file_info and file_info.get('type') == 'image') else "gpt-4o"
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )
        
        content = response.choices[0].message.content
        return content if content is not None else "No response generated."
        
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return f"Sorry, I couldn't get a response from OpenAI: {str(e)}"

# Legacy function for backward compatibility
def chatgpt_response(prompt: str) -> str:
    """Legacy function for backward compatibility."""
    return get_ai_response(prompt)