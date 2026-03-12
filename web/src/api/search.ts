import apiClient from './client';

export interface SearchResultItem {
  id: string;
  title: string;
  type: 'project' | 'chapter' | 'character';
  url: string;
  match_reason?: string[];
  // Project-specific
  genre?: string;
  status?: string;
  progress?: string;
  // Chapter-specific
  novel_id?: string;
  novel_title?: string;
  chapter_number?: number;
  preview?: string;
  // Character-specific
  name?: string;
  tier?: number;
  profession?: string;
  bio_preview?: string;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  projects: SearchResultItem[];
  chapters: SearchResultItem[];
  characters: SearchResultItem[];
}

export interface SearchParams {
  q: string;
  type?: 'project' | 'chapter' | 'character' | 'all';
  novel_id?: string;
}

export async function search(params: SearchParams): Promise<SearchResponse> {
  const queryParams = new URLSearchParams();
  queryParams.set('q', params.q);
  
  if (params.type) {
    queryParams.set('type', params.type);
  }
  
  if (params.novel_id) {
    queryParams.set('novel_id', params.novel_id);
  }
  
  const res = await apiClient.get<SearchResponse>(`/search?${queryParams.toString()}`);
  return res.data;
}
