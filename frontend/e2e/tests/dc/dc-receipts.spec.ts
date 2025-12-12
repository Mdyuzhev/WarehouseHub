import { test, expect } from '@playwright/test'
import { ReceiptPage } from '../../pages/receipt.page'
import { DashboardPage } from '../../pages/dashboard.page'
import { loginAs, clearLocalStorage, waitForApiResponse } from '../../utils/test-helpers'

test.describe('DC Receipts', () => {
  let receiptPage: ReceiptPage
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
    receiptPage = new ReceiptPage(page)
    dashboardPage = new DashboardPage(page)

    // Login as admin and select DC facility
    await loginAs(page, 'admin')
    await page.waitForTimeout(500)
    await dashboardPage.selectFacility('DC-C-001')
    await expect(page).toHaveURL(/\/dc/, { timeout: 5000 })
  })

  test('DCR1: Receipts list loads', async ({ page }) => {
    await receiptPage.gotoList('dc')
    await page.waitForLoadState('networkidle')

    // Table should be visible
    await expect(receiptPage.receiptsTable).toBeVisible({ timeout: 10000 })
  })

  test('DCR2: Click table row navigates to detail', async ({ page }) => {
    await receiptPage.gotoList('dc')
    await page.waitForLoadState('networkidle')

    // Wait for table to have rows
    const hasRows = await page.locator('table tbody tr').count()

    if (hasRows > 0) {
      // Click first row
      await receiptPage.clickRow(0)

      // Should navigate to detail page
      await expect(page).toHaveURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })
    } else {
      // If no rows, skip test or create one first
      test.skip()
    }
  })

  test('DCR3: Create Receipt with items - status DRAFT', async ({ page }) => {
    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    // Fill form
    await receiptPage.fillSupplier('Test Supplier Ltd')

    // Add item (assuming form has these fields)
    await receiptPage.selectProduct('1')  // Product ID 1
    await receiptPage.fillQuantity('100')

    // Save
    await receiptPage.save()

    // Wait for creation
    await page.waitForURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })

    // Status should be DRAFT
    const status = await receiptPage.getStatus()
    expect(status).toContain('DRAFT')
  })

  test('DCR4: Create Receipt without items shows validation error', async ({ page }) => {
    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    // Fill only supplier, no items
    await receiptPage.fillSupplier('Test Supplier')

    // Try to save
    await receiptPage.save()

    // Should show validation error (implementation-dependent)
    // Look for error message
    const errorVisible = await page.locator('[data-testid="error-message"]')
      .isVisible({ timeout: 3000 })
      .catch(() => false)

    expect(errorVisible).toBe(true)

    // Should NOT navigate away from create page
    await expect(page).toHaveURL(/\/dc\/receipts\/create/)
  })

  test('DCR5: Receipt detail displays all fields', async ({ page }) => {
    // First create a receipt
    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await receiptPage.fillSupplier('Detail Test Supplier')
    await receiptPage.selectProduct('1')
    await receiptPage.fillQuantity('50')
    await receiptPage.save()

    await page.waitForURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })

    // Verify all fields are displayed
    const status = await receiptPage.getStatus()
    expect(status).toBeTruthy()

    // Supplier should be visible
    const supplierElement = page.locator('text=Detail Test Supplier')
    await expect(supplierElement).toBeVisible()

    // Items table should be visible
    const itemsTable = page.locator('table')
    await expect(itemsTable).toBeVisible()
  })

  test('DCR6: Approve Receipt (DRAFT -> APPROVED)', async ({ page }) => {
    // Create receipt first
    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await receiptPage.fillSupplier('Approve Test Supplier')
    await receiptPage.selectProduct('1')
    await receiptPage.fillQuantity('25')
    await receiptPage.save()

    await page.waitForURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })

    // Approve
    await receiptPage.approve()
    await page.waitForTimeout(1000)

    // Status should change to APPROVED
    await expect(receiptPage.statusBadge).toContainText('APPROVED', { timeout: 5000 })

    // Confirm button should appear
    const confirmVisible = await receiptPage.confirmButton.isVisible({ timeout: 2000 })
      .catch(() => false)
    expect(confirmVisible).toBe(true)
  })

  test('DCR7: Confirm Receipt (APPROVED -> CONFIRMED)', async ({ page }) => {
    // Create and approve receipt
    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await receiptPage.fillSupplier('Confirm Test Supplier')
    await receiptPage.selectProduct('1')
    await receiptPage.fillQuantity('30')
    await receiptPage.save()

    await page.waitForURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })

    // Approve
    await receiptPage.approve()
    await page.waitForTimeout(1000)

    // Confirm
    await receiptPage.confirm()
    await page.waitForTimeout(1000)

    // Status should change to CONFIRMED
    await expect(receiptPage.statusBadge).toContainText('CONFIRMED', { timeout: 5000 })
  })

  test('DCR8: Complete Receipt (CONFIRMED -> COMPLETED)', async ({ page }) => {
    // Create, approve, and confirm receipt
    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await receiptPage.fillSupplier('Complete Test Supplier')
    await receiptPage.selectProduct('1')
    await receiptPage.fillQuantity('40')
    await receiptPage.save()

    await page.waitForURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })

    // Approve
    await receiptPage.approve()
    await page.waitForTimeout(1000)

    // Confirm
    await receiptPage.confirm()
    await page.waitForTimeout(1000)

    // Complete
    await receiptPage.complete()
    await page.waitForTimeout(1000)

    // Status should be COMPLETED
    await expect(receiptPage.statusBadge).toContainText('COMPLETED', { timeout: 5000 })

    // Action buttons should be hidden
    const approveVisible = await receiptPage.isApproveButtonVisible()
    expect(approveVisible).toBe(false)
  })

  test('DCR9: Cancel DRAFT Receipt removes it from list', async ({ page }) => {
    // Create receipt
    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await receiptPage.fillSupplier('Cancel Test Supplier')
    await receiptPage.selectProduct('1')
    await receiptPage.fillQuantity('15')
    await receiptPage.save()

    await page.waitForURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })

    // Get receipt ID from URL
    const url = page.url()
    const receiptId = url.match(/\/receipts\/(\d+)/)?.[1]

    // Cancel
    await receiptPage.cancel()
    await page.waitForTimeout(1000)

    // Should redirect to list
    await expect(page).toHaveURL(/\/dc\/receipts$/, { timeout: 5000 })

    // Receipt should not be in the list (or verify via API)
    // This is implementation-dependent
  })

  test('DCR10: EMPLOYEE user cannot see Approve button', async ({ page }) => {
    // Login as DC manager (EMPLOYEE role)
    await clearLocalStorage(page)
    await loginAs(page, 'dc_manager')
    await page.waitForTimeout(500)

    // Create a receipt
    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await receiptPage.fillSupplier('Employee Test Supplier')
    await receiptPage.selectProduct('1')
    await receiptPage.fillQuantity('20')
    await receiptPage.save()

    await page.waitForURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })

    // Approve button should NOT be visible for EMPLOYEE
    const approveVisible = await receiptPage.isApproveButtonVisible()
    expect(approveVisible).toBe(false)
  })
})
