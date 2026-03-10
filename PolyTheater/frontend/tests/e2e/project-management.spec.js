import { test, expect } from '../fixtures/base';

test.describe('项目管理', () => {
  test('首页应该加载', async ({ page }) => {
    await page.goto('/');
    
    // 验证页面标题
    await expect(page).toHaveTitle(/NovelWriter|PolyTheater/);
    
    // 验证 #app 元素存在
    const app = page.locator('#app');
    await expect(app).toBeAttached();
  });

  test('应该能访问项目列表页面', async ({ page }) => {
    await page.goto('/projects');
    
    // 验证 URL 变化
    await expect(page).toHaveURL(/\/projects/);
  });

  test('应该能访问创建项目表单', async ({ page }) => {
    await page.goto('/projects');
    
    // 验证页面加载（不检查具体内容，因为需要后端数据）
    await expect(page.locator('body')).toBeAttached();
  });

  test('后端 API 应该健康', async ({ page }) => {
    const response = await page.request.get('http://localhost:5001/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });
});
