# Amazon Best Sellers Scraper

This project is a Python-based web scraper designed to extract details about best-selling products from Amazon's "Best Sellers" pages. The extracted data includes product information such as name, price, discount, reviews, and ratings, and is saved to a CSV file. The script is capable of navigating multiple pages, handling CAPTCHAs, and filtering products based on discount thresholds.

---

## Features

- Scrapes Amazon Best Sellers categories.
- Extracts product details including:
  - Name
  - Price
  - Rating
  - Number of Reviews
  - Discount Percentage
  - Ships From
  - Sold By
  - Product Description
- Filters products based on discount percentage.
- Saves data to a CSV file with unique filenames to avoid overwriting.
- Handles Amazon CAPTCHAs and dynamic page loading.

---

## Installation

### Prerequisites

1. **Python 3.7+**
2. Required Python libraries:
   - `selenium`
   - `webdriver_manager`
   - `pandas`
   - `json`
   - `csv`
3. Chrome browser installed on your system.

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/Gedamu-tinsae/Amazon-Web-Scraper-with-Selenium.git
   cd Amazon-Web-Scraper-with-Selenium
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `credentials.json` file in the root directory with your Amazon account credentials:
   ```json
   {
       "username": "your_email",
       "password": "your_password"
   }
   ```

4. Add the categories you wish to scrape in the `CATEGORIES` list within the script.

---

## Usage

1. **Run the script:**
   ```bash
   python scraper.py
   ```

2. The script will:
   - Log in to Amazon using the credentials provided in `credentials.json`.
   - Scrape products from the specified categories.
   - Filter products based on the `DISCOUNT_THRESHOLD` variable.
   - Save the data to a uniquely named CSV file.

### Example CSV Output

| Product Name       | Price  | Rating | Reviews Count | Discount | Ships From | Sold By | Product Description | Number Bought | Category       |
|--------------------|--------|--------|---------------|----------|------------|---------|----------------------|---------------|----------------|
| Example Product 1 | ₹500.00| 4.5    | 150           | 60%      | Amazon     | Seller1 | Detailed description| 200           | kitchen        |

---

## Configuration

### Variables

- **`CATEGORIES`**: List of category URLs to scrape.
- **`MAX_PRODUCTS`**: Maximum number of products to scrape per category.
- **`DISCOUNT_THRESHOLD`**: Minimum discount percentage (as an integer) for products to be included in the CSV file.

### Driver Settings

- The WebDriver is configured to run in headless mode by default. To view browser actions, set `headless=False` when initializing the driver in `initialize_driver()`.

---

## Troubleshooting

1. **CAPTCHA Issues**:
   - If a CAPTCHA appears, you will need to solve it manually. The script will wait for a maximum of 5 minutes.

2. **No Products Scraped**:
   - Ensure the `CATEGORIES` URLs are correct.
   - Verify your Amazon account credentials in `credentials.json`.

3. **File Overwriting**:
   - The script automatically generates unique filenames to prevent overwriting existing CSV files.

---

## Future Enhancements

- Add support for more e-commerce platforms.
- Enhance CAPTCHA resolution with automated solvers.
- Include additional product details like delivery time and availability.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests for any bugs or improvements.

---

### Demo

Watch a demonstration of this project in action: [YouTube Demo](https://youtu.be/sjhPAXc7zbc)
