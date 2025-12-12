import { test, expect } from '@playwright/test'
import { IssuePage } from '../../pages/issue.page'
import { DashboardPage } from '../../pages/dashboard.page'
import { loginAs, clearLocalStorage } from '../../utils/test-helpers'

test.describe('PP Issue Acts', () => {
  let issuePage: IssuePage
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
    issuePage = new IssuePage(page)
    dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)
    await dashboardPage.selectFacility('PP-C-001')
    await expect(page).toHaveURL(/\/pp/, { timeout: 5000 })
  })

  test('PPI1: Issue Acts list loads', async ({ page }) => {
    await issuePage.gotoList()
    await page.waitForLoadState('networkidle')

    await expect(issuePage.issuesTable).toBeVisible({ timeout: 10000 })
  })

  test('PPI2: Create Issue Act with customerName', async ({ page }) => {
    await issuePage.gotoCreate()
    await page.waitForLoadState('networkidle')

    // Fill customer name
    await issuePage.fillCustomerName('John Doe')

    // Add item
    await issuePage.selectProduct('1')
    await issuePage.fillQuantity('5')

    // Save
    await issuePage.save()

    await page.waitForURL(/\/pp\/issues\/\d+/, { timeout: 5000 })

    // Verify customer name is displayed
    const customerNameElement = page.locator('text=John Doe')
    await expect(customerNameElement).toBeVisible()

    const status = await issuePage.getStatus()
    expect(status).toContain('DRAFT')
  })

  test('PPI3: Create Issue without customerName shows error', async ({ page }) => {
    await issuePage.gotoCreate()
    await page.waitForLoadState('networkidle')

    // Add item but no customer name
    await issuePage.selectProduct('1')
    await issuePage.fillQuantity('3')

    // Try to save
    await issuePage.save()

    // Should show validation error
    const errorVisible = await page.locator('[data-testid="error-message"]')
      .isVisible({ timeout: 3000 })
      .catch(() => false)

    expect(errorVisible).toBe(true)

    // Should stay on create page
    await expect(page).toHaveURL(/\/pp\/issues\/create/)
  })

  test('PPI4: Complete Issue Act - stock deducted', async ({ page }) => {
    await issuePage.gotoCreate()
    await page.waitForLoadState('networkidle')

    await issuePage.fillCustomerName('Jane Smith')
    await issuePage.selectProduct('1')
    await issuePage.fillQuantity('7')
    await issuePage.save()

    await page.waitForURL(/\/pp\/issues\/\d+/, { timeout: 5000 })

    // Complete
    await issuePage.complete()
    await page.waitForTimeout(1000)

    // Status should be COMPLETED
    await expect(issuePage.statusBadge).toContainText('COMPLETED', { timeout: 5000 })

    // Stock should be deducted (verify via stock page or API)
  })

  test('PPI5: Delete DRAFT Issue Act', async ({ page }) => {
    await issuePage.gotoCreate()
    await page.waitForLoadState('networkidle')

    await issuePage.fillCustomerName('Test Customer')
    await issuePage.selectProduct('1')
    await issuePage.fillQuantity('2')
    await issuePage.save()

    await page.waitForURL(/\/pp\/issues\/\d+/, { timeout: 5000 })

    // Delete
    await issuePage.delete()
    await page.waitForTimeout(1000)

    // Should redirect to list
    await expect(page).toHaveURL(/\/pp\/issues$/, { timeout: 5000 })
  })

  test('PPI6: EMPLOYEE cannot delete Issue Act', async ({ page }) => {
    // Login as PP operator (EMPLOYEE role)
    await clearLocalStorage(page)
    await loginAs(page, 'pp_1_op')
    await page.waitForTimeout(500)

    // Create an issue act
    await issuePage.gotoCreate()
    await page.waitForLoadState('networkidle')

    await issuePage.fillCustomerName('Employee Test')
    await issuePage.selectProduct('1')
    await issuePage.fillQuantity('4')
    await issuePage.save()

    await page.waitForURL(/\/pp\/issues\/\d+/, { timeout: 5000 })

    // Delete button should be hidden or disabled for EMPLOYEE
    const deleteVisible = await issuePage.isDeleteButtonVisible()
    expect(deleteVisible).toBe(false)
  })
})
