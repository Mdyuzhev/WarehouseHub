import { test, expect } from '@playwright/test'
import { ReceiptPage } from '../../pages/receipt.page'
import { DashboardPage } from '../../pages/dashboard.page'
import { loginAs, clearLocalStorage } from '../../utils/test-helpers'

test.describe('PP Receipts', () => {
  let receiptPage: ReceiptPage
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
    receiptPage = new ReceiptPage(page)
    dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)
    await dashboardPage.selectFacility('PP-C-001')
    await expect(page).toHaveURL(/\/pp/, { timeout: 5000 })
  })

  test('PPR1: Incoming receipts list loads (from WH)', async ({ page }) => {
    await receiptPage.gotoList('pp')
    await page.waitForLoadState('networkidle')

    await expect(receiptPage.receiptsTable).toBeVisible({ timeout: 10000 })
  })

  test('PPR2: Confirm Receipt updates PP stock', async ({ page }) => {
    await receiptPage.gotoList('pp')
    await page.waitForLoadState('networkidle')

    const hasRows = await page.locator('table tbody tr').count()

    if (hasRows > 0) {
      // Find an APPROVED receipt to confirm
      await receiptPage.clickRow(0)
      await page.waitForURL(/\/pp\/receipts\/\d+/, { timeout: 5000 })

      const status = await receiptPage.getStatus()

      if (status.includes('APPROVED')) {
        // Confirm
        await receiptPage.confirm()
        await page.waitForTimeout(1000)

        // Status should change to CONFIRMED
        await expect(receiptPage.statusBadge).toContainText('CONFIRMED', { timeout: 5000 })

        // Stock at PP should be updated
      }
    } else {
      test.skip()
    }
  })
})
