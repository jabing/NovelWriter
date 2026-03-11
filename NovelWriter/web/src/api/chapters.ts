import apiClient from './client';
import type { Chapter } from '../types';

export interface CreateChapterPayload {
  number: number;
  title: string;
  status: string;
}

export interface UpdateChapterPayload {
  content?: string;
  word_count?: number;
  status?: string;
  title?: string;
}

export async function getChapters(projectId: string): Promise<Chapter[]> {
  const res = await apiClient.get<Chapter[]>(`/novels/${projectId}/chapters`);
  return res.data;
}

export async function createChapter(
  projectId: string, 
  payload: CreateChapterPayload
): Promise<Chapter> {
  const res = await apiClient.post<Chapter>(`/novels/${projectId}/chapters`, payload);
  return res.data;
}

export async function updateChapter(
  chapterId: string, 
  payload: UpdateChapterPayload
): Promise<Chapter> {
  const res = await apiClient.put<Chapter>(`/chapters/${chapterId}`, payload);
  return res.data;
}

export async function deleteChapter(chapterId: string): Promise<void> {
  await apiClient.delete(`/chapters/${chapterId}`);
}

export async function getChapter(chapterId: string): Promise<Chapter> {
  const res = await apiClient.get<Chapter>(`/chapters/${chapterId}`);
  return res.data;
}
