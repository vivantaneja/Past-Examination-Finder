from playwright.sync_api import sync_playwright
import json

ARCHIVE_URL = "https://www.examinations.ie/exammaterialarchive/?i=109.114.105.94.105"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load archive page
        page.goto(ARCHIVE_URL, wait_until="networkidle")

        # NOTE: These rely on the accessible labels on the page.
        # If they don't match exactly, we can switch to different selectors.

        # Type: Exam Papers
        page.get_by_label("Type").select_option(label="Exam Papers")

        # Year: 2025
        page.get_by_label("Year").select_option(label="2025")

        # Examination: Leaving Certificate
        page.get_by_label("Examination").select_option(label="Leaving Certificate")

        # Subject: Chemistry
        page.get_by_label("Subject").select_option(label="Chemistry")

        # Some versions of the page need an explicit search click, some auto-update
        try:
            page.get_by_role("button", name="Search").click()
        except Exception:
            pass

        # Give results a moment to render
        page.wait_for_timeout(2000)

        # Grab the last table on the page (bottom results table)
        tables = page.locator("table")
        count = tables.count()
        if count == 0:
            raise RuntimeError("No tables found on page after search – selector likely needs updating.")

        results_table = tables.nth(count - 1)

        # Extract rows into structured data
        rows_data = results_table.evaluate(
            """(table) => {
                const rows = Array.from(table.querySelectorAll('tr'));
                if (rows.length === 0) return [];

                const headerCells = Array.from(rows[0].querySelectorAll('th,td'));
                const headers = headerCells.map(th => th.innerText.trim() || `col_${headers.indexOf(th)}`);

                return rows.slice(1).map(tr => {
                    const cells = Array.from(tr.querySelectorAll('td'));
                    const row = {};
                    cells.forEach((td, idx) => {
                        const key = headers[idx] || `col_${idx}`;
                        const link = td.querySelector('a');
                        if (link && link.getAttribute('href')) {
                            row[key] = link.getAttribute('href').trim();
                            row[key + "_text"] = (link.innerText || '').trim();
                        } else {
                            row[key] = td.innerText.trim();
                        }
                    });
                    return row;
                });
            }"""
        )

        browser.close()

        # Print JSON so you can inspect it or redirect to a file
        print(json.dumps(rows_data, indent=2))


if __name__ == "__main__":
    main()

