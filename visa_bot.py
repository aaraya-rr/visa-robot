import os
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import subprocess
import configparser
import calendar

# Load credentials from config.ini
config = configparser.ConfigParser()
config.read("config.ini")

try:
    EMAIL = config["credentials"]["email"]
    PASSWORD = config["credentials"]["password"]
except KeyError:
    print("[ERROR] Missing credentials in config.ini. Please make sure 'email' and 'password' are set under the [credentials] section.")
    exit(1)

# Load config from config.ini
config = configparser.ConfigParser()
config.read("config.ini")

try:
    EMAIL = config["credentials"]["email"]
    PASSWORD = config["credentials"]["password"]

    MAX_YEAR = int(config["settings"]["max_year"])
    MAX_MONTH = int(config["settings"]["max_month"])
    MAX_DAY = int(config["settings"]["max_day"])
    MAX_CALENDAR_ATTEMPTS = int(config["settings"]["max_calendar_attempts"])
except KeyError as e:
    print(f"[ERROR] Missing config key: {e}")
    exit(1)
except ValueError as e:
    print(f"[ERROR] Invalid value in config.ini: {e}")
    exit(1)


def beep():
    """
    Continuously plays beep.wav using the best available audio tool (Linux).
    """
    beep_path = os.path.abspath("beep.wav")

    if not os.path.exists(beep_path):
        print(f"[ERROR] File not found: {beep_path}")
        return

    if shutil.which("paplay"):
        play_cmd = ["paplay", beep_path]
    elif shutil.which("aplay"):
        play_cmd = ["aplay", beep_path]
    else:
        print("[ERROR] No suitable audio player found (paplay or aplay).")
        return

    while True:
        # Optional desktop notification
        subprocess.run(["notify-send", "Visa appointment available!"])
        subprocess.run(play_cmd)
        time.sleep(1)  # Wait before repeating the sound


def parse_month_year(text):
    """
    Parse month and year strings like "May 2025" into datetime objects.
    Returns None if parsing fails.
    """
    try:
        return datetime.strptime(text, "%B %Y")
    except ValueError:
        return None


def login(driver):
    """
    Log into the visa scheduling website.
    """
    print("[INFO] Opening login page...")
    driver.get("https://ais.usvisa-info.com/es-cr/niv/users/sign_in")

    print("[INFO] Waiting for email field...")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "user_email"))
    ).send_keys(EMAIL)

    print("[INFO] Filling in password...")
    driver.find_element(By.ID, "user_password").send_keys(PASSWORD)

    print("[INFO] Accepting terms and conditions...")
    checkbox = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.icheckbox"))
    )
    checkbox.click()

    print("[INFO] Clicking 'Sign In' button...")
    driver.find_element(By.NAME, "commit").click()

    print("[INFO] Waiting for redirection after login...")
    WebDriverWait(driver, 20).until(
        EC.url_changes("https://ais.usvisa-info.com/es-cr/niv/users/sign_in")
    )
    print("[INFO] URL after login:", driver.current_url)


def go_to_appointment_page(driver):
    """
    Navigate step-by-step to the appointment rescheduling section.
    """
    print("[INFO] Clicking 'Continue' after login...")
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Continuar"))
    ).click()

    print("[INFO] Locating 'Reprogramar cita' accordion item...")
    accordion_title = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//h5[contains(., 'Reprogramar cita')]/ancestor::a"))
    )

    parent_li = accordion_title.find_element(By.XPATH, "./ancestor::li")

    if "is-active" not in parent_li.get_attribute("class"):
        print("[INFO] Expanding accordion section...")
        driver.execute_script("arguments[0].click();", accordion_title)

    print("[INFO] Clicking green 'Reprogramar cita' button...")
    reprogramar_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'button') and contains(., 'Reprogramar cita')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", reprogramar_btn)
    reprogramar_btn.click()

    print("[INFO] Accepting 'Yo entiendo' checkbox by clicking the label...")
    label = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='confirmed_limit_message']"))
    )
    driver.execute_script("arguments[0].click();", label)

    print("[INFO] Clicking 'Continue' button...")
    continue_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "commit"))
    )
    driver.execute_script("arguments[0].click();", continue_btn)

    print("[INFO] Reached appointment calendar page.")

def build_max_date(year, month, day):
    """
    Build a valid max date even if the config day exceeds the month's length.
    """
    _, last_day = calendar.monthrange(year, month)
    safe_day = min(day, last_day)
    return datetime(year, month, safe_day)

