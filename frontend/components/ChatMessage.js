import React, { useState } from 'react';
import { SpeakerWaveIcon, UserIcon, ChatBubbleLeftEllipsisIcon } from '@heroicons/react/24/outline';
import { PlayIcon } from '@heroicons/react/24/solid';

const ChatMessage = ({ message, onPlayAudio, scriptDisplay = 'dual' }) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Handle audio playback
  const handlePlayAudio = () => {
    if (message.audioBase64 && onPlayAudio) {
      setIsPlayingAudio(true);
      onPlayAudio(message.audioBase64);
      
      // Reset playing state after a delay (estimated audio duration)
      const estimatedDuration = Math.max(2000, message.text.length * 100); // Rough estimate
      setTimeout(() => {
        setIsPlayingAudio(false);
      }, estimatedDuration);
    }
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Determine if text is primarily Hindi (contains Devanagari characters)
  const hasDevanagariScript = (text) => {
    return /[\u0900-\u097F]/.test(text);
  };

  // Render text based on script display preference
  const renderText = () => {
    const text = message.text;
    const hasDevanagari = hasDevanagariScript(text);
    
    switch (scriptDisplay) {
      case 'devanagari':
        // Show only Devanagari parts or romanized equivalent
        return hasDevanagari ? text : <em className="text-gray-600">{text}</em>;
      
      case 'latin':
        // Show only Latin script parts
        return !hasDevanagari ? text : <em className="text-gray-600">{text}</em>;
      
      case 'dual':
      default:
        // Show both scripts naturally
        return text;
    }
  };

  // Get message style based on type
  const getMessageStyle = () => {
    switch (message.type) {
      case 'user':
        return {
          container: 'flex justify-end',
          bubble: 'bg-blue-500 text-white',
          textAlign: 'text-right'
        };
      case 'ai':
        return {
          container: 'flex justify-start',
          bubble: 'bg-gray-100 text-gray-900',
          textAlign: 'text-left'
        };
      case 'error':
        return {
          container: 'flex justify-center',
          bubble: 'bg-red-100 text-red-700 border border-red-200',
          textAlign: 'text-center'
        };
      default:
        return {
          container: 'flex justify-start',
          bubble: 'bg-gray-100 text-gray-900',
          textAlign: 'text-left'
        };
    }
  };

  const style = getMessageStyle();

  return (
    <div className={`${style.container} mb-4`}>
      <div className="max-w-xs lg:max-w-md">
        {/* Message Header */}
        <div className={`flex items-center space-x-2 mb-1 ${
          message.type === 'user' ? 'justify-end' : 'justify-start'
        }`}>
          {/* Avatar */}
          <div className={`flex items-center space-x-2 ${
            message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
          }`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
              message.type === 'user' 
                ? 'bg-blue-500 text-white' 
                : message.type === 'ai'
                ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                : 'bg-red-500 text-white'
            }`}>
              {message.type === 'user' ? (
                <UserIcon className="w-4 h-4" />
              ) : message.type === 'ai' ? (
                <ChatBubbleLeftEllipsisIcon className="w-4 h-4" />
              ) : (
                '!'
              )}
            </div>
            
            {/* Timestamp and metadata */}
            <div className={`text-xs text-gray-500 ${style.textAlign}`}>
              {formatTime(message.timestamp)}
              {message.language && message.type !== 'error' && (
                <span className="ml-1 px-1 py-0.5 bg-gray-200 rounded text-xs">
                  {message.language === 'hi' ? 'हि' : 
                   message.language === 'en' ? 'EN' : 
                   message.language === 'hi-en' ? 'हि-EN' : 
                   message.language.toUpperCase()}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Message Bubble */}
        <div className={`relative px-4 py-3 rounded-lg ${style.bubble} ${
          message.type === 'user' ? 'rounded-br-none' : 'rounded-bl-none'
        }`}>
          {/* Message Text */}
          <div className={`${style.textAlign} ${
            hasDevanagariScript(message.text) ? 'font-hindi leading-relaxed' : ''
          }`}>
            {renderText()}
          </div>

          {/* Audio Controls for AI messages */}
          {message.type === 'ai' && message.audioBase64 && (
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-200">
              <button
                onClick={handlePlayAudio}
                disabled={isPlayingAudio}
                className={`flex items-center space-x-1 px-2 py-1 rounded text-xs transition-colors ${
                  isPlayingAudio 
                    ? 'bg-blue-100 text-blue-600 cursor-not-allowed' 
                    : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                }`}
                title={isPlayingAudio ? 'Playing audio...' : 'Play audio response'}
              >
                {isPlayingAudio ? (
                  <>
                    <div className="w-3 h-3 border border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    <span>Playing...</span>
                  </>
                ) : (
                  <>
                    <PlayIcon className="w-3 h-3" />
                    <span>Play</span>
                  </>
                )}
              </button>

              {/* TTS Engine indicator */}
              {message.ttsEngine && (
                <span className="text-xs text-gray-500 opacity-75">
                  {message.ttsEngine.toUpperCase()}
                </span>
              )}
            </div>
          )}

          {/* Language detection indicator for user messages */}
          {message.type === 'user' && message.language && (
            <div className="mt-2 pt-2 border-t border-blue-400 border-opacity-30">
              <span className="text-xs text-blue-200 opacity-75">
                Detected: {message.language === 'hi' ? 'Hindi' : 
                          message.language === 'en' ? 'English' : 
                          message.language === 'hi-en' ? 'Mixed' : 
                          message.language}
              </span>
            </div>
          )}

          {/* Processing indicators */}
          {message.processing && (
            <div className="mt-2 flex items-center space-x-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              <span className="text-xs text-gray-500 ml-2">Processing...</span>
            </div>
          )}
        </div>

        {/* Message delivery status */}
        {message.type === 'user' && (
          <div className={`mt-1 ${style.textAlign}`}>
            <span className="text-xs text-gray-400">
              {message.delivered ? '✓ Delivered' : '⏳ Sending...'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage; 