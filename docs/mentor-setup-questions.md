# VM Deployment Questions

The app currently runs locally: Python serves the browser interface and orchestrates model/MCP calls; MySQL 8.4 runs in Docker. App and database together on the new VM remain preferred. MySQL setup on that VM is already approved; VM readiness and the remaining deployment details are unconfirmed.

## VM availability and access

- Is the new VM ready, and which VM should I use for the application and database?
- Will the VM be dedicated to this project or shared with other users/services?
- What are its Linux distribution/version, CPU allocation, RAM, and available disk space?
- Could you provide its Tailscale MagicDNS hostname and SSH access instructions through our usual private channel?

## Installation and isolation

- May I run the Python app and MySQL together on the new VM, and do you prefer containers or native services?
- May I install Python and dependencies, create the project directory, and configure the app to run as a service?
- May I create separate OS users or appropriately isolated containers for the app/orchestrator, MCP server, and import/admin tasks so they do not share access to all credentials?
- Will I have sudo access, or should I coordinate installations, service configuration, and permission changes with you?
- Which existing services, data, directories, ports, or credentials must I leave untouched?
- May I use VS Code Remote-SSH, which installs server components on the VM?

## Network and browser access

- Is outbound HTTPS allowed to CollegeFootballData, the OpenAI model API, and GitHub, plus the package registries needed to install dependencies?
- For the initial browser UI, should we keep it on the VM's localhost and reach it through an SSH tunnel over Tailscale, or do you want direct tailnet access?
- If direct tailnet access is preferred, who should have access, and what authentication, HTTPS/reverse-proxy, firewall, and Tailscale policy requirements should we follow?
- Can MySQL remain private to the VM or container network, without publishing its database port to the tailnet or internet?

## Operations and sharing

- Will the project files, original import archives, database storage, and secret files persist across VM restarts or rebuilds, and where should they live?
- Who should handle backups, restore testing, updates, and recovery, and are there existing tools or policies I should use?
- What CPU, memory, storage, model-API spending, uptime, and cleanup limits should I plan around, and who owns any associated costs?
- Are there restrictions on publishing sanitized project code, screenshots, architecture notes, or deployment documentation, including hostnames or infrastructure details?
- If the new VM is delayed, is deployment to the original VM permitted, and what additional restrictions would apply there?

## Once the answers are available

- Confirm the authorized target and inspect its configuration with read-only commands before installing anything.
- Agree on service identities, secret storage, network exposure, persistence, and recovery before deployment.
- Keep credentials and private infrastructure details outside Git, prompts, and logs; use a private channel for access details.
- Treat the new VM as unavailable until Ry confirms readiness. No remote deployment or message to the mentor has been performed by Codex.
