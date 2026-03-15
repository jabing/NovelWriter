import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Complete Publishing Workflow
 * Tests platform selection, chapter selection, scheduling, and publish action
 * All API calls are mocked to avoid real platform interactions
 */

const mockPlatforms = [
  {
    id: '1',
    name: 'Wattpad',
    type: 'wattpad',
    description: 'Publish to Wattpad platform',
    enabled: true,
    connected: true,
    last_sync: '2024-03-15T10:30:00Z',
    published_chapters: 12,
    total_reads: 15432
  },
  {
    id: '2',
    name: 'Royal Road',
    type: 'royalroad',
    description: 'Publish to Royal Road platform',
    enabled: true,
    connected: true,
    last_sync: '2024-03-14T15:45:00Z',
    published_chapters: 8,
    total_reads: 8921
  },
  {
    id: '3',
    name: 'Amazon Kindle',
    type: 'amazon',
    description: 'Publish to Amazon Kindle Direct Publishing',
    enabled: true,
    connected: false,
    last_sync: null,
    published_chapters: 0,
    total_reads: 0
  }
];

const mockChapters = [
  { id: '1', number: 1, title: 'The Beginning', status: 'completed', word_count: 3500 },
  { id: '2', number: 2, title: 'Journey Begins', status: 'completed', word_count: 4200 },
  { id: '3', number: 3, title: 'First Conflict', status: 'completed', word_count: 3800 },
  { id: '4', number: 4, title: 'Rising Action', status: 'draft', word_count: 0 },
  { id: '5', number: 5, title: 'The Climax', status: 'draft', word_count: 0 }
];

const mockPublishResponse = {
  success: true,
  platform: 'Wattpad',
  published_chapters: [1, 2, 3],
  message: 'Successfully published 3 chapters to Wattpad'
};

async function setupPublishMocks(page) {
  await page.route('**/api/publishing/platforms', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockPlatforms)
    });
  });

  await page.route('**/api/publishing/novels/*/publish', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockPublishResponse)
    });
  });

  await page.route('**/api/novels/*/chapters', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockChapters)
    });
  });
}

async function setupErrorMocks(page) {
  await page.route('**/api/publishing/novels/*/publish', async (route) => {
    await route.fulfill({
      status: 400,
      contentType: 'application/json',
      body: JSON.stringify({
        success: false,
        message: 'Failed to publish: Platform connection error'
      })
    });
  });
}

test.describe('Publishing Workflow - Platform Selection', () => {
  test.beforeEach(async ({ page }) => {
    await setupPublishMocks(page);
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');
  });

  test('should display all available platforms', async ({ page }) => {
    // Wait for platforms to load
    await page.waitForSelector('[data-testid="platform-item"]');

    // Check that all platforms are visible
    const platformItems = page.locator('[data-testid="platform-item"]');
    await expect(platformItems).toHaveCount(3);

    // Verify platform names
    const platformNames = page.locator('[data-testid="platform-name"]');
    await expect(platformNames.nth(0)).toHaveText('Wattpad');
    await expect(platformNames.nth(1)).toHaveText('Royal Road');
    await expect(platformNames.nth(2)).toHaveText('Amazon Kindle');
  });

  test('should display connection status for each platform', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Check connected platforms
    const connectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'connected' });
    await expect(connectedBadge).toHaveCount(2);

    // Check disconnected platform
    const disconnectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'disconnected' });
    await expect(disconnectedBadge).toHaveCount(1);
  });

  test('should select Wattpad platform', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Click on Wattpad platform
    const wattpadPlatform = page.getByTestId('platform-name').filter({ hasText: 'Wattpad' });
    await wattpadPlatform.click();

    // Verify platform is selected (check for active class or visual indicator)
    const platformCard = wattpadPlatform.locator('..').locator('..');
    await expect(platformCard).toHaveClass(/selected/);
  });

  test('should select Royal Road platform', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Click on Royal Road platform
    const royalRoadPlatform = page.getByTestId('platform-name').filter({ hasText: 'Royal Road' });
    await royalRoadPlatform.click();

    // Verify platform is selected
    const platformCard = royalRoadPlatform.locator('..').locator('..');
    await expect(platformCard).toHaveClass(/selected/);
  });

  test('should select Amazon Kindle platform', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Click on Amazon Kindle platform
    const kindlePlatform = page.getByTestId('platform-name').filter({ hasText: 'Amazon Kindle' });
    await kindlePlatform.click();

    // Verify platform is selected
    const platformCard = kindlePlatform.locator('..').locator('..');
    await expect(platformCard).toHaveClass(/selected/);
  });

  test('should switch between platforms', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Select Wattpad
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();
    await expect(page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).locator('..').locator('..')).toHaveClass(/selected/);

    // Switch to Royal Road
    await page.getByTestId('platform-name').filter({ hasText: 'Royal Road' }).click();
    await expect(page.getByTestId('platform-name').filter({ hasText: 'Royal Road' }).locator('..').locator('..')).toHaveClass(/selected/);
    await expect(page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).locator('..').locator('..')).not.toHaveClass(/selected/);

    // Switch to Amazon Kindle
    await page.getByTestId('platform-name').filter({ hasText: 'Amazon Kindle' }).click();
    await expect(page.getByTestId('platform-name').filter({ hasText: 'Amazon Kindle' }).locator('..').locator('..')).toHaveClass(/selected/);
    await expect(page.getByTestId('platform-name').filter({ hasText: 'Royal Road' }).locator('..').locator('..')).not.toHaveClass(/selected/);
  });

  test('should show connect button for disconnected platforms', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Find disconnected platform (Amazon Kindle)
    const disconnectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'disconnected' });
    const disconnectedPlatform = disconnectedBadge.locator('..').locator('..');

    // Verify connect button is shown
    const connectButton = disconnectedPlatform.getByTestId('platform-connect-button');
    await expect(connectButton).toBeVisible();
    await expect(connectButton).toHaveText('Connect');
  });

  test('should show manage button for connected platforms', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Find connected platform (Wattpad)
    const connectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'connected' }).first();
    const connectedPlatform = connectedBadge.locator('..').locator('..');

    // Verify manage button is shown
    const manageButton = connectedPlatform.getByTestId('platform-connect-button');
    await expect(manageButton).toBeVisible();
    await expect(manageButton).toHaveText('Manage');
  });
});

