# Kotlin DDD Examples (FP Style)

DDD building blocks in Kotlin, written in a functional style, working together in one bounded context: aggregates are immutable data, state changes return the new state together with its events, failures are values (Arrow `Either`) instead of exceptions, and ports are `suspend` functions. Infrastructure is a MongoDB adapter; tests use JUnit 5, MockK, and AssertJ. See `fp-best-practices` for the underlying functional style.

---

## Folder Structure

**Intent:** Organize code by Bounded Context, not by technical layer.

**How it works:** A `contexts` package holds one package per bounded context (e.g., `mooc`, `backoffice`). Each context contains sub-domains organized by aggregate. A `shared` context holds cross-cutting building blocks (error and event contracts, event bus). Inside each aggregate package, the split is always `domain` → `application` → `infrastructure`.

**Example:**
```
src/
  main/kotlin/com/example/contexts/
    mooc/
      courses/
        domain/
          Course.kt                     # Aggregate (immutable data)
          CourseResult.kt               # State + Events
          CourseDomainEvent.kt          # Domain Events (sealed)
          CourseError.kt                # Typed failures
          CourseId.kt                   # Value Object
          CourseName.kt                 # Value Object
          CourseDuration.kt             # Value Object
          CourseRepository.kt           # Port (interface)
        application/
          create/
            CourseCreator.kt            # Use Case (Application Service)
            CreateCourseCommand.kt      # Command DTO
            CreateCourseCommandHandler.kt
        infrastructure/
          persistence/
            mongo/
              MongoCourseRepository.kt  # Driven Adapter
    shared/
      domain/
        DomainError.kt
        DomainEvent.kt
        EventBus.kt
  test/kotlin/com/example/contexts/
    mooc/
      courses/
        domain/CourseMother.kt          # Object Mother
        application/CreateCourse...Test.kt
```

**Practical heuristic:** If you cannot tell from the package name alone which business capability the code serves, the structure is wrong. Package names like `controllers` or `services` are red flags.

---

## Value Objects and Typed Errors

**Intent:** Give domain values explicit construction, immutable representation, and semantic equality — and make invalid input a value the caller must handle.

**How it works:** A `value class` with a private constructor and a factory returning `Either`. Construction is the only way in, so every `CourseName` in the system is valid. Validation failures are cases of a sealed `CourseError`, so callers handle them with an exhaustive `when` and the compiler flags new cases. Infrastructure failures are a shared `InfrastructureError`; both implement the `DomainError` marker.

**Example:**
```kotlin
// contexts/shared/domain/DomainError.kt
interface DomainError

data class InfrastructureError(val reason: String, val cause: Throwable? = null) : DomainError

// contexts/mooc/courses/domain/CourseError.kt
sealed interface CourseError : DomainError {
    data class InvalidCourseId(val value: String) : CourseError
    data class InvalidCourseName(val value: String) : CourseError
    data class InvalidCourseDuration(val value: String) : CourseError
    data object InvalidCriteria : CourseError
}

// contexts/mooc/courses/domain/CourseId.kt
@JvmInline
value class CourseId private constructor(val value: String) {
    companion object {
        fun create(value: String): Either<CourseError.InvalidCourseId, CourseId> = either {
            ensure(Either.catch { UUID.fromString(value) }.isRight()) { CourseError.InvalidCourseId(value) }
            CourseId(value)
        }
    }
}

// contexts/mooc/courses/domain/CourseName.kt
@JvmInline
value class CourseName private constructor(val value: String) {
    companion object {
        fun create(raw: String): Either<CourseError.InvalidCourseName, CourseName> = either {
            val value = raw.trim()
            ensure(value.isNotEmpty() && value.length <= 30) { CourseError.InvalidCourseName(value) }
            CourseName(value)
        }
    }
}

// contexts/mooc/courses/domain/CourseDuration.kt
@JvmInline
value class CourseDuration private constructor(val value: String) {
    companion object {
        fun create(raw: String): Either<CourseError.InvalidCourseDuration, CourseDuration> = either {
            ensure(raw.isNotBlank()) { CourseError.InvalidCourseDuration(raw) }
            CourseDuration(raw.trim())
        }
    }
}
```

**Practical heuristic:** Transport DTOs, commands, and messages carry primitives. Convert at a deliberate boundary (the command handler, the adapter), then use Value Objects in domain APIs.

---

## Aggregate Result (State + Events)

**Intent:** Return the events a state change produced together with the new state, instead of collecting them inside the aggregate.

