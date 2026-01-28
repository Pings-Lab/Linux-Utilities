#!/usr/bin/env python3
"""
password_ui.py
Single-file FastAPI app (local-only) that serves the Jinja UI and
implements password generation, saving, and optional GPG encryption.

Save HTML as templates/index.html (provided below).
Run: python3 password_ui.py
"""

import os
import json
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn

# ------------------ CONFIG ------------------

APP_NAME = "Secure Pass"
DATA_DIR = Path.home() / ".pingsvaults"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ACCOUNTS_TXT = DATA_DIR / "accounts"
ACCOUNTS_GPG = DATA_DIR / "accounts.gpg"
CONFIG_FILE = DATA_DIR / "config.json"

HOST = "127.0.0.1"
PORT = 8000

# ------------------------------------------------

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Simple per-process CSRF token (suffices for localhost tool)
CSRF_TOKEN = secrets.token_hex(24)
DATA_WRITTEN = False


def has_gpg() -> bool:
    return shutil.which("gpg") is not None


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        cfg = {"gpg_enabled": False, "recipients": []}
        save_config(cfg)
        return cfg
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"gpg_enabled": False, "recipients": []}


def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def list_gpg_recipients() -> List[str]:
    """
    Returns list of human-readable uids for keys present in keyring (emails / uid strings).
    If gpg not available, returns [].
    """
    if not has_gpg():
        return []
    try:
        # Use --with-colons output for easier parsing
        proc = subprocess.run(
            ["gpg", "--list-keys", "--with-colons"],
            capture_output=True,
            text=True,
            check=True,
        )
        recipients = []
        # Parse uid lines. Format: uid:<...>:<...>:<...>:<...>:<uid string>
        for line in proc.stdout.splitlines():
            if line.startswith("uid:"):
                parts = line.split(":")
                uid = parts[9] if len(parts) > 9 else None
                if uid:
                    recipients.append(uid)
        # Deduplicate preserving order
        seen = set()
        out = []
        for r in recipients:
            if r not in seen:
                out.append(r)
                seen.add(r)
        return out
    except Exception:
        return []


def generate_password(length: int) -> str:
    alphabet = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "!@#$%^&*()-_=+"
    )
    return "".join(secrets.choice(alphabet) for _ in range(max(4, int(length))))


def decrypt_if_needed(cfg: dict):
    """
    If a vault exists (accounts.gpg) and config says gpg_enabled and gpg present,
    attempt to decrypt to accounts file. If decrypt fails, keep the encrypted file and
    proceed with plaintext mode (do not delete anything).
    """
    try:
        if cfg.get("gpg_enabled") and ACCOUNTS_GPG.exists() and has_gpg():
            # Decrypt to ACCOUNTS_TXT, suppress informational stderr to keep UI clean
            with open(ACCOUNTS_TXT, "w", encoding="utf-8") as out, open(os.devnull, "w") as devnull:
                subprocess.run(
                    ["gpg", "--quiet", "--batch", "--yes", "--decrypt", str(ACCOUNTS_GPG)],
                    stdout=out,
                    stderr=devnull,
                    check=True,
                )
    except Exception:
        # On decrypt failure, don't delete anything and continue in plaintext mode.
        # Leave ACCOUNTS_GPG as-is. ACCOUNTS_TXT may be missing or stale.
        pass
    finally:
        ACCOUNTS_TXT.touch(exist_ok=True)


def encrypt_if_needed(cfg: dict):
    """
    If new data was written and GPG is enabled and available, encrypt ACCOUNTS_TXT into ACCOUNTS_GPG.
    If encryption fails, leave plaintext file in place for manual review.
    """
    global DATA_WRITTEN
    if not DATA_WRITTEN:
        return
    if cfg.get("gpg_enabled") and has_gpg():
        try:
            # Build recipient args: -r recipient for each
            rec_args: List[str] = []
            for r in cfg.get("recipients", []) or []:
                rec_args.extend(["-r", r])
            # Fall back to symmetric if no recipients given
            if not rec_args:
                # use symmetric encryption if user opted gpg but didn't supply recipients
                cmd = ["gpg", "--quiet", "--batch", "--yes", "--symmetric", str(ACCOUNTS_TXT)]
            else:
                cmd = ["gpg", "--quiet", "--batch", "--yes", "--encrypt", *rec_args, str(ACCOUNTS_TXT)]
            with open(os.devnull, "w") as devnull:
                subprocess.run(cmd, stderr=devnull, check=True)
            # remove plaintext only if encryption succeeded and produced .gpg
            if ACCOUNTS_GPG.exists():
                try:
                    ACCOUNTS_TXT.unlink(missing_ok=True)
                except Exception:
                    pass
        except Exception:
            # encryption failed; keep plaintext for manual recovery
            pass


