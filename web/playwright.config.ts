import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for AI Receptionist Dashboard E2E tests
 * Phase 4: Dashboard E2E Testing
 */
export default defineConfig({
  testDir: './tests/e2e',
  
  // Maximum time one test can run
  timeout: 30 * 1000,
  
  // Test execution settings
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html'],
    ['list'],
    ['json', { outputFile: 'playwright-report/results.json' }],
  ],
  
  // Shared settings for all tests
  use: {
    // Base URL for the frontend
    baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
    
    // Capture screenshots on failure
    screenshot: 'only-on-failure',
    
    // Capture videos on failure
    video: 'retain-on-failure',
    
    // Collect traces on failure
    trace: 'on-first-retry',
    
    // API endpoint for backend
    extraHTTPHeaders: {
      'Accept': 'application/json',
    },
  },
  
  // Configure projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Uncomment to test in Firefox
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // Uncomment to test in Safari
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],
  
  // Run your local dev server before starting the tests
  // Commented out - start services manually for now
  // webServer: [
  //   {
  //     command: 'cd .. && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000',
  //     port: 8000,
  //     timeout: 120 * 1000,
  //     reuseExistingServer: !process.env.CI,
  //   },
  //   {
  //     command: 'npm run dev',
  //     port: 3000,
  //     timeout: 120 * 1000,
  //     reuseExistingServer: !process.env.CI,
  //   },
  // ],
});
