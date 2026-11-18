# Real Estate — Property Buyer Intelligence

Python + Exa Search + SQLite + optional Meta Instagram webhooks.

## What this project does

1. Searches Exa for publicly indexed Instagram pages that may contain property-buyer wording for Pune, Lonavala, Karjat, Chakan and Mumbai.
2. Filters obvious seller / builder / rental advertisements and stores candidate page URLs and available publication dates.
3. Receives incoming Instagram DM and comment webhooks for **your own connected professional account**, after Meta app setup and approval.
4. Stores buyer-intent interactions in SQLite. Phone numbers and emails are redacted unless an explicit contact-consent phrase is detected in the incoming message.
5. Exports inbound lead records to CSV.

## Important scope and limitations

- Public Reel discovery uses Exa's public search index. It does not guarantee that every Reel or caption is indexed, and it cannot access private or login-only content.
- This project does not scrape other people's comments, harvest commenter phone numbers, access other people's private DMs, bypass login, or evade platform restrictions.
- Instagram webhooks apply to the app user's own connected professional account and subscribed events. They are not a way to monitor arbitrary accounts.
- Search results are **candidates**, not verified active buyers. Open source pages and confirm requirements before treating a person as a qualified buyer.
- A message sent to your Instagram account permits an in-app response under platform rules; it does not automatically mean the person consented to calls or WhatsApp. The app records external contact opt-in separately.
- Meta app review, permissions, token provisioning, webhook subscription and a public HTTPS callback are required before live events can reach the webhook server.

## Setup in PyCharm (Windows)

1. Clone or pull this repository in PyCharm.
2. Create/select a Python 3.10+ virtual environment.
3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env`.
5. Put your Exa API key in `.env` locally:

   ```text
   EXA_API_KEY=your_exa_key_here
   ```

6. Run `main.py`.

The Tkinter dashboard creates `property_buyers.sqlite3` automatically. The Exa key is not stored in the database or source code. The `.env` file is ignored by Git.

## Meta / Instagram setup (later, after you create your own account)

1. Create an Instagram Professional Business account.
2. Create a Meta developer app and add Instagram API with Instagram Login.
3. Request only the permissions needed for your own business account, such as `instagram_business_basic`, `instagram_business_manage_comments` and `instagram_business_manage_messages`.
4. Configure Instagram webhooks in Meta's App Dashboard and subscribe to supported fields.
5. Set `META_APP_SECRET` and a random `META_VERIFY_TOKEN` in your local `.env`.
6. Deploy the webhook receiver behind a public HTTPS URL; Meta cannot call a localhost-only URL.
7. Start locally for development with:

   ```powershell
   python main.py --webhook
   ```

Webhook callback path: `/webhook`. The receiver verifies `X-Hub-Signature-256` before processing events.

## Database tables

- `public_discoveries`: public indexed page candidates, source URLs, publication dates, buyer-intent score and review status.
- `inbound_leads`: interactions received by your own authorized Instagram account, extracted requirements and consent status.
- `webhook_events`: deduplication keys for incoming webhook events.

## Data handling

Keep API tokens and app secrets only in your local `.env`. Do not commit secrets, private conversations, or exported lead files to GitHub. Restrict database access on your PC and delete records when no longer needed. Contact people outside Instagram only when they have clearly opted in.
