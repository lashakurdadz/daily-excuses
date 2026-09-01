#!/usr/bin/env python3
"""
Publishes the scheduled post for the current time slot to Instagram.
Runs inside GitHub Actions on a cron (05,09,15,19 UTC = 09,13,19,23 Tbilisi).

Required env (GitHub repo secrets):
  IG_USER_ID        - your Instagram professional account's user ID
  IG_ACCESS_TOKEN   - long-lived Instagram API access token

Optional env:
  HANDLE            - your IG handle without @ (adds a follow line to captions)
  START_DATE        - YYYY-MM-DD of "day 1" (a Monday). Default: 2026-09-07
  TEST_POST_ID      - force-publish this post id right now (for testing)
  DRY_RUN           - "1" = do everything except actually publish
"""
import csv, os, sys, time, datetime, urllib.parse, urllib.request, json

API = "https://graph.instagram.com/v23.0"
TZ = datetime.timezone(datetime.timedelta(hours=4))  # Asia/Tbilisi, no DST
SLOTS = ["09:00", "13:00", "19:00", "23:00"]

CAPTION_POOL = [
    "posting this instead of going to therapy",
    "the accuracy is upsetting",
    "not me. definitely not me",
    "send this to someone with no context",
    "delete this if it's you. exactly",
    "we don't talk about how true this is",
    "screenshotted by 400 people already",
    "this one's personal",
]
TAGS = "#relatable #memes #mood #dailymemes #relatablememes"


def api(path, params, method="POST"):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{API}/{path}", data=data if method == "POST" else None,
                                 method=method)
    if method == "GET":
        req = urllib.request.Request(f"{API}/{path}?{urllib.parse.urlencode(params)}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise SystemExit(f"Instagram API error on /{path}: {e.code} {body}")


def pick_row():
    """row for the current day/slot, or TEST_POST_ID override"""
    rows = list(csv.DictReader(open("schedule.csv")))
    test = os.environ.get("TEST_POST_ID")
    if test:
        tid = f"{int(test):03d}.jpg"
        for r in rows:
            if r["file"] == tid:
                return r
        raise SystemExit(f"post id {test} not in schedule.csv")

    start = datetime.date.fromisoformat(os.environ.get("START_DATE", "2026-09-07"))
    now = datetime.datetime.now(TZ)
    day = (now.date() - start).days + 1
    if day < 1:
        print(f"start date {start} not reached yet - nothing to do"); sys.exit(0)
    # nearest slot within 2h (cron runners can be late)
    slot = min(SLOTS, key=lambda s: abs(now.hour * 60 + now.minute
                                        - (int(s[:2]) * 60 + int(s[3:]))))
    for r in rows:
        if int(r["day"]) == day and r["time"] == slot:
            return r
    print(f"no post scheduled for day {day} slot {slot} - batch may be finished. "
          f"ask claude for the next 150."); sys.exit(0)


def main():
    ig_user = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    row = pick_row()

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    image_url = f"https://raw.githubusercontent.com/{repo}/{branch}/images/{row['file']}"

    idx = int(row["file"][:3])
    caption = CAPTION_POOL[idx % len(CAPTION_POOL)]
    handle = os.environ.get("HANDLE", "").lstrip("@")
    if handle:
        caption += f"\n\nfollow @{handle} for daily excuses"
    caption += f"\n\n{TAGS}"

    print(f"day {row['day']} {row['weekday']} {row['time']} -> {row['file']}: {row['text']}")
    if os.environ.get("DRY_RUN") == "1":
        print("DRY_RUN=1 - skipping publish. image_url:", image_url); return

    container = api(f"{ig_user}/media",
                    {"image_url": image_url, "caption": caption, "access_token": token})
    creation_id = container["id"]
    time.sleep(15)  # let instagram fetch & process the image
    for attempt in range(4):
        try:
            result = api(f"{ig_user}/media_publish",
                         {"creation_id": creation_id, "access_token": token})
            print("published, media id:", result["id"]); return
        except SystemExit as e:
            if attempt == 3:
                raise
            print(f"publish attempt {attempt+1} failed ({e}), retrying in 20s...")
            time.sleep(20)


if __name__ == "__main__":
    main()
