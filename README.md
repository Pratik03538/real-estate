# Instagram Real Estate Reel Finder

A Python + Playwright project that opens Instagram keyword-search pages in Google Chrome for property-listing Reel discovery around Pune, Karjat, Panshet, and Pawna Lake.

## Current features

- Opens Google Chrome using a separate persistent profile in `browser-data/`.
- Lets you sign in manually.
- Offers location choices: Pune, Karjat, Panshet, Pawna Lake, or all.
- Searches property, plots, land, and farmhouse phrases.
- Includes queries such as "comment your number" and "drop your number".
- Attempts to select Instagram's visible Reels filter when the page exposes an exact Reels tab/button/link.
- Opens one search at a time and waits for your confirmation before the next search.

## What it does not do

- It does not scrape Instagram pages, captions, comments, or profiles.
- It does not extract, save, or compile phone numbers or lead databases.
- It does not like, follow, comment, message, or post.
- It does not bypass login, private accounts, rate limits, or access controls.

Instagram search results vary by account, region, login state, and UI version. A keyword search may show mixed content; manually select the Reels category if Instagram does not expose it automatically, then open only relevant property-listing Reels yourself. Search phrases are discovery hints, not a guarantee that every result matches.

## Windows / PyCharm setup

From the repository folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/main.py
```

Sign in manually in the Chrome window if Instagram asks. The separate browser profile is stored locally and ignored by Git.

**Do not upload `browser-data/`, cookies, session files, passwords, or access tokens to GitHub.**

## Project structure

```text
real-estate/
├── .gitignore
├── README.md
├── requirements.txt
└── src/
    ├── main.py
    └── search_catalog.py
```