test.describe('Publishing Workflow - Chapter Selection', () => {
  test.beforeEach(async ({ page }) => {
    await setupPublishMocks(page);
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');
  });

  test('should display available chapters for selection', async ({ page }) => {
    // Click on a platform to show chapter selection
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list to load
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Check that all chapters are displayed
    const chapterCheckboxes = page.locator('[data-testid="chapter-checkbox"]');
    await expect(chapterCheckboxes).toHaveCount(5);

    // Verify chapter titles
    const chapterTitles = page.locator('[data-testid="chapter-title"]');
    await expect(chapterTitles.nth(0)).toHaveText('The Beginning');
    await expect(chapterTitles.nth(1)).toHaveText('Journey Begins');
  });

  test('should select single chapter', async ({ page }) => {
    // Click on a platform to show chapter selection
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select first chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Verify chapter is selected
    await expect(page.locator('[data-testid="chapter-checkbox"]').first()).toBeChecked();
  });

  test('should select multiple chapters', async ({ page }) => {
    // Click on a platform to show chapter selection
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select multiple chapters
    await page.locator('[data-testid="chapter-checkbox"]').nth(0).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(1).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(2).check();

    // Verify all selected
    await expect(page.locator('[data-testid="chapter-checkbox"]').nth(0)).toBeChecked();
    await expect(page.locator('[data-testid="chapter-checkbox"]').nth(1)).toBeChecked();
    await expect(page.locator('[data-testid="chapter-checkbox"]').nth(2)).toBeChecked();
  });

  test('should select all chapters', async ({ page }) => {
    // Click on a platform to show chapter selection
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Click select all button
    await page.getByTestId('select-all-chapters').click();

    // Verify all chapters are selected
    const chapterCheckboxes = page.locator('[data-testid="chapter-checkbox"]');
    const count = await chapterCheckboxes.count();

    for (let i = 0; i < count; i++) {
      await expect(chapterCheckboxes.nth(i)).toBeChecked();
    }
  });

  test('should deselect chapters', async ({ page }) => {
    // Click on a platform to show chapter selection
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();
    await expect(page.locator('[data-testid="chapter-checkbox"]').first()).toBeChecked();

    // Deselect the same chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().uncheck();
    await expect(page.locator('[data-testid="chapter-checkbox"]').first()).not.toBeChecked();
  });

  test('should display chapter count', async ({ page }) => {
    // Click on a platform to show chapter selection
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Check initial count
    const selectedCount = page.getByTestId('selected-chapters-count');
    await expect(selectedCount).toHaveText('0 chapters selected');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Verify count updated
    await expect(selectedCount).toHaveText('1 chapter selected');

    // Select more chapters
    await page.locator('[data-testid="chapter-checkbox"]').nth(1).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(2).check();

    // Verify count updated
    await expect(selectedCount).toHaveText('3 chapters selected');
  });

  test('should disable draft chapters by default', async ({ page }) => {
    // Click on a platform to show chapter selection
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Check that draft chapters (4, 5) are disabled
    const draftChapter4 = page.locator('[data-testid="chapter-checkbox"]').nth(3);
    const draftChapter5 = page.locator('[data-testid="chapter-checkbox"]').nth(4);

    await expect(draftChapter4).toBeDisabled();
    await expect(draftChapter5).toBeDisabled();
  });

  test('should only show completed chapters by default', async ({ page }) => {
    // Click on a platform to show chapter selection
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Check that only completed chapters (1, 2, 3) are enabled
    const enabledCheckboxes = page.locator('[data-testid="chapter-checkbox"]:not(:disabled)');
    await expect(enabledCheckboxes).toHaveCount(3);
  });
});

