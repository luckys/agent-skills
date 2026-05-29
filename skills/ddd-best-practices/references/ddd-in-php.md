# DDD in PHP

Practical implementation guidance for Domain-Driven Design in PHP. Shows how tactical DDD patterns map to PHP idioms — applicable to any OO language, with PHP-specific notes.

Source: *Domain-Driven Design in PHP* by Carlos Buenosvinos, Christian Soronellas, and Keyvan Akbary.

---

## Value Objects in PHP

**What it looks like in PHP:**

```php
class Money
{
    private $amount;
    private $currency;

    public function __construct($anAmount, Currency $aCurrency)
    {
        $this->amount   = (int) $anAmount;
        $this->currency = $aCurrency;
    }

    public function add(Money $money): self
    {
        if (!$money->currency()->equals($this->currency())) {
            throw new \InvalidArgumentException();
        }
        return new self(
            $money->amount() + $this->amount(),
            $this->currency()
        );
    }

    public function equals(Money $money): bool
    {
        return $money->currency()->equals($this->currency())
            && $money->amount() === $this->amount();
    }

    public function amount(): int   { return $this->amount; }
    public function currency(): Currency { return $this->currency; }
}
```

**Key implementation note:** PHP has no built-in immutability — enforce it by never mutating `$this`; every "modifying" method must return `new self(...)` with the changed values.

Additional Value Object examples from the book:

```php
class Currency
{
    private $isoCode;

    public function __construct($anIsoCode)
    {
        if (!preg_match('/^[A-Z]{3}$/', $anIsoCode)) {
            throw new \InvalidArgumentException();
        }
        $this->isoCode = $anIsoCode;
    }

    public function equals(Currency $currency): bool
    {
        return $currency->isoCode() === $this->isoCode();
    }

    public function isoCode(): string { return $this->isoCode; }
}
```

Value equality uses `==` (same class + same attribute values) or an explicit `equals()` method. Avoid `===` for cross-instance comparison — it checks object identity, not value.

Semantic constructors (named factory methods) substitute PHP's lack of constructor overloading:

```php
class Money
{
    // ...
    public static function fromMoney(Money $aMoney): self
    {
        return new self($aMoney->amount(), $aMoney->currency());
    }

    public static function ofCurrency(Currency $aCurrency): self
    {
        return new self(0, $aCurrency);
    }
}
```

Use `self` instead of `static` in factory methods to avoid unexpected behavior when subclassed.

---

## Entities in PHP

**What it looks like in PHP:**

```php
namespace Ddd\Billing\Domain\Model;

class Order
{
    private $id;        // OrderId value object
    private $amount;
    private $firstName;
    private $lastName;

    public function __construct(
        OrderId $anOrderId,
        Amount  $amount,
        $aFirstName,
        $aLastName
    ) {
        $this->id        = $anOrderId;
        $this->amount    = $amount;
        $this->firstName = $aFirstName;
        $this->lastName  = $aLastName;
    }

    public function id(): OrderId { return $this->id; }
}
```

**Key implementation note:** Entity identity should be a Value Object (e.g., `OrderId`) rather than a plain primitive — this allows encapsulating equality logic and prevents accidental ID misuse.

Identity generation options:
- **Persistence-generated** (AUTO_INCREMENT): simplest, but the Entity has no ID until persisted.
- **Application-generated** (UUID): preferred; use `ramsey/uuid` via Composer.
- **Client-provided**: natural keys such as ISBN for a Book.

```php
class OrderId
{
    private $id;

    private function __construct($anId = null)
    {
        $this->id = $id ?: Uuid::uuid4()->toString();
    }

    public static function create($anId = null): self
    {
        return new static($anId);
    }

    public function equalsTo(OrderId $anOrderId): bool
    {
        return $anOrderId->id === $this->id;
    }
}
```

