#!/usr/bin/env bash
# One-time bootstrap: creates two locked, non-interactive service accounts only.
# Does not install software, grant sudo, change existing users, or move secrets.
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo 'Run this script with sudo after reviewing it.' >&2
    exit 1
fi

# Refuse existing users/groups rather than taking over an unrelated identity.
for account in longhorns_app longhorns_mcp; do
    if getent passwd "$account" >/dev/null || getent group "$account" >/dev/null; then
        echo "Existing user/group: $account. Stop and inspect before proceeding." >&2
        exit 1
    fi
done

# No passwords are set; useradd leaves these accounts password-locked.
# nologin blocks ordinary interactive login; administrators can still run services.
# Home paths are reserved here, not created or populated.
useradd --system --user-group --no-create-home \
    --home-dir /var/lib/longhorns-app --shell /usr/sbin/nologin longhorns_app
useradd --system --user-group --no-create-home \
    --home-dir /var/lib/longhorns-mcp --shell /usr/sbin/nologin longhorns_mcp

getent passwd longhorns_app longhorns_mcp
id longhorns_app
id longhorns_mcp
passwd --status longhorns_app
passwd --status longhorns_mcp
