# Instagram Real Estate Reel Finder

A Python + Playwright tool for finding property-listing Reels around Pune, Karjat, Panshet, and Pawna Lake, with a small local CSV contact register.

## Current workflow

1. Open Instagram in Google Chrome using a separate local browser profile.
2. Sign in manually.
3. Search location-specific property hashtags and keywords.
4. Review results and open relevant property Reels manually.
5. Read comments manually.
6. When a buyer has explicitly invited contact for the enquiry or agreed to receive relevant property details, choose the save-contact option and enter the number.
7. The tool validates the Indian mobile number, prevents duplicate numbers, and saves the contact to a local CSV file.

## Contact dataset

The local file is created at:

`data/buyers.csv`

It contains:
- Phone number
- Instagram username (optional)
- Location
- Source Reel URL
- Contact-permission confirmation
- Date/time recorded

The dataset is private to the local machine and `data/` is ignored by Git. Do not commit or upload buyer phone numbers, contact exports, cookies, browser sessions, or access tokens.

## Important limits

- This project does not automatically read Instagram comments or extract phone numbers from other users' posts.
- It does not scrape profiles, comments, or contact details.
- It does not like, follow, comment, DM, or post.
- It does not bypass login, access controls, or rate limits.
- Instagram's search is personalized and may show mixed results. Search phrases and hashtags are discovery hints, not a complete index.

Only record a buyer contact when you have permission to contact that person for the relevant enquiry. A number being visible in a comment does not automatically authorize unrelated marketing or repeated calls. Respect applicable platform terms and commercial communication rules.

## Windows / PyCharm

Run these commands from the repository folder:

```powershell
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/main.py
```

The separate Chrome profile is stored in `browser-data/` and is ignored by Git.
