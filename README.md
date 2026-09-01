# daily excuses — instagram auto-poster

Posts one image from `images/` to Instagram 4× a day (09:00, 13:00, 19:00, 23:00
Tbilisi time), following `schedule.csv`. Runs entirely on free GitHub Actions —
no server, nothing to keep running.

## One-time setup (~30 min)

### 1. Instagram side
1. In the Instagram app: **Settings → Account type and tools → Switch to
   professional account** (Creator is fine).
2. Go to [developers.facebook.com](https://developers.facebook.com) → **My Apps →
   Create App** → choose the **Business** type (no Facebook Page needed).
3. In the app dashboard, **Add product → Instagram** → choose
   **API setup with Instagram business login**.
4. Under **Generate access tokens**, add/log in with your Instagram account and
   approve the permissions (`instagram_business_basic`,
   `instagram_business_content_publish`).
5. Copy the **access token** (long-lived, valid 60 days) and the
   **Instagram user ID** shown next to your account.

The app can stay in Development mode — publishing to your own account works
without App Review.

### 2. GitHub side
1. Create a new **public** repository (public is required — Instagram fetches
   the images from this repo's raw URLs) and upload the contents of this folder.
2. Repo **Settings → Secrets and variables → Actions**:
   - Secret `IG_USER_ID` — from step 1.5
   - Secret `IG_ACCESS_TOKEN` — from step 1.5
   - Secret `GH_PAT` *(optional but recommended)* — a fine-grained personal
     access token scoped to this repo with **Secrets: read and write**. With it,
     the weekly refresh workflow keeps the Instagram token alive forever.
     Without it, you'll get a failure email from GitHub around day 60 telling
     you to paste a fresh token.
   - Variable `HANDLE` — your handle without the @ (used in captions)
   - Variable `START_DATE` — the Monday you want day 1 to be, e.g. `2026-09-07`

### 3. Test it
Actions → **post to instagram** → **Run workflow** → set `test_post_id` to `1`
and leave `dry_run` as `1`. Check the log: it should print the post and image
URL. Run again with `dry_run` = `0` for one real post (delete it on Instagram
afterwards if you don't want it live yet). After that, the schedule runs itself.

## Files
- `images/` — 150 finished posts (JPEG, 1080×1080)
- `schedule.csv` — which post goes out on which day/slot (day 1 = START_DATE,
  must be a Monday; weekday-specific posts are pinned to their weekdays)
- `publish.py` — picks the current slot's post and publishes it
- `refresh_token.py` + weekly workflow — keeps the 60-day token alive
- `lines.csv`, `make_posts.py` — the copy and the renderer that generates
  the images (needs the Poppins font)

## Notes
- GitHub cron can run a few minutes late; the publisher matches the nearest
  slot within the hour, so posts still go out.
- Instagram's API limit is 100 posts/day; this uses 4.
- When the 38 days run out the workflow logs "batch finished" and does nothing —
  ask Claude for the next 150, replace `images/` and `schedule.csv`, and bump
  `START_DATE`.
