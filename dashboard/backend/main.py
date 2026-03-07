"""
Yamaguchi Dashboard — FastAPI backend
Provides:
  GET  /api/health          health check
  GET  /api/tasks           snapshot of all sections (JSON)
  GET  /api/tasks/stream    real-time SSE stream
  --- Mail management ---
  GET  /api/mail/accounts                    list configured accounts
  GET  /api/mail/{account}/inbox             inbox messages
  GET  /api/mail/{account}/sent              sent messages
  GET  /api/mail/{account}/message/{uid}     single message detail
  POST /api/mail/{account}/send              send email
  POST /api/mail/{account}/delete            delete messages
  POST /api/mail/{account}/mark-read         mark messages as read
  GET  /api/mail/{account}/attachment/{uid}/{part}  download attachment

Data model:
  sections[]
    └── task_groups[]
          └── batches[] | events[]
"""

import asyncio
import datetime
import email
import email.header
import email.mime.application
import email.mime.multipart
import email.mime.text
import email.utils
import imaplib
import json
import logging
import os
import smtplib
import time
from email.header import decode_header
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger("dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="Yamaguchi Dashboard API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Configuration (from environment variables)
# ---------------------------------------------------------------------------

DATAAPP_API_URL = os.getenv("DATAAPP_API_URL", "http://localhost:8000")
DATAAPP_SERVICE_TOKEN = os.getenv("DATAAPP_SERVICE_TOKEN", "")
WEBAPP_API_URL = os.getenv("WEBAPP_API_URL", "http://localhost:8001")
WEBAPP_SERVICE_TOKEN = os.getenv("WEBAPP_SERVICE_TOKEN", "")
FETCH_INTERVAL_S = int(os.getenv("FETCH_INTERVAL_S", "30"))
FETCH_TIMEOUT_S = int(os.getenv("FETCH_TIMEOUT_S", "10"))
TIME_WINDOW_DAYS = int(os.getenv("TIME_WINDOW_DAYS", "2"))

# Mail configuration
XSERVER_MAIL_HOST = os.getenv("XSERVER_MAIL_HOST", "sv16698.xserver.jp")
MAIL_ACCOUNTS_JSON = os.getenv("MAIL_ACCOUNTS", "[]")

try:
    MAIL_ACCOUNTS: list[dict] = json.loads(MAIL_ACCOUNTS_JSON)
except json.JSONDecodeError:
    logger.error("Invalid MAIL_ACCOUNTS JSON, using empty list")
    MAIL_ACCOUNTS = []

# Build a lookup dict: key -> account config
_ACCOUNT_MAP: dict[str, dict] = {a["key"]: a for a in MAIL_ACCOUNTS}

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_cache: dict = {
    "sections": [],
    "timestamp": 0.0,
    "stale": False,
}
_lock = asyncio.Lock()

# ---------------------------------------------------------------------------
# Downstream API fetchers
# ---------------------------------------------------------------------------


async def _fetch_json(url: str, token: str, auth_scheme: str = "Token") -> list | dict | None:
    """Fetch JSON from a downstream API endpoint. Returns None on failure."""
    try:
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT_S) as client:
            r = await client.get(
                url,
                headers={"Authorization": f"{auth_scheme} {token}"},
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Section builders — transform downstream API responses into dashboard format
# ---------------------------------------------------------------------------


def _build_nextcloud_section(data: list | None) -> dict:
    """
    data: [{model_name, events: [{id, direction, timestamp, ...}]}]
    """
    task_groups = []
    if data:
        for group in data:
            model_name = group.get("model_name", "unknown")
            task_groups.append({
                "id": f"SYNC_{model_name.upper()}",
                "label": model_name,
                "pipeline": "nextcloud",
                "events": group.get("events", []),
            })
    return {
        "id": "nextcloud_sync",
        "label": "Nextcloud 数据同步",
        "task_groups": task_groups,
    }


def _build_webapp_section(data: list | None) -> dict:
    """
    data: [{source_name, events: [{id, source_name, timestamp, ...}]}]
    """
    task_groups = []
    if data:
        for group in data:
            source_name = group.get("source_name", "unknown")
            task_groups.append({
                "id": f"WEBAPP_{source_name.upper()}",
                "label": source_name,
                "pipeline": "webapp",
                "events": group.get("events", []),
            })
    return {
        "id": "webapp_scraper",
        "label": "价格抓取（Webapp）",
        "task_groups": task_groups,
    }


def _build_tracking_section(data: list | None, *, source_type: str) -> dict:
    """
    data: [{task_name, source_type, label, batches: [...]}]
    Filter by source_type ('excel' or 'db').
    """
    task_groups = []
    if data:
        for group in data:
            if group.get("source_type") != source_type:
                continue
            task_name = group.get("task_name", "unknown")
            task_groups.append({
                "id": task_name.upper(),
                "label": group.get("label", task_name),
                "pipeline": source_type,
                "batches": group.get("batches", []),
            })

    if source_type == "excel":
        return {
            "id": "excel_tracking",
            "label": "追踪任务（Excel 驱动）",
            "task_groups": task_groups,
        }
    else:
        return {
            "id": "db_tracking",
            "label": "追踪任务（DB 驱动）",
            "task_groups": task_groups,
        }


def _build_email_section(data: list | None) -> dict:
    """
    data: [{stage, label, batches: [{id, created_at, ...}]}]
    """
    task_groups = []
    if data:
        for group in data:
            stage = group.get("stage", "unknown")
            task_groups.append({
                "id": f"EMAIL_{stage.upper()}",
                "label": group.get("label", stage),
                "pipeline": "email",
                "batches": group.get("batches", []),
            })
    return {
        "id": "email",
        "label": "邮件处理",
        "task_groups": task_groups,
    }


# ---------------------------------------------------------------------------
# Refresh loop — pulls data from downstream APIs every FETCH_INTERVAL_S
# ---------------------------------------------------------------------------


async def _refresh_sections():
    """Fetch from all downstream APIs and rebuild the cached sections."""
    async with _lock:
        days = f"?days={TIME_WINDOW_DAYS}"

        nextcloud, tracking, email, scraper = await asyncio.gather(
            _fetch_json(
                f"{DATAAPP_API_URL}/api/acquisition/dashboard/nextcloud-sync/{days}",
                DATAAPP_SERVICE_TOKEN,
                auth_scheme="Bearer",
            ),
            _fetch_json(
                f"{DATAAPP_API_URL}/api/acquisition/dashboard/tracking-batches/{days}",
                DATAAPP_SERVICE_TOKEN,
                auth_scheme="Bearer",
            ),
            _fetch_json(
                f"{DATAAPP_API_URL}/api/aggregation/dashboard/email-tasks/{days}",
                DATAAPP_SERVICE_TOKEN,
                auth_scheme="Bearer",
            ),
            _fetch_json(
                f"{WEBAPP_API_URL}/api/dashboard/scraper-events/{days}",
                WEBAPP_SERVICE_TOKEN,
                auth_scheme="Token",
            ),
        )

        sections = [
            _build_nextcloud_section(nextcloud),
            _build_webapp_section(scraper),
            _build_tracking_section(tracking, source_type="excel"),
            _build_tracking_section(tracking, source_type="db"),
            _build_email_section(email),
        ]

        _cache["sections"] = sections
        _cache["timestamp"] = time.time()
        _cache["stale"] = any(x is None for x in [nextcloud, tracking, email, scraper])

        if _cache["stale"]:
            failed = []
            if nextcloud is None:
                failed.append("nextcloud")
            if tracking is None:
                failed.append("tracking")
            if email is None:
                failed.append("email")
            if scraper is None:
                failed.append("scraper")
            logger.warning("Stale data — failed to fetch: %s", ", ".join(failed))
        else:
            logger.info("Refreshed all sections successfully")


def _snapshot() -> dict:
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "sections": _cache.get("sections", []),
        "stale": _cache.get("stale", False),
    }


