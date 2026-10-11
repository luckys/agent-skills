# Retry and Compatibility Contracts

Use when clients retry writes, an operation crosses a remote provider, or a published API is evolving.

## Idempotency is a stored contract

Document which operations are safe to retry, what constitutes one intent, how keys are scoped, and how long replay is guaranteed. A random UUID generated once for an intent is valid; generating it for every attempt is not. Two legitimate identical purchases must remain distinct intents.

Bind a key to the authenticated actor/tenant, operation, and normalized request. Define normalization so omission, defaults, and ordered data are interpreted consistently. Authenticate and authorize replay as well as the initial request; a key must not grant access to another actor's result.

Use an atomic unique claim or equivalent mechanism. Define the same-key/different-payload error in the existing API convention. Choose the in-flight duplicate response deliberately: conflict with retry guidance, bounded waiting, or accepted with a status resource. Preserve the project's status codes rather than silently importing an upstream choice.

For local effects, commit the result and replay record atomically. For external effects, persist intent and reuse the provider's deduplication mechanism where supported. A timeout does not show whether the effect happened: keep the same intent and reconcile it instead of issuing a new key automatically. Do not promise retry safety an upstream provider cannot deliver.

Retention must cover the documented retry/replay paths. Explain behavior after expiry; a short cache TTL is not a complete payment guarantee. Test payload conflicts, concurrent duplicates, unknown outcomes, authorization on replay, and expiry with the real storage adapter.

## Observable behavior can be compatibility

Before changing an endpoint, inventory consumers and wire-level assumptions: missing versus null fields, enum values, ordering, normalization, error codes, pagination, and undocumented behavior used by clients. Optional fields are additive only if actual readers tolerate them.

Prefer compatible extension when it works. Otherwise version and stage the migration according to the existing public contract. An ideal of one active version does not override a compatibility promise. Consumer examples and contract tests should cover the risky assumptions.

## Sources and adaptation

Adapted from Addy Osmani's `api-and-interface-design` and `deprecation-and-migration`, with pstack's idempotency and caller-migration principles. Existing task endpoints, error formats, and versioning remain authoritative. See [third-party-notices.md](third-party-notices.md).
