# Instagram Real Estate Reel Finder

A guided Python + Playwright tool for finding property-listing Reels around Pune, Karjat, Panshet, and Pawna Lake.

## How searches work

- Location-specific hashtag searches open Instagram hashtag pages.
- Caption keyword searches open Instagram keyword-search pages.
- On keyword search pages, the script only clicks a Reels filter if it finds one in the main search-content area.
- The script intentionally avoids clicking Instagram's global left-navigation Reels item, which opens the general recommendation feed.
- If a safe search filter cannot be identified, choose the Reels category manually within the search results if Instagram shows one.

## Important limitations

Instagram results are ranked and personalized. A hashtag or keyword search is not a complete index of all Reels and may show mixed content. The available search categories vary across accounts, devices, and interface versions.

Instagram search targets searchable text such as terms and hashtags. It cannot reliably find Reels based on instructions written only inside their comments. Review a relevant Reel's comments manually to check for phrases like "comment your number" or "drop your number".

This project does not scrape captions/comments/profiles, collect phone numbers, build a lead database, like, follow, comment, message, post, or bypass access controls.

## Run on Windows

From the repository folder:

```powershell
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/main.py
```

Sign in manually in Chrome if needed. The separate profile is stored under `browser-data/` and is ignored by Git.

**Never upload `browser-data/`, cookies, session files, passwords, or access tokens to GitHub.**