test.describe('Publishing Workflow - Scheduling', () => {
  test.beforeEach(async ({ page }) => {
    await setupPublishMocks(page);
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');
  });

  test('should display scheduling options', async ({ page }) => {
    // Click on a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for scheduling section
    await page.waitForSelector('[data-testid="scheduling-section"]');

    // Verify scheduling options are visible
    await expect(page.getByTestId('schedule-immediate')).toBeVisible();
    await expect(page.getByTestId('schedule-custom')).toBeVisible();
  });

  test('should select immediate publishing', async ({ page }) => {
    // Click on a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for scheduling section
    await page.waitForSelector('[data-testid="scheduling-section"]');

    // Select immediate publishing
    await page.getByTestId('schedule-immediate').click();

    // Verify immediate is selected
    await expect(page.getByTestId('schedule-immediate')).toBeChecked();

    // Verify date picker is disabled
    await expect(page.getByTestId('schedule-date-picker')).toBeDisabled();
  });

  test('should select custom scheduling', async ({ page }) => {
    // Click on a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for scheduling section
    await page.waitForSelector('[data-testid="scheduling-section"]');

    // Select custom scheduling
    await page.getByTestId('schedule-custom').click();

    // Verify custom is selected
    await expect(page.getByTestId('schedule-custom')).toBeChecked();

    // Verify date picker is enabled
    await expect(page.getByTestId('schedule-date-picker')).toBeEnabled();
  });

  test('should set publish date', async ({ page }) => {
    // Click on a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for scheduling section
    await page.waitForSelector('[data-testid="scheduling-section"]');

    // Select custom scheduling
    await page.getByTestId('schedule-custom').click();

    // Set a future date
    const dateInput = page.getByTestId('schedule-date-picker');
    await dateInput.fill('2024-04-01');

    // Verify date is set
    await expect(dateInput).toHaveValue('2024-04-01');
  });

  test('should set publish time', async ({ page }) => {
    // Click on a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for scheduling section
    await page.waitForSelector('[data-testid="scheduling-section"]');

    // Select custom scheduling
    await page.getByTestId('schedule-custom').click();

    // Set a time
    const timeInput = page.getByTestId('schedule-time-picker');
    await timeInput.fill('14:30');

    // Verify time is set
    await expect(timeInput).toHaveValue('14:30');
  });

  test('should display scheduled preview', async ({ page }) => {
    // Click on a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for scheduling section
    await page.waitForSelector('[data-testid="scheduling-section"]');

    // Select custom scheduling
    await page.getByTestId('schedule-custom').click();

    // Set date and time
    await page.getByTestId('schedule-date-picker').fill('2024-04-01');
    await page.getByTestId('schedule-time-picker').fill('14:30');

    // Verify preview is displayed
    const schedulePreview = page.getByTestId('schedule-preview');
    await expect(schedulePreview).toBeVisible();
    await expect(schedulePreview).toContainText('April 1, 2024 at 2:30 PM');
  });
});

