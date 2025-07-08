import os
import io
import base64
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image
import PyPDF2
import aiofiles
import magic

class FileProcessor:
    """Handles processing of various file types for AI analysis."""
    
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    SUPPORTED_DOCUMENT_FORMATS = {'.pdf', '.txt'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @staticmethod
    async def process_file(file_path: str, file_data: bytes) -> Dict:
        """
        Process uploaded file and extract content for AI analysis.
        
        Args:
            file_path: Path/name of the file
            file_data: Raw file data
            
        Returns:
            Dict with processed file information
        """
        file_ext = os.path.splitext(file_path.lower())[1]
        file_size = len(file_data)
        
        if file_size > FileProcessor.MAX_FILE_SIZE:
            return {
                'success': False,
                'error': f'File too large. Maximum size is {FileProcessor.MAX_FILE_SIZE // (1024*1024)}MB'
            }
        
        try:
            if file_ext in FileProcessor.SUPPORTED_IMAGE_FORMATS:
                return await FileProcessor._process_image(file_data, file_ext)
            elif file_ext == '.pdf':
                return await FileProcessor._process_pdf(file_data)
            elif file_ext == '.txt':
                return await FileProcessor._process_text(file_data)
            else:
                # Try to detect MIME type
                mime_type = magic.from_buffer(file_data, mime=True)
                if mime_type.startswith('image/'):
                    return await FileProcessor._process_image(file_data, file_ext)
                elif mime_type == 'application/pdf':
                    return await FileProcessor._process_pdf(file_data)
                elif mime_type.startswith('text/'):
                    return await FileProcessor._process_text(file_data)
                else:
                    return {
                        'success': False,
                        'error': f'Unsupported file type: {file_ext} (MIME: {mime_type})'
                    }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing file: {str(e)}'
            }
    
    @staticmethod
    async def _process_image(file_data: bytes, file_ext: str) -> Dict:
        """Process image file for AI analysis."""
        try:
            # Open and validate image
            image = Image.open(io.BytesIO(file_data))
            
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            
            # Resize if too large (to save on API costs)
            max_dimension = 1024
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to base64 for AI APIs
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return {
                'success': True,
                'type': 'image',
                'format': image.format or 'JPEG',
                'size': image.size,
                'mode': image.mode,
                'base64_data': base64_image,
                'mime_type': f'image/jpeg'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing image: {str(e)}'
            }
    
    @staticmethod
    async def _process_pdf(file_data: bytes) -> Dict:
        """Extract text from PDF file."""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
            
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                except Exception as e:
                    text_content.append(f"--- Page {page_num + 1} ---\n[Error extracting text: {str(e)}]")
            
            full_text = "\n\n".join(text_content)
            
            return {
                'success': True,
                'type': 'document',
                'format': 'pdf',
                'pages': len(pdf_reader.pages),
                'text_content': full_text,
                'word_count': len(full_text.split())
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing PDF: {str(e)}'
            }
    
    @staticmethod
    async def _process_text(file_data: bytes) -> Dict:
        """Process text file."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            text_content = None
            
            for encoding in encodings:
                try:
                    text_content = file_data.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if text_content is None:
                return {
                    'success': False,
                    'error': 'Could not decode text file with any supported encoding'
                }
            
            return {
                'success': True,
                'type': 'document',
                'format': 'text',
                'text_content': text_content,
                'word_count': len(text_content.split()),
                'char_count': len(text_content)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing text file: {str(e)}'
            }
    
    @staticmethod
    def create_multimodal_prompt(user_prompt: str, file_info: Dict) -> str:
        """Create a comprehensive prompt for multimodal analysis."""
        if not file_info.get('success'):
            return user_prompt
        
        file_type = file_info.get('type')
        
        if file_type == 'image':
            size_info = f"{file_info['size'][0]}x{file_info['size'][1]}"
            return f"""Analyze the uploaded image and respond to: {user_prompt}

Image details:
- Format: {file_info.get('format', 'Unknown')}
- Size: {size_info}
- Mode: {file_info.get('mode', 'Unknown')}

Please provide a detailed analysis of the image content and address the user's request."""

        elif file_type == 'document':
            if file_info.get('format') == 'pdf':
                doc_info = f"PDF with {file_info.get('pages', 0)} pages, {file_info.get('word_count', 0)} words"
            else:
                doc_info = f"Text document with {file_info.get('word_count', 0)} words"
            
            return f"""Analyze the uploaded document and respond to: {user_prompt}

Document details: {doc_info}

Document content:
{file_info.get('text_content', '')}

Please analyze the document content and address the user's request."""
        
        return user_prompt 