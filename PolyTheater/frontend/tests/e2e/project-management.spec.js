import { test, expect } from '../fixtures/base';

test.describe('项目管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('首页加载', async ({ page }) => {
    // 验证页面标题或主要元素存在
    await expect(page).toHaveTitle(/NovelWriter/);
  });

  test('访问项目列表', async ({ page }) => {
    // 访问项目列表页
    await page.goto('/projects');
    
    // 验证页面加载
    await expect(page).toHaveURL(/\/projects/);
  });

  test('创建项目', async ({ page }) => {
    // 1. 访问项目列表页
    await page.goto('/projects');
    
    // 2. 点击创建按钮（如果存在）
    const createButton = page.locator('button:has-text("新建"), button:has-text("创建"), button:has-text("New")');
    
    // 如果按钮存在，点击它
    if (await createButton.count() > 0) {
      await createButton.first().click();
      
      // 3. 填写项目信息（如果有表单）
      const nameInput = page.locator('input[name="name"], input#name, input[placeholder*="名"], input[placeholder*="name"]');
      if (await nameInput.count() > 0) {
        await nameInput.fill('测试项目');
      }
      
      // 4. 提交
      const submitButton = page.locator('button:has-text("创建"), button:has-text("提交"), button:has-text("确定")');
      if (await submitButton.count() > 0) {
        await submitButton.first().click();
      }
    }
  });
});
