#!/usr/bin/env python3
"""
Scrape exam materials (papers, marking schemes, deferred, sound files)
from examinations.ie exam material archive. Saves to CSV.
"""
import time
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


URL = "https://www.examinations.ie/exammaterialarchive/"


def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.set_page_load_timeout(60)

    return driver


def accept_declaration(driver):
    driver.get(URL)

    # Longer wait; page or checkbox may load slowly
    wait = WebDriverWait(driver, 45)

    # Wait for page to settle (e.g. any redirect or overlay)
    time.sleep(2)

    # Try multiple ways to find and click the declaration checkbox
    checkbox = None
    for locator in [
        (By.ID, "declaration"),
        (By.NAME, "declaration"),
        (By.CSS_SELECTOR, "input[type='checkbox'][id='declaration']"),
        (By.CSS_SELECTOR, "input[type='checkbox']"),
    ]:
        try:
            checkbox = wait.until(EC.element_to_be_clickable(locator))
            break
        except Exception:
            continue

    if checkbox is None:
        raise RuntimeError(
            "Could not find declaration checkbox. "
            "Run without headless (comment out --headless in setup_driver()) to see the page."
        )

    # Scroll into view and click (helps if covered by banner)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
    time.sleep(0.5)
    checkbox.click()

    # Give the page time to react to the checkbox
    time.sleep(2)

    # Many declaration pages have a "Continue" / "Accept" / "Enter" button that reveals the form
    for btn in driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button'], button"):
        try:
            val = ((btn.get_attribute("value") or "") + " " + (btn.text or "")).lower()
            if any(x in val for x in ["continue", "accept", "enter", "submit", "proceed", "agree"]):
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    time.sleep(3)
                    break
        except Exception:
            continue

    # Wait for Material Type dropdown: try multiple selectors (site may use different ID/name)
    material_select = None
    for locator in [
        (By.ID, "MaterialType"),
        (By.NAME, "MaterialType"),
        (By.CSS_SELECTOR, "select#MaterialType"),
        (By.CSS_SELECTOR, "select[name='MaterialType']"),
        (By.ID, "materialType"),
        (By.CSS_SELECTOR, "select[id*='MaterialType']"),
        (By.CSS_SELECTOR, "select[id*='materialType']"),
    ]:
        try:
            material_select = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(locator)
            )
            if material_select.is_displayed():
                break
        except Exception:
            continue

    # Last resort: first <select> on the page with more than one option (often the Material Type)
    if material_select is None or not material_select.is_displayed():
        try:
            for sel in driver.find_elements(By.TAG_NAME, "select"):
                if sel.is_displayed() and len(Select(sel).options) > 1:
                    material_select = sel
                    break
        except Exception:
            pass

    if material_select is None or not material_select.is_displayed():
        raise RuntimeError(
            "Could not find Material Type dropdown after accepting declaration. "
            "Run without headless to see the page state."
        )

    # Wait until the select is enabled (may be disabled until declaration is processed)
    WebDriverWait(driver, 15).until(
        lambda d: material_select.is_enabled()
    )

    return material_select


def _find_select(driver, id_exact, id_contains=None):
    """Find a select by exact ID, partial ID, or first visible select with options."""
    try:
        el = driver.find_element(By.ID, id_exact)
        if el.is_displayed():
            return el
    except Exception:
        pass
    if id_contains:
        try:
            el = driver.find_element(By.CSS_SELECTOR, f"select[id*='{id_contains}']")
            if el.is_displayed():
                return el
        except Exception:
            pass
    # Fallback: first visible <select> with more than one option (for non-standard IDs)
    try:
        for el in driver.find_elements(By.TAG_NAME, "select"):
            if el.is_displayed() and len(Select(el).options) > 1:
                return el
    except Exception:
        pass
    return None


def get_select_options(select_element):
    select = Select(select_element)
    options = []

    for option in select.options:
        value = option.get_attribute("value")
        text = option.text.strip()

        if value and text and value != "0":
            options.append((value, text))

    return options


def select_option(driver, element_id_or_element, value):
    """Select by value. Second arg can be element ID (str) or the select WebElement."""
    if hasattr(element_id_or_element, "find_element"):
        select = Select(element_id_or_element)
    else:
        select = Select(driver.find_element(By.ID, element_id_or_element))
    select.select_by_value(value)
    time.sleep(1)


def extract_files(driver, material, year, exam, subject):
    data = []

    try:
        table = driver.find_element(By.ID, "GridView1")
        rows = table.find_elements(By.TAG_NAME, "tr")

        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, "td")

            if len(cols) >= 2:
                file_label = cols[0].text.strip()

                link_element = cols[0].find_element(By.TAG_NAME, "a")
                file_url = link_element.get_attribute("href")

                pdf_name = file_url.split("/")[-1] if file_url else ""

                data.append({
                    "Material Type": material,
                    "Year": year,
                    "Examination": exam,
                    "Subject": subject,
                    "File Label": file_label,
                    "PDF File Name": pdf_name,
                    "PDF URL": file_url
                })

    except Exception:
        pass

    return data


def scrape_all():
    driver = setup_driver()
    material_select = accept_declaration(driver)

    all_data = []

    if not material_select:
        raise RuntimeError("Could not find Material Type dropdown.")
    material_options = get_select_options(material_select)

    for material_value, material_text in material_options:

        material_select = _find_select(driver, "MaterialType", "MaterialType") or material_select
        select_option(driver, material_select, material_value)

        year_select = _find_select(driver, "Year", "Year")
        if not year_select:
            continue
        year_options = get_select_options(year_select)

        for year_value, year_text in year_options:

            year_select = _find_select(driver, "Year", "Year")
            if year_select:
                select_option(driver, year_select, year_value)

            exam_select = _find_select(driver, "Examination", "Examination")
            if not exam_select:
                continue
            exam_options = get_select_options(exam_select)

            for exam_value, exam_text in exam_options:

                exam_select = _find_select(driver, "Examination", "Examination")
                if exam_select:
                    select_option(driver, exam_select, exam_value)

                subject_select = _find_select(driver, "Subject", "Subject")
                if not subject_select:
                    continue
                subject_options = get_select_options(subject_select)

                for subject_value, subject_text in subject_options:

                    subject_select = _find_select(driver, "Subject", "Subject")
                    if subject_select:
                        select_option(driver, subject_select, subject_value)

                    try:
                        driver.find_element(By.ID, "SearchButton").click()
                        time.sleep(2)
                    except Exception:
                        pass

                    print(f"Scraping: {material_text}, {year_text}, {exam_text}, {subject_text}")

                    files = extract_files(
                        driver,
                        material_text,
                        year_text,
                        exam_text,
                        subject_text
                    )

                    all_data.extend(files)

    driver.quit()

    return all_data


def save_csv(data, filename="exam_materials.csv"):
    keys = [
        "Material Type",
        "Year",
        "Examination",
        "Subject",
        "File Label",
        "PDF File Name",
        "PDF URL"
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    data = scrape_all()

    print(f"Total files found: {len(data)}")

    save_csv(data)

    print("Saved to exam_materials.csv")
