import apiClient from './client';

export interface HealthStatus {
  status: 'healthy' | 'warning' | 'unhealthy' | 'unknown';
  uptime?: number;
  version?: string;
}

export interface Metrics {
  cpu_usage?: number;
  memory_usage?: number;
  active_projects?: number;
  total_chapters?: number;
  api_requests?: number;
}

export interface Alert {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  created_at: string;
  acknowledged: boolean;
}

export async function getHealth(): Promise<HealthStatus> {
  const res = await apiClient.get<HealthStatus>('/monitoring/health');
  return res.data;
}

export async function getMetrics(): Promise<Metrics> {
  const res = await apiClient.get<Metrics>('/monitoring/metrics');
  return res.data;
}

export async function getAlerts(): Promise<Alert[]> {
  const res = await apiClient.get<Alert[]>('/monitoring/alerts');
  return res.data;
}

export async function acknowledgeAlert(alertId: string): Promise<void> {
  await apiClient.post(`/monitoring/alerts/${alertId}/acknowledge`);
}