**How it works:** `CourseResult` pairs the new `Course` with the events that explain it. Domain functions that change state return it; the application service persists the state and hands the events on. There is no hidden event list to drain, so the only copy of an event cannot be cleared before handoff. Durable cross-process delivery requires handing the events to an Outbox in the same transaction as the Aggregate state.

**Example:**
```kotlin
// contexts/mooc/courses/domain/CourseResult.kt
data class CourseResult(val course: Course, val events: List<CourseDomainEvent>)
```

**Practical heuristic:** Never publish from inside the Aggregate. The application/Unit of Work owns durable handoff. Treat direct `save -> publish` as educational in-process delivery only; use `infrastructure-design` for transactional Outbox delivery.

---

## Aggregate (Concrete)

**Intent:** Model the aggregate as immutable data whose factory function enforces valid creation and returns the creation event.

**How it works:** `Course` is a `data class` of Value Objects, never raw primitives. Its constructor produces no events — used for reconstitution from persistence via `fromPrimitives()`. `Course.create()` is a pure function: event id and time are passed in, and it returns a `CourseResult` holding the new `Course` and `CourseCreated`. `fromPrimitives` rebuilds a `Course` through the Value Object factories and returns `null` when the data is missing or invalid instead of throwing.

**Example:**
```kotlin
// contexts/mooc/courses/domain/Course.kt
data class Course(
    val id: CourseId,
    val name: CourseName,
    val duration: CourseDuration,
) {
    fun toPrimitives(): Map<String, Any?> = mapOf(
        "id" to id.value,
        "name" to name.value,
        "duration" to duration.value,
    )

    companion object {
        // Creation: a new Course plus the event that records it
        fun create(
            id: CourseId,
            name: CourseName,
            duration: CourseDuration,
            eventId: UUID,
            now: Instant,
        ): CourseResult =
            CourseResult(
                course = Course(id, name, duration),
                events = listOf(CourseDomainEvent.CourseCreated(eventId, now, id, name, duration)),
            )

        // Reconstitution: used by the repository adapter — no events, null on corrupt data
        fun fromPrimitives(plainData: Map<String, Any?>): Course? {
            val id = (plainData["id"] as? String)?.let { CourseId.create(it).getOrNull() } ?: return null
            val name = (plainData["name"] as? String)?.let { CourseName.create(it).getOrNull() } ?: return null
            val duration = (plainData["duration"] as? String)?.let { CourseDuration.create(it).getOrNull() } ?: return null
            return Course(id, name, duration)
        }
    }
}
```

**Practical heuristic:** Keep creation and reconstitution separate so loading cannot emit creation events. Reconstitution returns a bare `Course?`, and the adapter decides what a `null` means. The Aggregate never reads a clock.

---

## Domain Events (Sealed)

**Intent:** Give every domain event a consistent structure — event ID and timestamp — while letting each concrete event define its own typed attributes.

**How it works:** `DomainEvent` declares the metadata every event carries. A `sealed interface` per aggregate lists every event it can produce, so subscribers and adapters map them with an exhaustive `when`. Each event is a `data class` of Value Objects. Metadata is passed in by the use case from an injected `Clock` and UUID generator, never generated inside the domain. Each concrete event declares `EVENT_NAME` in its companion object for the bus infrastructure.

**Example:**
```kotlin
// contexts/shared/domain/DomainEvent.kt
interface DomainEvent {
    val eventId: UUID
    val occurredOn: Instant
}

// contexts/mooc/courses/domain/CourseDomainEvent.kt
sealed interface CourseDomainEvent : DomainEvent {
    data class CourseCreated(
        override val eventId: UUID,
        override val occurredOn: Instant,
        val courseId: CourseId,
        val name: CourseName,
        val duration: CourseDuration,
    ) : CourseDomainEvent {
        companion object {
            const val EVENT_NAME = "course.created"
        }
    }
}
```

**Practical heuristic:** Name domain events in the past tense with dot notation: `course.created`, `payment.confirmed`. The `EVENT_NAME` constant is the contract between producers and consumers — treat it as an immutable API once deployed.

---

## Repository Port (Interface)

**Intent:** Declare what the domain needs from persistence in domain language, with no reference to any database technology.

**How it works:** The repository interface lives in the `domain` package — it is part of the domain layer, not infrastructure. Method names use domain vocabulary. Return types are domain objects, never raw database rows, wrapped in `Either` so infrastructure failures are values too. The interface is the driven port; concrete adapters (Mongo, Postgres, in-memory) implement it in `infrastructure`.

