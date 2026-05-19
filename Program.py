import json
import os
import re
import sys
import time
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import (
    InvalidCookieDomainException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

LOG_FILE = Path(__file__).with_name("tiktok_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

BASE_URL = "https://www.tiktok.com/messages"
MESSAGES_URL = "https://www.tiktok.com/messages"
COOKIE_FILE = Path(__file__).with_name("cookie.txt")

TARGET_CHAT_NAME = os.getenv("TIKTOK_TARGET_CHAT_NAME", "Pm")
MESSAGE_TEXT = os.getenv("TIKTOK_MESSAGE_TEXT", "ทดสอบระบบเติมไฟอัตโนมัติ")
WAIT_SECONDS = int(os.getenv("TIKTOK_WAIT_SECONDS", "10"))


def load_cookie_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Cookie file not found: {path}")

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("cookie.txt is empty. Paste cookies first, for example: sessionid=...; sid_tt=...")

    return text


def normalize_cookie(cookie: dict) -> dict:
    name = cookie.get("name")
    value = cookie.get("value")
    if not name or value is None:
        raise ValueError(f"Invalid cookie: {cookie}")

    normalized = {
        "name": str(name),
        "value": str(value),
        "domain": cookie.get("domain") or ".tiktok.com",
        "path": cookie.get("path") or "/",
    }

    if "expirationDate" in cookie:
        normalized["expiry"] = int(cookie["expirationDate"])
    elif "expiry" in cookie:
        normalized["expiry"] = int(cookie["expiry"])
    elif "expires" in cookie and isinstance(cookie["expires"], (int, float)):
        normalized["expiry"] = int(cookie["expires"])

    if "secure" in cookie:
        normalized["secure"] = bool(cookie["secure"])

    if "httpOnly" in cookie:
        normalized["httpOnly"] = bool(cookie["httpOnly"])

    same_site = cookie.get("sameSite") or cookie.get("same_site")
    if same_site:
        same_site = str(same_site).capitalize()
        if same_site in {"Strict", "Lax", "None"}:
            normalized["sameSite"] = same_site

    return normalized


def parse_json_cookies(text: str) -> list[dict]:
    data = json.loads(text)

    if isinstance(data, dict):
        if isinstance(data.get("cookies"), list):
            data = data["cookies"]
        else:
            data = [data]

    if not isinstance(data, list):
        raise ValueError("JSON cookies must be a list, or an object with a cookies key")

    return [normalize_cookie(cookie) for cookie in data]


def parse_expiry(value: str) -> int | None:
    value = value.strip()
    if not value or value.lower() == "session":
        return None

    if value.isdigit():
        return int(value)

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return int(parsed.astimezone(timezone.utc).timestamp())
    except ValueError:
        return None


def is_checked(value: str) -> bool:
    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "\u2713",
        "\u00e2\u0153\u201c",
    }


def parse_browser_table_cookies(text: str) -> list[dict]:
    cookies = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split("\t") if "\t" in line else re.split(r"\s{2,}", line)
        if len(parts) < 5:
            raise ValueError("Not a browser table cookie format")

        name, value, domain, path, expires = parts[:5]
        cookie = {
            "name": name,
            "value": value,
            "domain": domain or ".tiktok.com",
            "path": path or "/",
        }

        expiry = parse_expiry(expires)
        if expiry:
            cookie["expiry"] = expiry

        if len(parts) > 6 and is_checked(parts[6]):
            cookie["httpOnly"] = True

        if len(parts) > 7 and is_checked(parts[7]):
            cookie["secure"] = True

        if len(parts) > 8 and parts[8].strip() in {"Strict", "Lax", "None"}:
            cookie["sameSite"] = parts[8].strip()

        cookies.append(normalize_cookie(cookie))

    if not cookies:
        raise ValueError("No browser table cookies found")

    return cookies


def parse_netscape_cookies(text: str) -> list[dict]:
    cookies = []

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split("\t")
        if len(parts) != 7:
            raise ValueError("Not a Netscape cookie format")

        domain, _flag, path, secure, expires, name, value = parts
        cookie = {
            "domain": domain,
            "path": path or "/",
            "secure": secure.upper() == "TRUE",
            "name": name,
            "value": value,
        }

        if expires and expires != "0":
            cookie["expiry"] = int(expires)

        cookies.append(normalize_cookie(cookie))

    if not cookies:
        raise ValueError("No Netscape cookies found")

    return cookies


def parse_header_cookies(text: str) -> list[dict]:
    cookies = []

    for item in text.replace("\n", ";").split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue

        name, value = item.split("=", 1)
        name = name.strip()
        value = value.strip()

        if name.lower() in {
            "domain",
            "path",
            "expires",
            "max-age",
            "secure",
            "httponly",
            "samesite",
        }:
            continue

        cookies.append(
            normalize_cookie(
                {
                    "name": name,
                    "value": value,
                    "domain": ".tiktok.com",
                    "path": "/",
                    "secure": True,
                }
            )
        )

    if not cookies:
        raise ValueError("No name=value cookies found")

    return cookies


def parse_cookies(text: str) -> list[dict]:
    if text.startswith("[") or text.startswith("{"):
        return parse_json_cookies(text)

    try:
        return parse_browser_table_cookies(text)
    except ValueError:
        pass

    try:
        return parse_netscape_cookies(text)
    except ValueError:
        return parse_header_cookies(text)


def xpath_text_contains(text: str) -> str:
    lower_text = text.lower()
    return (
        "//*[not(self::script) and not(self::style)"
        " and string-length(normalize-space(.)) <= 180"
        " and contains(translate(normalize-space(.),"
        " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
        f" '{lower_text}')]"
    )


def click_element(driver: webdriver.Chrome, element) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.3)
    try:
        element.click()
    except WebDriverException:
        driver.execute_script("arguments[0].click();", element)


