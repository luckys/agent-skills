# Kotlin DDD Examples (CodelyTV Pattern)

Kotlin ports of the TypeScript DDD building blocks in `typescript-ddd-examples.md`, based on the CodelyTV `typescript-ddd-example` repository. These show the full stack of building blocks working together in a real bounded context. `Promise` maps to `suspend`; Jest maps to JUnit 5, MockK, and AssertJ.

Source: https://github.com/CodelyTV/typescript-ddd-example

---

## Folder Structure

**Intent:** Organize code by Bounded Context, not by technical layer.

**How it works:** A `contexts` package holds one package per bounded context (e.g., `mooc`, `backoffice`). Each context contains sub-domains organized by aggregate. A `shared` context holds cross-cutting building blocks (base classes, event bus, criteria). Inside each aggregate package, the split is always `domain` → `application` → `infrastructure`.

**Example:**
```
src/
  main/kotlin/com/example/contexts/
    mooc/
      courses/
        domain/
          Course.kt                    # Aggregate Root
          CourseRepository.kt          # Port (interface)
          CourseName.kt                # Value Object
          CourseDuration.kt            # Value Object
          CourseCreatedDomainEvent.kt  # Domain Event
        application/
          create/
            CourseCreator.kt           # Use Case (Application Service)
            CreateCourseCommand.kt     # Command DTO
            CreateCourseCommandHandler.kt
        infrastructure/
          persistence/
            mongo/
              MongoCourseRepository.kt # Driven Adapter
    shared/
      domain/
        AggregateRoot.kt
        DomainEvent.kt
        EventBus.kt
      infrastructure/
        persistence/
          mongo/
            MongoRepository.kt
  test/kotlin/com/example/contexts/
    mooc/
      courses/
        domain/CourseMother.kt         # Object Mother
        application/CreateCourse...Test.kt
```

**Practical heuristic:** If you cannot tell from the package name alone which business capability the code serves, the structure is wrong. Package names like `controllers` or `services` are red flags.

---

## Value Objects in Kotlin

**Intent:** Give domain values explicit construction, immutable representation, and semantic equality.

**How it works:** A `value class` or `data class` with a private constructor and a validating factory. Both generate structural `equals`/`hashCode`, so no shared base class is needed. Override equality only when the generated one is wrong for the domain: `Array` properties compare by reference, and `BigDecimal` equality includes scale.

**Example:**
```kotlin
// contexts/mooc/courses/domain/CourseName.kt
@JvmInline
value class CourseName private constructor(val value: String) {
    companion object {
        fun create(raw: String): CourseName {
            val value = raw.trim()
            if (value.isEmpty() || value.length > 30) throw CourseNameLengthExceeded(value)
            return CourseName(value)
        }
    }
}

// contexts/mooc/shared/domain/courses/CourseId.kt
@JvmInline
value class CourseId private constructor(val value: String) {
    companion object {
        fun create(value: String): CourseId {
            if (!isValidUuid(value)) throw InvalidCourseId(value)
            return CourseId(value)
        }
    }
}
```

**Practical heuristic:** Transport DTOs, commands, and messages normally carry primitives. Convert at a deliberate application/domain boundary, then use Value Objects in domain APIs where semantic distinction or guarantees justify them.

---

## AggregateRoot Base Class

**Intent:** Give every aggregate root the ability to collect domain events before publishing them, and enforce serialization to primitives.

**How it works:** `AggregateRoot` maintains a private list of domain events. The aggregate records an event via `record()` when state changes. A best-effort in-process application service can drain these events after persistence. Durable cross-process delivery requires handing them to an Outbox in the same transaction as Aggregate state; do not clear the only event copy before durable handoff.

**Example:**
```kotlin
// contexts/shared/domain/AggregateRoot.kt
abstract class AggregateRoot {
    private val domainEvents = mutableListOf<DomainEvent>()

    fun pullDomainEvents(): List<DomainEvent> {
        val events = domainEvents.toList()
        domainEvents.clear()
        return events
    }

    fun record(event: DomainEvent) {
        domainEvents += event
    }

    abstract fun toPrimitives(): Map<String, Any?>
}
```

