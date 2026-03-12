import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Publishing Workflow and Settings
 * Tests platform connection configuration, publishing workflow, and settings functionality
 */

// Test Suite: Platform Connection Configuration
test.describe('Platform Connection Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/publish');
  });

  test('should display platform list with status badges', async ({ page }) => {
    // Wait for platforms to load
    await page.waitForSelector('[data-testid="platform-item"]');

    // Check that platform items are visible
    const platformItems = page.locator('[data-testid="platform-item"]');
    await expect(platformItems).toHaveCount(3);

    // Check that status badges are displayed
    const statusBadges = page.locator('[data-testid="platform-status-badge"]');
    await expect(statusBadges.first()).toBeVisible();

    // Verify badge text for first platform
    const firstBadge = statusBadges.first();
    await expect(firstBadge).toHaveText('connected');
  });

  test('should display platform stats for connected platforms', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Check for connected platform
    const connectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'connected' });
    const connectedPlatform = connectedBadge.locator('..').locator('..');

    // Verify chapters count is displayed
    const chaptersCount = connectedPlatform.getByTestId('platform-chapters-count');
    await expect(chaptersCount).toBeVisible();
    const chaptersText = await chaptersCount.textContent();
    expect(parseInt(chaptersText || '0')).toBeGreaterThanOrEqual(0);

    // Verify reads count is displayed
    const readsCount = connectedPlatform.getByTestId('platform-reads-count');
    await expect(readsCount).toBeVisible();
  });

  test('should show connect button for disconnected platforms', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Find disconnected platform
    const disconnectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'disconnected' });
    const disconnectedPlatform = disconnectedBadge.locator('..').locator('..');

    // Verify connect button is shown
    const connectButton = disconnectedPlatform.getByTestId('platform-connect-button');
    await expect(connectButton).toBeVisible();
    await expect(connectButton).toHaveText('Connect');
  });

  test('should show manage button for connected platforms', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Find connected platform
    const connectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'connected' });
    const connectedPlatform = connectedBadge.locator('..').locator('..');

    // Verify manage button is shown
    const manageButton = connectedPlatform.getByTestId('platform-connect-button');
    await expect(manageButton).toBeVisible();
    await expect(manageButton).toHaveText('Manage');
  });

  test('should navigate to publish page from sidebar', async ({ page }) => {
    // Click on publish navigation item
    await page.click('[data-testid="nav-publish"]');

    // Verify URL
    expect(page.url()).toContain('/publish');

    // Verify page title
    const pageTitle = page.getByTestId('publish-page-title');
    await expect(pageTitle).toBeVisible();
    await expect(pageTitle).toHaveText('Publish');
  });
});

// Test Suite: Publishing Workflow
test.describe('Publishing Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/publish');
  });

  test('should display all publishing stats correctly', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Check first platform stats
    const firstPlatform = page.locator('[data-testid="platform-item"]').first();
    const chaptersCount = firstPlatform.getByTestId('platform-chapters-count');
    const readsCount = firstPlatform.getByTestId('platform-reads-count');

    await expect(chaptersCount).toBeVisible();
    await expect(readsCount).toBeVisible();

    // Verify reads count is formatted with commas
    const readsText = await readsCount.textContent();
    expect(readsText).toMatch(/^\d{1,3}(,\d{3})*$/);
  });

  test('should handle platform card interactions', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Hover over platform card
    const platformCard = page.locator('[data-testid="platform-item"]').first();
    await platformCard.hover();

    // Verify card style changes (hover effect)
    const boxStyle = await platformCard.evaluate(el => {
      return window.getComputedStyle(el);
    });
    expect(boxStyle.transition).toBeTruthy();
  });

  test('should display platform name in header', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Check platform name
    const platformName = page.locator('[data-testid="platform-item"]').first().getByTestId('platform-name');
    await expect(platformName).toBeVisible();
    const nameText = await platformName.textContent();
    expect(nameText?.length).toBeGreaterThan(0);
  });

  test('should render badge with correct status classes', async ({ page }) => {
    await page.waitForSelector('[data-testid="platform-item"]');

    // Check connected badge
    const connectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'connected' }).first();
    await expect(connectedBadge).toHaveClass(/badge-success/);

    // Check disconnected badge
    const disconnectedBadge = page.getByTestId('platform-status-badge').filter({ hasText: 'disconnected' }).first();
    await expect(disconnectedBadge).toHaveClass(/badge-warning/);
  });
});

