import { test, expect } from '@playwright/test';
import { exec } from 'child_process';
import util from 'util';

const execAsync = util.promisify(exec);

test.describe('Project GENESIS (Generative UI)', () => {

    test('should generate and render a component locally', async ({ page }) => {
        // 1. Run the Python Generator to create 'GeneratedComponent.tsx'
        // We use the "card" prompt to test the Card template
        console.log('Running Generator...');
        try {
            await execAsync('python ../../../core/ui/generator.py "I want a futuristic card component"');
        } catch (e) {
            console.error('Generator failed:', e);
            throw e;
        }

        // 2. Navigate to /genesis
        await page.goto('/genesis');
        // Allow client-side redirect to happen
        await page.waitForTimeout(1000);

        // 3. Handle Login (if redirected)
        if (page.url().includes('login')) {
            await page.route('**/api/auth/login', async route => {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({ access_token: 'mock-jwt', expires_in: 3600, user_id: '1', tenant_id: 'default' })
                });
            });

            await page.fill('input[name="username"]', 'admin');
            await page.fill('input[name="password"]', 'password');
            await page.click('button[type="submit"]');
            await page.waitForURL('**/genesis');
        }

        // Check for error message first
        const errorMsg = page.locator('text=No generated component found');
        if (await errorMsg.isVisible()) {
            const text = await errorMsg.textContent();
            console.error('Genesis Error:', text);
            throw new Error(`Genesis failed: ${text}`);
        }

        // Wait for loading to finish (Quantum Loader)
        // New Cycle 010 loader messages
        const loader = page.getByTestId('quantum-loader');
        await expect(loader).toBeHidden({ timeout: 15000 }); // Increased timeout for "Amazing" delay

        if (await page.locator('text=Waiting for Input...').isVisible()) {
            console.error('Genesis Error: Stuck on Waiting for Input');
            throw new Error('Genesis failed: Stuck on Waiting');
        }

        // Check canvas content directly
        const canvasContent = await page.getByTestId('canvas').textContent();
        // console.log('Canvas Text Content:', canvasContent);

        // 4. Verify the Component Renders
        const cardTitle = page.locator('text=Generative Card');
        await expect(cardTitle).toBeVisible();

        // Updated for Cycle 010
        const footer = page.locator('text=NEXUS Cycle 010');
        await expect(footer).toBeVisible();

        // 5. Verify Canvas UI
        await expect(page.locator('h1')).toContainText('Project GENESIS');
        await expect(page.locator('text=System Status: ONLINE')).toBeVisible();
    });
});
