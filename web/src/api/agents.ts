import apiClient from './client';
import type { Agent, AgentStatusEvent } from '../types';

export async function getAgents(): Promise<Agent[]> {
  const res = await apiClient.get<Agent[]>('/agents');
  return res.data;
}

 
export function createAgentStatusWebSocket(
  url: string,
  onMessage: (ev: AgentStatusEvent) => void,
  onOpen?: () => void,
  onError?: (ev: Event) => void
): WebSocket {
  const ws = new WebSocket(url);
  ws.onopen = () => onOpen?.();
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as AgentStatusEvent;
      onMessage(data);
      } catch (e) {
      }
  };
  ws.onerror = (ev) => {
    onError?.(ev);
  };
  return ws;
}
