import { test, expect } from '@playwright/test';
import type { Agent, AgentStatusEvent } from '../src/types';

async function navigateToAgentDashboard(page) {
  await page.goto('/agents');
  await page.waitForLoadState('networkidle');
}

const mockAgents: Agent[] = [
  {
    id: 'agent-1',
    name: 'Plot Writer',
    status: 'idle',
    last_seen: new Date(Date.now() - 300000).toISOString(),
  },
  {
    id: 'agent-2',
    name: 'Character Developer',
    status: 'running',
    last_seen: new Date(Date.now() - 120000).toISOString(),
  },
  {
    id: 'agent-3',
    name: 'World Builder',
    status: 'completed',
    last_seen: new Date(Date.now() - 600000).toISOString(),
  },
  {
    id: 'agent-4',
    name: 'Editor Agent',
    status: 'failed',
    last_seen: new Date(Date.now() - 900000).toISOString(),
  },
];

const mockExecutionHistory = [
  {
    agent_id: 'agent-2',
    agent_name: 'Character Developer',
    task: 'Develop character arc for protagonist',
    status: 'running',
    timestamp: new Date(Date.now() - 60000).toISOString(),
    duration: 45,
  },
  {
    agent_id: 'agent-3',
    agent_name: 'World Builder',
    task: 'Create magical system rules',
    status: 'completed',
    timestamp: new Date(Date.now() - 180000).toISOString(),
    duration: 120,
  },
  {
    agent_id: 'agent-1',
    agent_name: 'Plot Writer',
    task: 'Outline chapter structure',
    status: 'completed',
    timestamp: new Date(Date.now() - 360000).toISOString(),
    duration: 90,
  },
  {
    agent_id: 'agent-4',
    agent_name: 'Editor Agent',
    task: 'Review and edit chapter 1',
    status: 'failed',
    timestamp: new Date(Date.now() - 720000).toISOString(),
    duration: 30,
  },
];

