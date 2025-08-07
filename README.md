# GuideMate AI - Advanced Guidance Counselor Chatbot

A sophisticated AI guidance counselor that understands and responds in Hindi, English, and Hinglish with advanced audio processing, RAG-enhanced responses, and professional Indian language TTS.

## 🌟 Features

### 🤖 AI-Powered Guidance Counseling
- **Evidence-Based Responses**: RAG system provides authoritative guidance from PDF documents
- **Source Citations**: Responses include proper references to guidance materials
- **Conversational AI**: Context-aware, memory-enabled conversations
- **Cultural Sensitivity**: Trained for Indian student contexts and social norms

### 🎭 Advanced Audio Processing
- **Professional Indian TTS**: Indic Parler-TTS with 21 languages and 69 voices
- **Hinglish Speech Recognition**: OpenAI Whisper with optimized mixed-language support
- **Natural Pronunciation**: High-quality Hindi, English, and code-mixed speech
- **Real-time Audio**: WebSocket-based streaming audio communication

### 📚 RAG Knowledge System
- **Document Intelligence**: Process PDF guidance books and educational materials
- **Smart Retrieval**: Context-aware information retrieval from knowledge base
- **Citation Support**: Responses include source references and page numbers
- **Preloaded Content**: Add your guidance counselor PDFs for authoritative responses

### 🗣️ Language Intelligence
- **Automatic Language Detection**: Smart detection of Hindi, English, and mixed content
- **Dual Script Support**: Seamless handling of Devanagari and Latin scripts
- **Code-Mixing Mastery**: Natural Hinglish conversations with proper pronunciation
- **Cultural Context Awareness**: AI trained for Indian educational and social contexts

### 📱 Modern Architecture
- **Progressive Web App**: Installable mobile experience with offline support
- **Microservices Design**: Scalable Docker-based architecture
- **Real-time Communication**: WebSocket integration for instant responses
- **Mobile Optimized**: Responsive design for 430px+ mobile screens

## 🏗️ Architecture

```
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js Frontend  │    │   FastAPI Server │    │   AI Processing │
│                     │    │                  │    │                 │
│ • Advanced PWA      │◄──►│ • WebSocket API  │◄──►│ • Gemma 2 9B    │
│ • Voice Recording   │    │ • Audio Pipeline │    │ • RAG Enhanced  │
│ • Dual Script UI    │    │ • Language Route │    │ • Context Aware │
│ • Mobile Optimized  │    │ • TTS Manager    │    │ • Citation Gen  │
└─────────────────────┘    └──────────────────┘    └─────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────┐    ┌──────────────────┐
│   RAG System        │    │   TTS Engines    │
│                     │    │                  │
│ • Document Process  │    │ • Indic Parler   │
│ • Vector Database   │    │ • Coqui Fallback │
│ • Context Retrieval │    │ • gTTS Backup    │
│ • Source Citations  │    │ • Smart Routing  │
└─────────────────────┘    └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 10GB+ free disk space
- 8GB+ RAM (recommended)
- Microphone access for voice features

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd bade_bhai
   ./setup.sh
   ```

2. **Setup RAG Knowledge Base** (Optional but Recommended)
   ```bash
   # Add your guidance counselor PDF books
   mkdir -p hinglish-service/documents/raw
   # Copy your PDFs to documents/raw/
   
   # Build the knowledge base
   cd hinglish-service
   python setup_rag.py
   ```

3. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Ollama API: http://localhost:11434

4. **First Use**
   - Allow microphone permissions
   - Try voice recording or text input
   - Experience professional Indian language TTS
   - Get evidence-based guidance responses

## 🎭 Voice Quality Features

### Professional Indian Voices
- **Hindi Speakers**: Rohit, Divya, Aman, Rani - Natural Hindi pronunciation
- **English Speakers**: Mary, Thoma, Swapna - Indian English accents
- **Hinglish Experts**: Divya, Rohit - Perfect code-mixing capabilities
- **21 Languages**: Support for all major Indian languages

### TTS Engine Hierarchy
```
Primary: Indic Parler-TTS (Best Quality)
  ├── Hindi: Rohit/Divya (Professional voices)
  ├── English: Mary/Thoma (Indian accents)
  └── Hinglish: Divya (Code-mixing expert)
    ↓ (if unavailable)
Fallback 1: Coqui TTS (Proven technology)
    ↓ (if unavailable)
Fallback 2: gTTS (Online backup)
    ↓ (if unavailable)
Fallback 3: pyttsx3 (Offline system)
```

## 📚 RAG Knowledge System

### Setup Your Knowledge Base
```bash
# 1. Add guidance counselor PDF books
mkdir -p hinglish-service/documents/raw
# Copy your PDFs: career guides, psychology books, study materials

# 2. Build vector database
cd hinglish-service
python setup_rag.py

# 3. Restart server - now has evidence-based responses!
python main.py
```

### RAG-Enhanced Responses
```
Student: "I'm confused about career choices"
Bot: "I understand career choices can be confusing. According to career guidance resources, it's important to start by identifying your interests, skills, and values. 

[Source: Career Planning Guide, Page 23] suggests creating a list of activities you enjoy and subjects you excel in. This can help narrow down potential career paths that align with your strengths.

What specific areas or subjects do you find most interesting?"
```

## 📱 Usage Guide

### Voice Interaction
1. Click the microphone button
2. Speak in Hindi, English, or mixed (Hinglish)
3. Release to process and get AI response with professional TTS

### Text Chat
1. Type in any language/script
2. Send message for RAG-enhanced AI response
3. Audio responses play automatically with natural pronunciation