**Practical heuristic:** Never publish from inside the Aggregate. The application/Unit of Work owns durable handoff. Treat direct `save -> pull -> publish` as educational in-process delivery only; use `infrastructure-design` for transactional Outbox delivery.

---

## Aggregate Root (Concrete)

**Intent:** Implement a rich aggregate root that uses the static factory method pattern to enforce valid creation and record domain events.

**How it works:** The `Course` aggregate extends `AggregateRoot`. Construction through the constructor is valid but does not produce events — used for reconstitution from persistence via `fromPrimitives()`. Creation through the `Course.create()` factory method records the `CourseCreatedDomainEvent`. All fields are typed as Value Objects, never raw primitives.

**Example:**
```kotlin
// contexts/mooc/courses/domain/Course.kt
class Course(
    val id: CourseId,
    val name: CourseName,
    val duration: CourseDuration,
) : AggregateRoot() {

    override fun toPrimitives(): Map<String, Any?> = mapOf(
        "id" to id.value,
        "name" to name.value,
        "duration" to duration.value,
    )

    companion object {
        // Factory: creates a new Course and records the creation event
        fun create(id: CourseId, name: CourseName, duration: CourseDuration): Course {
            val course = Course(id, name, duration)
            course.record(
                CourseCreatedDomainEvent(
                    aggregateId = course.id.value,
                    duration = course.duration.value,
                    name = course.name.value,
                ),
            )
            return course
        }

        // Reconstitution: used by the repository adapter — no events recorded
        fun fromPrimitives(plainData: Map<String, Any?>): Course =
            Course(
                CourseId.create(plainData["id"] as String),
                CourseName.create(plainData["name"] as String),
                CourseDuration(plainData["duration"] as String),
            )
    }
}
```

**Practical heuristic:** Keep creation and reconstitution semantically separate so loading cannot emit creation events. `create()` plus `fromPrimitives()` is one valid strategy; a dedicated mapper is another.

---

## DomainEvent Base Class

**Intent:** Give every domain event a consistent structure — event name, aggregate ID, event ID, and timestamp — while letting each concrete event define its own typed attributes.

**How it works:** The abstract `DomainEvent` stores metadata automatically (generating `eventId` as a UUID and `occurredOn` as now if not provided). Kotlin has no abstract static members, so each concrete event declares `EVENT_NAME` and a `fromPrimitives()` factory (used by message bus infrastructure for deserialization) in its companion object, and implements `toPrimitives()` for serialization. `Instant` is immutable and always valid, so no defensive copy or date validation is needed.

**Example:**
```kotlin
// contexts/shared/domain/DomainEvent.kt
abstract class DomainEvent(
    val eventName: String,
    val aggregateId: String,
    eventId: String?,
    occurredOn: Instant?,
) {
    val eventId: String = eventId ?: UUID.randomUUID().toString()
    val occurredOn: Instant = occurredOn ?: Instant.now()

    abstract fun toPrimitives(): Map<String, Any?>
}

// contexts/mooc/courses/domain/CourseCreatedDomainEvent.kt
class CourseCreatedDomainEvent(
    aggregateId: String,
    val name: String,
    val duration: String,
    eventId: String? = null,
    occurredOn: Instant? = null,
) : DomainEvent(EVENT_NAME, aggregateId, eventId, occurredOn) {

    override fun toPrimitives(): Map<String, Any?> =
        mapOf("name" to name, "duration" to duration)

    companion object {
        const val EVENT_NAME = "course.created"

        // Used by the event bus infrastructure to deserialize incoming messages
        fun fromPrimitives(
            aggregateId: String,
            attributes: Map<String, Any?>,
            eventId: String,
            occurredOn: Instant,
        ): CourseCreatedDomainEvent =
            CourseCreatedDomainEvent(
                aggregateId = aggregateId,
                duration = attributes["duration"] as String,
                name = attributes["name"] as String,
                eventId = eventId,
                occurredOn = occurredOn,
            )
    }
}
```

