# Booking System — Progress & Next Steps

## Architecture (decided)

- **Backend:** AWS Lambda (Python 3.12) behind a Lambda Function URL (not API Gateway — avoids the 12-month free-tier expiry). Region: `us-east-1`.
- **Storage:** DynamoDB table `bookings` (partition key `slot_iso`), on-demand billing. Conditional `PutItem` prevents double-booking atomically.
- **Secrets:** SSM Parameter Store (SecureString) for `google_client_secret` and `google_refresh_token`. Lambda env vars for non-secret config.
- **Cost:** $0/month forever at expected traffic — fits Lambda + DynamoDB + SSM standard-tier free tiers.

## Done

- [x] DynamoDB table `bookings` created (partition key `slot_iso (S)`, on-demand)
- [x] Google OAuth scope upgraded from `calendar.readonly` → `calendar.events`
- [x] New refresh token stored in SSM at `/booking/google_refresh_token` (SecureString)
- [x] Lambda handler written — `lambda/handler.py` (stdlib + boto3 only, no deps)
  - Validates input, conditional DynamoDB write, OAuth token exchange, creates Google Calendar event with Meet link via `conferenceData`, `sendUpdates=all` to email both parties
  - All secrets read from SSM at cold start, cached across warm invocations
- [x] IAM policy JSON drafted — `lambda/iam-policy.json` (least-privilege: DynamoDB on `bookings` only, SSM on `/booking/*` only, KMS Decrypt via SSM only)
- [x] Deploy script written — `lambda/deploy.sh` (packages zip, updates Lambda, attaches policy, creates Function URL with CORS locked to `https://alireza12t.github.io`)
- [x] All secrets scrubbed from committable files — `.gitignore` expanded to cover `.env`, `*.zip`, `__pycache__`, `.claude/`
- [x] Setup docs — `lambda/SETUP.md`

## Left to do

### 1. AWS credentials on the Mac
- [ ] Create IAM user `booking-deployer` with `AdministratorAccess` in the AWS console
- [ ] Create access key for CLI, copy both parts
- [ ] `aws configure` on Mac → paste keys, region `us-east-1`, output `json`

### 2. Push client_secret to SSM (one-time)
- [ ] From Mac Terminal, run (don't paste the secret into any file):
  ```bash
  export GOOGLE_CLIENT_SECRET='<from SECRETS.md>'
  aws ssm put-parameter --name /booking/google_client_secret \
    --type SecureString --overwrite --region us-east-1 \
    --value "$GOOGLE_CLIENT_SECRET"
  unset GOOGLE_CLIENT_SECRET
  ```

### 3. Deploy the Lambda
- [ ] `cd ~/Desktop/alireza12t.github.io/lambda && ./deploy.sh`
- [ ] Copy the `FUNCTION_URL=...` it prints

### 4. Wire the website to the Lambda
- [x] Replace `confirmBooking()` in `script.js` — remove `.eml` download, POST JSON `{slot_iso, duration_min, name, email}` to the Function URL
- [x] Add loading state on the Confirm button
- [x] Handle `409 slot_taken` with a "pick another time" error in the UI
- [x] Show confirmation screen with the returned Meet link
- [ ] **Paste the Lambda Function URL** into `BOOKING_API_URL` in `script.js` (line ~98)

### 5. Live booking list (hide taken slots)
- [x] Add a `GET /bookings` path (or a separate read-only Lambda) that returns upcoming `slot_iso` values
- [x] Website fetches it on page load and removes taken slots from the grid
- [ ] (Optional) Add a 5-minute soft-hold when a visitor opens the confirm form

### 6. End-to-end test
- [ ] Book a test slot from a private-browser window
- [ ] Verify: Google Calendar event created, Meet link generated, both parties get invite emails, DynamoDB row written with `status=booked`
- [ ] Try to book the same slot again — should return `409 slot_taken`

### 7. Commit & push
- [ ] Review `git diff` once more to make sure nothing sensitive sneaks in
- [ ] `git add TODO.md .gitignore lambda/ scripts/get_refresh_token.py script.js`
- [ ] Commit, push to master

## What never hits the repo

- `SECRETS.md` (raw credentials, kept for personal reference)
- `.env` / `.env.*` (any env file)
- `lambda/handler.zip` (rebuilt from source by `deploy.sh`)
- `.venv/`, `__pycache__/`, `*.pyc`, `.DS_Store`, `.claude/`

Enforced by `.gitignore`. Verified with `git check-ignore` before each commit.
