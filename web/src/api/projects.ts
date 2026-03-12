import apiClient from './client';
import type { Project, CreateProjectPayload, UpdateProjectPayload } from '../types';

export async function getProjects(): Promise<Project[]> {
  const res = await apiClient.get<Project[]>('/projects');
  return res.data;
}

export async function getProject(id: string): Promise<Project> {
  const res = await apiClient.get<Project>(`/projects/${id}`);
  return res.data;
}

export async function createProject(payload: CreateProjectPayload): Promise<Project> {
  const res = await apiClient.post<Project>('/projects', payload);
  return res.data;
}

export async function updateProject(id: string, payload: UpdateProjectPayload): Promise<Project> {
  const res = await apiClient.put<Project>(`/projects/${id}`, payload);
  return res.data;
}

export async function deleteProject(id: string): Promise<void> {
  await apiClient.delete(`/projects/${id}`);
}
