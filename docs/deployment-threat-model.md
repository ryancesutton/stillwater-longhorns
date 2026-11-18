# Deployment Threat Model — Initial Draft

Prepared November 18, 2026 with Ry. This is a guided first pass, not a complete security assessment. No remote configuration was inspected or changed for this draft.

## Scope, assets, and assumptions

The working local app is our baseline. Planned deployment: Python web app/orchestrator and MCP on Smaug; MySQL on Rivendell. Smaug already hosts a separate static site, which must remain working. Both VMs are available and their owner has authorized installation and service-user configuration. Ry reports SSH access and has confirmed that `ry` may run all commands through sudo on both Smaug and Rivendell. This is user-verified access, not an independent remote inspection by Codex.

Protect API credentials and funds, database credentials and integrity, SSH/admin access, service availability, original import archives, and the existing static site. Football data has relatively low confidentiality; credentials and host access have much higher sensitivity. Backups and recovery remain unconfirmed.

Relevant identities: human administrator, future authenticated app user, app service, MCP service, importer, MySQL accounts, and static-site service. Research and writer are model roles, not independently established OS identities. Human login is not implemented; email/password with optional Google sign-in is planned for later.

## Flows and trust boundaries

1. Browser → web server: browser requests are untrusted; server validates them.
2. Orchestrator → external model API: credentials authenticate the request; prompts/evidence must exclude secrets.
3. Orchestrator → MCP over stdio: application validates proposed tool calls; MCP validates arguments independently.
4. MCP → MySQL: database identity and grants govern access. Moving this across VMs adds a network boundary.
5. Retrieved evidence → model context: source content is data, not authority to issue instructions.
6. Service → filesystem: OS identities and permissions must separate secrets, including from the static site.

Browser access through an SSH tunnel over Tailscale is the intended initial approach. Actual listening interfaces, tailnet policies, ports, service identities, and database connection protection are not yet verified. Tailscale membership alone is not authorization to use MySQL or paid generation.

## Initial threat register

“Existing” below refers to the local implementation and recorded checks, not verified VM deployment. Proposed controls are not counted as implemented protection.

| Threat and assumed starting access | Harm | Existing controls and limits | Proposed control / next verification |
|---|---|---|---|
| **T1: Secret theft.** An attacker compromises a service/process that can read credential files, or a secret leaks into prompts/logs. | Unauthorized API spending, permitted DB access, or wider host compromise depending on credential. | Secrets outside Git; restricted file modes; MCP minimal environment; selected evidence; sanitized audit fields. Same-OS-user file access remains a gap. | Separate runtime identities or narrowly mounted containers; no routine runtime sudo; inspect file access with dummy secrets. Mock API transport to verify a fake key occurs only in the authentication header, not body/logs, including error paths. |
| **T2: Paid-generation abuse.** Caller can reach and satisfy the generation endpoint checks, legitimately or through a compromised authorized machine. | API spending and denied service to others. | Request validation/token, one active generation, cooldown, ten attempts per server start, bounded model/tool workflow. No human login or persistent aggregate spending ceiling. | Verify private reachability; design persistent aggregate usage controls and later user authorization/quotas. Test bursts, concurrent attempts, restarts, and budget exhaustion without paid calls. |
| **T3: Indirect prompt injection.** Attacker can influence text that reaches model context through source/import data. This access is an assumption, not a demonstrated exploit. | Misleading briefing, attempted tool misuse, or disclosure if another boundary exposes sensitive information. | No model-facing file/shell/arbitrary-SQL tools; tool validation; evidence-only writer without tools; DB grants; output structure/reference checks. References do not prove factual accuracy. Earlier fixture tests cover sampled behaviors, not all attacks. | Map possible source/file/DB modification paths and their access requirements. Repeat harmless injection tests after relevant changes; test blocked tool proposals and secret boundaries independently. |
| **T4: Stolen MCP DB credential.** Attacker obtains the credential and can reach MySQL. | Copy approved-view data or consume DB resources, bypassing application tool limits. | SELECT only on approved views; base/private reads and writes denied in recorded local checks. Credential does not grant arbitrary database authority. | Restrict network path to intended host/service; preserve grants remotely; verify allowed/denied connections and queries. Define rotation/revocation and active-session termination procedures. |
| **T5: Dependency failure or exhaustion.** DB/model/network becomes unavailable, slow, or overloaded; accidental failure or deliberate load is possible. | Hanging/failed briefings, duplicate paid work on retries, reduced availability. | API/MCP/workflow timeouts, bounded responses, sanitized failure response, no automatic whole-workflow retry. Cancellation does not prove remote work stopped or was not billed. | Simulate DB/network/model failures; verify bounded response time, slot release, no unsupported briefing, and no accidental repeated generation. Inspect sanitized stage/duration/usage events. |
| **T6: Deployment disrupts the static site or loses persistent data.** Configuration mistake, resource contention, or host/storage failure. | Site/app outage, lost database or archives, difficult recovery. | Local DB uses persistent Docker storage; VM configuration and backups remain unverified. | Inventory Smaug directories, identities, services, ports, and resources before changes. Separate services and permissions; plan persistence, backups, restore test, and rollback. |

## Prioritization and residual risk

Ratings remain provisional until exposure and configuration are inspected. For each scenario, record **likelihood (low/medium/high)** with access prerequisites and supporting evidence, and **impact (low/medium/high)** with spending, confidentiality, integrity, availability, and recovery consequences. Record uncertainty rather than inventing precision.

Assess current risk separately from residual risk after a control is implemented and tested. Prioritize credential boundaries and reachable paid operations before enabling remote generation. Reachability and existing controls affect likelihood; credential scope and spending/recovery limits affect impact. Decide whether to mitigate, avoid the capability, or explicitly accept remaining risk. Link decisions to an owner, next action, and test evidence.

## Next session / deployment gate

- Inspect both VMs read-only, including the existing static-site service; verify network exposure. Administrative sudo capability on both hosts is confirmed by Ry; runtime services should use restricted identities without sudo.
- Map each runtime identity to its required secrets, files, tools, and network destinations before selecting OS-user/container boundaries.
- Choose one small negative test for Ry to implement and explain.
- Assign initial risk ratings using observed configuration; plan staged deployment, rollback, and restore verification before enabling remote paid generation.

## Learning checkpoint

Ry independently identified credential value, excessive generation, aggregate-budget risk, timeout/retry spending, and compromised trusted-client risk. Reinforce prompt injection versus SQL injection, attack entry prerequisites versus downstream containment, OS identities versus agent roles, and safe error logging. Foundational lessons should explain normal system behavior and candidate attack paths before asking Ry to assess unfamiliar mechanisms.
