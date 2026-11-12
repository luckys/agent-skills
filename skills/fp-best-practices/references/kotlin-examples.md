# Kotlin — Functional Programming Examples

Concepts covered: pure functions, collection pipelines, `let`, composition, partial application, nullable types, Either, immutable data classes, higher-order functions, sealed interfaces, the `either {}` builder, side effect boundary.

Kotlin is a multi-paradigm language on the JVM. The standard library covers immutable data, nullable types, and collection pipelines; Arrow (`arrow-core`, examples use 1.2) adds `Either`, the `either {}` builder, composition, and partial application.

---

## Pure Functions and Referential Transparency

```kotlin
// val bindings cannot be reassigned (var opts in to mutation, rarely needed)

fun applyDiscount(rate: Double, price: Double): Double =
    price * (1.0 - rate)

// Referentially transparent — applyDiscount(0.1, 100.0) == 90.0, always

// Data class — immutable product type when every property is a val
data class Cart(val items: List<Item>, val couponCode: String?)

fun addItem(cart: Cart, item: Item): Cart =
    cart.copy(items = listOf(item) + cart.items)
// copy — creates a new Cart, original unchanged
// List is a read-only view: never expose a MutableList through it
```

---

## Pipelines (chaining, `let`) and Composition (`andThen`)

```kotlin
import arrow.core.andThen

// Collection operations chain left to right, like |>
fun processOrder(orders: List<Order>): Double =
    orders
        .filter { it.active }
        .map { it.total }
        .sum()

// andThen (Arrow) — left-to-right composition (f andThen g = g(f(x)))
val normalizeEmail: (String) -> String =
    { s: String -> s.trim() } andThen { s -> s.lowercase() }

// let — pipes any value into a function
val email = rawEmail.let(normalizeEmail)

// Multiple pipeline steps with named helpers
val filterActive: (List<Order>) -> List<Order> = { orders -> orders.filter { it.active } }
val calculateTotals: (List<Order>) -> List<Double> = { orders -> orders.map { it.total } }
val grandTotal: (List<Double>) -> Double = { totals -> totals.sum() }

val summarize = filterActive andThen calculateTotals andThen grandTotal
```

---

## Partial Application and Currying

```kotlin
import arrow.core.curried
import arrow.core.partially1

// Kotlin functions are not curried — fix arguments with a lambda or Arrow's partiallyN

fun add(x: Int, y: Int): Int = x + y

val add5: (Int) -> Int = ::add.partially1(5)   // partial application

val curriedAdd: (Int) -> (Int) -> Int = ::add.curried()   // explicit currying
val add5Curried: (Int) -> Int = curriedAdd(5)

// Using partial application with a pipeline
val applyTenPercent: (Double) -> Double = ::applyDiscount.partially1(0.1)

val discounted = listOf(100.0, 200.0, 300.0).map(applyTenPercent)   // [90.0, 180.0, 270.0]
// or a plain lambda: .map { applyDiscount(0.1, it) }
```

---

## Nullable Types — Explicit Absence

```kotlin
import arrow.core.raise.nullable

// T? is either a T or null — the compiler forces the null case to be handled

fun findUser(id: String, db: Map<String, User>): User? =
    db[id]

// when — must handle both cases
fun describeUser(maybeUser: User?): String =
    when (maybeUser) {
        null -> "User not found"
        else -> "Found: ${maybeUser.name}"
    }

// ?. — transform if present (Option.map)
fun getEmail(maybeUser: User?): String? =
    maybeUser?.email
// or: maybeUser?.let { it.email }

// ?. chain — chain optional computations (Option.bind / flatMap)
fun getCity(user: User): String? =
    user.address?.city

// ?: — provide a fallback (Option.defaultValue)
fun displayCity(user: User): String =
    getCity(user) ?: "Unknown city"

// nullable builder (Arrow) — bind() short-circuits on null
fun getCityBuilder(user: User): String? = nullable {
    val address = user.address.bind()
    address.city.bind()
}
```

---

## Either — Explicit Failure

```kotlin
import arrow.core.Either
import arrow.core.flatMap
import arrow.core.left
import arrow.core.raise.either
import arrow.core.right

// Either<E, A> = Left(E) | Right(A); kotlin.Result fixes the error type to Throwable

sealed interface ValidationError {
    data object InvalidEmail : ValidationError
    data object InvalidAge : ValidationError
}

data class User(val email: String, val age: Int)

fun validateEmail(email: String): Either<ValidationError, String> =
    if ("@" in email) email.lowercase().right()
    else ValidationError.InvalidEmail.left()

fun validateAge(age: Int): Either<ValidationError, Int> =
    if (age in 0..150) age.right()
    else ValidationError.InvalidAge.left()

// either builder — chains Either values, short-circuits on Left
fun parseUser(email: String, age: Int): Either<ValidationError, User> =
    either {
        val validEmail = validateEmail(email).bind()
        val validAge = validateAge(age).bind()
        User(email = validEmail, age = validAge)
    }

// Pattern match at the call site
fun showResult(res: Either<ValidationError, User>): String =
    when (res) {
        is Either.Left -> when (res.value) {
            ValidationError.InvalidEmail -> "Bad email"
            ValidationError.InvalidAge -> "Bad age"
        }
        is Either.Right -> "User: ${res.value.email}"
    }

// map and flatMap for pipeline style
fun processEmail(email: String): Either<ValidationError, String> =
    validateEmail(email)
        .flatMap { e -> if (e.length > 5) e.right() else ValidationError.InvalidEmail.left() }
        .map { e -> e.uppercase() }
```

