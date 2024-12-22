import React, { createContext, useContext, useReducer, useEffect } from "react";
import WebSocketService from "../services/websocket";
import { AgentStatus, ActionTypes } from "../constants";

const AppContext = createContext();

// Initial state
const initialState = {
  connection: {
    connected: false,
    reconnecting: false,
    error: null,
  },
  agent: {
    autoMode: false,
    highlightMode: false,
    // playing: false,
    status: AgentStatus.STOPPED,
    currentTask: null,
    pendingTools: 0,
  },
  chat: {
    messages: [],
    error: null,
    currentInput: "",
  },

  compassWindow: {
    actionType: null,
  }
};

// Reducer
function appReducer(state, action) {
  console.log("AppReducer - Action:", action.type, "Payload:", action.payload);

  switch (action.type) {
    case ActionTypes.SET_CONNECTION_STATUS:
      return {
        ...state,
        connection: { ...state.connection, ...action.payload },
      };

    case ActionTypes.SET_AGENT_STATE:
      return {
        ...state,
        agent: {
          ...state.agent,
          ...action.payload,
          pendingTools: action.payload.pendingTools ?? state.agent.pendingTools,
        },
      };

    case ActionTypes.SET_CHAT_INPUT:
      return {
        ...state,
        chat: { ...state.chat, currentInput: action.payload },
      };

    case ActionTypes.ADD_CHAT_MESSAGE:
      return {
        ...state,
        chat: {
          ...state.chat,
          messages: [
            ...state.chat.messages,
            {
              ...action.payload,
              timestamp: action.payload.timestamp || new Date().toISOString(),
            },
          ],
        },
      };

    case ActionTypes.SET_ERROR:
      return {
        ...state,
        chat: { ...state.chat, error: action.payload },
      };

    case ActionTypes.START_PROCESSING:
      return {
        ...state,
        agent: {
          ...state.agent,
          status: AgentStatus.RUNNING,
          // playing: true,
        },
      };

    case ActionTypes.STOP_PROCESSING:
      return {
        ...state,
        agent: {
          ...state.agent,
          status: AgentStatus.STOPPING,
        },
      };

    case ActionTypes.UPDATE_PENDING_TOOLS:
      return {
        ...state,
        agent: {
          ...state.agent,
          pendingTools: action.payload,
        },
      };

    case ActionTypes.SET_COMPASS_WINDOW_STATE:
      return {
        ...state,
        compassWindow: {
          actionType: action.payload,
        },
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
      onConnect: () =>
        dispatch({
          type: ActionTypes.SET_CONNECTION_STATUS,
          payload: { connected: true, error: null },
        }),

      onDisconnect: () =>
        dispatch({
          type: ActionTypes.SET_CONNECTION_STATUS,
          payload: { connected: false },
        }),

      onResponse: (data) => {
        dispatch({
          type: ActionTypes.ADD_CHAT_MESSAGE,
          payload: {
            ...data,
            timestamp: new Date().toISOString(),
          },
        });
      },

      onStateUpdate: (data) => {
        console.log("Received state update:", data);
        dispatch({
          type: ActionTypes.SET_AGENT_STATE,
          payload: data,
        });
      },

      onCompassWindowState: (actionString) => {
        console.log("Received Compass window state:", actionString);
        dispatch({
          type: ActionTypes.SET_COMPASS_WINDOW_STATE,
          payload: actionString,
        });
      },

      onError: (error) =>
        dispatch({
          type: ActionTypes.SET_ERROR,
          payload: error.message,
        }),
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
    throw new Error("useAppState must be used within an AppProvider");
  }
  return context;
}
