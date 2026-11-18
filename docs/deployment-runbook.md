# Staged VM Deployment Runbook

Current status: November 18, 2026. Planning/checkpoint only; no deployment changes applied. The local working app remains the fallback. Owner permission and Ry's sudo capability on Smaug and Rivendell are confirmed.

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

Initial direct SSH attempts from this Codex session could not resolve `smaug` or `rivendell`. This is not evidence of a VM outage; exact resolvable destinations or access through Ry's existing SSH session are needed. No authentication or remote command ran during those attempts.

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
