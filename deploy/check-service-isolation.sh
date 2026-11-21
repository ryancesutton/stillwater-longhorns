#!/usr/bin/env bash
# Temporary dummy-file exercise. No real credentials, services or login settings.
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then
    echo 'Review this script, then run it with sudo.' >&2
    exit 1
fi
for account in longhorns_app longhorns_mcp; do
    getent passwd "$account" >/dev/null
    id "$account"
done

# Unique root-controlled directory; remove only this exercise's files on exit.
lab_dir=$(mktemp -d /var/tmp/longhorns-isolation.XXXXXXXX)
trap 'rm -rf -- "$lab_dir"' EXIT
chmod 711 "$lab_dir"

# Root controls each directory; the matching service group may traverse it.
install -d -o root -g longhorns_app -m 750 "$lab_dir/app"
install -d -o root -g longhorns_mcp -m 750 "$lab_dir/mcp"
printf '%s\n' 'DUMMY_MODEL_KEY_NOT_A_CREDENTIAL' > "$lab_dir/app/dummy-key"
printf '%s\n' 'DUMMY_DB_PASSWORD_NOT_A_CREDENTIAL' > "$lab_dir/mcp/dummy-key"
chown longhorns_app:longhorns_app "$lab_dir/app/dummy-key"
chown longhorns_mcp:longhorns_mcp "$lab_dir/mcp/dummy-key"
chmod 600 "$lab_dir/app/dummy-key" "$lab_dir/mcp/dummy-key"
stat -c '%A %U:%G %n' "$lab_dir/app" "$lab_dir/mcp" \
    "$lab_dir/app/dummy-key" "$lab_dir/mcp/dummy-key"

# Real reads executed under the intended identities, not just mode inspection.
runuser -u longhorns_app -- cat "$lab_dir/app/dummy-key" >/dev/null
echo 'PASS: app can read its own dummy credential'
runuser -u longhorns_mcp -- cat "$lab_dir/mcp/dummy-key" >/dev/null
echo 'PASS: MCP can read its own dummy credential'

expect_denied() {
    local account=$1 path=$2 label=$3
    if runuser -u "$account" -- cat "$path" >/dev/null 2>&1; then
        echo "FAIL: $label was readable" >&2
        exit 1
    fi
    echo "PASS: $label denied"
}
expect_denied longhorns_app "$lab_dir/mcp/dummy-key" 'app reading MCP dummy credential'
expect_denied longhorns_mcp "$lab_dir/app/dummy-key" 'MCP reading app dummy credential'
expect_denied ry "$lab_dir/app/dummy-key" 'ordinary ry process reading app dummy credential'
expect_denied ry "$lab_dir/mcp/dummy-key" 'ordinary ry process reading MCP dummy credential'
echo 'Exercise complete; temporary dummy files will be removed.'
echo 'Administrative root/sudo access can still cross these boundaries.'
