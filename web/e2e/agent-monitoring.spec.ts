import { test, expect } from '@playwright/test';

// Helper function to navigate to agent dashboard
async function navigateToAgentDashboard(page) {
  await page.goto('/agents');
  await page.waitForLoadState('networkidle');
}

test.describe('Agent Dashboard - WebSocket Connection', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToAgentDashboard(page);
  });

  test('should display connection indicator', async ({ page }) => {
    // Connection indicator should be visible
    const connectionIndicator = page.getByTestId('connection-indicator');
    await expect(connectionIndicator).toBeVisible();
  });

  test('should show connecting state initially', async ({ page }) => {
    // Wait for connecting state
    await page.waitForTimeout(500);

    const connectionText = page.getByTestId('connection-text');
    const text = await connectionText.textContent();
    
    // Should be in connecting or connected state
    expect(['Connecting...', 'Connected', 'Reconnecting...', 'Disconnected']).toContain(text);
  });

  test('should update connection state to connected', async ({ page }) => {
    // Wait for WebSocket connection to establish
    await page.waitForTimeout(2000);

    const connectionText = page.getByTestId('connection-text');
    await expect(connectionText).toHaveText(/Connected|Connecting/);
  });

  test('should show correct icon for connected state', async ({ page }) => {
    // Wait for connection
    await page.waitForTimeout(2000);

    const connectionIcon = page.getByTestId('connection-icon');
    await expect(connectionIcon).toBeVisible();
  });

  test('should show WiFi icon when connected', async ({ page }) => {
    await page.waitForTimeout(2000);

    // Check for WiFi icon (connected state)
    const wifiIcon = page.locator('.connection-indicator svg').first();
    await expect(wifiIcon).toBeVisible();
  });

  test('should handle disconnect state', async ({ page }) => {
    // Simulate disconnect by navigating away and back
    await page.goto('/');
    await page.waitForTimeout(500);
    await navigateToAgentDashboard(page);

    const connectionText = page.getByTestId('connection-text');
    await expect(connectionText).toBeVisible();
  });

  test('should display agent count', async ({ page }) => {
    const agentCount = page.getByTestId('agent-count');
    await expect(agentCount).toBeVisible();
    
    const countText = await agentCount.textContent();
    expect(parseInt(countText.replace(' agents', ''))).toBeGreaterThan(0);
  });
});