**Practical heuristic:** Name domain events in the past tense with dot notation: `course.created`, `payment.confirmed`. The `EVENT_NAME` constant is the contract between producers and consumers — treat it as an immutable API once deployed.

---

## Repository Port (Interface)

**Intent:** Declare what the domain needs from persistence in domain language, with no reference to any database technology.

**How it works:** The repository interface lives in the `domain` package — it is part of the domain layer, not infrastructure. Method names use domain vocabulary. Return types are domain objects or aggregates, never raw database rows. The interface is the driven port; concrete adapters (Mongo, Postgres, in-memory) implement it in `infrastructure`.

**Example:**
```kotlin
// contexts/mooc/courses/domain/CourseRepository.kt
interface CourseRepository {
    suspend fun save(course: Course)
    suspend fun searchAll(): List<Course>
}
```

**Practical heuristic:** If you find yourself adding methods like `findByRawQuery()` or `executeSql()` to a repository interface, the abstraction has broken down. Keep the interface in domain terms only.

---

## EventBus Port (Interface)

**Intent:** Declare the outbound event publishing contract so the domain layer never depends on RabbitMQ, Kafka, or any specific broker.

**Example:**
```kotlin
// contexts/shared/domain/EventBus.kt
interface EventBus {
    suspend fun publish(events: List<DomainEvent>)
    fun addSubscribers(subscribers: DomainEventSubscribers)
}

// contexts/shared/domain/DomainEventSubscriber.kt
interface DomainEventSubscriber<T : DomainEvent> {
    fun subscribedTo(): List<KClass<out DomainEvent>>
    suspend fun on(domainEvent: T)
}
```

**Practical heuristic:** For best-effort in-process reactions, inject an in-memory bus or a mock. For production broker delivery, persist an Outbox atomically and let a relay publish to the broker; do not publish directly from this use case.

---

## Use Case (Application Service)

**Intent:** Orchestrate the domain — fetch, mutate via the aggregate, persist, publish events — with no business logic of its own.

**How it works:** `CourseCreator` receives dependencies through constructor injection. The Command Handler translates the flat DTO command into typed Value Objects. The direct publication below is suitable only for best-effort in-process reactions; replace it with a Unit of Work plus Outbox when events must survive failures.

**Example:**
```kotlin
// contexts/mooc/courses/application/create/CourseCreator.kt
class CourseCreator(
    private val repository: CourseRepository,
    private val eventBus: EventBus,
) {
    suspend fun run(id: CourseId, name: CourseName, duration: CourseDuration) {
        val course = Course.create(id, name, duration)
        repository.save(course)
        eventBus.publish(course.pullDomainEvents())
    }
}

// contexts/mooc/courses/application/create/CreateCourseCommandHandler.kt
class CreateCourseCommandHandler(
    private val courseCreator: CourseCreator,
) : CommandHandler<CreateCourseCommand> {

    override fun subscribedTo(): KClass<CreateCourseCommand> = CreateCourseCommand::class

    override suspend fun handle(command: CreateCourseCommand) {
        val id = CourseId.create(command.id)
        val name = CourseName.create(command.name)
        val duration = CourseDuration(command.duration)
        courseCreator.run(id, name, duration)
    }
}
```

**Practical heuristic:** A use case may branch for orchestration, absence, authorization outcomes, retries, or policy results, but it must not own domain policy that belongs in the model. Treat it as a traffic controller, not as a rule-free syntax exercise.

---

## Infrastructure: MongoRepository Base (Driven Adapter)

**Intent:** Provide a reusable base class for all MongoDB-backed repository adapters, keeping the toPrimitives/fromPrimitives mapping in each concrete class.

**How it works:** `MongoRepository<T>` is generic over any `AggregateRoot` and uses the MongoDB Kotlin coroutine driver. It provides `persist()` (upsert by ID using `toPrimitives()`). Concrete repository classes extend this base and implement `collectionName()`. The `fromPrimitives()` call translates raw Mongo documents back into domain aggregates.

