#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${DEPLOY_HOST:?}" "${DEPLOY_USER:?}" "${DEPLOY_SSH_KEY:?}" "${DEPLOY_KNOWN_HOSTS:?}" "${EXPECTED_REPOSITORY:?}"
[[ "$DEPLOY_HOST" =~ ^[a-zA-Z0-9.-]+$ ]] || exit 1
[[ "$DEPLOY_USER" =~ ^firebridge(-webapp|-agent)?-deploy$ ]] || exit 1
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
printf '%s\n' "$DEPLOY_SSH_KEY" > "$temporary/key"
printf '%s\n' "$DEPLOY_KNOWN_HOSTS" > "$temporary/known_hosts"
chmod 600 "$temporary/key" "$temporary/known_hosts"
ssh -F /dev/null -i "$temporary/key" -o IdentitiesOnly=yes -o BatchMode=yes \
  -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$temporary/known_hosts" \
  -o ConnectTimeout=20 "$DEPLOY_USER@$DEPLOY_HOST" status > "$temporary/status.json"
python3 - "$temporary/status.json" <<'PY'
import json, os, sys
with open(sys.argv[1]) as stream:
    status = json.load(stream)
assert status["state"] == "healthy", "Existing service is not healthy"
assert status["deployment_repository"] == os.environ["EXPECTED_REPOSITORY"], "Server gateway trusts a different repository"
print("Verified restricted SSH deployment connection and repository identity; running revision: " + status["revision"])
PY
