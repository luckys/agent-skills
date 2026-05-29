# Cache

Source: CodelyTV/infrastructure_design-cache-course

> "Caches are a patch, but a patch in the right place improves the performance and maintainability of your application." — Codely

## General Principle

Cache is a performance optimization, not an architectural decision. Apply it after measuring, remove it when the root cause is fixed. Never use cache to mask a slow query that should be fixed at the DB or schema level.

---

## Cache-Aside (Lazy Loading)

**Intent:** Load data from the source on a cache miss and populate the cache for subsequent reads.

**How it works:** On `find()`, check the cache first. On a hit, return the cached value. On a miss, query the database, store the result in cache with a TTL, and return it. The application code manages both the cache and the source of truth.

**When to use:**
- Read-heavy workloads where the same data is requested many times
- Data that changes infrequently (user profiles, product details, configuration)
- When you can tolerate slightly stale data for the TTL duration

**When NOT to use:**
- Write-heavy data that changes on almost every read (cache hit rate will be too low to matter)
- Data that must always be fresh (financial balances, inventory counts)
- As a substitute for a proper index on the database

**Practical heuristic:** If cache hit rate is below 80%, the cache is not helping. Either increase the TTL, reconsider what you cache, or fix the underlying query instead.

**Example:**
```typescript
// CachedPostRepository.ts — cache-aside in the repository
export class CachedPostRepository implements PostRepository {
  constructor(
    private readonly wrapped: PostgresPostRepository,
    private readonly cache: Cache,
  ) {}

  async search(id: PostId): Promise<Post | null> {
    const cacheKey = `post:${id.value}`;
    const cached = await this.cache.get(cacheKey);
    if (cached) {
      return Post.fromPrimitives(cached);
    }
    const post = await this.wrapped.search(id);
    if (post) {
      await this.cache.set(cacheKey, post.toPrimitives(), { ttl: 60 });
    }
    return post;
  }
}
```

---

## Cache at Controller vs Use Case vs Repository

**Intent:** Choose the right layer for caching to maximize reuse and minimize coupling.

**How it works:**
- **Controller-level cache** (HTTP caching): `Cache-Control` headers let the browser or CDN cache responses. Zero application code needed. Works for public, stateless GET endpoints.
- **Use-case-level cache**: Cache the result of the entire use case. Useful when the response aggregates data from multiple repositories.
- **Repository-level cache** (recommended): Cache individual aggregate lookups. The cache key is the aggregate ID. Reusable across multiple use cases that load the same aggregate.

**When to use:**
- HTTP caching: public read endpoints (product listings, static content)
- Repository cache: aggregate-by-ID lookups shared across use cases
- Use-case cache: rarely — only when the assembled response (not the raw data) is expensive to produce

**When NOT to use:**
- Cache writes (mutations) — always invalidate or write-through on writes
- Cache at multiple layers for the same data simultaneously (leads to inconsistency between layers)

**Practical heuristic:** Cache at the repository level by default. Move to HTTP caching for public endpoints. Only cache at the use case level if the assembly step itself is the bottleneck.

---

## Write-Through Cache

**Intent:** Update the cache immediately on every write, keeping cache and source in sync.

**How it works:** On `save()`, write to the database AND update (or invalidate) the cache in the same operation. Subsequent reads always find fresh data in cache.