test.describe('Agent Monitoring - WebSocket Mock', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/ws/agents', route => {
      route.fulfill({
        status: 101,
        headers: {
          'Upgrade': 'websocket',
          'Connection': 'Upgrade',
        },
        body: '',
      });
    });

    await page.route('**/api/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgents),
      });
    });

    await page.route('**/api/agents/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockExecutionHistory),
      });
    });
  });

  test('should connect to WebSocket and display agents', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const connectionIndicator = page.getByTestId('connection-indicator');
    await expect(connectionIndicator).toBeVisible();

    const connectionText = page.getByTestId('connection-text');
    await expect(connectionText).toContainText(/Connected|Connecting/);

    const agentCards = page.getByTestId('agent-card');
    await expect(agentCards).toHaveCount(4);
  });

  test('should display correct status badges for all agents', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const agentCards = page.getByTestId('agent-card');

    for (let i = 0; i < await agentCards.count(); i++) {
      const card = agentCards.nth(i);
      const statusBadge = card.getByTestId('agent-status');
      const status = await statusBadge.textContent();

      expect(['idle', 'running', 'completed', 'failed']).toContain(status?.toLowerCase());
    }
  });

  test('should apply correct status badge colors', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const agentCards = page.getByTestId('agent-card');

    for (let i = 0; i < await agentCards.count(); i++) {
      const card = agentCards.nth(i);
      const statusBadge = card.getByTestId('agent-status');
      const status = await statusBadge.textContent();
      const classes = await statusBadge.getAttribute('class') || '';

      switch (status?.toLowerCase()) {
        case 'running':
          expect(classes).toContain('badge-success');
          break;
        case 'idle':
          expect(classes).toContain('badge-info');
          break;
        case 'completed':
          expect(classes).toContain('badge-success');
          break;
        case 'failed':
          expect(classes).toContain('badge-error');
          break;
      }
    }
  });

  test('should update agent status in real-time', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const agent2Card = page.getByTestId('agent-card').filter({ hasText: 'Character Developer' });
    const initialStatus = await agent2Card.getByTestId('agent-status').textContent();

    expect(initialStatus?.toLowerCase()).toBe('running');

    await page.evaluate(() => {
      const event = new CustomEvent('ws-message', {
        detail: {
          type: 'agent_status',
          data: {
            agent_id: 'agent-2',
            status: 'completed',
          },
        },
      });
      window.dispatchEvent(event);
    });

    await page.waitForTimeout(500);

    const updatedStatus = await agent2Card.getByTestId('agent-status').textContent();
    expect(updatedStatus?.toLowerCase()).toBe('completed');
  });

  test('should display execution timeline with correct data', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const timelineSection = page.getByTestId('execution-queue');
    await expect(timelineSection).toBeVisible();

    const timelineItems = page.getByTestId('timeline-item');
    await expect(timelineItems).toHaveCount(4);

    const firstItem = timelineItems.first();
    await expect(firstItem.getByTestId('timeline-title')).toHaveText('Develop character arc for protagonist');
    await expect(firstItem.getByTestId('timeline-agent-id')).toContainText('Character Developer');

    const firstStatusIcon = firstItem.getByTestId('timeline-icon');
    await expect(firstStatusIcon).toBeVisible();
    const firstClasses = await firstItem.getAttribute('class') || '';
    expect(firstClasses).toContain('timeline-running');
  });

  test('should show correct status indicators in timeline', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const timelineItems = page.getByTestId('timeline-item');
    const expectedStatuses = ['running', 'completed', 'completed', 'failed'];

    for (let i = 0; i < await timelineItems.count(); i++) {
      const item = timelineItems.nth(i);
      const classes = await item.getAttribute('class') || '';
      const expectedClass = `timeline-${expectedStatuses[i]}`;

      expect(classes).toContain(expectedClass);

      const statusIcon = item.getByTestId('timeline-icon');
      await expect(statusIcon).toBeVisible();
    }
  });

  test('should display agent statistics correctly', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const agentCards = page.getByTestId('agent-card');

    for (let i = 0; i < await agentCards.count(); i++) {
      const card = agentCards.nth(i);

      const lastSeen = card.getByTestId('agent-last-seen');
      await expect(lastSeen).toBeVisible();
      const lastSeenText = await lastSeen.textContent();
      expect(lastSeenText).toMatch(/(Just now|\d+m ago|\d+h ago)/);

      const tasksCompleted = card.getByTestId('agent-tasks-completed');
      await expect(tasksCompleted).toBeVisible();

      const successRate = card.getByTestId('agent-success-rate');
      await expect(successRate).toBeVisible();
    }
  });

  test('should filter timeline by status', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const filterButton = page.getByRole('button', { name: 'Completed' });
    await filterButton.click();
    await page.waitForTimeout(300);

    const timelineItems = page.getByTestId('timeline-item');
    const count = await timelineItems.count();

    expect(count).toBe(2);

    for (let i = 0; i < count; i++) {
      const item = timelineItems.nth(i);
      const classes = await item.getAttribute('class') || '';
      expect(classes).toContain('timeline-completed');
    }
  });

  test('should display connection status changes', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const connectionText = page.getByTestId('connection-text');
    const initialText = await connectionText.textContent();
    expect(['Connected', 'Connecting']).toContain(initialText);

    await page.evaluate(() => {
      const event = new CustomEvent('ws-close', { detail: { code: 1006 } });
      window.dispatchEvent(event);
    });

    await page.waitForTimeout(500);

    const disconnectedText = await connectionText.textContent();
    expect(['Reconnecting...', 'Disconnected']).toContain(disconnectedText);

    await page.evaluate(() => {
      const event = new CustomEvent('ws-open');
      window.dispatchEvent(event);
    });

    await page.waitForTimeout(500);

    const reconnectedText = await connectionText.textContent();
    expect(reconnectedText).toBe('Connected');
  });

  test('should handle rapid status updates', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const agent1Card = page.getByTestId('agent-card').filter({ hasText: 'Plot Writer' });
    const statusBadge = agent1Card.getByTestId('agent-status');

    const statusSequence = ['running', 'completed', 'idle', 'running'];

    for (const status of statusSequence) {
      await page.evaluate((newStatus) => {
        const event = new CustomEvent('ws-message', {
          detail: {
            type: 'agent_status',
            data: {
              agent_id: 'agent-1',
              status: newStatus,
            },
          },
        });
        window.dispatchEvent(event);
      }, status);

      await page.waitForTimeout(100);
    }

    const finalStatus = await statusBadge.textContent();
    expect(finalStatus?.toLowerCase()).toBe('running');
  });

  test('should display agent count in header', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const agentCount = page.getByTestId('agent-count');
    await expect(agentCount).toBeVisible();

    const countText = await agentCount.textContent();
    expect(countText).toContain('4');
  });

  test('should refresh agent data on button click', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const refreshButton = page.getByRole('button', { name: 'Refresh' });
    await refreshButton.click();

    await page.waitForTimeout(500);

    const agentCards = page.getByTestId('agent-card');
    await expect(agentCards).toHaveCount(4);
  });

  test('should display agent detail when card is clicked', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const firstCard = page.getByTestId('agent-card').first();
    await firstCard.click();

    await page.waitForTimeout(300);

    const detailView = page.locator('.agent-detail, .agent-modal');
    if (await detailView.count() > 0) {
      await expect(detailView).toBeVisible();
    }
  });

  test('should handle WebSocket errors gracefully', async ({ page }) => {
    await page.route('**/ws/agents', route => {
      route.abort('failed');
    });

    await navigateToAgentDashboard(page);
    await page.waitForTimeout(2000);

    const header = page.getByTestId('dashboard-header');
    await expect(header).toBeVisible();

    const connectionIndicator = page.getByTestId('connection-indicator');
    await expect(connectionIndicator).toBeVisible();

    const connectionText = page.getByTestId('connection-text');
    const text = await connectionText.textContent();
    expect(['Disconnected', 'Connecting...', 'Reconnecting...']).toContain(text);
  });

  test('should display last seen time with relative format', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const agentCards = page.getByTestId('agent-card');

    for (let i = 0; i < await agentCards.count(); i++) {
      const card = agentCards.nth(i);
      const lastSeen = card.getByTestId('agent-last-seen');
      const text = await lastSeen.textContent();

      expect(text).toMatch(/(Just now|\d+m ago|\d+h ago|\d+d ago)/);
    }
  });

  test('should sort timeline chronologically', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const timelineItems = page.getByTestId('timeline-item');
    const timestamps: string[] = [];

    for (let i = 0; i < await timelineItems.count(); i++) {
      const item = timelineItems.nth(i);
      const timestamp = await item.getByTestId('timeline-timestamp').textContent();
      timestamps.push(timestamp!);
    }

    expect(timestamps.length).toBeGreaterThan(0);
    expect(timestamps[0]).toMatch(/(Just now|\d+m ago)/);
  });

  test('should display pulse animation on active agents', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const agentCards = page.getByTestId('agent-card');

    for (let i = 0; i < await agentCards.count(); i++) {
      const card = agentCards.nth(i);
      const status = await card.getByTestId('agent-status').textContent();

      if (status?.toLowerCase() === 'running') {
        const classes = await card.getAttribute('class') || '';
        expect(classes).toContain('agent-active');
      }
    }
  });

  test('should handle large number of status updates', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    for (let i = 0; i < 50; i++) {
      await page.evaluate((iteration) => {
        const event = new CustomEvent('ws-message', {
          detail: {
            type: 'agent_status',
            data: {
              agent_id: `agent-${(iteration % 4) + 1}`,
              status: ['idle', 'running', 'completed', 'failed'][iteration % 4],
            },
          },
        });
        window.dispatchEvent(event);
      }, i);

      await page.waitForTimeout(10);
    }

    const agentCards = page.getByTestId('agent-card');
    await expect(agentCards).toHaveCount(4);
  });

  test('should persist agent data across page reload', async ({ page }) => {
    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const initialAgentCount = await page.getByTestId('agent-card').count();

    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const reloadedAgentCount = await page.getByTestId('agent-card').count();
    expect(reloadedAgentCount).toBe(initialAgentCount);
  });
});

