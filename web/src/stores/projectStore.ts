import { defineStore } from 'pinia';
import { getProjects, createProject, updateProject, deleteProject } from '../api/projects';
import type { Project, CreateProjectPayload, UpdateProjectPayload } from '../types';

export const useProjectStore = defineStore('project', {
  state: (): {
    projects: Project[];
    currentProject: string | null;
    loading: boolean;
    error: string | null;
  } => ({
    projects: [],
    currentProject: null,
    loading: false,
    error: null
  }),
  actions: {
    async fetchProjects(): Promise<void> {
      this.loading = true;
      this.error = null;
      try {
        this.projects = await getProjects();
        if (!this.currentProject && this.projects.length > 0 && this.projects[0]) {
          this.currentProject = this.projects[0].id;
        }
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to fetch projects';
        console.error('Failed to fetch projects:', err);
      } finally {
        this.loading = false;
      }
    },
    async createProject(payload: CreateProjectPayload): Promise<Project | null> {
      this.loading = true;
      this.error = null;
      try {
        const newProject = await createProject(payload);
        this.projects.push(newProject);
        this.currentProject = newProject.id;
        return newProject;
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to create project';
        console.error('Failed to create project:', err);
        return null;
      } finally {
        this.loading = false;
      }
    },
    async updateProject(projectId: string, payload: UpdateProjectPayload): Promise<Project | null> {
      this.loading = true;
      this.error = null;
      try {
        const updatedProject = await updateProject(projectId, payload);
        const index = this.projects.findIndex(p => p.id === projectId);
        if (index !== -1) {
          this.projects[index] = updatedProject;
        }
        return updatedProject;
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to update project';
        console.error('Failed to update project:', err);
        return null;
      } finally {
        this.loading = false;
      }
    },
    async deleteProject(projectId: string): Promise<boolean> {
      this.loading = true;
      this.error = null;
      try {
        await deleteProject(projectId);
        this.projects = this.projects.filter(p => p.id !== projectId);
        if (this.currentProject === projectId) {
          this.currentProject = this.projects.length > 0 ? (this.projects[0]?.id ?? null) : null;
        }
        return true;
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to delete project';
        console.error('Failed to delete project:', err);
        return false;
      } finally {
        this.loading = false;
      }
    },
    switchProject(projectId: string): void {
      if (this.projects.find((p) => p.id === projectId)) {
        this.currentProject = projectId;
      }
    },
    clearError(): void {
      this.error = null;
    }
  },
  getters: {
    projectList(state): Project[] {
      return state.projects;
    },
    currentProjectId(state): string | null {
      return state.currentProject;
    },
    currentProjectData(state): Project | undefined {
      return state.projects.find((p) => p.id === state.currentProject);
    },
    isLoading(state): boolean {
      return state.loading;
    },
    hasError(state): boolean {
      return state.error !== null;
    }
  }
});
