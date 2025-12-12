import { test, expect } from '@playwright/test'
import { DashboardPage } from '../../pages/dashboard.page'
import { loginAs, clearLocalStorage } from '../../utils/test-helpers'

test.describe('PP Dashboard', () => {
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
    dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)
    await dashboardPage.selectFacility('PP-C-001')
    await expect(page).toHaveURL(/\/pp/, { timeout: 5000 })
    await page.waitForLoadState('networkidle')
  })

  test('PP1: Dashboard loads with pickup point statistics', async ({ page }) => {
    // Dashboard should show PP-specific statistics
    const receiptsCountElement = dashboardPage.receiptsCount

    await expect(receiptsCountElement).toBeVisible({ timeout: 5000 })

    const receiptsCount = await dashboardPage.getReceiptsCount()
    expect(receiptsCount).toBeTruthy()
  })

  test('PP2: Click "Receipts" navigates to incoming receipts', async ({ page }) => {
    await dashboardPage.clickReceipts()
    await expect(page).toHaveURL(/\/pp\/receipts/, { timeout: 5000 })
  })

  test('PP3: Click "Issues" navigates to issue acts', async ({ page }) => {
    await dashboardPage.clickIssues()
    await expect(page).toHaveURL(/\/pp\/issues/, { timeout: 5000 })
  })

  test('PP4: Click "Stock" navigates to stock view', async ({ page }) => {
    await dashboardPage.clickStock()
    await expect(page).toHaveURL(/\/pp\/stock/, { timeout: 5000 })
  })
})
