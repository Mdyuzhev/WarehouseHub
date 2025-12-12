import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages/login.page'
import { DashboardPage } from '../pages/dashboard.page'
import { users, clearLocalStorage, getLocalStorage } from '../utils/test-helpers'

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
  })

  test('A1: Login with valid credentials (admin)', async ({ page }) => {
    const loginPage = new LoginPage(page)
    const dashboardPage = new DashboardPage(page)

    await loginPage.goto()
    await loginPage.login(users.admin.username, users.admin.password)

    // Should redirect to root
    await expect(page).toHaveURL(/^(?!.*login).*$/)

    // FacilitySelector should be visible for admin
    const isSelectorVisible = await dashboardPage.isFacilitySelectorVisible()
    expect(isSelectorVisible).toBe(true)
  })

  test('A2: Login with invalid password', async ({ page }) => {
    const loginPage = new LoginPage(page)

    await loginPage.goto()
    await loginPage.login(users.admin.username, 'wrongpassword')

    // Should show error message
    const isErrorVisible = await loginPage.isErrorVisible()
    expect(isErrorVisible).toBe(true)

    // Should stay on login page
    await expect(page).toHaveURL(/login/)
  })

  test('A3: Login with non-existent user', async ({ page }) => {
    const loginPage = new LoginPage(page)

    await loginPage.goto()
    await loginPage.login('nonexistentuser', 'password123')

    // Should show error message
    const isErrorVisible = await loginPage.isErrorVisible()
    expect(isErrorVisible).toBe(true)

    // Should stay on login page
    await expect(page).toHaveURL(/login/)
  })

  test('A4: Login user with facility (wh_north_op)', async ({ page }) => {
    const loginPage = new LoginPage(page)

    await loginPage.goto()
    await loginPage.login(users.wh_north_op.username, users.wh_north_op.password)

    // Should redirect to /wh (warehouse facility)
    await expect(page).toHaveURL(/\/wh/, { timeout: 2000 })

    // Facility should be auto-selected
    const token = await getLocalStorage(page, 'warehouse_auth_token')
    expect(token).toBeTruthy()
  })

  test('A5: Logout', async ({ page }) => {
    const loginPage = new LoginPage(page)
    const dashboardPage = new DashboardPage(page)

    // First login
    await loginPage.goto()
    await loginPage.login(users.admin.username, users.admin.password)
    await page.waitForURL(/^(?!.*login).*$/)

    // Check token exists
    let token = await getLocalStorage(page, 'warehouse_auth_token')
    expect(token).toBeTruthy()

    // Logout
    await dashboardPage.logout()

    // Should redirect to login
    await expect(page).toHaveURL(/login/)

    // Token should be removed
    token = await getLocalStorage(page, 'warehouse_auth_token')
    expect(token).toBeFalsy()
  })

  test('A6: Access protected page without authentication', async ({ page }) => {
    await page.goto('/dc')

    // Should redirect to login
    await expect(page).toHaveURL(/login/, { timeout: 2000 })
  })

  test('A7: Refresh page after login preserves session', async ({ page }) => {
    const loginPage = new LoginPage(page)

    // Login
    await loginPage.goto()
    await loginPage.login(users.admin.username, users.admin.password)
    await page.waitForURL(/^(?!.*login).*$/)

    // Get current URL
    const currentUrl = page.url()

    // Refresh page
    await page.reload()

    // Should stay on same page (not redirect to login)
    await expect(page).toHaveURL(currentUrl)

    // Token should still exist
    const token = await getLocalStorage(page, 'warehouse_auth_token')
    expect(token).toBeTruthy()
  })
})
