# Local Credential Inventory and Lifecycle

## Current checkpoint — November 21, 2026

The local web/terminal version remains on `main`; deployment work is on `feature/vm-deployment`. Smaug now has separate app/MCP OS accounts, six passing dummy-file access checks, and a systemd-managed MCP socket/service. Real discovery, unknown-tool rejection and actual MCP UID/no-new-privileges/capability checks passed; ordinary `ry` socket access was denied. Root-owned code and dependencies are installed. The static-site service remained active.

The first isolation implementation uses a permission-controlled Unix socket and unprivileged stdio adapter; containerization remains a documented alternative. No real DB/model credentials or remote DB connectivity are configured, and the web app is not deployed. Next: MySQL on Rivendell, restricted connectivity/secret configuration, and adapting the web game-list path to use isolated MCP. Backups/recovery and end-to-end secret isolation remain unverified. See the [deployment runbook](deployment-runbook.md) and [threat model](deployment-threat-model.md). Earlier dated local/demo notes below are historical.

No secret values belong in this document. Paths below are relative to the repository root.

| Identity | Credential file | Intended consumer |
|---|---|---|
| MySQL `root` | `secrets/mysql-root-password` | Local schema/account administration through `db-admin.sh` |
| MySQL `stillwater_import` | `secrets/mysql-import-password` | Offline importer and local integration checks |
| MySQL `stillwater_mcp` | `secrets/mysql-mcp-password` | MCP service and permission checks |
| MySQL `stillwater_view_owner` | None; locked against login | Definer privileges for the three approved views |
| OpenAI model API | `secrets/openai-api-key` | Orchestrator authentication only; never MCP environment or prompt content |
| CFBD | `secrets/cfbd-api-key` | Source retrieval scripts only |

Database passwords were generated locally with Python `secrets.token_hex(32)`: 32 cryptographically random bytes encoded as 64 hexadecimal characters. The language model supplied the generator code, not the password values. Generated values were not displayed in chat or command output. The CFBD key was supplied by the project owner through a hidden prompt.

## Storage and Limitations

Files are ignored by Git and have owner-only read/write permissions (`600`); the secrets directory uses `700`. MySQL stores its own authentication verifier. The root file is mounted into Docker using a Compose secret; import and MCP files are read by their respective local processes. Runtime code must not use the administrator secret or CFBD key.

These are plaintext files, not an encrypted secret manager. Programs running as the Mac user and sufficiently privileged Docker/host administrators can access secrets. Git ignore rules do not enforce process isolation or remove already tracked secrets. Separate database grants are tested; separate runtime OS identities/container secret isolation are not implemented yet. A host compromise can cross these boundaries.

The credential owner should know where each file is stored and how access is revoked, even without memorizing values. Do not paste values into chat, terminal command arguments, screenshots, prompts, or logs. Keep any credential backup in a private password manager or encrypted storage, separate from public project documentation; backup/recovery has not been configured or tested.

## Rotation and Recovery Plan — Not Yet Automated or Tested

1. Stop the affected consumer and identify the exact MySQL account, including its host component.
2. Generate a replacement cryptographically random password into a private temporary file without printing it.
3. Use an authorized administrative session to change the account password, then replace the matching consumer credential file with owner-only permissions. Treat this as coordinated work: changing only the file does not update MySQL.
4. Reconnect the consumer and verify its identity and permissions. New authentication should work with the replacement; old credentials should no longer establish a new session. Existing authenticated sessions may remain, so terminate/reconcile them as appropriate.
5. Remove superseded credential copies and update private backups. If any step fails, reconcile server and file state before restarting consumers; do not blindly rerun account-creation scripts.

Changing `MYSQL_ROOT_PASSWORD_FILE` or restarting the container does not rotate an already initialized database account. If a runtime file is lost but administrator access remains, reset that runtime account rather than trying to recover its password from MySQL. Loss of administrator access requires a separately reviewed recovery procedure; do not delete the database volume as a shortcut.

If a credential is exposed, revoke/rotate it at the provider/database first. Removing it from a file or Git commit alone does not revoke it. CFBD key rotation/revocation is managed through CFBD, not MySQL.

## LLM-Assisted Identity Setup Checklist

- Review identity, purpose, grants, and storage location before creation.
- Generate secrets with an OS-backed cryptographic generator, outside model-generated text.
- Keep values out of prompts, source files, process arguments, and logs.
- Inspect actual grants and test allowed and denied actions as the intended identity.
- Record implemented controls and limits separately from planned isolation.
- Review credential access again before MCP/agent runtime or VM deployment.

Current setup scripts are one-time administrative helpers and can partially complete because account/view DDL is not transactional. They refuse existing accounts/files; use state inspection and a deliberate recovery plan instead of deleting credentials to force a rerun.
