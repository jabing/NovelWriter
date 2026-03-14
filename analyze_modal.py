#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import os

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '0'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
    page.goto('http://localhost:5173/login')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='C:/dev_projects/NovelWriter/login_page.png')
    
    page.fill('input[type="email"]', 'test@example.com')
    page.fill('input[type="password"]', 'testpassword123')
    page.locator('button:has-text("登录")').click()
    page.wait_for_timeout(2000)
    
    page.goto('http://localhost:5173/projects')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='C:/dev_projects/NovelWriter/projects_page.png', full_page=True)
    
    page.locator('button:has-text("创建项目")').click()
    page.wait_for_timeout(1000)
    page.screenshot(path='C:/dev_projects/NovelWriter/modal_open.png', full_page=True)
    
    print("\n" + "="*60)
    print("MODAL ANALYSIS RESULTS")
    print("="*60)
    
    modal = page.locator('.modal-overlay')
    if modal.count() > 0:
        box = modal.bounding_box()
        print(f"Modal Overlay: {box['width']:.0f}x{box['height']:.0f}px")
    
    container = page.locator('.modal-container')
    if container.count() > 0:
        box = container.bounding_box()
        print(f"Modal Container: {box['width']:.0f}x{box['height']:.0f}px")
    
    body = page.locator('.modal-body')
    if body.count() > 0:
        box = body.bounding_box()
        print(f"Modal Body: {box['width']:.0f}x{box['height']:.0f}px")
    
    form_groups = page.locator('.form-group').all()
    print(f"Form groups: {len(form_groups)}")
    
    footer = page.locator('.modal-footer')
    if footer.count() > 0:
        box = footer.bounding_box()
        print(f"Footer: {box['width']:.0f}x{box['height']:.0f}px")
    
    print("\nScreenshots saved to project root:")
    print("  - login_page.png")
    print("  - projects_page.png") 
    print("  - modal_open.png")
    
    browser.close()
