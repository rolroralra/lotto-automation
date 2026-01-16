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

    # Core headless settings - use classic headless mode for Lambda stability
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    # Anti-detection: Real browser User-Agent
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

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


def buy_lotto_ticket(username: str, password: str, ticket_count: int = 5) -> dict:
    """
    Buy lotto tickets

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

        # Navigate to lotto purchase page
        driver.get('https://el.dhlottery.co.kr/game/TotalGame.jsp?LottoId=LO40')
        time.sleep(5)

        # Switch to iframe
        iframe = driver.find_element(By.XPATH, '//*[@id="ifrm_tab"]')
        driver.switch_to.frame(iframe)
        time.sleep(1)

        # Click lotto ticket button (auto number)
        driver.find_element(By.XPATH, '/html/body/header[1]/div/div/nav/div/ul/li[1]/div/ul/li[1]/div/button').click()
        time.sleep(1)

        # Select ticket count
        select_element = driver.find_element(By.XPATH, '//*[@id="amoundApply"]')
        select = Select(select_element)
        select.select_by_index(ticket_count - 1)

        # Confirm purchase
        driver.find_element(By.XPATH, '//*[@id="btnSelectNum"]').click()
        driver.find_element(By.XPATH, '//*[@id="btnBuy"]').click()
        driver.find_element(By.XPATH, '//*[@id="popupLayerConfirm"]/div/div[2]/input[1]').click()
        time.sleep(5)

        message = f"{username}: Successfully purchased {ticket_count} lotto tickets"
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

        element = driver.find_element(By.XPATH, '//*[@id="totalAmt"]')
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
