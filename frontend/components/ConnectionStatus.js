import React from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon 
} from '@heroicons/react/24/solid';

const ConnectionStatus = ({ status }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: CheckCircleIcon,
          color: 'text-green-500',
          bgColor: 'bg-green-100',
          text: 'Connected',
          description: 'Real-time connection active'
        };
      case 'connecting':
        return {
          icon: ExclamationTriangleIcon,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-100',
          text: 'Connecting',
          description: 'Establishing connection...'
        };
      case 'disconnected':
        return {
          icon: XCircleIcon,
          color: 'text-red-500',
          bgColor: 'bg-red-100',
          text: 'Disconnected',
          description: 'No connection to server'
        };
      default:
        return {
          icon: ExclamationTriangleIcon,
          color: 'text-gray-500',
          bgColor: 'bg-gray-100',
          text: 'Unknown',
          description: 'Connection status unknown'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div className="relative group">
      {/* Status Indicator */}
      <div className={`flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg ${config.bgColor} border border-opacity-20 transition-colors`}>
        <div className="relative">
          <Icon className={`w-4 h-4 ${config.color}`} />
          
          {/* Pulsing animation for connecting state */}
          {status === 'connecting' && (
            <div className={`absolute inset-0 w-4 h-4 ${config.color} opacity-30 animate-ping`}>
              <Icon className="w-4 h-4" />
            </div>
          )}
        </div>
        
        <span className={`text-xs sm:text-sm font-medium ${config.color} hidden sm:inline`}>
          {config.text}
        </span>
      </div>

      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
        {config.description}
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
      </div>
    </div>
  );
};

export default ConnectionStatus; 