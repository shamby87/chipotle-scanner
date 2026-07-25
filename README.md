# chipotle-scanner

Cron job that polls the PGA Tour Instagram account (via Meta Business Discovery) for Chipotle SMS promo codes and alerts Discord.

## Meta API access

The scanner reads another account's posts through the [Business Discovery](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/business-discovery/) edge of the Instagram Graph API (Instagram API with Facebook Login). That flavor of the API only works if *your own* Instagram account is a professional account attached to a Facebook Page you administer, and it only returns data for target accounts that are themselves Business or Creator accounts. `@pgatour` qualifies; personal accounts and age-gated accounts do not.

Work through the steps below once; they produce the four Meta values in `.env` (`IG_USER_ID`, `IG_ACCESS_TOKEN`, `META_APP_ID`, `META_APP_SECRET`).

### 1. Set up the Instagram and Facebook accounts

1. Convert your Instagram account to a professional account: Instagram app -> **Settings and privacy -> Account type and tools -> Switch to professional account**, and pick **Business** (Creator also works).
2. Create a Facebook Page at [facebook.com/pages/create](https://www.facebook.com/pages/create) if you don't already have one. Any name and category is fine - the Page exists only to anchor API permissions. You must be a Page admin.
3. Link the two: Meta Business Suite -> **Settings -> Linked accounts -> Instagram -> Connect account**.
4. Confirm the link resolved by opening [business.facebook.com](https://business.facebook.com/) and checking that the Instagram account appears under the Page.

### 2. Create a business portfolio

1. In [Meta Business Suite](https://business.facebook.com/) -> **Settings -> Business portfolio**, create a portfolio if you don't have one.
2. Under **Accounts -> Pages**, click **Add** and add the Page from step 1.
3. Under **Accounts -> Instagram accounts**, add the Instagram account.

Both assets must live in the same portfolio as the app you create next, otherwise token generation will silently omit the Instagram account.

### 3. Create the Meta app

1. Go to [developers.facebook.com/apps](https://developers.facebook.com/apps) -> **Create app**.
2. For use case, choose **Other**, then app type **Business**, and attach the business portfolio from step 2.
3. On the app dashboard, add the **Instagram** product (listed as "Instagram Graph API" or "Instagram" depending on the console version) and, when prompted, the **Facebook Login for Business** product. Business Discovery lives under the Facebook Login variant - do **not** use "Instagram API with Instagram Login" or the retired Basic Display API.
4. Copy **App ID** and **App secret** from **App settings -> Basic** into `META_APP_ID` and `META_APP_SECRET`.

Leave the app in **Development** mode. Development mode grants the permissions below to any user who holds a role on the app (that's you), so no App Review is needed for a personal cron job. App Review is only required if other people need to authorize the app.

### 4. Grant the permissions

Business Discovery requires a **Facebook User** access token - not a Page token, not an Instagram token - carrying:

| Permission | Why it's needed |
| --- | --- |
| `instagram_basic` | Read the Instagram account linked to your Page |
| `instagram_manage_insights` | Required by the `business_discovery` edge specifically |
| `pages_read_engagement` | Read the Page that the Instagram account is attached to |
| `pages_show_list` | List your Pages so you can look up the Instagram user id |

If your Page role was granted through the business portfolio rather than directly on the Page, Meta also requires `ads_read` (or `ads_management`). Adding `ads_read` is harmless either way, so include it if token generation fails with a permissions error.

### 5. Generate a token and find your Instagram user id

Open the [Graph API Explorer](https://developers.facebook.com/tools/explorer/), select your app, and set **User or Page** to **Get User Access Token**. Add each permission from step 4, click **Generate Access Token**, and complete the consent dialog - make sure you grant access to the Page *and* the Instagram account when the dialog asks which assets to share.

That yields a short-lived (~1 hour) token. Put it in `IG_ACCESS_TOKEN` as-is - on the first run the scanner exchanges it for a long-lived (~60 day) token and writes the result to `data/token.json`, which takes precedence over `.env` from then on. On later runs it re-exchanges again once the stored token is within 7 days of expiring, so as long as cron runs at least weekly you never have to touch the token again. If it does lapse, delete `data/token.json`, generate a fresh short-lived token from the Graph API Explorer, update `IG_ACCESS_TOKEN`, and run once.

Also look up your Instagram user id while the short-lived token is still valid:

```bash
export TOKEN='<short-lived token from the explorer>'
curl -s "https://graph.facebook.com/v25.0/me/accounts?access_token=$TOKEN"
curl -s "https://graph.facebook.com/v25.0/<PAGE_ID>?fields=instagram_business_account&access_token=$TOKEN"
```

The first call lists your Pages; the second returns `instagram_business_account.id`, which is your `IG_USER_ID`.

### 6. Verify

```bash
curl -s "https://graph.facebook.com/v25.0/<IG_USER_ID>\
?fields=business_discovery.username(pgatour){media.limit(1){id,caption,timestamp}}\
&access_token=<IG_ACCESS_TOKEN>"
```

A JSON payload containing `business_discovery.media.data` means everything is wired up. Common failures:

- `(#100) ... does not exist, cannot be loaded due to missing permissions` - the token is missing `instagram_manage_insights`, or you used a Page token instead of a User token.
- `(#190) Invalid OAuth access token` - the token expired, or it was generated for a different app.
- Empty or absent `business_discovery` - the target username is not a professional account, or your Instagram account isn't linked to the Page.

Business Discovery is rate limited to roughly 200 calls per user per hour, which the once per minute cron schedule below stays under.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# fill in IG_USER_ID, IG_ACCESS_TOKEN, META_APP_ID, META_APP_SECRET, DISCORD_WEBHOOK, USER_ID
```

`GRAPH_VERSION` defaults to `v25.0`; override it in `.env` if you pin a different Graph API version.

## Run once

```bash
.venv/bin/python main.py
```

## Cron

Runs every 1 minute from 7:00 AM through 8:59 PM, Thursday through Sunday.

```bash
* 7-20 * * THU-SAT,SUN cd path/to/chipotle-scanner && .venv/bin/python main.py >> logs/$(date +\%Y-\%m-%d).log 2>&1
```

Create `logs/` before enabling cron. Seen media ids live in `data/seen_posts.json`; refreshed tokens in `data/token.json`.
