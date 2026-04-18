#!/usr/bin/env bash
# Deploy/update the booking-api Lambda.
#
# Zero secrets in this file. Client secret and refresh token live in SSM
# Parameter Store as SecureString params (one-time setup — see SETUP.md).
#
# Run locally or from AWS CloudShell after AWS creds are configured.

set -euo pipefail
cd "$(dirname "$0")"

REGION="us-east-1"
FN="booking-api"

# --- non-secret config (fine to commit) ---
GOOGLE_CLIENT_ID="582018673706-qbv3q1rv78f93jup1jqoei29rs7090bh.apps.googleusercontent.com"
ALLOWED_ORIGIN="https://alireza12t.github.io"
HOST_EMAIL="alireza.toghiani@icloud.com"
HOST_NAME="Alireza Toghiani"
TIMEZONE="America/Toronto"
DDB_TABLE="bookings"
SSM_CLIENT_SECRET_PARAM="/booking/google_client_secret"
SSM_REFRESH_TOKEN_PARAM="/booking/google_refresh_token"

# rebuild the zip from handler.py
echo "[0/5] Packaging handler.zip..."
rm -f handler.zip
zip -q handler.zip handler.py

echo "[1/5] Updating function code..."
aws lambda update-function-code \
  --function-name "$FN" \
  --zip-file fileb://handler.zip \
  --region "$REGION" >/dev/null
aws lambda wait function-updated --function-name "$FN" --region "$REGION"

echo "[2/5] Setting env vars, handler, timeout, memory..."
aws lambda update-function-configuration \
  --function-name "$FN" \
  --handler handler.lambda_handler \
  --timeout 15 \
  --memory-size 256 \
  --environment "Variables={GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID,ALLOWED_ORIGIN=$ALLOWED_ORIGIN,HOST_EMAIL=$HOST_EMAIL,HOST_NAME=\"$HOST_NAME\",TIMEZONE=$TIMEZONE,DDB_TABLE=$DDB_TABLE,SSM_CLIENT_SECRET_PARAM=$SSM_CLIENT_SECRET_PARAM,SSM_REFRESH_TOKEN_PARAM=$SSM_REFRESH_TOKEN_PARAM}" \
  --region "$REGION" >/dev/null
aws lambda wait function-updated --function-name "$FN" --region "$REGION"

echo "[3/5] Attaching inline IAM policy (DynamoDB + SSM + KMS)..."
ROLE_ARN=$(aws lambda get-function-configuration --function-name "$FN" --region "$REGION" --query 'Role' --output text)
ROLE_NAME="${ROLE_ARN##*/}"
echo "  role: $ROLE_NAME"
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name booking-api-extras \
  --policy-document file://iam-policy.json

echo "[4/5] Creating Function URL with CORS..."
if ! aws lambda create-function-url-config \
       --function-name "$FN" \
       --auth-type NONE \
       --cors "AllowOrigins=[\"$ALLOWED_ORIGIN\"],AllowMethods=[\"*\"],AllowHeaders=[\"content-type\"],MaxAge=300" \
       --region "$REGION" 2>/dev/null; then
  aws lambda update-function-url-config \
    --function-name "$FN" \
    --auth-type NONE \
    --cors "AllowOrigins=[\"$ALLOWED_ORIGIN\"],AllowMethods=[\"*\"],AllowHeaders=[\"content-type\"],MaxAge=300" \
    --region "$REGION" >/dev/null
fi

aws lambda add-permission \
  --function-name "$FN" \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --region "$REGION" 2>/dev/null || true

aws lambda add-permission \
  --function-name "$FN" \
  --statement-id FunctionURLAllowInvoke \
  --action lambda:InvokeFunction \
  --principal "*" \
  --region "$REGION" 2>/dev/null || true

FN_URL=$(aws lambda get-function-url-config --function-name "$FN" --region "$REGION" --query 'FunctionUrl' --output text)

echo "[5/5] Done."
echo ""
echo "Function URL: $FN_URL"
