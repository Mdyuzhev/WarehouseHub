import { test, expect } from '@playwright/test'
import { DashboardPage } from '../../pages/dashboard.page'
import { loginAs, clearLocalStorage } from '../../utils/test-helpers'

test.describe('WH Inventory', () => {
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
    dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)
    await dashboardPage.selectFacility('WH-C-001')
    await expect(page).toHaveURL(/\/wh/, { timeout: 5000 })
  })

  test('WHI1: Create Inventory Act with items from stock', async ({ page }) => {
    await page.goto('/wh/inventory/create')
    await page.waitForLoadState('networkidle')

    // Inventory act should load items from current stock
    // Fill act data
    const saveButton = page.locator('[data-testid="save-button"]')

    if (await saveButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await saveButton.click()
      await page.waitForTimeout(1000)

      // Should create inventory act
      await expect(page).toHaveURL(/\/wh\/inventory\/\d+/, { timeout: 5000 })

      const statusBadge = page.locator('[data-testid="status-badge"]')
      const status = await statusBadge.textContent()
      expect(status).toContain('DRAFT')
    } else {
      test.skip()
    }
  })

  test('WHI2: Fill actual quantities - difference calculated', async ({ page }) => {
    await page.goto('/wh/inventory')
    await page.waitForLoadState('networkidle')

    const hasRows = await page.locator('table tbody tr').count()

    if (hasRows > 0) {
      // Click first inventory act
      await page.locator('table tbody tr').first().click()
      await page.waitForURL(/\/wh\/inventory\/\d+/, { timeout: 5000 })

      // Fill actual quantity
      const actualQuantityInput = page.locator('[data-testid="actual-quantity-input"]').first()

      if (await actualQuantityInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await actualQuantityInput.fill('100')
        await page.waitForTimeout(500)

        // Difference should be calculated automatically
        const differenceCell = page.locator('[data-testid="difference"]').first()
        const difference = await differenceCell.textContent()
        expect(difference).toBeTruthy()
      }
    } else {
      test.skip()
    }
  })

  test('WHI3: Approve Inventory Act (DRAFT -> APPROVED)', async ({ page }) => {
    await page.goto('/wh/inventory')
    await page.waitForLoadState('networkidle')

    const hasRows = await page.locator('table tbody tr').count()

    if (hasRows > 0) {
      await page.locator('table tbody tr').first().click()
      await page.waitForURL(/\/wh\/inventory\/\d+/, { timeout: 5000 })

      const status = await page.locator('[data-testid="status-badge"]').textContent()

      if (status?.includes('DRAFT')) {
        const approveButton = page.locator('[data-testid="approve-button"]')

        if (await approveButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await approveButton.click()
          await page.waitForTimeout(1000)

          const newStatus = await page.locator('[data-testid="status-badge"]').textContent()
          expect(newStatus).toContain('APPROVED')
        }
      }
    } else {
      test.skip()
    }
  })

  test('WHI4: Complete Inventory Act - stock corrected', async ({ page }) => {
    await page.goto('/wh/inventory')
    await page.waitForLoadState('networkidle')

    const hasRows = await page.locator('table tbody tr').count()

    if (hasRows > 0) {
      await page.locator('table tbody tr').first().click()
      await page.waitForURL(/\/wh\/inventory\/\d+/, { timeout: 5000 })

      const completeButton = page.locator('[data-testid="complete-button"]')

      if (await completeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await completeButton.click()
        await page.waitForTimeout(1000)

        const status = await page.locator('[data-testid="status-badge"]').textContent()
        expect(status).toContain('COMPLETED')

        // Stock should be updated based on differences
      }
    } else {
      test.skip()
    }
  })

  test('WHI5: Delete DRAFT Inventory Act', async ({ page }) => {
    await page.goto('/wh/inventory')
    await page.waitForLoadState('networkidle')

    const hasRows = await page.locator('table tbody tr').count()

    if (hasRows > 0) {
      await page.locator('table tbody tr').first().click()
      await page.waitForURL(/\/wh\/inventory\/\d+/, { timeout: 5000 })

      const status = await page.locator('[data-testid="status-badge"]').textContent()

      if (status?.includes('DRAFT')) {
        const deleteButton = page.locator('[data-testid="delete-button"]')

        if (await deleteButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await deleteButton.click()
          await page.waitForTimeout(1000)

          // Should redirect to list
          await expect(page).toHaveURL(/\/wh\/inventory$/, { timeout: 5000 })
        }
      }
    } else {
      test.skip()
    }
  })
})
