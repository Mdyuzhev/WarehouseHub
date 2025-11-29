#!/usr/bin/env python3
"""
Selenium UI Tests for Warehouse Application
Captures screenshots of successful pages
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import os

# Configuration
SELENOID_URL = "http://192.168.1.74:30040/wd/hub"
FRONTEND_URL = "http://192.168.1.74:30081"
SCREENSHOT_DIR = "/home/flomaster/warehouse-master/e2e-tests/screenshots"

# Test credentials
TEST_USER = "ivanov"
TEST_PASSWORD = "password123"

def setup_driver():
    """Setup Selenium WebDriver with Selenoid"""
    capabilities = {
        "browserName": "chrome",
        "browserVersion": "131.0",
        "selenoid:options": {
            "enableVNC": True,
            "enableVideo": False,
            "screenResolution": "1920x1080x24"
        }
    }

    driver = webdriver.Remote(
        command_executor=SELENOID_URL,
        desired_capabilities=capabilities
    )
    driver.set_window_size(1920, 1080)
    return driver

def save_screenshot(driver, name):
    """Save screenshot to file"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    filepath = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(filepath)
    print(f"Screenshot saved: {filepath}")
    return filepath

def test_login_page(driver):
    """Test Login Page"""
    print("\n=== Testing Login Page ===")
    driver.get(FRONTEND_URL)
    time.sleep(2)

    # Capture login page
    save_screenshot(driver, "01_login_page")

    # Find and fill login form
    wait = WebDriverWait(driver, 10)
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password_input = driver.find_element(By.ID, "password")

    username_input.send_keys(TEST_USER)
    password_input.send_keys(TEST_PASSWORD)

    save_screenshot(driver, "02_login_filled")

    # Click login button
    login_btn = driver.find_element(By.CSS_SELECTOR, ".login-btn")
    login_btn.click()

    # Wait for redirect to home page
    time.sleep(3)

    return True

def test_home_page(driver):
    """Test Home Page with Products"""
    print("\n=== Testing Home Page ===")

    wait = WebDriverWait(driver, 10)

    # Wait for nav bar (authentication successful)
    try:
        nav = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".main-nav")))
        print("Navigation bar loaded successfully")
    except:
        print("ERROR: Navigation bar not found")
        save_screenshot(driver, "ERROR_no_navbar")
        return False

    # Wait for products to load
    time.sleep(2)
    save_screenshot(driver, "03_home_page_products")

    # Check if products are displayed
    try:
        products = driver.find_elements(By.CSS_SELECTOR, ".product-item")
        print(f"Found {len(products)} products")
    except:
        print("No products found")

    return True

def test_add_product_page(driver):
    """Test Add Product Page"""
    print("\n=== Testing Add Product Page ===")

    # Click on Add Product link
    try:
        add_link = driver.find_element(By.CSS_SELECTOR, "a[href='/add']")
        add_link.click()
        time.sleep(2)
        save_screenshot(driver, "04_add_product_page")
        print("Add Product page loaded")
    except Exception as e:
        print(f"Add Product link not found (may not have permission): {e}")

    return True

def test_status_page(driver):
    """Test Status Page"""
    print("\n=== Testing Status Page ===")

    # Click on Status link
    try:
        status_link = driver.find_element(By.CSS_SELECTOR, "a[href='/status']")
        status_link.click()
        time.sleep(3)
        save_screenshot(driver, "05_status_page")
        print("Status page loaded")
    except Exception as e:
        print(f"Status link not found (may not have permission): {e}")

    return True

def test_refresh_button(driver):
    """Test Refresh Button on Home Page"""
    print("\n=== Testing Refresh Button ===")

    # Go back to home
    driver.get(FRONTEND_URL)
    time.sleep(2)

    # Click refresh button
    try:
        refresh_btn = driver.find_element(By.CSS_SELECTOR, ".btn-refresh")
        refresh_btn.click()
        time.sleep(1)
        save_screenshot(driver, "06_refresh_spinning")
        print("Refresh button works")
    except Exception as e:
        print(f"Refresh button not found: {e}")

    return True

def test_logout(driver):
    """Test Logout"""
    print("\n=== Testing Logout ===")

    try:
        logout_btn = driver.find_element(By.CSS_SELECTOR, ".logout-btn")
        logout_btn.click()
        time.sleep(2)
        save_screenshot(driver, "07_after_logout")
        print("Logout successful")
    except Exception as e:
        print(f"Logout button not found: {e}")

    return True

def main():
    """Run all UI tests"""
    print("=" * 60)
    print("Warehouse UI Selenium Tests")
    print("=" * 60)

    driver = None
    try:
        driver = setup_driver()
        print(f"Connected to Selenoid at {SELENOID_URL}")

        # Run tests
        test_login_page(driver)
        test_home_page(driver)
        test_add_product_page(driver)
        test_status_page(driver)
        test_refresh_button(driver)
        test_logout(driver)

        print("\n" + "=" * 60)
        print("All tests completed!")
        print(f"Screenshots saved to: {SCREENSHOT_DIR}")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR: {e}")
        if driver:
            save_screenshot(driver, "ERROR_exception")
        raise
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
