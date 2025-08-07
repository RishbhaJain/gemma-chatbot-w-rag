import React, { useState, useRef, useEffect } from 'react';
import { MicrophoneIcon, StopIcon } from '@heroicons/react/24/solid';

const VoiceRecorder = ({ onRecordingComplete, disabled, currentLanguage }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [hasPermission, setHasPermission] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const intervalRef = useRef(null);

  // Request microphone permission on mount
  useEffect(() => {
    requestMicrophonePermission();
    return () => {
      // Cleanup on unmount
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const requestMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setHasPermission(true);
      // Stop the stream immediately as we only needed to check permission
      stream.getTracks().forEach(track => track.stop());
    } catch (error) {
      console.error('Microphone permission denied:', error);
      setHasPermission(false);
    }
  };

  const startRecording = async () => {
    if (!hasPermission || disabled) return;

    try {
      // Get audio stream with optimal settings for Whisper
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,  // Whisper prefers 16kHz
          channelCount: 1,    // Mono audio
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      // Set up audio context for visualization
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      analyserRef.current.fftSize = 256;
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      // Start audio level monitoring
      const updateAudioLevel = () => {
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
        setAudioLevel(average / 255 * 100); // Convert to percentage
        animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
      };
      updateAudioLevel();

      // Set up MediaRecorder
      const mimeType = getSupportedMimeType();
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: mimeType,
        audioBitsPerSecond: 16000 // Low bitrate for efficiency
      });

      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        onRecordingComplete(audioBlob);
        
        // Cleanup
        stream.getTracks().forEach(track => track.stop());
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
        
        setAudioLevel(0);
        setRecordingTime(0);
      };

      // Start recording
      mediaRecorderRef.current.start();
      setIsRecording(true);

      // Start timer
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const getSupportedMimeType = () => {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/wav'
    ];
    
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    return 'audio/webm'; // fallback
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getRecordingText = () => {
    switch (currentLanguage) {
      case 'hi':
        return isRecording ? 'रिकॉर्डिंग रोकें' : 'रिकॉर्डिंग शुरू करें';
      case 'en':
        return isRecording ? 'Stop Recording' : 'Start Recording';
      case 'hinglish':
        return isRecording ? 'Stop Recording' : 'Start Recording';
      default:
        return isRecording ? 'Stop Recording' : 'Start Recording';
    }
  };

  const getPermissionText = () => {
    switch (currentLanguage) {
      case 'hi':
        return 'माइक्रोफ़ोन की अनुमति चाहिए';
      case 'en':
        return 'Microphone permission needed';
      case 'hinglish':
        return 'Microphone permission needed';
      default:
        return 'Microphone permission needed';
    }
  };

  if (hasPermission === false) {
    return (
      <div className="flex flex-col items-center space-y-2">
        <button
          onClick={requestMicrophonePermission}
          className="p-3 bg-gray-100 text-gray-500 rounded-full hover:bg-gray-200 transition-colors"
          disabled={disabled}
        >
          <MicrophoneIcon className="w-6 h-6" />
        </button>
        <span className="text-xs text-gray-500 text-center">{getPermissionText()}</span>
      </div>
    );
  }

  if (hasPermission === null) {
    return (
      <div className="flex flex-col items-center space-y-2">
        <div className="p-3 bg-gray-100 rounded-full">
          <div className="w-6 h-6 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <span className="text-xs text-gray-500">Checking...</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center space-y-2">
      {/* Recording Button */}
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled}
        className={`relative p-2.5 sm:p-3 rounded-full transition-all duration-200 min-h-[44px] min-w-[44px] ${
          isRecording
            ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg'
            : 'bg-blue-500 hover:bg-blue-600 text-white shadow-md hover:shadow-lg'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        title={getRecordingText()}
      >
        {isRecording ? (
          <StopIcon className="w-6 h-6" />
        ) : (
          <MicrophoneIcon className="w-6 h-6" />
        )}
        
        {/* Audio level indicator */}
        {isRecording && (
          <div className="absolute inset-0 rounded-full border-4 border-white opacity-30 animate-ping"></div>
        )}
      </button>

      {/* Recording Status */}
      {isRecording && (
        <div className="flex flex-col items-center space-y-1">
          {/* Timer */}
          <div className="text-sm font-mono text-red-600 font-medium">
            {formatTime(recordingTime)}
          </div>
          
          {/* Audio Level Visualizer */}
          <div className="flex items-center space-x-1">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className={`w-1 bg-red-500 rounded-full transition-all duration-100 ${
                  audioLevel > (i + 1) * 20 ? 'h-4' : 'h-1'
                }`}
              />
            ))}
          </div>
          
          {/* Recording indicator text */}
          <div className="text-xs text-red-600 animate-pulse">
            {currentLanguage === 'hi' ? 'रिकॉर्डिंग चल रही है...' :
             currentLanguage === 'en' ? 'Recording...' :
             'Recording chal rahi hai...'}
          </div>
        </div>
      )}

      {/* Help text when not recording */}
      {!isRecording && (
        <span className="text-xs text-gray-500 text-center max-w-20">
          {getRecordingText()}
        </span>
      )}
    </div>
  );
};

export default VoiceRecorder; 