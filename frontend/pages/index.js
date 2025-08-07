import React, { useState, useEffect, useRef, useCallback } from 'react';
import Head from 'next/head';
import { MicrophoneIcon, StopIcon, SpeakerWaveIcon, Cog6ToothIcon } from '@heroicons/react/24/solid';
import { ChatBubbleLeftEllipsisIcon, LanguageIcon } from '@heroicons/react/24/outline';
// Components
import ChatMessage from '../components/ChatMessage';
import VoiceRecorder from '../components/VoiceRecorder';
import LanguageToggle from '../components/LanguageToggle';
import SettingsPanel from '../components/SettingsPanel';
import ConnectionStatus from '../components/ConnectionStatus';

export default function HinglishChatbot({ pwa }) {
  // State management
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState('hinglish');
  const [showSettings, setShowSettings] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [audioEnabled, setAudioEnabled] = useState(true);
  
  // Settings state
  const [settings, setSettings] = useState({
    ttsEngine: 'coqui',
    voiceSpeed: 1.0,
    voiceModel: 'multilingual', // New unified voice model selection
    voiceQuality: 'balanced', // high, balanced, fast
    hindiVoice: 'hi_female', // Updated default to female (more natural)
    englishVoice: 'en_jenny', // Updated to Jenny voice
    autoLanguageDetection: true,
    scriptDisplay: 'dual', // 'devanagari', 'latin', 'dual'
    conversationMode: 'guidance_counselor' // conversation style - default to counselor mode
  });

  // Conversation management
  const [conversationMode, setConversationMode] = useState('guidance_counselor'); // hinglish, conversational, counselor
  
  // Sync conversation mode with settings
  useEffect(() => {
    setConversationMode(settings.conversationMode);
  }, [settings.conversationMode]);

  // Refs
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);
  const audioContextRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Initialize WebSocket connection
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    
    const connectWebSocket = () => {
      setConnectionStatus('connecting');
      
      try {
        socketRef.current = new WebSocket(wsUrl);
        
        socketRef.current.onopen = () => {
          setConnectionStatus('connected');
          console.log('Connected to Hinglish service');
        };
        
        socketRef.current.onclose = () => {
          setConnectionStatus('disconnected');
          console.log('Disconnected from Hinglish service');
          
          // Auto-reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };
        
        socketRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionStatus('disconnected');
        };
        
        socketRef.current.onmessage = (event) => {
          handleSocketMessage(event.data);
        };
        
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setConnectionStatus('disconnected');
        setTimeout(connectWebSocket, 3000);
      }
    };
    
    connectWebSocket();

    // Cleanup
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle WebSocket messages
  const handleSocketMessage = useCallback((data) => {
    const message = JSON.parse(data);
    
    if (message.type === 'audio_response' || message.type === 'text_response') {
      const newMessage = {
        id: Date.now(),
        type: 'ai',
        text: message.response_text,
        language: message.detected_language,
        audioBase64: message.audio_response,
        ttsEngine: message.tts_engine,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, newMessage]);
      
      // Auto-play audio if enabled
      if (audioEnabled && message.audio_response) {
        playAudioResponse(message.audio_response);
      }
    } else if (message.type === 'error') {
      console.error('Server error:', message.message);
      // Show error message
      const errorMessage = {
        id: Date.now(),
        type: 'error',
        text: `Error: ${message.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
    
    setIsProcessing(false);
  }, [audioEnabled]);

  // Send text message
  const sendTextMessage = useCallback((text) => {
    if (!text.trim() || !socketRef.current) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: text,
      language: currentLanguage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsProcessing(true);

    // Send to server
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'text',
        data: text,
        language: currentLanguage,
        conversationMode: conversationMode
      }));
    }
  }, [currentLanguage, conversationMode]);

  // Send audio message
  const sendAudioMessage = useCallback((audioBlob) => {
    if (!audioBlob || !socketRef.current) return;

    setIsProcessing(true);

    // Convert audio blob to base64
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64Audio = reader.result.split(',')[1]; // Remove data URL prefix
      
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: 'audio',
          data: base64Audio,
          language: currentLanguage,
          conversationMode: conversationMode
        }));
      }
    };
    reader.readAsDataURL(audioBlob);
  }, [currentLanguage, conversationMode]);

  // Play audio response
  const playAudioResponse = useCallback((audioBase64) => {
    try {
      const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
      audio.play().catch(error => {
        console.error('Audio playback failed:', error);
      });
    } catch (error) {
      console.error('Audio creation failed:', error);
    }
  }, []);

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    sendTextMessage(inputText);
  };

  // Handle recording completion
  const handleRecordingComplete = (audioBlob) => {
    sendAudioMessage(audioBlob);
  };

  // Toggle language
  const toggleLanguage = () => {
    const languages = ['hinglish', 'hi', 'en'];
    const currentIndex = languages.indexOf(currentLanguage);
    const nextIndex = (currentIndex + 1) % languages.length;
    setCurrentLanguage(languages[nextIndex]);
  };

  // Get language display name
  const getLanguageDisplayName = (lang) => {
    switch (lang) {
      case 'hi': return 'हिंदी';
      case 'en': return 'English';
      case 'hinglish': return 'Hinglish';
      default: return lang;
    }
  };

  // Get placeholder text based on language
  const getPlaceholderText = () => {
    switch (currentLanguage) {
      case 'hi': return 'अपनी बात यहाँ साझा करें... मैं यहाँ आपकी मदद के लिए हूँ';
      case 'en': return 'Share what\'s on your mind... I\'m here to help and listen';
      case 'hinglish': return 'Apni baat share kariye... Main yahan aapki help ke liye hun';
      default: return 'Share what\'s on your mind... I\'m here to help and listen';
    }
  };

  return (
    <>
      <Head>
        <title>GuideMate AI</title>
        <meta name="description" content="Supportive AI counselor providing guidance for students in Hindi and English. A safe space for academic, career, and personal conversations." />
        <meta name="keywords" content="Guidance Counselor, Student Support, Academic Help, Career Guidance, Hindi, English, Mental Health" />
        <meta property="og:title" content="Student Guidance Counselor AI" />
        <meta property="og:description" content="Compassionate AI counselor supporting students with academics, careers, and personal challenges" />
        <meta property="og:type" content="website" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Student Guidance Counselor AI" />
        <meta name="twitter:description" content="Safe, supportive AI counselor for student guidance" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-green-100">
          <div className="max-w-4xl mx-auto px-2 sm:px-4 py-3 sm:py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 sm:space-x-3">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-r from-green-500 to-teal-600 rounded-full flex items-center justify-center shadow-md">
                  <svg className="w-5 h-5 sm:w-7 sm:h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C20.832 18.477 19.246 18 17.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-lg sm:text-xl font-bold text-gray-800">GuideMate AI</h1>
                  <p className="text-xs sm:text-sm text-green-600 font-medium">Safe space for support & guidance</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-1 sm:space-x-3">
                <ConnectionStatus status={connectionStatus} />
                <LanguageToggle 
                  currentLanguage={currentLanguage}
                  onToggle={toggleLanguage}
                  getDisplayName={getLanguageDisplayName}
                />
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="p-1.5 sm:p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <Cog6ToothIcon className="w-5 h-5" />
                </button>
                
                {/* PWA Install Button */}
                {pwa?.isInstallable && (
                  <button
                    onClick={pwa.promptInstall}
                    className="px-2 sm:px-3 py-1.5 sm:py-2 bg-blue-600 text-white text-xs sm:text-sm rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <span className="hidden sm:inline">Install App</span>
                    <span className="sm:hidden">Install</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Settings Panel */}
        {showSettings && (
          <SettingsPanel
            settings={settings}
            onSettingsChange={setSettings}
            onClose={() => setShowSettings(false)}
          />
        )}

        {/* Main Chat Area */}
        <main className="max-w-4xl mx-auto px-2 sm:px-4 py-3 sm:py-6">
          {/* Welcome & Chat Messages */}
          <div className="bg-white rounded-lg shadow-sm mb-4 sm:mb-6 h-64 sm:h-80 md:h-96 overflow-y-auto border border-green-100">
            <div className="p-3 sm:p-4 md:p-6 space-y-3 sm:space-y-4">
              {messages.length === 0 ? (
                <div className="text-center py-4 sm:py-6 md:py-8">
                  <div className="w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 bg-gradient-to-r from-green-400 to-teal-500 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4 shadow-lg">
                    <svg className="w-6 h-6 sm:w-7 sm:h-7 md:w-9 md:h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                  </div>
                  <h2 className="text-lg sm:text-xl font-semibold text-gray-800 mb-2 sm:mb-3">
                    {currentLanguage === 'hi' ? 'नमस्ते! मैं यहाँ आपकी मदद के लिए हूँ' : 
                     currentLanguage === 'en' ? 'Hello! I\'m here to support you' : 
                     'Namaste! Main yahan aapki help ke liye hun'}
                  </h2>
                  <div className="bg-green-50 rounded-lg p-3 sm:p-4 mb-3 sm:mb-4 border border-green-100">
                    <p className="text-green-800 text-xs sm:text-sm leading-relaxed">
                      {currentLanguage === 'hi' ? 'यह एक सुरक्षित स्थान है जहाँ आप अपनी पढ़ाई, करियर, या व्यक्तिगत चुनौतियों के बारे में बात कर सकते हैं। मैं यहाँ आपकी बात सुनने और सहायता करने के लिए हूँ।' :
                       currentLanguage === 'en' ? 'This is a safe space where you can talk about your studies, career goals, or personal challenges. I\'m here to listen and support you.' :
                       'Yeh ek safe space hai jahan aap apni studies, career goals, ya personal challenges ke baare mein baat kar sakte hain. Main yahan sunne aur support karne ke liye hun.'}
                    </p>
                  </div>
                  <p className="text-gray-600 text-sm">
                    {currentLanguage === 'hi' ? 'आप हिंदी, अंग्रेजी, या दोनों में बात कर सकते हैं' :
                     currentLanguage === 'en' ? 'You can speak in Hindi, English, or both' :
                     'Aap Hindi, English, ya dono mein baat kar sakte hain'}
                  </p>
                </div>
              ) : (
                messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    onPlayAudio={playAudioResponse}
                    scriptDisplay={settings.scriptDisplay}
                  />
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="bg-white rounded-lg shadow-sm p-2 sm:p-4 md:p-6 border border-green-100">
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
              {/* Text Input */}
              <div className="flex-1">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder={getPlaceholderText()}
                  className={`w-full px-3 sm:px-4 py-2 sm:py-3 border border-green-200 rounded-lg focus:ring-2 focus:ring-green-400 focus:border-transparent resize-none placeholder-gray-500 text-sm sm:text-base ${
                    currentLanguage === 'hi' ? 'font-hindi' : ''
                  }`}
                  rows="2"
                  disabled={isProcessing}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                />
              </div>

              {/* Voice Recorder & Send Button Row */}
              <div className="flex items-center justify-center space-x-2 sm:contents">
                {/* Voice Recorder */}
                <VoiceRecorder
                  onRecordingComplete={handleRecordingComplete}
                  disabled={isProcessing}
                  currentLanguage={currentLanguage}
                />

                {/* Send Button */}
                <button
                  type="submit"
                  disabled={!inputText.trim() || isProcessing}
                  className="flex-1 sm:flex-none px-4 sm:px-6 py-2.5 sm:py-3 bg-gradient-to-r from-green-500 to-teal-600 text-white rounded-lg hover:from-green-600 hover:to-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium shadow-sm text-sm sm:text-base min-h-[44px] flex items-center justify-center"
                >
                {isProcessing ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>
                      {currentLanguage === 'hi' ? 'सुन रहा हूँ...' : 
                       currentLanguage === 'en' ? 'Thinking...' : 'Soch raha hun ...'}
                    </span>
                  </div>
                ) : (
                  <>
                    <svg
                      className="w-4 h-4 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      style={{ transform: 'rotate(90deg)' }}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                      />
                    </svg>
                    <span>
                      {currentLanguage === 'hi' ? 'साझा करें' : 
                       currentLanguage === 'en' ? 'Share' : 'Share kariye'}
                    </span>
                  </>
                )}
                </button>
              </div>
            </form>

            {/* Quick Start Conversation Topics */}
            {messages.length === 0 && (
              <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-green-100">
                <p className="text-xs sm:text-sm text-gray-600 mb-2 sm:mb-3 font-medium">
                  {currentLanguage === 'hi' ? 'आप इन विषयों पर बात कर सकते हैं:' :
                   currentLanguage === 'en' ? 'You can talk about:' :
                   'Aap in topics par baat kar sakte hain:'}
                </p>
                <div className="flex flex-wrap gap-2">
                  {[
                    { 
                      hi: '📚 पढ़ाई की समस्याएं', 
                      en: '📚 Study challenges',
                      hinglish: '📚 Padhai ki problems'
                    },
                    { 
                      hi: '🎯 करियर गाइडेंस', 
                      en: '🎯 Career guidance',
                      hinglish: '🎯 Career guidance'
                    },
                    { 
                      hi: '👥 दोस्तों के साथ मुद्दे', 
                      en: '👥 Friend issues',
                      hinglish: '👥 Dosto ke saath issues'
                    },
                    { 
                      hi: '🏠 पारिवारिक दबाव', 
                      en: '🏠 Family pressure',
                      hinglish: '🏠 Parivarik pressure'
                    },
                    { 
                      hi: '😟 तनाव और चिंता', 
                      en: '😟 Stress & anxiety',
                      hinglish: '😟 Stress aur anxiety'
                    },
                    { 
                      hi: '🎓 कॉलेज चुनना', 
                      en: '🎓 College selection',
                      hinglish: '🎓 College choose karna'
                    }
                  ].map((topic, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        const topicText = topic[currentLanguage] || topic.en;
                        setInputText(`I want to talk about ${topicText.replace(/📚|🎯|👥|🏠|😟|🎓/, '').trim()}`);
                      }}
                      className="px-2 sm:px-3 py-1.5 sm:py-2 bg-green-50 text-green-700 rounded-full text-xs sm:text-sm hover:bg-green-100 transition-colors border border-green-200 min-h-[32px] flex items-center justify-center"
                    >
                      {topic[currentLanguage] || topic.en}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Audio Controls */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-gray-200 space-y-2 sm:space-y-0">
              <div className="flex items-center space-x-2 sm:space-x-4">
                <button
                  onClick={() => setAudioEnabled(!audioEnabled)}
                  className={`flex items-center space-x-2 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg transition-colors ${
                    audioEnabled 
                      ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                      : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                  }`}
                >
                  <SpeakerWaveIcon className="w-4 h-4" />
                  <span className="text-xs sm:text-sm">
                    {audioEnabled ? 
                      (currentLanguage === 'hi' ? 'ऑडियो चालू' : 
                       currentLanguage === 'en' ? 'Audio On' : 'Audio On') : 
                      (currentLanguage === 'hi' ? 'ऑडियो बंद' : 
                       currentLanguage === 'en' ? 'Audio Off' : 'Audio band')
                    }
                  </span>
                </button>
              </div>

              <div className="text-xs text-gray-500 text-center sm:text-left">
                {currentLanguage === 'hi' ? 'भाषा: ' : 
                 currentLanguage === 'en' ? 'Language: ' : 'Language: '}
                <span className="font-medium">{getLanguageDisplayName(currentLanguage)}</span>
              </div>
            </div>
          </div>

          {/* Supportive Footer */}
          <div className="mt-6 sm:mt-8 p-4 sm:p-6 bg-gradient-to-r from-green-50 to-teal-50 rounded-lg border border-green-100">
            <div className="text-center">
              <div className="flex justify-center mb-2 sm:mb-3">
                <div className="w-6 h-6 sm:w-8 sm:h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.031 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
              </div>
              <h3 className="text-xs sm:text-sm font-semibold text-green-800 mb-1 sm:mb-2">
                {currentLanguage === 'hi' ? 'गोपनीय और सुरक्षित' :
                 currentLanguage === 'en' ? 'Confidential & Safe' :
                 'Gopniya aur Surakshit'}
              </h3>
              <p className="text-xs text-green-700 leading-relaxed max-w-2xl mx-auto">
                {currentLanguage === 'hi' ? 
                  'यह बातचीत पूरी तरह निजी है। यदि आपको तत्काल सहायता की आवश्यकता है, तो कृपया किसी विश्वसनीय वयस्क, शिक्षक, या परामर्शदाता से संपर्क करें।' :
                 currentLanguage === 'en' ? 
                  'Your conversation is completely private. If you need immediate help, please contact a trusted adult, teacher, or counselor.' :
                  'Aapki conversation puri tarah private hai. Agar aapko immediate help chahiye, to kripaya kisi trusted adult, teacher, ya counselor se contact kariye.'}
              </p>
              <div className="mt-2 sm:mt-3 flex justify-center space-x-3 sm:space-x-6 text-xs text-green-600">
                <span className="flex items-center">
                  <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {currentLanguage === 'hi' ? 'सुरक्षित' : currentLanguage === 'en' ? 'Safe' : 'Surakshit'}
                </span>
                <span className="flex items-center">
                  <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  {currentLanguage === 'hi' ? 'निजी' : currentLanguage === 'en' ? 'Private' : 'Niji'}
                </span>
                <span className="flex items-center">
                  <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                  {currentLanguage === 'hi' ? 'सहायक' : currentLanguage === 'en' ? 'Supportive' : 'Sahayak'}
                </span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
} 