# Past Examination Finder

A small web app to find Irish state exam materials (past papers, marking schemes, deferred papers, and audio) from the [State Examinations Commission](https://www.examinations.ie/exammaterialarchive/) archive. Filter by examination, subject, year, level, language, and material type—then open direct links to the official PDFs and audio files.

**This app does not host any exam content.** It only links to resources on examinations.ie.

## Features

- **Examination**: Junior Certificate, Leaving Certificate, Leaving Certificate Applied
- **Subject**: All subjects available for the chosen examination
- **Year**: Years with available materials
- **Level**: Higher, Ordinary, Foundation, or Common (where applicable)
- **Language**: English or Irish
- **Material type**: Exam paper, Marking scheme, Deferred exam paper, Deferred marking scheme, or Audio

Only options that have data are shown, so you never pick a combination that returns nothing.

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

## Project structure

| File        | Purpose                                  |
|------------|------------------------------------------|
| `index.html` | Single-page app structure and filters   |
| `app.js`     | Filter logic and link building          |
| `styles.css` | Layout and styling                      |
| `data.json`  | Exam metadata (subjects, years, files)  |

## Disclaimer

This is an **unofficial** project and is not affiliated with the State Examinations Commission. All exam materials remain the property of their respective owners. This app only provides easier access to publicly available links.

## Thanks

Heavily inspired by [examfinder.ie](https://examfinder.ie). Thanks to [Thomas Forbes](https://github.com/tjmf) for the open-source `data.json` used in this project.
