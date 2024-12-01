import React, { createContext, useContext, useReducer, useEffect } from 'react';
import WebSocketService from '../services/websocket';

const AppContext = createContext();

// States
export const AgentStatus = {
  IDLE: 'IDLE',
  RUNNING: 'RUNNING',
  STOPPING: 'STOPPING',
};

// Initial state
const initialState = {
  connection: {
    connected: false,
    reconnecting: false,
    error: null
  },
  agent: {
    autoMode: false,
    highlightMode: false,
    playing: false,
    status: AgentStatus.IDLE,
    currentTask: null
  },
  chat: {
    messages: [],
    error: null,
    currentInput: ''
  }
};

// Action types
const ActionTypes = {
  SET_CONNECTION_STATUS: 'SET_CONNECTION_STATUS',
  SET_AGENT_STATE: 'SET_AGENT_STATE',
  SET_CHAT_INPUT: 'SET_CHAT_INPUT',
  ADD_CHAT_MESSAGE: 'ADD_CHAT_MESSAGE',
  SET_ERROR: 'SET_ERROR',
  START_PROCESSING: 'START_PROCESSING',
  STOP_PROCESSING: 'STOP_PROCESSING',
};

// Reducer
function appReducer(state, action) {
  console.log('AppReducer - Action:', action.type, 'Payload:', action.payload);
  console.log('AppReducer - Current State:', state.agent);

  if (action.type === ActionTypes.ADD_CHAT_MESSAGE) {
    console.log('Adding chat message:', action.payload);
    console.log('Current messages:', state.chat.messages);
  }

  console.log('AppReducer - Received action:', action.type, 'with payload:', action.payload);

  switch (action.type) {
    case ActionTypes.SET_CONNECTION_STATUS:
      return {
        ...state,
        connection: { ...state.connection, ...action.payload }
      };
    
    case ActionTypes.SET_AGENT_STATE:
      // Backend state should take precedence
      const newState = {
        ...state,
        agent: { ...state.agent, ...action.payload }
      };
      console.log('AppReducer - New State after SET_AGENT_STATE:', newState.agent);
      return newState;
    
    case ActionTypes.SET_CHAT_INPUT:
      return {
        ...state,
        chat: { ...state.chat, currentInput: action.payload }
      };
    
    case ActionTypes.ADD_CHAT_MESSAGE:
      console.log('AppReducer - Before adding message:', state.chat.messages);
      const newMessages = [...state.chat.messages, action.payload];
      console.log('AppReducer - After adding message:', newMessages);
      return {
        ...state,
        chat: {
          ...state.chat,
          messages: newMessages
        }
      };
    
    case ActionTypes.SET_ERROR:
      return {
        ...state,
        chat: { ...state.chat, error: action.payload }
      };
    
    case ActionTypes.START_PROCESSING:
      console.log('AppReducer - Starting Processing');
      return {
        ...state,
        agent: {
          ...state.agent,
          processing: true,
          playing: true
        }
      };
    
    case ActionTypes.STOP_PROCESSING:
      console.log('AppReducer - Stopping Processing');
      return {
        ...state,
        agent: {
          ...state.agent,
          processing: false,
          playing: false
        }
      };
    
    default:
      return state;
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Setup WebSocket handlers
  useEffect(() => {
    WebSocketService.setStateHandlers({
      onConnect: () => dispatch({ 
        type: ActionTypes.SET_CONNECTION_STATUS, 
        payload: { connected: true, error: null } 
      }),
      
      onDisconnect: () => dispatch({ 
        type: ActionTypes.SET_CONNECTION_STATUS, 
        payload: { connected: false } 
      }),
      
      onResponse: (data) => {
        dispatch({ 
          type: ActionTypes.ADD_CHAT_MESSAGE, 
          payload: {
            ...data,
            timestamp: new Date().toISOString()
          } 
        });
      },
      
      onStateUpdate: (data) => dispatch({ 
        type: ActionTypes.SET_AGENT_STATE, 
        payload: data 
      }),
      
      onError: (error) => dispatch({ 
        type: ActionTypes.SET_ERROR, 
        payload: error.message 
      })
    });

    WebSocketService.connect();
    
    return () => WebSocketService.disconnect();
  }, []);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hooks
export function useAppState() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppState must be used within an AppProvider');
  }
  return context;
}
