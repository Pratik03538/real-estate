"""Location-focused Instagram Reel discovery for real-estate listings.

Searches location-specific hashtags and caption keywords. A person manually
reviews Reels/comments and enters an authorized contact into the local CSV.
No automated comment scraping, phone extraction, likes, follows, or DMs.
"""

from pathlib import Path
from urllib.parse import quote
import re

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from contact_store import prompt_and_save_contact
from search_catalog import LOCATION_SEARCHES

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BROWSER_PROFILE = PROJECT_ROOT / "browser-data"
INSTAGRAM_URL = "https://www.instagram.com/"
KEYWORD_SEARCH_URL = "https://www.instagram.com/explore/search/keyword/?q={query}"
HASHTAG_URL = "https://www.instagram.com/explore/tags/{tag}/"


def choose_location() -> list[str]:
    locations = list(LOCATION_SEARCHES)

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
                    term
                    for terms in LOCATION_SEARCHES.values()
                    for term in terms
                ]
        print("Invalid choice. Please enter one of the menu numbers.")


def location_for_term(term: str) -> str:
    for location, terms in LOCATION_SEARCHES.items():
        if term in terms:
            return location
    return "Multiple locations"


def safe_click_search_reels_filter(page) -> bool:
    """Click Reels only when it appears inside the search content area."""
    for role in ("tab", "button", "link"):
        candidates = page.get_by_role(
            role,
            name=re.compile(r"^reels$", re.IGNORECASE),
        )
        try:
            matches = []
            for index in range(candidates.count()):
                item = candidates.nth(index)
                if not item.is_visible():
                    continue
                bounds = item.bounding_box()
                if not bounds:
                    continue

                # Do not click Instagram's global left-navigation Reels item.
                if bounds["x"] >= 250 and bounds["y"] >= 80:
                    matches.append(item)

            if len(matches) == 1:
                matches[0].click(timeout=2_500)
                page.wait_for_timeout(1_500)
                print("Selected the Reels filter in the search content area.")
                return True
        except PlaywrightError:
            continue

    return False


def build_search_url(term: str) -> tuple[str, bool]:
    cleaned = term.strip()
    if cleaned.startswith("#"):
        tag = cleaned[1:].replace(" ", "")
        return HASHTAG_URL.format(tag=quote(tag, safe="")), True

    return KEYWORD_SEARCH_URL.format(query=quote(cleaned, safe="")), False


def open_search(page, term: str, index: int, total: int) -> None:
    search_url, is_hashtag = build_search_url(term)
    print(f"\n[{index}/{total}] Search: {term}")
    print(f"Opening: {search_url}")

    try:
        page.goto(search_url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2_500)
    except PlaywrightError as exc:
        print(f"Search page did not finish loading: {exc}")

    if is_hashtag:
        print("Hashtag results opened. Review them and open relevant property Reels.")
    elif not safe_click_search_reels_filter(page):
        print(
            "A safe Reels search filter was not found. The global Reels "
            "navigation was NOT clicked. Choose the Reels category manually "
            "within search results if Instagram shows it."
        )

    print(
        "\nIn Chrome, open a relevant property Reel and review its comments. "
        "The program does not read or scrape comments automatically."
    )


def review_and_save_contacts(location: str) -> None:
    while input(
        "\nDid you find a buyer who invited contact for this enquiry? "
        "Save their contact? (y/n): "
    ).strip().lower() in {"y", "yes"}:
        prompt_and_save_contact(location)
        if input("Save another buyer from this location? (y/n): ").strip().lower() not in {"y", "yes"}:
            break


def main() -> None:
    BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)
    print("Starting Chrome with the project's separate browser profile...")

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
                "Could not start Google Chrome. Confirm Chrome is installed, "
                "close any previous project browser window, and retry. "
                f"Playwright details: {exc}"
            ) from exc

        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(INSTAGRAM_URL, wait_until="domcontentloaded", timeout=60_000)
            print("\nInstagram is open.")
            input("Sign in manually if Instagram asks, then press Enter here...")

            while True:
                terms = choose_location()
                if not terms:
                    break

                print(f"\n{len(terms)} targeted searches queued.")
                for index, term in enumerate(terms, start=1):
                    open_search(page, term, index, len(terms))

                    action = input(
                        "\nAfter reviewing this search in Chrome, press Enter "
                        "to continue, type s to save a buyer contact, or q to stop: "
                    ).strip().lower()

                    if action == "s":
                        review_and_save_contacts(location_for_term(term))
                        action = input(
                            "Press Enter for next search or q to stop: "
                        ).strip().lower()

                    if action == "q":
                        break

                if input("\nSearch another location? (y/n): ").strip().lower() != "y":
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