**Example:**
```kotlin
// contexts/mooc/courses/domain/CourseRepository.kt
interface CourseRepository {
    suspend fun save(course: Course): Either<InfrastructureError, Unit>
    suspend fun searchAll(): Either<InfrastructureError, List<Course>>
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
    suspend fun publish(events: List<DomainEvent>): Either<InfrastructureError, Unit>
    fun addSubscribers(subscribers: List<DomainEventSubscriber<*>>)
}

// contexts/shared/domain/DomainEventSubscriber.kt
interface DomainEventSubscriber<T : DomainEvent> {
    fun subscribedTo(): List<KClass<out T>>
    suspend fun on(domainEvent: T): Either<DomainError, Unit>
}
```

**Practical heuristic:** For best-effort in-process reactions, inject an in-memory bus or a mock. For production broker delivery, persist an Outbox atomically and let a relay publish to the broker; do not publish directly from this use case.

---

## Use Case (Application Service)

**Intent:** Orchestrate the domain — fetch, decide via the aggregate, persist, publish events — with no business logic of its own.

**How it works:** `CourseCreator` receives dependencies through constructor injection, including a `Clock` and a UUID generator so the domain stays pure and tests stay deterministic. Inside `either {}`, each `bind()` short-circuits on the first error. The Command Handler converts the flat command into Value Objects; invalid input returns a `Left`, nothing is thrown. The direct publication below is suitable only for best-effort in-process reactions; replace it with a Unit of Work plus Outbox when events must survive failures.

**Example:**
```kotlin
// contexts/mooc/courses/application/create/CourseCreator.kt
class CourseCreator(
    private val repository: CourseRepository,
    private val eventBus: EventBus,
    private val clock: Clock,
    private val generateUUID: () -> UUID,
) {
    suspend fun run(id: CourseId, name: CourseName, duration: CourseDuration): Either<InfrastructureError, Unit> =
        either {
            val result = Course.create(id, name, duration, generateUUID(), clock.instant())
            repository.save(result.course).bind()
            eventBus.publish(result.events).bind()
        }
}

// contexts/mooc/courses/application/create/CreateCourseCommandHandler.kt
class CreateCourseCommandHandler(
    private val courseCreator: CourseCreator,
) : CommandHandler<CreateCourseCommand> {

    override fun subscribedTo(): KClass<CreateCourseCommand> = CreateCourseCommand::class

    override suspend fun handle(command: CreateCourseCommand): Either<DomainError, Unit> = either {
        val id = CourseId.create(command.id).bind()
        val name = CourseName.create(command.name).bind()
        val duration = CourseDuration.create(command.duration).bind()
        courseCreator.run(id, name, duration).bind()
    }
}
```

**Practical heuristic:** A use case may branch for orchestration, absence, authorization outcomes, retries, or policy results, but it must not own domain policy that belongs in the model. Wire real time and ids (`Clock.systemUTC()`, `UUID::randomUUID`) at the composition root, never as defaults in the use case.

---

## Infrastructure: Mongo Repository (Driven Adapter)

**Intent:** Implement the repository port with MongoDB, keeping the `toPrimitives`/`fromPrimitives` mapping in the adapter.

**How it works:** `MongoCourseRepository` uses the MongoDB Kotlin coroutine driver. `save()` upserts by ID using `toPrimitives()`. Exceptions are caught at this boundary with `Either.catch` and become `InfrastructureError`. `searchAll()` translates raw Mongo documents back into aggregates with `fromPrimitives()`; a `null` (corrupt document) becomes an `InfrastructureError` instead of a crash.

**Example:**
```kotlin
// contexts/mooc/courses/infrastructure/persistence/mongo/MongoCourseRepository.kt
class MongoCourseRepository(database: MongoDatabase) : CourseRepository {

    private val courses = database.getCollection<Document>("courses")

    override suspend fun save(course: Course): Either<InfrastructureError, Unit> =
        Either.catch {
            val document = Document(course.toPrimitives() - "id")
            courses.updateOne(eq("_id", course.id.value), Document("\$set", document), UpdateOptions().upsert(true))
            Unit
        }.mapLeft(::infrastructureError)

    override suspend fun searchAll(): Either<InfrastructureError, List<Course>> = either {
        val documents = Either.catch { courses.find().toList() }.mapLeft(::infrastructureError).bind()
        documents.map { document ->
            ensureNotNull(Course.fromPrimitives(document + ("id" to document["_id"]))) {
                InfrastructureError("corrupt course ${document["_id"]}")
            }
        }
    }

    private fun infrastructureError(e: Throwable) = InfrastructureError(e.toString(), e)
}
```

**Practical heuristic:** The concrete adapter is the only place where `toPrimitives()` and `fromPrimitives()` are called, and the only place that catches exceptions. Everything else works with typed domain objects and `Either`.

---

