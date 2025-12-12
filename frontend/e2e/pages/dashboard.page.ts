import { Page, Locator } from '@playwright/test'

export class DashboardPage {
  readonly page: Page
  readonly receiptsLink: Locator
  readonly shipmentsLink: Locator
  readonly receiptsCount: Locator
  readonly shipmentsCount: Locator
  readonly stockLink: Locator
  readonly inventoryLink: Locator
  readonly issuesLink: Locator
  readonly facilitySelector: Locator
  readonly facilityCode: Locator
  readonly logoutButton: Locator

  constructor(page: Page) {
    this.page = page
    this.receiptsLink = page.locator('[data-testid="receipts-link"]')
    this.shipmentsLink = page.locator('[data-testid="shipments-link"]')
    this.receiptsCount = page.locator('[data-testid="receipts-count"]')
    this.shipmentsCount = page.locator('[data-testid="shipments-count"]')
    this.stockLink = page.locator('[data-testid="stock-link"]')
    this.inventoryLink = page.locator('[data-testid="inventory-link"]')
    this.issuesLink = page.locator('[data-testid="issues-link"]')
    this.facilitySelector = page.locator('[data-testid="facility-selector"]')
    this.facilityCode = page.locator('[data-testid="facility-code"]')
    this.logoutButton = page.locator('[data-testid="logout-button"]')
  }

  async goto(facilityType: 'dc' | 'wh' | 'pp') {
    await this.page.goto(`/${facilityType}`)
  }

  async clickReceipts() {
    await this.receiptsLink.click()
  }

  async clickShipments() {
    await this.shipmentsLink.click()
  }

  async clickStock() {
    await this.stockLink.click()
  }

  async clickInventory() {
    await this.inventoryLink.click()
  }

  async clickIssues() {
    await this.issuesLink.click()
  }

  async getReceiptsCount(): Promise<string> {
    return await this.receiptsCount.textContent() || '0'
  }

  async getShipmentsCount(): Promise<string> {
    return await this.shipmentsCount.textContent() || '0'
  }

  async selectFacility(facilityCode: string) {
    await this.facilitySelector.click()
    await this.page.locator(`[data-testid="facility-option-${facilityCode}"]`).click()
  }

  async getFacilityCode(): Promise<string> {
    return await this.facilityCode.textContent() || ''
  }

  async logout() {
    await this.logoutButton.click()
  }

  async isFacilitySelectorVisible(): Promise<boolean> {
    return await this.facilitySelector.isVisible()
  }
}