test.describe('Publishing Workflow - Publish Action', () => {
  test.beforeEach(async ({ page }) => {
    await setupPublishMocks(page);
  });

  test('should publish selected chapters immediately', async ({ page }) => {
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select chapters
    await page.locator('[data-testid="chapter-checkbox"]').nth(0).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(1).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(2).check();

    // Select immediate publishing
    await page.getByTestId('schedule-immediate').click();

    // Click publish button
    await page.getByTestId('publish-button').click();

    // Wait for success message
    await page.waitForSelector('[data-testid="publish-success-message"]');

    // Verify success message
    await expect(page.getByTestId('publish-success-message')).toBeVisible();
    await expect(page.getByTestId('publish-success-message')).toHaveText('Successfully published 3 chapters to Wattpad');
  });

  test('should publish with custom scheduling', async ({ page }) => {
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select chapters
    await page.locator('[data-testid="chapter-checkbox"]').nth(0).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(1).check();

    // Select custom scheduling
    await page.getByTestId('schedule-custom').click();

    // Set date and time
    await page.getByTestId('schedule-date-picker').fill('2024-04-01');
    await page.getByTestId('schedule-time-picker').fill('14:30');

    // Click publish button
    await page.getByTestId('publish-button').click();

    // Wait for success message
    await page.waitForSelector('[data-testid="publish-success-message"]');

    // Verify success message
    await expect(page.getByTestId('publish-success-message')).toBeVisible();
    await expect(page.getByTestId('publish-success-message')).toContainText('scheduled');
  });

  test('should show loading state during publish', async ({ page }) => {
    // Mock a slow publish request
    await page.route('**/api/publishing/novels/*/publish', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPublishResponse)
      });
    });

    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Click publish button
    await page.getByTestId('publish-button').click();

    // Verify loading state
    await expect(page.getByTestId('publish-button')).toHaveAttribute('disabled');
    await expect(page.getByTestId('publish-button')).toContainText('Publishing...');

    // Wait for success
    await page.waitForSelector('[data-testid="publish-success-message"]', { timeout: 5000 });
  });

  test('should handle publish errors gracefully', async ({ page }) => {
    await setupErrorMocks(page);

    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Click publish button
    await page.getByTestId('publish-button').click();

    // Wait for error message
    await page.waitForSelector('[data-testid="publish-error-message"]');

    // Verify error message
    await expect(page.getByTestId('publish-error-message')).toBeVisible();
    await expect(page.getByTestId('publish-error-message')).toHaveText('Failed to publish: Platform connection error');
  });

  test('should disable publish button when no chapters selected', async ({ page }) => {
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Verify publish button is disabled
    await expect(page.getByTestId('publish-button')).toBeDisabled();

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Verify publish button is now enabled
    await expect(page.getByTestId('publish-button')).toBeEnabled();
  });

  test('should show confirmation dialog before publish', async ({ page }) => {
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select chapters
    await page.locator('[data-testid="chapter-checkbox"]').nth(0).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(1).check();

    // Click publish button
    await page.getByTestId('publish-button').click();

    // Verify confirmation dialog is shown
    await expect(page.getByTestId('publish-confirmation-dialog')).toBeVisible();
    await expect(page.getByTestId('publish-confirmation-dialog')).toContainText('Are you sure you want to publish 2 chapters to Wattpad?');

    // Confirm publish
    await page.getByTestId('confirm-publish').click();

    // Wait for success message
    await page.waitForSelector('[data-testid="publish-success-message"]');
  });

  test('should cancel publish from confirmation dialog', async ({ page }) => {
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Click publish button
    await page.getByTestId('publish-button').click();

    // Verify confirmation dialog is shown
    await expect(page.getByTestId('publish-confirmation-dialog')).toBeVisible();

    // Cancel publish
    await page.getByTestId('cancel-publish').click();

    // Verify dialog is closed and no success message
    await expect(page.getByTestId('publish-confirmation-dialog')).not.toBeVisible();
    await expect(page.getByTestId('publish-success-message')).not.toBeVisible();
  });
});

