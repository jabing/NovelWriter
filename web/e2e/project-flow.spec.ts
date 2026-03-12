import { test, expect } from '@playwright/test';
import type { Project } from '../src/types';

// Mock data
const mockProjects: Project[] = [
  {
    id: '1',
    title: 'The Chronicles of Eldermere',
    genre: 'Fantasy',
    language: 'English',
    status: 'in_progress',
    premise: 'A young girl discovers a magical compass that leads her between worlds.',
    themes: ['Magic', 'Adventure', 'Coming of Age'],
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
  },
  {
    id: '2',
    title: 'Starlight Protocol',
    genre: 'Science Fiction',
    language: 'English',
    status: 'draft',
    premise: 'In a future where humanity has colonized the stars, a rogue AI threatens to destroy everything.',
    themes: ['AI', 'Space', 'Survival'],
    pov: 'Third Person Limited',
    tone: 'Tense',
    target_audience: 'Adult',
    story_structure: 'Hero\'s Journey',
    content_rating: 'PG-13',
    target_chapters: 30,
    completed_chapters: 5,
    total_words: 18000,
    target_words: 90000,
    progress_percent: 20,
    created_at: '2024-02-01T00:00:00Z',
    updated_at: '2024-03-10T00:00:00Z',
    platforms: []
  },
  {
    id: '3',
    title: 'The Last Detective',
    genre: 'Mystery',
    language: 'English',
    status: 'completed',
    premise: 'A detective in 1950s London solves her final case before retirement.',
    themes: ['Mystery', 'Historical', 'Noir'],
    pov: 'First Person',
    tone: 'Melancholic',
    target_audience: 'Adult',
    story_structure: 'Mystery',
    content_rating: 'PG-13',
    target_chapters: 20,
    completed_chapters: 20,
    total_words: 80000,
    target_words: 80000,
    progress_percent: 100,
    created_at: '2023-11-01T00:00:00Z',
    updated_at: '2024-02-28T00:00:00Z',
    platforms: []
  }
];

