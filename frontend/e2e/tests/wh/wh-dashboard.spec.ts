import { test, expect } from '@playwright/test'
import { DashboardPage } from '../../pages/dashboard.page'
import { loginAs, clearLocalStorage } from '../../utils/test-helpers'

test.describe('WH Dashboard', () => {
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
    dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)
    await dashboardPage.selectFacility('WH-C-001')
    await expect(page).toHaveURL(/\/wh/, { timeout: 5000 })
    await page.waitForLoadState('networkidle')
  })

  test('WH1: Dashboard loads with warehouse statistics', async ({ page }) => {
    // Dashboard should show relevant statistics
    const receiptsCountElement = dashboardPage.receiptsCount
    const shipmentsCountElement = dashboardPage.shipmentsCount

    await expect(receiptsCountElement).toBeVisible({ timeout: 5000 })
    await expect(shipmentsCountElement).toBeVisible({ timeout: 5000 })

    const receiptsCount = await dashboardPage.getReceiptsCount()
    const shipmentsCount = await dashboardPage.getShipmentsCount()

    expect(receiptsCount).toBeTruthy()
    expect(shipmentsCount).toBeTruthy()
  })

  test('WH2: Click "Receipts" navigates to incoming receipts', async ({ page }) => {
    await dashboardPage.clickReceipts()
    await expect(page).toHaveURL(/\/wh\/receipts/, { timeout: 5000 })
  })

  test('WH3: Click "Shipments" navigates to outgoing shipments', async ({ page }) => {
    await dashboardPage.clickShipments()
    await expect(page).toHaveURL(/\/wh\/shipments/, { timeout: 5000 })
  })

  test('WH4: Click "Stock" navigates to stock view', async ({ page }) => {
    await dashboardPage.clickStock()
    await expect(page).toHaveURL(/\/wh\/stock/, { timeout: 5000 })
  })

  test('WH5: Click "Inventory" navigates to inventory acts', async ({ page }) => {
    await dashboardPage.clickInventory()
    await expect(page).toHaveURL(/\/wh\/inventory/, { timeout: 5000 })
  })
})
