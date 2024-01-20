import hashlib
import json
import os
import time
from urllib.parse import quote

from loguru import logger
from pypinyin import Style, pinyin
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config


def get_driver():
    """Creates and configures a web browser driver.

    Returns:
        webdriver.Firefox: An instance of the Firefox web browser driver.

    Raises:
        WebDriverException: If an error occurs while creating the web browser driver.
    """
    logger.info("Opening the web browser driver...")

    # Create Firefox options
    firefox_options = webdriver.FirefoxOptions()

    # Disable image and CSS loading for faster crawling
    firefox_options.set_preference('permissions.default.image', 2)
    firefox_options.set_preference(
        'dom.ipc.plugins.enabled.libflashplayer.so', 'false')
    firefox_options.set_preference('permissions.default.stylesheet', 2)

    # Set the path to geckodriver (modify based on your actual situation)
    geckodriver_path = Service("./drivers/geckodriver.exe")

    try:
        # Create the Firefox web browser driver with the specified options
        driver = webdriver.Firefox(
            service=geckodriver_path, options=firefox_options)
        logger.info("Web browser driver successfully created.")
        return driver

    except Exception as e:
        logger.error(f"Failed to create the web browser driver: {str(e)}")
        raise


def perform_login(driver, username, password):
    """Perform login using the provided driver, username, and password.

    Args:
        driver: WebDriver instance for browser automation.
        username (str): The username to log in.
        password (str): The password associated with the username.
    """
    # Locate the username field and enter the username
    username_field = driver.find_element(By.XPATH, '//*[@id="loginname"]')
    username_field.send_keys(username)

    # Locate the password field and enter the password
    password_field = driver.find_element(By.XPATH, '//*[@id="nloginpwd"]')
    password_field.send_keys(password)

    # Click the login button
    login_button = driver.find_element(By.XPATH, '//*[@id="loginsubmit"]')
    login_button.click()
    logger.info("Login successful.")


def scroll_to_half(driver):
    """Scroll to the middle of the page.

    Args:
        driver: WebDriver instance for browser automation.
    """
    # Get the total height of the current window
    js = 'return action=document.body.scrollHeight'
    # Total height of the current window
    total_height = driver.execute_script(js)

    # Scroll to the middle of the page
    half_height = total_height - total_height // 4
    driver.execute_script("window.scrollTo(0, {})".format(half_height))
    logger.info("Scrolled to the middle of the page.")
    time.sleep(0.01)


def get_pinyin_initials(input_chinese):
    """Converts a Chinese string to its lowercase pinyin initials.

    Args:
        input_chinese (str): The input Chinese string.

    Returns:
        str: A string containing the lowercase pinyin initials for each character in the input.
    """
    # Get lowercase pinyin initials
    pinyin_list = pinyin(input_chinese, style=Style.FIRST_LETTER)

    # Concatenate the pinyin initials into a string
    initials = ''.join([char[0].lower() if char[0].isalpha()
                       else char[0] for char in pinyin_list])

    return initials


def save_product_ids(product_list, save_dir, filename):
    """
    Save the product_list as a JSON file.

    Args:
        product_list (list): A list of dictionaries containing product information.
        save_dir (str): The directory path where the file should be saved.
        filename (str): The name of the JSON file.

    Returns:
        str: The full path to the saved JSON file.
    """
    try:
        # Ensure that the directory exists, create if not
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # Construct the full path for the JSON file
        json_file_path = os.path.join(save_dir, filename + ".json")

        # Save the product_list as JSON
        with open(json_file_path, 'w', encoding="utf8") as json_file:
            json.dump(product_list, json_file, indent=4, ensure_ascii=False)

        logger.info(f"Product list saved successfully.")
        return json_file_path

    except Exception as e:
        logger.error(f"Error saving product list: {e}")
        return None


def jd_search_spider(keywords, username, password, save_dir):
    """Perform web scraping on the JD website for the specified keywords.

    Args:
        keywords (list): A list of keywords to search for.
        username (str): The username to log in.
        password (str): The password associated with the username.
        save_dir (str): The directory path where the file should be saved.
    """
    driver = None

    try:
        # Assuming get_driver() is defined and returns a webdriver instance
        driver = get_driver()

        # Open the JD homepage in the first tab and perform login
        url = "https://passport.jd.com/new/login.aspx"
        driver.get(url)
        perform_login(driver, username, password)

        # Wait to ensure that the login is successful
        time.sleep(10)

        for keyword in keywords:
            # Open a new tab for each keyword
            driver.execute_script("window.open('', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])

            search_url = "https://search.jd.com/Search?keyword={}".format(
                quote(keyword))

            # Open the specified URL in the new tab
            driver.get(search_url)

            # Wait for the page to load using WebDriverWait
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.gl-item")))

            # Scroll to the bottom of the page
            scroll_to_half(driver)

            # Find all product elements on the page
            products = driver.find_elements(By.CSS_SELECTOR, "li.gl-item")

            # Extract information from each product
            product_list = []
            for product in products:
                sku_value = product.get_attribute("data-sku")
                desc = product.find_element(
                    By.CSS_SELECTOR, "div.p-name em").text
                product_info = {"sku": sku_value, "description": desc}
                product_list.append(product_info)

            logger.info(
                f"Web scraping for keyword '{keyword}' completed successfully.")

            # Save the product list for the current keyword in a separate file
            keyword_filename = get_pinyin_initials(
                f"{keyword.replace(' ', '_')}")
            save_product_ids({keyword: product_list},
                             save_dir, keyword_filename)

    except WebDriverException as e:
        # Handle WebDriverException
        logger.error(f"WebDriverException: {e}")

    finally:
        # Make sure to quit the driver even if an exception occurs
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Perform web scraping on the JD website for the specified keywords
    jd_search_spider(keywords=config.KEYWORDS_TO_SEARCH, username=config.USERNAME,
                     password=config.PASSWORD, save_dir=config.PRODUCT_ID_DIR)
