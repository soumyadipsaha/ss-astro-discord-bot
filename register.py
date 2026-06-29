import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.commands import COMMANDS


def main():
    token = os.environ.get("DISCORD_TOKEN")
    app_id = os.environ.get("DISCORD_APP_ID")
    if not token or not app_id:
        raise SystemExit("DISCORD_TOKEN and DISCORD_APP_ID must be set.")

    url = f"https://discord.com/api/v10/applications/{app_id}/commands"
    with httpx.Client(timeout=30) as client:
        r = client.put(url, json=COMMANDS, headers={"Authorization": f"Bot {token}"})
    print(f"Status: {r.status_code}")
    print(r.text)
    if r.is_success:
        for cmd in r.json():
            print(f"  registered /{cmd['name']} (id {cmd['id']})")


if __name__ == "__main__":
    main()
