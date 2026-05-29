# Transactions

Source: CodelyTV/infrastructure_design-transactions-course

## Transaction in Repository (Anti-Pattern)

**Intent:** Wrapping individual repository calls in transactions — shown here as the wrong approach to avoid.

**How it works:** Each `save()` or `find()` call opens and commits its own transaction. Multiple repository calls in one use case run in separate transactions, making partial failure possible.

**When to use:**
- Never for multi-step writes (each step can commit independently, leaving data in an inconsistent state)
- Acceptable only for truly single-operation use cases where exactly one DB write happens

**When NOT to use:**
- Any use case that calls `repositoryA.save()` AND `repositoryB.save()` — the two saves are not atomic

**Practical heuristic:** If your use case calls more than one repository write method, the transaction does not belong inside the repository.

---

## Transaction in Use Case (Application Service)

**Intent:** Wrap the entire unit of work for a use case in a single transaction at the application service level.

**How it works:** The use case opens a transaction before doing any work, executes all repository operations within that transaction, and commits (or rolls back on error) at the end. Repositories receive the active transaction context either via constructor injection or a thread-local/async-context store.

**When to use:**
- Use cases that write to two or more tables/aggregates that must be consistent
- Any "create X then create Y" pattern where partial completion is unacceptable
- Domain events that must be saved atomically with the aggregate (see event-bus.md Outbox pattern)

**When NOT to use:**
- Read-only use cases (no transaction needed)
- Use cases that span multiple bounded contexts or remote services (use sagas / process managers instead)
- Very long-running operations (holding a DB transaction for seconds causes lock contention)

**Practical heuristic:** The use case is the transaction boundary. One use case = one transaction. If you need two transactions, you probably need two use cases.

**Example:**
```typescript
// PostPublisher.ts — use case owns the transaction boundary
export class PostPublisher {
  constructor(
    private readonly clock: Clock,
    private readonly repository: PostRepository,
    private readonly eventBus: EventBus,
  ) {}

  async publish(id: string, userId: string, content: string): Promise<void> {
    const post = Post.publish(id, userId, content, this.clock);
    await this.repository.save(post);           // write aggregate
    await this.eventBus.publish(post.pullDomainEvents()); // write events (same tx if DB-backed bus)
  }
}
```

---

## Transaction Decorator (Transparent Wrapping)

**Intent:** Add transaction semantics to a use case without modifying its code, using the Decorator pattern.

**How it works:** A `TransactionalPostPublisher` wraps the real `PostPublisher`. Before delegating to the inner use case, it opens a transaction; after successful execution it commits; on exception it rolls back. The inner use case has no knowledge of transactions.

**When to use:**
- When you want to apply transactions uniformly to many use cases
- When transaction management is a cross-cutting concern you want to keep out of business logic
- In frameworks with DI containers that support decoration (NestJS interceptors, diod decorators)

**When NOT to use:**
- When the transaction boundary requires conditional logic that the decorator cannot express
- When different use case methods need different transaction scopes

**Practical heuristic:** Start with the transaction inside the use case. Extract to a decorator only when you see the same wrapping code copy-pasted across multiple use cases.

**Example:**
```typescript
// TransactionalPostPublisher.ts — decorator approach
export class TransactionalPostPublisher implements PostPublisherInterface {
  constructor(
    private readonly wrapped: PostPublisher,
    private readonly transactionManager: TransactionManager,
  ) {}

  async publish(id: string, userId: string, content: string): Promise<void> {
    await this.transactionManager.run(async () => {
      await this.wrapped.publish(id, userId, content);
    });
  }
}
```

---

## Transaction at Entry Point

**Intent:** Open the transaction at the HTTP controller or message consumer level, wrapping the entire request.

**How it works:** Middleware or an interceptor starts a transaction before the request reaches the use case, and commits or rolls back after the response is produced.

**When to use:**
- Framework-level transaction management (e.g., Spring `@Transactional` on controller, NestJS interceptor)
- When every endpoint in a group always needs a transaction

**When NOT to use:**
- Read-only GET endpoints (transaction is wasteful)
- When only some endpoints in a group need transactions
- When the entry point is a message consumer that already handles idempotency separately