# ---------------------------------------------------------------------------
# Startup — background refresh loop
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def start_refresh_loop():
    async def loop():
        while True:
            try:
                await _refresh_sections()
            except Exception:
                logger.exception("Refresh loop error")
            await asyncio.sleep(FETCH_INTERVAL_S)

    asyncio.create_task(loop())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}


@app.get("/api/tasks")
def get_tasks():
    return _snapshot()


@app.get("/api/tasks/stream")
async def stream_tasks():
    """Server-Sent Events — pushes sections snapshot every 10 seconds."""

    async def event_generator():
        while True:
            payload = json.dumps(_snapshot(), ensure_ascii=False)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(10)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# Mail helpers
# ---------------------------------------------------------------------------


def _get_account(account: str) -> dict:
    """Resolve account key to config dict, or raise 404."""
    acct = _ACCOUNT_MAP.get(account)
    if not acct:
        raise HTTPException(status_code=404, detail=f"Unknown account: {account}")
    return acct


def _decode_header_value(raw: str | None) -> str:
    """Decode an RFC 2047 encoded header into a plain string."""
    if not raw:
        return ""
    parts = decode_header(raw)
    result = []
    for data, charset in parts:
        if isinstance(data, bytes):
            result.append(data.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(data)
    return "".join(result)


def _parse_envelope(msg: email.message.Message, uid: str) -> dict:
    """Extract envelope-level info for the mail list view."""
    subject = _decode_header_value(msg.get("Subject"))
    from_addr = _decode_header_value(msg.get("From"))
    to_addr = _decode_header_value(msg.get("To"))
    date_str = msg.get("Date", "")
    date_parsed = email.utils.parsedate_to_datetime(date_str).isoformat() if date_str else ""

    has_attachment = False
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                has_attachment = True
                break

    return {
        "uid": uid,
        "subject": subject,
        "from": from_addr,
        "to": to_addr,
        "date": date_parsed,
        "has_attachment": has_attachment,
    }


def _parse_message_detail(msg: email.message.Message, uid: str) -> dict:
    """Full message parse including body and attachment list."""
    envelope = _parse_envelope(msg, uid)
    cc = _decode_header_value(msg.get("Cc"))

    body_text = ""
    body_html = ""
    attachments = []
    part_index = 0

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()

            if disposition == "attachment":
                filename = part.get_filename()
                if filename:
                    filename = _decode_header_value(filename)
                attachments.append({
                    "part": part_index,
                    "filename": filename or f"attachment_{part_index}",
                    "content_type": content_type,
                    "size": len(part.get_payload(decode=True) or b""),
                })
            elif content_type == "text/plain" and not body_text:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                body_text = payload.decode(charset, errors="replace") if payload else ""
            elif content_type == "text/html" and not body_html:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                body_html = payload.decode(charset, errors="replace") if payload else ""

            part_index += 1
    else:
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or "utf-8"
        if msg.get_content_type() == "text/html":
            body_html = payload.decode(charset, errors="replace") if payload else ""
        else:
            body_text = payload.decode(charset, errors="replace") if payload else ""

    return {
        **envelope,
        "cc": cc,
        "body_text": body_text,
        "body_html": body_html,
        "attachments": attachments,
    }


def _imap_connect(acct: dict) -> imaplib.IMAP4_SSL:
    """Create and authenticate an IMAP4_SSL connection."""
    conn = imaplib.IMAP4_SSL(XSERVER_MAIL_HOST, 993)
    conn.login(acct["address"], acct["password"])
    return conn


def _fetch_mail_list(
    acct: dict, folder: str = "INBOX", page: int = 1, per_page: int = 20
) -> dict:
    """Fetch paginated mail list from an IMAP folder."""
    conn = _imap_connect(acct)
    try:
        status, _ = conn.select(folder, readonly=True)
        if status != "OK":
            return {"messages": [], "total": 0, "page": page, "per_page": per_page}

        _, data = conn.search(None, "ALL")
        all_uids = data[0].split() if data[0] else []
        all_uids.reverse()  # newest first

        total = len(all_uids)
        start = (page - 1) * per_page
        page_uids = all_uids[start : start + per_page]

        messages = []
        for uid_bytes in page_uids:
            uid = uid_bytes.decode()
            _, msg_data = conn.fetch(uid_bytes, "(RFC822.HEADER FLAGS)")
            if msg_data and msg_data[0] and isinstance(msg_data[0], tuple):
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                envelope = _parse_envelope(msg, uid)
                # Check \Seen flag
                flags_line = msg_data[0][0].decode() if msg_data[0][0] else ""
                envelope["seen"] = "\\Seen" in flags_line
                messages.append(envelope)

        return {"messages": messages, "total": total, "page": page, "per_page": per_page}
    finally:
        conn.logout()


def _fetch_single_message(acct: dict, uid: str, folder: str = "INBOX") -> dict:
    """Fetch a single full message by UID (sequence number)."""
    conn = _imap_connect(acct)
    try:
        conn.select(folder, readonly=False)
        _, msg_data = conn.fetch(uid.encode(), "(RFC822)")
        if not msg_data or not msg_data[0] or not isinstance(msg_data[0], tuple):
            raise HTTPException(status_code=404, detail="Message not found")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        # Mark as seen
        conn.store(uid.encode(), "+FLAGS", "\\Seen")
        return _parse_message_detail(msg, uid)
    finally:
        conn.logout()


def _fetch_attachment(acct: dict, uid: str, part_idx: int, folder: str = "INBOX") -> tuple:
    """Fetch a specific attachment. Returns (filename, content_type, data)."""
    conn = _imap_connect(acct)
    try:
        conn.select(folder, readonly=True)
        _, msg_data = conn.fetch(uid.encode(), "(RFC822)")
        if not msg_data or not msg_data[0] or not isinstance(msg_data[0], tuple):
            raise HTTPException(status_code=404, detail="Message not found")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        current_idx = 0
        for part in msg.walk():
            if current_idx == part_idx and part.get_content_disposition() == "attachment":
                filename = _decode_header_value(part.get_filename()) or f"attachment_{part_idx}"
                content_type = part.get_content_type()
                data = part.get_payload(decode=True) or b""
                return filename, content_type, data
            current_idx += 1

        raise HTTPException(status_code=404, detail="Attachment not found")
    finally:
        conn.logout()


def _send_mail(
    acct: dict,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
):
    """Send an email via SMTP over SSL."""
    msg = email.mime.multipart.MIMEMultipart()
    msg["From"] = acct["address"]
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=True)

    msg.attach(email.mime.text.MIMEText(body, "plain", "utf-8"))

    if attachments:
        for filename, data, content_type in attachments:
            part = email.mime.application.MIMEApplication(data, Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            msg.attach(part)

    with smtplib.SMTP_SSL(XSERVER_MAIL_HOST, 465) as smtp:
        smtp.login(acct["address"], acct["password"])
        recipients = to + (cc or [])
        smtp.sendmail(acct["address"], recipients, msg.as_string())


# ---------------------------------------------------------------------------
# Mail API routes
# ---------------------------------------------------------------------------


@app.get("/api/mail/accounts")
def list_mail_accounts():
    """Return the list of configured mail accounts (without passwords)."""
    return [
        {"key": a["key"], "address": a["address"]}
        for a in MAIL_ACCOUNTS
    ]


@app.get("/api/mail/{account}/inbox")
async def get_inbox(
    account: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    acct = _get_account(account)
    return await asyncio.to_thread(_fetch_mail_list, acct, "INBOX", page, per_page)


@app.get("/api/mail/{account}/sent")
async def get_sent(
    account: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    acct = _get_account(account)
    # Xserver commonly uses "Sent" or "INBOX.Sent"
    for folder_name in ("Sent", "INBOX.Sent", "sent"):
        try:
            result = await asyncio.to_thread(
                _fetch_mail_list, acct, folder_name, page, per_page
            )
            return result
        except Exception:
            continue
    return {"messages": [], "total": 0, "page": page, "per_page": per_page}


@app.get("/api/mail/{account}/message/{uid}")
async def get_message(
    account: str,
    uid: str,
    folder: str = Query("INBOX"),
):
    acct = _get_account(account)
    return await asyncio.to_thread(_fetch_single_message, acct, uid, folder)


@app.get("/api/mail/{account}/attachment/{uid}/{part}")
async def get_attachment(account: str, uid: str, part: int):
    acct = _get_account(account)
    filename, content_type, data = await asyncio.to_thread(
        _fetch_attachment, acct, uid, part
    )
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class MailSendRequest(BaseModel):
    to: list[str]
    subject: str
    body: str
    cc: Optional[list[str]] = None


@app.post("/api/mail/{account}/send")
async def send_mail(account: str, req: MailSendRequest):
    acct = _get_account(account)
    await asyncio.to_thread(
        _send_mail, acct, req.to, req.subject, req.body, req.cc
    )
    return {"status": "sent"}


class MailUidsRequest(BaseModel):
    uids: list[str]
    folder: str = "INBOX"


@app.post("/api/mail/{account}/delete")
async def delete_mail(account: str, req: MailUidsRequest):
    acct = _get_account(account)

    def _do_delete():
        conn = _imap_connect(acct)
        try:
            conn.select(req.folder)
            for uid in req.uids:
                conn.store(uid.encode(), "+FLAGS", "\\Deleted")
            conn.expunge()
        finally:
            conn.logout()

    await asyncio.to_thread(_do_delete)
    return {"status": "deleted", "count": len(req.uids)}


@app.post("/api/mail/{account}/mark-read")
async def mark_read(account: str, req: MailUidsRequest):
    acct = _get_account(account)

    def _do_mark():
        conn = _imap_connect(acct)
        try:
            conn.select(req.folder)
            for uid in req.uids:
                conn.store(uid.encode(), "+FLAGS", "\\Seen")
        finally:
            conn.logout()

    await asyncio.to_thread(_do_mark)
    return {"status": "marked", "count": len(req.uids)}
