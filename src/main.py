"""Guided Instagram Reel discovery for real-estate listings by location.

The browser opens Instagram search pages and optionally selects the visible
Reels filter. A person reviews and opens matching Reels manually.
No scraping, likes, follows, comments, DMs, or lead extraction is performed.
"""

from pathlib import Path
from urllib.parse import quote
import re

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from search_catalog import LOCATION_SEARCHES

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BROWSER_PROFILE = PROJECT_ROOT / "browser-data"
INSTAGRAM_URL = "https://www.instagram.com/"
SEARCH_URL = "https://www.instagram.com/explore/search/keyword/?q={query}"


def choose_location() -> list[str]:
    """Show a menu and return the selected search phrases."""
    locations = list(LOCATION_SEARCHES.keys())

    print("\n========== REAL ESTATE REEL SEARCH ==========")
    for index, location in enumerate(locations, start=1):
        print(f"{index}. {location}")
    print(f"{len(locations) + 1}. All locations")
    print("0. Exit")

    while True:
        choice = input("\nChoose a location: ").strip()
        if choice == "0":
            return []
        if choice.isdigit():
            number = int(choice)
            if 1 <= number <= len(locations):
                return LOCATION_SEARCHES[locations[number - 1]]
            if number == len(locations) + 1:
                return [
                    query
                    for searches in LOCATION_SEARCHES.values()
                    for query in searches
                ]
        print("Invalid choice. Please select one of the menu numbers.")


def select_reels_filter(page) -> bool:
    """Click an exact, visible Reels filter only when Instagram exposes it."""
    for role in ("tab", "button", "link"):
        try:
            locator = page.get_by_role(role, name=re.compile(r"^reels$", re.I))
            if locator.count() == 1 and locator.is_visible():
                locator.click(timeout=2_000)
                page.wait_for_timeout(1_000)
                return True
        except PlaywrightError:
            continue
    return False


def open_search(page, query: str, index: int, total: int) -> None:
    """Open one Instagram keyword search page."""
    search_url = SEARCH_URL.format(query=quote(query, safe=""))
    print(f"\n[{index}/{total}] Searching: {query}")

    try:
        page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        page.wait_for_timeout(2_000)
    except PlaywrightError as exc:
        print(f"Instagram search page did not finish loading: {exc}")

    if select_reels_filter(page):
        print("Reels filter selected.")
    else:
        print(
            "Instagram did not expose a clear Reels filter on this page. "
            "Use Instagram's visible Reels category if available."
        )

    print(
        "\nReview the results yourself. Open only property-listing Reels "
        "for the selected location. Look for captions such as "
        "'comment your number', 'drop your number', or 'comment number'."
    )


def main() -> None:
    BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)

    print("Starting Google Chrome with this project's separate browser profile...")

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
                "Could not start Google Chrome. Make sure Chrome is installed, "
                "close any previous project browser window, and try again. "
                f"Playwright details: {exc}"
            ) from exc

        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(
                INSTAGRAM_URL,
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            print("\nInstagram is open.")
            input(
                "Sign in manually in Chrome if needed, then press Enter here "
                "to continue..."
            )

            while True:
                queries = choose_location()
                if not queries:
                    break

                print(f"\n{len(queries)} search phrases queued.")
                for index, query in enumerate(queries, start=1):
                    open_search(page, query, index, len(queries))
                    action = input(
                        "\nPress Enter for next search, or type q to stop: "
                    ).strip().lower()
                    if action == "q":
                        break

                again = input(
                    "\nSearch another location? (y/n): "
                ).strip().lower()
                if again != "y":
                    break

        except (EOFError, KeyboardInterrupt):
            print("\nStopping Reel search...")
        finally:
            try:
                context.close()
            except PlaywrightError:
                pass


if __name__ == "__main__":
    main()
