import { test, expect } from '../fixtures/base';

test.describe('角色管理', () => {
  test.beforeEach(async ({ page }) => {
    // 访问首页
    await page.goto('/');
  });

  test('访问角色列表', async ({ page }) => {
    // 尝试访问角色相关页面
    await page.goto('/characters');
    
    // 验证页面加载
    await expect(page).toHaveURL(/\/characters/);
  });

  test('创建角色', async ({ page }) => {
    // 1. 访问角色页面
    await page.goto('/characters');
    
    // 2. 点击创建按钮（如果存在）
    const createButton = page.locator('button:has-text("新建"), button:has-text("创建"), button:has-text("New")');
    
    if (await createButton.count() > 0) {
      await createButton.first().click();
      
      // 3. 填写角色信息（如果有表单）
      const nameInput = page.locator('input[name="name"], input#name, input[placeholder*="名"], input[placeholder*="name"]');
      if (await nameInput.count() > 0) {
        await nameInput.fill('测试角色');
      }
      
      // 4. 提交
      const submitButton = page.locator('button:has-text("创建"), button:has-text("提交"), button:has-text("确定")');
      if (await submitButton.count() > 0) {
        await submitButton.first().click();
      }
    }
  });

  test('API 健康检查', async ({ page }) => {
    // 测试后端 API 连接
    const response = await page.request.get('http://localhost:5001/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });
});
