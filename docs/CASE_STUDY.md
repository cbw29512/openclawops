# OpenClawOps Case Study

## Executive summary

OpenClawOps is a local-first supervised automation workspace designed to let an AI system research, score, prepare, audit, and improve work continuously without gaining permission to publish, spend, perform outreach, use credentials, commit code, push changes, or modify live systems.

The project demonstrates a governance-first approach to AI operations: visible queues, explicit approval semantics, local evidence, stop conditions, quality thresholds, and human authority over every external or risky action.

## The problem

A continuously running local AI can create value by reviewing sources, organizing ideas, improving drafts, and preparing recommendations. It can also create risk when “work harder” is confused with “take action.”

The central product problem was not simply automation. It was creating a system that could:

- stay productive locally
- show Chris what it was doing
- learn from outcomes
- prioritize stronger ideas
- preserve evidence and audit history
- stop when health or evidence failed
- never convert local confidence into external permission

## Constraints

- The workspace must remain local-only.
- External actions must default to disabled.
- Dashboard v1 may write only to `data/opportunity_index.json`.
- Boost and Bury may change local priority only.
- Publishing, spending, outreach, credentials, Git, and live changes require Chris.
- Missing or malformed reports must not crash the command center.
- Public-facing drafts must not expose internal AI workflow language.
- Quality scores may trigger local regeneration, never external release.
- Repository validation must not execute preserved operational scripts.
- The repository is a pre-reinstall snapshot; runtime services must not be claimed as currently active.

## Solution

### Local command center

A FastAPI dashboard provides a single local view of:

- current cycle and health state
- enterprise audit counts
- work orders
- source-review queues
- simulation attempts
- learning patterns
- activity events
- candidate review
- Boost and Bury controls

The dashboard binds to `127.0.0.1:8788` and reads local JSON reports and registries.

### Approval model

The approval model separates intent from authority.

**Boost +1** means:

- increase local priority
- research adjacent angles
- improve the artifact
- prepare a stronger review packet

It does not mean publish, sell, contact anyone, spend money, commit, push, or modify a live system.

**Bury -1** means:

- reduce priority
- park the idea
- preserve it for deduplication and future evidence

It does not mean destructive deletion.

### Local operating loop

The saved PowerShell workflows coordinate local cycles for source health, idea discovery, deduplication, opportunity indexing, artifact preparation, enterprise audits, reports, simulations, experiments, and learning ledgers.

The local model/gateway layer was designed to consume this context and prepare next actions. External execution remains outside the autonomous loop.

### Quality and public-page gates

Saved policy data requires minimum scores for quality, SEO, code, mobile experience, and trust. Candidates may be regenerated locally when they fail.

A separate public-page cleanliness policy prevents visitor-facing pages from exposing terms such as internal role names, draft workflow labels, or regeneration instructions. It also requires mobile and trust markers.

### Observable activity

The dashboard includes a live activity feed so Chris can see the system's current micro-task and cycle events without exposing private chain-of-thought.

### Static showcase validation

The repository now includes a machine-readable showcase contract and validator. CI checks the policy and code snapshot without running operational automation.

The validator confirms:

- required files exist
- local-only is true
- external, spending, outreach, and publishing flags are false
- approval language still blocks risky actions
- Dashboard v1 remains limited to the opportunity index
- quality thresholds are not weakened
- dashboard safety markers remain present

## Key decisions

| Decision | Reason | Tradeoff |
|---|---|---|
| Local-first operation | Keeps research and preparation private and inexpensive | Remote control and cloud scaling are not provided |
| Human approval for external actions | Prevents local priority from becoming permission | Chris remains in the final execution loop |
| Boost/Bury instead of execute buttons | Provides steering without unsafe autonomy | Dashboard actions intentionally feel limited |
| JSON reports and registries | Easy to inspect, back up, and audit | Requires corruption detection and schema discipline |
| Separate internal and public-page policies | Protects visitor experience from workflow leakage | Adds another gate to candidate review |
| Quality thresholds before review | Reduces weak candidates reaching Chris | Scores do not replace human judgment |
| Stop conditions | Prevents repeated or conflicting failures from compounding | Automation pauses rather than forcing progress |
| Static CI validation | Proves policy drift and syntax safely | Does not prove Windows scheduled tasks currently run |
| Snapshot labeling | Preserves truth after reinstall | The repository cannot claim current runtime availability |

## Evidence

The saved system manifest records:

- local-only enabled
- external actions disabled
- spending disabled
- outreach disabled
- publishing disabled
- required scripts present at backup time
- required data registries present at backup time
- required policy files present at backup time
- an explicit warning against copying credentials or account sessions

The dashboard state code also returns all external-action safety flags as false and restricts local voting to validated item IDs and two vote values.

The NothingButA quality policy blocks publication, domains, ads, affiliate links, lead capture, commits, and pushes before approval.

Repository CI adds fresh evidence by:

- compiling dashboard Python code
- validating the machine-readable showcase contract
- uploading a sanitized validation report
- auditing dashboard Python dependencies
- avoiding all operational PowerShell execution

## Security posture

Current design controls include:

- localhost dashboard binding
- explicit action allow/block policy
- human approval boundary
- local-only priority mutation
- input validation for voting
- safe empty/error fallback states for dashboard reports
- quality and trust thresholds
- public-page cleanliness gates
- stop-and-escalate conditions
- credential and secret exclusion rules
- non-executing repository validation

The preserved dashboard was not designed for public internet exposure. Authentication, authorization, CSRF protection, rate limiting, TLS, session management, and path/config portability would be required before any remote deployment.

## Business and customer value

OpenClawOps demonstrates how I approach customer-facing AI automation:

- define exactly what the AI may and may not do
- distinguish recommendations from authorization
- give operators visible state and steering controls
- keep risky actions behind human approval
- use audits, quality gates, and stop conditions
- preserve local evidence and learning data
- explain stale snapshot versus live runtime honestly
- validate governance drift without starting the operational system

These patterns apply directly to AI operations, solutions consulting, implementation, technical account management, governance, and responsible automation roles.

## Current status

Preserved and documented:

- local operating policies
- FastAPI dashboard
- local priority voting
- activity visibility
- quality and cleanliness gates
- candidate review code
- PowerShell operating scripts
- data contracts and system manifest
- showcase validation and CI

Not claimed as currently active:

- OpenClaw gateway
- Ollama or the saved model
- Windows scheduled tasks
- hourly cycles
- current local reports
- publishing or monetization
- external action execution

## Interview walkthrough

1. Start with the approval policy and explain the external-action boundary.
2. Show the dashboard state model and local-only safety flags.
3. Explain Boost/Bury as steering rather than execution.
4. Show the activity feed and visible work queues.
5. Show quality and public-page policies.
6. Show the system manifest and replication warning.
7. Run `scripts/validate_showcase.py` and show that runtime execution is false.
8. Explain why the repository is labeled as a preserved snapshot instead of a currently running service.
