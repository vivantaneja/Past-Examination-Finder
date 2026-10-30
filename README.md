# Past Examination Finder

A small web app to find Irish state exam materials (past papers, marking schemes, deferred papers, and audio) from the [State Examinations Commission](https://www.examinations.ie/exammaterialarchive/) archive. Filter by examination, subject, year, level, language, and material type—then open direct links to the official PDFs and audio files.

**This app does not host any exam content.** It only links to resources on examinations.ie.

## Features

- **Examination**: Junior Cycle / Junior Certificate, Leaving Certificate, Leaving Certificate Applied
- **Subject**: All subjects available for the chosen examination
- **Year**: Years with available materials
- **Level**: Higher, Ordinary, Foundation, or Common (where applicable), plus All levels for shared resources
- **Language**: English, Irish, or Bilingual; shared bilingual files also appear with English/Irish materials
- **Material type**: Exam paper, Marking scheme, Deferred exam paper, Deferred marking scheme, Audio, or Video (with separate deferred audio/video options)

Only options that have data are shown, so you never pick a combination that returns nothing.

The catalogue includes **573 official 2026 entries**, checked on 30 October 2026: 349 examination papers/media entries and 224 marking schemes. The SEC did not list 2026 deferred papers or deferred marking schemes at that check. Availability varies by subject and material type; the app lists only entries found in the archive.

## Quick start

The app loads `data.json` via `fetch()`, so it must be served over HTTP (you can’t just open `index.html` in the browser).

**Option 1 — Python (no install if you have Python):**

```bash
git clone https://github.com/vivantaneja/Past-Examination-Finder.git
cd Past-Examination-Finder
python3 -m http.server 8000
```

**Option 2 — Node.js:**

```bash
npx serve
```

Then open **http://localhost:8000** (or the port shown) in your browser.

## Refresh the official catalogue

The site is static: it reads the checked-in `data.json`, rather than making cross-origin requests to the SEC from visitors' browsers. Refresh it using Python 3.9+ and `curl`:

```bash
python3 scripts/update_catalogue.py --year 2026 --accept-terms
```

Read the [SEC archive terms](https://www.examinations.ie/TermsConditions.html) before using `--accept-terms`. This command visits the actual archive form, discovers its examinations and subjects, and imports the published papers, schemes, deferred papers/schemes, and associated media. Each new entry retains its filename, description, and exact official download link. No document contents are copied into this project, and no filenames or unpublished years are invented.

Only the requested year is replaced; historical years are retained. The complete refresh must succeed before `data.json` is atomically replaced. Failed requests, unrecognised page structures, empty years, and disappearing material categories leave the current file intact. Source information, refresh time, and counts are recorded under `data.json`'s `_meta.years`.

Repeat `--year` to refresh several years. For an interrupted import, you can retain responses in a temporary cache and rerun the same command; use a new cache directory for each fresh refresh:

```bash
python3 scripts/update_catalogue.py --year 2026 --accept-terms --cache-dir /tmp/sec-2026-refresh
```

Requests are spaced one second apart. If the SEC rate-limits access, wait before retrying and increase `--delay` if needed. Commit and deploy the refreshed `data.json` with the app to publish an update.

## Checks

No test packages are required (Node.js 18+ and Python 3.9+):

```bash
node --test tests/catalogue.test.js
python3 -m unittest discover -s tests -p 'test_*.py'
```

These cover official link routing, reachable levels/languages/media, archive parsing, safe refreshes, and preservation of historical data.

## Project structure

| File        | Purpose                                  |
|------------|------------------------------------------|
| `index.html` | Single-page app structure and filters   |
| `app.js`     | Filter controls and result rendering    |
| `catalogue.js` | Shared material, language, level, and official-link handling |
| `styles.css` | Layout and styling                      |
| `data.json`  | Exam metadata (subjects, years, files)  |
| `scripts/update_catalogue.py` | Refresh selected years from the SEC archive |
| `tests/` | Catalogue and importer regression checks |

## Disclaimer

This is an **unofficial** project and is not affiliated with the State Examinations Commission. All exam materials remain the property of their respective owners. This app only provides easier access to publicly available links.

## Thanks

Heavily inspired by [examfinder.ie](https://examfinder.ie). Thanks to [Thomas Forbes](https://github.com/tjmf) for the original open-source `data.json`. New refreshes are sourced directly from the SEC's official archive.