def check_for_appointments(driver):
    """
    Check the calendar for available appointment dates.
    """
    calendar_attempts = 0

    while calendar_attempts < MAX_CALENDAR_ATTEMPTS:
        try:
            print(f"[INFO] Attempting to open calendar (attempt {calendar_attempts + 1})...")
            field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "appointments_consulate_appointment_date"))
            )
            field.click()

            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "ui-datepicker-title"))
            )
            break
        except:
            print("[WARN] Failed to load calendar. Reloading page...")
            driver.refresh()
            time.sleep(5)
            calendar_attempts += 1
    else:
        print("[ERROR] All attempts failed. Restarting session...")
        return False

    max_date = build_max_date(MAX_YEAR, MAX_MONTH, MAX_DAY)
    print(f"[INFO] Max allowed date: {max_date.date()}")

    while True:
        time.sleep(1)

        # Each month panel is a div.ui-datepicker-group
        panels = driver.find_elements(By.CSS_SELECTOR, "div.ui-datepicker-group")
        if len(panels) < 2:
            print("[ERROR] Could not detect both calendar panels.")
            return False

        # Titles inside each panel
        left_title_el = panels[0].find_element(By.CLASS_NAME, "ui-datepicker-title")
        right_title_el = panels[1].find_element(By.CLASS_NAME, "ui-datepicker-title")

        left_month = parse_month_year(left_title_el.text)
        right_month = parse_month_year(right_title_el.text)

        print(f"[INFO] Left month: {left_title_el.text} | Right month: {right_title_el.text}")

        check_dates_in_panel(panels[0], left_month, max_date)
        check_dates_in_panel(panels[1], right_month, max_date)

        # Stop when the right panel goes beyond max range (after checking it)
        if (right_month.year > MAX_YEAR or
            (right_month.year == MAX_YEAR and right_month.month > MAX_MONTH)):
            print("[INFO] Reached max calendar range.")
            return True

        try:
            next_button = driver.find_element(By.CLASS_NAME, "ui-datepicker-next")
            next_button.click()
        except:
            print("[ERROR] Could not click 'Next' button.")
            return True


def check_dates_in_panel(panel_el, current_month, max_date):
    """
    Scan available dates inside a specific calendar panel.
    """
    if not current_month:
        return

    # Only anchors inside THIS panel
    available_dates = panel_el.find_elements(By.CSS_SELECTOR, "table.ui-datepicker-calendar td a")
    print(f"[INFO] Checking dates for {current_month.strftime('%B %Y')}, found: {len(available_dates)}")

    year = current_month.year
    month = current_month.month
    _, last_day = calendar.monthrange(year, month)

    for elem in available_dates:
        text = elem.text.strip()
        if not text:
            continue

        try:
            day = int(text)
        except ValueError:
            continue

        # Defensive: ignore overflow days
        if day < 1 or day > last_day:
            continue

        appointment_date = datetime(year, month, day)
        print(f"[DEBUG] Found date: {appointment_date}")

        if appointment_date <= max_date:
            print(f"[ALERT] Appointment available on {appointment_date}!")
            beep()
            input("Press Enter to exit...")
            driver.quit()
            exit()


def check_dates(driver, current_date):
    """
    Scan available dates in the current calendar view and trigger alarm if a valid date is found.
    """
    if not current_date:
        return

    available_dates = driver.find_elements(
        By.CSS_SELECTOR, ".ui-datepicker-calendar td a")
    print(
        f"[INFO] Checking dates for {current_date.strftime('%B %Y')}, found: {len(available_dates)}")

    for elem in available_dates:
        try:
            day = int(elem.text)
            appointment_date = current_date.replace(day=day)
            print(f"[DEBUG] Found date: {appointment_date}")

            if appointment_date <= datetime(MAX_YEAR, MAX_MONTH, MAX_DAY):
                print(f"[ALERT] Appointment available on {appointment_date}!")
                beep()
                input("Press Enter to exit...")
                driver.quit()
                exit()
        except Exception as e:
            print(f"[WARN] Failed to parse date: {e}")


options = Options()
options.add_argument("--start-maximized")

print("[INFO] Launching Chrome browser...")
driver = webdriver.Chrome(options=options)

while True:
    try:
        login(driver)
        go_to_appointment_page(driver)

        print("[INFO] Monitoring appointments...")

        while True:
            time.sleep(5)
            driver.refresh()
            print("[INFO] Page refreshed.")

            success = check_for_appointments(driver)
            if not success:
                break  # Restart login
    except Exception as e:
        print(f"[ERROR] Unhandled exception: {e}. Restarting workflow...")