Use a **Surrogate Identity** (an extra private field mapped to the DB's integer PK) when the ORM requires an integer primary key but the domain uses a UUID identity:

```php
class DoctrineOrder extends Order
{
    private $surrogateId; // used only by Doctrine mapping

    public function __construct(OrderId $anOrderId, ...)
    {
        parent::__construct($anOrderId, ...);
        $this->surrogateId = $anOrderId->id();
    }
}
```

Active Record ORMs (Eloquent, Propel) force inheritance from a base class, coupling the Domain Model to persistence. Use Doctrine (Data Mapper) to keep Entities free of persistence details.

---

## Aggregate Root in PHP

**What it looks like in PHP:**

```php
class Order // Aggregate Root
{
    private $id;
    private $lines;       // collection of OrderLine (child entities/VOs)
    private $totalAmount;

    public function addLine(string $productName, Money $price): void
    {
        // All mutations go through the root — invariant enforced here
        $line = new OrderLine($productName, $price);
        $this->lines[] = $line;
        $this->recalculateTotal();
    }

    private function recalculateTotal(): void
    {
        $this->totalAmount = array_reduce(
            $this->lines,
            fn($carry, $line) => $carry->add($line->amount()),
            Money::ofCurrency($this->totalAmount->currency())
        );
    }
}
```

**Key implementation note:** External code must never hold direct references to child entities or Value Objects inside an Aggregate — all access must go through the root to preserve invariants.

Aggregate design rules from the book:
1. **Design around business invariants**, not convenience.
2. **One repository per Aggregate Root** — child entities have no repository of their own.
3. **Persist the entire Aggregate atomically** — one transaction, one Aggregate.
4. Reference other Aggregates by identity only, not by object reference.

```php
// Correct: add through root (Tell-Don't-Ask)
$order->addLine('DDD in PHP', new Money(2499, new Currency('USD')));

// Wrong: building child outside and setting it
$orderLine = new OrderLine('DDD in PHP', 24.99);
$order->addOrderLine($orderLine); // reveals internal structure
```

---

## Domain Events in PHP

**What it looks like in PHP:**

```php
// 1. Event definition
class UserRegistered
{
    private $userId;
    private $occurredOn;

    public function __construct(UserId $userId)
    {
        $this->userId     = $userId;
        $this->occurredOn = new \DateTimeImmutable();
    }

    public function userId(): UserId             { return $this->userId; }
    public function occurredOn(): \DateTimeImmutable { return $this->occurredOn; }
}

// 2. Aggregate Root collects events
class User
{
    private $events = [];

    public static function register(UserId $id, Email $email): self
    {
        $user = new self($id, $email);
        $user->events[] = new UserRegistered($id);
        return $user;
    }

    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];
        return $events;
    }
}

// 3. Application Service dispatches after persisting
$user = User::register($id, $email);
$this->userRepository->persist($user);
foreach ($user->releaseEvents() as $event) {
    $this->eventBus->publish($event);
}
```

**Key implementation note:** Never fire Domain Events in the constructor if the Entity is reconstituted from the database (e.g., via Doctrine's `serialize/unserialize`) — that would re-publish events on every load.

---

## Repository Interface + Implementation Separation in PHP

**What it looks like in PHP:**

```php
// Domain layer — interface only, no persistence details
namespace Domain\Model;

interface PostRepository
{
    public function nextIdentity(): PostId;
    public function add(Post $aPost): void;
    public function remove(Post $aPost): void;
    public function postOfId(PostId $anId): ?Post;
    public function latestPosts(\DateTimeImmutable $sinceADate): array;
}

// Infrastructure layer — Doctrine implementation
namespace Infrastructure\Persistence\Doctrine;

use Doctrine\ORM\EntityRepository;
use Domain\Model\Post;
use Domain\Model\PostId;
use Domain\Model\PostRepository;

class DoctrinePostRepository extends EntityRepository implements PostRepository
{
    public function nextIdentity(): PostId
    {
        return PostId::create();
    }

    public function add(Post $aPost): void
    {
        $this->getEntityManager()->persist($aPost);
    }

    public function postOfId(PostId $anId): ?Post
    {
        return $this->find((string) $anId);
    }
}

// In-memory implementation for tests
namespace Infrastructure\Persistence\InMemory;

class InMemoryPostRepository implements PostRepository
{
    private array $posts = [];

    public function add(Post $aPost): void
    {
        $this->posts[$aPost->id()->id()] = $aPost;
    }

    public function postOfId(PostId $anId): ?Post
    {
        return $this->posts[$anId->id()] ?? null;
    }
}
```

**Key implementation note:** The Repository interface belongs in the Domain layer; all concrete implementations belong in the Infrastructure layer — this keeps the domain free of framework and database dependencies.

Key distinctions:
- Repositories are **not DAOs**: they model a collection, not a database gateway. Avoid table-centric CRUD methods.
- **`nextIdentity()`** belongs on the Repository — the preferred place to generate UUIDs for new Aggregates.
- Use **Collection-Oriented** style (no explicit `save()` call needed when the ORM tracks changes) or **Persistence-Oriented** style (explicit `persist()`/`save()`) depending on ORM capabilities.

---

## Domain Service in PHP

**What it looks like in PHP:**

```php
// Domain Service: logic that doesn't naturally belong to one Entity
class TransferService
{
    public function transfer(
        Money   $amount,
        Account $sourceAccount,
        Account $targetAccount
    ): void {
        if ($sourceAccount->balance()->lessThan($amount)) {
            throw new InsufficientFundsException();
        }
        $sourceAccount->debit($amount);
        $targetAccount->credit($amount);
    }
}
```

**Key implementation note:** A Domain Service is stateless and operates solely on Domain objects — it must not depend on infrastructure (no repositories, no databases) directly; inject interfaces if persistence is needed.

When to use a Domain Service vs. putting logic on an Entity:
- The operation involves **multiple Aggregates**.
- The operation doesn't conceptually "belong" to any single Entity.
- Putting it on an Entity would require injecting infrastructure or violating Tell-Don't-Ask.

---

## Application Service in PHP

**What it looks like in PHP:**

```php
// Request DTO (input boundary)
class SignUpUserRequest
{
    public function __construct(
        public readonly string $email,
        public readonly string $password
    ) {}
}

// Application Service: orchestrates domain objects, no business logic
class SignUpUserService
{
    public function __construct(
        private UserRepository $userRepository
    ) {}

    public function execute(SignUpUserRequest $request): void
    {
        $email = $request->email;

        if (null !== $this->userRepository->userOfEmail($email)) {
            throw new UserAlreadyExistsException();
        }

        $user = new User(
            $this->userRepository->nextIdentity(),
            $email,
            $request->password
        );

        $this->userRepository->persist($user);
    }
}
```

**Key implementation note:** Application Services receive primitive DTOs (not Domain objects) from the outside world, coordinate domain objects to fulfill a use case, and return DTOs or nothing — they must not contain business rules.

Output patterns:
- Return a **response DTO** (plain data, no Domain objects exposed to callers).
- Use an **output port / Data Transformer** injected into the service for flexibility.
- Module structure: `Application/PlaceAnOrder/PlaceAnOrder.php`, `PlaceAnOrderRequest.php`, `PlaceAnOrderResponse.php`.

---

## Specification Pattern in PHP

**What it looks like in PHP:**

```php
interface Specification
{
    public function isSatisfiedBy($candidate): bool;
}

class PostPublishedAfterSpecification implements Specification
{
    public function __construct(private \DateTimeImmutable $date) {}

    public function isSatisfiedBy($candidate): bool
    {
        return $candidate->publishedAt() > $this->date;
    }
}

// Composite specifications
class AndSpecification implements Specification
{
    public function __construct(
        private Specification $one,
        private Specification $two
    ) {}

    public function isSatisfiedBy($candidate): bool
    {
        return $this->one->isSatisfiedBy($candidate)
            && $this->two->isSatisfiedBy($candidate);
    }
}

// Usage
$spec = new AndSpecification(
    new PostPublishedAfterSpecification(new \DateTimeImmutable('-30 days')),
    new PostByAuthorSpecification($authorId)
);

$matchingPosts = array_filter($posts, fn($p) => $spec->isSatisfiedBy($p));
```

**Key implementation note:** When used with Doctrine, create a parallel `DoctrineSpecification` that translates to DQL/QueryBuilder expressions rather than filtering in-memory — filtering large collections in PHP is a performance anti-pattern.

Common uses:
- Validation (is this Entity in a valid state for an operation?).
- Selection / querying from repositories.
- Business rule encapsulation that needs to be reused across services.

---

## PHP-Specific Anti-Patterns to Avoid

### Active Record ORM Leaking into the Domain

**Problem:**

```php
// Anti-pattern: Eloquent model IS the domain object
class User extends \Illuminate\Database\Eloquent\Model
{
    // Domain logic mixed with persistence concerns
    // Enforces one-to-one table-to-class mapping
    // Makes unit testing without a database nearly impossible
}
```

**Why it hurts DDD:**
- Active Record assumes a one-to-one mapping between Entity and table, coupling database schema to Domain design.
- Inheriting from the ORM base class pollutes Domain objects with infrastructure methods (`save()`, `delete()`, query scopes).
- Collections, inheritance, and complex invariants are hard to model.

**Fix:** Use **Doctrine ORM** (Data Mapper pattern). Keep Entities as plain PHP objects; let Doctrine handle persistence through XML/YAML/attribute mappings.

### Anemic Domain Model

**Problem:**

```php
// Anti-pattern: Entity is just a bag of getters/setters
class Order
{
    private $status;
    public function getStatus() { return $this->status; }
    public function setStatus($status) { $this->status = $status; } // no invariant
}

// Business logic lives in a Service
$order->setStatus('shipped'); // any value, any time — invariant impossible
```

**Fix:** Put business behaviour on the Entity itself. Methods like `ship()`, `cancel()`, `approve()` encode the state transition and protect invariants:

```php
class Order
{
    private $status;

    public function ship(): void
    {
        if ($this->status !== 'paid') {
            throw new \DomainException('Only paid orders can be shipped.');
        }
        $this->status = 'shipped';
        $this->events[] = new OrderShipped($this->id);
    }
}
```

### Using PHP `serialize/unserialize` for Domain Objects

**Problem:** Refactoring class names or namespaces silently breaks deserialized objects stored in Redis or sessions.

**Fix:** Use JSON with explicit reconstruction logic, or rely on Doctrine's internal proxy/hydration which bypasses the constructor.

### Mutating Value Objects

**Problem:**

```php
public function add(Money $money): void
{
    $this->amount += $money->amount(); // mutates — breaks immutability contract
}
```

**Fix:** Always return a new instance from any method that would change state (shown in the Value Objects section above).

### Using `static` Instead of `self` in Value Object Factory Methods

**Problem:**

```php
public static function fromMoney(Money $aMoney): static
{
    return new static(...); // breaks when subclassed
}
```

**Fix:** Use `new self(...)` to avoid binding to subclass constructors unexpectedly.
