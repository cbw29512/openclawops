# Replication Policy

## Purpose

If Nova Money Scout starts earning money, Chris may replicate the system on other machines.

Replication must be controlled, repeatable, and safe.

## Repeatable System Parts

These can be replicated:

- scripts
- policies
- schemas
- local reports
- source-review workflow
- artifact factory
- opportunity index model
- learning ledger model
- budget simulation model
- dashboard model

## Machine-Specific Parts

These must be regenerated per machine:

- scheduled task registration
- local paths
- machine identity
- gateway port status
- installed model list
- heartbeat status
- environment checks

## Never Copy Blindly

Do not blindly copy:

- credentials
- API keys
- payment methods
- browser sessions
- cookies
- personal account tokens
- affiliate credentials
- email sending credentials
- live production deployment secrets

## Replication Stages

1. Export safe system pack
2. Install prerequisites
3. Restore policies and schemas
4. Register scheduled task
5. Run source health
6. Run enterprise audit
7. Run one manual ops cycle
8. Confirm no external actions enabled
9. Only then allow normal local operation

## Success Criteria For A New Machine

A replicated machine must show:

- gateway healthy
- scheduled task registered
- latest ops cycle pass
- enterprise audit pass
- memory pack present
- safety flags locked
- no real spending enabled
- no outreach enabled
- no publishing enabled

## Scaling Rule

Do not run multiple machines against the same external accounts or outreach channels until dedupe, budget, compliance, and sending limits are centrally coordinated.
