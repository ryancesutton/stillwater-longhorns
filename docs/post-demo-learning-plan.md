# Post-Demo Learning and Security Engineering Plan

Prepared November 2, 2026 for Ry to review. This is a proposed next-phase plan, not a record of completed controls or authorization for remote/cloud changes. Refine it when the mentor clarifies the potential team's duties and VM setup.

## Objective

Use the working Longhorns app to move from explaining security concepts to independently implementing, testing, operating, and evaluating controls. Keep learning depth, product improvements, and infrastructure practice as distinct session goals. Avoid adding features simply to fill time while deployment answers are pending.

The project already offers relevant practice in least privilege, parameterized queries, transactions, provenance, restricted model tools, evidence handoff, negative testing, and communication. The next gaps to address are threat modeling, Linux/process isolation, credential lifecycle, vulnerability management, detection, and recovery.

Current model and database tests establish behavior on tested cases, not general security or job readiness. The latest writer prompt received a live factual spot check and the existing tests; earlier live injection/missing-statistics evaluations predate that prompt revision.

## Phase 1: Consolidate the Current System

**Initial estimate:** 5–8 hours of focused review over one or two weeks, alongside 4–6 hours of small hands-on exercises. Adjust based on demonstrated understanding; these hours are not a job-readiness guarantee.

1. Trace one live briefing and one import end-to-end using the code and [architecture review](glass-to-metal-review.md).
2. Revisit the distinctions that need precision:
   - Model proposal versus application-controlled execution and MCP dispatch.
   - Tool results versus model responses; two roles versus multiple API turns.
   - Authentication, authorization, and cross-site request protection.
   - Database grants versus view definitions; validation versus parameterization.
   - Minimal environment versus OS isolation.
   - Citation linkage versus factual support; hashing versus source/transformation correctness.
   - Repeatable dataset identities versus new import history; rollback versus uncertain commit outcomes.
3. Move beyond repeated recall. For each selected boundary, Ry should:
   - Explain it without reading the presentation script.
   - Locate its implementation, using documentation freely.
   - Predict what happens when it fails or is bypassed.
   - Make a small change and inspect the diff.
   - Produce meaningful evidence that permitted and denied behavior work as intended.
4. Track progress as **introduced → explained → demonstrated → independently applied**, with evidence. A correct verbal answer alone does not establish independent implementation skill.

A useful first exercise is adding a meaningful malformed-tool-argument case, predicting the rejection point, and verifying that dispatch never occurs. Use dummy secrets and disposable fixtures; do not break the working database or expose real credentials for exercises.

## Phase 2: Threat Model and Prioritize Risks

**Next session proposal:** about 90 minutes of targeted review, then draft a one-page threat model and implement one denial test with Ry driving the change. Completing the exercise may require another session.

- Identify assets: credentials, dataset integrity, private configuration, model spending, generated output, and availability.
- Identify actors and entry points: browser callers, imported source text, model responses, tool results, dependencies, local processes, and future remote users.
- Mark trust boundaries and permitted actions using the actual code, not only intended architecture.
- Rank five plausible abuse cases by impact and likelihood, noting assumptions and existing controls.
- Select one risk for mitigation and define how success and failure will be verified.

Deliverables: a small threat model, prioritized risk register, and a tested change. A risk entry should include affected assets, attack path, existing control, remaining exposure, owner, next action, and evidence.

## Phase 3: Strengthen Foundations and Operations

The order below is a priority guide, not a requirement to finish every topic before learning the next. Continue small explain → try → inspect → verify → review diff → commit loops.

| Priority | Topic | Practical exercise / evidence |
| --- | --- | --- |
| First | Linux and process isolation | Understand users/groups, file permissions, process ownership, services and container mounts; demonstrate that one service identity cannot read another's dummy secret. |
| First | Credential lifecycle | Rotate a disposable DB credential, verify the old credential fails, update its consumer, and document recovery without printing secrets. |
| Next | Web/API security | Deepen HTTP, origins, sessions, CSRF, XSS, authorization and TLS; inspect requests and directly test denied requests against the local app. |
| Next | Secure development and vulnerability management | Add suitable automated checks, investigate a dependency finding for actual relevance, remediate it, and verify the fix. |
| Next | Detection and response | Choose useful sanitized security-event categories and rehearse a suspected key exposure; decide how to detect, contain, revoke, recover, and document it. |
| Next | Backup and recovery | Restore a backup into a disposable database and verify counts, relationships and source traceability. |
| Throughout | Agent security evaluations | Expand injection and tool-result-tampering cases, resource-exhaustion checks, factual evaluations, and regression checks after prompt/model/tool changes. |

