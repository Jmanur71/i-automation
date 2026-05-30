import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config import CHROME_HEADLESS, CHROME_USER_DATA_DIR, CHROME_AI_TARGET, CHROME_GOOGLE_AI_MODE, LOGGER

# Ensure logs directory
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'chrome_client.log')

# Add file handler for Chrome-specific logging
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logging.getLogger('VoiceAssistant').addHandler(file_handler)


class ChromeClient:
    def __init__(self, headless=None):
        options = Options()

        # headless: if None, read default from config; otherwise override
        if headless is None:
            headless = bool(CHROME_HEADLESS)
        self._used_headless = headless
        if headless:
            options.add_argument('--headless=new')

        # If a user data dir is provided, persist profile to enable signed-in AI flows
        if CHROME_USER_DATA_DIR:
            options.add_argument(f'--user-data-dir={CHROME_USER_DATA_DIR}')

        options.add_argument('--start-maximized')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--disable-blink-features=AutomationControlled')

        service = Service(ChromeDriverManager().install())
        try:
            LOGGER.info('Launching Chrome (headless=%s)', self._used_headless)
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            # If headless mode fails on this environment, retry without headless
            LOGGER.exception('Initial Chrome launch failed')
            if self._used_headless:
                try:
                    LOGGER.info('Attempting fallback to non-headless Chrome')
                    options = Options()
                    if CHROME_USER_DATA_DIR:
                        options.add_argument(f'--user-data-dir={CHROME_USER_DATA_DIR}')
                    options.add_argument('--start-maximized')
                    options.add_experimental_option('excludeSwitches', ['enable-logging'])
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    self.driver = webdriver.Chrome(service=service, options=options)
                    self._used_headless = False
                    LOGGER.warning('Fell back to non-headless Chrome')
                except Exception:
                    LOGGER.exception('Fallback launch also failed')
                    raise
            else:
                raise

        self.wait = WebDriverWait(self.driver, 12)
        self._retried_fallback = False

    def _activate_google_ai_mode(self):
        selectors = [
            "//a[normalize-space()='AI Mode']",
            "//button[normalize-space()='AI Mode']",
            "//div[normalize-space()='AI Mode']",
            "//*[contains(@aria-label, 'AI Mode') or contains(@aria-label, 'AI mode') or contains(@aria-label, 'AI-mode')]"
        ]
        for selector in selectors:
            try:
                el = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                LOGGER.info('AI Mode selector found: %s', selector)
                el.click()
                # Wait for the AI content region to appear.
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="main"], div[data-attrid="wa:/description"], div.VwiC3b')))
                LOGGER.info('Switched to Google AI Mode')
                return True
            except Exception as exc:
                LOGGER.debug('AI Mode selector not found for %s: %s', selector, exc)
                continue
        LOGGER.info('Google AI Mode selector not found, staying on standard results')
        return False

    def query(self, text, callback):
        try:
            # Determine target URL based on AI target
            if CHROME_AI_TARGET == 'bard':
                target_url = 'https://bard.google.com/'
            else:
                target_url = 'https://www.google.com'

            LOGGER.info('Navigating to %s', target_url)
            self.driver.get(target_url)

            # Locate input depending on target
            search_box = None
            # Special check for Bard: it generally requires a signed-in session.
            if CHROME_AI_TARGET == 'bard':
                try:
                    # quick presence check for an editable area
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea, [contenteditable="true"]')))
                except Exception:
                    msg = 'AI target appears to require sign-in (e.g. Bard). Please sign into the configured Chrome profile.'
                    LOGGER.warning(msg)
                    try:
                        callback(msg)
                    except Exception:
                        pass
                    return msg
            if CHROME_AI_TARGET == 'google':
                search_box = self.wait.until(EC.presence_of_element_located((By.NAME, 'q')))
                search_box.clear()
                search_box.send_keys(text)
                search_box.send_keys(Keys.RETURN)
                # Wait for Google search results
                self.wait.until(EC.presence_of_element_located((By.ID, 'search')))
                if CHROME_GOOGLE_AI_MODE:
                    self._activate_google_ai_mode()
            else:
                # Generic attempt for AI interfaces (may require signed-in session)
                try:
                    search_box = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea, [contenteditable="true"]'))
                    )
                    search_box.clear()
                    search_box.send_keys(text)
                    search_box.send_keys(Keys.RETURN)
                except Exception:
                    LOGGER.warning('Could not find AI input element on target; proceeding to scrape page')

            # Try to extract a featured snippet or the first result text
            snippet = ''
            selectors = [
                'div[data-attrid="wa:/description"]',
                'div.ifM9O',
                'div.VwiC3b'
            ]
            for sel in selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    snippet = elem.text.strip()
                    if snippet:
                        break
                except Exception:
                    continue

            if not snippet:
                try:
                    first_result = self.driver.find_element(By.CSS_SELECTOR, 'div#search .g')
                    snippet = first_result.text.strip()
                except Exception:
                    snippet = 'No clear answer found. Check Chrome window for results.'

            callback(snippet)
            return snippet

        except Exception as e:
            LOGGER.exception('Query failed, evaluating fallback')
            # If headless mode failed at runtime, try once with non-headless driver
            if getattr(self, '_used_headless', False) and not getattr(self, '_retried_fallback', False):
                self._retried_fallback = True
                try:
                    try:
                        self.driver.quit()
                    except Exception:
                        pass

                    service = Service(ChromeDriverManager().install())
                    options = Options()
                    if CHROME_USER_DATA_DIR:
                        options.add_argument(f'--user-data-dir={CHROME_USER_DATA_DIR}')
                    options.add_argument('--start-maximized')
                    options.add_experimental_option('excludeSwitches', ['enable-logging'])
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    logging.info('Retrying with non-headless Chrome')
                    self.driver = webdriver.Chrome(service=service, options=options)
                    self.wait = WebDriverWait(self.driver, 12)
                    return self.query(text, callback)
                except Exception as retry_e:
                    LOGGER.exception('Fallback retry failed')
                    error_msg = f'Search error after fallback: {retry_e}'
                    try:
                        callback(error_msg)
                    except Exception:
                        pass
                    return error_msg
            else:
                error_msg = f'Search error: {e}'
                try:
                    callback(error_msg)
                except Exception:
                    pass
                return error_msg

    def reset(self):
        try:
            self.driver.delete_all_cookies()
        except Exception:
            pass

    def close(self):
        """Properly close Chrome WebDriver."""
        try:
            if hasattr(self, 'driver') and self.driver:
                LOGGER.info('Closing Chrome WebDriver')
                self.driver.quit()
        except Exception as e:
            LOGGER.warning(f'Error closing WebDriver: {e}')
