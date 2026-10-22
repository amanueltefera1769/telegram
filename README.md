# Vision Vertex × ISHUB — Telegram invitation sender

This sends from **your personal Telegram account**, not a Telegram Bot API bot. Telegram bots cannot start private chats with people who have never started them.

## Setup
1. Install Python 3.10+ and open a terminal in this folder.
2. Create a virtual environment and install the requirements. In PowerShell:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
   If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` instead of `python` in the commands below. On macOS/Linux, use `python3 -m venv .venv` and `source .venv/bin/activate`.
3. Get your own API ID and API hash from https://my.telegram.org/apps . Keep them private.
4. Copy `.env.example` to `.env` next to `invite.py` and fill in your credentials and group link:
   ```dotenv
   TG_API_ID=YOUR_API_ID
   TG_API_HASH=YOUR_API_HASH
   TG_GROUP_LINK=https://t.me/YOUR_GROUP_INVITE
   ```
   The script loads this file automatically, even if launched from another folder. Existing environment variables take priority; remove old variables if you want to use the file instead. Keep `.env` private: it is excluded by `.gitignore`, but still included if you manually share the entire folder. Do not paste credentials into `invite.py`. You can override the group link for one run with `--group-link`.
5. Copy `participants.example.csv` to `participants.csv`. Add your own recipients under the exact `Full Name,Telegram Username` headers. The template is empty; no real participant data is included in Git.
6. Review the invitation text, event details, and signature in the `message()` function in `invite.py`. They currently describe the Vision Vertex × ISHUB event on October 24, 2026. Prefer **Request Admin Approval** in Telegram group settings.
7. Optional: save your invitation graphic as `poster.jpg` next to the script.

## Preview safely
`python invite.py`

## Test one invitation to yourself FIRST
Edit a copy of `participants.csv` containing only your own Telegram username, and run:
`python invite.py --csv test.csv --send --limit 1` (add `--poster poster.jpg` only if you have added the image)

When you are ready, try a small group of people who have agreed to receive the invitation:
`python invite.py --send --limit 5` (add `--poster poster.jpg` if available)

The script requests confirmation, then on first send Telethon will prompt for Telegram login (phone, code, possibly 2FA). Do not share any login codes or the `organizer_session.session` file. That session grants Telegram account access. Run locally, not on a shared/public computer.

It saves `invitation_log.csv` and skips usernames previously marked sent when rerun. Failed contacts may be retried individually only after addressing the failure; don't repeatedly reattempt restricted recipients. Telegram may restrict unsolicited bulk messages. The delay is operational pacing, **not a guarantee against Telegram limits**. Do not attempt to bypass Telegram restrictions.

## Sharing the code
Each person must configure their own `.env`, recipient list, and Telegram login. Git excludes `.env`, Telegram session files, local virtual environments, and all CSV files except the empty `participants.example.csv` template. Share the repository rather than zipping the working folder, which contains private local files. Keep your invitation log when continuing an existing run so sent recipients are skipped.

**Important:** Sent means Telegram accepted the outgoing message, **not** that the student read it, joined, or confirmed attendance. Confirm the student's name against the spreadsheet and verify AAU ID on-site. With admin approval enabled, only approve verified join requests.
