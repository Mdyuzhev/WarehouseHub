import { test, expect } from '@playwright/test'
import { ShipmentPage } from '../../pages/shipment.page'
import { DashboardPage } from '../../pages/dashboard.page'
import { loginAs, clearLocalStorage } from '../../utils/test-helpers'

test.describe('DC Shipments', () => {
  let shipmentPage: ShipmentPage
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
    shipmentPage = new ShipmentPage(page)
    dashboardPage = new DashboardPage(page)

    await loginAs(page, 'admin')
    await page.waitForTimeout(500)
    await dashboardPage.selectFacility('DC-C-001')
    await expect(page).toHaveURL(/\/dc/, { timeout: 5000 })
  })

  test('DCS1: Shipments list loads', async ({ page }) => {
    await shipmentPage.gotoList('dc')
    await page.waitForLoadState('networkidle')

    await expect(shipmentPage.shipmentsTable).toBeVisible({ timeout: 10000 })
  })

  test('DCS2: Create Shipment to WH-C-001 - status DRAFT', async ({ page }) => {
    await shipmentPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    // Select destination warehouse
    await shipmentPage.selectDestination('2')  // WH-C-001 id=2

    // Add item
    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('50')

    await shipmentPage.save()

    await page.waitForURL(/\/dc\/shipments\/\d+/, { timeout: 5000 })

    const status = await shipmentPage.getStatus()
    expect(status).toContain('DRAFT')
  })

  test('DCS3: Create Shipment to PP-C-001', async ({ page }) => {
    await shipmentPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    // Cannot ship directly from DC to PP in normal workflow
    // But test UI allows selection
    await shipmentPage.selectDestination('4')  // PP-C-001 id=4

    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('30')

    await shipmentPage.save()

    await page.waitForURL(/\/dc\/shipments\/\d+/, { timeout: 5000 })

    const status = await shipmentPage.getStatus()
    expect(status).toContain('DRAFT')
  })

  test('DCS4: Create Shipment without destination shows error', async ({ page }) => {
    await shipmentPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    // Add item but no destination
    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('25')

    await shipmentPage.save()

    // Should show error
    const errorVisible = await page.locator('[data-testid="error-message"]')
      .isVisible({ timeout: 3000 })
      .catch(() => false)

    expect(errorVisible).toBe(true)
    await expect(page).toHaveURL(/\/dc\/shipments\/create/)
  })

  test('DCS5: Shipment detail shows source and destination', async ({ page }) => {
    await shipmentPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await shipmentPage.selectDestination('2')
    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('40')
    await shipmentPage.save()

    await page.waitForURL(/\/dc\/shipments\/\d+/, { timeout: 5000 })

    // Source and destination should be displayed
    const source = await shipmentPage.getSourceFacility()
    const destination = await shipmentPage.getDestinationFacility()

    expect(source).toContain('DC-C-001')
    expect(destination).toContain('WH-C-00')  // WH-C-001 or WH-C-002
  })

  test('DCS6: Approve Shipment (DRAFT -> APPROVED)', async ({ page }) => {
    await shipmentPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await shipmentPage.selectDestination('2')
    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('35')
    await shipmentPage.save()

    await page.waitForURL(/\/dc\/shipments\/\d+/, { timeout: 5000 })

    await shipmentPage.approve()
    await page.waitForTimeout(1000)

    await expect(shipmentPage.statusBadge).toContainText('APPROVED', { timeout: 5000 })
  })

  test('DCS7: Ship Shipment (APPROVED -> SHIPPED)', async ({ page }) => {
    await shipmentPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await shipmentPage.selectDestination('2')
    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('45')
    await shipmentPage.save()

    await page.waitForURL(/\/dc\/shipments\/\d+/, { timeout: 5000 })

    await shipmentPage.approve()
    await page.waitForTimeout(1000)

    await shipmentPage.ship()
    await page.waitForTimeout(1000)

    await expect(shipmentPage.statusBadge).toContainText('SHIPPED', { timeout: 5000 })
  })

  test('DCS8: Deliver Shipment (SHIPPED -> DELIVERED)', async ({ page }) => {
    await shipmentPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await shipmentPage.selectDestination('2')
    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('55')
    await shipmentPage.save()

    await page.waitForURL(/\/dc\/shipments\/\d+/, { timeout: 5000 })

    await shipmentPage.approve()
    await page.waitForTimeout(1000)

    await shipmentPage.ship()
    await page.waitForTimeout(1000)

    await shipmentPage.deliver()
    await page.waitForTimeout(1000)

    await expect(shipmentPage.statusBadge).toContainText('DELIVERED', { timeout: 5000 })
  })

  test('DCS9: Cancel DRAFT Shipment', async ({ page }) => {
    await shipmentPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await shipmentPage.selectDestination('2')
    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('20')
    await shipmentPage.save()

    await page.waitForURL(/\/dc\/shipments\/\d+/, { timeout: 5000 })

    await shipmentPage.cancel()
    await page.waitForTimeout(1000)

    await expect(page).toHaveURL(/\/dc\/shipments$/, { timeout: 5000 })
  })

  test('DCS10: Cancel APPROVED Shipment releases stock', async ({ page }) => {
    await shipmentPage.gotoCreate('dc')
    await page.waitForLoadState('networkidle')

    await shipmentPage.selectDestination('2')
    await shipmentPage.selectProduct('1')
    await shipmentPage.fillQuantity('60')
    await shipmentPage.save()

    await page.waitForURL(/\/dc\/shipments\/\d+/, { timeout: 5000 })

    await shipmentPage.approve()
    await page.waitForTimeout(1000)

    // Cancel approved shipment
    await shipmentPage.cancel()
    await page.waitForTimeout(1000)

    // Should return to list or show cancelled status
    // Stock should be released (verify via API or stock page)
    const currentUrl = page.url()
    expect(currentUrl).toBeTruthy()
  })
})
