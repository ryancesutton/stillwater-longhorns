# VM Setup Questions for Mentor

Draft message to send when the mentor responds; no message has been sent by Codex.

> Thanks for helping with the VM. Has the new one been stood up yet? If it is ready, could you send the MagicDNS hostname and SSH access instructions through our usual private channel?
>
> I’m planning to run the Python app and MySQL together. You’ve approved MySQL setup on the new VM; may I also install Python and dependencies, create a project directory and separate service users, and run the application? Would containers be permitted if needed? Will I have sudo access, or should I coordinate administrative changes with you?
>
> Are there existing services, data, or credentials I should leave alone? Is outbound HTTPS to CollegeFootballData, the model API, and GitHub allowed? May I use VS Code Remote–SSH, which installs server components?
>
> Is storage persistent, and who handles backups, recovery, cleanup, and any resource limits? Are there restrictions on publishing sanitized code and project documentation?
>
> If the new VM isn’t available, would running the app on the original VM be permitted, and under what restrictions? Our current demo uses a terminal over SSH, so it doesn’t need a public website or inbound web port.

## Checks Once Access Is Available

- Inspect Linux distribution, CPU, RAM, and free disk with read-only commands.
- Confirm which host is authorized and whether it is dedicated or shared.
- Confirm MySQL version, installation method, database location, and isolation before setup. App and database together remain preferred; a split deployment requires a separately reviewed connection plan.
- Keep credentials and private infrastructure details outside Git, prompts, and logs.
- Treat the new VM as unavailable until the project owner explicitly reports readiness. Continue local development meanwhile.
