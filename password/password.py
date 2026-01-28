import os
import sys
import pathlib
import subprocess
import secrets
import string
import shutil
from pathlib import Path
# --------------------------------
import colorsys

def logo(lines, start_hsl, end_hsl):
    h1, s1, l1 = start_hsl[0]/360, start_hsl[1]/100, start_hsl[2]/100
    h2, s2, l2 = end_hsl[0]/360, end_hsl[1]/100, end_hsl[2]/100
    rgb_start = colorsys.hls_to_rgb(h1, l1, s1)
    rgb_end = colorsys.hls_to_rgb(h2, l2, s2)

    for row, line in enumerate(lines):
        for col, char in enumerate(line):
            fraction = (row / 20 + col / 40) % 1.0
            r = int((rgb_start[0] + (rgb_end[0] - rgb_start[0]) * fraction) * 255)
            g = int((rgb_start[1] + (rgb_end[1] - rgb_start[1]) * fraction) * 255)
            b = int((rgb_start[2] + (rgb_end[2] - rgb_start[2]) * fraction) * 255)
            print(f"\033[38;2;{r};{g};{b}m{char}", end="")
        print("\033[0m")

name = [
    "---*---*---*---*---*---*---*---*---",
    "     Ping's Lab: Secure Pass     ",
    "---*---*---*---*---*---*---*---*---"
]

logo(name, (187, 94, 43), (262, 83, 58))

# ---------- USER CONFIG ----------

ENABLE_GPG = True                  # True = encrypt, False = plaintext only
GPG_RECIPIENT = "pradeepubuntu@victus"  # must exist in: gpg --list-keys
ALLOW_PLAINTEXT_FALLBACK = True

DATA_DIR = Path.home() / ".pingsvaults"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ACCOUNTS_TXT = DATA_DIR / "accounts"
ACCOUNTS_GPG = DATA_DIR / "accounts.gpg"
CONFIG_FILE = DATA_DIR / "config.json"
USE_COLORS = True
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
            "--quiet",
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
            "--quiet",
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

class COLORS:
  if USE_COLORS == True:
   MENU1, MENU2, OUT1, OUT2, ALERT1, ALERT2, ALERT3, ALERT4, WEB = '\033[38;5;182m','\033[38;5;183m', '\033[38;5;184m', '\033[38;5;84m', '\033[38;5;1m', '\033[38;5;178m', '\033[38;5;245m', '\033[38;5;99m', '\033[38;5;123m'
  else:
   MENU1= MENU2= OUT1= OUT2= ALERT1= ALERT2= ALERT3= ALERT4= WEB = '\033[0m'

  END = '\033[0m'

# ---------- password logic ----------

def generate_password(length):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+=-"
    return "".join(secrets.choice(alphabet) for _ in range(length))

# ---------- startup ----------

gpg_available = has_gpg()

if not ENABLE_GPG:
    plaintext_mode = True

if ENABLE_GPG and not gpg_available:
    print(f"{COLORS.ALERT2}[!] gpg not found, switching to plaintext mode{COLORS.END}")
    plaintext_mode = True

if ENABLE_GPG and gpg_available and os.path.exists(ACCOUNTS_GPG):
    try:
        decrypt_accounts()
        print(f"{COLORS.ALERT4}[+] Decrypted existing accounts.gpg{COLORS.END}")
    except Exception:
        print(f"{COLORS.ALERT1}[!] Failed to decrypt accounts.gpg, manual check required{COLORS.END}")
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

    print(f"\n{COLORS.OUT1}Generated password [{last_length} chars]:\n{COLORS.OUT2}{pwd}{COLORS.END}")

    choice = input(
        f"\n{COLORS.MENU2}[n]{COLORS.MENU1} new | {COLORS.MENU2}[number] {COLORS.MENU1}new length | {COLORS.MENU2}[y] {COLORS.MENU1}accept | {COLORS.MENU2}[q] {COLORS.MENU1}quit {COLORS.END}: "
    ).strip()

    if choice.lower() == "n":
        continue

    if choice.isdigit():
        last_length = int(choice)
        continue

    if choice.lower() == "y":
        copied = copy_clipboard(pwd)
        if copied:
            print(f"{COLORS.ALERT4}[+] Password copied to clipboard{COLORS.END}")
        else:
            print(f"{COLORS.ALERT3}[!] Clipboard not available{COLORS.END}")

        site = input(f"{COLORS.WEB}Website (optional): {COLORS.END}").strip()

        with open(ACCOUNTS_TXT, "a") as f:
            f.write(site + "\n")
            f.write(pwd + "\n\n")

        data_written = True
        print(f"{COLORS.ALERT4}[+] Saved{COLORS.END}")
        continue

    if choice.lower() == "q":
        break

# ---------- shutdown ----------

if not data_written:
    print(f"{COLORS.ALERT3}[*] No new passwords added, skipping encryption{COLORS.END}")
    sys.exit(0)

if ENABLE_GPG and not plaintext_mode:
    try:
        encrypt_accounts()
        print(f"{COLORS.ALERT4}[+] accounts encrypted to accounts.gpg{COLORS.END}")
    except Exception:
        print(f"{COLORS.ALERT1}[!] gpg failed, plaintext accounts left for manual check{COLORS.END}")
else:
    print(f"{COLORS.ALERT2}[!] Enable gpg to protect your passwords{COLORS.END}")
