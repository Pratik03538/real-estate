# Real Estate — Instagram Property Buyer Intelligence

Python desktop CRM using Exa public search, SQLite, and Meta's Instagram API with Instagram Login.

## Features

- Discover publicly indexed Instagram pages that may contain explicit buyer requirements for Pune, Lonavala, Karjat, Chakan, and Mumbai.
- Filter clear seller / builder / rental language from search candidates.
- Store source URL, available publication date, evidence, deduplication key, and manual review status.
- Verify a connected Instagram professional account using an Instagram Login access token.
- Receive incoming DMs and supported comment events for your own connected professional account using a signed Meta webhook.
- Extract city, property type, and budget from buyer enquiries.
- Redact phone and email details unless the inbound text contains an explicit contact-consent phrase.
- Export inbound lead records to CSV.

## Important scope

- Public discovery is only an Exa search of publicly indexed Instagram pages. It cannot guarantee every post, caption, Reel, comment, or page is indexed.
- The app does not bulk scrape other people's comments, collect hidden phone numbers, access third-party private DMs, bypass login/CAPTCHA, or evade Instagram restrictions.
- The official Instagram API works with professional Business or Creator accounts that authorize your app. It is not an API for monitoring arbitrary Instagram users.
- Messaging webhooks deliver messages sent to the connected professional account. Comment webhooks are for supported media owned by the connected account.
- Meta's current Instagram webhook documentation lists Reels as unsupported for the comments webhook. The project does not promise automated Reel-comment capture. A person can still share a Reel in a DM; supported message webhook attachments can include Reel shares.
- Public search results are only candidate pages. They are not proof that a buyer is active or that the author is identifiable. Manually review the source before qualifying a buyer.
- Receiving a DM or comment permits an in-platform business response subject to Meta's messaging policies; it is not automatic consent for calls, SMS, or WhatsApp. Use off-platform contact only after explicit opt-in.
- Meta app configuration, token generation, webhook subscriptions, app roles/review, and a public HTTPS callback are required before live events are delivered.

## Windows / PyCharm setup

1. Clone or pull this repository in PyCharm.
2. Use Python 3.10 or later.
3. Install dependencies by running: python -m pip install -r requirements.txt
4. Copy the local environment template: copy .env.example .env
5. Edit .env locally and add your Exa API key as EXA_API_KEY=...
6. Add your Instagram Login user access token as INSTAGRAM_ACCESS_TOKEN=...
7. Run the desktop app with: python main.py

The app creates property_buyers.sqlite3 automatically. The .env file and local database are excluded from Git by .gitignore.

## Instagram connection check

After setting INSTAGRAM_ACCESS_TOKEN, restart the app and press Check Instagram Account. The app calls the versioned Instagram profile endpoint on graph.instagram.com and requests user_id and username.

Or run: python main.py --check-instagram

The API token is read from local .env; it is not committed to GitHub or stored in the SQLite database.

## Instagram account and Meta app configuration

See INSTAGRAM_SETUP.md for the step-by-step setup. Use Meta's Instagram API with Instagram Login for your own professional account. This setup does not require a Facebook Page to be linked to the Instagram professional account.

Request only the needed scopes:
- instagram_business_basic
- instagram_business_manage_messages
- instagram_business_manage_comments

For a new Meta app, add the Instagram product and use the Instagram Login/API setup shown in the Meta App Dashboard. Generate an access token for your own professional account and place it in the local .env.

## Webhook receiver

After the Meta app and token are configured, set these values locally in .env:

- META_APP_SECRET: App Secret from Meta App settings (server-side only).
- META_VERIFY_TOKEN: a random secret string that you create for webhook verification.
- WEBHOOK_PORT=5000.

Start the receiver with: python main.py --webhook

Callback path: /webhook. Meta requires a publicly reachable HTTPS callback; a localhost-only URL cannot receive Meta's webhook requests. Configure the Instagram object and subscribe to supported messages and/or comments fields in the Meta App Dashboard. Ensure your selected Instagram Login setup exposes the relevant webhook fields and required permissions. Advanced Access / App Review may be required for people who do not have an app role.

Do not run a public tunnel or production callback until you have configured HTTPS, verified the endpoint, secured secrets, and reviewed the Meta requirements for your app.

## Database tables

- public_discoveries: public indexed Instagram page candidates, source URL, publication date, evidence, buyer-intent score, manual review state.
- inbound_leads: relevant DMs/comments received by your own connected professional account, extracted buyer fields, and contact-consent state.
- webhook_events: webhook event hashes to prevent duplicate processing.

## Privacy and secrets

- Never commit .env, access tokens, Meta App Secret, webhook verification token, real customer messages, or exported lead files to GitHub.
- The webhook verifies Meta's X-Hub-Signature-256 signature before processing.
- Phone numbers are not retained from inbound text unless the message also contains a recognized explicit contact-consent phrase. Review each opt-in manually before contacting outside Instagram.
- Restrict access to your PC and database. Delete records when no longer needed.