def read_password_blocks() -> List[str]:
    """
    Read the accounts file and return list of blocks separated by blank line.
    Each block is expected to be two lines:
      line1 = website/label
      line2 = password
    We'll return raw blocks; template will split them.
    """
    if not ACCOUNTS_TXT.exists():
        return []
    try:
        content = ACCOUNTS_TXT.read_text(encoding="utf-8").strip()
        if not content:
            return []
        blocks = [b for b in content.split("\n\n") if b.strip()]
        return blocks
    except Exception:
        return []


# ------------------ FastAPI routes ------------------


@app.on_event("startup")
def startup_event():
    # ensure data dir and base files exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    decrypt_if_needed(cfg)
    ACCOUNTS_TXT.touch(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    cfg = load_config()
    gpg_available = has_gpg()
    gpg_keys = list_gpg_recipients() if gpg_available else []
    pw_blocks = read_password_blocks()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": APP_NAME,
            "csrf_token": CSRF_TOKEN,
            "config": cfg,
            "gpg_available": gpg_available,
            "gpg_keys": gpg_keys,
            "passwords": pw_blocks,
        },
    )


@app.post("/generate")
async def generate(length: int = Form(...), csrf_token: str = Form(...)):
    # CSRF
    if csrf_token != CSRF_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    try:
        pwd = generate_password(int(length))
        return JSONResponse({"password": pwd})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid length")


@app.post("/save")
async def save(website: Optional[str] = Form(""), password: str = Form(...), csrf_token: str = Form(...)):
    global DATA_WRITTEN
    if csrf_token != CSRF_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    # sanitize newlines in website and password
    website_clean = (website or "").strip().splitlines()[0] if website else ""
    password_clean = (password or "").strip().splitlines()[0]
    # append block
    try:
        with open(ACCOUNTS_TXT, "a", encoding="utf-8") as f:
            f.write(website_clean + "\n")
            f.write(password_clean + "\n\n")
        DATA_WRITTEN = True
        cfg = load_config()
        encrypt_if_needed(cfg)
        decrypt_if_needed(cfg)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to write vault file")
    # redirect back to index (Post-Redirect-Get)
    return RedirectResponse("/", status_code=303)


@app.post("/config")
async def update_config(request: Request):
    """
    We parse form manually to support multiple recipients reliably.
    """
    form = await request.form()
    csrf = form.get("csrf_token")
    if csrf != CSRF_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    gpg_enabled = form.get("gpg_enabled") in ("on", "true", "True", "1")
    # gather recipients - form may contain multiple 'recipients'
    recipients = []
    # form is a MultiDict; .getlist exists on starlette UploadFileMultiDict? We try multiple ways
    try:
        # Try starlette approach
        recipients = form.getlist("recipients")
    except Exception:
        # fallback: gather keys
        for k, v in form.multi_items():
            if k == "recipients":
                recipients.append(v)
    # Deduplicate/trim
    recipients = [r.strip() for r in recipients if r and r.strip()]
    cfg = {"gpg_enabled": bool(gpg_enabled), "recipients": recipients}
    save_config(cfg)
    # After changing config, if gpg_enabled is True and accounts.gpg exists and gpg available, try decrypt now
    try:
        decrypt_if_needed(cfg)
    except Exception:
        pass
    return RedirectResponse("/", status_code=303)


@app.on_event("shutdown")
def shutdown_event():
    cfg = load_config()
    encrypt_if_needed(cfg)


# ------------------ entry ------------------

if __name__ == "__main__":
    # Always bind to localhost only
    uvicorn.run(app, host=HOST, port=PORT)
