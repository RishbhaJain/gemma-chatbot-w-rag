#!/bin/bash

# Hinglish Chatbot Setup Script
# Enhanced Audio Processing Pipeline with Hindi/English TTS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Docker
    if command_exists docker; then
        print_success "Docker is installed"
    else
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose is available"
    else
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    # Check available disk space (need at least 10GB)
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 10 ]; then
        print_warning "Available disk space is less than 10GB. You may encounter issues downloading models."
    else
        print_success "Sufficient disk space available"
    fi
    
    # Check RAM (recommend at least 8GB)
    if command_exists free; then
        total_ram=$(free -g | awk '/^Mem:/{print $2}')
        if [ "$total_ram" -lt 8 ]; then
            print_warning "Available RAM is less than 8GB. Performance may be impacted."
        else
            print_success "Sufficient RAM available"
        fi
    fi
}

# Function to setup Ollama and pull models
setup_ollama() {
    print_status "Setting up Ollama and downloading models..."
    
    # Start Ollama service
    docker-compose up -d ollama
    
    # Wait for Ollama to be ready
    print_status "Waiting for Ollama service to start..."
    sleep 10
    
    # Pull Gemma model
    print_status "Downloading Gemma 2 9B model (this may take a while)..."
    docker-compose exec ollama ollama pull gemma2:9b
    
    if [ $? -eq 0 ]; then
        print_success "Gemma 2 9B model downloaded successfully"
    else
        print_error "Failed to download Gemma model"
        exit 1
    fi
}

# Function to setup Python backend
setup_backend() {
    print_status "Setting up Python backend..."
    
    # Create virtual environment if running locally
    if [ "$1" = "local" ]; then
        print_status "Creating Python virtual environment..."
        cd hinglish-service
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd ..
        print_success "Python backend setup complete"
    else
        # Build Docker image
        print_status "Building backend Docker image..."
        docker-compose build hinglish-service
        print_success "Backend Docker image built"
    fi
}

# Function to setup React frontend
setup_frontend() {
    print_status "Setting up React frontend..."
    
    if [ "$1" = "local" ]; then
        print_status "Installing Node.js dependencies..."
        cd frontend
        npm install
        cd ..
        print_success "Frontend dependencies installed"
    else
        # Build Docker image
        print_status "Building frontend Docker image..."
        docker-compose build react-app
        print_success "Frontend Docker image built"
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p models
    mkdir -p audio_temp
    mkdir -p tts_models
    mkdir -p logs
    
    # Set permissions
    chmod 755 models audio_temp tts_models logs
    
    print_success "Directories created"
}

# Function to download TTS models
download_tts_models() {
    print_status "Downloading TTS models..."
    
    # Create TTS models directory
    mkdir -p tts_models
    
    # Note: Coqui TTS models will be downloaded on first use
    # This is a placeholder for future model pre-downloading
    print_status "TTS models will be downloaded automatically on first use"
    print_success "TTS setup complete"
}

# Function to start services
start_services() {
    print_status "Starting all services..."
    
    # Start all services
    docker-compose up -d
    
    print_status "Waiting for services to start..."
    sleep 30
    
    # Check service health
    check_service_health
}

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    
    # Check Ollama
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "Ollama service is healthy"
    else
        print_error "Ollama service is not responding"
    fi
    
    # Check backend
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Backend service is healthy"
    else
        print_error "Backend service is not responding"
    fi
    
    # Check frontend
    if curl -s http://localhost:3000/health >/dev/null 2>&1; then
        print_success "Frontend service is healthy"
    else
        print_error "Frontend service is not responding"
    fi
}

# Function to run tests
run_tests() {
    print_status "Running basic functionality tests..."
    
    # Test language detection
    python3 -c "
import sys
sys.path.append('hinglish-service')
from language_detector import LanguageDetector
detector = LanguageDetector()
result = detector.detect_language('Hello नमस्ते')
print(f'Language detection test: {result}')
assert result in ['hi-en', 'en', 'hi'], 'Language detection failed'
print('✓ Language detection test passed')
"
    
    print_success "Basic tests completed"
}

# Function to display completion message
display_completion() {
    print_success "🎉 Hinglish Chatbot setup completed!"
    echo
    echo -e "${GREEN}Access your chatbot at:${NC}"
    echo -e "  Frontend: ${BLUE}http://localhost:3000${NC}"
    echo -e "  Backend API: ${BLUE}http://localhost:8000${NC}"
    echo -e "  Ollama API: ${BLUE}http://localhost:11434${NC}"
    echo
    echo -e "${GREEN}Features available:${NC}"
    echo "  ✓ Hinglish speech recognition (Whisper)"
    echo "  ✓ Multi-engine TTS (Coqui, gTTS, pyttsx3)"
    echo "  ✓ Language detection (Hindi/English/Mixed)"
    echo "  ✓ AI responses (Gemma 2 9B)"
    echo "  ✓ Real-time WebSocket communication"
    echo "  ✓ Dual script support (Devanagari/Latin)"
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Open http://localhost:3000 in your browser"
    echo "  2. Allow microphone permissions when prompted"
    echo "  3. Try voice recording or text input in Hindi/English"
    echo "  4. Adjust settings for voice preferences"
    echo
    echo -e "${BLUE}To stop services:${NC} docker-compose down"
    echo -e "${BLUE}To view logs:${NC} docker-compose logs -f"
    echo -e "${BLUE}To restart:${NC} docker-compose restart"
}

# Main setup function
main() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════╗"
    echo "║     Hinglish Chatbot Setup           ║"
    echo "║  Enhanced Audio Processing Pipeline  ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Parse command line arguments
    DEPLOYMENT_MODE="docker"
    SKIP_MODELS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --local)
                DEPLOYMENT_MODE="local"
                shift
                ;;
            --skip-models)
                SKIP_MODELS=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --local       Setup for local development (without Docker)"
                echo "  --skip-models Skip model downloads (for faster setup)"
                echo "  --help        Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run setup steps
    check_requirements
    create_directories
    
    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        setup_backend "docker"
        setup_frontend "docker"
        
        if [ "$SKIP_MODELS" = false ]; then
            setup_ollama
            download_tts_models
        fi
        
        start_services
    else
        setup_backend "local"
        setup_frontend "local"
        print_status "Local development setup complete"
        print_status "To start services manually:"
        echo "  1. Start Ollama: ollama serve"
        echo "  2. Start backend: cd hinglish-service && python main.py"
        echo "  3. Start frontend: cd frontend && npm start"
    fi
    
    # Run tests if possible
    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        sleep 10
        run_tests
    fi
    
    display_completion
}

# Trap errors and cleanup
trap 'print_error "Setup failed! Check the logs above for details."' ERR

# Run main function
main "$@" 