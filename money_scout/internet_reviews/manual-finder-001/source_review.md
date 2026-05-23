# Source Review: manual-finder-001

Generated At: 2026-05-19 16:24:54 -04:00

## Idea

Finder Fee Sourcing Concierge

## Source

Chris strategy signal plus local policy:

- FINDER_FEE_CONCIERGE_POLICY.md
- finder_fee_concierge_rules.json

## Model

Small upfront research fee plus 1 percent success fee if a transaction succeeds.

## Why Upfront Fee Exists

The upfront fee filters unserious, impossible, vague, or joke requests before Nova spends research time.

## Current Mode

simulation_only

## Allowed

- simulate buyer request intake
- score request seriousness
- research public seller availability
- estimate item value
- estimate upfront research fee
- estimate 1 percent success fee
- score fraud/platform risk
- prepare local match packet

## Blocked

- message buyer
- message seller
- collect payment
- buy item
- ship item
- guarantee item
- use credentials
- spend money
- post listing
- move marketplace users off-platform

## Recommended Next Step

Add this to the Nova work order and experiment plan as a simulation-only high-priority business lane.
