# Apple Notes-like Web UI for Telegram Publishing (Stateless)

## What it is
- A three-pane web UI that mimics Apple Notes (channels sidebar, notes list, editor).
- Stateless backend: no database. "Folders" are your Telegram channels from env.
- Create and edit local drafts in the browser (stored in localStorage per channel) and publish directly to a selected Telegram channel.

## Backend
- FastAPI serves the static frontend and two APIs:
  - GET `/api/channels/` → returns configured channels
  - POST `/api/publish` → publish provided HTML + optional title to a Telegram channel

### Configure channels and credentials
Provide environment variables when running the app:

- `TELEGRAM_BOT_TOKEN`: your bot token (required unless you pass token per request)
- `TELEGRAM_CHANNELS`: list of channels. Supports either JSON or a compact string:
  - JSON example: `[{"id":"-100123","name":"Tech"},{"id":"@public","name":"Public"}]`
  - Compact example: `Tech=-100123, Public=@public`

Optional defaults:
- `APP_NAME`: title displayed in the browser tab

### Run locally
```bash
python3 -m pip install -r backend/requirements.txt
export TELEGRAM_BOT_TOKEN=123:ABC
export TELEGRAM_CHANNELS='[{"id":"-100123","name":"Tech"}]'
python3 -m uvicorn backend.app.main:app --reload --port 8000
```
Then open `http://localhost:8000`.

## Frontend
- Apple Notes-like layout with: channels list, local drafts list, rich-text editor.
- Images are embedded as data URLs and supported in Telegram publishing.
- Pin notes locally for sorting.

### Usage
1. Select a channel in the left sidebar.
2. Click "New Note" to create a local draft.
3. Write your post; use toolbar buttons for formatting and image uploads.
4. Click "Publish" to send to Telegram.

## API Reference
- GET `/api/channels/` → `[ { id: string, name: string }, ... ]`
- POST `/api/publish`
  - Body:
    ```json
    { "channel_id": "-100123...", "title": "Optional title", "content_html": "<p>HTML</p>" }
    ```
  - Uses global `TELEGRAM_BOT_TOKEN` unless `token` is provided in the request.

## Notes and limitations
- This project is stateless; drafts live in the browser. Clear site data to reset.
- Telegram supports a limited HTML subset; the backend automatically simplifies HTML.
- First image in the content is sent with the caption; additional images are sent as separate photos.
