#section imports
import time
import json
import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd


# Function to load credentials from the JSON file
def load_credentials():
    with open('credentials.json', 'r') as file:
        credentials = json.load(file)
    return credentials['username'], credentials['password']

# Categories to scrape
CATEGORIES = [
    "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0",
    "https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0",
    # "https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0",
    # "https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0",
]

MAX_PRODUCTS = 10  # Limit to 1500 best-selling products per category
DISCOUNT_THRESHOLD = 50  # Discount > 50%

# Initialize Selenium WebDriver with WebDriver Manager in Headless Mode
def initialize_driver(headless=True):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    
    if headless:
        options.add_argument("--headless")  # Run in hidden mode
        options.add_argument("--disable-gpu")  # Disable GPU for headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
    
    # Initialize WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Function to check for CAPTCHA
def is_captcha_present(driver):
    try:
        # Check if CAPTCHA is present by looking for known CAPTCHA elements
        driver.find_element(By.ID, "captchacharacters")  # or another CAPTCHA identifier
        return True
    except NoSuchElementException:
        return False
    
# Wait for CAPTCHA resolution
def wait_for_captcha_resolution(driver):
    print("CAPTCHA detected. Please solve it manually within 5 minutes...")
    try:
        WebDriverWait(driver, 300).until(lambda d: not is_captcha_present(d))
        print("CAPTCHA solved! Resuming operations.")
    except TimeoutException:
        print("CAPTCHA not solved within 5 minutes. Exiting.")
        driver.quit()
        exit(1)

# Wait for the page to load by detecting a URL change
def wait_for_page_to_load(driver, current_url):
    try:
        WebDriverWait(driver, 10).until(
            EC.url_changes(current_url)
        )
        print("Next page loaded.")
        return True
    except TimeoutException:
        print("Page load timeout. Current URL:", driver.current_url)
        return False

# Click the "Next Page" button
def click_next_page(driver):
    try:
        # Wait for the "Next Page" button to be clickable
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//ul[contains(@class, 'a-pagination')]/li[contains(@class, 'a-last')]/a"))
        )
        driver.execute_script("arguments[0].click();", next_button)
        print("Clicked on the 'Next Page' button.")
        time.sleep(3)  # Wait for the next page to start loading
        return True
    except TimeoutException:
        print("No 'Next Page' button found. End of pages.")
        return False
    except Exception as e:
        print(f"Error clicking 'Next Page' button: {e}")
        return False

# Modified login_to_amazon function with CAPTCHA handling
def login_to_amazon(driver):
    print("Logging in to Amazon...")
    driver.get("https://www.amazon.in")
    time.sleep(2)

    # Check if CAPTCHA is shown
    if is_captcha_present(driver):
        wait_for_captcha_resolution(driver)

    try:
        # Load credentials from the JSON file
        USERNAME, PASSWORD = load_credentials()

        # Go to sign-in page
        driver.find_element(By.ID, "nav-link-accountList").click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ap_email")))

        # Enter credentials
        driver.find_element(By.ID, "ap_email").send_keys(USERNAME)
        driver.find_element(By.ID, "continue").click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ap_password")))

        driver.find_element(By.ID, "ap_password").send_keys(PASSWORD)
        driver.find_element(By.ID, "signInSubmit").click()
        
        # Check if CAPTCHA is shown
        if is_captcha_present(driver):
            wait_for_captcha_resolution(driver)

        # Check for login error
        if driver.find_elements(By.ID, "auth-error-message-box"):
            print("Login failed: Incorrect credentials.")
            driver.quit()
            exit(1)

        print("Login successful!\n")
    
    except Exception as e:
        print(f"Error during login: {e}")
        driver.quit()
        exit(1)


def get_element_text(item, xpath, default_value="Not Available"):
    """
    Helper function to safely extract text from a page element.
    Returns a default value if the element is not found or an error occurs.
    """
    try:
        return item.find_element(By.XPATH, xpath).text.strip()
    except (NoSuchElementException, StaleElementReferenceException):
        return default_value

def get_element_attribute(item, xpath, attribute, default_value="Not Available"):
    """
    Helper function to safely extract an attribute from a page element.
    Returns a default value if the element or attribute is not found or an error occurs.
    """
    try:
        return item.find_element(By.XPATH, xpath).get_attribute(attribute).strip()
    except (NoSuchElementException, StaleElementReferenceException):
        return default_value