**When to use:**
- Data that is read frequently immediately after being written (e.g., a user's profile after editing it)
- When stale reads are unacceptable

**When NOT to use:**
- Data that is written frequently but read rarely (you pay cache write cost for no read benefit)
- When cache consistency across nodes is hard to guarantee (prefer invalidation over write-through in distributed caches)

**Practical heuristic:** Write-through is simpler to reason about than invalidation. Start with invalidation-on-write (delete the cache key on save); upgrade to write-through only if you see cache miss storms after writes.

---

## Write-Behind (Write-Back) Cache

**Intent:** Write to the cache immediately and flush to the database asynchronously.

**How it works:** Writes go to the cache first; a background process flushes dirty cache entries to the database. Reads see up-to-date data from cache. The database may lag behind.

**When to use:**
- Very high write throughput where DB latency is the bottleneck
- Batch write scenarios (analytics counters, view counts)

**When NOT to use:**
- Any data where loss of a cache flush (process crash before flush) is unacceptable
- Financial or transactional data
- When you need immediate DB consistency

**Practical heuristic:** Write-behind introduces data loss risk. Only use it for non-critical counters or metrics. For all business data, prefer cache-aside with invalidation.

---

## Cache Invalidation

**Intent:** Remove or update cached entries when the underlying data changes, preventing stale reads.

**How it works:** On any write operation (create, update, delete), delete the corresponding cache key(s). The next read will be a cache miss and will re-populate from the database with fresh data.

**When to use:**
- Any cache-aside implementation — invalidation is mandatory on writes
- After event handlers that update aggregates

**When NOT to use:**
- Do not invalidate eagerly for every event if the cached data is not affected (unnecessary cache churn)

**Practical heuristic:** Invalidate by aggregate ID. If you cannot derive the cache key from the write operation, your caching design is too coarse.

---

## Redis Integration — Concrete TypeScript Implementation

**Intent:** Wrap the `redis` npm package behind a typed `RedisClient` class to keep infrastructure details out of domain code and enable easy testing via the `Cache` interface.

**Example — RedisClient.ts (from CodelyTV/infrastructure_design-cache-course):**
```typescript
import {
  createClient,
  RedisClientType,
  RedisDefaultModules,
  RedisFunctions,
  RedisModules,
  RedisScripts,
} from "redis";

export class RedisClient {
  private readonly client: Promise<
    RedisClientType<RedisDefaultModules & RedisModules, RedisFunctions, RedisScripts>
  >;

  constructor() {
    this.client = createClient().connect();
  }

  async has(key: string): Promise<boolean> {
    return (await (await this.client).exists(key)) === 1;
  }

  public async get<T>(key: string, deserializer: (parsedJson: any) => T): Promise<T | null> {
    const value = await (await this.client).get(key);
    if (value !== null) {
      try {
        const parsedValue = JSON.parse(value);
        return deserializer(parsedValue);
      } catch (error) {
        console.error("Error parsing JSON from Redis", error);
        return null;
      }
    }
    return null;
  }

  public async set<T>(key: string, value: T, ttlInSeconds: number): Promise<void> {
    const serializedValue = JSON.stringify(value);
    await (await this.client).set(key, serializedValue, { EX: ttlInSeconds });
  }

  async flushAll(): Promise<void> {
    await (await this.client).flushAll();
  }
}
```

**Usage in a cached repository:**
```typescript
export class RedisCachedPostRepository implements PostRepository {
  constructor(
    private readonly wrapped: PostgresPostRepository,
    private readonly redis: RedisClient,
  ) {}

  async search(id: PostId): Promise<Post | null> {
    const key = `post:${id.value}`;
    const cached = await this.redis.get(key, (raw) => Post.fromPrimitives(raw));
    if (cached) return cached;

    const post = await this.wrapped.search(id);
    if (post) {
      await this.redis.set(key, post.toPrimitives(), 60); // 60s TTL
    }
    return post;
  }

  async save(post: Post): Promise<void> {
    await this.wrapped.save(post);
    // Invalidate on write — next read will repopulate from DB
    await this.redis.set(`post:${post.id.value}`, post.toPrimitives(), 60);
  }
}
```

**Practical heuristic:** Inject `RedisClient` via DI as a singleton. The `get` method accepts a `deserializer` function so callers control how raw JSON maps to domain objects — the cache layer never needs to know the domain model's constructor signature.

---

## Cache Key Strategies

**Intent:** Build cache keys that are unique, predictable, and easy to invalidate without key collisions between contexts or aggregate types.

**Patterns:**

| Pattern | Key format | Use case |
|---|---|---|
| Aggregate by ID | `<type>:<id>` | `post:abc-123` | Single aggregate lookup |
| Namespaced by context | `<context>:<type>:<id>` | `rrss:post:abc-123` | Multi-context apps sharing one Redis |
| Versioned | `<type>:<id>:v<n>` | `post:abc-123:v2` | Breaking schema change — old keys expire naturally |
| Composite | `<type>:<field1>:<value1>` | `user:email:foo@bar.com` | Secondary index lookup |

**Rules:**
1. **Never cache list queries with arbitrary filters.** The key space explodes (`post:page:1:size:10:sort:date` × N) and you cannot invalidate efficiently. Cache only by aggregate ID.
2. **Use the aggregate ID as the canonical key.** Derive all cache operations from the ID — you always have the ID on writes.
3. **Prefix by aggregate type, not by use case.** A `post:abc-123` key is reusable across `GetPost`, `PublishPost`, and `DeletePost` use cases. A `get-post:abc-123` key is not.
4. **In shared Redis instances, prefix by bounded context** to prevent collisions: `mooc:course:abc` vs `rrss:post:abc`.

**Example — In-memory cache (simple alternative to Redis for tests/dev):**
```typescript
// InMemoryCacheUserRepository.ts — from CodelyTV/infrastructure_design-eventbus-db-course
export class InMemoryCacheUserRepository implements UserRepository {
  private readonly users: Map<UserId, User> = new Map();

  constructor(private readonly repository: UserRepository) {}

  async save(user: User): Promise<void> {
    await this.repository.save(user);
    this.users.set(user.id, user);        // write-through
  }

  async search(id: UserId): Promise<User | null> {
    const cached = this.users.get(id);
    if (cached) return cached;

    const user = await this.repository.search(id);
    if (user) this.users.set(id, user);   // populate on miss
    return user;
  }
}
```

**Practical heuristic:** Use `InMemoryCache*Repository` in tests and development — no Redis container needed. Swap in `RedisCached*Repository` in production via DI container configuration only.

---

## What to Cache in DDD Contexts

| Layer | Good candidates | Bad candidates |
|---|---|---|
| Repository | Aggregate.findById() results | Search/filter queries (too many keys) |
| Use case | Expensive aggregation reads | Anything with side effects |
| HTTP | Public GET endpoints | Authenticated or personalized responses |
| Domain | Nothing — domain is pure logic | Any infrastructure concern |

**Key rule:** Cache queries that are: (1) read-heavy, (2) rarely mutated, and (3) expensive to compute. Avoid caching list queries with arbitrary filters — the key space explodes and invalidation becomes impossible.
