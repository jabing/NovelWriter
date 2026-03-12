import apiClient from './client';

// Types based on backend schemas
export interface Character {
  name: string;
  aliases: string[];
  birth_chapter?: number;
  death_chapter?: number;
  current_status: string;
  tier: number;
  bio: string;
  persona: string;
  mbti: string;
  profession: string;
  relationships: Record<string, string>;
  interested_topics: string[];
}

export interface CharacterListResponse {
  project_id: string;
  characters: Character[];
  total_count: number;
  main_characters: number;
  supporting_characters: number;
}

export interface CreateCharacterPayload {
  name: string;
  aliases?: string[];
  tier?: number;
  bio?: string;
  persona?: string;
  mbti?: string;
  profession?: string;
  relationships?: Record<string, string>;
  interested_topics?: string[];
}

export interface UpdateCharacterPayload extends Partial<CreateCharacterPayload> {}

// API functions
export async function getCharacters(projectId: string): Promise<CharacterListResponse> {
  const res = await apiClient.get<CharacterListResponse>(`/novels/${projectId}/characters`);
  return res.data;
}

export async function getCharacter(projectId: string, name: string): Promise<Character> {
  const res = await apiClient.get<Character>(`/novels/${projectId}/characters/${name}`);
  return res.data;
}

export async function createCharacter(
  projectId: string,
  payload: CreateCharacterPayload
): Promise<Character> {
  const res = await apiClient.post<Character>(`/novels/${projectId}/characters`, payload);
  return res.data;
}

export async function updateCharacter(
  projectId: string,
  characterName: string,
  payload: UpdateCharacterPayload
): Promise<Character> {
  const res = await apiClient.put<Character>(`/novels/${projectId}/characters/${characterName}`, payload);
  return res.data;
}