def clickable_parent(element):
    try:
        return element.find_element(
            By.XPATH,
            "./ancestor-or-self::*[self::button or self::a or @role='button' or @tabindex][1]",
        )
    except NoSuchElementException:
        return element


def find_visible_elements(driver: webdriver.Chrome, xpath: str) -> list:
    return [
        element
        for element in driver.find_elements(By.XPATH, xpath)
        if element.is_displayed()
    ]


def click_chat_by_name(driver: webdriver.Chrome, chat_name: str) -> None:
    wait = WebDriverWait(driver, WAIT_SECONDS)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    search_box_xpaths = [
        "//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search')]",
        "//input[contains(@placeholder, 'ค้นหา')]",
        "//*[@role='search']//input",
    ]

    end_time = time.time() + WAIT_SECONDS
    searched = False
    chat_xpath = xpath_text_contains(chat_name)

    while time.time() < end_time:
        for element in find_visible_elements(driver, chat_xpath):
            click_element(driver, clickable_parent(element))
            time.sleep(2)
            return

        if not searched:
            for search_xpath in search_box_xpaths:
                search_boxes = find_visible_elements(driver, search_xpath)
                if not search_boxes:
                    continue

                search_box = search_boxes[0]
                click_element(driver, search_box)
                search_box.send_keys(Keys.CONTROL, "a")
                search_box.send_keys(chat_name)
                searched = True
                time.sleep(2)
                break

        time.sleep(1)

    raise TimeoutException(f"Could not find chat name: {chat_name}")


def find_message_box(driver: webdriver.Chrome):
    wait = WebDriverWait(driver, WAIT_SECONDS)
    composer_xpaths = [
        "//*[@contenteditable='true' and not(ancestor::*[@role='search'])]",
        "//*[@role='textbox' and not(self::input) and not(ancestor::*[@role='search'])]",
        "//textarea[not(ancestor::*[@role='search'])]",
    ]

    end_time = time.time() + WAIT_SECONDS
    while time.time() < end_time:
        for xpath in composer_xpaths:
            elements = find_visible_elements(driver, xpath)
            if elements:
                return elements[-1]
        time.sleep(1)

    return wait.until(EC.visibility_of_element_located((By.XPATH, composer_xpaths[0])))


def element_text_and_labels(element) -> str:
    values = []
    for attr in ("aria-label", "title", "data-e2e", "data-testid"):
        value = element.get_attribute(attr)
        if value:
            values.append(value)

    text = element.text
    if text:
        values.append(text)

    return " ".join(values).strip().lower()


