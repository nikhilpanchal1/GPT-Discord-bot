# 🤖 Enhanced GPT-Discord Bot

A sophisticated Discord bot engineered with persistent conversation memory and advanced multimodal processing capabilities. Built on OpenAI GPT-4o and Google Gemini models.

## Key Features
• **Persistent Conversations**: Built per-user/channel memory with automatic context injection
• **Multimodal Analysis**: Integrated GPT-4V + Gemini Vision for images, PDF extraction for documents  
• **Smart File Processing**: Developed drag-and-drop analysis with automatic type detection (50MB limit)
• **Sarcasm Mode**: AI-powered sarcastic responses with intelligent conversation context analysis
• **Language Detection**: Automatic detection of English, Hinglish, and Romanized Hindi conversation patterns
• **Enhanced UX**: Implemented /clear, /help commands with typing indicators and emoji feedback

## Technical Highlights
• Engineered async file download/processing pipeline with aiohttp + Pillow + PyPDF2
• Implemented AI-powered sarcasm mode with intelligent conversation context analysis
• Designed intelligent language detection system for English, Hinglish, and Romanized Hindi
• Built dynamic response generation with multiple personality modes and styles
• Architected type-safe codebase with comprehensive error handling and message splitting
• Built modular architecture: separate storage, utils, and AI model layers

## Usage Examples
Upload image + "/gpt analyze this chart" → Full GPT-4V analysis with conversation context  
Upload PDF + "/gemini summarize" → Text extraction + Gemini analysis with memory  
"/clear" → Reset conversation history

Production-ready with backward compatibility maintained.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd GPT-Discord-bot

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Copy `example.env` to `.env` and configure your API keys:

```bash
cp example.env .env
```

Edit `.env` with your credentials:
```env
DISCORD_TOKEN="your_discord_bot_token"
CHATGPT_APIKEY="your_openai_api_key"
GEMINI_API_KEY="your_gemini_api_key"
```

### 3. Run the Bot

```bash
python run.py
```

## 📝 Usage

### Basic Commands

| Command | Description |
|---------|-------------|
| `/gpt <message>` | Chat with GPT-4o |
| `/gemini <message>` | Chat with Gemini Flash |
| `/gemini S [message]` | Sarcastic mode - Jump into conversation with witty, sarcastic responses |
| `/clear` or `/reset` | Clear conversation history |
| `/help` | Show available commands |

### Multimodal Usage

**Image Analysis:**
```
Upload an image + "/gpt What do you see in this image?"
Upload an image + "/gemini Describe this photo in detail"
```

**Document Analysis:**
```
Upload a PDF + "/gpt Summarize this document"
Upload a text file + "/gemini What are the key points?"
```

**File-only Analysis:**
```
Simply upload any supported file without a command - defaults to GPT analysis
```

### Sarcasm Mode 🔥

The bot features an intelligent sarcasm mode that analyzes recent conversation context and delivers perfectly timed sarcastic responses.

**Usage:**
```
/gemini S                    # Jump into conversation with sarcastic comment
/gemini S what do you think? # Sarcastic response about specific topic
```

**Features:**
- **Context Analysis**: Automatically fetches and analyzes recent Discord messages
- **Language Detection**: Detects English, Hinglish, or Romanized Hindi conversation patterns
- **Multiple Response Styles**: Sarcastic jab, meme reference, simple & salty responses
- **Intelligent Relevance**: AI determines current conversation thread from timestamps
- **Personality Modes**: Corporate professional, chaos agent, boomer uncle, and more

**Example:**
```
[Recent chat about gaming plans]
User: /gemini S
Bot: Oh wow, another "8:30 pe khelenge" plan? Revolutionary scheduling skills! 🎮
```

### Conversation Memory

The bot automatically:
- Remembers your previous messages in each channel
- Maintains context across multiple exchanges
- Stores conversations persistently
- Provides natural, contextual responses

Example conversation:
```
User: /gpt What's the capital of France?
Bot: The capital of France is Paris.

User: /gpt What's the population?
Bot: Paris has a population of approximately 2.1 million people in the city proper...
```

## 🛠️ Technical Details

### Supported File Types

| Type | Extensions | Max Size |
|------|------------|----------|
| Images | .jpg, .jpeg, .png, .gif, .bmp, .webp | 50MB |
| Documents | .pdf, .txt | 50MB |

### Architecture

```
app/
├── ai_model/
│   ├── openai.py      # GPT-4o integration with multimodal support
│   └── gemini.py      # Gemini integration with vision capabilities
├── discord_bot/
│   └── discord_api.py # Main bot logic with file handling
├── storage/
│   └── conversation_storage.py # Persistent conversation memory
└── utils/
    └── file_utils.py  # File processing and content extraction
```

### Conversation Storage

- **Format**: JSON with timestamps and metadata
- **Location**: `conversations.json` in project root
- **Structure**: Organized by user-channel pairs
- **Retention**: 7 days (configurable)
- **Max History**: 20 messages per conversation (configurable)

### Error Handling

- Graceful file processing failures
- API rate limit handling
- Large message splitting (Discord 2000 char limit)
- Comprehensive error logging

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | ✅ | Your Discord bot token |
| `CHATGPT_APIKEY` | ✅ | OpenAI API key for GPT models |
| `GEMINI_API_KEY` | ✅ | Google AI API key for Gemini models |
| `DEBUG_MODE` | ❌ | Enable debug output for all bot interactions (default: false) |

### Debug Mode

When `DEBUG_MODE=true` is set, the bot provides comprehensive console logging for both regular and sarcasm modes:

**Regular Mode (`/gemini` or `/gpt`):**
- User info and channel details
- Input message content
- File attachment information
- AI response content
- Response delivery confirmation

**Sarcasm Mode (`/gemini S`):**
- Context analysis details
- Recent message fetching
- Language detection results
- Response generation process
- Sarcastic output details

Example debug output:
```
🤖 REGULAR MODE ACTIVATED by UserName
📍 Channel: #general | Model: GEMINI
💬 User input: 'What's the weather like?'
✅ AI RESPONSE RECEIVED:
--------------------------------------------------
💬 Response: The weather varies by location...
--------------------------------------------------
📤 Sending to Discord channel...
```

## 🎯 Examples

### Image Analysis
```
[Upload image of a chart]
User: /gpt What trends do you see in this data?
Bot: Looking at this chart, I can see several key trends...
```

### Document Processing
```
[Upload PDF report]
User: /gemini Extract the key findings from this report
Bot: Based on the document content, here are the key findings...
```

### Contextual Conversation
```
User: /gpt I'm planning a trip to Japan
Bot: That sounds exciting! Japan is a wonderful destination...

User: What's the best time to visit?
Bot: For your trip to Japan, the best times to visit are...
```

## 🚨 Important Notes

- The bot processes one attachment per message
- Image analysis uses GPT-4o or Gemini Vision models
- Document text is extracted and included in the prompt
- Conversations are automatically saved and restored
- File processing is asynchronous for better performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Happy chatting! 🎉**

