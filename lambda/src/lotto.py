"""
Lotto Automation for AWS Lambda
Selenium-based automation for dhlottery.co.kr
"""
import os
import time
import shutil
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)


def cleanup_chrome_tmp():
    """Clean up Chrome temporary directories in /tmp"""
    dirs_to_clean = [
        '/tmp/chrome-user-data',
        '/tmp/chrome-data',
        '/tmp/chrome-cache',
    ]
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                logger.info(f"Cleaned up {dir_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {dir_path}: {e}")

# Chrome/ChromeDriver paths (Docker container or Lambda Layer)
CHROME_PATHS = [
    '/opt/chrome/chrome',          # Chrome for Testing
    '/usr/bin/google-chrome',      # Docker container symlink
    '/usr/bin/google-chrome-stable',
    '/opt/bin/chromium',
    '/opt/headless-chromium',
]

CHROMEDRIVER_PATHS = [
    '/opt/chromedriver',           # Docker container & Lambda Layer
    '/opt/bin/chromedriver',
    '/usr/local/bin/chromedriver',
]


def find_executable(paths):
    """Find first existing executable from list of paths"""
    for path in paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def get_chrome_driver():
    """
    Create Chrome WebDriver configured for Lambda environment
    """
    # Clean up previous Chrome data
    cleanup_chrome_tmp()

    options = Options()

    # Core headless settings - use new headless mode for better compatibility
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    # Anti-detection: Real browser User-Agent (matching Docker Chrome version 119)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.105 Safari/537.36')

    # Lambda-specific memory and resource constraints
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--single-process')

    # Use /tmp for all Chrome data (Lambda only has /tmp writable)
    options.add_argument('--user-data-dir=/tmp/chrome-user-data')
    options.add_argument('--disk-cache-dir=/tmp/chrome-cache')
    options.add_argument('--crash-dumps-dir=/tmp/chrome-crashes')
    options.add_argument('--homedir=/tmp')

    # Stability options for Lambda
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    options.add_argument('--no-first-run')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--mute-audio')

    # Anti-detection: Disable automation flags
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    # Find Chrome binary
    chrome_path = find_executable(CHROME_PATHS)
    if chrome_path:
        logger.info(f"Found Chrome at: {chrome_path}")
        options.binary_location = chrome_path
    else:
        logger.warning("Chrome binary not found in expected paths")
        # List /opt contents for debugging
        if os.path.exists('/opt'):
            for item in os.listdir('/opt'):
                logger.info(f"/opt/{item}")

    # Find ChromeDriver
    chromedriver_path = find_executable(CHROMEDRIVER_PATHS)
    if chromedriver_path:
        logger.info(f"Found ChromeDriver at: {chromedriver_path}")
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        logger.warning("ChromeDriver not found, trying auto-detection")
        # Let Selenium try to find/download driver automatically
        driver = webdriver.Chrome(options=options)

    # Anti-detection: Override navigator.webdriver
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en']
            });
        '''
    })

    return driver


def login_lotto(driver, username: str, password: str):
    """Login to dhlottery.co.kr"""
    logger.info(f"Logging in as {username}")

    driver.get('https://www.dhlottery.co.kr/login')
    logger.info(f"Current URL: {driver.current_url}")

    # Wait for login form to be present
    wait = WebDriverWait(driver, 20)

    try:
        user_id_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="inpUserId"]')))
        logger.info("Found userId field")
        user_id_field.send_keys(username)

        password_field = driver.find_element(By.XPATH, '//*[@id="inpUserPswdEncn"]')
        password_field.send_keys(password)

        login_btn = driver.find_element(By.XPATH, '//*[@id="btnLogin"]')
        login_btn.click()

        # Wait for login to complete
        time.sleep(5)
        logger.info(f"Login completed. Current URL: {driver.current_url}")

    except Exception as e:
        logger.error(f"Login failed. Page source length: {len(driver.page_source)}")
        logger.error(f"Current URL: {driver.current_url}")
        logger.error(f"Page title: {driver.title}")
        raise e


def wait_for_element(driver, by, value, timeout=10):
    """Wait for an element to be present and return it"""
    wait = WebDriverWait(driver, timeout)
    element = wait.until(EC.presence_of_element_located((by, value)))
    return element


def close_popup_if_exists(driver, username):
    """Check for popup alert and close it, return popup text if found"""
    try:
        popup_alert = driver.find_element(By.ID, 'popupLayerAlert')
        if popup_alert.is_displayed():
            popup_text = popup_alert.text
            logger.warning(f"{username}: Popup alert detected: {popup_text}")

            # Find and click the close button
            try:
                close_btn = popup_alert.find_element(By.CSS_SELECTOR, 'input[type="button"], button')
                close_btn.click()
                logger.info(f"{username}: Closed popup via button click")
            except Exception:
                driver.execute_script("arguments[0].style.display = 'none';", popup_alert)
                logger.info(f"{username}: Closed popup via JavaScript")

            time.sleep(1)
            return popup_text
    except Exception:
        pass
    return None


def buy_lotto_ticket(username: str, password: str, ticket_count: int = 5) -> dict:
    """
    Buy lotto tickets (simplified version matching local working code)

    Args:
        username: dhlottery.co.kr username
        password: dhlottery.co.kr password
        ticket_count: Number of tickets to buy (1-5)

    Returns:
        dict with status and message
    """
    driver = None

    try:
        driver = get_chrome_driver()
        login_lotto(driver, username, password)

        # Navigate directly to lotto purchase page (same as working local code)
        logger.info(f"{username}: Navigating to lotto purchase page...")
        driver.get('https://ol.dhlottery.co.kr/olotto/game/game645.do')
        time.sleep(5)
        logger.info(f"{username}: Page loaded. URL: {driver.current_url}, Title: {driver.title}")

        # Check and close any initial popup
        popup_text = close_popup_if_exists(driver, username)
        if popup_text and ('로그인' in popup_text or '세션' in popup_text):
            raise Exception(f"Login required: {popup_text}")

        # Click auto number tab (same xpath as working code)
        logger.info(f"{username}: Clicking auto number tab...")
        auto_tab = wait_for_element(driver, By.XPATH, '//*[@id="tabWay2Buy"]/li[2]')
        auto_tab.click()
        logger.info(f"{username}: Clicked auto number tab")
        time.sleep(1)

        # Close popup if appears after clicking tab
        close_popup_if_exists(driver, username)

        # Select ticket count
        logger.info(f"{username}: Selecting {ticket_count} tickets...")
        select_element = wait_for_element(driver, By.XPATH, '//*[@id="amoundApply"]')
        select = Select(select_element)
        select.select_by_index(ticket_count - 1)
        logger.info(f"{username}: Selected {ticket_count} tickets")

        # Click select numbers button
        logger.info(f"{username}: Clicking select numbers button...")
        wait_for_element(driver, By.XPATH, '//*[@id="btnSelectNum"]').click()
        logger.info(f"{username}: Clicked select numbers button")
        time.sleep(1)

        # Close popup if appears
        close_popup_if_exists(driver, username)

        # Click buy button
        logger.info(f"{username}: Clicking buy button...")
        wait_for_element(driver, By.XPATH, '//*[@id="btnBuy"]').click()
        logger.info(f"{username}: Clicked buy button")
        time.sleep(1)

        # Close popup if appears
        close_popup_if_exists(driver, username)

        # Click confirm button in confirmation popup
        logger.info(f"{username}: Clicking confirm button...")
        wait_for_element(driver, By.XPATH, '//*[@id="popupLayerConfirm"]/div/div[2]/input[1]').click()
        logger.info(f"{username}: Clicked confirm button")
        time.sleep(5)

        # Check for purchase result
        page_source = driver.page_source
        if '구매완료' in page_source or '복권이 구매' in page_source or '구매가 완료' in page_source:
            message = f"{username}: Successfully purchased {ticket_count} lotto tickets"
            logger.info(message)
            return {
                'status': 'success',
                'message': message,
                'username': username,
                'ticket_count': ticket_count
            }
        elif '잔액이 부족' in page_source or '잔고가 부족' in page_source:
            message = f"{username}: Insufficient balance"
            logger.error(message)
            return {
                'status': 'error',
                'message': message,
                'username': username,
                'error': 'Insufficient balance'
            }
        else:
            # Log for debugging
            logger.info(f"{username}: Page source snippet: {page_source[:500]}")
            message = f"{username}: Purchase completed (unverified)"
            logger.info(message)
            return {
                'status': 'success',
                'message': message,
                'username': username,
                'ticket_count': ticket_count
            }

    except Exception as e:
        message = f"{username}: Failed to purchase lotto tickets - {str(e)}"
        logger.error(message)

        if driver:
            try:
                logger.error(f"{username}: Debug - Current URL: {driver.current_url}")
                logger.error(f"{username}: Debug - Page title: {driver.title}")
            except Exception:
                pass

        return {
            'status': 'error',
            'message': message,
            'username': username,
            'error': str(e)
        }

    finally:
        if driver:
            driver.quit()


def check_lotto_balance(username: str, password: str) -> dict:
    """Check account balance"""
    driver = None

    try:
        driver = get_chrome_driver()
        login_lotto(driver, username, password)

        driver.get('https://www.dhlottery.co.kr/mypage/home')
        time.sleep(5)

        element = driver.find_element(By.XPATH, '//*[@id="divCrntEntrsAmt"]')
        balance_text = element.text.strip()
        balance = int(balance_text.replace("원", "").replace(",", ""))

        message = f"{username}: Current balance is {balance_text}"
        logger.info(message)

        return {
            'status': 'success',
            'message': message,
            'username': username,
            'balance': balance,
            'balance_text': balance_text
        }

    except Exception as e:
        message = f"{username}: Failed to check balance - {str(e)}"
        logger.error(message)

        return {
            'status': 'error',
            'message': message,
            'username': username,
            'error': str(e)
        }

    finally:
        if driver:
            driver.quit()


def check_lotto_result(username: str, password: str) -> dict:
    """Check lotto results"""
    driver = None

    try:
        driver = get_chrome_driver()
        login_lotto(driver, username, password)

        driver.get('https://www.dhlottery.co.kr/mypage/mylotteryledger')
        time.sleep(5)

        # Try to click toggle button if exists
        try:
            toggle_btn = driver.find_element(By.XPATH, '//*[@id="srchBtnToggle"]/span[2]')
            driver.execute_script("arguments[0].click();", toggle_btn)
            time.sleep(3)
        except Exception:
            pass

        # Click 3 months button using JavaScript to avoid click intercept
        months_btn = driver.find_element(By.XPATH, '//*[@id="containerBox"]/div[2]/div/div/div/form/div[1]/div/div[2]/div/div[2]/div[2]/button[3]')
        driver.execute_script("arguments[0].scrollIntoView(true);", months_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", months_btn)

        # Click search button
        search_btn = driver.find_element(By.XPATH, '//*[@id="btnSrch"]')
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(5)

        result_elements = driver.find_elements(By.XPATH, '//*[@id="winning-history-list"]/ul[2]/li/div[6]/span[2]')
        results = [elem.text.strip() for elem in result_elements]

        has_winning = any("당첨" in result for result in results)

        if has_winning:
            message = f"{username}: Found winning ticket!"
        else:
            message = f"{username}: No winning tickets"

        logger.info(message)

        return {
            'status': 'success',
            'message': message,
            'username': username,
            'has_winning': has_winning,
            'results': results
        }

    except Exception as e:
        message = f"{username}: Failed to check results - {str(e)}"
        logger.error(message)

        return {
            'status': 'error',
            'message': message,
            'username': username,
            'error': str(e)
        }

    finally:
        if driver:
            driver.quit()
