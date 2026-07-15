# Introducing Domain Events into Legacy Code

Source: migration lessons and counterexamples from [CodelyTV/domain_modeling-domain_events-course](https://github.com/CodelyTV/domain_modeling-domain_events-course).

Introducing events changes coupling, timing, failure behavior, and often consistency. Treat it as an incremental behavior change, not a mechanical class extraction.

## Migration Sequence

1. Characterize the primary state change and every existing side effect.
2. Identify the business fact and give it a semantic past-tense name.
3. Introduce a narrow message port at an application seam with a recording fake or no-op adapter.
4. Record the fact at the Aggregate transition, or at the narrowest honest application seam when the model cannot yet change.
5. Keep primary persistence synchronous and unchanged.
6. Move one secondary reaction at a time into a directly tested subscriber.
7. Compare old and new paths before removing the direct call; dual-run only idempotent or safely suppressed effects.
8. Add transactional Outbox delivery before relying on subscribers for consistency.
9. Make consumers idempotent and prove retry/replay behavior.
10. Remove the old side-effect path only after parity and recovery are observable.

Use a recording Event Bus as a sensing seam: drive the legacy entry point, observe database/message/email outputs, and assert the new fact without changing its delivery timing prematurely.

## Preserve Semantics Deliberately

Moving a direct call to asynchronous delivery changes when errors reach the caller. Document whether the command can succeed while the reaction is pending or failed, and add monitoring/recovery before making that change.

Do not move the original Aggregate save into an ordinary subscriber. That changes the source-of-truth transaction and can acknowledge success before state is durable.

Do not dual-run payments, emails, inventory decrements, or other non-idempotent effects without a deduplication key and suppression strategy.

## Change Data Capture

Use CDC when the writer cannot be changed or as a migration/anti-corruption bridge. Map a specific table plus mutation action to a stable integration message.

CDC observes rows, not domain intent. A generic update may not reveal whether a user was archived, corrected, imported, or migrated. Compare old/new values when available, version mappings with schema evolution, preserve stable message identity across retries, and require idempotent consumers.

Prefer an application-recorded Outbox once the writer can be modified. Do not rename raw row mutations as Domain Events indefinitely.

## Red Flags

- Big-bang event-driven rewrite.
- Event Bus injected into Entities or static publication from constructors.
- Event created manually in every use case after the transition.
- Primary persistence implemented as a derived subscriber action.
- Synchronous failures silently becoming eventual consistency.
- Old and new non-idempotent side effects running together.
- CDC contracts coupled directly to unstable table schemas.
