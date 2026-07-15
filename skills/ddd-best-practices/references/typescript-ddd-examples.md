# TypeScript DDD Examples (CodelyTV Pattern)

Practical TypeScript implementations of DDD building blocks, based on the CodelyTV `typescript-ddd-example` repository. These show the full stack of building blocks working together in a real bounded context.

Source: https://github.com/CodelyTV/typescript-ddd-example

---

## Folder Structure

**Intent:** Organize code by Bounded Context, not by technical layer.

**How it works:** The top-level `src/Contexts/` directory holds one folder per bounded context (e.g., `Mooc`, `Backoffice`). Each context contains sub-domains organized by aggregate. A `Shared/` context holds cross-cutting building blocks (base classes, event bus, criteria). Inside each aggregate folder, the split is always `domain/` → `application/` → `infrastructure/`.

**Example:**
```
src/
  Contexts/
    Mooc/
      Courses/
        domain/
          Course.ts                    # Aggregate Root
          CourseRepository.ts          # Port (interface)
          CourseName.ts                # Value Object
          CourseDuration.ts            # Value Object
          CourseCreatedDomainEvent.ts  # Domain Event
        application/
          Create/
            CourseCreator.ts           # Use Case (Application Service)
            CreateCourseCommand.ts     # Command DTO
            CreateCourseCommandHandler.ts
        infrastructure/
          persistence/
            mongo/
              MongoCourseRepository.ts # Driven Adapter
    Shared/
      domain/
        AggregateRoot.ts
        DomainEvent.ts
        EventBus.ts
        value-object/
          ValueObject.ts
          StringValueObject.ts
          Uuid.ts
      infrastructure/
        persistence/
          mongo/
            MongoRepository.ts
tests/
  Contexts/
    Mooc/
      Courses/
        domain/CourseMother.ts         # Object Mother
        application/CreateCourse...test.ts
```

**Practical heuristic:** If you cannot tell from the folder name alone which business capability the code serves, the structure is wrong. Folder names like `controllers/` or `services/` are red flags.

---

## Value Objects in TypeScript

**Intent:** Give domain values explicit construction, immutable representation, and semantic equality without assuming one generic base can compare every representation safely.

**How it works:** Implement equality explicitly for each semantic type. A shared base may remove repetition for scalar strings, numbers, or booleans, but `Date`, arrays, objects, and composite values need domain-aware comparison and defensive copies. Composition, branded scalars, and records are valid alternatives to inheritance.

**Example:**
```typescript
// src/Contexts/Mooc/Courses/domain/CourseName.ts
export class CourseName {
  private constructor(readonly value: string) {}

  static create(raw: string): CourseName {
    const value = raw.trim();
    if (value.length === 0 || value.length > 30) {
      throw new CourseNameLengthExceeded(value);
    }
    return new CourseName(value);
  }

  equals(other: CourseName): boolean {
    return this.value === other.value;
  }
}

// src/Contexts/Mooc/Shared/domain/Courses/CourseId.ts
export class CourseId {
  private constructor(readonly value: string) {}

  static create(value: string): CourseId {
    if (!validateUuid(value)) throw new InvalidCourseId(value);
    return new CourseId(value);
  }

  equals(other: CourseId): boolean {
    return this.value === other.value;
  }
}
```

**Practical heuristic:** Transport DTOs, commands, and messages normally carry primitives. Convert at a deliberate application/domain boundary, then use Value Objects in domain APIs where semantic distinction or guarantees justify them. Run `tsc --noEmit`; transpile-only tests do not prove type correctness.

---

## AggregateRoot Base Class

**Intent:** Give every aggregate root the ability to collect domain events before publishing them, and enforce serialization to primitives.

**How it works:** `AggregateRoot` maintains a private list of domain events. The aggregate records an event via `record()` when state changes. A best-effort in-process application service can drain these events after persistence. Durable cross-process delivery requires handing them to an Outbox in the same transaction as Aggregate state; do not clear the only event copy before durable handoff.

**Example:**
```typescript
// src/Contexts/Shared/domain/AggregateRoot.ts
export abstract class AggregateRoot {
  private domainEvents: Array<DomainEvent>;

  constructor() {
    this.domainEvents = [];
  }

  pullDomainEvents(): Array<DomainEvent> {
    const domainEvents = this.domainEvents.slice();
    this.domainEvents = [];
    return domainEvents;
  }

  record(event: DomainEvent): void {
    this.domainEvents.push(event);
  }

  abstract toPrimitives(): any;
}
```

