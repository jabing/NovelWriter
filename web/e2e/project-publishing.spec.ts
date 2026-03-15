import { test, expect } from '@playwright/test';
import type { Project, CreateProjectPayload, UpdateProjectPayload } from '../src/types';

// Page Object Model for Project CRUD operations
class ProjectPage {
  constructor(private page: any) {}

  async gotoProjects() {
    await this.page.goto('/projects');
    await this.page.waitForLoadState('networkidle');
  }

  async gotoProjectDetail(projectId: string) {
    await this.page.goto(`/projects/${projectId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async gotoCreateProject() {
    await this.page.goto('/projects/new');
    await this.page.waitForLoadState('networkidle');
  }

  async clickCreateButton() {
    await this.page.locator('.create-btn').click();
    await this.page.waitForURL(/\/projects\/new/);
  }

  async fillProjectForm(data: Partial<CreateProjectPayload>) {
    if (data.title) {
      await this.page.fill('input[name="title"]', data.title);
    }
    if (data.genre) {
      await this.page.selectOption('select[name="genre"]', data.genre);
    }
    if (data.language) {
      await this.page.selectOption('select[name="language"]', data.language);
    }
    if (data.premise) {
      await this.page.fill('textarea[name="premise"]', data.premise);
    }
    if (data.pov) {
      await this.page.selectOption('select[name="pov"]', data.pov);
    }
    if (data.tone) {
      await this.page.selectOption('select[name="tone"]', data.tone);
    }
    if (data.target_audience) {
      await this.page.selectOption('select[name="target_audience"]', data.target_audience);
    }
    if (data.target_chapters) {
      await this.page.fill('input[name="target_chapters"]', String(data.target_chapters));
    }
    if (data.target_words) {
      await this.page.fill('input[name="target_words"]', String(data.target_words));
    }
  }

  async submitForm() {
    await this.page.locator('button[type="submit"]').click();
    await this.page.waitForLoadState('networkidle');
  }

  async cancelForm() {
    await this.page.locator('.cancel-btn').click();
    await this.page.waitForURL(/\/projects/);
  }

  async getProjectCardCount() {
    return await this.page.locator('.project-card').count();
  }

  async getProjectCard(title: string) {
    return this.page.locator('.project-card').filter({ hasText: title });
  }

  async clickProjectCard(title: string) {
    const card = await this.getProjectCard(title);
    await card.click();
  }

  async clickEditButton() {
    await this.page.locator('.edit-btn').click();
  }

  async clickDeleteButton() {
    await this.page.locator('.delete-btn').click();
  }

  async confirmDelete() {
    await this.page.locator('.confirm-delete-btn').click();
    await this.page.waitForLoadState('networkidle');
  }

  async cancelDelete() {
    await this.page.locator('.cancel-delete-btn').click();
  }

  async projectExists(title: string) {
    const count = await this.page.locator('.project-card').filter({ hasText: title }).count();
    return count > 0;
  }

  async getProjectTitle() {
    return await this.page.locator('.project-title').textContent();
  }

  async getProjectGenre() {
    return await this.page.locator('.project-genre').textContent();
  }

  async getProjectPremise() {
    return await this.page.locator('.project-premise').textContent();
  }

  async hasErrorMessage() {
    return await this.page.locator('.error-message').count() > 0;
  }

  async getErrorMessages() {
    const errors = await this.page.locator('.error-message').allTextContents();
    return errors;
  }

  async hasSuccessMessage() {
    return await this.page.locator('.success-message').count() > 0;
  }

  async getSuccessMessage() {
    return await this.page.locator('.success-message').textContent();
  }

  async isEditMode() {
    return await this.page.locator('form input[name="title"]').count() > 0;
  }

  async takeScreenshot(name: string) {
    await this.page.screenshot({ path: `test-results/screenshots/${name}.png`, fullPage: true });
  }
}

// Mock data for testing
const mockProjects: Project[] = [
  {
    id: '1',
    title: 'The Chronicles of Eldermere',
    genre: 'Fantasy',
    language: 'English',
    status: 'in_progress',
    premise: 'A young girl discovers a magical compass that leads her between worlds.',
    themes: ['Magic', 'Adventure'],
    pov: 'First Person',
    tone: 'Wonder',
    target_audience: 'Young Adult',
    story_structure: 'Three-Act',
    content_rating: 'PG',
    target_chapters: 50,
    completed_chapters: 12,
    total_words: 45000,
    target_words: 150000,
    progress_percent: 30,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-03-15T00:00:00Z',
    platforms: []
  }
];

const newProjectData: CreateProjectPayload = {
  title: 'Galactic Chronicles',
  genre: 'Science Fiction',
  language: 'English',
  premise: 'A space odyssey through uncharted galaxies',
  themes: ['Space', 'Adventure', 'Discovery'],
  pov: 'Third Person Limited',
  tone: 'Epic',
  target_audience: 'Adult',
  story_structure: 'Hero\'s Journey',
  content_rating: 'PG-13',
  target_chapters: 30,
  target_words: 90000
};

const updatedProjectData: UpdateProjectPayload = {
  title: 'Galactic Chronicles: Remastered',
  genre: 'Science Fiction',
  premise: 'A space odyssey through uncharted galaxies - expanded edition',
  target_chapters: 40,
  target_words: 120000
};

test.describe('Project Publishing Flow E2E Tests', () => {
  let projectPage: ProjectPage;

  test.beforeEach(async ({ page }) => {
    projectPage = new ProjectPage(page);

    await page.route('**/api/projects', async (route) => {
      const url = new URL(route.request().url());
      const method = route.request().method();

      if (method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockProjects)
        });
      } else if (method === 'PUT') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            ...newProjectData,
            id: '2',
            status: 'draft',
            completed_chapters: 0,
            total_words: 0,
            progress_percent: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            platforms: []
          })
        });
      }
    });

    await page.route('**/api/projects/*', async (route) => {
      const url = new URL(route.request().url());
      const method = route.request().method();
      const projectId = url.pathname.split('/').pop();

      if (method === 'GET') {
        const project = mockProjects.find(p => p.id === projectId);
        if (project) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(project)
          });
        } else {
          await route.fulfill({
            status: 404,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Project not found' })
          });
        }
      } else if (method === 'PUT') {
        // Update project
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockProjects[0],
            ...updatedProjectData,
            updated_at: new Date().toISOString()
          })
        });
      } else if (method === 'DELETE') {
        await route.fulfill({
          status: 204,
          contentType: 'application/json',
          body: ''
        });
      }
    });
  });

  test.describe('Create Project', () => {
    test('should create a new project with valid data', async ({ page }) => {
      try {
        await projectPage.gotoProjects();

        const initialCount = await projectPage.getProjectCardCount();
        expect(initialCount).toBe(1);

        await projectPage.clickCreateButton();

        await expect(page).toHaveURL(/\/projects\/new/);
        await expect(page.locator('form')).toBeVisible();

        await projectPage.fillProjectForm(newProjectData);

        await projectPage.submitForm();

        await expect(page).toHaveURL(/\/projects\/\d+/);

        await expect(page.locator('.success-message')).toBeVisible();
        await expect(page.locator('.success-message')).toContainText('created successfully');

        const title = await projectPage.getProjectTitle();
        expect(title).toContain('Galactic Chronicles');

        await page.locator('.back-button').click();
        await expect(page).toHaveURL('/projects');

        const newCount = await projectPage.getProjectCardCount();
        expect(newCount).toBe(initialCount + 1);
        expect(await projectPage.projectExists('Galactic Chronicles')).toBe(true);
      } catch (error) {
        await projectPage.takeScreenshot('create-project-failure');
        throw error;
      }
    });

    test('should validate required fields on project creation', async ({ page }) => {
      try {
        await projectPage.gotoProjects();
        await projectPage.clickCreateButton();

        await projectPage.submitForm();

        const errorCount = await page.locator('.error-message').count();
        expect(errorCount).toBeGreaterThan(0);

        const errors = await projectPage.getErrorMessages();
        expect(errors.some(e => e.includes('title'))).toBe(true);

        await projectPage.fillProjectForm({ title: 'Test Project' });
        await projectPage.submitForm();

        const errorCount2 = await page.locator('.error-message').count();
        expect(errorCount2).toBeGreaterThan(0);
      } catch (error) {
        await projectPage.takeScreenshot('validation-failure');
        throw error;
      }
    });

    test('should cancel project creation', async ({ page }) => {
      await projectPage.gotoProjects();
      await projectPage.clickCreateButton();

      await projectPage.fillProjectForm({ title: 'Test Project' });

      await projectPage.cancelForm();

      await expect(page).toHaveURL('/projects');

      expect(await projectPage.projectExists('Test Project')).toBe(false);
    });
  });

  test.describe('Read Project', () => {
    test('should view project details', async ({ page }) => {
      try {
        await projectPage.gotoProjects();
        await projectPage.clickProjectCard('The Chronicles of Eldermere');

        await expect(page).toHaveURL('/projects/1');

        await expect(page.locator('.project-title')).toHaveText('The Chronicles of Eldermere');

        await expect(page.locator('.project-genre')).toHaveText('Fantasy');

        await expect(page.locator('.project-premise')).toContainText('magical compass');

        await expect(page.locator('.stat-title').filter({ hasText: 'Statistics' })).toBeVisible();

        const themeCount = await page.locator('.theme-tag').count();
        expect(themeCount).toBeGreaterThan(0);
      } catch (error) {
        await projectPage.takeScreenshot('view-project-failure');
        throw error;
      }
    });

    test('should display all project tabs', async ({ page }) => {
      await projectPage.gotoProjectDetail('1');

      const tabs = ['Overview', 'Chapters', 'Characters', 'Settings'];
      for (const tab of tabs) {
        await expect(page.locator('.tab-button').filter({ hasText: tab })).toBeVisible();
      }

      await page.locator('.tab-button').filter({ hasText: 'Chapters' }).click();
      await expect(page.locator('.tab-button.active')).toHaveText('Chapters');

      await page.locator('.tab-button').filter({ hasText: 'Characters' }).click();
      await expect(page.locator('.tab-button.active')).toHaveText('Characters');

      await page.locator('.tab-button').filter({ hasText: 'Settings' }).click();
      await expect(page.locator('.tab-button.active')).toHaveText('Settings');
    });

    test('should handle non-existent project', async ({ page }) => {
      await projectPage.gotoProjectDetail('999');

      await expect(page.locator('.not-found')).toBeVisible();
      await expect(page.locator('.not-found-title')).toHaveText('Project Not Found');
    });
  });

  test.describe('Update Project', () => {
    test('should edit project details', async ({ page }) => {
      try {
        await projectPage.gotoProjectDetail('1');

        await projectPage.clickEditButton();

        await expect(projectPage.isEditMode()).toBe(true);

        await projectPage.fillProjectForm(updatedProjectData);

        await projectPage.submitForm();

        await expect(page.locator('.success-message')).toBeVisible();
        await expect(page.locator('.success-message')).toContainText('updated successfully');

        const title = await projectPage.getProjectTitle();
        expect(title).toContain('Remastered');

        await expect(page.locator('.stat-text')).toContainText('40');
      } catch (error) {
        await projectPage.takeScreenshot('update-project-failure');
        throw error;
      }
    });

    test('should cancel edit without saving', async ({ page }) => {
      await projectPage.gotoProjectDetail('1');
      await projectPage.clickEditButton();

      await projectPage.fillProjectForm({ title: 'Changed Title' });

      await projectPage.cancelForm();

      const title = await projectPage.getProjectTitle();
      expect(title).toBe('The Chronicles of Eldermere');
    });

    test('should show validation errors on update', async ({ page }) => {
      await projectPage.gotoProjectDetail('1');
      await projectPage.clickEditButton();

      await page.fill('input[name="title"]', '');
      await projectPage.submitForm();

      await expect(page.locator('.error-message')).toBeVisible();
      await expect(page.locator('.error-message')).toContainText('title');
    });
  });

  test.describe('Delete Project', () => {
    test('should delete project with confirmation', async ({ page }) => {
      try {
        await projectPage.gotoProjects();

        expect(await projectPage.projectExists('The Chronicles of Eldermere')).toBe(true);

        await projectPage.clickProjectCard('The Chronicles of Eldermere');

        await projectPage.clickDeleteButton();

        await expect(page.locator('.delete-dialog')).toBeVisible();
        await expect(page.locator('.delete-dialog')).toContainText('Are you sure');

        await projectPage.confirmDelete();

        await expect(page.locator('.success-message')).toBeVisible();
        await expect(page.locator('.success-message')).toContainText('deleted successfully');

        await page.locator('.back-button').click();

        expect(await projectPage.projectExists('The Chronicles of Eldermere')).toBe(false);
      } catch (error) {
        await projectPage.takeScreenshot('delete-project-failure');
        throw error;
      }
    });

    test('should cancel project deletion', async ({ page }) => {
      await projectPage.gotoProjectDetail('1');
      await projectPage.clickDeleteButton();

      await projectPage.cancelDelete();

      await expect(page.locator('.delete-dialog')).not.toBeVisible();

      await expect(page.locator('.project-title')).toHaveText('The Chronicles of Eldermere');
    });
  });

  test.describe('Accessibility Tests', () => {
    test('should have proper ARIA labels on form elements', async ({ page }) => {
      await projectPage.gotoCreateProject();

      const titleLabel = page.locator('label[for="title"]');
      await expect(titleLabel).toBeVisible();
      await expect(titleLabel).toHaveAttribute('for', 'title');

      const titleInput = page.locator('input[name="title"]');
      await expect(titleInput).toHaveAttribute('aria-required', 'true');
      await expect(titleInput).toHaveAttribute('aria-invalid', 'false');

      await expect(page.locator('button[type="submit"]')).toHaveAttribute('type', 'submit');
    });

    test('should support keyboard navigation', async ({ page }) => {
      await projectPage.gotoProjects();

      await page.keyboard.press('Tab');
      await expect(page.locator('.create-btn')).toBeFocused();

      await page.keyboard.press('Tab');
      await expect(page.locator('.search-input')).toBeFocused();

      await page.keyboard.press('Enter');

      await page.keyboard.press('ArrowDown');
    });

    test('should announce actions to screen readers', async ({ page }) => {
      await projectPage.gotoCreateProject();

      await projectPage.fillProjectForm({ title: 'Test Project' });
      await projectPage.submitForm();

      const liveRegion = page.locator('[aria-live]');
      await expect(liveRegion).toBeVisible();

      await expect(liveRegion).toContainText('success', { ignoreCase: true });
    });

    test('should have proper focus management', async ({ page }) => {
      await projectPage.gotoProjectDetail('1');

      await projectPage.clickDeleteButton();

      const dialog = page.locator('.delete-dialog');
      await expect(dialog).toBeVisible();
      await expect(dialog).toBeFocused();

      await page.keyboard.press('Escape');

      await expect(page.locator('.delete-btn')).toBeFocused();
    });

    test('should have sufficient color contrast', async ({ page }) => {
      await projectPage.gotoProjects();

      const title = page.locator('.project-title');
      const styles = await title.evaluate((el: any) => {
        const computed = window.getComputedStyle(el);
        return {
          color: computed.color,
          backgroundColor: computed.backgroundColor,
          fontSize: computed.fontSize
        };
      });

      expect(styles.color).not.toBe('rgb(255, 255, 255)');
    });

    test('should provide alternative text for images', async ({ page }) => {
      await projectPage.gotoProjectDetail('1');

      const avatar = page.locator('img.avatar');
      if (await avatar.count() > 0) {
        await expect(avatar.first()).toHaveAttribute('alt');
      }
    });
  });

  test.describe('Full CRUD Flow', () => {
    test('should complete full project lifecycle', async ({ page, context }) => {
      try {
        const projectPage = new ProjectPage(page);

        await projectPage.gotoProjects();
        await projectPage.clickCreateButton();
        await projectPage.fillProjectForm(newProjectData);
        await projectPage.submitForm();

        await expect(page).toHaveURL(/\/projects\/\d+/);
        await expect(page.locator('.success-message')).toContainText('created');

        const projectId = page.url().split('/').pop();
        await projectPage.takeScreenshot(`after-create-${projectId}`);

        const title = await projectPage.getProjectTitle();
        expect(title).toContain('Galactic Chronicles');
        const premise = await projectPage.getProjectPremise();
        expect(premise).toContain('space odyssey');

        await projectPage.clickEditButton();
        await projectPage.fillProjectForm({
          title: 'Galactic Chronicles: Updated'
        });
        await projectPage.submitForm();

        await expect(page.locator('.success-message')).toContainText('updated');
        const updatedTitle = await projectPage.getProjectTitle();
        expect(updatedTitle).toContain('Updated');
        await projectPage.takeScreenshot(`after-update-${projectId}`);

        await page.locator('.back-button').click();

        await projectPage.clickProjectCard('Galactic Chronicles: Updated');
        await projectPage.clickDeleteButton();
        await projectPage.confirmDelete();

        await expect(page.locator('.success-message')).toContainText('deleted');
        await projectPage.takeScreenshot('after-delete');

        await page.locator('.back-button').click();
        expect(await projectPage.projectExists('Galactic Chronicles')).toBe(false);
      } catch (error) {
        await projectPage.takeScreenshot('full-crud-failure');
        throw error;
      }
    });
  });
});
