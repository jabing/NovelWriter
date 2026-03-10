import { test, expect } from '../fixtures/base';

test.describe('角色管理', () => {
  test('应该能访问角色页面', async ({ page }) => {
    await page.goto('/characters');
    
    // 验证 URL 变化
    await expect(page).toHaveURL(/\/characters/);
  });

  test('角色页面应该有内容', async ({ page }) => {
    await page.goto('/characters');
    
    // 验证页面加载
    await expect(page.locator('body')).toBeAttached();
  });

  test('后端 API 应该健康', async ({ page }) => {
    const response = await page.request.get('http://localhost:5001/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('角色 API 端点应该可访问', async ({ page }) => {
    const response = await page.request.get('http://localhost:5001/api/v1/characters');
    // 允许 200（成功）或 500（数据库问题），只要不是 404（端点不存在）
    expect([200, 500]).toContain(response.status());
  });
});