**Practical heuristic:** Never publish from inside the Aggregate. The application/Unit of Work owns durable handoff. Treat direct `save -> pull -> publish` as educational in-process delivery only; use `infrastructure-design` for transactional Outbox delivery.

---

## Aggregate Root (Concrete)

**Intent:** Implement a rich aggregate root that uses the static factory method pattern to enforce valid creation and record domain events.

**How it works:** The `Course` aggregate extends `AggregateRoot`. Construction through `new Course()` is valid but does not produce events — used for reconstitution from persistence via `fromPrimitives()`. Creation through the static `Course.create()` factory method records the `CourseCreatedDomainEvent`. All fields are typed as Value Objects, never raw primitives.

**Example:**
```typescript
// src/Contexts/Mooc/Courses/domain/Course.ts
export class Course extends AggregateRoot {
  readonly id: CourseId;
  readonly name: CourseName;
  readonly duration: CourseDuration;

  constructor(id: CourseId, name: CourseName, duration: CourseDuration) {
    super();
    this.id = id;
    this.name = name;
    this.duration = duration;
  }

  // Static factory: creates a new Course and records the creation event
  static create(id: CourseId, name: CourseName, duration: CourseDuration): Course {
    const course = new Course(id, name, duration);
    course.record(
      new CourseCreatedDomainEvent({
        aggregateId: course.id.value,
        duration: course.duration.value,
        name: course.name.value,
      })
    );
    return course;
  }

  // Reconstitution: used by the repository adapter — no events recorded
  static fromPrimitives(plainData: { id: string; name: string; duration: string }): Course {
    return new Course(
      CourseId.create(plainData.id),
      CourseName.create(plainData.name),
      new CourseDuration(plainData.duration)
    );
  }

  toPrimitives(): any {
    return {
      id: this.id.value,
      name: this.name.value,
      duration: this.duration.value,
    };
  }
}
```

**Practical heuristic:** Keep creation and reconstitution semantically separate so loading cannot emit creation events. `create()` plus `fromPrimitives()` is one valid strategy; a dedicated mapper is another.

---

## DomainEvent Base Class

**Intent:** Give every domain event a consistent structure — event name, aggregate ID, event ID, and timestamp — while letting each concrete event define its own typed attributes.

**How it works:** The abstract `DomainEvent` stores metadata automatically (auto-generating `eventId` as a UUID and `occurredOn` as now if not provided). Each concrete event declares a static `EVENT_NAME` constant and implements `toPrimitives()` for serialization plus a static `fromPrimitives()` factory for deserialization (used by message bus infrastructure).

**Example:**
```typescript
// src/Contexts/Shared/domain/DomainEvent.ts
export abstract class DomainEvent {
  static EVENT_NAME: string;
  static fromPrimitives: (params: {
    aggregateId: string;
    eventId: string;
    occurredOn: Date;
    attributes: DomainEventAttributes;
  }) => DomainEvent;

  readonly aggregateId: string;
  readonly eventId: string;
  private readonly occurredOnMs: number;
  readonly eventName: string;

  constructor(params: {
    eventName: string;
    aggregateId: string;
    eventId?: string;
    occurredOn?: Date;
  }) {
    this.aggregateId = params.aggregateId;
    this.eventId = params.eventId ?? Uuid.random().value;
    this.occurredOnMs = (params.occurredOn ?? new Date()).getTime();
    if (!Number.isFinite(this.occurredOnMs)) throw new InvalidEventDate();
    this.eventName = params.eventName;
  }

  get occurredOn(): Date {
    return new Date(this.occurredOnMs);
  }

  abstract toPrimitives(): DomainEventAttributes;
}

// src/Contexts/Mooc/Courses/domain/CourseCreatedDomainEvent.ts
type CreateCourseDomainEventAttributes = {
  readonly duration: string;
  readonly name: string;
};

export class CourseCreatedDomainEvent extends DomainEvent {
  static readonly EVENT_NAME = 'course.created';

  readonly duration: string;
  readonly name: string;

  constructor({
    aggregateId,
    name,
    duration,
    eventId,
    occurredOn,
  }: {
    aggregateId: string;
    eventId?: string;
    duration: string;
    name: string;
    occurredOn?: Date;
  }) {
    super({
      eventName: CourseCreatedDomainEvent.EVENT_NAME,
      aggregateId,
      eventId,
      occurredOn,
    });
    this.duration = duration;
    this.name = name;
  }

  toPrimitives(): CreateCourseDomainEventAttributes {
    return { name: this.name, duration: this.duration };
  }

  // Used by the event bus infrastructure to deserialize incoming messages
  static fromPrimitives(params: {
    aggregateId: string;
    attributes: CreateCourseDomainEventAttributes;
    eventId: string;
    occurredOn: Date;
  }): DomainEvent {
    return new CourseCreatedDomainEvent({
      aggregateId: params.aggregateId,
      duration: params.attributes.duration,
      name: params.attributes.name,
      eventId: params.eventId,
      occurredOn: params.occurredOn,
    });
  }
}
```

