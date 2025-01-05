import { useState, useEffect } from 'react';
import WebSocketService from '../../../services/websocket';

export function useSocketConnection() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [detections, setDetections] = useState([]);

  useEffect(() => {
    WebSocketService.setStateHandlers({
      onConnect: () => {
        console.log('Template training WebSocket connected');
      },
      onDisconnect: () => {
        console.log('Template training WebSocket disconnected');
      },
      onDetectionResult: (data) => {
        // Ensure we're getting the detections array
        if (data && data.detections) {
          setDetections(data.detections);
        } else {
          console.error('Invalid detection result format:', data);
          setDetections([]);
        }
        setIsAnalyzing(false);
      },
      onError: (error) => {
        console.error('WebSocket error:', error);
        setIsAnalyzing(false);
      }
    });

    // Ensure WebSocket connection
    if (!WebSocketService.socket?.connected) {
      WebSocketService.connect();
    }

    // Cleanup
    return () => {
      WebSocketService.setStateHandlers(null);
    };
  }, []);

  return {
    isAnalyzing,
    setIsAnalyzing,
    detections,
    setDetections
  };
} 