test.describe('Publishing Workflow - Form Validation', () => {
  test.beforeEach(async ({ page }) => {
    await setupPublishMocks(page);
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');
  });

  test('should validate that at least one chapter is selected', async ({ page }) => {
    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Don't select any chapters
    // Try to click publish button (should be disabled)
    const publishButton = page.getByTestId('publish-button');
    await expect(publishButton).toBeDisabled();

    // Verify error message is shown
    await expect(page.getByTestId('no-chapters-error')).toBeVisible();
    await expect(page.getByTestId('no-chapters-error')).toHaveText('Please select at least one chapter to publish');
  });

  test('should validate scheduled date is in the future', async ({ page }) => {
    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Select custom scheduling
    await page.getByTestId('schedule-custom').click();

    // Set a past date
    await page.getByTestId('schedule-date-picker').fill('2020-01-01');

    // Try to publish
    await page.getByTestId('publish-button').click();

    // Verify error message
    await expect(page.getByTestId('schedule-date-error')).toBeVisible();
    await expect(page.getByTestId('schedule-date-error')).toHaveText('Schedule date must be in the future');
  });

  test('should validate scheduled time format', async ({ page }) => {
    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Select custom scheduling
    await page.getByTestId('schedule-custom').click();

    // Set invalid time
    await page.getByTestId('schedule-time-picker').fill('25:00');

    // Verify error message
    await expect(page.getByTestId('schedule-time-error')).toBeVisible();
  });

  test('should validate platform connection before publish', async ({ page }) => {
    // Select disconnected platform
    await page.getByTestId('platform-name').filter({ hasText: 'Amazon Kindle' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Try to publish
    await page.getByTestId('publish-button').click();

    // Verify error message about platform connection
    await expect(page.getByTestId('platform-not-connected-error')).toBeVisible();
    await expect(page.getByTestId('platform-not-connected-error')).toHaveText('Please connect to Amazon Kindle before publishing');
  });
});

test.describe('Publishing Workflow - Success and Error States', () => {
  test.beforeEach(async ({ page }) => {
    await setupPublishMocks(page);
  });

  test('should display success message after successful publish', async ({ page }) => {
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select chapters
    await page.locator('[data-testid="chapter-checkbox"]').nth(0).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(1).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(2).check();

    // Publish
    await page.getByTestId('schedule-immediate').click();
    await page.getByTestId('confirm-publish').click();

    // Wait for success message
    await page.waitForSelector('[data-testid="publish-success-message"]');

    // Verify success message
    await expect(page.getByTestId('publish-success-message')).toBeVisible();
    await expect(page.getByTestId('publish-success-message')).toHaveClass(/alert-success/);

    // Verify success icon
    await expect(page.getByTestId('publish-success-icon')).toBeVisible();
  });

  test('should display error message on publish failure', async ({ page }) => {
    await setupErrorMocks(page);

    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Try to publish
    await page.getByTestId('publish-button').click();

    // Wait for error message
    await page.waitForSelector('[data-testid="publish-error-message"]');

    // Verify error message
    await expect(page.getByTestId('publish-error-message')).toBeVisible();
    await expect(page.getByTestId('publish-error-message')).toHaveClass(/alert-error/);

    // Verify error icon
    await expect(page.getByTestId('publish-error-icon')).toBeVisible();
  });

  test('should allow retry after error', async ({ page }) => {
    await setupErrorMocks(page);

    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Try to publish (will fail)
    await page.getByTestId('publish-button').click();
    await page.waitForSelector('[data-testid="publish-error-message"]');

    // Now mock success
    await setupPublishMocks(page);

    // Try to publish again
    await page.getByTestId('retry-publish-button').click();

    // Wait for success
    await page.waitForSelector('[data-testid="publish-success-message"]');
  });

  test('should clear error message when form is modified', async ({ page }) => {
    await setupErrorMocks(page);

    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Try to publish (will fail)
    await page.getByTestId('publish-button').click();
    await page.waitForSelector('[data-testid="publish-error-message"]');

    // Verify error is shown
    await expect(page.getByTestId('publish-error-message')).toBeVisible();

    // Modify form by selecting another chapter
    await page.locator('[data-testid="chapter-checkbox"]').nth(1).check();

    // Verify error is cleared
    await expect(page.getByTestId('publish-error-message')).not.toBeVisible();
  });

  test('should disable platform selection during publish', async ({ page }) => {
    // Mock slow publish
    await page.route('**/api/publishing/novels/*/publish', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPublishResponse)
      });
    });

    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Select a chapter
    await page.locator('[data-testid="chapter-checkbox"]').first().check();

    // Click publish
    await page.getByTestId('publish-button').click();

    // Try to switch platform during publish (should be disabled)
    const otherPlatform = page.getByTestId('platform-name').filter({ hasText: 'Royal Road' });
    await expect(otherPlatform).toHaveAttribute('disabled');
  });
});