**Practical heuristic:** Name domain events in the past tense with dot notation: `course.created`, `payment.confirmed`. The static `EVENT_NAME` is the contract between producers and consumers — treat it as an immutable API once deployed.

---

## Repository Port (Interface)

**Intent:** Declare what the domain needs from persistence in domain language, with no reference to any database technology.

**How it works:** The repository interface lives in the `domain/` folder — it is part of the domain layer, not infrastructure. Method names use domain vocabulary. Return types are domain objects or aggregates, never raw database rows. The interface is the driven port; concrete adapters (Mongo, Postgres, in-memory) implement it in `infrastructure/`.

**Example:**
```typescript
// src/Contexts/Mooc/Courses/domain/CourseRepository.ts
import { Course } from './Course';

export interface CourseRepository {
  save(course: Course): Promise<void>;
  searchAll(): Promise<Array<Course>>;
}
```

**Practical heuristic:** If you find yourself adding methods like `findByRawQuery()` or `executeSQL()` to a repository interface, the abstraction has broken down. Keep the interface in domain terms only.

---

## EventBus Port (Interface)

**Intent:** Declare the outbound event publishing contract so the domain layer never depends on RabbitMQ, Kafka, or any specific broker.

**Example:**
```typescript
// src/Contexts/Shared/domain/EventBus.ts
export interface EventBus {
  publish(events: Array<DomainEvent>): Promise<void>;
  addSubscribers(subscribers: DomainEventSubscribers): void;
}

// src/Contexts/Shared/domain/DomainEventSubscriber.ts
export interface DomainEventSubscriber<T extends DomainEvent> {
  subscribedTo(): Array<DomainEventClass>;
  on(domainEvent: T): Promise<void>;
}
```

**Practical heuristic:** For best-effort in-process reactions, inject an in-memory bus or spy. For production broker delivery, persist an Outbox atomically and let a relay publish to RabbitMQ; do not publish directly from this use case.

---

## Use Case (Application Service)

**Intent:** Orchestrate the domain — fetch, mutate via the aggregate, persist, publish events — with no business logic of its own.

**How it works:** `CourseCreator` receives dependencies through constructor injection. The Command Handler translates the flat DTO command into typed Value Objects. The direct publication below is suitable only for best-effort in-process reactions; replace it with a Unit of Work plus Outbox when events must survive failures.

**Example:**
```typescript
// src/Contexts/Mooc/Courses/application/Create/CourseCreator.ts
export class CourseCreator {
  constructor(
    private repository: CourseRepository,
    private eventBus: EventBus
  ) {}

  async run(params: {
    id: CourseId;
    name: CourseName;
    duration: CourseDuration;
  }): Promise<void> {
    const course = Course.create(params.id, params.name, params.duration);
    await this.repository.save(course);
    await this.eventBus.publish(course.pullDomainEvents());
  }
}

// src/Contexts/Mooc/Courses/application/Create/CreateCourseCommandHandler.ts
export class CreateCourseCommandHandler
  implements CommandHandler<CreateCourseCommand> {
  constructor(private courseCreator: CourseCreator) {}

  subscribedTo(): MessageConstructor<CreateCourseCommand> {
    return CreateCourseCommand;
  }

  async handle(command: CreateCourseCommand): Promise<void> {
    const id       = CourseId.create(command.id);
    const name     = CourseName.create(command.name);
    const duration = new CourseDuration(command.duration);
    await this.courseCreator.run({ id, name, duration });
  }
}
```

