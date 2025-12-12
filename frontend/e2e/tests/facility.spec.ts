import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages/login.page'
import { DashboardPage } from '../pages/dashboard.page'
import { users, loginAs, clearLocalStorage, getLocalStorage } from '../utils/test-helpers'

test.describe('Facility Selector', () => {
  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
  })

  test('F1: Selector visible after admin login', async ({ page }) => {
    const loginPage = new LoginPage(page)
    const dashboardPage = new DashboardPage(page)

    await loginPage.goto()
    await loginPage.login(users.admin.username, users.admin.password)
    await page.waitForURL(/^(?!.*login).*$/)

    // Selector should be visible
    const isSelectorVisible = await dashboardPage.isFacilitySelectorVisible()
    expect(isSelectorVisible).toBe(true)
  })

  test('F2: Select DC facility', async ({ page }) => {
    const dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)

    // Select DC facility
    await dashboardPage.selectFacility('DC-C-001')

    // Should redirect to /dc
    await expect(page).toHaveURL(/\/dc/, { timeout: 5000 })

    // Check facility code is displayed
    await page.waitForTimeout(500)
    const facilityCode = await dashboardPage.getFacilityCode()
    expect(facilityCode).toContain('DC-C-001')
  })

  test('F3: Select WH facility', async ({ page }) => {
    const dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)

    // Select WH facility
    await dashboardPage.selectFacility('WH-C-001')

    // Should redirect to /wh
    await expect(page).toHaveURL(/\/wh/, { timeout: 5000 })

    // Check facility code is displayed
    await page.waitForTimeout(500)
    const facilityCode = await dashboardPage.getFacilityCode()
    expect(facilityCode).toContain('WH-C-001')
  })

  test('F4: Select PP facility', async ({ page }) => {
    const dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)

    // Select PP facility
    await dashboardPage.selectFacility('PP-C-001')

    // Should redirect to /pp
    await expect(page).toHaveURL(/\/pp/, { timeout: 5000 })

    // Check facility code is displayed
    await page.waitForTimeout(500)
    const facilityCode = await dashboardPage.getFacilityCode()
    expect(facilityCode).toContain('PP-C-001')
  })

  test('F5: Change facility (DC -> WH)', async ({ page }) => {
    const dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)

    // Select DC facility first
    await dashboardPage.selectFacility('DC-C-001')
    await expect(page).toHaveURL(/\/dc/, { timeout: 5000 })

    // Change to WH facility
    await dashboardPage.selectFacility('WH-C-001')

    // URL should change to /wh
    await expect(page).toHaveURL(/\/wh/, { timeout: 5000 })

    // Facility code should update
    await page.waitForTimeout(500)
    const facilityCode = await dashboardPage.getFacilityCode()
    expect(facilityCode).toContain('WH-C-001')
  })

  test('F6: Facility persists in localStorage after refresh', async ({ page }) => {
    const dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)

    // Select WH facility
    await dashboardPage.selectFacility('WH-C-001')
    await expect(page).toHaveURL(/\/wh/, { timeout: 5000 })

    // Get current URL
    const currentUrl = page.url()

    // Refresh page
    await page.reload()

    // Should stay on same facility page
    await expect(page).toHaveURL(currentUrl)

    // Facility should still be selected
    await page.waitForTimeout(500)
    const facilityCode = await dashboardPage.getFacilityCode()
    expect(facilityCode).toContain('WH-C-001')
  })

  test('F7: User with facility does not see selector', async ({ page }) => {
    const loginPage = new LoginPage(page)
    const dashboardPage = new DashboardPage(page)

    await loginPage.goto()
    await loginPage.login(users.wh_north_op.username, users.wh_north_op.password)
    await page.waitForURL(/\/wh/, { timeout: 10000 })

    // Selector should be hidden or disabled for users with assigned facility
    // Wait a bit for page to fully load
    await page.waitForTimeout(1000)

    const isSelectorVisible = await dashboardPage.isFacilitySelectorVisible()
    // For users with assigned facility, selector might be hidden or disabled
    // This depends on implementation - adjust assertion based on actual behavior
    expect(isSelectorVisible).toBe(false)
  })
})
