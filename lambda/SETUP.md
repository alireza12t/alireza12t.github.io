# booking-api — one-time setup

Everything sensitive lives in AWS SSM Parameter Store. Nothing in this
directory contains secrets.

## 1. Push the OAuth client_secret into SSM (one-time)

Run once from your Mac (or CloudShell), substituting the real value from
`../SECRETS.md`:

```bash
aws ssm put-parameter \
  --name /booking/google_client_secret \
  --type SecureString \
  --overwrite \
  --value "$GOOGLE_CLIENT_SECRET" \
  --region us-east-1
```

Tip: `export GOOGLE_CLIENT_SECRET='...'` first (from `SECRETS.md`) so the
value never appears in shell history. Then `unset GOOGLE_CLIENT_SECRET`.

## 2. Push the refresh_token into SSM (already done)

The refresh token was stored via the console earlier. If you ever need to
rotate it, re-run `scripts/get_refresh_token.py` and:

```bash
aws ssm put-parameter \
  --name /booking/google_refresh_token \
  --type SecureString \
  --overwrite \
  --value "$REFRESH_TOKEN" \
  --region us-east-1
```

## 3. Deploy the Lambda

```bash
./deploy.sh
```

The script packages `handler.py` into a zip, updates Lambda code + config,
attaches the IAM policy, creates a Function URL with CORS, and prints the
resulting URL. It contains NO secrets.

## What's in SSM vs env vars

| Place | Name | Why |
|---|---|---|
| SSM SecureString | `/booking/google_client_secret` | secret |
| SSM SecureString | `/booking/google_refresh_token` | secret |
| Lambda env var | `GOOGLE_CLIENT_ID` | not a secret — public in OAuth URLs |
| Lambda env var | `HOST_EMAIL`, `HOST_NAME`, `TIMEZONE`, etc. | config |

The Lambda execution role has least-privilege access: DynamoDB on the
`bookings` table only, SSM GetParameter on `/booking/*` only, and KMS
Decrypt only via the SSM service.
