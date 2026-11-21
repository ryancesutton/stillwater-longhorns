# Staged VM Deployment Runbook

Current status: November 18, 2026. Initial read-only inspection completed; no application/database deployment changes applied. Ry installed a dedicated SSH public key on both hosts and key-based access from this session succeeded. The local working app remains the fallback. Owner permission and Ry's sudo capability on Smaug and Rivendell are confirmed.

## Target and gates

| Component | Target | Intended boundary |
|---|---|---|
| Existing static site | Smaug | Preserve its files, service, user and ports; inspect before modifying shared configuration |
| Web app / orchestrator | Smaug | Separate unprivileged runtime; model API key only where required; browser initially through SSH tunnel |
| MCP retrieval | Smaug | Restricted process/container, DB credential only, no model/import/admin secret access |
| MySQL | Rivendell | Persistent storage; private app-host access; independently enforced restricted accounts/views |
| Import and administration | Deliberate maintenance context | Separate credentials, unavailable to ordinary app/MCP runtime |

Do not copy the entire local secrets directory to either runtime. Generate deployment-specific database credentials privately. The Google/email-password login plan remains future work; the current request token is not human authentication.

## 1. Inspect read-only

Use verified SSH destinations and known host keys; do not disable host-key validation. Record sanitized conclusions, not private connection details. Inspect OS/architecture, CPU/RAM/disk, service users, running services, listening ports, Docker/container/runtime availability, Tailscale state and existing firewall rules. Refresh Rivendell capacity. Inventory Smaug's working static site before choosing directories/ports. Avoid raw service environment/configuration dumps that could contain secrets.

Initial short-name resolution and password-only authentication problems were resolved using full MagicDNS destinations and a dedicated Ed25519 key installed by Ry. Do not publish private destination details or key material.

Observed inventory:

| Host | OS / Python | CPU | Available memory / disk at inspection | Existing workload |
|---|---|---|---|---|
| Smaug | Ubuntu 24.04.5 / Python 3.12.3 | 4 logical CPUs | 7.2 GiB / 94 GiB | `linrei-review.service` user service, Python process owned by `ry`, listener on Tailscale interface port 8181 |
| Rivendell | Ubuntu 24.04.5 / Python 3.12.3 | 2 logical CPUs | 3.4 GiB / 55 GiB | No application/database listener observed |

Neither host has Docker or Podman on the inspected PATH; both have subordinate-user mappings including `ry`. No swap was configured. Current application compatibility with Python 3.12 is unverified; local development used 3.13. Inspection did not establish firewall/tailnet policy, backups or persistence across rebuilds.

`sudo -n true` requires a password on both hosts. This does not contradict Ry's unrestricted sudo authorization: the SSH key authenticates login, but does not supply sudo authentication. Keep passwords out of chat and automation arguments. Prepare explicit administrator bootstrap commands for Ry to execute in his terminal; do not enable blanket passwordless sudo for the app or automation.


## 2. Explain and choose isolation before implementation

A Python module's location does not establish an identity: a process executes as an OS user. Current stdio child processes inherit the app user's authority. A minimal environment is not filesystem isolation.

For the proposed MCP container, review together:

- Minimal required code/dependencies and non-root runtime user.
- A credential-only read-only mount; no project-wide `secrets/` mount.
- Stdio input/output wiring, with protocol stdout separate from diagnostics.
- Restricted writable paths, capabilities, network destinations and no Docker socket inside the container.
- Host-side launch authority. Do not grant the app broad sudo or rootful Docker control to obtain isolation. Select an appropriate rootless runtime or narrowly controlled service mechanism after inspecting host support.
- Positive read test and negative dummy-secret access tests; containerization alone is not proof of isolation.

**Code gap:** the web game-list route currently calls `list_games()` directly and reads the MCP DB credential in the web process. To reserve that credential for MCP, route that lookup through the isolated retrieval boundary too. Review this change with Ry before implementation. Local connection code also hardcodes loopback/port and repository secret paths; introduce deliberate configuration and verify remote connection protection without weakening identity checks.

## 3. Configure database and private connectivity

Choose a reviewed private listener or tunnel mechanism after network inspection. No public MySQL listener. Restrict permitted source/destination paths, authenticate the database identity, and verify encryption/server identity as appropriate to the chosen transport. Do not assume a broad MySQL host match or Tailscale membership is a firewall policy.

