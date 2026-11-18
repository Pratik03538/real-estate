"""Open Instagram in a dedicated, persistent Google Chrome profile.

This starter deliberately does not automate login, posting, following,
messaging, or data collection. Sign in manually in the opened browser.
"""

from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BROWSER_PROFILE = PROJECT_ROOT / "browser-data"
INSTAGRAM_URL = "https://www.instagram.com/"


def main() -> None:
    BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)

    print("Starting Google Chrome with the project's separate browser profile...")

    with sync_playwright() as playwright:
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE),
                channel="chrome",
                headless=False,
                no_viewport=True,
                args=["--start-maximized"],
            )
        except PlaywrightError as exc:
            raise SystemExit(
                "Could not start Google Chrome. Make sure Google Chrome is "
                "installed, close any previous project browser window, and "
                f"try again. Playwright details: {exc}"
            ) from exc

        try:
            page = context.pages[0] if context.pages else context.new_page()
            print(f"Opening {INSTAGRAM_URL}")

            try:
                page.goto(
                    INSTAGRAM_URL,
                    wait_until="domcontentloaded",
                    timeout=60_000,
                )
            except PlaywrightError as exc:
                print(f"Instagram navigation did not finish normally: {exc}")

            print("\nInstagram has been opened in Chrome.")
            print("You can sign in manually in this browser window.")
            input("Press Enter here when you want to close this project browser...")

        except (EOFError, KeyboardInterrupt):
            print("\nClosing the project browser...")
        finally:
            try:
                context.close()
            except PlaywrightError:
                # The user may already have closed the Chrome window.
                pass


if __name__ == "__main__":
    main()
