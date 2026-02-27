# Irish State Examinations — Past Papers

A simple web app to find and open past exam papers from [examinations.ie](https://www.examinations.ie/exammaterialarchive/) by course, subject, year, level, and language.

## Run the web app

`data.json` is loaded via `fetch()`, so the app must be served over HTTP (not opened as a file).

```bash
python3 -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000) and use the filters to get a list of papers with direct links to examinations.ie.

## Scraping exam materials (papers, marking schemes, deferred, sound)

To build or refresh the dataset from the official archive (all material types):

1. **Install scraper dependencies** (requires Chrome/Chromium):

   ```bash
   pip install -r requirements-scrape.txt
   ```

2. **Run the scraper**:

   ```bash
   python3 scrape_examinations.py
   ```

   This opens the examinations.ie archive, accepts the declaration, then iterates through Material Type, Year, Examination, and Subject. Results are saved to `exam_materials.csv` with columns: Material Type, Year, Examination, Subject, File Label, PDF File Name, PDF URL.

   The script runs in headless Chrome. Remove the `--headless` option in `setup_driver()` if you want to watch the browser. A full run can take a while due to the number of combinations.

## CLI (optional)

```bash
python3 main.py
```

Follow the prompts to pick course → subject → year → level → language → paper; the script prints the examinations.ie URL.
