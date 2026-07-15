# Aggregates and Aggregate Roots

Source: [CodelyTV/aggregates-course](https://github.com/CodelyTV/aggregates-course), synthesized with the aggregate rules in Evans and Vernon.

Use this reference to discover, review, split, or implement aggregate boundaries. Treat the course as design evidence, not as production-ready code: retain the principles below and avoid copying its unsafe concurrency and testing details.

## Aggregate Is a Consistency Boundary

An aggregate is the smallest cluster of entities and value objects that must remain atomically consistent after a command. It is not:

- every object associated with a domain noun
- an ORM object graph or cascade configuration
- a database table, module, bounded context, or service
- the shape required by a screen or report

Keep a rule inside one aggregate only when the business requires it to hold immediately. Coordinate rules that may settle later across aggregates using events, policies, or process managers.

Small aggregates are usually easier to load, lock, and evolve, but size is a consequence of the invariants. Never use a property-count or table-count threshold.

## Discover the Boundary from a Command

Analyze one business command at a time:

1. Name the command in Ubiquitous Language: `ApproveOrder`, `ReserveSeat`, `AddReview`.
2. List the state the decision reads and changes.
3. State each invariant as a sentence the business recognizes.
4. Ask which state must commit or reject as one unit.
5. Put only that state behind one root.
6. Treat remaining coordination as cross-aggregate and make its consistency expectation explicit.
7. Recheck lifecycle, cardinality, contention, and failure recovery before finalizing the boundary.

Example: adding a product review does not normally require loading and saving the product with every historical review. A review has independent identity and lifecycle, and the collection can grow without bound. Model `ProductReview` as its own aggregate and retain `ProductId` as an identity reference unless a genuine atomic product-review invariant proves otherwise.

## Boundary Signals

| Signal | Prefer the same aggregate | Prefer separate aggregates |
|---|---|---|
| Consistency | Rule must hold at commit | Temporary inconsistency is acceptable |
| Lifecycle | Child exists only with owner | Object is created, archived, or deleted independently |
| Cardinality | Small and naturally bounded | Collection is large or unbounded |
| Concurrency | Changes must serialize | Parts change independently or are highly contended |
| Access | Only meaningful through owner | Needs direct lookup or its own use cases |
| Ownership | Root exclusively owns the part | Object is shared by several owners |
| Failure | Partial success is invalid | Retry, compensation, or reconciliation is meaningful |

Do not split a real invariant merely to improve performance. First understand the business consequence, then choose reservation, optimistic concurrency, a different invariant, or a larger boundary deliberately.

## Protect the Root

Give every aggregate exactly one root and route all commands through it.

- Keep mutable state and child collections private.
- Expose named operations, not public setters.
- Return immutable snapshots or copies; never expose a mutable collection that bypasses the root.
- Give child entities local identity when the root must distinguish them.
- Create repositories for roots, not for internal children.
- Reference another aggregate by its identity, not by a live object reference.

An identity reference prevents accidental cross-aggregate mutation, but it does not guarantee that the referenced aggregate still exists. Enforce strong referential requirements with the appropriate database constraint, lifecycle policy, reservation, or reconciliation process.

## Put Each Rule in the Narrowest Owner

Use this order when deciding where a rule belongs:

| Rule | Owner |
|---|---|
| Intrinsic validity of one value, independent of context | Value Object |
| Stateful invariant over members of one aggregate | Aggregate Root behavior |
| Stateless domain policy that belongs to no entity or value | Narrow Domain Service |
| Loading, existence checks, transactions, I/O, and workflow | Application Service |
| Database uniqueness or serialization under concurrency | Persistence constraint plus application handling |

Examples:

- Rating from 0 to 5: `ReviewRating` Value Object.
- Order total cannot exceed its approved limit: `Order` Aggregate Root.
- Exchange rate policy involving two currencies and a supplied rate source: a named Domain Service or port.
- Load a product before creating a review: application orchestration.

Avoid generic `Ensurer`, `Manager`, or `Validator` services that accept raw primitives and collect unrelated rules. A Domain Service must use domain language, remain stateless, and never import an application use case.

Context-sensitive rules do not automatically belong in a Value Object. If a comment limit varies by tenant, role, product, or date, pass the policy explicitly or enforce it at the aggregate boundary rather than hiding ambient context in the value.

## Creation, Reconstitution, and Transitions

Separate three semantic paths:

- `create(...)`: establish a new identity and record creation facts.
- `fromPrimitives(...)`, `rehydrate(...)`, or a mapper: restore persisted state without recording new facts.
- named commands such as `rename(...)` or `addCategory(...)`: enforce transitions and record resulting facts.

Restrict raw constructors where the language permits it. Never reconstitute through `create(...)`; loading an aggregate must not emit `Created` again.

Technical Aggregate IDs may be generated by the caller and supplied to `create(...)`. This makes create commands deterministic across retries and supports idempotency. Do not confuse an opaque technical ID with a business sequence such as an invoice number; business numbering may require a concurrency-safe allocator and its own domain policy.

Reconstitution still has to produce a valid usable object, but rule evolution needs care. A stricter constructor can reject historical data that was valid under an earlier rule. Handle that with migration, version-aware mapping, or an explicit legacy state rather than silently treating stored data as newly created.

`toPrimitives()` and `fromPrimitives()` are one mapping style, not a DDD requirement. A dedicated mapper is equally valid when it keeps persistence concerns out of the model more effectively.

## Transactions and Concurrency

Use one aggregate root per transaction as the default, not an inviolable law. Multiple tables may persist one aggregate atomically. Updating multiple roots in one local transaction can be justified, but treat it as a boundary warning and document why eventual consistency is unacceptable.

Protect concurrent updates when lost updates matter. Carry an expected Aggregate version across load and save, reject stale decisions, and choose retry versus user-visible conflict according to the command semantics. Do not silently use last-write-wins for business decisions. Read `../../infrastructure-design/references/transactions.md` for optimistic-lock implementation and integration testing.

Watch for hot aggregates: many users appending to one root will serialize on one version even if they change unrelated children. Unbounded collections, repeated write conflicts, large payloads, and long lock times are evidence to revisit the boundary.

## Cross-Aggregate Rules

An in-memory check cannot guarantee a global rule under concurrency. Examples include unique email, sequential invoice number, stock shared across orders, and existence of another aggregate.

Choose enforcement by semantics:

- Use a unique database constraint for uniqueness and translate collisions into a domain/application error.
- Use an atomic database sequence, locked counter, serializable transaction with retry, or explicit allocator for business numbering.
- Use reservations when scarce capacity must be held across a workflow.
- Use events and idempotent handlers when temporary inconsistency is acceptable.
- Use a process manager for stateful, multi-step coordination and compensation.

Never use `MAX(number) + 1` as a safe concurrent allocator. A unique constraint can detect the collision, but it does not make allocation correct by itself.

If two changes truly must commit together, reconsider whether they belong in one aggregate before introducing a saga. A saga cannot retroactively create atomic consistency; it manages eventual consistency and partial failure.

## Persistence, Events, and Reads

Model one repository per aggregate root. Persist the aggregate as a unit even when its state spans several tables. Keep transaction control outside individual repository methods so the application boundary can commit state and outbox records together.

Let the aggregate decide which domain facts occurred and record them internally. Let the application or Unit of Work persist those facts. Do not inject an Event Bus into the aggregate.

The educational sequence `save -> pull events -> publish` has a dual-write failure window. For events that must survive a crash or cross a process boundary, store aggregate changes and outbox messages in the same database transaction, then publish asynchronously with idempotent consumers.

Do not distort aggregates for queries. Use a dedicated read model or projection when a query joins aggregates, computes totals, or serves a consumer-specific shape. A synchronous database view is one projection option; asynchronous projections additionally require replay, ordering, idempotency, monitoring, and a stated staleness expectation.

## Testing Expectations

Test the root through public commands, with real value objects and child entities. At minimum verify:

- valid transitions change the observable state
- each invariant rejects its boundary cases
- rejected commands leave state and pending events unchanged
- creation records the expected event
- reconstitution records no event
- named transitions record the right event payload
- child uniqueness and collection rules use value equality
- persistence round trips preserve the model
- optimistic conflicts and global constraints work against real infrastructure

Read `../../tdd-best-practices/references/aggregate-testing.md` for the complete testing workflow.

## Common Failure Modes

- Copying the ORM relationship graph into one aggregate.
- Measuring aggregate size by properties, classes, or tables.
- Loading an unbounded child collection to append one item.
- Exposing public setters or mutable child arrays.
- Providing a repository for an internal child entity.
- Updating several roots in every command without reviewing the boundary.
- Treating a read/report model as the write aggregate.
- Checking global uniqueness only in memory.
- Emitting creation events during reconstitution.
- Clearing events before durable handoff to an outbox.
- Moving all rules into a procedural Domain Service.

## Review Checklist

- Can every invariant be stated in domain language?
- Does each invariant require immediate consistency?
- Is the boundary the smallest one that can enforce those invariants?
- Can any collection grow without a business-defined bound?
- Do independently changing objects have independent identities and lifecycles?
- Can callers mutate state without a root command?
- Does one repository represent one root rather than one table?
- Is cross-aggregate consistency explicit and failure-aware?
- Are global constraints enforced under real concurrency?
- Are creation and reconstitution separate?
- Are durable events written atomically with state?
- Are query shapes kept out of the write model?

## Course-Specific Caveats

Do not generalize these details from the course:

- Aggregate inheritance, public `toPrimitives()`, or a wrapper for every primitive are not mandatory.
- A synchronous existence check cannot guarantee the referenced aggregate remains present.
- SQL views are not the default projection mechanism.
- `MAX + 1` is unsafe for concurrent numbering.
- JavaScript `includes(new ValueObject(...))` compares object identity, not domain value.
- The demonstrated self-asserting repository/event-bus mocks can pass without proving the System Under Test made the call.
- The repository history illustrates design evolution but does not demonstrate a strict Red-Green-Refactor process.