**Practical heuristic:** Entry-point transactions are convenient but coarse. Prefer use-case-level transactions — they make the boundary explicit and testable.

---

## Transaction Decorator — Proxy-Based Generic Implementation

**Intent:** Apply transaction semantics to any use case automatically using a JavaScript `Proxy`, without writing a decorator class for each use case.

**How it works:** `TransactionalDecorator.decorate(useCase, connection)` wraps every method on the target object. Before the method runs, it calls `connection.beginTransaction()`. On success it calls `connection.commit()`. On any exception it calls `connection.rollback()` and re-throws. The use case code has zero transaction awareness.

**When to use:**
- When you have many use cases that all need the same transaction boundary
- In DI containers where you can decorate at registration time (e.g., `diod`, NestJS providers)
- When you want to enforce "every use case = one transaction" as a container-level convention

**When NOT to use:**
- When the use case has read-only methods that should not open transactions
- When you need different isolation levels per method
- TypeScript `Proxy` bypasses the type system — add `// @ts-ignore` carefully and test thoroughly

**Practical heuristic:** Use the Proxy decorator for cross-cutting transaction enforcement at the composition root. If only one or two use cases need transactions, write explicit decorators instead — the Proxy approach pays off at scale (5+ use cases).

**Example — TransactionalDecorator.ts (from CodelyTV/infrastructure_design-transactions-course):**
```typescript
import { DatabaseConnection } from "../domain/DatabaseConnection";

export class TransactionalDecorator {
  static decorate<T>(decorated: T, connection: DatabaseConnection): T {
    // @ts-ignore
    return new Proxy(decorated, {
      get: (target, propKey) => {
        // @ts-ignore
        const originalMethod = target[propKey];
        if (typeof originalMethod === "function") {
          return async (...args: any[]) => {
            try {
              await connection.beginTransaction();
              const result = await originalMethod.apply(target, args);
              await connection.commit();
              return result;
            } catch (error) {
              await connection.rollback();
              throw error;
            }
          };
        }
        return originalMethod;
      },
    });
  }
}
```

**Example — DatabaseConnection interface and MariaDB implementation:**
```typescript
// DatabaseConnection.ts (domain interface — no ORM dependency)
export abstract class DatabaseConnection {
  abstract searchOne<T>(query: string): Promise<T | null>;
  abstract execute(query: string): Promise<void>;
  abstract beginTransaction(): Promise<void>;
  abstract commit(): Promise<void>;
  abstract rollback(): Promise<void>;
}

// MariaDBConnection.ts (infrastructure — wraps mariadb pool)
export class MariaDBConnection extends DatabaseConnection {
  private poolInstance: Pool | null = null;
  private connection: MinimalConnection | null = null;

  async beginTransaction(): Promise<void> {
    this.connection = await this.pool.getConnection();
    await this.connection.beginTransaction();
  }

  async commit(): Promise<void> {
    await this.connection?.commit();
    await this.connection?.end();
    this.connection = null;
  }

  async rollback(): Promise<void> {
    await this.connection?.rollback();
    await this.connection?.end();
    this.connection = null;
  }
}
```

**Registration in DI container:**
```typescript
// Use at composition root — the use case itself stays clean
const postPublisher = TransactionalDecorator.decorate(
  new PostPublisher(repository, eventBus),
  mariadbConnection,
);
```

---

## Distributed Transactions

**Intent:** Coordinate writes across multiple services or databases.

**How it works:** True distributed transactions (2PC) require all participants to lock resources simultaneously, which is impractical at scale. The alternative is the Saga pattern: a sequence of local transactions, each with a compensating transaction for rollback.

**When to use:**
- Only when data genuinely lives in separate services with no shared DB

**When NOT to use:**
- When you can put the data in the same database (the simplest and most reliable solution)
- As a first choice — always ask "can we share the DB?" before reaching for sagas

**Practical heuristic:** A distributed transaction is a design smell that often signals the wrong bounded context split. Before implementing a saga, reconsider whether the aggregates belong in the same context.