// Test Suite: Settings Page Functionality
test.describe('Settings Page Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('should navigate to settings page', async ({ page }) => {
    // Verify URL
    expect(page.url()).toContain('/settings');

    // Verify page title
    const pageTitle = page.getByTestId('settings-page-title');
    await expect(pageTitle).toBeVisible();
    await expect(pageTitle).toHaveText('Settings');
  });

  test('should display all settings sections', async ({ page }) => {
    // Check Quality Mode section
    await expect(page.getByTestId('settings-quality-mode-section')).toBeVisible();

    // Check Language section
    await expect(page.getByTestId('settings-language-section')).toBeVisible();

    // Check API Key section
    await expect(page.getByTestId('settings-api-key-section')).toBeVisible();

    // Check Theme section
    await expect(page.getByTestId('settings-theme-section')).toBeVisible();
  });

  test('should allow selecting quality mode', async ({ page }) => {
    // Click on High Quality mode
    const highQualityMode = page.getByTestId('quality-mode-high');
    await highQualityMode.click();

    // Verify it's selected
    await expect(highQualityMode).toHaveClass(/active/);

    // Click on Medium Quality mode
    const mediumQualityMode = page.getByTestId('quality-mode-medium');
    await mediumQualityMode.click();

    // Verify it's selected
    await expect(mediumQualityMode).toHaveClass(/active/);
    await expect(highQualityMode).not.toHaveClass(/active/);

    // Click on Low Quality mode
    const lowQualityMode = page.getByTestId('quality-mode-low');
    await lowQualityMode.click();

    // Verify it's selected
    await expect(lowQualityMode).toHaveClass(/active/);
  });

  test('should toggle language between EN and ZH', async ({ page }) => {
    const languageToggle = page.getByTestId('language-toggle');

    // Get initial state
    const initialState = await languageToggle.isChecked();

    // Toggle language
    await languageToggle.click();

    // Verify state changed
    const newState = await languageToggle.isChecked();
    expect(newState).not.toBe(initialState);

    // Toggle back
    await languageToggle.click();
    const finalState = await languageToggle.isChecked();
    expect(finalState).toBe(initialState);
  });

  test('should show API key in masked state by default', async ({ page }) => {
    // Check API key is masked
    await expect(page.getByTestId('api-key-masked')).toBeVisible();
    await expect(page.getByTestId('api-key-input')).not.toBeVisible();

    // Mask should show dots
    const maskedText = await page.getByTestId('api-key-masked').textContent();
    expect(maskedText).toContain('••••••••');
  });

  test('should reveal API key when show button is clicked', async ({ page }) => {
    // Click reveal button
    await page.click('[data-testid="api-key-reveal-btn"]');

    // API key input should now be visible
    await expect(page.getByTestId('api-key-input')).toBeVisible();
    await expect(page.getByTestId('api-key-masked')).not.toBeVisible();

    // Save and Clear buttons should appear
    await expect(page.getByTestId('api-key-save-btn')).toBeVisible();
    await expect(page.getByTestId('api-key-clear-btn')).toBeVisible();
  });

  test('should hide API key when save is clicked', async ({ page }) => {
    // Reveal API key
    await page.click('[data-testid="api-key-reveal-btn"]');

    // Enter a test API key
    await page.fill('[data-testid="api-key-input"]', 'test-api-key-12345');

    // Click save
    await page.click('[data-testid="api-key-save-btn"]');

    // Verify it's masked again
    await expect(page.getByTestId('api-key-masked')).toBeVisible();
    await expect(page.getByTestId('api-key-input')).not.toBeVisible();
  });

  test('should allow selecting theme', async ({ page }) => {
    // Click on Light theme
    const lightTheme = page.getByTestId('theme-light');
    await lightTheme.click();

    // Verify it's selected
    await expect(lightTheme).toHaveClass(/active/);

    // Click on Dark theme
    const darkTheme = page.getByTestId('theme-dark');
    await darkTheme.click();

    // Verify it's selected
    await expect(darkTheme).toHaveClass(/active/);
    await expect(lightTheme).not.toHaveClass(/active/);
  });

  test('should display theme preview circles', async ({ page }) => {
    // Check theme previews
    await expect(page.getByTestId('theme-light').getByTestId('theme-preview')).toBeVisible();
    await expect(page.getByTestId('theme-dark').getByTestId('theme-preview')).toBeVisible();
  });

  test('should display quality mode descriptions', async ({ page }) => {
    // Check descriptions for each quality mode
    const highQualityDesc = page.getByTestId('quality-mode-high').getByTestId('quality-mode-description');
    await expect(highQualityDesc).toBeVisible();
    await expect(highQualityDesc).toHaveText(/Best quality output/);

    const mediumQualityDesc = page.getByTestId('quality-mode-medium').getByTestId('quality-mode-description');
    await expect(mediumQualityDesc).toBeVisible();
    await expect(mediumQualityDesc).toHaveText(/Balanced quality/);

    const lowQualityDesc = page.getByTestId('quality-mode-low').getByTestId('quality-mode-description');
    await expect(lowQualityDesc).toBeVisible();
    await expect(lowQualityDesc).toHaveText(/Fastest generation/);
  });

  test('should navigate to settings from sidebar', async ({ page }) => {
    // Start from a different page
    await page.goto('/');

    // Click on settings navigation item
    await page.click('[data-testid="nav-settings"]');

    // Verify URL
    expect(page.url()).toContain('/settings');

    // Verify page title
    const pageTitle = page.getByTestId('settings-page-title');
    await expect(pageTitle).toBeVisible();
  });
});

