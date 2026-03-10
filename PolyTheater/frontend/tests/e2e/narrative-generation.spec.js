import { test, expect } from '../fixtures/base';

test.describe('叙事生成', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('访问章节编辑器', async ({ page }) => {
    // 尝试访问章节编辑器页面
    await page.goto('/story/1/chapter/1');
    
    // 验证页面加载
    await expect(page).toHaveURL(/\/story\/\d+\/chapter\/\d+/);
  });

  test('叙事生成页面元素', async ({ page }) => {
    // 访问叙事相关页面
    await page.goto('/narratives');
    
    // 验证页面加载
    await expect(page).toHaveURL(/\/narratives/);
  });

  test('API 叙事生成检查', async ({ page }) => {
    // 测试后端叙事 API 连接
    const response = await page.request.get('http://localhost:5001/api/v1/narratives');
    expect(response.ok()).toBeTruthy();
  });

  test('API 状态检查', async ({ page }) => {
    // 测试 API 状态端点
    const response = await page.request.get('http://localhost:5001/api/v1/status');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('running');
  });
});
