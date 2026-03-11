import apiClient from './client';
import type { Project, CreateProjectPayload } from '../types';

export async function getProjects(): Promise<Project[]> {
  const res = await apiClient.get<Project[]>('/projects');
  return res.data;
}

export async function createProject(payload: CreateProjectPayload): Promise<Project> {
  const res = await apiClient.post<Project>('/projects', payload);
  return res.data;
}
