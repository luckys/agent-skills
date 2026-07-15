# Cache Design

Source: [CodelyTV/infrastructure_design-cache-course](https://github.com/CodelyTV/infrastructure_design-cache-course), corrected for invalidation, privacy, failure, concurrency, and test semantics.

A cache is a derived copy, not the source of truth. Add it only after measuring the bottleneck and define acceptable staleness, ownership, invalidation, failure behavior, and removal criteria before implementation. Hit rate alone is not a success metric: compare end-to-end latency, source load, cache cost, and correctness incidents.

## Choose the Layer

| Layer | Appropriate when | Main risk |
|---|---|---|
| HTTP/browser/CDN | A representation is safely reusable under HTTP semantics | Private or personalized data leaks |
| Application query | The expensive result combines multiple sources | Policy leaks into orchestration |
| Repository decorator | Repeated repository reads share one cache policy | Stale Aggregates or unbounded query keys |
| Process-local | Tiny bounded hot set and per-process inconsistency is acceptable | Memory growth and divergent replicas |

Do not default to repository caching before checking indexes, query plans, pagination, read models, materialized views, or HTTP caching. Multiple cache layers are valid only when their keys, privacy rules, freshness budgets, and invalidation order are designed together. The longest outer TTL bounds visible staleness even if an inner Redis entry expires sooner.

HTTP validators, `Cache-Control`, `Vary`, authorization, `304`, and CDN behavior belong to REST/API policy. Never mark authenticated, tenant-specific, or personal data as shared-cacheable unless the cache key and authorization model prove isolation. Do not strip cookies or credentials generically to force a cache hit.

## Cache-Aside

Read with one `GET`; `EXISTS` followed by `GET` adds latency and races expiration.

```typescript
async search(id: PostId): Promise<Post | null> {
  const key = postKey(id);
  try {
    const cached = await this.cache.get(key);
    if (cached !== null) {
      try {
        return decodePost(cached);
      } catch (error) {
        this.metrics.cachePayloadInvalid(error);
        await this.cache.delete(key).catch(() => undefined);
      }
    }
  } catch (error) {
    this.metrics.cacheReadFailed(error);
  }

  const post = await this.source.search(id);
  if (post !== null) {
    try {
      await this.cache.set(key, encodePost(post), ttlWithJitter(60));
    } catch (error) {
      this.metrics.cacheWriteFailed(error);
    }
  }
  return post;
}
```

For ordinary performance caches, reads should usually fail open to the authoritative source with short timeouts and a circuit breaker. Security decisions, authorization, idempotency, locks, and correctness-critical state are not ordinary caches; do not silently fail open there.

Negative caching can protect the source from repeated misses, but use a distinguishable sentinel, short TTL, and invalidation on create. Never confuse cached absence, corrupted data, and Redis failure.

## Keys and Payloads

A production key should encode:

```text
<app>:<env>:<bounded-context>:<resource>:<schema-version>:<tenant/auth-scope>:<canonical-identity>
```

- Use primitive canonical values, not Value Object instances as `Map` keys.
- Canonicalize equivalent query filters, ordering, pagination, locale, feature flags, and authorization scope.
- Hash long non-sensitive canonical material. For sensitive or low-entropy values, prefer opaque identifiers or a versioned HMAC with a protected, rotatable key; a plain deterministic hash does not hide PII.
- Include a schema version so incompatible payloads cannot be reconstituted accidentally.
- Validate decoded payloads. On corruption or unknown schema, record a redacted metric, delete only that key, and treat it as a miss.
- Cache DTO/primitives, not live mutable Aggregate instances or ORM entities.

Arbitrary filtered lists are cacheable only when reuse justifies their key cardinality and invalidation has a concrete design. Prefer by-ID entries when possible. For list caches, use bounded dimensions plus collection versioning, tags, or explicit dependency tracking; TTL alone is an accepted-staleness policy, not invalidation.

## Write Ordering and Invalidation

Cache and database writes are a distributed dual write. Neither sequential write-through nor `save(); delete()` is atomic by itself.

Common default:

1. Commit the authoritative database write.
2. Invalidate affected keys after commit.
3. Treat invalidation failure as observable degraded freshness and repair/retry it.

This still has races: a concurrent miss can read old database state and populate it after invalidation. Choose a correction according to the freshness requirement. An Outbox makes invalidation delivery durable, but does not close this race by itself:

- versioned keys or generation counters;
- compare-and-set using source versions;
- durable invalidation events through an Outbox, combined with generations/CAS or repeated/delayed invalidation;
- short TTL as a bounded fallback;
- bypass cache briefly after writes when read-your-writes is required.

Write-through means updating the cache after the source write; invalidation means deleting/advancing affected entries. They are different strategies. A successful DB write followed by Redis failure must not be reported as if the business write failed unless the API explicitly models that ambiguous partial outcome.

Write-behind is durable asynchronous persistence only when the write queue itself is durable, ordered as required, retryable, and observable. A volatile cache that later flushes business data can lose acknowledged writes and is not acceptable for critical state.

## Stampede and Capacity

Concurrent misses can overload the source. Use one or more of:

- in-process request coalescing for one instance;
- distributed lease/single-flight with owner token, short expiry, and safe release;
- stale-while-revalidate or stale-if-error where stale data is acceptable;
- proactive refresh for a small known hot set;
- TTL jitter to avoid synchronized expiry.

Never hold an unbounded lock while loading. Clients that lose the lease should wait briefly, serve allowed stale data, or fall back according to policy.

Every local cache needs maximum entries/bytes, an eviction policy, expiry cleanup, and lifecycle behavior across deploys. A module-global object with lazy expiry is unbounded and differs across serverless instances and replicas.

## Redis Operations

- Configure endpoint, authentication/TLS, connect and command timeouts, bounded retries, and error listeners.
- Reuse a managed client, but close it during application/test shutdown.
- Namespace every environment and test worker.
- Never use `FLUSHALL` against a shared instance; delete only keys owned by the test namespace or use an isolated disposable Redis.
- Avoid production key scans for invalidation; maintain tags/generations or a known key set.
- Do not log cached payloads, raw sensitive keys, credentials, or full deserialization errors containing data.

## Observability and Review

Measure per cache and operation:

- hit, miss, negative-hit, stale-served, and bypass rates;
- hit/miss/source latency and timeout/error rates;
- evictions, memory, key cardinality, and oldest refresh age;
- coalesced loads, lease contention, and source amplification;
- invalidation failures and schema/corruption misses.

Review checklist:

- Is the source of truth explicit?
- Is acceptable staleness defined per use case?
- Do keys include schema and tenant/authorization scope?
- Can every mutation identify or version all affected entries?
- What happens when cache read, population, or invalidation fails?
- Is stampede bounded and capacity limited?
- Are outer HTTP/CDN TTLs consistent with inner caches?
- Can the cache be disabled safely and the client closed cleanly?

## Course Caveats

The course is a progression of educational snapshots, not production-ready cache infrastructure. Do not copy its ETag over `object.join()`, cookie stripping, unbounded controller object, raw `Criteria.toString()` keys, `EXISTS` plus `GET`, forced `null` casts, missing invalidation, fixed TTLs, `FLUSHALL`, or self-asserting test doubles. Its final decorator usefully demonstrates separation from the source repository, but it caches arbitrary query results without a consistency strategy.
