import { defineConfig, devices } from '@playwright/test'

/**
 * See https://playwright.dev/docs/test-configuration.
 */
// Auto-detect headed mode: use headed if DISPLAY is set, otherwise headless
const hasDisplay = !!process.env.DISPLAY

export default defineConfig({
  testDir: './e2e',
  timeout: 5000,
  expect: {
    timeout: 1000
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: process.env.BASE_URL || 'http://192.168.1.74:31081',
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    headless: !hasDisplay,
    actionTimeout: 1000,
    navigationTimeout: 2000,
    launchOptions: {
      args: [
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--single-process',
        '--no-zygote',
      ],
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
