"""Supervised hackathon invitation sender (Telethon, personal Telegram account)."""
import argparse
import asyncio
import csv
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, errors

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / '.env', override=False, encoding='utf-8-sig')
DEFAULT_GROUP_LINK = os.environ.get('TG_GROUP_LINK', '').strip()
USER_RE = re.compile(r"^@?[A-Za-z][A-Za-z0-9_]{4,31}$")


def rows_from_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    unique = set()
    result = []
    for row in rows:
        name = (row.get("Full Name") or "").strip()
        username = (row.get("Telegram Username") or "").strip()
        if not name or not USER_RE.fullmatch(username):
            raise ValueError(f"Invalid name or username in input row: {row!r}")
        username = "@" + username.lstrip("@")
        if username.casefold() in unique:
            raise ValueError(f"Duplicate username: {username}")
        unique.add(username.casefold())
        result.append((name, username))
    return result


def message(name, link):
    first = name.split()[0]
    return (f"Hello {first},\n\n"
            "Congratulations! You have been shortlisted to participate in the "
            "**Vision Vertex × ISHUB AI Agent Hackathon 2026**.\n\n"
            "**Event Details**\n\n"
            "- **Date:** Saturday, October 24, 2026\n"
            "- **Arrival Time:** 8:00 AM\n\n"
            "**To confirm your participation, please complete the following steps:**\n\n"
            "1. Join our official Telegram group using the link below.\n"
            "2. Once you join, send a message in the group stating your "
            "**full name as registered in your application**.\n\n"
            f"**Telegram Group:**\n{link}\n\n"
            "Your participation will be considered confirmed once you have joined the group "
            "and submitted your full name.\n\n"
            "**What to bring:**\n\n"
            "- Laptop and charger\n"
            "- Valid Addis Ababa University student ID\n\n"
            "We look forward to welcoming you and seeing what you can build.\n\n"
            "Best regards,\n\n"
            "**Amanuel Tefera**\n"
            "Head of Marketing\n"
            "**Vision Vertex × ISHUB Hackathon 2026**")


def load_sent(logfile):
    if not logfile.exists():
        return set()
    with logfile.open(encoding="utf-8", newline="") as f:
        return {r['username'].casefold() for r in csv.DictReader(f) if r['status'] == 'sent'}


def append_log(logfile, row):
    exists = logfile.exists() and logfile.stat().st_size > 0
    with logfile.open('a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['utc_timestamp','name','username','status','details'])
        if not exists: writer.writeheader()
        writer.writerow(row)


async def main():
    parser = argparse.ArgumentParser(description="Preview/send personalized Telegram invitations")
    parser.add_argument('--csv', type=Path, default=HERE / 'participants.csv')
    parser.add_argument('--group-link', default=DEFAULT_GROUP_LINK, help="Telegram group invite URL (defaults to TG_GROUP_LINK in .env)")
    parser.add_argument('--poster', type=Path, help="Optional poster JPG or PNG")
    parser.add_argument('--send', action='store_true', help="Actually send messages (default: preview only)")
    parser.add_argument('--limit', type=int, default=5, help="Maximum contacts per run in send mode; default 5")
    parser.add_argument('--delay', type=float, default=25, help="Seconds between attempts, default 25")
    parser.add_argument('--log', type=Path, default=HERE / 'invitation_log.csv')
    args = parser.parse_args()
    if args.limit < 1 or args.delay < 0: parser.error('Limit must be positive and delay nonnegative')
    if not (args.group_link.startswith('https://t.me/') or args.group_link.startswith('https://telegram.me/')):
        parser.error('Set TG_GROUP_LINK in .env or pass --group-link with a Telegram invite URL beginning with https://t.me/')
    if args.poster and not args.poster.is_file(): parser.error('Poster file not found')
    participants = rows_from_csv(args.csv)
    already_sent = load_sent(args.log)
    pending = [(n,u) for n,u in participants if u.casefold() not in already_sent]
    print(f"Loaded {len(participants)} people, already sent: {len(participants)-len(pending)}; remaining: {len(pending)}")
    print("\nSAMPLE MESSAGE:\n" + message(pending[0][0],args.group_link) if pending else 'All recorded as sent.')
    if not args.send:
        print('\nPREVIEW ONLY. Nothing was sent. Add --send when ready.');return
    if not pending: return
    print(f"\nSEND MODE: Will attempt at most {min(args.limit, len(pending))} messages. Telegram may refuse unsolicited DMs.")
    confirmation = input('Type SEND to confirm: ').strip()
    if confirmation != 'SEND': print('Cancelled.');return
    api_id = os.environ.get('TG_API_ID', '').strip()
    api_hash = os.environ.get('TG_API_HASH', '').strip()
    if not api_id or not api_hash:
        raise SystemExit('Set TG_API_ID and TG_API_HASH in the .env file next to invite.py or in your environment.')
    try:
        api_id = int(api_id)
    except ValueError:
        raise SystemExit('TG_API_ID must be a positive number. Check your .env file or environment.') from None
    if api_id < 1:
        raise SystemExit('TG_API_ID must be a positive number. Check your .env file or environment.')
    async with TelegramClient(str(HERE / 'organizer_session'), api_id, api_hash) as client:
        for index,(name,username) in enumerate(pending[:args.limit]):
            try:
                entity = await client.get_entity(username)
                text = message(name,args.group_link)
                if args.poster:
                    await client.send_file(entity,str(args.poster),caption=text)
                else:
                    await client.send_message(entity,text,link_preview=False)
                status,details='sent','Telegram accepted the message; delivery/read/participation not confirmed'
            except errors.FloodWaitError as exc:
                print(f'Rate limit: Telegram requested a wait of {exc.seconds} seconds. Stopping this run.');break
            except (errors.PeerFloodError, errors.UserPrivacyRestrictedError, errors.ChatWriteForbiddenError) as exc:
                status,details='failed',type(exc).__name__
                if isinstance(exc,errors.PeerFloodError):
                    append_log(args.log,{'utc_timestamp':datetime.now(timezone.utc).isoformat(),'name':name,'username':username,'status':status,'details':details})
                    print('Telegram restricted messaging. Stop and use manual/group-based invitations.');break
            except Exception as exc:
                status,details='failed',type(exc).__name__
            append_log(args.log,{'utc_timestamp':datetime.now(timezone.utc).isoformat(),'name':name,'username':username,'status':status,'details':details})
            print(f'{index+1}: {username} - {status} ({details})')
            if index < min(args.limit,len(pending))-1:
                await asyncio.sleep(args.delay)
    print(f'Log saved to {args.log}. A sent status does NOT prove the student received or accepted the invitation.')


if __name__ == '__main__':
    asyncio.run(main())
