# Secure Pass – Minimal Password Utility for Linux

Secure Pass is a lightweight, dependency-free Linux password generator and vault helper written in **Python**.  
It focuses on strong password generation, smooth CLI interaction, and optional GPG-based encryption without forcing virtual environments or Python package installs.

Designed with a Unix mindset: simple, composable, and safe by default.

---

## ✨ Features

- **Interactive Password Generation**
  - Generate strong random passwords
  - Regenerate instantly without restarting the script
  - Change password length on the fly

- **Clipboard Integration (Optional)**
  - Automatically copies accepted passwords to clipboard
  - Uses native system tools (`wl-copy`, `xclip`, `xsel`)
  - Gracefully skips clipboard if unavailable

- **Secure Storage**
  - Append passwords to a local `accounts` file
  - Optional GPG public-key encryption
  - Existing encrypted vaults are safely decrypted and re-encrypted

- **Fault-Tolerant by Design**
  - Works without GPG (plaintext fallback with warning)
  - Never overwrites or deletes data on failure
  - No encryption prompts if no new passwords are saved

---

## 🧱 Tech Stack

- **Language:** Python 3.10+
- **Crypto:** GPG (public-key encryption)
- **Clipboard:** Native Linux tools (no Python dependencies)
- **Platform:** Linux (tested on Ubuntu, Wayland & X11)

---

## 🚀 Getting Started

### Prerequisites

- Linux system
- Python 3.10+
- GPG (optional, but recommended)

---

### Installation

Clone the repository:

```bash
git clone git@github.com:your-username/vault-spark.git
cd password
```

Or just clone the Script

```bash
curl -fsSL https://raw.githubusercontent.com/Pings-Lab/Linux-Utilities/main/password/password.py -o password.py
python3 password.py
```

### GPG setup and Config in script (Optional but Recommended)

```bash
#First take time and generate key with passphrase (Don't forget the passphrase)
gpg --full-generate-key

#List to see your generated key
gpg --list-keys

#1 copy your key and open password.py
#2 scroll to configuration section and add the value
#3 GPG_RECIPIENT = "your-email@example.com" as listed in gpg --list-keys
#4 All set
```

### Clipboard copy (Optional)
You can enter yes and copy the password and use. Or you can install one of the below dependcies so it will be automatically copied.

```bash
# On Ubuntu
sudo apt install wl-clipboard

# On X11
sudo apt install xclip
```
