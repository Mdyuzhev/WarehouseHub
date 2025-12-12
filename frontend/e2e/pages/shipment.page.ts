import { Page, Locator } from '@playwright/test'

export class ShipmentPage {
  readonly page: Page
  readonly shipmentsTable: Locator
  readonly shipmentRow: Locator
  readonly createButton: Locator
  readonly destinationSelect: Locator
  readonly productSelect: Locator
  readonly quantityInput: Locator
  readonly addItemButton: Locator
  readonly saveButton: Locator
  readonly statusBadge: Locator
  readonly approveButton: Locator
  readonly shipButton: Locator
  readonly deliverButton: Locator
  readonly cancelButton: Locator
  readonly deleteButton: Locator
  readonly sourceFacility: Locator
  readonly destinationFacility: Locator

  constructor(page: Page) {
    this.page = page
    this.shipmentsTable = page.locator('[data-testid="shipments-table"]')
    this.shipmentRow = page.locator('[data-testid="shipment-row"]')
    this.createButton = page.locator('[data-testid="create-button"]')
    this.destinationSelect = page.locator('[data-testid="destination-select"]')
    this.productSelect = page.locator('[data-testid="product-select"]')
    this.quantityInput = page.locator('[data-testid="quantity-input"]')
    this.addItemButton = page.locator('[data-testid="add-item-button"]')
    this.saveButton = page.locator('[data-testid="save-button"]')
    this.statusBadge = page.locator('[data-testid="status-badge"]')
    this.approveButton = page.locator('[data-testid="approve-button"]')
    this.shipButton = page.locator('[data-testid="ship-button"]')
    this.deliverButton = page.locator('[data-testid="deliver-button"]')
    this.cancelButton = page.locator('[data-testid="cancel-button"]')
    this.deleteButton = page.locator('[data-testid="delete-button"]')
    this.sourceFacility = page.locator('[data-testid="source-facility"]')
    this.destinationFacility = page.locator('[data-testid="destination-facility"]')
  }

  async gotoList(facilityType: 'dc' | 'wh' | 'pp') {
    await this.page.goto(`/${facilityType}/shipments`)
  }

  async gotoCreate(facilityType: 'dc' | 'wh' | 'pp') {
    await this.page.goto(`/${facilityType}/shipments/create`)
  }

  async gotoDetail(facilityType: 'dc' | 'wh' | 'pp', id: string) {
    await this.page.goto(`/${facilityType}/shipments/${id}`)
  }

  async clickRow(index: number = 0) {
    await this.shipmentRow.nth(index).click()
  }

  async selectDestination(facilityId: string) {
    await this.destinationSelect.selectOption(facilityId)
  }

  async selectProduct(productId: string) {
    await this.productSelect.selectOption(productId)
  }

  async fillQuantity(quantity: string) {
    await this.quantityInput.fill(quantity)
  }

  async addItem() {
    await this.addItemButton.click()
  }

  async save() {
    await this.saveButton.click()
  }

  async approve() {
    await this.approveButton.click()
  }

  async ship() {
    await this.shipButton.click()
  }

  async deliver() {
    await this.deliverButton.click()
  }

  async cancel() {
    await this.cancelButton.click()
  }

  async delete() {
    await this.deleteButton.click()
  }

  async getStatus(): Promise<string> {
    return await this.statusBadge.textContent() || ''
  }

  async getSourceFacility(): Promise<string> {
    return await this.sourceFacility.textContent() || ''
  }

  async getDestinationFacility(): Promise<string> {
    return await this.destinationFacility.textContent() || ''
  }

  async waitForTableLoad() {
    await this.page.waitForSelector('table tbody tr', { timeout: 10000 })
  }
}
