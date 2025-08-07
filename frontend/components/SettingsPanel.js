import React from 'react';
import { XMarkIcon, SpeakerWaveIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';

const SettingsPanel = ({ settings, onSettingsChange, onClose }) => {
  const updateSetting = (key, value) => {
    onSettingsChange({
      ...settings,
      [key]: value
    });
  };

  const ttsEngines = [
    { value: 'coqui', label: 'Coqui TTS (Best Quality)', description: 'Neural AI voices with natural speech' },
    { value: 'gtts', label: 'Google TTS (Fast)', description: 'Fast and reliable for basic usage' },
    { value: 'pyttsx3', label: 'System TTS (Offline)', description: 'Uses built-in system voices' }
  ];

  const voiceOptions = [
    { value: 'hi_female', label: 'Hindi Female (Natural)', description: 'Soft, natural female Hindi voice' },
    { value: 'hi_male', label: 'Hindi Male (Traditional)', description: 'Standard male Hindi voice' },
    { value: 'en_jenny', label: 'English Female (Jenny)', description: 'Warm, natural English voice' },
    { value: 'en_vctk', label: 'English Multi-Speaker', description: 'High-quality varied voices' },
    { value: 'multilingual', label: 'Multilingual XTTS', description: 'Latest AI model, best quality' }
  ];

  const voiceQualityOptions = [
    { value: 'high', label: 'High Quality', description: 'Best sound, slower generation' },
    { value: 'balanced', label: 'Balanced', description: 'Good quality, reasonable speed' },
    { value: 'fast', label: 'Fast', description: 'Quick generation, lower quality' }
  ];

  const scriptDisplayOptions = [
    { value: 'dual', label: 'Dual Script (Recommended)', description: 'Show both Devanagari and Latin' },
    { value: 'devanagari', label: 'Devanagari Only', description: 'Show only Hindi script' },
    { value: 'latin', label: 'Latin Only', description: 'Show only English script' }
  ];

  const conversationModes = [
    { value: 'guidance_counselor', label: 'Guidance Counselor (Recommended)', description: 'Supportive, professional counseling mode for students' },
    { value: 'conversational', label: 'Maximum Conversational', description: 'Most engaging dialogue with follow-up questions' },
    { value: 'hinglish', label: 'Standard Hinglish', description: 'Natural mixed language responses' },
    { value: 'casual_chat', label: 'Casual Chat', description: 'Friendly informal conversation' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <h2 className="text-xl font-semibold text-gray-800">Counselor Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Settings Content */}
        <div className="p-6 space-y-8">
          {/* Voice Quality Tips */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-semibold text-blue-900 mb-2 flex items-center">
              💡 For Better Voice Quality
            </h3>
            <div className="text-sm text-blue-800 space-y-1">
              <div>• Choose <strong>Multilingual XTTS</strong> for the most natural sound</div>
              <div>• Use <strong>High Quality</strong> mode for important conversations</div>
              <div>• Female voices often sound more natural than male voices</div>
              <div>• Test different voices to find your preference</div>
            </div>
          </div>

          {/* TTS Engine Selection */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
              <SpeakerWaveIcon className="w-5 h-5" />
              <span>Text-to-Speech Engine</span>
            </h3>
            <div className="space-y-3">
              {ttsEngines.map((engine) => (
                <label key={engine.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="ttsEngine"
                    value={engine.value}
                    checked={settings.ttsEngine === engine.value}
                    onChange={(e) => updateSetting('ttsEngine', e.target.value)}
                    className="mt-1 w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div>
                    <div className="font-medium text-gray-900">{engine.label}</div>
                    <div className="text-sm text-gray-500">{engine.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Conversation Mode Selection */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <span>Conversation Style</span>
            </h3>
            <div className="space-y-3">
              {conversationModes.map((mode) => (
                <label key={mode.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="conversationMode"
                    value={mode.value}
                    checked={settings.conversationMode === mode.value}
                    onChange={(e) => updateSetting('conversationMode', e.target.value)}
                    className="mt-1 w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div>
                    <div className="font-medium text-gray-900">{mode.label}</div>
                    <div className="text-sm text-gray-500">{mode.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Voice Selection */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m-9 0h10m-10 0l1 12a2 2 0 002 2h6a2 2 0 002-2L20 4" />
              </svg>
              <span>Voice Model</span>
            </h3>
            <div className="space-y-3">
              {voiceOptions.map((voice) => (
                <label key={voice.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="voiceModel"
                    value={voice.value}
                    checked={settings.voiceModel === voice.value}
                    onChange={(e) => updateSetting('voiceModel', e.target.value)}
                    className="mt-1 w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div>
                    <div className="font-medium text-gray-900">{voice.label}</div>
                    <div className="text-sm text-gray-500">{voice.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Voice Quality */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
              <span>Voice Quality</span>
            </h3>
            <div className="space-y-3">
              {voiceQualityOptions.map((quality) => (
                <label key={quality.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="voiceQuality"
                    value={quality.value}
                    checked={settings.voiceQuality === quality.value}
                    onChange={(e) => updateSetting('voiceQuality', e.target.value)}
                    className="mt-1 w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div>
                    <div className="font-medium text-gray-900">{quality.label}</div>
                    <div className="text-sm text-gray-500">{quality.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Voice Speed */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Voice Speed</h3>
            <div className="space-y-3">
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={settings.voiceSpeed}
                onChange={(e) => updateSetting('voiceSpeed', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-sm text-gray-500">
                <span>Slow (0.5x)</span>
                <span className="font-medium text-gray-900">{settings.voiceSpeed}x</span>
                <span>Fast (2.0x)</span>
              </div>
            </div>
          </div>

          {/* Voice Test */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Test Voice</h3>
            <div className="space-y-3">
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    // Test Hindi voice
                    const testText = "नमस्ते, मैं आपका AI सहायक हूं। मुझसे हिंदी में बात करें।";
                    // Implementation would send test message to backend
                    console.log('Testing Hindi voice:', testText);
                  }}
                  className="flex-1 px-4 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors font-medium"
                >
                  🎤 Test Hindi Voice
                </button>
                <button
                  onClick={() => {
                    // Test English voice
                    const testText = "Hello, I am your AI assistant. You can speak to me in English.";
                    // Implementation would send test message to backend
                    console.log('Testing English voice:', testText);
                  }}
                  className="flex-1 px-4 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors font-medium"
                >
                  🎤 Test English Voice
                </button>
              </div>
              <div className="text-sm text-gray-500 text-center">
                Click to hear a sample of the selected voice
              </div>
            </div>
          </div>

          {/* Voice Preferences */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Voice Preferences</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hindi Voice
                </label>
                <select
                  value={settings.hindiVoice}
                  onChange={(e) => updateSetting('hindiVoice', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  {voiceOptions.filter(v => v.value.startsWith('hi_')).map((voice) => (
                    <option key={voice.value} value={voice.value}>
                      {voice.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  English Voice
                </label>
                <select
                  value={settings.englishVoice}
                  onChange={(e) => updateSetting('englishVoice', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  {voiceOptions.filter(v => v.value.startsWith('en_')).map((voice) => (
                    <option key={voice.value} value={voice.value}>
                      {voice.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Script Display */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Script Display</h3>
            <div className="space-y-3">
              {scriptDisplayOptions.map((option) => (
                <label key={option.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="scriptDisplay"
                    value={option.value}
                    checked={settings.scriptDisplay === option.value}
                    onChange={(e) => updateSetting('scriptDisplay', e.target.value)}
                    className="mt-1 w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div>
                    <div className="font-medium text-gray-900">{option.label}</div>
                    <div className="text-sm text-gray-500">{option.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Advanced Options */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Advanced Options</h3>
            <div className="space-y-4">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.autoLanguageDetection}
                  onChange={(e) => updateSetting('autoLanguageDetection', e.target.checked)}
                  className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div>
                  <div className="font-medium text-gray-900">Auto Language Detection</div>
                  <div className="text-sm text-gray-500">Automatically detect the language of responses</div>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 transition-colors"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel; 