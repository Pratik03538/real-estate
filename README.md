# Instagram Chrome Automation

A Python + Playwright starter project that opens Instagram in Google Chrome.

## Current scope

- Launches the installed Google Chrome browser.
- Opens https://www.instagram.com/.
- Uses a separate persistent browser profile in `browser-data/`.
- Lets you sign in manually; the local browser profile can retain that session.
- Does not automate login, posting, likes, follows, comments, direct messages, or scraping.

## Requirements

- Windows 10/11
- Python 3.10+
- Google Chrome installed
- PyCharm or another Python IDE

## Setup in PyCharm / Windows terminal

Clone the repository, then open its folder in PyCharm.

Create and activate a virtual environment:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the project:

```powershell
python src/main.py
```

Chrome will open Instagram. Sign in manually when needed. Return to the terminal and press Enter to close the project browser.

## Browser profile and privacy

The project stores its separate Chrome profile in `browser-data/`. This keeps the automation separate from your normal Chrome profile and allows the local session to persist between runs.

**Never upload `browser-data/`, cookies, session files, passwords, or access tokens to GitHub.** The profile directory is ignored by Git.

If Chrome does not launch, confirm that Google Chrome is installed and that another copy of this project's browser is not still running.

## Project structure

```text
real-estate/
├── .gitignore
├── README.md
├── requirements.txt
└── src/
    └── main.py
```

## Next development steps

Add future browser workflows as separate, clearly named modules after their requirements are defined. Keep authentication manual unless a safe, supported official authentication flow is explicitly designed.
