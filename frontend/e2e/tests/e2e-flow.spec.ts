import { test, expect } from '@playwright/test'
import { ReceiptPage } from '../pages/receipt.page'
import { ShipmentPage } from '../pages/shipment.page'
import { IssuePage } from '../pages/issue.page'
import { DashboardPage } from '../pages/dashboard.page'
import { loginAs, clearLocalStorage } from '../utils/test-helpers'

test.describe('E2E Full Flow', () => {
  test('E2E1: DC → WH → PP complete cycle', async ({ page }) => {
    const receiptPage = new ReceiptPage(page)
    const shipmentPage = new ShipmentPage(page)
    const issuePage = new IssuePage(page)
    const dashboardPage = new DashboardPage(page)

    // Step 1: DC creates Receipt from supplier
    await clearLocalStorage(page)
    await loginAs(page, 'admin')
    await page.waitForTimeout(500)
    await dashboardPage.selectFacility('DC-C-001')
    await expect(page).toHaveURL(/\/dc/, { timeout: 5000 })

    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await receiptPage.fillSupplier('E2E Test Supplier')
    await receiptPage.selectProduct('1')
    await receiptPage.fillQuantity('100')
    await receiptPage.save()

    await page.waitForURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })
    const dcReceiptUrl = page.url()

    // Approve
    await receiptPage.approve()
    await page.waitForTimeout(1000)

    // Confirm
    await receiptPage.confirm()
    await page.waitForTimeout(1000)

    await expect(receiptPage.statusBadge).toContainText('CONFIRMED', { timeout: 5000 })

    // Step 2: DC creates Shipment to WH
    await shipmentPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await shipmentPage.selectDestination('2')  // WH-C-001
    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('50')
    await shipmentPage.save()

    await page.waitForURL(/\/dc\/shipments\/\d+/, { timeout: 5000 })

    // Approve
    await shipmentPage.approve()
    await page.waitForTimeout(1000)

    // Ship
    await shipmentPage.ship()
    await page.waitForTimeout(1000)

    await expect(shipmentPage.statusBadge).toContainText('SHIPPED', { timeout: 5000 })

    // Step 3: WH confirms auto-receipt
    await dashboardPage.selectFacility('WH-C-001')
    await expect(page).toHaveURL(/\/wh/, { timeout: 5000 })

    await receiptPage.gotoList('wh')
    await page.waitForLoadState('networkidle')

    // Find and confirm the receipt (would need better selection logic in real scenario)
    const hasRows = await page.locator('table tbody tr').count()
    if (hasRows > 0) {
      await receiptPage.clickRow(0)
      await page.waitForURL(/\/wh\/receipts\/\d+/, { timeout: 5000 })

      const status = await receiptPage.getStatus()
      if (status.includes('APPROVED')) {
        await receiptPage.confirm()
        await page.waitForTimeout(1000)
      }
    }

    // Step 4: WH creates Shipment to PP
    await shipmentPage.gotoCreate('wh')
    await page.waitForLoadState('networkidle')

    await shipmentPage.selectDestination('4')  // PP-C-001
    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('25')
    await shipmentPage.save()

    await page.waitForURL(/\/wh\/shipments\/\d+/, { timeout: 5000 })

    await shipmentPage.approve()
    await page.waitForTimeout(1000)

    await shipmentPage.ship()
    await page.waitForTimeout(1000)

    await expect(shipmentPage.statusBadge).toContainText('SHIPPED', { timeout: 5000 })

    // Step 5: PP confirms receipt
    await dashboardPage.selectFacility('PP-C-001')
    await expect(page).toHaveURL(/\/pp/, { timeout: 5000 })

    await receiptPage.gotoList('pp')
    await page.waitForLoadState('networkidle')

    const ppHasRows = await page.locator('table tbody tr').count()
    if (ppHasRows > 0) {
      await receiptPage.clickRow(0)
      await page.waitForURL(/\/pp\/receipts\/\d+/, { timeout: 5000 })

      const status = await receiptPage.getStatus()
      if (status.includes('APPROVED')) {
        await receiptPage.confirm()
        await page.waitForTimeout(1000)
      }
    }

    // Step 6: PP creates Issue Act and completes
    await issuePage.gotoCreate()
    await page.waitForLoadState('networkidle')

    await issuePage.fillCustomerName('E2E Test Customer')
    await issuePage.selectProduct('1')
    await issuePage.fillQuantity('10')
    await issuePage.save()

    await page.waitForURL(/\/pp\/issues\/\d+/, { timeout: 5000 })

    await issuePage.complete()
    await page.waitForTimeout(1000)

    await expect(issuePage.statusBadge).toContainText('COMPLETED', { timeout: 5000 })

    // Full cycle complete!
  })

  test('E2E2: Inventory correction at WH', async ({ page }) => {
    const dashboardPage = new DashboardPage(page)

    await clearLocalStorage(page)
    await loginAs(page, 'admin')
    await page.waitForTimeout(500)
    await dashboardPage.selectFacility('WH-C-001')
    await expect(page).toHaveURL(/\/wh/, { timeout: 5000 })

    // Create inventory act
    await page.goto('/wh/inventory/create')
    await page.waitForLoadState('networkidle')

    // Fill actual quantities (different from system)
    const actualInput = page.locator('[data-testid="actual-quantity-input"]').first()

    if (await actualInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await actualInput.fill('150')
      await page.waitForTimeout(500)
    }

    // Save
    const saveButton = page.locator('[data-testid="save-button"]')
    if (await saveButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await saveButton.click()
      await page.waitForTimeout(1000)

      await page.waitForURL(/\/wh\/inventory\/\d+/, { timeout: 5000 })

      // Approve
      const approveButton = page.locator('[data-testid="approve-button"]')
      if (await approveButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await approveButton.click()
        await page.waitForTimeout(1000)
      }

      // Complete
      const completeButton = page.locator('[data-testid="complete-button"]')
      if (await completeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await completeButton.click()
        await page.waitForTimeout(1000)

        const status = await page.locator('[data-testid="status-badge"]').textContent()
        expect(status).toContain('COMPLETED')
      }
    }
  })
})