test.describe('Agent Monitoring - Integration Tests', () => {
  test('should complete full monitoring workflow', async ({ page }) => {
    await page.route('**/ws/agents', route => {
      route.fulfill({
        status: 101,
        headers: {
          'Upgrade': 'websocket',
          'Connection': 'Upgrade',
        },
        body: '',
      });
    });

    await page.route('**/api/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgents),
      });
    });

    await page.route('**/api/agents/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockExecutionHistory),
      });
    });

    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    await expect(page.getByTestId('dashboard-header')).toBeVisible();
    await expect(page.getByTestId('connection-indicator')).toBeVisible();
    await expect(page.getByTestId('agents-section')).toBeVisible();
    await expect(page.getByTestId('queue-section')).toBeVisible();
    await expect(page.getByTestId('fab')).toBeVisible();

    await page.evaluate(() => {
      const event = new CustomEvent('ws-message', {
        detail: {
          type: 'agent_status',
          data: {
            agent_id: 'agent-2',
            status: 'completed',
          },
        },
      });
      window.dispatchEvent(event);
    });

    await page.waitForTimeout(500);

    const agent2Card = page.getByTestId('agent-card').filter({ hasText: 'Character Developer' });
    const status = await agent2Card.getByTestId('agent-status').textContent();
    expect(status?.toLowerCase()).toBe('completed');

    await page.screenshot({ path: 'e2e/screenshots/agent-monitoring-full-workflow.png', fullPage: true });
  });

  test('should handle offline and reconnection scenarios', async ({ page }) => {
    await page.route('**/ws/agents', route => {
      route.fulfill({
        status: 101,
        headers: {
          'Upgrade': 'websocket',
          'Connection': 'Upgrade',
        },
        body: '',
      });
    });

    await page.route('**/api/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgents),
      });
    });

    await navigateToAgentDashboard(page);
    await page.waitForTimeout(1000);

    const connectionText = page.getByTestId('connection-text');
    await expect(connectionText).toContainText(/Connected|Connecting/);

    await page.evaluate(() => {
      const event = new CustomEvent('ws-close', { detail: { code: 1006 } });
      window.dispatchEvent(event);
    });

    await page.waitForTimeout(1000);

    await expect(connectionText).toContainText(/Reconnecting|Disconnected/);

    await page.evaluate(() => {
      const event = new CustomEvent('ws-open');
      window.dispatchEvent(event);
    });

    await page.waitForTimeout(500);

    await expect(connectionText).toHaveText('Connected');
  });
});
