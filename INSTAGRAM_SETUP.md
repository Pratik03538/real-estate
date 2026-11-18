# Instagram Business Connection — Setup Guide

This project uses Meta's Instagram API with Instagram Login for an Instagram Professional Business or Creator account.

Official references:
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/
- https://developers.facebook.com/docs/instagram/platform/instagram-api/changelog/
- https://developers.facebook.com/docs/graph-api/webhooks/reference/instagram
- https://developers.facebook.com/documentation/business-messaging/instagram-messaging/webhooks

## A. Create your Instagram account

1. Create an Instagram account using your own business details.
2. In Instagram settings, switch it to a Professional account.
3. Choose Business (recommended for this property lead workflow) or Creator.
4. Complete the profile and enable two-factor authentication.

## B. Create a Meta developer app

1. Go to https://developers.facebook.com/ and sign in.
2. Complete developer registration if prompted.
3. Create a Meta app and add the Instagram product.
4. In the Instagram product, choose API setup with Instagram Login.
5. Add your Instagram professional account as an app role/tester if the dashboard asks for it.
6. Request only these scopes:
   - instagram_business_basic
   - instagram_business_manage_messages
   - instagram_business_manage_comments
7. Use the Dashboard token generation flow to authorize your own professional account and generate a user access token.

Instagram Login uses graph.instagram.com and does not require a Facebook Page linked to the professional Instagram account. Use the current instagram_business_... scope names.

## C. Put credentials in the local .env file

Copy .env.example to .env, then edit it locally:

    EXA_API_KEY=your_exa_key
    INSTAGRAM_ACCESS_TOKEN=your_instagram_user_access_token
    META_API_VERSION=v27.0
    META_APP_SECRET=your_meta_app_secret
    META_VERIFY_TOKEN=create_a_long_random_string
    WEBHOOK_PORT=5000

Do not paste these values into GitHub, a screenshot, or a chat. The repository .gitignore excludes .env.

## D. Verify the Instagram token

Restart the PyCharm app and press Check Instagram Account.

Or run: python main.py --check-instagram

Successful output should include the connected professional account's username and user ID. If it fails, check that:
- The token was generated for the same app and Instagram Login product.
- The token has not expired or been revoked.
- META_API_VERSION is set to a version available in your Meta dashboard/docs.
- The requested scopes were granted.

## E. Configure webhooks after token verification

1. In Meta App Dashboard, configure the Instagram webhook product/object.
2. Set the callback URL to your deployed public HTTPS endpoint ending in /webhook.
3. Use the same random string in META_VERIFY_TOKEN when Meta asks for the verification token.
4. Subscribe to the supported event fields available for your login setup, such as messages and comments.
5. Start the local receiver for development with: python main.py --webhook
6. For live delivery, deploy behind a public HTTPS URL. Meta cannot deliver webhooks to 127.0.0.1 or a private LAN address.
7. Complete App Review / Advanced Access where Meta requires it for users who are not app-role testers.

## F. What this project can and cannot receive

- It can process incoming text messages sent to the professional account connected to your app, after webhook subscription and permissions are approved.
- It can process supported comments on media owned by the connected account, if the comments webhook is available and subscribed.
- Meta's current Instagram webhook documentation says Reels are not supported for the comments webhook. Therefore, this project does not claim to automatically receive all comments on your Reels.
- A DM may contain a shared Reel attachment. The messaging webhook can report Reel attachment types, but that is different from collecting comments from someone else's Reel.
- It cannot read arbitrary people's private DMs or scrape comments/phone numbers from other accounts.

## G. Lead handling rules

- The database stores relevant property enquiries received by your own connected account.
- Contact details in a message are withheld unless a recognized explicit contact-consent phrase is present. Phrase matching is only a first-pass aid; a human must check the wording and consent scope.
- An Instagram DM is permission to respond inside Instagram subject to Meta's messaging policies. It is not automatic permission to call or WhatsApp the person.
- Treat saved interactions as unverified until a human reviews the conversation and confirms the buyer's need.