## Command / Query Contracts

**Intent:** Give bus infrastructure type-safe command, query, response, and handler relationships.

**How it works:** Kotlin types are nominal, so marker interfaces distinguish command and query families. A query carries its response type. Handlers return the `KClass` they subscribe to, not a message instance.

**Example:**
```kotlin
// contexts/shared/domain/Command.kt
interface Command

// contexts/shared/domain/Query.kt
interface Query<R>

// Serialized/external commands carry flat primitives.
// contexts/mooc/courses/application/create/CreateCourseCommand.kt
data class CreateCourseCommand(
    val id: String,
    val name: String,
    val duration: String,
) : Command
```

**Practical heuristic:** Serialized commands carry transport primitives and are converted at the handler boundary. A trusted in-process command may carry Value Objects when that contract is deliberate and no serialization boundary is implied.

---

## CommandBus / QueryBus — CQRS Bus Interfaces

**Intent:** Decouple the driver adapter (controller, consumer) from the use case by routing through a bus.

**How it works:** `CommandBus` dispatches a command and returns success or a domain error. `QueryBus` infers the response type carried by `Query<R>`. Both are interfaces implemented in infrastructure.

**Example:**
```kotlin
// contexts/shared/domain/CommandBus.kt
interface CommandBus {
    suspend fun dispatch(command: Command): Either<DomainError, Unit>
}

// contexts/shared/domain/QueryBus.kt
interface QueryBus {
    suspend fun <R> ask(query: Query<R>): R
}

// contexts/shared/domain/CommandHandler.kt
interface CommandHandler<T : Command> {
    fun subscribedTo(): KClass<T>
    suspend fun handle(command: T): Either<DomainError, Unit>
}

// contexts/shared/domain/QueryHandler.kt
interface QueryHandler<R, Q : Query<R>> {
    fun subscribedTo(): KClass<Q>
    suspend fun handle(query: Q): R
}
```

**Practical heuristic:** The CQRS split is at the bus level: commands change state and return only success or a domain error; queries read state and return a response. Never mix the two in one handler.

---

## CommandBus — In-Memory Implementation

**Intent:** Provide an in-process bus for development and testing.

**How it works:** The registry maps message classes to handlers, keyed by the class each handler returns from `subscribedTo()`. A missing handler is a wiring defect, not a domain outcome, so the lookup fails fast with `error(...)` instead of returning a `Left`.

**Example:**
```kotlin
// contexts/shared/infrastructure/commandbus/CommandHandlers.kt
class CommandHandlers(commandHandlers: List<CommandHandler<*>>) {
    private val handlers: Map<KClass<*>, CommandHandler<*>> =
        commandHandlers.associateBy { it.subscribedTo() }

    // Safe: each handler is registered under the class it handles
    @Suppress("UNCHECKED_CAST")
    fun <T : Command> get(command: T): CommandHandler<T> =
        handlers[command::class] as? CommandHandler<T>
            ?: error("No handler registered for ${command::class}")
}

// contexts/shared/infrastructure/commandbus/InMemoryCommandBus.kt
class InMemoryCommandBus(private val commandHandlers: CommandHandlers) : CommandBus {
    override suspend fun dispatch(command: Command): Either<DomainError, Unit> =
        commandHandlers.get(command).handle(command)
}
```

**Practical heuristic:** The lookup key is the message class, not an instance. Mirror the same typed registry for queries. Buses that cross serialization boundaries use explicit stable message names instead of classes.

---

## Nullable Types — Absence

**Intent:** Express one canonical absence representation in a domain API, separate from failure.

**Example:**
```kotlin
// Usage in a repository return type: Left is a failure, Right(null) means absent
interface CourseRepository {
    suspend fun findById(id: CourseId): Either<InfrastructureError, Course?>
}
```

**Practical heuristic:** Use `T?` in domain APIs rather than `java.util.Optional`, Arrow `Option`, or sentinel values. Accept other representations only at an external boundary and normalize to `T?` immediately.

---

## Criteria Pattern — Flexible Repository Queries

**Intent:** Express genuinely dynamic query conditions without exposing SQL or storage syntax. Keep stable business searches as named methods and use a read-model query port for projections.

**How it works:** An immutable `Criteria` carries a typed predicate tree, stable logical fields, order, and one bounded page. `courseCriteria` validates it and returns `Either`. Infrastructure maps logical fields and operators to backend-native expressions and rejects unsupported ones.

