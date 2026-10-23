#!/bin/bash
# Renew the Google Calendar refresh token and store it everywhere it's used:
#   - AWS SSM /booking/google_refresh_token (booking Lambda)
#   - GitHub secret GOOGLE_REFRESH_TOKEN (Sync Calendar Availability workflow)
# The token is never printed. Reads client id/secret from SECRETS.md.
set -euo pipefail
cd "$(dirname "$0")/.."

export GOOGLE_CLIENT_ID=$(grep -o '[0-9]*-[a-z0-9]*\.apps\.googleusercontent\.com' SECRETS.md | head -1)
export GOOGLE_CLIENT_SECRET=$(grep -o 'GOCSPX-[A-Za-z0-9_-]*' SECRETS.md | head -1)

TOKEN=$(.venv/bin/python - <<'EOF'
import os
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_config(
    {"installed": {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }},
    scopes=["https://www.googleapis.com/auth/calendar.events"],
)
import sys
# The flow prints its sign-in prompt to stdout; send that to stderr so only
# the token ends up in $TOKEN.
real_stdout, sys.stdout = sys.stdout, sys.stderr
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent",
                              open_browser=True)
sys.stdout = real_stdout
print(creds.refresh_token or "")
EOF
)

[ -n "$TOKEN" ] || { echo "No refresh token returned"; exit 1; }

aws ssm put-parameter --name /booking/google_refresh_token --type SecureString \
  --overwrite --value "$TOKEN" --region us-east-1 >/dev/null
echo "Saved to SSM /booking/google_refresh_token"

printf '%s' "$TOKEN" | gh secret set GOOGLE_REFRESH_TOKEN --repo alireza12t/alireza12t.github.io
echo "Saved GitHub secret GOOGLE_REFRESH_TOKEN"

gh workflow run sync-calendar.yml --repo alireza12t/alireza12t.github.io
echo "Started Sync Calendar Availability run"
