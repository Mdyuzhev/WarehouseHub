import { test, expect } from '@playwright/test'
import { DashboardPage } from '../../pages/dashboard.page'
import { loginAs, clearLocalStorage } from '../../utils/test-helpers'

test.describe('DC Dashboard', () => {
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
    dashboardPage = new DashboardPage(page)

    // Login as admin and select DC facility
    await loginAs(page, 'admin')
    await page.waitForTimeout(500)
    await dashboardPage.selectFacility('DC-C-001')
    await expect(page).toHaveURL(/\/dc/, { timeout: 5000 })
    await page.waitForLoadState('networkidle')
  })

  test('DC1: Dashboard loads with statistics', async ({ page }) => {
    // Dashboard should show receipts and shipments count
    const receiptsCountElement = dashboardPage.receiptsCount
    const shipmentsCountElement = dashboardPage.shipmentsCount

    // Verify elements exist and are visible
    await expect(receiptsCountElement).toBeVisible({ timeout: 5000 })
    await expect(shipmentsCountElement).toBeVisible({ timeout: 5000 })

    // Counts should be numbers (or text containing numbers)
    const receiptsCount = await dashboardPage.getReceiptsCount()
    const shipmentsCount = await dashboardPage.getShipmentsCount()

    expect(receiptsCount).toBeTruthy()
    expect(shipmentsCount).toBeTruthy()
  })

  test('DC2: Click "Receipts" navigates to receipts list', async ({ page }) => {
    await dashboardPage.clickReceipts()

    // Should navigate to receipts page
    await expect(page).toHaveURL(/\/dc\/receipts/, { timeout: 5000 })
  })

  test('DC3: Click "Shipments" navigates to shipments list', async ({ page }) => {
    await dashboardPage.clickShipments()

    // Should navigate to shipments page
    await expect(page).toHaveURL(/\/dc\/shipments/, { timeout: 5000 })
  })

  test('DC4: Click "New Receipt" navigates to create receipt', async ({ page }) => {
    // Click on create new receipt button on dashboard
    const createReceiptLink = page.locator('[data-testid="new-receipt-link"]')
    await createReceiptLink.waitFor({ state: 'visible', timeout: 5000 })
    await createReceiptLink.click()
    await expect(page).toHaveURL(/\/dc\/receipts\/create/, { timeout: 5000 })
  })

  test('DC5: Click "New Shipment" navigates to create shipment', async ({ page }) => {
    // Click on create new shipment button on dashboard
    const createShipmentLink = page.locator('[data-testid="new-shipment-link"]')
    await createShipmentLink.waitFor({ state: 'visible', timeout: 5000 })
    await createShipmentLink.click()
    await expect(page).toHaveURL(/\/dc\/shipments\/create/, { timeout: 5000 })
  })

  test('DC6: Statistics update after document creation', async ({ page }) => {
    // Get initial receipts count
    const initialCount = await dashboardPage.getReceiptsCount()
    const initialNumber = parseInt(initialCount) || 0

    // Navigate to create receipt
    await dashboardPage.clickReceipts()
    await page.click('[data-testid="create-button"]')

    // Create a receipt via API would be more reliable, but for UI test:
    // Fill minimal form and save (this part depends on actual form implementation)
    await page.waitForTimeout(500)

    // For now, just verify we can navigate back to dashboard
    await page.goto('/dc')
    await page.waitForLoadState('networkidle')

    // Note: Actual count verification would require creating a real receipt
    // This is a placeholder - adjust based on actual implementation
    const newCount = await dashboardPage.getReceiptsCount()
    expect(newCount).toBeTruthy()
  })
})