def scrape_page(driver, category_name, max_items=10):
    products = []
    base_url = "https://www.amazon.in"  # Add Amazon's base URL

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'zg-grid-general-faceout')]"))
        )
    except TimeoutException:
        print("No product elements found on the page. Printing page source for debugging.")
        return products

    # Retrieve items once
    items = driver.find_elements(By.XPATH, "//div[contains(@class, 'zg-grid-general-faceout')]")
    num_items = min(len(items), max_items)  # Limit the number of items to scrape
    print(f"Found {num_items} items to scrape...")

    for index in range(num_items):
        retry_count = 0
        max_retries = 3  # Limit retries

        while retry_count < max_retries:
            try:
                # Re-fetch the updated items list and get the current item
                items = driver.find_elements(By.XPATH, "//div[contains(@class, 'zg-grid-general-faceout')]")
                item = items[index]  # Get the fresh element reference

                # Scrape the product details on the main page
                product_name = get_element_text(item, ".//div[@class='_cDEzb_p13n-sc-css-line-clamp-3_g3dy1']", "No name available")
                price = get_element_text(item, ".//span[@class='_cDEzb_p13n-sc-price_3mJ9Z']", "No price available")
                rating_text = get_element_attribute(item, ".//i[contains(@class, 'a-icon-star-small')]/span", "innerText", "No rating available")
                rating = rating_text.split(' ')[0] if rating_text != "No rating available" else rating_text
                reviews_count = get_element_text(item, ".//a[contains(@title, 'ratings')]/span", "No reviews available")
                image_url = get_element_attribute(item, ".//img[contains(@class, 'a-dynamic-image')]", "src", "No image available")

                # Get the relative product link
                relative_link = item.find_element(By.XPATH, ".//a[@class='a-link-normal aok-block']").get_attribute('href')
                product_link = base_url + relative_link if relative_link.startswith('/') else relative_link

                # Navigate to the product page
                driver.get(product_link)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'savingPriceOverride')]"))
                )

                # Scrape additional information from the product page
                discount = get_element_text(driver, ".//span[contains(@class, 'savingPriceOverride') and contains(@class, 'savingsPercentage')]", "No discount available")

                # Remove the '%' sign and ensure the value is positive
                discount_value_str = discount.replace('%', '').strip()
                if discount_value_str.startswith('-'):
                    discount_value_str = discount_value_str[1:]  # Remove the negative sign

                try:
                    discount_value = int(discount_value_str)
                except ValueError:
                    print(f"Invalid discount value for product {index + 1}, skipping.")
                    continue  # Skip this product if the discount value is invalid

                # Compare with the discount threshold
                if discount_value > DISCOUNT_THRESHOLD:
                    ship_from = get_element_text(driver, ".//div[@class='tabular-buybox-text' and contains(text(), 'Ships from')]/span", "Not Available")
                    sold_by = get_element_text(driver, ".//div[@class='tabular-buybox-text' and contains(text(), 'Sold by')]/span", "Not Available")
                    product_description = get_element_text(driver, ".//div[@id='feature-bullets']//span[contains(@class, 'a-list-item')]", "Not Available")
                    number_bought = get_element_text(driver, ".//span[contains(@id, 'social-proofing-faceout-title-tk_bought')]", "Not Available")

                    # Go back to the listing page
                    driver.back()

                    # Append the product details to the list
                    products.append({
                        "Product Name": product_name,
                        "Price": price,
                        "Rating": rating,
                        "Reviews Count": reviews_count,
                        "Image URL": image_url,
                        "Discount": discount,
                        "Ships From": ship_from,
                        "Sold By": sold_by,
                        "Product Description": product_description,
                        "Number Bought": number_bought,
                        "Category Name": category_name,
                    })
                    print(f"Scraped product {index + 1} successfully.")
                else:
                    print(f"Skipping product {index + 1} due to low discount: {discount_value}%")
                break  # Exit retry loop after success

            except StaleElementReferenceException:
                retry_count += 1
                print(f"StaleElementReferenceException caught for item {index + 1}, retrying ({retry_count}/{max_retries})...")
                if retry_count >= max_retries:
                    print(f"Skipping item {index + 1} due to repeated StaleElementReferenceException.")

            except IndexError:
                print(f"Index out of range for item {index + 1}. Likely due to dynamic DOM changes. Skipping...")
                break

            except Exception as e:
                print(f"Error scraping product {index + 1}: {e}")
                break  # Skip item on any unexpected error

    return products




# Scrape products for a category
def scrape_category(driver, category_url):
    print(f"Scraping category: {category_url}")
    driver.get(category_url)
    time.sleep(3)

    all_products = []
    current_page = 1

    # Extract category name from URL for reference
    category_name = category_url.split("/")[-2]

    while len(all_products) < MAX_PRODUCTS:
        print(f"Scraping page {current_page}...")

        if is_captcha_present(driver):
            wait_for_captcha_resolution(driver)

        try:
            # Scroll to the bottom of the page to load all elements
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Scrape data from the current page
            products = scrape_page(driver, category_name, max_items=10)
            all_products.extend(products)

            print(f"Found {len(products)} products on page {current_page}. Total so far: {len(all_products)}")

            # Stop if the required product count is reached
            if len(all_products) >= MAX_PRODUCTS:
                break

            # Attempt to navigate to the next page
            current_url = driver.current_url
            if not click_next_page(driver):
                break  # Exit the loop if there is no next page or navigation fails

            if not wait_for_page_to_load(driver, current_url):
                print("Page did not load successfully. Stopping.")
                break

            current_page += 1

        except Exception as e:
            print(f"Error while scraping page {current_page}: {e}")
            break

    print(f"Scraped {len(all_products)} products from category.\n")
    return all_products[:MAX_PRODUCTS]

# Function to get a unique filename by appending a number if the file already exists
def get_unique_filename(filename):
    # Check if the file already exists
    if not os.path.exists(filename):
        return filename

    # Split the file into the name and extension
    name, extension = os.path.splitext(filename)

    # Try creating a new filename with an incremented number
    counter = 1
    new_filename = f"{name}_{counter}{extension}"
    while os.path.exists(new_filename):
        counter += 1
        new_filename = f"{name}_{counter}{extension}"

    return new_filename

# Main scraping function
def main():
    driver = initialize_driver(headless=False)  # Set headless mode to True or False

    try:
        login_to_amazon(driver)
        all_data = []

        for category_url in CATEGORIES:
            data = scrape_category(driver, category_url)
            for product in data:
                product["Category"] = category_url.split("/")[-2]  # Extract category name
                all_data.append(product)

        # Save data to CSV with a unique filename
        filename = "amazon_best_sellers2.csv"
        unique_filename = get_unique_filename(filename)

        df = pd.DataFrame(all_data)
        df.to_csv(unique_filename, index=False)
        print(f"Data saved to {unique_filename}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
