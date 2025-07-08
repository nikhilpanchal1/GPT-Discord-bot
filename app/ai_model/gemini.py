from dotenv import load_dotenv
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
import os
from typing import List, Dict, Optional
import base64

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    configure(api_key=api_key)

def get_gemini_response(prompt: str, conversation_history: Optional[List[Dict]] = None, file_info: Optional[Dict] = None) -> str:
    """
    Get response from Gemini model with conversation history and multimodal support.
    
    Args:
        prompt: User's current prompt
        conversation_history: Previous conversation messages
        file_info: Processed file information for multimodal input
    
    Returns:
        AI response string
    """
    if not api_key:
        return "GEMINI_API_KEY not found in environment."
    
    try:
        # Choose appropriate model based on content
        if file_info and file_info.get('success') and file_info.get('type') == 'image':
            model = GenerativeModel('gemini-1.5-flash-latest')
        else:
            model = GenerativeModel('gemini-1.5-flash-latest')
        
        # Build conversation history for context
        full_prompt = ""
        
        if conversation_history:
            # Add recent conversation context (last 10 messages to manage token limits)
            recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
            context_parts = []
            
            for msg in recent_history:
                role = msg['role']
                content = msg['content']
                if role == 'user':
                    context_parts.append(f"User: {content}")
                elif role == 'assistant':
                    context_parts.append(f"Assistant: {content}")
            
            if context_parts:
                full_prompt = "Previous conversation:\n" + "\n".join(context_parts) + "\n\nCurrent message:\n"
        
        full_prompt += prompt
        
        # Handle multimodal content
        if file_info and file_info.get('success'):
            if file_info.get('type') == 'image':
                # For images, use the image data directly
                import io
                from PIL import Image
                
                # Decode base64 image
                image_data = base64.b64decode(file_info['base64_data'])
                image = Image.open(io.BytesIO(image_data))
                
                # Generate content with image
                response = model.generate_content([full_prompt, image])
                
            elif file_info.get('type') == 'document':
                # For documents, include the text content in the prompt
                doc_content = file_info.get('text_content', '')
                document_prompt = f"{full_prompt}\n\nDocument content:\n{doc_content}"
                response = model.generate_content(document_prompt)
            else:
                response = model.generate_content(full_prompt)
        else:
            response = model.generate_content(full_prompt)
        
        return response.text if response.text else "No response generated."
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return f"Sorry, I couldn't get a response from Gemini: {str(e)}" 