test.describe('Publishing Workflow - Platform Connection Status', () => {
  test.beforeEach(async ({ page }) => {
    await setupPublishMocks(page);
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');
  });

  test('should display last sync time for connected platforms', async ({ page }) => {
    // Find connected platform (Wattpad)
    const connectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'connected' }).first();
    const connectedPlatform = connectedBadge.locator('..').locator('..');

    // Verify last sync time is displayed
    const lastSync = connectedPlatform.getByTestId('platform-last-sync');
    await expect(lastSync).toBeVisible();
    await expect(lastSync).toContainText('Last sync');
  });

  test('should show never synced for disconnected platforms', async ({ page }) => {
    // Find disconnected platform (Amazon Kindle)
    const disconnectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'disconnected' });
    const disconnectedPlatform = disconnectedBadge.locator('..').locator('..');

    // Verify never synced is displayed
    const lastSync = disconnectedPlatform.getByTestId('platform-last-sync');
    await expect(lastSync).toContainText('Never synced');
  });

  test('should update connection status after connect', async ({ page }) => {
    // Find disconnected platform
    const disconnectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'disconnected' }).first();
    const disconnectedPlatform = disconnectedBadge.locator('..').locator('..');

    // Click connect button
    await disconnectedPlatform.getByTestId('platform-connect-button').click();

    // Verify connection status changes to connected
    // (This would require mocking the connection API)
    await expect(disconnectedBadge).toHaveText('connected');
  });

  test('should update connection status after disconnect', async ({ page }) => {
    // Find connected platform
    const connectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'connected' }).first();
    const connectedPlatform = connectedBadge.locator('..').locator('..');

    // Click disconnect button
    await connectedPlatform.getByTestId('platform-connect-button').click();

    // Verify connection status changes to disconnected
    await expect(connectedBadge).toHaveText('disconnected');
  });

  test('should show connection status badge with correct color', async ({ page }) => {
    // Check connected badge has success color
    const connectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'connected' }).first();
    await expect(connectedBadge).toHaveClass(/badge-success/);

    // Check disconnected badge has warning color
    const disconnectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'disconnected' });
    await expect(disconnectedBadge).toHaveClass(/badge-warning/);
  });

  test('should refresh platform status', async ({ page }) => {
    // Find a platform
    const firstPlatform = page.locator('[data-testid="platform-item"]').first();

    // Click refresh button
    await firstPlatform.getByTestId('refresh-platform-status').click();

    // Wait for refresh to complete
    await page.waitForTimeout(1000);

    // Verify platform is still visible (refresh didn't break it)
    await expect(firstPlatform).toBeVisible();
  });
});

test.describe('Publishing Workflow - Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    await setupPublishMocks(page);
  });

  test('should complete full publishing workflow', async ({ page }) => {
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Step 1: Select platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();
    await expect(page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).locator('..').locator('..')).toHaveClass(/selected/);

    // Step 2: Select chapters
    await page.waitForSelector('[data-testid="chapter-checkbox"]');
    await page.locator('[data-testid="chapter-checkbox"]').nth(0).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(1).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(2).check();
    await expect(page.getByTestId('selected-chapters-count')).toHaveText('3 chapters selected');

    // Step 3: Select scheduling
    await page.getByTestId('schedule-immediate').click();
    await expect(page.getByTestId('schedule-immediate')).toBeChecked();

    // Step 4: Publish
    await page.getByTestId('publish-button').click();
    await page.waitForSelector('[data-testid="publish-confirmation-dialog"]');
    await page.getByTestId('confirm-publish').click();

    // Step 5: Verify success
    await page.waitForSelector('[data-testid="publish-success-message"]');
    await expect(page.getByTestId('publish-success-message')).toBeVisible();
    await expect(page.getByTestId('publish-success-message')).toContainText('Successfully published 3 chapters to Wattpad');
  });

  test('should complete full workflow with custom scheduling', async ({ page }) => {
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select platform (Royal Road)
    await page.getByTestId('platform-name').filter({ hasText: 'Royal Road' }).click();

    // Select chapters
    await page.waitForSelector('[data-testid="chapter-checkbox"]');
    await page.locator('[data-testid="chapter-checkbox"]').nth(0).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(1).check();

    // Select custom scheduling
    await page.getByTestId('schedule-custom').click();

    // Set date and time
    await page.getByTestId('schedule-date-picker').fill('2024-05-01');
    await page.getByTestId('schedule-time-picker').fill('10:00');

    // Publish
    await page.getByTestId('publish-button').click();
    await page.getByTestId('confirm-publish').click();

    // Verify success
    await page.waitForSelector('[data-testid="publish-success-message"]');
    await expect(page.getByTestId('publish-success-message')).toContainText('scheduled');
  });

  test('should maintain state when navigating between platforms', async ({ page }) => {
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select platform A and chapters
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();
    await page.waitForSelector('[data-testid="chapter-checkbox"]');
    await page.locator('[data-testid="chapter-checkbox"]').nth(0).check();
    await page.locator('[data-testid="chapter-checkbox"]').nth(1).check();

    // Switch to platform B
    await page.getByTestId('platform-name').filter({ hasText: 'Royal Road' }).click();

    // Verify platform B has no chapters selected (separate state)
    await expect(page.getByTestId('selected-chapters-count')).toHaveText('0 chapters selected');

    // Switch back to platform A
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Verify platform A still has chapters selected
    await expect(page.getByTestId('selected-chapters-count')).toHaveText('2 chapters selected');
  });

  test('should handle rapid platform switching', async ({ page }) => {
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Rapidly switch between platforms
    for (let i = 0; i < 3; i++) {
      await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();
      await page.waitForTimeout(200);
      await page.getByTestId('platform-name').filter({ hasText: 'Royal Road' }).click();
      await page.waitForTimeout(200);
      await page.getByTestId('platform-name').filter({ hasText: 'Amazon Kindle' }).click();
      await page.waitForTimeout(200);
    }

    // Final platform should be Amazon Kindle
    await expect(page.getByTestId('platform-name').filter({ hasText: 'Amazon Kindle' }).locator('..').locator('..')).toHaveClass(/selected/);
  });
});

