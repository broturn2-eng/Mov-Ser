[README.md](https://github.com/user-attachments/files/31103267/README.md)
# Movies + Web Series Bot

This is a clean replacement for the supplied movie bot. Use it only with media you own or are authorised to distribute.

## What was changed

`main.py` from the supplied files is the 5,077-line anime bot: it supports anime → season → episode. `main MOV.py` is the 2,729-line movie-only bot. The latter has no web-series hierarchy and it posts immediately after receiving a short link.

The replacement has one normalized MongoDB `contents` collection:

```text
movie  → title, poster, description, quality files
series → title, poster, description
          └─ season → title, optional poster/description
                        └─ episode → title, description, quality files
```

`Add Movie` and `Add Web Series` are separate admin paths. Series has separate `Add Season` and `Add Episode` controls.

## Exact post flow

1. Admin picks Movie / Series / Season / Episode and receives the original Telegram deep link.
2. Admin sends the shortened HTTPS link.
3. The bot **automatically asks for the group-post description**. `/skip` retains the original description.
4. The admin can additionally change the temporary post title, set the destination, and preview it.
5. Publish sends the poster, an HTTPS Download button, and the edited text. Long descriptions use Telegram HTML `<blockquote expandable>` so they collapse in clients that support expandable quotes.

The edited title and description are held only in Telegram `user_data` for that draft. The `contents` document is never updated, and the post audit stores only content ID, destination, and time—not the edited text.

## Features

- Movie and web-series/season/episode flows; 480p, 720p, 1080p, and 4K files.
- Private deep-link delivery, optional timed deletion, Mongo indexes, pagination, title/description edits, content/season/episode deletion.
- Admin/co-admin roles, broadcast, user/content statistics, post preview, and deep-link generator.
- Admin setting for English, Hindi, Hinglish, Bengali, and Arabic. Static bot UI strings go through the language pack; user-added titles and descriptions are deliberately not machine-translated.
- Native asynchronous `AsyncMongoClient`, per-user update locks, connection pooling, Flask + Waitress webhook, and Telegram secret-header validation.

## Deploy

1. Copy `.env.example` to `.env` and fill every value. `WEBHOOK_PUBLIC_URL` must be a publicly reachable HTTPS URL.
2. Create a virtual environment and install packages:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Start it:

   ```powershell
   python main.py
   ```

4. Telegram webhook becomes `https://your-domain/telegram` (or the configured `WEBHOOK_PATH`). Do not put the bot token in the webhook path.

Give the bot admin access in every channel/group where it must publish. Send `/admin` in the bot's private chat to begin.

## Notes for old MongoDB data

This program intentionally uses a new `contents` collection inside `MONGO_DB`. That preserves old collections untouched. If you want to import old movie records, map each old `movies` document to `content_type: "movie"`, `title`, `description`, `poster_file_id`, and `files`; test the migration on a backup first.
