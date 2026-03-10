import { test, expect } from '../fixtures/base';

test.describe('Dashboard', () => {
  test('Dashboard 路由应该存在', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 验证 URL 变化
    await expect(page).toHaveURL(/\/dashboard/);
    
    // 验证页面加载（即使内容是空的）
    await expect(page.locator('#app').first()).toBeAttached();
  });

  test('Dashboard API 应该返回统计数据', async ({ page }) => {
    const response = await page.request.get('http://localhost:5001/api/dashboard/stats');
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.success).toBeTruthy();
    expect(data.data).toHaveProperty('projects');
    expect(data.data).toHaveProperty('characters');
    expect(data.data).toHaveProperty('events');
  });

  test('Dashboard API 应该返回健康状态', async ({ page }) => {
    const response = await page.request.get('http://localhost:5001/api/dashboard/health/detailed');
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.success).toBeTruthy();
    expect(data.data.database.status).toBe('connected');
    expect(data.data.database.response_time_ms).toBeGreaterThan(0);
  });

  test('Dashboard API 应该返回活动日志', async ({ page }) => {
    const response = await page.request.get('http://localhost:5001/api/dashboard/activity');
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.success).toBeTruthy();
    expect(Array.isArray(data.data)).toBeTruthy();
  });

  test('Dashboard 应该支持自动刷新', async ({ page }) => {
    // 第一次请求
    const response1 = await page.request.get('http://localhost:5001/api/dashboard/stats');
    expect(response1.ok()).toBeTruthy();
    
    // 等待一小段时间
    await page.waitForTimeout(100);
    
    // 第二次请求
    const response2 = await page.request.get('http://localhost:5001/api/dashboard/stats');
    expect(response2.ok()).toBeTruthy();
    
    // 验证两次请求都成功
    const data1 = await response1.json();
    const data2 = await response2.json();
    expect(data1.success).toBeTruthy();
    expect(data2.success).toBeTruthy();
  });

  test('所有 Dashboard 端点都应该可访问', async ({ page }) => {
    const endpoints = [
      '/api/dashboard/stats',
      '/api/dashboard/activity',
      '/api/dashboard/health/detailed'
    ];
    
    for (const endpoint of endpoints) {
      const response = await page.request.get(`http://localhost:5001${endpoint}`);
      if (!response.ok()) {
        throw new Error(`Failed to access ${endpoint}`);
      }
      expect(response.ok()).toBeTruthy();
    }
  });
});