test.describe('Publishing Workflow - Responsive Design', () => {
  test.beforeEach(async ({ page }) => {
    await setupPublishMocks(page);
  });

  test('should display correctly on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Platforms should be visible
    await expect(page.locator('[data-testid="platform-item"]').first()).toBeVisible();

    // Platform cards should stack vertically
    const platformCards = page.locator('[data-testid="platform-item"]');
    const firstCard = platformCards.first();
    const secondCard = platformCards.nth(1);

    const firstBox = await firstCard.boundingBox();
    const secondBox = await secondCard.boundingBox();

    expect(secondBox?.y).toBeGreaterThan(firstBox?.y || 0);
  });

  test('should display correctly on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // Select a platform to show chapter selection
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Chapter selection should be visible
    await page.waitForSelector('[data-testid="chapter-checkbox"]');
    await expect(page.locator('[data-testid="chapter-checkbox"]').first()).toBeVisible();
  });

  test('should display correctly on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');

    // All platforms should be visible
    await expect(page.locator('[data-testid="platform-item"]')).toHaveCount(3);

    // Select a platform
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();

    // Chapter selection should be visible and well-organized
    await page.waitForSelector('[data-testid="chapter-checkbox"]');
    await expect(page.locator('[data-testid="chapter-checkbox"]').first()).toBeVisible();
  });
});

test.describe('Publishing Workflow - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await setupPublishMocks(page);
    await page.goto('/publish');
    await page.waitForLoadState('networkidle');
  });

  test('should have proper ARIA labels', async ({ page }) => {
    // Check platform cards have proper roles
    const platformCards = page.locator('[data-testid="platform-item"]');
    await expect(platformCards.first()).toHaveAttribute('role', 'button');

    // Check chapter checkboxes have proper labels
    await page.getByTestId('platform-name').filter({ hasText: 'Wattpad' }).click();
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    const chapterCheckbox = page.locator('[data-testid="chapter-checkbox"]').first();
    await expect(chapterCheckbox).toHaveAttribute('aria-label');
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Select first platform with keyboard
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');

    // Wait for chapter list
    await page.waitForSelector('[data-testid="chapter-checkbox"]');

    // Navigate to first chapter checkbox
    await page.keyboard.press('Tab');
    await page.keyboard.press('Space');

    // Verify chapter is selected
    await expect(page.locator('[data-testid="chapter-checkbox"]').first()).toBeChecked();
  });

  test('should have proper focus states', async ({ page }) => {
    const platformCard = page.locator('[data-testid="platform-item"]').first();

    // Focus the card
    await platformCard.focus();

    // Check focus state
    const isFocused = await platformCard.evaluate(el => {
      return document.activeElement === el;
    });

    expect(isFocused).toBe(true);
  });
});
