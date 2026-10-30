#!/bin/sh
# Local setup helper only. Never use this administrative identity in agent code.
# SQL arrives on stdin. Password is read inside the container, never printed.
set -eu
cd "$(dirname "$0")/.."
docker_cli=${DOCKER_CLI:-/Applications/Docker.app/Contents/Resources/bin/docker}
"$docker_cli" compose exec -T db sh -eu -c '
    umask 077
    config=$(mktemp)
    trap '\''rm -f "$config"'\'' EXIT
    printf "[client]\nuser=root\npassword=%s\nprotocol=socket\n" \
        "$(cat /run/secrets/mysql_root_password)" > "$config"
    mysql --defaults-extra-file="$config" --batch --database=stillwater
'