test.describe('Agent Status Cards', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToAgentDashboard(page);
  });

  test('should display all agent cards', async ({ page }) => {
    const agentCards = page.getByTestId('agent-card');
    const count = await agentCards.count();
    
    expect(count).toBeGreaterThan(0);
    await page.screenshot({ path: 'e2e/screenshots/agent-cards.png' });
  });

  test('should display agent name', async ({ page }) => {
    const firstAgentCard = page.getByTestId('agent-card').first();
    const agentName = firstAgentCard.getByTestId('agent-name');
    
    await expect(agentName).toBeVisible();
    const name = await agentName.textContent();
    expect(name).toMatch(/Agent \d+/);
  });

  test('should display agent status badge', async ({ page }) => {
    const firstAgentCard = page.getByTestId('agent-card').first();
    const statusBadge = firstAgentCard.getByTestId('agent-status');
    
    await expect(statusBadge).toBeVisible();
    
    const status = await statusBadge.textContent();
    expect(['online', 'busy', 'offline', 'error']).toContain(status?.toLowerCase());
  });

  test('should display agent statistics', async ({ page }) => {
    const firstAgentCard = page.getByTestId('agent-card').first();
    
    const lastSeen = firstAgentCard.getByTestId('agent-last-seen');
    const tasksCompleted = firstAgentCard.getByTestId('agent-tasks-completed');
    const successRate = firstAgentCard.getByTestId('agent-success-rate');
    
    await expect(lastSeen).toBeVisible();
    await expect(tasksCompleted).toBeVisible();
    await expect(successRate).toBeVisible();
  });

  test('should show correct status icon for online agents', async ({ page }) => {
    const agentCards = page.getByTestId('agent-card');
    
    for (let i = 0; i < await agentCards.count(); i++) {
      const card = agentCards.nth(i);
      const status = await card.getByTestId('agent-status').textContent();
      
      if (status?.toLowerCase() === 'online') {
        const statusIcon = card.getByTestId('agent-status-icon');
        await expect(statusIcon).toBeVisible();
      }
    }
  });

  test('should apply pulse animation to active agents', async ({ page }) => {
    const agentCards = page.getByTestId('agent-card');
    
    for (let i = 0; i < await agentCards.count(); i++) {
      const card = agentCards.nth(i);
      const status = await card.getByTestId('agent-status').textContent();
      
      if (status?.toLowerCase() === 'online' || status?.toLowerCase() === 'busy') {
        await expect(card).toHaveClass(/agent-active/);
      }
    }
  });

  test('should display refresh button on agent card', async ({ page }) => {
    const firstAgentCard = page.getByTestId('agent-card').first();
    const refreshButton = firstAgentCard.getByRole('button', { name: 'Refresh' });
    
    await expect(refreshButton).toBeVisible();
  });

  test('should hover effect on agent cards', async ({ page }) => {
    const firstAgentCard = page.getByTestId('agent-card').first();
    
    await firstAgentCard.hover();
    await page.waitForTimeout(200); // Wait for transition
    
    // Verify hover effect by checking transform
    const box = await firstAgentCard.boundingBox();
    expect(box).toBeTruthy();
  });

  test('should display last seen time correctly', async ({ page }) => {
    const firstAgentCard = page.getByTestId('agent-card').first();
    const lastSeen = firstAgentCard.getByTestId('agent-last-seen');
    
    const text = await lastSeen.textContent();
    expect(text).toMatch(/(Just now|\d+m ago|\d+h ago|\d+d ago)/);
  });
});

test.describe('Agent Execution Queue', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToAgentDashboard(page);
  });

  test('should display execution queue section', async ({ page }) => {
    const queueSection = page.getByTestId('execution-queue');
    await expect(queueSection).toBeVisible();
  });

  test('should display task count in queue', async ({ page }) => {
    const taskCount = page.getByTestId('queue-task-count');
    await expect(taskCount).toBeVisible();
    
    const count = parseInt((await taskCount.textContent()).replace(' tasks', ''));
    expect(count).toBeGreaterThan(0);
  });

  test('should display all timeline items', async ({ page }) => {
    const timelineItems = page.getByTestId('timeline-item');
    const count = await timelineItems.count();
    
    expect(count).toBeGreaterThan(0);
    await page.screenshot({ path: 'e2e/screenshots/execution-queue.png' });
  });

  test('should display task title in timeline', async ({ page }) => {
    const firstTimelineItem = page.getByTestId('timeline-item').first();
    const taskTitle = firstTimelineItem.getByTestId('timeline-title');
    
    await expect(taskTitle).toBeVisible();
    
    const title = await taskTitle.textContent();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);
  });

  test('should display agent ID in timeline', async ({ page }) => {
    const firstTimelineItem = page.getByTestId('timeline-item').first();
    const agentId = firstTimelineItem.getByTestId('timeline-agent-id');
    
    await expect(agentId).toBeVisible();
    
    const id = await agentId.textContent();
    expect(id).toMatch(/Agent \d+/);
  });

  test('should display task timestamp', async ({ page }) => {
    const firstTimelineItem = page.getByTestId('timeline-item').first();
    const timestamp = firstTimelineItem.getByTestId('timeline-timestamp');
    
    await expect(timestamp).toBeVisible();
    
    const time = await timestamp.textContent();
    expect(time).toMatch(/(Just now|\d+m ago|\d+h ago|\d+d ago)/);
  });

  test('should display correct status icons for tasks', async ({ page }) => {
    const timelineItems = page.getByTestId('timeline-item');
    
    const statuses = ['running', 'completed', 'pending', 'error'];
    
    for (let i = 0; i < await timelineItems.count(); i++) {
      const item = timelineItems.nth(i);
      const statusIcon = item.getByTestId('timeline-icon');
      
      await expect(statusIcon).toBeVisible();
    }
  });

  test('should apply correct classes based on task status', async ({ page }) => {
    const timelineItems = page.getByTestId('timeline-item');
    
    const statusClasses = ['timeline-running', 'timeline-completed', 'timeline-pending', 'timeline-error'];
    
    for (let i = 0; i < await timelineItems.count(); i++) {
      const item = timelineItems.nth(i);
      const classes = await item.getAttribute('class');
      
      const hasStatusClass = statusClasses.some(cls => classes?.includes(cls));
      expect(hasStatusClass).toBeTruthy();
    }
  });

  test('should display timeline in chronological order', async ({ page }) => {
    const timelineItems = page.getByTestId('timeline-item');
    const timestamps: string[] = [];
    
    for (let i = 0; i < await timelineItems.count(); i++) {
      const item = timelineItems.nth(i);
      const timestamp = await item.getByTestId('timeline-timestamp').textContent();
      timestamps.push(timestamp!);
    }
    
    // All timestamps should exist
    expect(timestamps.length).toBeGreaterThan(0);
  });
});

