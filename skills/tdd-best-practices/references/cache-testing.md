# Testing Cache Behavior

Source: lessons and counterexamples from [CodelyTV/infrastructure_design-cache-course](https://github.com/CodelyTV/infrastructure_design-cache-course), corrected for behavior-focused and concurrent tests.

## Contract Tests

Run the same cache-decorator contract against a fake and the real adapter:

- miss loads the source once, returns its result, and stores the encoded value with the configured TTL;
- hit returns the decoded value without calling the source;
- cached absence is distinct from miss, corruption, and adapter failure;
- equivalent identifiers and canonical queries share a key;
- different filter values, tenant/auth scopes, locales, pages, and schema versions do not collide;
- invalid payload/version is evicted and reloaded without exposing its contents.

Assert after Act with recording spies. Do not make `shouldSet()` call the mock during Arrange or put the only assertion inside `get()`/`set()`; those tests remain green when production omits the interaction.

## Time and Invalidation

Use a fake clock where possible and real disposable Redis for expiry semantics. Test just-before, exact, and just-after TTL boundaries without sleeps. For create/update/delete, prove every affected by-ID, secondary, and list entry is invalidated or generation-versioned only after the authoritative commit.

Exercise the race where a reader loads old source state while a writer commits and invalidates. Verify the chosen source-version/CAS/generation policy prevents stale repopulation. Test read-your-writes bypass separately when promised.

## Failure Tests

Inject cache connect, timeout, `GET`, decode, `SET`, and invalidation failures independently. For a performance cache, verify reads still use the source and a successful business write is not falsely reported as failed solely because cache maintenance failed. Verify metrics are emitted without payloads or sensitive keys.

## Concurrency and Capacity

Use barriers rather than sleeps to release many callers onto one missing key. Assert bounded source calls, lease expiry/recovery, non-owner behavior, and no unlock by a stale owner. Test TTL jitter deterministically through injected randomness. For local caches, verify maximum capacity, eviction, expired-entry cleanup, and isolation between requests/tenants.

## HTTP Tests

Test cache headers and validators at the real HTTP boundary: canonical payload changes alter ETag even with equal item count; matching validators return `304`; `Vary` covers representation dimensions; personalized or authorized responses are private/no-store unless explicitly isolated; shared caches never reuse one principal's response for another.

## Test Isolation

Use an isolated disposable Redis or a unique prefix per suite/worker. Clean only that prefix and close clients. Never run `FLUSHALL` against a potentially shared Redis. Include a test with the cache disabled to prove it remains an optimization rather than a hidden source of truth.

## Course Caveats

The course's cache doubles self-assert inside production calls and can produce false positives; its Redis test uses global `FLUSHALL`. It lacks regression tests for filter-value key collisions, invalidation, expiry, corruption, Redis outages, concurrent misses, ETag content changes, and personalized-response isolation.
