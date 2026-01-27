import os
import sys
import pathlib
import subprocess
import secrets
import string
import shutil

# ---------- USER CONFIG ----------

ENABLE_GPG = True                  # True = encrypt, False = plaintext only
GPG_RECIPIENT = "pingslab@linux"  # must exist in: gpg --list-keys
ALLOW_PLAINTEXT_FALLBACK = True

ACCOUNTS_TXT = "accounts"
ACCOUNTS_GPG = "accounts.gpg"

# ---------- internal state ----------

data_written = False
plaintext_mode = False

# ---------- utilities ----------

def has_gpg():
    return shutil.which("gpg") is not None

def decrypt_accounts():
    subprocess.run(
        [
            "gpg",
            "--yes",
            "--batch",
            "--decrypt",
            ACCOUNTS_GPG,
        ],
        stdout=open(ACCOUNTS_TXT, "w"),
        check=True
    )

def encrypt_accounts():
    subprocess.run(
        [
            "gpg",
            "--yes",
            "--batch",
            "--encrypt",
            "--recipient",
            GPG_RECIPIENT,
            ACCOUNTS_TXT,
        ],
        check=True
    )
    os.remove(ACCOUNTS_TXT)

def copy_clipboard(text):
    if shutil.which("wl-copy"):
        subprocess.run(
            ["wl-copy"],
            input=text.encode(),
            check=True
        )
        return "wl-copy"
    if shutil.which("xclip"):
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode(),
            check=True
        )
        return "xclip"
    if shutil.which("xsel"):
        subprocess.run(
            ["xsel", "--clipboard", "--input"],
            input=text.encode(),
            check=True
        )
        return "xsel"
    return None

# ---------- password logic ----------

def generate_password(length):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+=-"
    return "".join(secrets.choice(alphabet) for _ in range(length))

# ---------- startup ----------

gpg_available = has_gpg()

if not ENABLE_GPG:
    plaintext_mode = True

if ENABLE_GPG and not gpg_available:
    print("[!] gpg not found, switching to plaintext mode")
    plaintext_mode = True

if ENABLE_GPG and gpg_available and os.path.exists(ACCOUNTS_GPG):
    try:
        decrypt_accounts()
        print("[+] Decrypted existing accounts.gpg")
    except Exception:
        print("[!] Failed to decrypt accounts.gpg, manual check required")
        if ALLOW_PLAINTEXT_FALLBACK:
            plaintext_mode = True
        else:
            sys.exit(1)
else:
    pathlib.Path(ACCOUNTS_TXT).touch(exist_ok=True)

# ---------- interactive loop ----------

last_length = None

while True:
    if last_length:
        pwd = generate_password(last_length)
    else:
        last_length = secrets.choice(range(12, 21))
        pwd = generate_password(last_length)

    print(f"\nGenerated password ({last_length} chars):\n{pwd}")

    choice = input(
        "\n[n] new | [number] new length | [y] accept | [q] quit : "
    ).strip()

    if choice.lower() == "n":
        continue

    if choice.isdigit():
        last_length = int(choice)
        continue

    if choice.lower() == "y":
        copied = copy_clipboard(pwd)
        if copied:
            print("[+] Password copied to clipboard")
        else:
            print("[!] Clipboard not available")

        site = input("Website (optional): ").strip()

        with open(ACCOUNTS_TXT, "a") as f:
            f.write(site + "\n")
            f.write(pwd + "\n\n")

        data_written = True
        print("[+] Saved")
        continue

    if choice.lower() == "q":
        break

# ---------- shutdown ----------

if not data_written:
    print("[*] No new passwords added, skipping encryption")
    sys.exit(0)

if ENABLE_GPG and not plaintext_mode:
    try:
        encrypt_accounts()
        print("[+] accounts encrypted to accounts.gpg")
    except Exception:
        print("[!] gpg failed, plaintext accounts left for manual check")
else:
    print("[!] Enable gpg to protect your passwords")
