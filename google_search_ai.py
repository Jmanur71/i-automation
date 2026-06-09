import os
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from urllib.parse import quote_plus

from config import (
    CHROME_GOOGLE_AI_MODE,
    CHROME_HEADLESS,
    CHROME_USER_DATA_DIR,
    GOOGLE_AI_CACHE_TTL_SECONDS,
    GOOGLE_AI_MIN_REQUEST_INTERVAL_SECONDS,
    GOOGLE_AI_PAGE_TIMEOUT_SECONDS,
    LOGGER,
)

try:
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
except Exception:
    webdriver = None
    TimeoutException = Exception
    WebDriverException = Exception
    Options = None
    By = None


@dataclass
class GoogleSearchResult:
    answer: str
    source: str
    mode: str


class GoogleSearchAIClient:
    def __init__(
        self,
        headless=CHROME_HEADLESS,
        user_data_dir=CHROME_USER_DATA_DIR,
        cache_ttl_seconds=GOOGLE_AI_CACHE_TTL_SECONDS,
        min_request_interval_seconds=GOOGLE_AI_MIN_REQUEST_INTERVAL_SECONDS,
        page_timeout_seconds=GOOGLE_AI_PAGE_TIMEOUT_SECONDS,
    ):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.cache_ttl_seconds = cache_ttl_seconds
        self.min_request_interval_seconds = min_request_interval_seconds
        self.page_timeout_seconds = page_timeout_seconds
        self._driver = None
        self._lock = threading.RLock()
        self._cache = OrderedDict()
        self._last_request_time = 0.0

    def query(self, question):
        if not question or webdriver is None or Options is None or By is None:
            return None

        normalized = self._normalize_question(question)
        cached = self._get_cached(normalized)
        if cached:
            LOGGER.debug("Google AI cache hit for query")
            return cached.answer

        with self._lock:
            cached = self._get_cached(normalized)
            if cached:
                LOGGER.debug("Google AI cache hit after lock")
                return cached.answer

            driver = self._ensure_driver()
            if driver is None:
                return None

            self._respect_rate_limit()
            try:
                result = self._fetch_ai_mode_answer(driver, question)
                if not result:
                    result = self._fetch_regular_search_answer(driver, question)
                if result:
                    self._store_cache(normalized, result)
                    return result.answer
            except Exception as exc:
                LOGGER.debug("Google Search AI query failed: %s", exc)

        return None

    def close(self):
        with self._lock:
            if self._driver is not None:
                try:
                    self._driver.quit()
                except Exception:
                    pass
                self._driver = None

    def _ensure_driver(self):
        if self._driver is not None:
            return self._driver

        if webdriver is None or Options is None:
            LOGGER.warning("Selenium is unavailable; Google Search AI Mode cannot start.")
            return None

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1600,1200")
        options.add_argument("--lang=en-US")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--remote-allow-origins=*")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        )

        binary_location = self._find_chrome_binary()
        if binary_location:
            options.binary_location = binary_location

        resolved_user_data_dir = self._resolve_user_data_dir()
        if resolved_user_data_dir:
            options.add_argument(f"--user-data-dir={resolved_user_data_dir}")

        driver = None
        start_errors = []
        try:
            driver = webdriver.Chrome(options=options)
        except Exception as exc:
            start_errors.append(exc)
            try:
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager

                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
            except Exception as fallback_exc:
                start_errors.append(fallback_exc)

        if driver is None:
            for err in start_errors:
                LOGGER.error("Failed to start Chrome for Google Search AI: %s", err)
            return None

        try:
            driver.set_page_load_timeout(self.page_timeout_seconds)
            try:
                driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {
                        "source": """
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            });
                        """
                    },
                )
            except Exception:
                pass
            self._driver = driver
            return driver
        except Exception as exc:
            LOGGER.error("Unexpected Chrome startup failure: %s", exc)
            try:
                driver.quit()
            except Exception:
                pass
            return None

    def _find_chrome_binary(self):
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return None

    def _resolve_user_data_dir(self):
        candidates = []
        if self.user_data_dir:
            candidates.append(self.user_data_dir)

        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates.append(os.path.join(local_app_data, "Google", "Chrome", "User Data"))
            candidates.append(os.path.join(local_app_data, "Microsoft", "Edge", "User Data"))

        for candidate in candidates:
            if candidate and os.path.isdir(candidate):
                return candidate
        return None

    def _respect_rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_request_interval_seconds:
            time.sleep(self.min_request_interval_seconds - elapsed)
        self._last_request_time = time.time()

    def _get_cached(self, normalized_question):
        entry = self._cache.get(normalized_question)
        if not entry:
            return None
        if (time.time() - entry["ts"]) > self.cache_ttl_seconds:
            self._cache.pop(normalized_question, None)
            return None
        return entry["value"]

    def _store_cache(self, normalized_question, result):
        self._cache[normalized_question] = {"ts": time.time(), "value": result}
        while len(self._cache) > 64:
            self._cache.popitem(last=False)

    def _normalize_question(self, question):
        return re.sub(r"\s+", " ", question or "").strip().lower()

    def _fetch_ai_mode_answer(self, driver, question):
        if not CHROME_GOOGLE_AI_MODE:
            return None

        url = "https://www.google.com/search?udm=50&aep=11&hl=en&gl=us&pws=0&q=" + quote_plus(question)
        return self._fetch_answer_from_url(driver, url, mode="ai_mode")

    def _fetch_regular_search_answer(self, driver, question):
        url = "https://www.google.com/search?hl=en&gl=us&pws=0&num=5&q=" + quote_plus(question)
        return self._fetch_answer_from_url(driver, url, mode="search")

    def _fetch_answer_from_url(self, driver, url, mode):
        try:
            driver.get(url)
        except TimeoutException:
            LOGGER.debug("Page load timed out for %s", url)
        except Exception as exc:
            LOGGER.debug("Browser navigation failed for %s: %s", url, exc)
            return None

        body_text = self._wait_for_body_text(driver)
        if not body_text:
            return None

        text_lower = body_text.lower()
        if "our systems have detected unusual traffic" in text_lower:
            LOGGER.warning("Google blocked the browser session with a verification page.")
            return None

        if "ai mode is not currently available on your device or account" in text_lower:
            LOGGER.info("Google AI Mode is unavailable for this session.")
            if mode == "ai_mode":
                return None

        if mode == "ai_mode":
            answer = self._extract_ai_mode_overview(body_text)
            if answer:
                return GoogleSearchResult(answer=answer, source=url, mode=mode)

        answer = self._extract_search_summary(body_text)
        if answer:
            return GoogleSearchResult(answer=answer, source=url, mode=mode)

        return None

    def _wait_for_body_text(self, driver):
        deadline = time.time() + self.page_timeout_seconds
        last_text = ""
        while time.time() < deadline:
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                text = body.text.strip()
                if text and text != last_text:
                    last_text = text
                    if self._looks_ready(text):
                        return text
                time.sleep(0.5)
            except Exception:
                time.sleep(0.5)
        return last_text.strip()

    def _looks_ready(self, text):
        markers = [
            "ai overview",
            "ai mode",
            "search results",
            "our systems have detected unusual traffic",
            "ai mode is not currently available",
        ]
        lowered = text.lower()
        return any(marker in lowered for marker in markers) or len(text) > 400

    def _extract_ai_mode_overview(self, body_text):
        lines = self._visible_lines(body_text)
        candidates = self._collect_section(lines, ("ai overview", "ai mode"))
        if not candidates:
            return ""
        return self._clean_answer(candidates)

    def _extract_search_summary(self, body_text):
        lines = self._visible_lines(body_text)
        candidates = self._collect_section(lines, ("search results",))
        if not candidates:
            candidates = self._fallback_search_lines(lines)
        return self._clean_answer(candidates)

    def _visible_lines(self, text):
        cleaned = []
        for raw_line in text.splitlines():
            line = re.sub(r"\s+", " ", raw_line).strip()
            if line:
                cleaned.append(line)
        return cleaned

    def _collect_section(self, lines, start_markers):
        stop_markers = (
            "sources",
            "related questions",
            "people also ask",
            "learn more",
            "footer links",
            "sign in",
            "images",
            "videos",
            "news",
            "more",
            "all",
            "search results",
        )

        candidate = []
        collecting = False
        for line in lines:
            lowered = line.lower()
            if any(marker in lowered for marker in start_markers):
                collecting = True
                continue
            if not collecting:
                continue
            if any(stop in lowered for stop in stop_markers) and candidate:
                break
            if len(line) < 3:
                continue
            if line in {"AI Overview", "AI Mode"}:
                continue
            candidate.append(line)
            if len(" ".join(candidate)) >= 700 or len(candidate) >= 6:
                break
        return "\n".join(candidate).strip()

    def _fallback_search_lines(self, lines):
        candidate = []
        for line in lines:
            lowered = line.lower()
            if lowered.startswith("footer"):
                break
            if lowered in {"all", "images", "videos", "news", "more", "search results", "sign in"}:
                continue
            if len(line) < 20:
                continue
            if any(domain in lowered for domain in ("http://", "https://")):
                continue
            candidate.append(line)
            if len(candidate) >= 4:
                break
        return "\n".join(candidate).strip()

    def _clean_answer(self, text):
        if not text:
            return ""

        lines = []
        seen = set()
        for raw_line in text.splitlines():
            line = re.sub(r"\s+", " ", raw_line).strip(" -•\t")
            if not line:
                continue
            lower = line.lower()
            if lower in seen:
                continue
            seen.add(lower)
            if lower in {"learn more", "sources"}:
                continue
            lines.append(line)

        cleaned = "\n".join(lines).strip()
        return cleaned