---

## Sealed Interfaces — Sum Types

```kotlin
import java.time.LocalDateTime

// sealed interface — exactly one variant at a time
sealed interface OrderStatus {
    data object Pending : OrderStatus
    data class Shipped(val trackingCode: String) : OrderStatus
    data class Delivered(val deliveredAt: LocalDateTime) : OrderStatus
    data class Cancelled(val reason: String) : OrderStatus
}

// Exhaustive when — the compiler rejects missing cases when when is an expression
fun describeStatus(status: OrderStatus): String =
    when (status) {
        OrderStatus.Pending -> "Awaiting shipment"
        is OrderStatus.Shipped -> "Shipped — ${status.trackingCode}"
        is OrderStatus.Delivered -> "Delivered on ${status.deliveredAt.toLocalDate()}"
        is OrderStatus.Cancelled -> "Cancelled: ${status.reason}"
    }

// Recursive sealed interface
sealed interface Tree<out A> {
    data object Leaf : Tree<Nothing>
    data class Node<out A>(val value: A, val left: Tree<A>, val right: Tree<A>) : Tree<A>
}

fun <A> depth(tree: Tree<A>): Int =
    when (tree) {
        Tree.Leaf -> 0
        is Tree.Node -> 1 + maxOf(depth(tree.left), depth(tree.right))
    }
```

---

## Immutable Data Classes

```kotlin
data class Address(val street: String, val city: String)
data class User(val id: String, val name: String, val email: String, val address: Address?)

// copy — copy-and-update
fun updateEmail(user: User, newEmail: String): User =
    user.copy(email = newEmail)

// Nested update
fun updateCity(user: User, city: String): User =
    when (val address = user.address) {
        null -> user
        else -> user.copy(address = address.copy(city = city))
    }

// Value class for nominal typing (equivalent to single-case DUs in F#, branded types in TS)
@JvmInline value class UserId(val value: String)
@JvmInline value class OrderId(val value: String)

fun getUser(id: UserId): User? = db.users.findById(id.value)

val orderId = OrderId("order-123")
// getUser(orderId)  — type error! OrderId ≠ UserId
```

---

## Higher-Order Functions

```kotlin
// map :: ((A) -> B) -> List<A> -> List<B>
val doubled = listOf(1, 2, 3).map { it * 2 }   // [2, 4, 6]

// filter :: ((A) -> Boolean) -> List<A> -> List<A>
val evens = (1..10).filter { it % 2 == 0 }   // [2, 4, 6, 8, 10]

// fold :: (B, (B, A) -> B) -> List<A> -> B
val total = listOf(1, 2, 3, 4, 5).fold(0) { acc, n -> acc + n }   // 15

// flatMap
val allTags = posts.flatMap { it.tags }

// groupBy :: ((A) -> K) -> List<A> -> Map<K, List<A>>
val byStatus = orders.groupBy { it.status }

// sortedBy :: ((A) -> K) -> List<A> -> List<A>
val sorted = orders.sortedBy { it.total }
val sortedDesc = orders.sortedByDescending { it.total }

// Sequence — lazy evaluation (infinite sequences possible)
val naturals = generateSequence(0) { it + 1 }
val firstTenEvens = naturals.filter { it % 2 == 0 }.take(10)
```

---

## Side Effect Boundary

```kotlin
import arrow.core.Either
import arrow.core.left
import arrow.core.right
import java.time.Instant
import java.util.UUID

// Pure core — all logic, no I/O
fun processRegistration(
    existingEmails: Set<String>,
    input: RegistrationInput,
    id: String,
    now: Instant,
): Either<String, User> {
    val email = input.email.lowercase().trim()
    return when {
        "@" !in email -> "Invalid email".left()
        email in existingEmails -> "Email already registered".left()
        else -> User(id = id, email = email, createdAt = now).right()
    }
}

// Impure shell — thin I/O layer
suspend fun registerUser(input: RegistrationInput): Either<String, User> {
    val existingEmails = db.users.allEmails()                          // I/O
    val id = UUID.randomUUID().toString()                               // I/O
    val now = Instant.now()                                             // I/O
    val result = processRegistration(existingEmails, input, id, now)    // pure
    result.onRight { user -> db.users.save(user) }                      // I/O
    return result
}
```

---

## Coroutines — `suspend` Functions

```kotlin
import arrow.core.Either
import arrow.core.flatMap

// suspend fun — like Async<'T> or Promise, but written as sequential code
suspend fun fetchAndProcess(userId: String): String {
    val user = db.users.findById(userId)             // suspends — non-blocking
    val profile = db.profiles.findByUserId(userId)
    return "${user.name} (${profile.city})"
}

// Railway-oriented programming with Either + suspend
suspend fun registerAsync(input: RegistrationInput): Either<RegistrationError, User> {
    val emails = db.allEmails()
    return validateInput(input)                       // Either<RegistrationError, ValidInput>
        .flatMap { valid -> buildUser(emails, valid) } // Either<RegistrationError, User>
}
```