Provision separate deployment administrator, import, MCP and locked view-definer identities. Apply schema/views deliberately to a new database; one-time existing setup scripts are local helpers, not automatically safe remote migration tools. Load the preserved archives through the import identity. Verify scope/provenance, repeated-import stability, rollback, allowed view reads, denied base/private reads and writes.

## 4. Bring up app safely

Deploy reviewed code into administrator-controlled locations with separate secret/state directories. Keep runtime users unable to modify deployed code or gain administrative launch authority. Pin/install compatible dependencies, verify their resolved versions on Linux, and inspect relevant security findings. Preserve the local fallback and existing site; do not change shared web-server settings until the listening/access plan is understood.

Begin in preview/offline mode with no paid calls. Verify static-site health, SSH-tunneled browser access, game lookup, tool validation, sanitized errors/logs, secret isolation and service restart behavior. Enable live generation only after these gates pass; a single deliberate paid test requires known usage limits and no automatic full-workflow retries.

## 5. Recovery and residual risk

Choose persistent storage, backup ownership/retention, and restore procedure; backup coverage is currently unconfirmed. Restore into a disposable database and check counts/relationships/provenance. Record rollback steps before service/network changes. Document credential revocation/rotation and existing-session handling. Keep aggregate usage controls, human authentication and audit attribution gaps explicit; planned controls do not count as protection.

Update the [threat register](deployment-threat-model.md) with observed likelihood/impact rationale, test evidence, owner and residual-risk decision. Teach each step as concept → configuration/code → permitted/denied verification, identifying identity-security and agentic-security controls separately.

## November 21 — Service identity exercise

Ry ran `deploy/create-smaug-service-users.sh` on November 18. Read-only inspection on November 21 confirmed `longhorns_app` and `longhorns_mcp` exist with distinct UIDs/groups and `/usr/sbin/nologin`; Ry's execution output showed both passwords locked. The existing static-site user service remains active. Runtime processes, containers and real secret isolation are not configured yet.

Prepared and uploaded `deploy/check-service-isolation.sh`; syntax checked locally. Ry executed it on Smaug and supplied output on November 21: all six actual-read checks passed (each service could read its own dummy file; cross-service reads and ordinary `ry` reads were denied). The script reported cleanup on exit; cleanup was not independently inspected. Run with sudo after review. It creates root-controlled temporary directories and service-owned mode-600 dummy files, tests actual permitted/denied reads under each identity (including ordinary `ry`), then cleans up. No real secrets or persistent service configuration are changed. Root/sudo can bypass this ordinary-user boundary; these checks do not prove container, network or full runtime isolation.

## November 21 — Separate MCP runtime: prepared, not installed

