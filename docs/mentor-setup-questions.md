# VM Deployment: Five Questions

The app works locally. For the first VM deployment, I propose running the Python app and MySQL together, keeping MySQL private, and accessing the browser UI through an SSH tunnel over Tailscale.

- **Which VM should I use, and is it ready?** Please send its MagicDNS hostname and SSH access instructions through our usual private channel.
- **What am I allowed to install and configure?** Can I install Python/dependencies and Docker, run the app and MySQL, and create separate service users or containers? Will I have sudo access, or should I coordinate those changes with you?
- **Is the VM dedicated or shared, and what must I leave untouched?** Any existing services, data, directories, or ports to avoid?
- **Is the proposed network setup okay?** Browser access through an SSH tunnel over Tailscale, MySQL private to the VM/container network, and outbound HTTPS to OpenAI, CollegeFootballData, GitHub, and package registries.
- **Where should persistent project/database data live, and is it backed up?** Any storage limits or cleanup expectations I should know about?

## Details we can resolve as we go

After access is confirmed, inspect the OS, CPU, RAM, disk, and existing configuration with read-only commands. Work out service configuration, credential isolation, backup/restore procedures, and maintenance within the permissions granted above. Ask separately before installing optional VS Code Remote-SSH server components, expanding network exposure, or publishing private infrastructure details.

The new VM remains unavailable until Ry confirms readiness. MySQL setup on that VM was previously approved; other changes still depend on the agreed scope. Keep credentials outside Git, prompts, and logs.