**Practical heuristic:** A use case may branch for orchestration, absence, authorization outcomes, retries, or policy results, but it must not own domain policy that belongs in the model. Treat it as a traffic controller, not as a rule-free syntax exercise.

---

## Infrastructure: MongoRepository Base (Driven Adapter)

**Intent:** Provide a reusable base class for all MongoDB-backed repository adapters, keeping the toPrimitives/fromPrimitives mapping in each concrete class.

**How it works:** `MongoRepository<T>` is generic over any `AggregateRoot`. It provides `persist()` (upsert by ID using `toPrimitives()`) and `searchByCriteria()` (for flexible querying). Concrete repository classes extend this base and implement `collectionName()`. The `fromPrimitives()` call translates raw Mongo documents back into domain aggregates.

**Example:**
```typescript
// src/Contexts/Shared/infrastructure/persistence/mongo/MongoRepository.ts
export abstract class MongoRepository<T extends AggregateRoot> {
  constructor(private _client: Promise<MongoClient>) {}

  protected abstract collectionName(): string;

  protected async persist(id: string, aggregateRoot: T): Promise<void> {
    const collection = await this.collection();
    const document = { ...aggregateRoot.toPrimitives(), _id: id, id: undefined };
    await collection.updateOne({ _id: id }, { $set: document }, { upsert: true });
  }
}

// Concrete adapter (in infrastructure/persistence/mongo/)
export class MongoCourseRepository
  extends MongoRepository<Course>
  implements CourseRepository {
  protected collectionName(): string {
    return 'courses';
  }

  async save(course: Course): Promise<void> {
    await this.persist(course.id.value, course);
  }

  async searchAll(): Promise<Array<Course>> {
    const collection = await this.collection();
    const documents = await collection.find({}).toArray();
    return documents.map(Course.fromPrimitives);
  }
}
```

**Practical heuristic:** The concrete adapter is the only place where `toPrimitives()` and `fromPrimitives()` are called. Everything else in the system works with typed domain objects.

---

## Command / Query Contracts

**Intent:** Give bus infrastructure type-safe command, query, response, and handler relationships without relying on empty structural marker types.

**How it works:** Private/protected brands distinguish command and query families under TypeScript structural typing. A query carries its response type. Handlers return the constructor they subscribe to, not a message instance.

**Example:**
```typescript
export abstract class Command {
  protected readonly __commandBrand!: never;
}

export abstract class Query<R> {
  protected readonly __responseBrand!: R;
}

export type MessageConstructor<T> = new (...args: any[]) => T;

// Serialized/external commands normally carry flat primitives.
// src/Contexts/Mooc/Courses/domain/CreateCourseCommand.ts
type Params = { id: string; name: string; duration: string };

export class CreateCourseCommand extends Command {
  id: string;
  name: string;
  duration: string;

  constructor({ id, name, duration }: Params) {
    super();
    this.id = id;
    this.name = name;
    this.duration = duration;
  }
}
```

**Practical heuristic:** Serialized commands normally carry transport primitives and are converted at the handler boundary. A trusted in-process command may carry Value Objects when that contract is deliberate and no serialization boundary is implied.

---

## CommandBus / QueryBus — CQRS Bus Interfaces

**Intent:** Decouple the controller (driver adapter) from the use case by routing through a bus. The controller does not need to know which handler exists — it only dispatches a command or queries with a query.

**How it works:** `CommandBus` dispatches a command and returns completion. `QueryBus` infers the response type carried by `Query<R>`. Both are interfaces implemented in infrastructure.

**Example:**
```typescript
// src/Contexts/Shared/domain/CommandBus.ts
export interface CommandBus {
  dispatch<T extends Command>(command: T): Promise<void>;
}

// src/Contexts/Shared/domain/QueryBus.ts
export interface QueryBus {
  ask<R>(query: Query<R>): Promise<R>;
}

// src/Contexts/Shared/domain/CommandHandler.ts
export interface CommandHandler<T extends Command> {
  subscribedTo(): MessageConstructor<T>;
  handle(command: T): Promise<void>;
}

// src/Contexts/Shared/domain/QueryHandler.ts
export interface QueryHandler<R, Q extends Query<R>> {
  subscribedTo(): MessageConstructor<Q>;
  handle(query: Q): Promise<R>;
}
```

**Practical heuristic:** CQRS split is at the bus level: commands mutate state and return nothing; queries read state and return a response. Never mix the two in one handler.

---