Keep these distinctions explicit:

- Metadata logs help explain executions; they are not automatically a detection/alerting capability.
- Pinned dependencies and passing tests are not a vulnerability-management process.
- Separate DB identities do not isolate same-user processes or secret files.
- A security finding is not finished until it is prioritized, addressed or consciously accepted, verified, and communicated.
- Learn Python error handling, async control flow, context managers and tests through these exercises; connect them to familiar Java/MySQL patterns rather than memorizing SDK internals.

## Deployment Decision Point

If VM answers arrive, use [mentor setup questions](mentor-setup-questions.md) to confirm the authorized host, resources, installation permissions, identity isolation, networking, browser access, persistence and recovery before changes. The new VM remains unavailable until Ry confirms readiness. App and MySQL together remain preferred; final topology is unconfirmed.

If answers do not arrive, continue local review, threat modeling, disposable tests, dependency investigation and recovery planning. Do not treat the delay as permission to use the original VM or another account.

## Later Extension A: Private S3 Import Archives

S3 is a phase-two infrastructure exercise, not a prerequisite for the app. Original import archives provide a concrete use case.

Before implementation:

- Confirm whose AWS account is authorized, ownership, budget, cleanup and data-use constraints.
- Introduce IAM identities, role trust, permission policies, temporary credentials and denied-access testing before uploading data.
- Choose authentication deliberately: the friend's VM is outside AWS, so an EC2 instance role cannot simply be assumed available.
- Design private storage, Block Public Access, narrow resource permissions, encryption requirements, audit visibility, retention/versioning and recovery.
- Verify permitted archive access and denied public/unrelated access; never upload credentials or silently redistribute raw CFBD data.

Keep RDS, Athena, cross-account architecture and infrastructure-changing agents deferred unless separately justified and approved within the task scope.

## Later Extension B: Web-Assisted Alias Checks

Ry’s stated feature priority after deployment/security work is exploring live alias checks. Current aliases remain reviewed static configuration; no runtime web capability has been added.

Before enabling lookup, threat-model the new untrusted input and tool surface. Decide allowed sources, request/size/time limits, source references, ambiguity handling, what may be persisted, and which changes require human review. The model may propose an identity; application code must still map it to permitted imported records. Never let downloaded instructions grant tools, credentials or write access.

Develop representative success, ambiguity, poisoned-source and no-result cases before treating the feature as reliable. Further product features remain deferred.

## Documentation Improvements to Make Incrementally

- Establish one authoritative current-state summary and clearly label historical checkpoints.
- Consolidate diagrams: the older project-outline diagram can imply direct research-to-MCP/writer communication; the detailed review correctly places application validation and evidence handoff between them.
- Add the competency tracker and risk register described above.
- Build a concise operational runbook for startup, shutdown, rotation, backup/restore and suspected compromise.
- Prefer clear planned/implemented/tested status and linked evidence over repeatedly appending conflicting progress notes.

## Career Alignment and Scope

This plan is most directly aligned with application security and AI-agent security engineering. Current role examples include design reviews, code review, security automation, vulnerability management and incident support; agent-specific work adds delegated identity, sandboxing and untrusted tool outputs. Some researched postings are senior roles: use their duties to understand the work, not as an immediate hiring checklist or a promise of readiness in six months.

Ask the mentor which responsibilities will dominate the potential role: application security, infrastructure security, detection/response, or building security automation. Adjust later exercises accordingly. Continue producing small, reviewable engineering artifacts rather than collecting technologies without a purpose.

## Research References

Reviewed November 2, 2026. Job listings and product guidance can change. Use these as references and verify details when applying them.

- [NIST NICE Framework Resource Center](https://www.nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center): cybersecurity work, knowledge, skills and role-based learning.
- [OpenAI application security role](https://openai.com/careers/security-engineer-application-security-seattle/): examples of secure design, assessment, automation, vulnerability management and incident support duties.
- [Anthropic agent-focused application security role](https://job-boards.greenhouse.io/anthropic/jobs/4502508008): examples of agent boundaries, delegated credentials, sandboxing and security automation; a senior-role example, not an entry-level baseline.
- [OWASP ASVS](https://asvs.owasp.org/): use selected verification requirements as a learning checklist, not a claim of compliance.
- [OWASP LLM risks](https://genai.owasp.org/llm-top-10/) and [agentic application guidance](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/): risk categories for expanding model/tool functionality.
- [AWS IAM security practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) and [S3 security practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html): identity and private-storage considerations for the later cloud exercise.
