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

## ValueObject Base Class

**Intent:** Enforce immutability, null safety, and structural equality for all Value Objects from a single base class.

**How it works:** The generic `ValueObject<T>` holds the primitive value as `readonly`, rejects null/undefined in the constructor, and provides `equals()` by constructor name + value comparison. Concrete value objects extend `StringValueObject` or `Uuid` — which themselves extend `ValueObject` — adding domain-specific validation.

**Example:**
```typescript
// src/Contexts/Shared/domain/value-object/ValueObject.ts
export type Primitives = String | string | number | Boolean | boolean | Date;

export abstract class ValueObject<T extends Primitives> {
  readonly value: T;

  constructor(value: T) {
    this.value = value;
    this.ensureValueIsDefined(value);
  }

  private ensureValueIsDefined(value: T): void {
    if (value === null || value === undefined) {
      throw new InvalidArgumentError('Value must be defined');
    }
  }

  equals(other: ValueObject<T>): boolean {
    return other.constructor.name === this.constructor.name && other.value === this.value;
  }

  toString(): string {
    return this.value.toString();
  }
}

// src/Contexts/Shared/domain/value-object/StringValueObject.ts
export abstract class StringValueObject extends ValueObject<string> {}

// src/Contexts/Shared/domain/value-object/Uuid.ts
export class Uuid extends ValueObject<string> {
  constructor(value: string) {
    super(value);
    this.ensureIsValidUuid(value);
  }

  static random(): Uuid {
    return new Uuid(uuid());
  }

  private ensureIsValidUuid(id: string): void {
    if (!validate(id)) {
      throw new InvalidArgumentError(`<${this.constructor.name}> does not allow the value <${id}>`);
    }
  }
}

// src/Contexts/Mooc/Courses/domain/CourseName.ts
export class CourseName extends StringValueObject {
  constructor(value: string) {
    super(value);
    this.ensureLengthIsLessThan30Characters(value);
  }

  private ensureLengthIsLessThan30Characters(value: string): void {
    if (value.length > 30) {
      throw new CourseNameLengthExceeded(`The Course Name <${value}> has more than 30 characters`);
    }
  }
}

// src/Contexts/Mooc/Shared/domain/Courses/CourseId.ts
// ID value objects simply extend Uuid — no additional code needed
export class CourseId extends Uuid {}
```

**Practical heuristic:** Every primitive you pass across a layer boundary (string IDs, string names, numeric amounts) should be wrapped in a Value Object. The wrapper is where validation, formatting, and equality live.

---

## AggregateRoot Base Class

**Intent:** Give every aggregate root the ability to collect domain events before publishing them, and enforce serialization to primitives.

**How it works:** `AggregateRoot` maintains a private list of domain events. The aggregate records an event via `record()` when state changes. The application service calls `pullDomainEvents()` after persisting — this returns the events and clears the list, so events are never published twice. The abstract `toPrimitives()` forces each concrete aggregate to define how it serializes to a plain object for persistence.

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

**Practical heuristic:** Never call `pullDomainEvents()` inside the aggregate itself. The application service — not the aggregate — is responsible for publishing events after the repository save completes.

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
      new CourseId(plainData.id),
      new CourseName(plainData.name),
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

**Practical heuristic:** Always have two paths into an aggregate: a static factory for new instances (records events) and `fromPrimitives` for reconstitution from storage (no events). Never let infrastructure call `create()` when loading from the database.

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
  readonly occurredOn: Date;
  readonly eventName: string;

  constructor(params: {
    eventName: string;
    aggregateId: string;
    eventId?: string;
    occurredOn?: Date;
  }) {
    this.aggregateId = params.aggregateId;
    this.eventId = params.eventId || Uuid.random().value;
    this.occurredOn = params.occurredOn || new Date();
    this.eventName = params.eventName;
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

**Practical heuristic:** The application service receives `EventBus` by constructor injection. At test time, inject an in-memory spy. At production time, inject the RabbitMQ adapter.

---

## Use Case (Application Service)

**Intent:** Orchestrate the domain — fetch, mutate via the aggregate, persist, publish events — with no business logic of its own.

**How it works:** `CourseCreator` receives its dependencies through constructor injection (both typed as interfaces, never concrete classes). The `run()` method follows a fixed sequence: create the aggregate via its factory, save via the repository, publish events from `pullDomainEvents()`. The Command Handler translates the flat DTO command into typed Value Objects before calling the use case.

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

  subscribedTo(): Command {
    return CreateCourseCommand;
  }

  async handle(command: CreateCourseCommand): Promise<void> {
    const id       = new CourseId(command.id);
    const name     = new CourseName(command.name);
    const duration = new CourseDuration(command.duration);
    await this.courseCreator.run({ id, name, duration });
  }
}
```

**Practical heuristic:** The use case (`CourseCreator.run`) should contain no `if` statements. Branching on domain conditions belongs inside the aggregate. The use case is the "traffic cop" — it sequences calls but makes no domain decisions.

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