## CommandBus / QueryBus — In-Memory Implementations

**Intent:** Provide a synchronous, in-process bus for development and testing. The registry (`CommandHandlers`, `QueryHandlers`) maps command/query classes to their handlers.

**How it works:** The registry maps message constructors to handlers. Handlers register the concrete constructor returned by `subscribedTo()`. The bus looks up `command.constructor` at dispatch time and fails explicitly when no handler exists.

**Example:**
```typescript
// src/Contexts/Shared/infrastructure/CommandBus/CommandHandlers.ts
export class CommandHandlers {
  private readonly handlers = new Map<MessageConstructor<Command>, CommandHandler<any>>();

  constructor(commandHandlers: ReadonlyArray<CommandHandler<any>>) {
    commandHandlers.forEach((handler) => {
      this.handlers.set(handler.subscribedTo(), handler);
    });
  }

  get<T extends Command>(command: T): CommandHandler<T> {
    const constructor = command.constructor as MessageConstructor<T>;
    const commandHandler = this.handlers.get(constructor);
    if (!commandHandler) {
      throw new CommandNotRegisteredError(command);
    }
    return commandHandler as CommandHandler<T>;
  }
}

// src/Contexts/Shared/infrastructure/CommandBus/InMemoryCommandBus.ts
export class InMemoryCommandBus implements CommandBus {
  constructor(private commandHandlers: CommandHandlers) {}

  async dispatch<T extends Command>(command: T): Promise<void> {
    const handler = this.commandHandlers.get(command);
    await handler.handle(command);
  }
}
```

**Practical heuristic:** The lookup key is the message constructor, not an instance. Mirror the same typed constructor registry for queries. More elaborate buses can use explicit stable message names when constructors cannot cross serialization boundaries.

---

## Nullable Type Utility

**Intent:** Express one canonical absence representation in a domain API.

**Example:**
```typescript
// src/Contexts/Shared/domain/Nullable.ts
export type Nullable<T> = T | null;

// Usage in a repository return type
async findById(id: CourseId): Promise<Nullable<Course>> { ... }
```

**Practical heuristic:** Choose either `null` or `undefined` within a domain API rather than combining both. Accept both only at an external parsing boundary and normalize immediately.

---

## Criteria Pattern — Flexible Repository Queries

**Intent:** Express repository search conditions as domain objects (not raw SQL or query strings) so the domain layer can construct complex queries without depending on infrastructure.

**How it works:** `Criteria` composes `Filters` (a list of `Filter` objects) and an `Order`. Each `Filter` holds a `FilterField` (the attribute name), a `FilterOperator` (enum: `=`, `!=`, `>`, `<`, `CONTAINS`, `NOT_CONTAINS`), and a `FilterValue`. Repository adapters translate `Criteria` to their native query language (SQL WHERE clauses, Elasticsearch DSL, etc.).

**Example:**
```typescript
// src/Contexts/Shared/domain/criteria/Criteria.ts
export class Criteria {
  readonly filters: Filters;
  readonly order: Order;
  readonly limit?: number;
  readonly offset?: number;

  constructor(filters: Filters, order: Order, limit?: number, offset?: number) {
    this.filters = filters;
    this.order = order;
    this.limit = limit;
    this.offset = offset;
  }

  public hasFilters(): boolean {
    return this.filters.filters.length > 0;
  }
}

// src/Contexts/Shared/domain/criteria/Filter.ts
export class Filter {
  readonly field: FilterField;
  readonly operator: FilterOperator;
  readonly value: FilterValue;

  constructor(field: FilterField, operator: FilterOperator, value: FilterValue) { ... }

  static fromValues(values: Map<string, string>): Filter {
    const field = values.get('field');
    const operator = values.get('operator');
    const value = values.get('value');
    if (!field || !operator || !value) {
      throw new InvalidArgumentError('The filter is invalid');
    }
    return new Filter(
      new FilterField(field),
      FilterOperator.fromValue(operator),
      new FilterValue(value)
    );
  }
}

// src/Contexts/Shared/domain/criteria/FilterOperator.ts
export enum Operator {
  EQUAL = '=',
  NOT_EQUAL = '!=',
  GT = '>',
  LT = '<',
  CONTAINS = 'CONTAINS',
  NOT_CONTAINS = 'NOT_CONTAINS'
}

export class FilterOperator extends EnumValueObject<Operator> {
  static fromValue(value: string): FilterOperator { ... }
  static equal() { return this.fromValue(Operator.EQUAL); }
  public isPositive(): boolean {
    return this.value !== Operator.NOT_EQUAL && this.value !== Operator.NOT_CONTAINS;
  }
}
```

