import apiClient from './client';

export interface GenerateContentPayload {
  project_id: string;
  chapter_id: string;
  genre: string;
  style: string;
  word_count: number;
  plot_points: string[];
}

export interface GenerateContentResponse {
  content: string;
  word_count: number;
  estimated_tokens: number;
}

export interface WriterExecutePayload {
  project_id: string;
  chapter_id: string;
  prompt?: string;
  context?: {
    genre?: string;
    style?: string;
    word_count?: number;
    plot_points?: string[];
    previous_chapters?: string[];
  };
}

export interface WriterExecuteResponse {
  success: boolean;
  result?: {
    content: string;
    word_count: number;
  };
  error?: string;
}

/**
 * Generate chapter content using AI writer
 */
export async function generateChapterContent(
  payload: GenerateContentPayload
): Promise<GenerateContentResponse> {
  const res = await apiClient.post<GenerateContentResponse>(
    '/agents/writer/generate',
    payload
  );
  return res.data;
}

/**
 * Execute writer agent with custom parameters
 */
export async function executeWriterAgent(
  payload: WriterExecutePayload
): Promise<WriterExecuteResponse> {
  const res = await apiClient.post<WriterExecuteResponse>(
    '/agents/writer/execute',
    payload
  );
  return res.data;
}

/**
 * Get writer agent status
 */
export async function getWriterStatus(): Promise<{
  status: string;
  last_activity?: string;
  queue_length?: number;
}> {
  const res = await apiClient.get('/agents/writer/status');
  return res.data;
}
