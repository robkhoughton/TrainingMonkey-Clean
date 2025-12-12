import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Screenshot capture script for TrainingMonkey UI
 *
 * Captures all main pages at desktop and mobile viewports.
 * Used for design agent visual review sessions.
 *
 * Prerequisites:
 *   1. Start mock server: scripts\start_mock_server.bat
 *   2. Run: npm run test:screenshots
 *
 * Screenshots saved to: tests/screenshots/output/
 */

// Pages to capture
const pages = [
  { name: 'dashboard', url: '/dashboard', waitFor: '.training-load-dashboard, .dashboard-container' },
  { name: 'activities', url: '/dashboard?tab=activities', waitFor: '.activities-page, .activity-card' },
  { name: 'journal', url: '/dashboard?tab=journal', waitFor: '.journal-page, .journal-entry' },
  { name: 'coach', url: '/dashboard?tab=coach', waitFor: '.coach-page, .recommendations' },
  { name: 'settings', url: '/settings/profile', waitFor: 'form, .settings-page' },
];

// Viewports to test
const viewports = [
  { name: 'desktop', width: 1920, height: 1080 },
  { name: 'mobile', width: 375, height: 667 },
];

// Ensure output directory exists
const outputDir = path.join(__dirname, 'output');
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Generate timestamp for this run
const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);

test.describe('Screenshot Capture - All Pages', () => {
  for (const viewport of viewports) {
    test.describe(`${viewport.name} (${viewport.width}x${viewport.height})`, () => {
      test.use({ viewport: { width: viewport.width, height: viewport.height } });

      for (const page of pages) {
        test(`capture ${page.name}`, async ({ page: browserPage }) => {
          // Navigate to page
          await browserPage.goto(page.url, { waitUntil: 'networkidle' });

          // Wait for main content to load
          try {
            // Try each selector in the waitFor (comma-separated)
            const selectors = page.waitFor.split(',').map(s => s.trim());
            await Promise.race(
              selectors.map(selector =>
                browserPage.waitForSelector(selector, { timeout: 10000 }).catch(() => null)
              )
            );
          } catch (e) {
            // Continue even if specific element not found
            console.log(`Note: Could not find specific element for ${page.name}, continuing anyway`);
          }

          // Additional wait for any animations/loading
          await browserPage.waitForTimeout(1000);

          // Take screenshot
          const filename = `${timestamp}_${viewport.name}_${page.name}.png`;
          const filepath = path.join(outputDir, filename);

          await browserPage.screenshot({
            path: filepath,
            fullPage: true,
          });

          console.log(`Captured: ${filename}`);

          // Verify screenshot was created
          expect(fs.existsSync(filepath)).toBeTruthy();
        });
      }
    });
  }
});

// Quick single-page capture for rapid iteration
test.describe('Quick Capture - Dashboard Only', () => {
  test('dashboard desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/dashboard', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const filename = `${timestamp}_quick_dashboard.png`;
    await page.screenshot({
      path: path.join(outputDir, filename),
      fullPage: true,
    });

    console.log(`Quick capture: ${filename}`);
  });
});