**Practical heuristic:** The domain builds `Criteria` objects; infrastructure translates them. No `WHERE` clause or Elasticsearch DSL ever appears in the domain layer.

---

## Object Mother Pattern — Test Data Factories

**Intent:** Centralize valid test data creation so tests stay short and readable. Each domain concept gets its own Mother class with deterministic defaults and focused overrides.

**How it works:** Each Mother has `create(explicit params)` and may provide seeded generation for intentional variation. The test specifies every value relevant to its rule. If randomness is used, inject/print the seed so failures reproduce exactly.

**Example:**
```typescript
// tests/Contexts/Mooc/Courses/domain/CourseMother.ts
export class CourseMother {
  static create(id: CourseId, name: CourseName, duration: CourseDuration): Course {
    return new Course(id, name, duration);
  }

  static from(command: CreateCourseCommand): Course {
    return this.create(
      CourseIdMother.create(command.id),
      CourseNameMother.create(command.name),
      CourseDurationMother.create(command.duration)
    );
  }

  static random(seed: number): Course {
    return this.create(
      CourseIdMother.random(seed),
      CourseNameMother.random(seed + 1),
      CourseDurationMother.random(seed + 2)
    );
  }
}

// tests/Contexts/Mooc/Courses/domain/CourseNameMother.ts
export class CourseNameMother {
  static create(value: string): CourseName { return CourseName.create(value); }
  static random(seed: number): CourseName {
    return this.create(WordMother.random({ seed, maxLength: 20 }));
  }
  static invalidName(): string { return 'a'.repeat(40); }
}

// tests/Contexts/Mooc/Courses/application/CreateCourseCommandMother.ts
export class CreateCourseCommandMother {
  static create(id: CourseId, name: CourseName, duration: CourseDuration): CreateCourseCommand {
    return { id: id.value, name: name.value, duration: duration.value };
  }

  static random(seed: number): CreateCourseCommand {
    return this.create(
      CourseIdMother.random(seed),
      CourseNameMother.random(seed + 1),
      CourseDurationMother.random(seed + 2)
    );
  }

  static invalid(seed: number): CreateCourseCommand {
    return {
      id: CourseIdMother.random(seed).value,
      name: CourseNameMother.invalidName(),  // 40 chars — exceeds limit
      duration: CourseDurationMother.random(seed + 1).value
    };
  }
}
```

**Practical heuristic:** Command Mothers produce flat primitives; Domain Mothers produce Value Objects. Keep them at the right layer — don't mix them.

---

## Unit Test Structure — Command Handler + Mock Repository + Mock EventBus

**Intent:** Show the idiomatic test structure: inject mock repository and EventBus, use Object Mothers to build inputs and expectations, use assertion helpers on the mock to verify side effects.

**Example:**
```typescript
// tests/Contexts/Mooc/Courses/application/CreateCourseCommandHandler.test.ts
let repository: CourseRepositoryMock;
let creator: CourseCreator;
let eventBus: EventBusMock;
let handler: CreateCourseCommandHandler;

beforeEach(() => {
  repository = new CourseRepositoryMock();
  eventBus = new EventBusMock();
  creator = new CourseCreator(repository, eventBus);
  handler = new CreateCourseCommandHandler(creator);
});

describe('CreateCourseCommandHandler', () => {
  it('should create a valid course', async () => {
    const command = CreateCourseCommandMother.random(42);
    const course = CourseMother.from(command);
    const domainEvent = CourseCreatedDomainEventMother.fromCourse(course);

    await handler.handle(command);

    repository.assertSaveHaveBeenCalledWith(course);
    eventBus.assertLastPublishedEventIs(domainEvent);
  });

  it('should throw error if course name length is exceeded', async () => {
    const command = CreateCourseCommandMother.invalid(42);

    await expect(handler.handle(command)).rejects.toThrow(CourseNameLengthExceeded);
  });
});
```

**Practical heuristic:** Mothers provide valid deterministic defaults; override values relevant to the behavior. Verify calls after Act so a missing interaction cannot skip an assertion. Use seeded generation only when variation is intentional and reproducible.
