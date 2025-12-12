import { Page, Locator } from '@playwright/test'

export class ReceiptPage {
  readonly page: Page
  readonly receiptsTable: Locator
  readonly receiptRow: Locator
  readonly createButton: Locator
  readonly supplierInput: Locator
  readonly productSelect: Locator
  readonly quantityInput: Locator
  readonly addItemButton: Locator
  readonly saveButton: Locator
  readonly statusBadge: Locator
  readonly approveButton: Locator
  readonly confirmButton: Locator
  readonly completeButton: Locator
  readonly cancelButton: Locator
  readonly deleteButton: Locator

  constructor(page: Page) {
    this.page = page
    this.receiptsTable = page.locator('[data-testid="receipts-table"]')
    this.receiptRow = page.locator('[data-testid="receipt-row"]')
    this.createButton = page.locator('[data-testid="create-button"]')
    this.supplierInput = page.locator('[data-testid="supplier-input"]')
    this.productSelect = page.locator('[data-testid="product-select"]')
    this.quantityInput = page.locator('[data-testid="quantity-input"]')
    this.addItemButton = page.locator('[data-testid="add-item-button"]')
    this.saveButton = page.locator('[data-testid="save-button"]')
    this.statusBadge = page.locator('[data-testid="status-badge"]')
    this.approveButton = page.locator('[data-testid="approve-button"]')
    this.confirmButton = page.locator('[data-testid="confirm-button"]')
    this.completeButton = page.locator('[data-testid="complete-button"]')
    this.cancelButton = page.locator('[data-testid="cancel-button"]')
    this.deleteButton = page.locator('[data-testid="delete-button"]')
  }

  async gotoList(facilityType: 'dc' | 'wh' | 'pp') {
    await this.page.goto(`/${facilityType}/receipts`)
  }

  async gotoCreate(facilityType: 'dc' | 'wh' | 'pp') {
    await this.page.goto(`/${facilityType}/receipts/create`)
  }

  async gotoDetail(facilityType: 'dc' | 'wh' | 'pp', id: string) {
    await this.page.goto(`/${facilityType}/receipts/${id}`)
  }

  async clickRow(index: number = 0) {
    await this.receiptRow.nth(index).click()
  }

  async fillSupplier(supplier: string) {
    await this.supplierInput.fill(supplier)
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

  async confirm() {
    await this.confirmButton.click()
  }

  async complete() {
    await this.completeButton.click()
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

  async isApproveButtonVisible(): Promise<boolean> {
    try {
      await this.approveButton.waitFor({ state: 'visible', timeout: 1000 })
      return true
    } catch {
      return false
    }
  }

  async waitForTableLoad() {
    await this.page.waitForSelector('table tbody tr', { timeout: 10000 })
  }
}
