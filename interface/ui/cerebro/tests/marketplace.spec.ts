import { test, expect } from '@playwright/test';

test.describe('Agent Marketplace', () => {
    test('should display agent cards and allow installation', async ({ page }) => {
        // 1. Mock Login (if ProtectedRoute requires it, we might need to bypass or simulate auth)
        // For now, assuming dev server runs on localhost:5173

        // 2. Navigate to Marketplace (Will redirect to login)
        await page.goto('http://localhost:3000/marketplace');

        // 3. Handle Login Flow
        // Wait for login form
        await page.waitForURL('**/login');

        // Fill credentials (mock/stub doesn't matter as long as frontend accepts it 
        // or if we have a real backend. Since we use `api/client`, we might need to mock the API response.
        // BUT since we don't have a backend running, the Login page might fail network requests.
        // SO we should MOCK the network request for login.

        await page.route('**/api/auth/login', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    access_token: 'mock-jwt-token',
                    expires_in: 3600,
                    user_id: '1',
                    tenant_id: 'default'
                })
            });
        });

        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'password');
        await page.click('button[type="submit"]');

        // Wait for navigation back to marketplace
        await page.waitForURL('**/marketplace');

        // 4. Verify Marketplace Header
        await expect(page.locator('h1')).toContainText('NEXUS Agent Marketplace');

        // 5. Verify QA Sentinel Card matches Product Strategy
        const qaCard = page.locator('text=QA Sentinel');
        await expect(qaCard).toBeVisible();
        await expect(page.locator('text=$50/mo').first()).toBeVisible();

        // 6. Test Interaction (Install)
        // We need to handle the window.alert
        page.on('dialog', async dialog => {
            expect(dialog.message()).toContain('Installing QA Sentinel');
            await dialog.accept();
        });

        await page.click('[data-testid="install-qa_sentinel"]');
    });
});
