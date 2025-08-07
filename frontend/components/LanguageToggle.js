import React from 'react';
import { LanguageIcon } from '@heroicons/react/24/outline';

const LanguageToggle = ({ currentLanguage, onToggle, getDisplayName }) => {
  const languages = [
    { code: 'hinglish', name: 'Hinglish', flag: '🇮🇳', color: 'bg-gradient-to-r from-orange-500 to-green-500' },
    { code: 'hi', name: 'हिंदी', flag: '🇮🇳', color: 'bg-orange-500' },
    { code: 'en', name: 'English', flag: '🇺🇸', color: 'bg-blue-500' }
  ];

  const currentLangData = languages.find(lang => lang.code === currentLanguage) || languages[0];

  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 transition-colors shadow-sm"
        title={`Current language: ${getDisplayName(currentLanguage)}`}
      >
        <div className={`w-4 h-4 rounded-full ${currentLangData.color} flex items-center justify-center text-xs`}>
          <span className="text-white font-bold">
            {currentLanguage === 'hi' ? 'हि' : 
             currentLanguage === 'en' ? 'EN' : 
             'HI-EN'}
          </span>
        </div>
        <span className="text-xs sm:text-sm font-medium text-gray-700 hidden sm:inline">
          {getDisplayName(currentLanguage)}
        </span>
      </button>

      {/* Language indicator tooltip */}
      <div className="absolute top-full left-0 mt-2 bg-black text-white text-xs px-2 py-1 rounded opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity whitespace-nowrap">
        Click to switch language
      </div>
    </div>
  );
};

export default LanguageToggle; 