def is_upload_or_attach_button(element) -> bool:
    if element.find_elements(
        By.XPATH,
        ".//input[@type='file'] | ./ancestor-or-self::label[.//input[@type='file']]",
    ):
        return True

    label_text = element_text_and_labels(element)
    blocked_terms = (
        "upload",
        "attach",
        "attachment",
        "file",
        "image",
        "photo",
        "video",
        "media",
        "อัปโหลด",
        "อัพโหลด",
        "แนบ",
        "ไฟล์",
        "รูป",
        "ภาพ",
        "วิดีโอ",
        "สื่อ",
    )
    return any(term in label_text for term in blocked_terms)


def is_send_button(element) -> bool:
    if is_upload_or_attach_button(element):
        return False

    label_text = element_text_and_labels(element)
    send_terms = ("message-send", "send", "ส่ง")
    return any(term in label_text for term in send_terms)


def click_send_button_if_available(driver: webdriver.Chrome) -> bool:
    send_xpaths = [
        "//*[@data-e2e='message-send' and not(@disabled)]",
        "//button[not(@disabled) and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')]",
        "//*[@role='button' and not(@aria-disabled='true') and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')]",
        "//button[not(@disabled) and contains(@aria-label, 'ส่ง')]",
        "//*[@role='button' and not(@aria-disabled='true') and contains(@aria-label, 'ส่ง')]",
    ]

    for xpath in send_xpaths:
        for button in find_visible_elements(driver, xpath):
            if is_send_button(button):
                click_element(driver, button)
                return True

    return False


def send_message(driver: webdriver.Chrome, message: str) -> None:
    message_box = find_message_box(driver)
    click_element(driver, message_box)
    message_box.send_keys(message)
    time.sleep(1)

    message_box.send_keys(Keys.ENTER)
    time.sleep(1)

    try:
        remaining_text = message_box.text.strip()
    except WebDriverException:
        return

    if remaining_text:
        click_send_button_if_available(driver)


def quit_driver(driver: webdriver.Chrome | None) -> None:
    if not driver:
        return

    def shutdown():
        try:
            driver.quit()
        except Exception:
            pass

    thread = threading.Thread(target=shutdown, daemon=True)
    thread.start()
    thread.join(timeout=8)

    if thread.is_alive():
        logging.warning("driver.quit() timed out; continuing shutdown")


def open_tiktok_with_cookies(cookies: list[dict]) -> None:
    driver = None
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        driver = webdriver.Chrome(options=options)

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })

        wait = WebDriverWait(driver, WAIT_SECONDS)

        logging.info("Starting TikTok...")
        driver.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        logging.info("Deleting all cookies...")
        driver.delete_all_cookies()
        time.sleep(1)

        added = 0
        for cookie in cookies:
            if cookie.get("expiry") and cookie["expiry"] <= int(time.time()):
                logging.warning(f"Skipped expired cookie {cookie.get('name')}")
                continue

            try:
                driver.add_cookie(cookie)
                added += 1
            except (InvalidCookieDomainException, WebDriverException) as exc:
                logging.warning(
                    "Skipped cookie name=%s domain=%s path=%s reason=%s",
                    cookie.get("name"),
                    cookie.get("domain"),
                    cookie.get("path"),
                    exc,
                )

        logging.info(f"Added cookies: {added}/{len(cookies)}")

        logging.info("Refreshing webpage...")
        driver.refresh()
        time.sleep(3)

        logging.info(f"Directing to message: {MESSAGES_URL}")
        driver.get(MESSAGES_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        logging.info(f"Looking for name: {TARGET_CHAT_NAME}")
        click_chat_by_name(driver, TARGET_CHAT_NAME)

        logging.info(f"Sending message: '{MESSAGE_TEXT}'")
        send_message(driver, MESSAGE_TEXT)
        logging.info(f"Sent message to {TARGET_CHAT_NAME}: {MESSAGE_TEXT}")
        time.sleep(2)

    except Exception as e:
        logging.error(f"Error during execution: {str(e)}", exc_info=True)
        raise

    finally:
        if driver:
            try:
                driver.save_screenshot("final_screenshot.png")
                logging.info("Saved final screenshot successfully.")
            except Exception as screenshot_err:
                logging.warning(f"Could not save final screenshot: {screenshot_err}")

            quit_driver(driver)


def main() -> int:
    logging.info("Starting TikTok Automation Bot...")

    try:
        cookie_text = load_cookie_text(COOKIE_FILE)
        cookies = parse_cookies(cookie_text)
        open_tiktok_with_cookies(cookies)
        logging.info("Bot executed successfully.")
        return 0
    except Exception as e:
        logging.critical(f"Bot failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())