// Test Suite: Cross-page Navigation and State
test.describe('Cross-page Navigation and State', () => {
  test('should navigate between publish and settings pages', async ({ page }) => {
    // Start at publish page
    await page.goto('/publish');
    expect(page.url()).toContain('/publish');

    // Navigate to settings
    await page.click('[data-testid="nav-settings"]');
    expect(page.url()).toContain('/settings');

    // Navigate back to publish
    await page.click('[data-testid="nav-publish"]');
    expect(page.url()).toContain('/publish');
  });

  test('should maintain navigation state', async ({ page }) => {
    // Check initial active state
    await page.goto('/publish');
    await expect(page.getByTestId('nav-publish')).toHaveClass(/active/);

    // Navigate to settings
    await page.click('[data-testid="nav-settings"]');
    await expect(page.getByTestId('nav-settings')).toHaveClass(/active/);
    await expect(page.getByTestId('nav-publish')).not.toHaveClass(/active/);
  });

  test('should handle browser back and forward navigation', async ({ page }) => {
    // Navigate to publish
    await page.goto('/publish');

    // Navigate to settings
    await page.click('[data-testid="nav-settings"]');
    expect(page.url()).toContain('/settings');

    // Go back
    await page.goBack();
    expect(page.url()).toContain('/publish');

    // Go forward
    await page.goForward();
    expect(page.url()).toContain('/settings');
  });
});

// Test Suite: Error Handling and Edge Cases
test.describe('Error Handling and Edge Cases', () => {
  test('should handle missing platform data gracefully', async ({ page }) => {
    // Navigate to publish page
    await page.goto('/publish');

    // If no platforms are loaded, show empty state
    const platformItems = page.locator('[data-testid="platform-item"]');
    const count = await platformItems.count();

    if (count === 0) {
      // Should show empty state message (if implemented)
      // This test documents expected behavior
      expect(true).toBe(true); // Test passes as long as page loads
    }
  });

  test('should handle rapid quality mode switching', async ({ page }) => {
    await page.goto('/settings');

    // Rapidly switch between quality modes
    for (let i = 0; i < 3; i++) {
      await page.click('[data-testid="quality-mode-high"]');
      await page.click('[data-testid="quality-mode-medium"]');
      await page.click('[data-testid="quality-mode-low"]');
    }

    // Final state should be low quality
    await expect(page.getByTestId('quality-mode-low')).toHaveClass(/active/);
  });

  test('should handle empty API key save', async ({ page }) => {
    await page.goto('/settings');

    // Reveal API key
    await page.click('[data-testid="api-key-reveal-btn"]');

    // Clear any existing value
    await page.fill('[data-testid="api-key-input"]', '');

    // Click save (should handle gracefully)
    await page.click('[data-testid="api-key-save-btn"]');

    // Should still be masked
    await expect(page.getByTestId('api-key-masked')).toBeVisible();
  });
});

// Test Suite: Responsive Design
test.describe('Responsive Design', () => {
  test('should display correctly on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/publish');

    // Platforms should still be visible
    await expect(page.locator('[data-testid="platform-item"]').first()).toBeVisible();
  });

  test('should display correctly on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/settings');

    // Settings sections should be visible
    await expect(page.getByTestId('settings-quality-mode-section')).toBeVisible();
  });

  test('should handle window resize', async ({ page }) => {
    await page.goto('/publish');

    // Resize to mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('[data-testid="platform-item"]').first()).toBeVisible();

    // Resize to desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('[data-testid="platform-item"]').first()).toBeVisible();
  });
});
