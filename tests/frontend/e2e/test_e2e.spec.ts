"""
Playwright End-to-End tests for complete user flows
"""
import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';
const API_URL = process.env.E2E_API_URL || 'http://localhost:8000';

// Test users
const USERS = {
  admin: { email: 'admin@parsheid.ir', password: 'admin123' },
  analyst: { email: 'analyst@parsheid.ir', password: 'analyst123' },
  reviewer: { email: 'reviewer@parsheid.ir', password: 'reviewer123' },
  applicant: { email: 'applicant@test.com', password: 'password123' },
};

async function login(page: Page, user: typeof USERS.admin) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[type="email"]', user.email);
  await page.fill('input[type="password"]', user.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(`${BASE_URL}/dashboard`);
}

async function createApplication(page: Page, data: Record<string, string> = {}) {
  await page.goto(`${BASE_URL}/onboarding`);
  
  // Step 1: Personal info
  await page.fill('input[name="first_name"]', data.first_name || 'Test');
  await page.fill('input[name="last_name"]', data.last_name || 'User');
  await page.fill('input[name="national_id"]', data.national_id || '0012345679');
  await page.fill('input[name="birth_date"]', data.birth_date || '1370/01/01');
  await page.selectOption('select[name="gender"]', data.gender || 'مرد');
  await page.click('button:has-text("ادامه")');
  
  // Step 2: Contact info
  await page.fill('input[name="phone"]', data.phone || '09123456789');
  await page.fill('input[name="email"]', data.email || 'test@test.com');
  await page.fill('input[name="province"]', data.province || 'تهران');
  await page.fill('input[name="city"]', data.city || 'تهران');
  await page.fill('textarea[name="address"]', data.address || 'خیابان ولیعصر پلاک ۱۰');
  await page.click('button:has-text("ادامه")');
  
  // Step 3: Document upload
  await page.setInputFiles('input[type="file"]', 'tests/fixtures/national_id.jpg');
  await page.click('button:has-text("ادامه")');
  
  // Steps 4-5: Quality and extraction (auto)
  await page.waitForTimeout(2000);
  await page.click('button:has-text("ادامه")');
  
  // Step 6: Confirm fields
  await page.click('button:has-text("ادامه")');
  
  // Step 7: Selfie
  await page.setInputFiles('input[type="file"]', 'tests/fixtures/selfie.jpg');
  await page.click('button:has-text("ادامه")');
  
  // Step 8: Additional info
  await page.fill('input[name="occupation"]', data.occupation || 'مهندس');
  await page.fill('input[name="declared_income"]', data.declared_income || '۵۰-۱۰۰ میلیون');
  await page.fill('input[name="source_of_funds"]', data.source_of_funds || 'حقوق');
  await page.selectOption('select[name="expected_volume"]', data.expected_volume || 'متوسط');
  await page.click('button:has-text("ادامه")');
  
  // Step 9: Review
  await page.click('button:has-text("ادامه")');
  
  // Step 10: Submit
  await page.click('button:has-text("ارسال نهایی")');
  
  await page.waitForURL(/\/dashboard/);
  return page.url().split('/').pop();
}

test.describe('Authentication Flow', () => {
  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', USERS.admin.email);
    await page.fill('input[type="password"]', USERS.admin.password);
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(`${BASE_URL}/dashboard`);
    await expect(page.locator('text=داشبورد')).toBeVisible();
  });

  test('should reject invalid credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', 'wrong@test.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=خطای ورود')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    await login(page, USERS.admin);
    await page.click('button:has-text("خروج")');
    await expect(page).toHaveURL(`${BASE_URL}/login`);
  });

  test('should redirect to login when accessing protected route', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page).toHaveURL(`${BASE_URL}/login`);
  });
});

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, USERS.admin);
  });

  test('should display dashboard with KPIs', async ({ page }) => {
    await expect(page.locator('text=داشبورد')).toBeVisible();
    await expect(page.locator('text=کل درخواست‌ها')).toBeVisible();
    await expect(page.locator('text=نرخ تأیید')).toBeVisible();
    await expect(page.locator('text=پرونده‌های باز')).toBeVisible();
    await expect(page.locator('text=ریسک بالا')).toBeVisible();
  });

  test('should display charts', async ({ page }) => {
    await expect(page.locator('text=روند درخواست‌ها')).toBeVisible();
    await expect(page.locator('text=توزیع ریسک')).toBeVisible();
    await expect(page.locator('text=وضعیت درخواست‌ها')).toBeVisible();
    await expect(page.locator('text=سند بر اساس نوع')).toBeVisible();
  });

  test('should show verification funnel', async ({ page }) => {
    await expect(page.locator('text=قیف احراز هویت')).toBeVisible();
    await expect(page.locator('text=درخواست')).toBeVisible();
    await expect(page.locator('text=تأیید')).toBeVisible();
  });

  test('should show recent activity', async ({ page }) => {
    await expect(page.locator('text=فعالیت اخیر')).toBeVisible();
  });
});

