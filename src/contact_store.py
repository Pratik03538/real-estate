"""Save buyer contacts that the operator is authorized to record.

This module does not read Instagram comments or scrape phone numbers. The
operator reviews a Reel and enters a contact only after confirming permission
to contact the person about the relevant property enquiry.
"""

import csv
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CONTACTS_FILE = DATA_DIR / "buyers.csv"

FIELDNAMES = [
    "phone_number",
    "instagram_username",
    "location",
    "source_reel_url",
    "permission_to_contact_confirmed",
    "collected_at",
]


def normalize_indian_mobile(raw_number: str) -> str | None:
    """Normalize a valid Indian mobile number to +91XXXXXXXXXX."""
    digits = re.sub(r"\D", "", raw_number)

    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]

    if len(digits) != 10 or digits[0] not in "6789":
        return None

    return f"+91{digits}"


def existing_numbers() -> set[str]:
    """Read existing numbers for deduplication."""
    if not CONTACTS_FILE.exists():
        return set()

    saved: set[str] = set()
    try:
        with CONTACTS_FILE.open("r", newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                number = normalize_indian_mobile(row.get("phone_number", ""))
                if number:
                    saved.add(number)
    except (OSError, csv.Error) as exc:
        raise RuntimeError(f"Could not read the local contacts file: {exc}") from exc

    return saved


def prompt_and_save_contact(location: str) -> bool:
    """Prompt for one buyer contact and append it to the private local CSV."""
    print("\n--- Save buyer contact ---")
    print("Only record a contact when the buyer invited contact for this enquiry")
    print("or has agreed to receive your relevant property details.")

    raw_phone = input("Buyer mobile number: ").strip()
    phone_number = normalize_indian_mobile(raw_phone)
    if not phone_number:
        print("Not saved: enter a valid 10-digit Indian mobile number.")
        return False

    if phone_number in existing_numbers():
        print("Not saved: this phone number is already in your local dataset.")
        return False

    username = input("Instagram username (optional, without @): ").strip().lstrip("@")
    reel_url = input("Source Reel URL (paste the exact Instagram Reel link): ").strip()

    if not (
        reel_url.startswith("https://www.instagram.com/reel/")
        or reel_url.startswith("https://instagram.com/reel/")
        or reel_url.startswith("https://www.instagram.com/p/")
        or reel_url.startswith("https://instagram.com/p/")
    ):
        print("Not saved: paste a valid Instagram Reel/post URL as the source.")
        return False

    consent = input(
        "Did the buyer explicitly invite contact for this enquiry or agree "
        "to receive your relevant property details? (y/n): "
    ).strip().lower()

    if consent not in {"y", "yes"}:
        print("Not saved: permission to contact was not confirmed.")
        return False

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_exists = CONTACTS_FILE.exists()

    try:
        with CONTACTS_FILE.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
            if not file_exists or CONTACTS_FILE.stat().st_size == 0:
                writer.writeheader()

            writer.writerow(
                {
                    "phone_number": phone_number,
                    "instagram_username": username,
                    "location": location,
                    "source_reel_url": reel_url,
                    "permission_to_contact_confirmed": "yes",
                    "collected_at": datetime.now().astimezone().isoformat(
                        timespec="seconds"
                    ),
                }
            )
    except (OSError, csv.Error) as exc:
        print(f"Could not save the contact: {exc}")
        return False

    print(f"Saved locally. Dataset: {CONTACTS_FILE}")
    return True
