export interface CreateProjectPayload {
  title: string;
  genre?: string;
  language?: string;
  premise?: string;
  themes?: string[];
  pov?: string;
  tone?: string;
  target_audience?: string;
  story_structure?: string;
  content_rating?: string;
  target_chapters?: number;
  target_words?: number;
  platforms?: string[];
}

export interface UpdateProjectPayload {
  title?: string;
  genre?: string;
  language?: string;
  premise?: string;
  themes?: string[];
  pov?: string;
  tone?: string;
  target_audience?: string;
  story_structure?: string;
  content_rating?: string;
  target_chapters?: number;
  target_words?: number;
  platforms?: string[];
  status?: string;
}

export interface Project {
  id: string;
  title: string;
  genre: string;
  language: string;
  status: string;
  premise: string;
  themes: string[];
  pov: string;
  tone: string;
  target_audience: string;
  story_structure: string;
  content_rating: string;
  sensitive_handling?: string;
  target_chapters: number;
  completed_chapters: number;
  total_words: number;
  target_words: number;
  progress_percent: number;
  created_at: string;
  updated_at: string;
  platforms: string[];
  published_chapters?: number;
  total_reads?: number;
  total_votes?: number;
  total_comments?: number;
  followers?: number;
}

export interface Agent {
  id: string;
  name: string;
  status: string;
  last_seen?: string;
}

export interface AgentStatusEvent {
  type: string;
  agent_id: string;
  status: string;
}

export type ChapterStatus = 'draft' | 'in_progress' | 'completed' | 'published';

export interface Chapter {
  id: string;
  project_id: string;
  number: number;
  title: string;
  status: ChapterStatus;
  word_count: number;
  content?: string;
  created_at: string;
  updated_at: string;
}

export interface CharacterRelationship {
  character_id: string;
  type: string;
}

export interface Platform {
  id: string;
  name: string;
  type: string;
  connected: boolean;
  last_sync?: string;
}

export interface Character {
  id: string;
  project_id: string;
  name: string;
  role: 'protagonist' | 'antagonist' | 'supporting' | 'minor';
  description: string;
  avatar_url?: string;
  status: 'active' | 'minor' | 'archived';
  relationships?: CharacterRelationship[];
}