test.describe('Customer Onboarding Flow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, USERS.applicant);
  });

  test('should complete full onboarding wizard', async ({ page }) => {
    const appId = await createApplication(page, {
      first_name: 'Test',
      last_name: 'User',
      national_id: '0012345679',
    });
    
    // Verify application was created
    await expect(page.locator('text=درخواست شما با موفقیت ارسال شد')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto(`${BASE_URL}/onboarding`);
    
    // Try to continue without filling required fields
    await page.click('button:has-text("ادامه")');
    
    // Should show validation errors
    await expect(page.locator('text=این فیلد الزامی است')).toBeVisible();
  });

  test('should save progress at each step', async ({ page }) => {
    await page.goto(`${BASE_URL}/onboarding`);
    
    // Fill step 1
    await page.fill('input[name="first_name"]', 'Test');
    await page.fill('input[name="last_name"]', 'User');
    await page.fill('input[name="national_id"]', '0012345679');
    await page.fill('input[name="birth_date"]', '1370/01/01');
    await page.selectOption('select[name="gender"]', 'مرد');
    
    // Go to next step and back
    await page.click('button:has-text("ادامه")');
    await page.click('button:has-text("بازگشت")');
    
    // Data should be preserved
    await expect(page.locator('input[name="first_name"]')).toHaveValue('Test');
  });

  test('should upload and validate document', async ({ page }) => {
    await page.goto(`${BASE_URL}/onboarding`);
    
    // Fill steps 1-2 quickly
    await page.fill('input[name="first_name"]', 'Test');
    await page.fill('input[name="last_name"]', 'User');
    await page.fill('input[name="national_id"]', '0012345679');
    await page.fill('input[name="birth_date"]', '1370/01/01');
    await page.selectOption('select[name="gender"]', 'مرد');
    await page.click('button:has-text("ادامه")');
    
    await page.fill('input[name="phone"]', '09123456789');
    await page.fill('input[name="email"]', 'test@test.com');
    await page.fill('input[name="province"]', 'تهران');
    await page.fill('input[name="city"]', 'تهران');
    await page.fill('textarea[name="address"]', 'Test Address');
    await page.click('button:has-text("ادامه")');
    
    // Upload document
    await page.setInputFiles('input[type="file"]', 'tests/fixtures/national_id.jpg');
    await page.click('button:has-text("ادامه")');
    
    // Should process document
    await expect(page.locator('text=بررسی کیفیت')).toBeVisible();
  });
});

test.describe('Application Management', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, USERS.analyst);
  });

  test('should list applications', async ({ page }) => {
    await page.goto(`${BASE_URL}/applications`);
    
    await expect(page.locator('text=درخواست‌ها')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('should filter applications by status', async ({ page }) => {
    await page.goto(`${BASE_URL}/applications`);
    
    await page.selectOption('select', 'submitted');
    await page.click('button:has-text("جستجو")');
    
    await expect(page.locator('text=ارسال‌شده')).toBeVisible();
  });

  test('should view application detail', async ({ page }) => {
    await page.goto(`${BASE_URL}/applications`);
    
    // Click first application
    await page.click('table tbody tr:first-child');
    
    await expect(page.locator('text=نمای کلی')).toBeVisible();
    await expect(page.locator('text=مدارک')).toBeVisible();
    await expect(page.locator('text=احراز هویت')).toBeVisible();
    await expect(page.locator('text=ریسک')).toBeVisible();
    await expect(page.locator('text=غربالگری')).toBeVisible();
    await expect(page.locator('text=تصمیمات')).toBeVisible();
    await expect(page.locator('text=تاریخچه')).toBeVisible();
  });

  test('should show risk assessment in detail', async ({ page }) => {
    await page.goto(`${BASE_URL}/applications`);
    await page.click('table tbody tr:first-child');
    await page.click('text=ریسک');
    
    await expect(page.locator('text=امتیاز ریسک')).toBeVisible();
    await expect(page.locator('text=عوامل ریسک')).toBeVisible();
  });

  test('should show screening results', async ({ page }) => {
    await page.goto(`${BASE_URL}/applications`);
    await page.click('table tbody tr:first-child');
    await page.click('text=غربالگری');
    
    await expect(page.locator('text=تحریم‌ها')).toBeVisible();
    await expect(page.locator('text=اشخاص سیاسی')).toBeVisible();
  });

  test('should show verification results', async ({ page }) => {
    await page.goto(`${BASE_URL}/applications`);
    await page.click('table tbody tr:first-child');
    await page.click('text=احراز هویت');
    
    await expect(page.locator('text=تطبیق چهره')).toBeVisible();
    await expect(page.locator('text=بررسی مدارک')).toBeVisible();
  });
});

test.describe('Case Management', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, USERS.reviewer);
  });

  test('should list cases', async ({ page }) => {
    await page.goto(`${BASE_URL}/cases`);
    
    await expect(page.locator('text=پرونده‌ها')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('should filter cases by status and priority', async ({ page }) => {
    await page.goto(`${BASE_URL}/cases`);
    
    await page.selectOption('select', 'open');
    await expect(page.locator('text=باز')).toBeVisible();
  });

  test('should view case detail', async ({ page }) => {
    await page.goto(`${BASE_URL}/cases`);
    await page.click('table tbody tr:first-child');
    
    await expect(page.locator('text=اطلاعات پرونده')).toBeVisible();
    await expect(page.locator('text=بررسی‌ها')).toBeVisible();
    await expect(page.locator('text=تاریخچه اختصاص')).toBeVisible();
  });

  test('should review case', async ({ page }) => {
    await page.goto(`${BASE_URL}/cases`);
    await page.click('table tbody tr:first-child');
    
    await page.click('button:has-text("بررسی")');
    await expect(page.locator('text=بررسی پرونده')).toBeVisible();
    
    await page.selectOption('select', 'approve');
    await page.fill('textarea', 'Approved after review');
    await page.click('button:has-text("ثبت")');
    
    await expect(page.locator('text=تأیید')).toBeVisible();
  });
});

test.describe('Risk & AML', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, USERS.analyst);
  });

  test('should display risk overview', async ({ page }) => {
    await page.goto(`${BASE_URL}/risk`);
    
    await expect(page.locator('text=ارزیابی ریسک')).toBeVisible();
    await expect(page.locator('text=توزیع سطح ریسک')).toBeVisible();
  });

  test('should show AML screening results', async ({ page }) => {
    await page.goto(`${BASE_URL}/aml`);
    
    await expect(page.locator('text=مبارزه با پولشویی')).toBeVisible();
    await expect(page.locator('text=تحریم‌ها')).toBeVisible();
    await expect(page.locator('text=اشخاص سیاسی')).toBeVisible();
  });
});

