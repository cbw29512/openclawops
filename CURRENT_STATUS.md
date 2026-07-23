# Public Project Status

This repository contains public-safe source and documentation for a local automation workspace.

Live service status, installed model names, scheduled-task details, local paths, account information, and deployment configuration are intentionally excluded from this public document.

Operational status belongs in an ignored local file such as `CURRENT_STATUS.local.md`.

## Current development goal

Maintain a repeatable local workflow that:

1. reads approved local state;
2. reviews the task queue;
3. prepares safe proposed actions;
4. sends risky actions through an explicit approval gate;
5. records an operator-visible audit trail; and
6. generates a local status report without publishing private runtime data.