**Example:**
```kotlin
sealed interface Predicate {
    data class Comparison(val field: Field, val operator: Operator, val value: String) : Predicate {
        enum class Field { NAME, DURATION, ID }
        enum class Operator { EQ, CONTAINS, GT }
    }

    data class And(val operands: List<Predicate>) : Predicate
}

data class Order(val field: Field, val direction: Direction) {
    enum class Field { NAME, ID }
    enum class Direction { ASC, DESC }
}

data class Page(val limit: Int, val offset: Int)

data class Criteria(
    val predicate: Predicate?,
    val order: List<Order>,
    val page: Page,
)

fun courseCriteria(input: Criteria): Either<CourseError.InvalidCriteria, Criteria> = either {
    ensure(input.page.limit in 1..100) { CourseError.InvalidCriteria }
    ensure(input.page.offset >= 0) { CourseError.InvalidCriteria }
    // A unique last sort key makes pagination stable
    ensure(input.order.lastOrNull()?.field == Order.Field.ID) { CourseError.InvalidCriteria }
    input
}

interface CourseRepository {
    suspend fun matching(criteria: Criteria): Either<InfrastructureError, List<Course>>
}
```

**Practical heuristic:** Criteria's layer follows its vocabulary: domain-named selectors may live with an Aggregate repository; generic filters belong to the application/query core. No HTTP parameter, SQL identifier, or Elasticsearch DSL belongs in this contract. Use `design-patterns-best-practices` for converter, pagination, and testing details.

---

## Object Mother Pattern — Test Data Factories

**Intent:** Centralize valid test data creation so tests stay short and readable. Each domain concept gets its own Mother with deterministic defaults and focused overrides.

**How it works:** Each Mother has `create(explicit params)` and may provide seeded generation for intentional variation. Value Object Mothers unwrap the factory `Either` and fail loudly on an invalid fixture — a broken fixture is a test bug, not a case to handle. If randomness is used, inject/print the seed so failures reproduce exactly.

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
    fun create(value: String): CourseName = CourseName.create(value).getOrElse { error("invalid fixture: $it") }
    fun random(seed: Long): CourseName = create("Course $seed")
    fun invalidName(): String = "a".repeat(40)
}

object CourseIdMother {
    fun create(value: String): CourseId = CourseId.create(value).getOrElse { error("invalid fixture: $it") }
    fun random(seed: Long): CourseId = create(UUID(0, seed).toString())
}

object CourseDurationMother {
    fun create(value: String): CourseDuration = CourseDuration.create(value).getOrElse { error("invalid fixture: $it") }
    fun random(seed: Long): CourseDuration = create("${seed % 10 + 1} hours")
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

**Intent:** Show the idiomatic test structure: inject a mock repository and EventBus plus a fixed clock and UUID, use Object Mothers to build inputs and expectations, and assert on the returned `Either` and the calls on the mocks.

**How it works:** JUnit 5 creates a new test class instance per test, so mocks declared as properties are fresh for every test. `Course` and events are data classes, so expected arguments compare by value; the fixed clock and UUID make event metadata deterministic. Invalid input returns a `Left` and nothing is saved.

**Example:**
```kotlin
// src/test/kotlin/.../contexts/mooc/courses/application/CreateCourseCommandHandlerTest.kt
class CreateCourseCommandHandlerTest {

    private val now = Instant.parse("2026-01-01T00:00:00Z")
    private val eventId = UUID.fromString("00000000-0000-0000-0000-000000000001")
    private val repository = mockk<CourseRepository> {
        coEvery { save(any()) } returns Unit.right()
    }
    private val eventBus = mockk<EventBus> {
        coEvery { publish(any()) } returns Unit.right()
    }
    private val creator = CourseCreator(repository, eventBus, Clock.fixed(now, ZoneOffset.UTC)) { eventId }
    private val handler = CreateCourseCommandHandler(creator)

    @Test
    fun `should create a valid course`() = runTest {
        val command = CreateCourseCommandMother.random(42)
        val course = CourseMother.from(command)
        val domainEvent = CourseCreated(eventId, now, course.id, course.name, course.duration)

        assertThat(handler.handle(command)).isEqualTo(Unit.right())

        coVerify { repository.save(course) }
        coVerify { eventBus.publish(listOf(domainEvent)) }
    }

    @Test
    fun `should return an error if course name length is exceeded`() = runTest {
        assertThat(handler.handle(CreateCourseCommandMother.invalid(42)))
            .isEqualTo(InvalidCourseName("a".repeat(40)).left())

        coVerify(exactly = 0) { repository.save(any()) }
    }
}
```

**Practical heuristic:** Mothers provide valid deterministic defaults; override values relevant to the behavior. Verify calls after Act so a missing interaction cannot skip an assertion. Use seeded generation only when variation is intentional and reproducible.