**Example:**
```kotlin
import com.mongodb.client.model.Filters.eq
import com.mongodb.client.model.UpdateOptions
import com.mongodb.kotlin.client.coroutine.MongoCollection
import com.mongodb.kotlin.client.coroutine.MongoDatabase
import kotlinx.coroutines.flow.toList
import org.bson.Document

// contexts/shared/infrastructure/persistence/mongo/MongoRepository.kt
abstract class MongoRepository<T : AggregateRoot>(private val database: MongoDatabase) {

    protected abstract fun collectionName(): String

    protected fun collection(): MongoCollection<Document> =
        database.getCollection<Document>(collectionName())

    protected suspend fun persist(id: String, aggregateRoot: T) {
        val document = Document(aggregateRoot.toPrimitives() - "id")
        collection().updateOne(eq("_id", id), Document("\$set", document), UpdateOptions().upsert(true))
    }
}

// Concrete adapter (in infrastructure/persistence/mongo/)
class MongoCourseRepository(database: MongoDatabase) :
    MongoRepository<Course>(database), CourseRepository {

    override fun collectionName(): String = "courses"

    override suspend fun save(course: Course) {
        persist(course.id.value, course)
    }

    override suspend fun searchAll(): List<Course> =
        collection().find().toList()
            .map { document -> Course.fromPrimitives(document + ("id" to document["_id"])) }
}
```

**Practical heuristic:** The concrete adapter is the only place where `toPrimitives()` and `fromPrimitives()` are called. Everything else in the system works with typed domain objects.

---

## Command / Query Contracts

**Intent:** Give bus infrastructure type-safe command, query, response, and handler relationships.

**How it works:** Kotlin types are nominal, so marker interfaces distinguish command and query families — TypeScript's brand fields are unnecessary. A query carries its response type. Handlers return the `KClass` they subscribe to, not a message instance.

**Example:**
```kotlin
interface Command

interface Query<R>

// Serialized/external commands normally carry flat primitives.
// contexts/mooc/courses/application/create/CreateCourseCommand.kt
data class CreateCourseCommand(
    val id: String,
    val name: String,
    val duration: String,
) : Command
```

**Practical heuristic:** Serialized commands normally carry transport primitives and are converted at the handler boundary. A trusted in-process command may carry Value Objects when that contract is deliberate and no serialization boundary is implied.

---

## CommandBus / QueryBus — CQRS Bus Interfaces

**Intent:** Decouple the controller (driver adapter) from the use case by routing through a bus. The controller does not need to know which handler exists — it only dispatches a command or queries with a query.

**How it works:** `CommandBus` dispatches a command and returns completion. `QueryBus` infers the response type carried by `Query<R>`. Both are interfaces implemented in infrastructure.

**Example:**
```kotlin
// contexts/shared/domain/CommandBus.kt
interface CommandBus {
    suspend fun dispatch(command: Command)
}

// contexts/shared/domain/QueryBus.kt
interface QueryBus {
    suspend fun <R> ask(query: Query<R>): R
}

// contexts/shared/domain/CommandHandler.kt
interface CommandHandler<T : Command> {
    fun subscribedTo(): KClass<T>
    suspend fun handle(command: T)
}

// contexts/shared/domain/QueryHandler.kt
interface QueryHandler<R, Q : Query<R>> {
    fun subscribedTo(): KClass<Q>
    suspend fun handle(query: Q): R
}
```

**Practical heuristic:** CQRS split is at the bus level: commands mutate state and return nothing; queries read state and return a response. Never mix the two in one handler.

---

## CommandBus / QueryBus — In-Memory Implementations

**Intent:** Provide an in-process bus for development and testing. The registry (`CommandHandlers`, `QueryHandlers`) maps command/query classes to their handlers.

