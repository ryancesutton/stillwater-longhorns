# VM Deployment — Mentor Answers and Remaining Checks

## Confirmed by owner / Ry

- **Hosts and access:** Smaug and Rivendell are available to Ry, using SSH user `ry`. Ry confirmed unrestricted sudo on both.
- **Installation/configuration:** owner permits Python/dependencies, Docker, service accounts/containers, and project service configuration on these isolated VMs.
- **Existing workloads:** owner allocated both VMs to Ry. Since then, the separate static site has been deployed to Smaug; preserve it.
- **Network approach:** owner approved Tailscale/SSH, private MySQL access and outbound HTTPS to source/model/GitHub/package services. Actual policy/connectivity must still be verified.
- **Storage:** inspect available capacity; the answer did not establish backup coverage, persistence across rebuilds, or recovery procedures.

## Current deployment decision

App/orchestrator and MCP on Smaug; MySQL on Rivendell. Browser access initially through an SSH tunnel. Separate runtime identities/secret access are planned; no remote configuration has been applied by this project yet. Owner approval is not proof of a particular existing firewall or service configuration.

Rivendell output supplied by Ry: Ubuntu 24.04.5 LTS, 3.8 GiB RAM (3.4 GiB then available), 55 GiB then free disk. Refresh capacity and inspect Smaug before installation. These are non-AWS VMs on the owner's PC; S3/account permissions remain separate future questions.

Use the [deployment runbook](deployment-runbook.md) and [threat model](deployment-threat-model.md). Keep passwords, keys, private addresses and connection details outside public documentation, prompts and logs. No further owner confirmation is needed for the already authorized setup; inspect technical constraints and coordinate if requirements expand.
