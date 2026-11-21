#!/usr/bin/env bash
# One-time MCP runtime installation; no database/model credentials are installed.
# Run from the uploaded mcp-install directory after reviewing this script.
set -euo pipefail
preflight_only=false
case "${1:-}" in
    --check) preflight_only=true ;;
    "") ;;
    *) echo 'Usage: install-smaug-mcp.sh [--check]' >&2; exit 1 ;;
esac
if [[ ${EUID} -ne 0 && $preflight_only != true ]]; then
    echo 'Run with sudo after review.' >&2
    exit 1
fi
payload_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
target=/opt/longhorns
# Service users cannot traverse the private upload directory; use a neutral cwd.
cd /
[[ ! -e "$target" && ! -L "$target" ]] || { echo 'Deployment path exists; stop and inspect.' >&2; exit 1; }
for account in longhorns_app longhorns_mcp; do
    [[ $(id -u "$account") -ne 0 ]]
done
for unit in longhorns-mcp.socket longhorns-mcp@.service; do
    # systemctl show needs a concrete instance, not a bare @.service template.
    probe=${unit/@.service/@preflight.service}
    if ! load_state=$(systemctl show --property=LoadState --value "$probe"); then
        echo "Could not inspect $unit; stop before installation." >&2
        exit 1
    fi
    [[ $load_state == not-found ]] || {
        echo "Unit $unit already exists (state: $load_state); stop and inspect." >&2; exit 1;
    }
    [[ -f "$payload_dir/systemd/$unit" ]]
done
for filename in mcp_server.py game_tools.py local_db.py mcp_socket_bridge.py check_managed_mcp.py; do
    [[ -f "$payload_dir/scripts/$filename" && ! -L "$payload_dir/scripts/$filename" ]]
done
[[ -f "$payload_dir/requirements-linux.lock" ]]
compgen -G "$payload_dir/wheels/*.whl" >/dev/null
if [[ $preflight_only == true ]]; then
    echo 'PASS: deployment path unused, units absent, accounts and payload present; no changes made.'
    exit 0
fi

# No blanket sudo/Docker privileges are granted to either service user.
install -d -o root -g root -m 755 "$target" "$target/scripts" "$target/wheels"
install -o root -g root -m 644 "$payload_dir/requirements-linux.lock" "$target/requirements-linux.lock"
for filename in mcp_server.py game_tools.py local_db.py mcp_socket_bridge.py check_managed_mcp.py; do
    install -o root -g root -m 644 "$payload_dir/scripts/$filename" "$target/scripts/$filename"
done
for wheel in "$payload_dir"/wheels/*.whl; do
    [[ ! -L "$wheel" ]]
    install -o root -g root -m 644 "$wheel" "$target/wheels/"
done

# Recreate at the final path. Install third-party packages without root or network.
python3 -m venv "$target/.venv"
chown -R longhorns_mcp:longhorns_mcp "$target/.venv"
runuser -u longhorns_mcp -- env HOME=/nonexistent PIP_CONFIG_FILE=/dev/null \
    PIP_DISABLE_PIP_VERSION_CHECK=1 "$target/.venv/bin/python" -m pip install \
    --no-index --no-cache-dir --only-binary=:all: --find-links "$target/wheels" \
    -r "$target/requirements-linux.lock"
chown -R root:root "$target/.venv"
chmod -R go-w "$target/.venv"
runuser -u longhorns_mcp -- "$target/.venv/bin/python" -m pip check

install -o root -g root -m 644 "$payload_dir/systemd/longhorns-mcp.socket" /etc/systemd/system/
install -o root -g root -m 644 "$payload_dir/systemd/longhorns-mcp@.service" /etc/systemd/system/
systemd-analyze verify /etc/systemd/system/longhorns-mcp.socket /etc/systemd/system/longhorns-mcp@.service
systemctl daemon-reload
# If protocol/identity checks fail, disable the newly installed socket for review.
trap 'systemctl disable --now longhorns-mcp.socket >/dev/null 2>&1 || true; echo "Installation stopped; inspect before rerunning." >&2' ERR
systemctl enable --now longhorns-mcp.socket
runuser -u longhorns_app -- "$target/.venv/bin/python" "$target/scripts/check_managed_mcp.py"

# Ordinary ry processes should not be able to connect; sudo remains administrative.
runuser -u ry -- "$target/.venv/bin/python" - <<'PY'
import socket
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
    try:
        connection.connect('/run/longhorns-mcp.sock')
    except PermissionError:
        print('PASS: ordinary ry connection to MCP socket denied')
    else:
        raise SystemExit('FAIL: ordinary ry can connect to MCP socket')
PY
stat -c '%A %U:%G %n' /run/longhorns-mcp.sock "$target" "$target/scripts" "$target/.venv"
trap - ERR
echo 'MCP service installed; protocol/identity checks passed. No DB credentials or live model access configured.'
echo 'Rollback: sudo systemctl disable --now longhorns-mcp.socket'