**How it works:** The registry maps message classes to handlers. Handlers register the concrete class returned by `subscribedTo()`. The bus looks up `command::class` at dispatch time and fails explicitly when no handler exists.

**Example:**
```kotlin
// contexts/shared/infrastructure/commandbus/CommandHandlers.kt
class CommandHandlers(commandHandlers: List<CommandHandler<*>>) {
    private val handlers: Map<KClass<*>, CommandHandler<*>> =
        commandHandlers.associateBy { it.subscribedTo() }

    // Safe: each handler is registered under the class it handles
    @Suppress("UNCHECKED_CAST")
    fun <T : Command> get(command: T): CommandHandler<T> =
        handlers[command::class] as CommandHandler<T>?
            ?: throw CommandNotRegisteredError(command)
}

// contexts/shared/infrastructure/commandbus/InMemoryCommandBus.kt
class InMemoryCommandBus(private val commandHandlers: CommandHandlers) : CommandBus {
    override suspend fun dispatch(command: Command) {
        commandHandlers.get(command).handle(command)
    }
}
```

**Practical heuristic:** The lookup key is the message class, not an instance. Mirror the same typed class registry for queries. More elaborate buses can use explicit stable message names when classes cannot cross serialization boundaries.

---

## Nullable Types — Absence

**Intent:** Express one canonical absence representation in a domain API.

**Example:**
```kotlin
// Kotlin's built-in T? is the single absence representation — no utility type needed
interface CourseRepository {
    suspend fun findById(id: CourseId): Course?
}
```

**Practical heuristic:** Use `T?` in domain APIs rather than `java.util.Optional`, Arrow `Option`, or sentinel values. Accept other representations (Java platform types, `Optional`) only at an external boundary and normalize to `T?` immediately.

---

## Criteria Pattern — Flexible Repository Queries

**Intent:** Express genuinely dynamic query conditions without exposing SQL or storage syntax. Keep stable business searches as named methods and use a read-model query port for projections.

**How it works:** A validated immutable Criteria carries a typed predicate tree, stable logical fields, order, and one bounded pagination variant. Infrastructure maps logical fields/operators to backend-native expressions and rejects unsupported semantics.

**Example:**
```kotlin
sealed interface Predicate {
    data class Comparison(val field: Field, val operator: Operator, val value: String) : Predicate {
        enum class Field { NAME, PUBLISHED_AT, ID }
        enum class Operator { EQ, CONTAINS, GT }
    }

    data class And(val operands: List<Predicate>) : Predicate
}

data class Order(val field: Field, val direction: Direction) {
    enum class Field { PUBLISHED_AT, ID }
    enum class Direction { ASC, DESC }
}

data class Page(val limit: Int, val offset: Int)

data class Criteria(
    val predicate: Predicate?,
    val order: List<Order>,
    val page: Page,
)

class InvalidCriteria : Exception()

fun courseCriteria(input: Criteria): Criteria {
    if (input.page.limit !in 1..100) throw InvalidCriteria()
    if (input.page.offset < 0) throw InvalidCriteria()
    if (input.order.lastOrNull()?.field != Order.Field.ID) throw InvalidCriteria()
    // vals are already immutable; copy the list in case the caller passed a MutableList
    return input.copy(order = input.order.toList())
}

interface CourseRepository {
    suspend fun matching(criteria: Criteria): List<Course>
}
```

**Practical heuristic:** Criteria's layer follows its vocabulary: domain-named selectors may live with an Aggregate repository; generic filters belong to the application/query core. No HTTP parameter, SQL identifier, or Elasticsearch DSL belongs in this contract. Use `design-patterns-best-practices` for converter, pagination, and testing details.

---

## Object Mother Pattern — Test Data Factories

**Intent:** Centralize valid test data creation so tests stay short and readable. Each domain concept gets its own Mother object with deterministic defaults and focused overrides.

**How it works:** Each Mother has `create(explicit params)` and may provide seeded generation for intentional variation. The test specifies every value relevant to its rule. If randomness is used, inject/print the seed so failures reproduce exactly.