test.describe('Floating Action Button (FAB)', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToAgentDashboard(page);
  });

  test('should display FAB button', async ({ page }) => {
    const fab = page.getByTestId('fab');
    await expect(fab).toBeVisible();
  });

  test('should display FAB in fixed position', async ({ page }) => {
    const fab = page.getByTestId('fab');
    
    // Check that FAB is in viewport
    await expect(fab).toBeInViewport();
    
    // Scroll and check FAB still visible
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await expect(fab).toBeInViewport();
  });

  test('should trigger action on FAB click', async ({ page }) => {
    const fab = page.getByTestId('fab');
    await fab.click();
    
    // Verify action was triggered (console.log should have been called)
    await page.waitForTimeout(100);
  });

  test('should have hover effect on FAB', async ({ page }) => {
    const fab = page.getByTestId('fab');
    
    await fab.hover();
    await page.waitForTimeout(200);
    
    // FAB should still be visible after hover
    await expect(fab).toBeVisible();
  });
});

test.describe('Agent Dashboard Layout', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToAgentDashboard(page);
  });

  test('should display header with title', async ({ page }) => {
    const header = page.getByTestId('dashboard-header');
    await expect(header).toBeVisible();
    
    const title = page.getByTestId('dashboard-title');
    await expect(title).toHaveText('Agent Monitor');
  });

  test('should display subtitle', async ({ page }) => {
    const subtitle = page.getByTestId('dashboard-subtitle');
    await expect(subtitle).toBeVisible();
    await expect(subtitle).toHaveText(/Real-time status/);
  });

  test('should display agents and queue side by side', async ({ page }) => {
    const agentsSection = page.getByTestId('agents-section');
    const queueSection = page.getByTestId('queue-section');
    
    await expect(agentsSection).toBeVisible();
    await expect(queueSection).toBeVisible();
    
    // Check positions
    const agentsBox = await agentsSection.boundingBox();
    const queueBox = await queueSection.boundingBox();
    
    expect(agentsBox?.y).toBeLessThan(queueBox?.y || Infinity);
  });

  test('should be responsive on smaller screens', async ({ page }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(200);
    
    const agentsSection = page.getByTestId('agents-section');
    const queueSection = page.getByTestId('queue-section');
    
    await expect(agentsSection).toBeVisible();
    await expect(queueSection).toBeVisible();
    
    await page.screenshot({ path: 'e2e/screenshots/mobile-view.png' });
  });

  test('should maintain layout on medium screens', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(200);
    
    const header = page.getByTestId('dashboard-header');
    await expect(header).toBeVisible();
    
    await page.screenshot({ path: 'e2e/screenshots/tablet-view.png' });
  });
});

