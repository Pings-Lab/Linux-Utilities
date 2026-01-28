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

Clone the repository: For both CLI and GUI

```bash
git clone git@github.com:Pings-Lab/Linux-Utilities.git
cd password
```

Or just pull one file, if you want to use only CLI tool

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

## For GUI usage
Within the password directory,
run these commands:

```bash
uv sync
uv run python password_ui.py
```

## 👤 Users Section
### 1. What is happening?
- When you enter 'y' and enter website name for example, it will create a text file 'accounts'.
- It will let you generate as many passwords as you want and go on appending website name and password to accounts file.
- When you enter 'q' to quit. It will try to convert 'accounts' file to 'accounts.gpg' using gpg encryption and delete the 'accounts' text file.
- If gpg encryption fails, it won't delete text file so you can view it and use.
- Next time when you use password.py, it will decrypt the existing 'accounts.gpg' file and then appends the new passwords to it.

### 2. How to see my Saved password?

Run the below command. It will ask for your passphrase, after your passphrase your passwords will be listed in terminal.

```bash
gpg -d .pingsvaults/accounts.gpg
```

If you don't setup any gpg, you can view password by printing the text file.

```bash
cat .pingsvaults/accounts
```

### 3. Can I turn off the colors?

You can do more than that.
1. Open the password.py
2. Scroll to the configuration section
3. You can turn on or off the all available properties in configuration section.

### 4. Can I contribute to the project?

You are most welcome.
Not only for this repo, any repo under this organization is open for use and modification

1. Clone the repo
2. Make your changes
3. Create a pull request

### 5. Can I join the Ping's lab organization?

We welcome you with open arms.
Use the Organization website or email to contact us.

- Website: [link](https://pings-lab.github.io)
- Email: thepingslab@gmail.com
