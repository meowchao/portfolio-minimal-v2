#!/usr/bin/env python3
"""Poll Telegram for new photos, resize, append to gallery/gallery.json.

Does NOT ack updates: it prints the offset to ack via $GITHUB_OUTPUT so the
workflow acks only after the commit has been pushed. Processing is idempotent
(ids derive from message date + message_id), so a re-run never duplicates.
"""
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageOps

TOKEN = os.environ["BOT_TOKEN"]
ALLOWED = int(os.environ["ALLOWED_USER_ID"])
API = f"https://api.telegram.org/bot{TOKEN}"
FILE_API = f"https://api.telegram.org/file/bot{TOKEN}"

ROOT = Path(__file__).resolve().parent.parent
GALLERY = ROOT / "gallery"
JSON_PATH = GALLERY / "gallery.json"
FULL_MAX, THUMB_MAX = 1400, 480
CAPTION_MAX = 280


def tg(method, **params):
    r = requests.post(f"{API}/{method}", json=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"{method}: {data}")
    return data["result"]


def download(file_id):
    info = tg("getFile", file_id=file_id)
    r = requests.get(f"{FILE_API}/{info['file_path']}", timeout=60)
    r.raise_for_status()
    return r.content


def pick_file_id(msg):
    """Compressed photo -> largest size. Sent-as-file -> document if image/*."""
    if msg.get("photo"):
        return msg["photo"][-1]["file_id"]
    doc = msg.get("document")
    if doc and doc.get("mime_type", "").startswith("image/"):
        return doc["file_id"]
    return None


def save_variants(raw, entry_id):
    img = Image.open(io.BytesIO(raw))
    img = ImageOps.exif_transpose(img)  # fix phone rotation before stripping EXIF
    img = img.convert("RGB")            # also drops alpha/palette weirdness

    full = img.copy()
    full.thumbnail((FULL_MAX, FULL_MAX), Image.LANCZOS)
    # No exif= kwarg -> metadata (incl. GPS) is not written.
    full.save(GALLERY / "img" / f"{entry_id}.webp", "WEBP", quality=80, method=6)

    thumb = img.copy()
    thumb.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
    thumb.save(GALLERY / "thumb" / f"{entry_id}.webp", "WEBP", quality=72, method=6)
    return full.size


def delete_entry(items, entry_id):
    kept = [e for e in items if e["id"] != entry_id]
    if len(kept) == len(items):
        return items, False
    for sub in ("img", "thumb"):
        (GALLERY / sub / f"{entry_id}.webp").unlink(missing_ok=True)
    return kept, True


def reply(chat_id, text):
    try:
        tg("sendMessage", chat_id=chat_id, text=text)
    except Exception as e:  # feedback is best-effort
        print(f"reply failed: {e}", file=sys.stderr)


def main():
    items = json.loads(JSON_PATH.read_text()) if JSON_PATH.exists() else []
    known = {e["id"] for e in items}

    updates = tg("getUpdates", timeout=0, allowed_updates=["message"])
    if not updates:
        print("no updates")
        return
    max_id = max(u["update_id"] for u in updates)
    changed = False

    for u in updates:
        msg = u.get("message")
        if not msg or msg.get("from", {}).get("id") != ALLOWED:
            continue  # ignore everyone but you
        chat_id = msg["chat"]["id"]

        text = (msg.get("text") or "").strip()
        if text.startswith("/del "):
            items, ok = delete_entry(items, text[5:].strip())
            changed |= ok
            reply(chat_id, "removed" if ok else "no such id")
            continue
        if text.startswith("/list"):
            lines = [f"{e['id']}  {e['caption'][:30]}" for e in items[:10]] or ["empty"]
            reply(chat_id, "\n".join(lines))
            continue

        file_id = pick_file_id(msg)
        if not file_id:
            continue

        ts = datetime.fromtimestamp(msg["date"], tz=timezone.utc)
        entry_id = f"{ts:%Y%m%d-%H%M%S}-{msg['message_id']}"
        if entry_id in known:
            continue

        try:
            w, h = save_variants(download(file_id), entry_id)
        except Exception as e:
            print(f"failed {entry_id}: {e}", file=sys.stderr)
            reply(chat_id, f"failed to process: {e}")
            sys.exit(1)  # non-zero -> workflow stops before ack, retried next run

        items.append({
            "id": entry_id,
            "file": f"gallery/img/{entry_id}.webp",
            "thumb": f"gallery/thumb/{entry_id}.webp",
            "caption": (msg.get("caption") or "").strip()[:CAPTION_MAX],
            "date": ts.isoformat(timespec="seconds"),
            "w": w, "h": h,
        })
        known.add(entry_id)
        changed = True
        reply(chat_id, f"queued {entry_id} - live after next deploy")

    if changed:
        items.sort(key=lambda e: e["date"], reverse=True)
        JSON_PATH.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"ack_offset={max_id + 1}\n")


if __name__ == "__main__":
    main()
