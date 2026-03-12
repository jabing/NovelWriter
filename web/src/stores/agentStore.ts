import { defineStore } from 'pinia';
import type { Agent, AgentStatusEvent } from '../types';

// WebSocket connection states
type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

// WebSocket message type for incoming data
interface WebSocketMessage {
  type: 'agent_status' | 'agent_list' | 'ping';
  data?: AgentStatusEvent | Agent[];
}

// Store state type
interface AgentState {
  agents: Agent[];
  activeTask: string | null;
  connectionState: ConnectionState;
  lastError: string | null;
}

// Exponential backoff configuration
const RECONNECT_CONFIG = {
  initialDelay: 1000,  // 1 second
  maxDelay: 30000,     // 30 seconds
  multiplier: 1.5
};

export const useAgentStore = defineStore('agent', {
  state: (): AgentState => ({
    agents: [],
    activeTask: null,
    connectionState: 'disconnected',
    lastError: null
  }),

  actions: {
    // Private properties for WebSocket management
    _ws: null as WebSocket | null,
    _reconnectTimer: null as ReturnType<typeof setTimeout> | null,
    _reconnectDelay: RECONNECT_CONFIG.initialDelay,

    /**
     * Connect to the WebSocket endpoint for real-time agent updates
     */
    connect(): void {
      if (this._ws && this._ws.readyState !== WebSocket.CLOSED) {
        return; // Already connected or connecting
      }

      this.connectionState = 'connecting';
      this.lastError = null;

      const wsUrl = this._getWebSocketUrl();
      
      try {
        this._ws = new WebSocket(wsUrl);
        this._setupWebSocketHandlers();
      } catch (error) {
        this.lastError = `Failed to create WebSocket: ${error}`;
        this.connectionState = 'disconnected';
        this._scheduleReconnect();
      }
    },

    /**
     * Disconnect from WebSocket and cleanup
     */
    disconnect(): void {
      this._clearReconnectTimer();
      
      if (this._ws) {
        this._ws.onopen = null;
        this._ws.onmessage = null;
        this._ws.onerror = null;
        this._ws.onclose = null;
        
        if (this._ws.readyState === WebSocket.OPEN) {
          this._ws.close(1000, 'Store disposed');
        }
        this._ws = null;
      }
      
      this.connectionState = 'disconnected';
    },

    /**
     * Fetch agents (legacy - initializes via WebSocket agent_list message)
     */
    async fetchAgents(): Promise<void> {
      // If not connected, connect first - the agent list will come via WebSocket
      if (!this._ws || this._ws.readyState !== WebSocket.OPEN) {
        this.connect();
      }
    },

    /**
     * Subscribe to agent status updates (connects if not connected)
     */
    subscribeToStatus(): void {
      if (this.connectionState === 'disconnected') {
        this.connect();
      }
    },

    // Private methods

    _getWebSocketUrl(): string {
      // Use Vite proxy path - the /ws prefix is proxied to ws://localhost:8000/ws
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${protocol}//${window.location.host}/ws/agents`;
    },

    _setupWebSocketHandlers(): void {
      if (!this._ws) return;

      this._ws.onopen = () => {
        this.connectionState = 'connected';
        this._reconnectDelay = RECONNECT_CONFIG.initialDelay; // Reset delay on successful connection
        this.lastError = null;
      };

      this._ws.onmessage = (event: MessageEvent) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this._handleMessage(message);
        } catch (error) {
          console.warn('Failed to parse WebSocket message:', error);
        }
      };

      this._ws.onerror = (event: Event) => {
        this.lastError = 'WebSocket connection error';
        console.error('WebSocket error:', event);
      };

      this._ws.onclose = (event: CloseEvent) => {
        this.connectionState = 'disconnected';
        
        // Only attempt reconnect if not a normal closure
        if (event.code !== 1000) {
          this._scheduleReconnect();
        }
      };
    },

    _handleMessage(message: WebSocketMessage): void {
      switch (message.type) {
        case 'agent_list':
          // Initial or full agent list
          if (Array.isArray(message.data)) {
            this.agents = message.data as Agent[];
          }
          break;

        case 'agent_status':
          // Single agent status update
          if (message.data && 'agent_id' in message.data) {
            this._updateAgentStatus(message.data as AgentStatusEvent);
          }
          break;

        case 'ping':
          // Respond to ping with pong (if needed)
          if (this._ws?.readyState === WebSocket.OPEN) {
            this._ws.send(JSON.stringify({ type: 'pong' }));
          }
          break;

        default:
          console.warn('Unknown WebSocket message type:', message.type);
      }
    },

    _updateAgentStatus(event: AgentStatusEvent): void {
      const index = this.agents.findIndex(a => a.id === event.agent_id);
      
      if (index !== -1) {
        // Update existing agent
        this.agents[index] = {
          ...this.agents[index],
          status: event.status,
          last_seen: new Date().toISOString()
        };
      } else {
        // Add new agent if not found
        this.agents.push({
          id: event.agent_id,
          name: `Agent ${event.agent_id}`,
          status: event.status,
          last_seen: new Date().toISOString()
        });
      }
    },

    _scheduleReconnect(): void {
      this._clearReconnectTimer();
      
      if (this.connectionState !== 'reconnecting') {
        this.connectionState = 'reconnecting';
      }

      this._reconnectTimer = setTimeout(() => {
        this.connect();
        // Increase delay for next attempt
        this._reconnectDelay = Math.min(
          this._reconnectDelay * RECONNECT_CONFIG.multiplier,
          RECONNECT_CONFIG.maxDelay
        );
      }, this._reconnectDelay);
    },

    _clearReconnectTimer(): void {
      if (this._reconnectTimer) {
        clearTimeout(this._reconnectTimer);
        this._reconnectTimer = null;
      }
    }
  },

  getters: {
    activeAgents(state): Agent[] {
      return state.agents.filter(a => a.status === 'online' || a.status === 'busy');
    },

    isConnecting(state): boolean {
      return state.connectionState === 'connecting' || state.connectionState === 'reconnecting';
    },

    isConnected(state): boolean {
      return state.connectionState === 'connected';
    }
  }
});