test.describe('Project Flow E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API for fetching projects
    await page.route('**/api/projects', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProjects)
      });
    });
  });

  test('should display project list with correct data', async ({ page }) => {
    await page.goto('/projects');

    // Wait for projects to load
    await expect(page.locator('.project-card')).toHaveCount(3);

    // Verify first project details
    const firstCard = page.locator('.project-card').first();
    await expect(firstCard.locator('.project-title')).toHaveText('The Chronicles of Eldermere');
    await expect(firstCard.locator('.project-genre')).toHaveText('Fantasy');
    await expect(firstCard.locator('.project-premise')).toHaveText(/magical compass/);

    // Verify progress stats
    await expect(firstCard).toContainText('12/50');
    await expect(firstCard).toContainText('45.0k');
    await expect(firstCard).toContainText('30%');
  });

  test('should filter projects by search query', async ({ page }) => {
    await page.goto('/projects');

    // Fill search input
    await page.fill('.search-input', 'Starlight');

    // Should show only one matching project
    await expect(page.locator('.project-card')).toHaveCount(1);
    await expect(page.locator('.project-title')).toHaveText('Starlight Protocol');

    // Clear search
    await page.click('.search-input');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Delete');

    // Should show all projects again
    await expect(page.locator('.project-card')).toHaveCount(3);
  });

  test('should navigate to project detail when clicking a project card', async ({ page }) => {
    await page.goto('/projects');

    // Click on first project
    await page.locator('.project-card').first().click();

    // Verify navigation to project detail
    await expect(page).toHaveURL(/\/projects\/\d+/);

    // Verify project detail page elements
    await expect(page.locator('.project-title')).toBeVisible();
    await expect(page.locator('.project-title')).toHaveText('The Chronicles of Eldermere');
    await expect(page.locator('.project-genre')).toHaveText('Fantasy');

    // Verify progress ring
    await expect(page.locator('.progress-value')).toHaveText('30');
  });

  test('should switch between card and table views', async ({ page }) => {
    await page.goto('/projects');

    // Verify default card view
    await expect(page.locator('.projects-grid')).toBeVisible();

    // Switch to table view
    await page.locator('.toggle-btn[title="Table view"]').click();

    // Verify table view
    await expect(page.locator('.projects-table')).toBeVisible();
    await expect(page.locator('.table-row')).toHaveCount(3);

    // Verify table content
    const firstRow = page.locator('.table-row').first();
    await expect(firstRow.locator('.title-text')).toHaveText('The Chronicles of Eldermere');
    await expect(firstRow).toContainText('Fantasy');
    await expect(firstRow).toContainText('30%');

    // Switch back to card view
    await page.locator('.toggle-btn[title="Card view"]').click();
    await expect(page.locator('.projects-grid')).toBeVisible();
  });

  test('should display project detail overview tab', async ({ page }) => {
    await page.goto('/projects/1');

    // Verify overview tab is active
    await expect(page.locator('.tab-button.active')).toHaveText('Overview');

    // Verify premise card
    await expect(page.locator('.stat-title').filter({ hasText: 'Premise' })).toBeVisible();
    await expect(page.locator('.stat-text').filter({ hasText: /magical compass/ })).toBeVisible();

    // Verify statistics card
    await expect(page.locator('.stat-title').filter({ hasText: 'Statistics' })).toBeVisible();
    const statsSection = page.locator('.stat-title').filter({ hasText: 'Statistics' }).locator('..');
    await expect(statsSection).toContainText('12/50');
    await expect(statsSection).toContainText('45,000');
    await expect(statsSection).toContainText('150,000');

    // Verify themes
    await expect(page.locator('.theme-tag')).toHaveCount(3);
    await expect(page.locator('.theme-tag').nth(0)).toHaveText('Magic');
    await expect(page.locator('.theme-tag').nth(1)).toHaveText('Adventure');
    await expect(page.locator('.theme-tag').nth(2)).toHaveText('Coming of Age');

    // Verify details
    await expect(page.locator('.detail-row').filter({ hasText: 'POV' })).toBeVisible();
    await expect(page.locator('.detail-row').filter({ hasText: 'POV' })).toContainText('First Person');
  });

  test('should switch between project detail tabs', async ({ page }) => {
    await page.goto('/projects/1');

    // Click on Chapters tab
    await page.locator('.tab-button').filter({ hasText: 'Chapters' }).click();
    await expect(page.locator('.tab-button.active')).toHaveText('Chapters');
    await expect(page.locator('.empty-content h3')).toHaveText('Chapters');

    // Click on Characters tab
    await page.locator('.tab-button').filter({ hasText: 'Characters' }).click();
    await expect(page.locator('.tab-button.active')).toHaveText('Characters');
    await expect(page.locator('.empty-content h3')).toHaveText('Characters');

    // Click on Settings tab
    await page.locator('.tab-button').filter({ hasText: 'Settings' }).click();
    await expect(page.locator('.tab-button.active')).toHaveText('Settings');
    await expect(page.locator('.empty-content h3')).toHaveText('Project Settings');

    // Return to Overview tab
    await page.locator('.tab-button').filter({ hasText: 'Overview' }).click();
    await expect(page.locator('.tab-button.active')).toHaveText('Overview');
  });

  test('should navigate back to projects list', async ({ page }) => {
    await page.goto('/projects/1');

    // Click back button
    await page.locator('.back-button').click();

    // Verify navigation
    await expect(page).toHaveURL('/projects');
    await expect(page.locator('.project-card')).toHaveCount(3);
  });

  test('should display reading bookshelf view', async ({ page }) => {
    await page.goto('/reading');

    // Verify "Continue Reading" section exists (for in-progress projects)
    const continueSection = page.locator('.continue-section');
    if (await continueSection.count() > 0) {
      await expect(continueSection).toBeVisible();
      await expect(continueSection.locator('.continue-title')).toContainText('The Chronicles of Eldermere');
    }

    // Verify all books grid
    await expect(page.locator('.book-card')).toHaveCount(3);

    // Verify first book
    const firstBook = page.locator('.book-card').first();
    await expect(firstBook.locator('.book-title')).toHaveText('The Chronicles of Eldermere');
    await expect(firstBook.locator('.book-author')).toHaveText('Fantasy');
    await expect(firstBook).toContainText('30%');
  });

  test('should sort books by reading progress', async ({ page }) => {
    await page.goto('/reading');

    // Verify books are sorted (in-progress first, then by progress)
    const bookTitles = page.locator('.book-title');
    await expect(bookTitles.nth(0)).toHaveText('The Chronicles of Eldermere');
    await expect(bookTitles.nth(1)).toHaveText('Starlight Protocol');
    await expect(bookTitles.nth(2)).toHaveText('The Last Detective');
  });

  test('should navigate to reader from bookshelf', async ({ page }) => {
    // Mock reader navigation by intercepting project navigation
    await page.goto('/reading');

    // Click on a book
    await page.locator('.book-card').first().click();

    // Verify navigation to project detail
    await expect(page).toHaveURL(/\/projects\/\d+/);
    await expect(page.locator('.project-title')).toBeVisible();
  });

  test('should display reader view', async ({ page }) => {
    await page.goto('/reader/1/10');

    // Verify reader elements
    await expect(page.locator('.reader-view')).toBeVisible();
    await expect(page.locator('.chapter-number')).toHaveText('Chapter 1');
    await expect(page.locator('.chapter-text')).toBeVisible();

    // Verify navigation
    await expect(page.locator('.floating-nav')).toBeVisible();
    await expect(page.locator('.chapter-current')).toHaveText(/Chapter 1 of 10/);
  });

  test('should navigate between chapters in reader', async ({ page }) => {
    await page.goto('/reader/1/10');

    // Initial state
    await expect(page.locator('.chapter-current')).toHaveText(/Chapter 1 of 10/);
    await expect(page.locator('.nav-prev')).toHaveCount(0); // No previous button on first chapter
    await expect(page.locator('.nav-next')).toBeVisible();

    // Click next chapter
    await page.locator('.nav-next').click();
    await expect(page.locator('.chapter-current')).toHaveText(/Chapter 2 of 10/);
    await expect(page.locator('.nav-prev')).toBeVisible();

    // Click previous chapter
    await page.locator('.nav-prev').click();
    await expect(page.locator('.chapter-current')).toHaveText(/Chapter 1 of 10/);
  });

  test('should toggle reader settings', async ({ page }) => {
    await page.goto('/reader/1/10');

    // Open settings
    await page.locator('.nav-settings').click();
    await expect(page.locator('.settings-panel')).toBeVisible();
    await expect(page.locator('.settings-overlay')).toBeVisible();

    // Verify theme options
    await expect(page.locator('.theme-btn')).toHaveCount(3);
    await expect(page.locator('.theme-btn').nth(0)).toHaveAttribute('aria-label', /Light theme/);
    await expect(page.locator('.theme-btn').nth(1)).toHaveAttribute('aria-label', /Sepia theme/);
    await expect(page.locator('.theme-btn').nth(2)).toHaveAttribute('aria-label', /Dark theme/);

    // Verify font size options
    await expect(page.locator('.size-btn')).toHaveCount(6);

    // Close settings
    await page.locator('.settings-close').click();
    await expect(page.locator('.settings-panel')).not.toBeVisible();
  });

  test('should change reader theme', async ({ page }) => {
    await page.goto('/reader/1/10');

    // Open settings
    await page.locator('.nav-settings').click();

    // Select dark theme
    await page.locator('.theme-btn').filter({ hasText: 'Dark' }).click();

    // Verify theme class is applied
    await expect(page.locator('.reader-view')).toHaveClass(/theme-dark/);

    // Open settings again
    await page.locator('.nav-settings').click();

    // Select sepia theme
    await page.locator('.theme-btn').filter({ hasText: 'Sepia' }).click();

    // Verify theme class is updated
    await expect(page.locator('.reader-view')).toHaveClass(/theme-sepia/);
  });

  test('should display keyboard shortcuts in reader settings', async ({ page }) => {
    await page.goto('/reader/1/10');

    // Open settings
    await page.locator('.nav-settings').click();

    // Verify keyboard shortcuts
    await expect(page.locator('.shortcut')).toHaveCount(3);
    const shortcuts = page.locator('.shortcut');
    await expect(shortcuts.nth(0)).toContainText('Previous chapter');
    await expect(shortcuts.nth(1)).toContainText('Next chapter');
    await expect(shortcuts.nth(2)).toContainText('Exit reader');
  });

  test('should use keyboard navigation in reader', async ({ page }) => {
    await page.goto('/reader/2/10');

    // Use keyboard to go to next chapter
    await page.keyboard.press('ArrowRight');
    await expect(page.locator('.chapter-current')).toHaveText(/Chapter 3 of 10/);

    // Use keyboard to go back
    await page.keyboard.press('ArrowLeft');
    await expect(page.locator('.chapter-current')).toHaveText(/Chapter 2 of 10/);
  });

  test('should exit reader with keyboard', async ({ page }) => {
    await page.goto('/reader/1/10');

    // Press Escape to exit
    await page.keyboard.press('Escape');

    // Should navigate back
    await expect(page).toHaveURL(/\/reading/);
  });

  test('should show empty state when no projects exist', async ({ page }) => {
    // Mock empty projects response
    await page.route('**/api/projects', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/projects');

    // Verify empty state
    await expect(page.locator('.empty-state')).toBeVisible();
    await expect(page.locator('.empty-state-title')).toHaveText('No Data');
    await expect(page.locator('.empty-state-description')).toBeVisible();
    await expect(page.locator('.create-btn')).toBeVisible();
  });

  test('should filter projects by genre', async ({ page }) => {
    await page.goto('/projects');

    // Select Fantasy genre
    await page.selectOption('.filter-select', 'Fantasy');

    // Should show only Fantasy projects
    await expect(page.locator('.project-card')).toHaveCount(1);
    await expect(page.locator('.project-title')).toHaveText('The Chronicles of Eldermere');

    // Clear filter
    await page.selectOption('.filter-select', '');
    await expect(page.locator('.project-card')).toHaveCount(3);
  });

  test('should filter projects by status', async ({ page }) => {
    await page.goto('/projects');

    // Select Completed status
    await page.locator('.filter-select').nth(1).selectOption('Completed');

    // Should show only completed projects
    await expect(page.locator('.project-card')).toHaveCount(1);
    await expect(page.locator('.project-title')).toHaveText('The Last Detective');
    await expect(page.locator('.status-badge.badge-success')).toHaveCount(1);
  });

  test('should display project not found state', async ({ page }) => {
    await page.goto('/projects/999');

    // Verify not found state
    await expect(page.locator('.not-found')).toBeVisible();
    await expect(page.locator('.not-found-title')).toHaveText('Project Not Found');
    await expect(page.locator('.not-found-description')).toContainText("doesn't exist");
    await expect(page.locator('.back-button')).toBeVisible();
  });

  test('should show quick action buttons on project detail', async ({ page }) => {
    await page.goto('/projects/1');

    // Verify quick action buttons
    await expect(page.locator('.quick-actions')).toBeVisible();
    await expect(page.locator('.action-button')).toHaveCount(4);
  });

  test('should display progress percentage correctly on project cards', async ({ page }) => {
    await page.goto('/projects');

    // Verify progress bars
    const cards = page.locator('.project-card');
    const progressValues = [30, 20, 100];

    for (let i = 0; i < await cards.count(); i++) {
      const card = cards.nth(i);
      await expect(card).toContainText(`${progressValues[i]}%`);

      // Verify progress bar width (roughly)
      const progressBar = card.locator('.progress-fill');
      await expect(progressBar).toBeVisible();
    }
  });

  test('should scroll reader content', async ({ page }) => {
    await page.goto('/reader/1/10');

    // Verify scroll progress bar exists
    await expect(page.locator('.progress-container')).toBeVisible();
    await expect(page.locator('.progress-bar')).toBeVisible();

    // Initial progress
    const progressLocator = page.locator('.chapter-progress');
    await expect(progressLocator).toHaveText(/0% read/);

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, 500));

    // Wait for scroll update
    await page.waitForTimeout(100);

    // Progress should have increased
    await expect(progressLocator).not.toHaveText(/0% read/);
  });
});

// Placeholder tests for features not yet implemented
test.describe('Project Creation (Not Implemented)', () => {
  test('should create a new project', async () => {
    // This test is a placeholder for when project creation is implemented
    test.skip(true, 'Project creation route not yet implemented');

    // Expected flow:
    // 1. Navigate to /projects/new
    // 2. Fill in project details
    // 3. Submit form
    // 4. Verify project is created
  });
});

test.describe('Project Edit and Delete (Not Implemented)', () => {
  test('should edit an existing project', async () => {
    // This test is a placeholder for when project editing is implemented
    test.skip(true, 'Project editing feature not yet implemented');
  });

  test('should delete a project', async () => {
    // This test is a placeholder for when project deletion is implemented
    test.skip(true, 'Project deletion feature not yet implemented');
  });
});