Chosen first implementation: a systemd-managed service under `longhorns_mcp`, reached through a permission-controlled Unix socket. This replaces the earlier container proposal for the first isolation milestone; no container runtime is required. Containers remain optional later defense in depth. See [systemd socket activation](https://www.freedesktop.org/software/systemd/man/latest/systemd.socket.html) and [execution settings](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html).

Prepared files:

- `deploy/systemd/longhorns-mcp.socket`: local `/run` socket, root-owned, group `longhorns_app`, mode 0660; bounded concurrent connections. No TCP listener.
- `deploy/systemd/longhorns-mcp@.service`: per-connection process under `longhorns_mcp`, stdin/stdout connected to socket, diagnostics separate; no new privileges/capabilities, read-only system view, private temporary files, bounded memory/tasks/lifetime.
- `scripts/mcp_socket_bridge.py`: unprivileged stdio byte relay. It does not read secrets, execute model-selected commands, or change users. The connect attempt is bounded; idle socket waits rely on the enclosing client/workflow deadlines rather than timing out during an intervening model request.
- `briefing.mcp_server_parameters()`: default local development behavior retained; explicitly setting `STILLWATER_MCP_SOCKET` selects the relay. A configured unavailable socket fails rather than falling back to a same-user MCP subprocess.

These unit files are templates for the planned `/opt/longhorns` deployment. They have not been installed, started or verified with Ubuntu's systemd. Dependencies, protected code/secret locations, remote DB settings, web game-list routing, and Linux service-level positive/negative tests remain to do. Unix-socket access permits the approved retrieval protocol, not service configuration or arbitrary process launches; root still controls service definitions.

Local verification: a real MCP server communicated through the Unix-socket relay, discovered exactly the two approved tools, and rejected an unregistered SQL tool without accessing the DB. All 43 Python tests and the existing JavaScript search checks passed during this milestone. This tests transport/protocol behavior, not Linux UID enforcement. No paid requests or DB calls were made by the new transport tests.

### Alternative retained: containerized MCP

Containerization remains an explicitly retained alternative to the first systemd-service implementation. A future comparison should evaluate rootless execution or administrator-managed containers, minimal code/dependency images, credential-only mounts, network restrictions, resource limits, and positive/negative access tests. The app must not receive unrestricted rootful Docker/socket access. Container launch authority and host file mappings require review; a container is not automatically a separate secret boundary. No container runtime or image has been installed for this project.

### Connection vocabulary

A Unix-domain socket is a local inter-process communication endpoint addressed by a filesystem path. Its ownership/mode controls which ordinary users may connect; it is not a regular file storing MCP messages and has no TCP port. The adapter (`mcp_socket_bridge.py`) translates the connection mechanism: it relays the client's stdio bytes to/from the socket without changing the MCP protocol or granting a different identity. systemd starts the receiving MCP process under its configured service identity. Administrator/root access remains privileged.


## November 21 — Linux Python/MCP staging verified

Ry installed Ubuntu's `python3-venv` support on Smaug. A private staging environment now exists at `~/longhorns-setup/runtime-check/.venv`, owned by administrative user `ry`; it is not the final service runtime and is inaccessible beneath the private setup directory to the service accounts.

Installed the two pinned direct dependencies from `requirements.txt` using binary wheels only. `pip check` passed. Real MCP discovery through the Unix socket relay and rejection of an unregistered tool passed on Python 3.12.3/Linux; two transport/configuration tests passed. No DB queries, model API calls or real credentials were involved. The existing static-site service remained active. Preserved resolved dependency versions in `deploy/requirements-linux.lock`; this is a compatibility snapshot, not a vulnerability audit or hash-verified supply-chain guarantee.

Still pending: administrator-controlled final code/venv installation under `/opt/longhorns`, service-account execution and systemd sandbox tests, protected credential configuration, game-list path adaptation and remote DB setup. Do not relocate a virtual environment by copying it: recreate it at its final path using the reviewed dependency manifest because its launch scripts can contain absolute paths.

Ubuntu's package-install output reported a pending kernel reboot and deferred service restarts. Schedule maintenance separately and verify SSH/Tailscale/static-site recovery afterward; no reboot was performed in this step.


## November 21 — Administrator install prepared (execution pending)

`deploy/install-smaug-mcp.sh` and its explicit code/unit/dependency payload are staged in Ry's private `~/longhorns-setup/mcp-install` directory on Smaug. Locked binary wheels are downloaded; no sudo installation has run yet. The script refuses an existing deployment directory or existing units, recreates the venv at its final path, installs wheels offline as the MCP user, then makes code/environment root-owned and non-writable to runtime users. No real credentials are included.

After review, Ry runs `sudo bash ~/longhorns-setup/mcp-install/install-smaug-mcp.sh`. It validates unit definitions, enables only the local socket, and runs `check_managed_mcp.py` as the app user. That check performs real discovery, rejects an unknown tool without querying MySQL, and reads active process metadata to verify the MCP UID, no-new-privileges and zero effective capabilities. An ordinary `ry` socket connection must be denied. If post-activation checks fail, the installer disables the new socket and leaves artifacts for deliberate inspection; it does not remove or overwrite an existing installation. Rollback is disabling the socket; no static-site files or configuration are changed.

This configuration check does not establish database connectivity, production readiness or complete sandbox security. DB credentials/settings and real service secret tests remain pending. The full app is not deployed. Runbook result must be updated from actual installer output before claiming the service is active.


Installer correction: the first execution stopped during preflight because querying a bare `@.service` template with `systemctl show` is invalid. Its error was incorrectly interpreted as an existing unit. Inspection confirmed `/opt/longhorns` was absent and no MCP units were installed; the static site remained active. Corrected the query to use a concrete probe instance and distinguish query failures from existing units. Added `--check` read-only mode; it passed on Smaug after the fix. A fresh sudo installation attempt is safe from the confirmed untouched preflight state; no cleanup or deletion was needed.