test.describe('Global Search', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, USERS.admin);
  });

  test('should search across all entities', async ({ page }) => {
    await page.fill('header input[type="text"]', 'APP-1001');
    await page.waitForTimeout(500);
    
    await expect(page.locator('text=APP-1001')).toBeVisible();
  });

  test('should navigate to result', async ({ page }) => {
    await page.fill('header input[type="text"]', 'APP-1001');
    await page.waitForTimeout(500);
    await page.click('text=APP-1001');
    
    await expect(page).toHaveURL(/\/applications\//);
  });
});

test.describe('Notifications', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, USERS.admin);
  });

  test('should open notification center', async ({ page }) => {
    await page.click('header button:has(svg)'); // Notification bell
    await expect(page.locator('text=اعلانات')).toBeVisible();
  });

  test('should mark notifications as read', async ({ page }) => {
    await page.click('header button:has(svg)');
    await page.click('button:has-text("خواندن")');
    
    await expect(page.locator('text= خوانده')).toBeVisible();
  });
});

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, USERS.admin);
  });

  test('should display settings page', async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    
    await expect(page.locator('text=تنظیمات')).toBeVisible();
    await expect(page.locator('text=پروفایل')).toBeVisible();
    await expect(page.locator('text=تغییر گذرواژه')).toBeVisible();
  });

  test('should update profile', async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    
    await page.fill('input[placeholder="نام کامل"]', 'Updated Name');
    await page.click('button:has-text("ذخیره")');
    
    await expect(page.locator('text=پروفایل به‌روزرسانی شد')).toBeVisible();
  });

  test('should change password', async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    
    await page.fill('input[name="old_password"]', 'admin123');
    await page.fill('input[name="new_password"]', 'newpassword123');
    await page.fill('input[name="confirm_password"]', 'newpassword123');
    await page.click('button:has-text("تغییر گذرواژه")');
    
    await expect(page.locator('text=گذرواژه با موفقیت تغییر کرد')).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await login(page, USERS.admin);
    
    await expect(page.locator('text=داشبورد')).toBeVisible();
    
    // Sidebar should be hidden or toggleable
    await page.click('button[aria-label="menu"]');
    await expect(page.locator('text=مشتریان')).toBeVisible();
  });

  test('should work on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await login(page, USERS.admin);
    
    await expect(page.locator('text=داشبورد')).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await login(page, USERS.admin);
    await page.goto(`${BASE_URL}/dashboard`);
    
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThanOrEqual(1);
  });

  test('should have proper form labels', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    const emailLabel = await page.locator('label[for="email"]').count();
    const passwordLabel = await page.locator('label[for="password"]').count();
    
    expect(emailLabel).toBe(1);
    expect(passwordLabel).toBe(1);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    await page.keyboard.press('Tab');
    await expect(page.locator('input[type="email"]')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator('input[type="password"]')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator('button[type="submit"]')).toBeFocused();
  });
});

test.describe('Performance', () => {
  test('dashboard should load within 3 seconds', async ({ page }) => {
    const start = Date.now();
    await login(page, USERS.admin);
    const loadTime = Date.now() - start;
    
    expect(loadTime).toBeLessThan(3000);
  });

  test('application list should load within 2 seconds', async ({ page }) => {
    await login(page, USERS.analyst);
    const start = Date.now();
    await page.goto(`${BASE_URL}/applications`);
    await page.waitForSelector('table');
    const loadTime = Date.now() - start;
    
    expect(loadTime).toBeLessThan(2000);
  });
});

test.afterAll(async () => {
  // Cleanup if needed
});