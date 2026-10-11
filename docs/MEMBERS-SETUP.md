# Member accounts and collections

Sign-up is free. People who are not signed in can still search, identify a figure and read the reference answers. Saving a figure, making lists and the checklist appear only after sign-in.

Sign-in providers are email, Google and Facebook.

If the environment variables below are missing, the deployed site hides Sign in and every collection control. Identification keeps working.

Nothing in this repository creates a Clerk application, a Neon database, or a paid Vercel add-on. You create those yourself. Do not commit secret values.

## Stack

- **Clerk** for sign-in. The site is a static page plus Vercel functions, and Clerk's browser SDK mounts on that page. Email codes, Google and Facebook are switched on in the Clerk dashboard. The server checks the session with `@clerk/backend`.
- **Neon Postgres** for the lists and saved items. The function uses `@neondatabase/serverless`, which speaks HTTP, so it fits a short-lived Hobby function.
- A `plan` column (and Clerk `publicMetadata.plan`, if you set it later) is the subscription gate. Today every new member is `free` and can save. No payment is collected.

Auth.js was not used because it expects a Next.js app, and this site is not one. Supabase would add a second sign-in system next to Clerk.

## Local trial, with no accounts

From the project directory, after `npm install`:

```bash
node tools/dev-server.mjs
```

Open `http://127.0.0.1:4173`. Sign in, Save to…, lists and the checklist work on this computer. The dev server sets `MEMBERS_DEV=1` and stores rows in a temp file. That flag is ignored when `VERCEL_ENV=production`, so it cannot turn on a back door on the live site.

Google and Facebook buttons in this local mode sign in with the email you type. They do not contact Google or Facebook.

## 1. Clerk

1. Create a free Clerk application at [https://dashboard.clerk.com](https://dashboard.clerk.com), or add the Clerk integration from the Vercel Marketplace and connect it to this project. The Marketplace step is yours to confirm. This repo does not install it.
2. In the Clerk application, enable **Email** (email code), **Google** and **Facebook**.
3. Under API keys, copy the publishable key and the secret key.
4. In the Vercel project, add:
   - `CLERK_PUBLISHABLE_KEY` (starts with `pk_`)
   - `CLERK_SECRET_KEY` (starts with `sk_`)
5. Redeploy. The page asks `/api/members` for the publishable key, so the key does not have to be baked into `index.html`.
6. In Clerk, set the allowed redirect URL to `https://YOUR-DOMAIN/sso-callback.html` and the home URL to `https://YOUR-DOMAIN/`. The callback page is `sso-callback.html`.
7. Use Clerk's development instance while you are testing. Confirm the current free-plan monthly active user cap on Clerk's pricing page before you invite collectors.

The publishable key is public. The secret key stays on the server.

This code uses Clerk core 2: `@clerk/backend` 2.x on the server and `@clerk/clerk-js` 5.128.0 in the browser. Keep those major versions together. Clerk core 3 uses different package majors.

## 2. Google

Google Cloud has no fee for this OAuth client.

1. Open [https://console.cloud.google.com](https://console.cloud.google.com) and create a project.
2. Configure the OAuth consent screen (External is fine for a public collector site). Add the app name SW-7885 and your contact email.
3. Create an OAuth client ID of type **Web application**.
4. Clerk's Google connection page shows the authorised redirect URI. Paste that exact URI into the Google client. It looks like `https://....clerk.accounts.dev/v1/oauth_callback`.
5. Copy the client ID and client secret into Clerk's Google social connection.
6. While the consent screen is in testing, only the Google accounts you list as test users can sign in. Publish the consent screen when you want any Google account to work.

## 3. Facebook

A Meta developer account and Facebook Login have no fee.

1. Open [https://developers.facebook.com](https://developers.facebook.com) and create an app. Choose a consumer app if Meta asks for a type.
2. Add the **Facebook Login** product.
3. Clerk's Facebook connection page shows the redirect URI. Put that URI in Facebook Login's valid OAuth redirect URIs.
4. Copy the Facebook App ID and App secret into Clerk's Facebook connection.
5. Until the Meta app is live, only people you add as admin, developer or tester can sign in with Facebook. App review is Meta's process for letting everyone else in. There is no programme fee for that review.

## 4. Neon Postgres

1. In the Vercel Marketplace, add Neon, or create a free project at [https://neon.tech](https://neon.tech). Confirm the free storage cap on Neon's pricing page. A free project pauses after a period with no queries and wakes on the next request.
2. Copy the pooled connection string into the Vercel environment variable `DATABASE_URL`.
3. Redeploy. The members function creates its tables the first time someone signs in. You do not run a migration by hand.

Saved photos are reduced JPEGs (longest side 960 pixels, under about 180 KB each). A Hobby Neon allowance is enough for a personal collection. It is not sized for thousands of full camera photos.

Without `DATABASE_URL`, a deployed site that has Clerk keys will still sign in, but the collection rows only live in that function's memory and disappear. Set `DATABASE_URL` before you invite anyone.

## 5. Environment variables

| Name | Where | Required |
| --- | --- | --- |
| `CLERK_PUBLISHABLE_KEY` | Vercel, server | Yes, for live sign-in |
| `CLERK_SECRET_KEY` | Vercel, server | Yes, for live sign-in |
| `DATABASE_URL` | Vercel, server | Yes, to keep collections |
| `MEMBERS_DEV` | Your computer only | Set by `tools/dev-server.mjs`. Ignored in production |
| `MEMBERS_DEV_SECRET` | Your computer only | Optional cookie signing secret for local mode |
| `MEMBERS_STORE_PATH` | Your computer only | Optional file for local collections |

`.env.example` lists the same names with empty values.

## 6. Adding a paid gate later

Do not add a card form yet. When you are ready:

1. Keep using the `plan` value. New members are `free`. `free`, `member` and `subscriber` can save. `lapsed` cannot.
2. `canSave()` in `lib/members-plan.js` is the only check. Save, edit, move and new lists are refused when it returns false. Reading and deleting still work, so a lapsed member can export nothing automatic but can remove their rows.
3. Set the plan from your billing webhook by updating the member row, or set Clerk `publicMetadata.plan` to `subscriber` or `lapsed`. The sign-in check reads that metadata and writes it onto the member row.
4. The tables do not need a new column for this.

## What a member can save

Each item stores the figure, the factory, the mould, the COO, a grade for the figure, each accessory with its own variant and grade, an optional reduced photo, notes, and a date. The grade list starts at Near Mint and ends at Poor.

Lists start with Personal Collection. A member can add lists such as Trades, Selling and Wants, then move or delete items. Personal Collection cannot be renamed or deleted. The checklist compares saved figures with the Kenner debut list and marks each one owned or needed.
