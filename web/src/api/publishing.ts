import apiClient from './client';

// Types
export interface PlatformInfo {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

export interface PublishRequest {
  platform: string;
  chapter_numbers?: number[];
}

export interface PublishResponse {
  success: boolean;
  platform: string;
  published_chapters: number[];
  message: string;
}

export interface CommentResponse {
  id: string;
  author: string;
  content: string;
  chapter: number;
  created_at: string;
}

export interface CommentListResponse {
  novel_id: string;
  platform: string;
  comments: CommentResponse[];
  total_count: number;
}

// API functions
export async function getPlatforms(): Promise<PlatformInfo[]> {
  const res = await apiClient.get<PlatformInfo[]>('/publishing/platforms');
  return res.data;
}

export async function publishNovel(
  novelId: string,
  request: PublishRequest
): Promise<PublishResponse> {
  const res = await apiClient.post<PublishResponse>(
    `/publishing/novels/${novelId}/publish`,
    request
  );
  return res.data;
}

export async function getComments(
  novelId: string,
  platform?: string
): Promise<CommentListResponse> {
  const params = platform ? { platform } : {};
  const res = await apiClient.get<CommentListResponse>(
    `/publishing/comments/${novelId}`,
    { params }
  );
  return res.data;
}