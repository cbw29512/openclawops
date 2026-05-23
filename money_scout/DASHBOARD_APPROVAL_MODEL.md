# Dashboard Approval Model

## Purpose

The dashboard should let Chris steer Nova without babysitting it.

## Buttons

### Boost +1

Means:
- increase priority_index by 1
- work harder locally
- improve artifact
- research adjacent angle
- prepare stronger review packet

Does not mean:
- publish
- sell
- outreach
- send messages
- spend money
- commit
- push

### Bury -1

Means:
- decrease priority_index by 1
- park or lower priority
- preserve for dedupe memory
- revive only if new evidence or Chris votes bring it back

## V1 Dashboard Rule

The dashboard may write only to:

- data/opportunity_index.json

V1 must not write to:

- live websites
- email systems
- GitHub
- payment systems
- affiliate links
- outreach queues

## Queue Logic

- active_positive: AI works hardest locally
- active_watch: AI watches lightly
- neutral_hold: AI waits
- idea_pit: AI parks
- deep_freeze: AI preserves only for memory
