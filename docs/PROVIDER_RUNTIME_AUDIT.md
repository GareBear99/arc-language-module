# Provider Runtime Audit

This version adds a provider registry, health snapshots, and job receipts.

## Core ideas

- Registry truth: what providers are known and enabled
- Health truth: latest observed provider status
- Receipt truth: every runtime translation/speech request stores request + response payloads

## Policy

- Offline providers are blocked
- Degraded providers remain usable but are marked degraded
- Unregistered providers are not considered healthy runtime targets
- Local seeded graph translation can still run without an external provider
