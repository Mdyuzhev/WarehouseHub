import { Page, Locator } from '@playwright/test'

export class IssuePage {
  readonly page: Page
  readonly issuesTable: Locator
  readonly issueRow: Locator
  readonly createButton: Locator
  readonly customerNameInput: Locator
  readonly productSelect: Locator
  readonly quantityInput: Locator
  readonly addItemButton: Locator
  readonly saveButton: Locator
  readonly statusBadge: Locator
  readonly completeButton: Locator
  readonly deleteButton: Locator

  constructor(page: Page) {
    this.page = page
    this.issuesTable = page.locator('[data-testid="issues-table"]')
    this.issueRow = page.locator('[data-testid="issue-row"]')
    this.createButton = page.locator('[data-testid="create-button"]')
    this.customerNameInput = page.locator('[data-testid="customer-name-input"]')
    this.productSelect = page.locator('[data-testid="product-select"]')
    this.quantityInput = page.locator('[data-testid="quantity-input"]')
    this.addItemButton = page.locator('[data-testid="add-item-button"]')
    this.saveButton = page.locator('[data-testid="save-button"]')
    this.statusBadge = page.locator('[data-testid="status-badge"]')
    this.completeButton = page.locator('[data-testid="complete-button"]')
    this.deleteButton = page.locator('[data-testid="delete-button"]')
  }

  async gotoList() {
    await this.page.goto('/pp/issues')
  }

  async gotoCreate() {
    await this.page.goto('/pp/issues/create')
  }

  async gotoDetail(id: string) {
    await this.page.goto(`/pp/issues/${id}`)
  }

  async clickRow(index: number = 0) {
    await this.issueRow.nth(index).click()
  }

  async fillCustomerName(name: string) {
    await this.customerNameInput.fill(name)
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

  async complete() {
    await this.completeButton.click()
  }

  async delete() {
    await this.deleteButton.click()
  }

  async getStatus(): Promise<string> {
    return await this.statusBadge.textContent() || ''
  }

  async isDeleteButtonVisible(): Promise<boolean> {
    try {
      await this.deleteButton.waitFor({ state: 'visible', timeout: 1000 })
      return true
    } catch {
      return false
    }
  }

  async waitForTableLoad() {
    await this.page.waitForSelector('table tbody tr', { timeout: 10000 })
  }
}