**Example:**
```kotlin
// src/test/kotlin/.../contexts/mooc/courses/domain/CourseMother.kt
object CourseMother {
    fun create(id: CourseId, name: CourseName, duration: CourseDuration): Course =
        Course(id, name, duration)

    fun from(command: CreateCourseCommand): Course =
        create(
            CourseIdMother.create(command.id),
            CourseNameMother.create(command.name),
            CourseDurationMother.create(command.duration),
        )

    fun random(seed: Long): Course =
        create(
            CourseIdMother.random(seed),
            CourseNameMother.random(seed + 1),
            CourseDurationMother.random(seed + 2),
        )
}

// src/test/kotlin/.../contexts/mooc/courses/domain/CourseNameMother.kt
object CourseNameMother {
    fun create(value: String): CourseName = CourseName.create(value)
    fun random(seed: Long): CourseName = create(WordMother.random(seed = seed, maxLength = 20))
    fun invalidName(): String = "a".repeat(40)
}

// src/test/kotlin/.../contexts/mooc/courses/application/CreateCourseCommandMother.kt
object CreateCourseCommandMother {
    fun create(id: CourseId, name: CourseName, duration: CourseDuration): CreateCourseCommand =
        CreateCourseCommand(id = id.value, name = name.value, duration = duration.value)

    fun random(seed: Long): CreateCourseCommand =
        create(
            CourseIdMother.random(seed),
            CourseNameMother.random(seed + 1),
            CourseDurationMother.random(seed + 2),
        )

    fun invalid(seed: Long): CreateCourseCommand =
        CreateCourseCommand(
            id = CourseIdMother.random(seed).value,
            name = CourseNameMother.invalidName(), // 40 chars — exceeds limit
            duration = CourseDurationMother.random(seed + 1).value,
        )
}
```

**Practical heuristic:** Command Mothers produce flat primitives; Domain Mothers produce Value Objects. Keep them at the right layer — don't mix them.

---

## Unit Test Structure — Command Handler + Mock Repository + Mock EventBus

**Intent:** Show the idiomatic test structure: inject mock repository and EventBus, use Object Mothers to build inputs and expectations, verify side effects on the mocks.

**How it works:** JUnit 5 creates a new test class instance per test, so mocks declared as properties are fresh for every test. `Course` and the event have identity equality, so captured arguments are compared field by field with AssertJ; generated event metadata is ignored.

**Example:**
```kotlin
// src/test/kotlin/.../contexts/mooc/courses/application/CreateCourseCommandHandlerTest.kt
class CreateCourseCommandHandlerTest {

    private val repository = mockk<CourseRepository>(relaxUnitFun = true)
    private val eventBus = mockk<EventBus>(relaxUnitFun = true)
    private val creator = CourseCreator(repository, eventBus)
    private val handler = CreateCourseCommandHandler(creator)

    @Test
    fun `should create a valid course`() = runTest {
        val command = CreateCourseCommandMother.random(42)
        val course = CourseMother.from(command)
        val domainEvent = CourseCreatedDomainEventMother.fromCourse(course)

        handler.handle(command)

        val saved = slot<Course>()
        val published = slot<List<DomainEvent>>()
        coVerify { repository.save(capture(saved)) }
        coVerify { eventBus.publish(capture(published)) }
        assertThat(saved.captured).usingRecursiveComparison().isEqualTo(course)
        assertThat(published.captured.last())
            .usingRecursiveComparison()
            .ignoringFields("eventId", "occurredOn")
            .isEqualTo(domainEvent)
    }

    @Test
    fun `should throw error if course name length is exceeded`() = runTest {
        val command = CreateCourseCommandMother.invalid(42)

        assertThrows<CourseNameLengthExceeded> { handler.handle(command) }
    }
}
```

**Practical heuristic:** Mothers provide valid deterministic defaults; override values relevant to the behavior. Verify calls after Act so a missing interaction cannot skip an assertion. Use seeded generation only when variation is intentional and reproducible.
