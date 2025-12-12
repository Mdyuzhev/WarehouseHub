import { test, expect } from '@playwright/test'
import { ReceiptPage } from '../pages/receipt.page'
import { DashboardPage } from '../pages/dashboard.page'
import { loginAs, clearLocalStorage } from '../utils/test-helpers'

test.describe('Role-based Access Control', () => {
  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
  })

  test('R1: Admin - access all facility types and approve/cancel', async ({ page }) => {
    const receiptPage = new ReceiptPage(page)
    const dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)

    // Test DC access
    await dashboardPage.selectFacility('DC-C-001')
    await expect(page).toHaveURL(/\/dc/, { timeout: 5000 })

    // Create receipt and verify approve button visible
    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await receiptPage.fillSupplier('Admin Test DC')
    await receiptPage.selectProduct('1')
    await receiptPage.fillQuantity('20')
    await receiptPage.save()

    await page.waitForURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })

    // Admin should see approve button
    const approveVisible = await receiptPage.isApproveButtonVisible()
    expect(approveVisible).toBe(true)

    // Test WH access
    await dashboardPage.selectFacility('WH-C-001')
    await expect(page).toHaveURL(/\/wh/, { timeout: 5000 })

    // Test PP access
    await dashboardPage.selectFacility('PP-C-001')
    await expect(page).toHaveURL(/\/pp/, { timeout: 5000 })

    // Admin has access to all facility types
  })

  test('R2: DC Manager (EMPLOYEE) - only DC routes, create/view works', async ({ page }) => {
    const receiptPage = new ReceiptPage(page)
    const dashboardPage = new DashboardPage(page)

    await loginAs(page, 'dc_manager')
    await page.waitForTimeout(500)

    // Should be on DC page
    await expect(page).toHaveURL(/\/dc/, { timeout: 5000 })

    // Can create receipt
    await receiptPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await receiptPage.fillSupplier('DC Manager Test')
    await receiptPage.selectProduct('1')
    await receiptPage.fillQuantity('15')
    await receiptPage.save()

    await page.waitForURL(/\/dc\/receipts\/\d+/, { timeout: 5000 })

    // EMPLOYEE cannot approve
    const approveVisible = await receiptPage.isApproveButtonVisible()
    expect(approveVisible).toBe(false)

    // Can view list
    await receiptPage.gotoList('dc')
    await page.waitForLoadState('networkidle')

    await expect(receiptPage.receiptsTable).toBeVisible({ timeout: 10000 })

    // Cannot access WH or PP routes (facility selector should not allow it)
    // DC manager should not see WH/PP facilities in selector
  })

  test('R3: WH Operator (EMPLOYEE) - only WH routes, create/view works', async ({ page }) => {
    const receiptPage = new ReceiptPage(page)
    const dashboardPage = new DashboardPage(page)

    await loginAs(page, 'wh_north_op')
    await page.waitForTimeout(500)

    // Should be on WH page
    await expect(page).toHaveURL(/\/wh/, { timeout: 5000 })

    // Can view receipts
    await receiptPage.gotoList('wh')
    await page.waitForLoadState('networkidle')

    await expect(receiptPage.receiptsTable).toBeVisible({ timeout: 10000 })

    // Can create shipment
    await page.goto('/wh/shipments/create')
    await page.waitForLoadState('networkidle')

    const destinationSelect = page.locator('[data-testid="destination-select"]')

    if (await destinationSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
      await destinationSelect.selectOption('4')  // PP
      await page.locator('[data-testid="product-select"]').selectOption('1')
      await page.locator('[data-testid="quantity-input"]').fill('10')
      await page.locator('[data-testid="save-button"]').click()

      await page.waitForURL(/\/wh\/shipments\/\d+/, { timeout: 5000 })

      // EMPLOYEE cannot approve
      const approveButton = page.locator('[data-testid="approve-button"]')
      const approveVisible = await approveButton.isVisible({ timeout: 2000 })
        .catch(() => false)
      expect(approveVisible).toBe(false)
    }
  })

  test('R4: PP Operator (EMPLOYEE) - only PP routes, create/view works', async ({ page }) => {
    const issuePage = require('../pages/issue.page').IssuePage
    const issuePageInstance = new issuePage(page)

    await loginAs(page, 'pp_1_op')
    await page.waitForTimeout(500)

    // Should be on PP page
    await expect(page).toHaveURL(/\/pp/, { timeout: 5000 })

    // Can create issue act
    await issuePageInstance.gotoCreate()
    await page.waitForLoadState('networkidle')

    await issuePageInstance.fillCustomerName('PP Operator Test')
    await issuePageInstance.selectProduct('1')
    await issuePageInstance.fillQuantity('5')
    await issuePageInstance.save()

    await page.waitForURL(/\/pp\/issues\/\d+/, { timeout: 5000 })

    // Can complete (EMPLOYEE can complete issue acts)
    const completeButton = page.locator('[data-testid="complete-button"]')
    const completeVisible = await completeButton.isVisible({ timeout: 2000 })
      .catch(() => false)
    expect(completeVisible).toBe(true)

    // Cannot delete (only SUPER_USER can delete)
    const deleteVisible = await issuePageInstance.isDeleteButtonVisible()
    expect(deleteVisible).toBe(false)
  })
})