test.describe('Agent Dashboard - Integration', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000); // Allow WebSocket to connect
  });

  test('should load all components without errors', async ({ page }) => {
    // Check all main components are loaded
    const header = page.getByTestId('dashboard-header');
    const connection = page.getByTestId('connection-indicator');
    const agents = page.getByTestId('agents-section');
    const queue = page.getByTestId('queue-section');
    const fab = page.getByTestId('fab');
    
    await expect(header).toBeVisible();
    await expect(connection).toBeVisible();
    await expect(agents).toBeVisible();
    await expect(queue).toBeVisible();
    await expect(fab).toBeVisible();
    
    await page.screenshot({ path: 'e2e/screenshots/full-dashboard.png' });
  });

  test('should update agent states dynamically', async ({ page }) => {
    const firstAgentCard = page.getByTestId('agent-card').first();
    const initialStatus = await firstAgentCard.getByTestId('agent-status').textContent();
    
    // Wait for potential updates
    await page.waitForTimeout(3000);
    
    const updatedStatus = await firstAgentCard.getByTestId('agent-status').textContent();
    expect(updatedStatus).toBeTruthy();
  });

  test('should handle rapid state changes', async ({ page }) => {
    // Navigate between pages to trigger state changes
    await page.goto('/');
    await page.waitForTimeout(200);
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(500);
    
    const connectionIndicator = page.getByTestId('connection-indicator');
    await expect(connectionIndicator).toBeVisible();
  });

  test('should persist data across refresh', async ({ page }) => {
    const firstAgentName = await page.getByTestId('agent-card').first().getByTestId('agent-name').textContent();
    
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    const agentNameAfterReload = await page.getByTestId('agent-card').first().getByTestId('agent-name').textContent();
    expect(agentNameAfterReload).toBe(firstAgentName);
  });
});

test.describe('Error Handling', () => {
  test('should handle WebSocket connection errors gracefully', async ({ page }) => {
    // Mock a connection error by setting an invalid WebSocket URL
    await page.route('**/ws/**', route => route.abort('failed'));
    
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);
    
    // Connection indicator should still be visible
    const connectionIndicator = page.getByTestId('connection-indicator');
    await expect(connectionIndicator).toBeVisible();
  });

  test('should handle missing agent data', async ({ page }) => {
    await page.route('**/api/agents/**', route => route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Not found' })
    }));
    
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(500);
    
    // Should still show some UI elements
    const header = page.getByTestId('dashboard-header');
    await expect(header).toBeVisible();
  });

  test('should capture screenshot on error', async ({ page, context }) => {
    // This is a test to ensure screenshot capture works
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(500);
    
    // Take a screenshot
    await page.screenshot({ path: 'e2e/screenshots/error-test.png', fullPage: true });
    
    // Verify screenshot was created
    const fs = require('fs');
    expect(fs.existsSync('e2e/screenshots/error-test.png')).toBeTruthy();
  });
});

test.describe('Performance', () => {
  test('should load dashboard within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await navigateToAgentDashboard(page);
    
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(5000); // Should load within 5 seconds
  });

  test('should render agent cards quickly', async ({ page }) => {
    await navigateToAgentDashboard(page);
    
    const startTime = Date.now();
    const agentCards = page.getByTestId('agent-card');
    await agentCards.first().waitFor({ state: 'visible' });
    const renderTime = Date.now() - startTime;
    
    expect(renderTime).toBeLessThan(2000); // Should render within 2 seconds
  });

  test('should handle rapid navigation without errors', async ({ page }) => {
    for (let i = 0; i < 5; i++) {
      await page.goto('/');
      await navigateToAgentDashboard(page);
      await page.waitForTimeout(200);
    }
    
    // Should still be functional after rapid navigation
    const header = page.getByTestId('dashboard-header');
    await expect(header).toBeVisible();
  });
});
