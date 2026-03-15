import apiClient from './client';

/**
 * Graph node representing a character or entity
 */
export interface GraphNode {
  data: {
    id: string;
    label: string;
    type: 'character' | 'location' | 'item' | 'faction';
    properties: {
      tier?: number;
      mbti?: string;
      profession?: string;
      bio?: string;
      avatar_url?: string;
      [key: string]: any;
    };
  };
}

/**
 * Graph edge representing a relationship between nodes
 */
export interface GraphEdge {
  data: {
    source: string;
    target: string;
    relationship: RelationshipType;
    properties: {
      description?: string;
      strength?: number;
      [key: string]: any;
    };
  };
}

/**
 * Relationship types for character connections
 */
export type RelationshipType =
  | 'FAMILY'
  | 'FRIEND'
  | 'ENEMY'
  | 'ALLY'
  | 'ROMANTIC'
  | 'MENTOR'
  | 'STUDENT'
  | 'RIVAL'
  | 'BUSINESS';

/**
 * Graph response from the API
 */
export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/**
 * Relationship type metadata for legend display
 */
export interface RelationshipTypeInfo {
  type: RelationshipType;
  color: string;
  label: string;
  description: string;
}

/**
 * All relationship types with their display properties
 */
export const RELATIONSHIP_TYPES: RelationshipTypeInfo[] = [
  { type: 'FAMILY', color: '#FF6B6B', label: 'Family', description: 'Family members' },
  { type: 'FRIEND', color: '#4ECDC4', label: 'Friend', description: 'Friends' },
  { type: 'ENEMY', color: '#E74C3C', label: 'Enemy', description: 'Enemies' },
  { type: 'ALLY', color: '#27AE60', label: 'Ally', description: 'Allies' },
  { type: 'ROMANTIC', color: '#E91E63', label: 'Romantic', description: 'Romantic partners' },
  { type: 'MENTOR', color: '#9B59B6', label: 'Mentor', description: 'Mentor relationship' },
  { type: 'STUDENT', color: '#3498DB', label: 'Student', description: 'Student relationship' },
  { type: 'RIVAL', color: '#F39C12', label: 'Rival', description: 'Rivals' },
  { type: 'BUSINESS', color: '#95A5A6', label: 'Business', description: 'Business partners' },
];

/**
 * Get color for a relationship type
 */
export function getRelationshipColor(type: RelationshipType): string {
  const rel = RELATIONSHIP_TYPES.find(r => r.type === type);
  return rel?.color || '#999999';
}

/**
 * Get label for a relationship type
 */
export function getRelationshipLabel(type: RelationshipType): string {
  const rel = RELATIONSHIP_TYPES.find(r => r.type === type);
  return rel?.label || type;
}

/**
 * Fetch character graph data for a project
 * @param projectId - The project ID
 * @returns Promise with graph nodes and edges
 */
export async function getCharacterGraph(projectId: string): Promise<GraphResponse> {
  const res = await apiClient.get<GraphResponse>(`/projects/${projectId}/graph/characters`);
  return res.data;
}