### Settings Configuration
- **TTS Engine**: Choose between Indic Parler, Coqui, gTTS, or system voices
- **Voice Selection**: Pick from 69 professional Indian voices
- **Voice Speed**: Adjust playback speed (0.5x to 2.0x)
- **Script Display**: Select Devanagari, Latin, or dual script
- **Conversation Mode**: Guidance counselor, conversational, or casual chat

## 🔧 Configuration

### Environment Variables

**Backend Service**
```env
OLLAMA_URL=http://ollama:11434
COQUI_MODEL_PATH=/app/models
INDIC_PARLER_MODEL=ai4bharat/indic-parler-tts
DEFAULT_HINDI_VOICE=rohit
TEMP_DIR=/app/temp
LOG_LEVEL=INFO
```

**Frontend**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_SUPPORT_HINDI=true
NEXT_PUBLIC_DEFAULT_LANG=hinglish
```

### TTS Engine Configuration

**Indic Parler-TTS** (Primary - Best Quality)
- 21 Indian languages + English
- 69 professional voices
- Perfect Hinglish code-mixing
- Native speaker quality (84.79% for Hindi)

**Coqui TTS** (Fallback - Proven Technology)
- High-quality neural voices
- Supports Hindi and English
- Reliable, fast performance

**Google TTS** (Online Backup)
- Cloud-based synthesis
- Good for quick responses
- Requires internet connection

**System TTS** (Offline Backup)
- Uses system voices
- Completely offline
- Quality varies by system

## 🔧 Development

### Project Structure
```
bade_bhai/
├── hinglish-service/          # FastAPI backend
│   ├── main.py               # Server entry point with RAG
│   ├── audio_pipeline.py     # Audio processing with RAG
│   ├── language_detector.py  # Language detection
│   ├── tts_manager.py        # Enhanced TTS with Indic Parler
│   ├── ollama_client.py      # AI client with RAG
│   ├── rag/                  # RAG system components
│   │   ├── document_processor.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   └── rag_pipeline.py
│   ├── setup_rag.py          # RAG setup script
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Next.js PWA
│   ├── pages/
│   │   ├── index.js         # Main application page
│   │   ├── _app.js          # App wrapper with PWA
│   │   └── _document.js     # Custom HTML document
│   ├── components/          # React components
│   ├── styles/              # Global styles with Hindi fonts
│   ├── public/              # Static assets and PWA files
│   ├── next.config.js       # Next.js configuration
│   ├── package.json         # Node dependencies
│   └── Dockerfile           # Frontend container
├── docker-compose.yml       # Service orchestration
├── setup.sh                 # Installation script
└── README.md               # Documentation
```

### Running in Development Mode

**Backend with RAG**
```bash
cd hinglish-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup RAG (optional)
python setup_rag.py

# Start server
python main.py
```

**Frontend**
```bash
cd frontend
npm install
npm run dev    # Development mode
# OR
npm run build && npm start  # Production mode
```

**Ollama**
```bash
ollama serve
ollama pull gemma2:9b
```

## 🐛 Troubleshooting

### Common Issues

**TTS Installation Issues**
```bash
# Install git-lfs for Parler-TTS
brew install git-lfs
git lfs install

# Install Indic Parler-TTS
pip install git+https://github.com/huggingface/parler-tts.git
```

**RAG System Issues**
- Ensure PDFs contain extractable text (not just images)
- Check vector database exists: `ls vector_db/`
- Verify document processing: `python setup_rag.py`

**Audio Not Working**
- Check microphone permissions
- Verify browser audio support
- Test with different browsers

**Language Detection Issues**
- Mixed content may need adjustment
- Update language patterns
- Check confidence thresholds

### Performance Optimization

**For Better Performance**
- Use GPU acceleration (uncomment in docker-compose.yml)
- Increase RAM allocation
- Use faster storage (SSD)
- Optimize Whisper model size

**For Lower Resource Usage**
- Use smaller Whisper model
- Disable Indic Parler-TTS (use Coqui fallback)
- Reduce audio quality
- Limit concurrent requests

## 📊 Monitoring

### Health Checks
```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:3000/health
curl http://localhost:11434/api/tags

# Check RAG status
curl http://localhost:8000/rag/status

# View service logs
docker-compose logs -f hinglish-service
docker-compose logs -f nextjs-app
docker-compose logs -f ollama
```

### Performance Metrics
```bash
# Service resource usage
docker stats

# Audio processing metrics
curl http://localhost:8000/metrics
```

## 🔒 Security Considerations

### Production Deployment
- Configure CORS properly
- Use HTTPS/WSS protocols
- Implement rate limiting
- Set up authentication
- Monitor audio data handling

### Privacy
- Audio data processed locally
- No data sent to external services (except gTTS)
- Conversation history stored locally
- Model inference runs offline
- RAG documents processed locally

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Follow code style guidelines
4. Add tests for new features
5. Submit pull request

### Code Style
- Python: Follow PEP 8
- JavaScript: Use ESLint configuration
- Commit messages: Use conventional commits
- Documentation: Update README for changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **AI4Bharat** for Indic Parler-TTS
- **OpenAI Whisper** for speech recognition
- **Coqui TTS** for high-quality voice synthesis
- **Ollama** for local LLM inference
- **Meta Llama/Gemma** for language models
- **React** and **FastAPI** communities

## 📞 Support

### Getting Help
- Create GitHub issue for bugs
- Check troubleshooting section
- Review logs for error details
- Test with minimal configuration

### Performance Issues
- Monitor resource usage
- Check model configurations
- Verify network connectivity
- Review audio settings

---
