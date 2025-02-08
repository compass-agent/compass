import { useState, useEffect } from 'react';
import WebSocketService from '../../common/services/websocket';

export function useSocketConnection() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [detections, setDetections] = useState([]);

  useEffect(() => {
    console.log('🔌 useSocketConnection hook mounted');
    const prevHandlers = { ...WebSocketService.stateHandlers };
    console.log('📝 Previous socket handlers:', Object.keys(prevHandlers));

    WebSocketService.setStateHandlers({
      ...prevHandlers,
      onConnect: () => {
        console.log('🌟 Template training WebSocket connected');
      },
      onDisconnect: () => {
        console.log('💤 Template training WebSocket disconnected');
      },
      onDetectionResult: (data) => {
        console.log('🎯 Detection result received:', data);
        if (data && data.detections) {
          setDetections(data.detections);
        } else {
          console.error('❌ Invalid detection result format:', data);
          setDetections([]);
        }
        setIsAnalyzing(false);
      },
      onError: (error) => {
        console.error('⚠️ WebSocket error:', error);
        setIsAnalyzing(false);
        setDetections([]);
      }
    });

    if (!WebSocketService.socket?.connected) {
      console.log('🔄 Initiating WebSocket connection');
      WebSocketService.connect();
    }

    return () => {
      console.log('🧹 Cleaning up useSocketConnection hook');
      console.log('🔄 Restoring previous handlers:', Object.keys(prevHandlers));
      WebSocketService.setStateHandlers(prevHandlers);
    };
  }, []);

  return {
    isAnalyzing,
    setIsAnalyzing,
    detections,
    setDetections
  };
} 