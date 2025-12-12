import { Page } from '@playwright/test'

export const users = {
  admin: { username: 'admin', password: 'admin123' },
  dc_manager: { username: 'dc_central_mgr', password: 'password123' },
  wh_north_op: { username: 'wh_north_op', password: 'password123' },
  wh_south_op: { username: 'wh_south_op', password: 'password123' },
  pp_1_op: { username: 'pp_1_op', password: 'password123' },
  pp_2_op: { username: 'pp_2_op', password: 'password123' },
}

/**
 * Login as a specific user
 */
export async function loginAs(page: Page, userKey: keyof typeof users) {
  const user = users[userKey]
  await page.goto('/login')
  await page.fill('[data-testid="username"]', user.username)
  await page.fill('[data-testid="password"]', user.password)
  await page.click('[data-testid="login-button"]')
  await page.waitForURL(/^(?!.*login).*$/, { timeout: 2000 })
}

/**
 * Select a facility from the selector
 */
export async function selectFacility(page: Page, facilityCode: string) {
  await page.click('[data-testid="facility-selector"]')
  await page.locator(`[data-testid="facility-option-${facilityCode}"]`).click()
}

/**
 * Logout current user
 */
export async function logout(page: Page) {
  await page.click('[data-testid="logout-button"]')
  await page.waitForURL('/login')
}

/**
 * Wait for API calls to complete
 */
export async function waitForApi(page: Page) {
  await page.waitForLoadState('networkidle')
}

/**
 * Wait for a toast notification with specific text
 */
export async function waitForToast(page: Page, text: string) {
  await page.waitForSelector(`text=${text}`, { timeout: 1000 })
}

/**
 * Wait for table to load with rows
 */
export async function waitForTableLoad(page: Page) {
  await page.waitForSelector('table tbody tr', { timeout: 1000 })
}

/**
 * Wait for a specific API response
 */
export async function waitForApiResponse(page: Page, urlPattern: string | RegExp) {
  await page.waitForResponse(resp => {
    const url = resp.url()
    if (typeof urlPattern === 'string') {
      return url.includes(urlPattern)
    }
    return urlPattern.test(url)
  })
}

/**
 * Wait for API response with specific status
 */
export async function waitForApiResponseWithStatus(
  page: Page,
  urlPattern: string | RegExp,
  status: number
) {
  await page.waitForResponse(resp => {
    const url = resp.url()
    const matches = typeof urlPattern === 'string'
      ? url.includes(urlPattern)
      : urlPattern.test(url)
    return matches && resp.status() === status
  })
}

/**
 * Get text content from element
 */
export async function getTextContent(page: Page, selector: string): Promise<string> {
  const element = await page.locator(selector).textContent()
  return element?.trim() || ''
}

/**
 * Check if element is visible
 */
export async function isVisible(page: Page, selector: string): Promise<boolean> {
  return await page.locator(selector).isVisible()
}

/**
 * Get localStorage value
 */
export async function getLocalStorage(page: Page, key: string): Promise<string | null> {
  return await page.evaluate((k) => localStorage.getItem(k), key)
}

/**
 * Set localStorage value
 */
export async function setLocalStorage(page: Page, key: string, value: string) {
  await page.evaluate(({ k, v }) => localStorage.setItem(k, v), { k: key, v: value })
}

/**
 * Clear localStorage
 * Navigates to the app first to ensure localStorage is accessible
 */
export async function clearLocalStorage(page: Page) {
  // Navigate to the app first to get access to localStorage
  await page.goto('/login')
  await page.evaluate(() => localStorage.clear())
}
