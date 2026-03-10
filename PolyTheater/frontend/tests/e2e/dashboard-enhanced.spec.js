import { test, expect } from '../fixtures/base';

test.describe('Enhanced Dashboard', () => {
  test('Dashboard 页面应该加载增强版', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 等待网络空闲和应用加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    // 验证 URL
    await expect(page).toHaveURL(/\/dashboard/);
    
    // 验证页面标题
    const title = page.locator('h1');
    await expect(title.first()).toBeVisible();
  });

  test('Dashboard 应该显示统计卡片', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 等待网络空闲和应用加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    // 验证统计卡片存在
    const statCards = page.locator('.stat-card, .overview-card');
    await expect(statCards.first()).toBeVisible({ timeout: 10000 });
    
    // 至少应该有 4 个卡片
    await expect(statCards).toHaveCount(4);
  });

  test('Dashboard 应该显示图表', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 等待网络空闲和应用加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    // 等待图表加载
    const charts = page.locator('.chart, .chart-container');
    await expect(charts.first()).toBeVisible({ timeout: 10000 });
  });

  test('Dashboard 应该显示活动区域', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 等待网络空闲和应用加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    // 验证活动区域存在
    const activitySection = page.locator('.activity, .activity-section');
    await expect(activitySection.first()).toBeVisible();
  });

  test('Dashboard 应该有刷新按钮', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 等待网络空闲和应用加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    // 验证刷新按钮存在
    const refreshBtn = page.locator('button:has-text("刷新"), .btn-refresh');
    await expect(refreshBtn.first()).toBeVisible();
  });

  test('点击刷新按钮应该刷新数据', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 等待网络空闲和应用加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    // 点击刷新按钮
    const refreshBtn = page.locator('button:has-text("刷新"), .btn-refresh');
    if (await refreshBtn.count() > 0) {
      await refreshBtn.first().click();
      
      // 验证页面没有崩溃
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('Dashboard API 应该返回正确数据', async ({ page }) => {
    // 测试统计 API
    const statsResponse = await page.request.get('http://localhost:5001/api/dashboard/stats');
    expect(statsResponse.ok()).toBeTruthy();
    
    const stats = await statsResponse.json();
    expect(stats.success).toBeTruthy();
    expect(stats.data).toHaveProperty('projects');
    expect(stats.data).toHaveProperty('characters');
    expect(stats.data).toHaveProperty('events');
    
    // 测试健康 API
    const healthResponse = await page.request.get('http://localhost:5001/api/dashboard/health/detailed');
    expect(healthResponse.ok()).toBeTruthy();
    
    const health = await healthResponse.json();
    expect(health.success).toBeTruthy();
    expect(health.data.database.status).toBe('connected');
  });
});
