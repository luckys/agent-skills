# Value Objects — Advanced Patterns

Source: CodelyTV `value_objects-course`

This file covers advanced value object patterns beyond basic immutability: refactoring to value objects, optional value objects, domain exception modeling, complex value objects, and typed collections.

---

## Refactoring to Value Objects — Reducing 100 Lines

**Intent:** Replace primitive parameters with value objects to collapse scattered validation and formatting into the concept itself.

**How it works:** A domain aggregate with 5–8 primitive string/number fields typically has validation scattered across controllers, application services, and tests. Extracting each field into its own value object moves the invariant to the concept, making the aggregate's constructor trivial and removing 30–40% of the boilerplate.

**Before — primitive User:**
```typescript
// Validation duplicated in every caller:
// controllers, use cases, factories, tests
class User {
  constructor(
    private id: string,
    private email: string,
    private birthdate: Date | null
  ) {
    if (!email.includes("@")) throw new Error("invalid email");
    // ... more validation scattered elsewhere
  }
}
```

**After — value object User:**
```typescript
export class User {
  constructor(
    private readonly id: UserId,
    private email: UserEmail,
    private readonly birthdate: UserBirthdate | null
  ) {}

  static create(id: string, email: string, birthdate: Date | null): User {
    return new User(
      new UserId(id),
      new UserEmail(email),
      birthdate !== null ? new UserBirthdate(birthdate) : null
    );
  }

  static fromPrimitives(primitives: UserPrimitives): User {
    return new User(
      new UserId(primitives.id),
      new UserEmail(primitives.email),
      primitives.birthdate !== null ? new UserBirthdate(primitives.birthdate) : null
    );
  }
}
```

**Practical heuristic:** Count all the places that validate the same field. If it is more than one, extract a value object.

---

## Value Objects with Domain Validation

**Intent:** Each value object encapsulates and self-validates its own invariants at construction time.

**How it works:** Validation runs in the constructor. Invalid inputs fail fast with a domain-specific error. The VO also inherits from a base class (`StringValueObject`, `DateValueObject`) to share structural equality logic.

**Example — UserEmail (TypeScript):**
```typescript
export class UserEmail extends StringValueObject {
  private readonly validEmailRegExp =
    /^(?=.*[@](?:gmail\.com|hotmail\.com)$)[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+/;

  constructor(readonly value: string) {
    super(value);
    this.ensureIsValidEmail(value);
  }

  toPrimitives(): string {
    return this.value;
  }

  private ensureIsValidEmail(value: string): void {
    if (!this.validEmailRegExp.test(value)) {
      throw new InvalidArgumentError(`<${value}> is not a valid email`);
    }
  }
}
```

**Example — UserBirthdate with business rule (TypeScript):**
```typescript
export class UserBirthdate extends DateValueObject {
  constructor(readonly value: Date) {
    super(value);
    this.ensureIsValidBirthdate(value);
  }

  private ensureIsValidBirthdate(value: Date): void {
    const currentDate = new Date();
    let ageInYears = currentDate.getFullYear() - value.getFullYear();

    if (
      currentDate.getMonth() < value.getMonth() ||
      (currentDate.getMonth() === value.getMonth() &&
        currentDate.getDate() < value.getDate())
    ) {
      ageInYears--;
    }

    if (ageInYears < 18 || ageInYears > 110) {
      throw new InvalidArgumentError(`<${value.toString()}> is not a valid birthdate`);
    }
  }
}
```

**Practical heuristic:** The value object's constructor is the only place where the invariant lives. If you find yourself validating the same thing outside the VO, move it in.

---

## Optional Value Objects — Three Approaches

**Intent:** Model fields that may legitimately be absent without spreading null checks through the codebase.

**How it works:** The course shows three progressive approaches:

### Approach 1 — Nullable field (simplest)
```typescript
class User {
  constructor(
    private readonly birthdate: UserBirthdate | null
  ) {}

  get birthdateValue(): Date | null {
    return this.birthdate !== null ? this.birthdate.value : null;
  }
}
```
Use when absence is a valid, permanent state and callers rarely need to branch on it.

### Approach 2 — Maybe/Option type
```typescript
// Wraps the optional value in a container that forces explicit handling
type Maybe<T> = T | null;

class User {
  constructor(private readonly birthdate: Maybe<UserBirthdate>) {}

  mapBirthdate<R>(fn: (bd: UserBirthdate) => R, fallback: R): R {
    return this.birthdate !== null ? fn(this.birthdate) : fallback;
  }
}
```
Use when callers frequently need to branch on presence/absence — the `map` method forces them to handle both paths.

### Approach 3 — Null Object pattern
```typescript
// Provides a default no-op implementation so callers never need to branch
abstract class UserBirthdateBase {
  abstract toPrimitives(): Date | null;
  abstract isPresent(): boolean;
}

class UserBirthdate extends UserBirthdateBase {
  constructor(readonly value: Date) { super(); }
  toPrimitives(): Date { return this.value; }
  isPresent(): boolean { return true; }
}

class NoUserBirthdate extends UserBirthdateBase {
  toPrimitives(): null { return null; }
  isPresent(): boolean { return false; }
}
```
Use when callers would otherwise do many `if (birthdate !== null)` checks — the null object removes the branching entirely.

**Practical heuristic:** Start with nullable fields. Introduce Maybe when you catch callers repeatedly branching. Introduce Null Object only when the branching is in many places and the default behavior is non-trivial.

---

## Modeling Domain Exceptions via Value Objects

**Intent:** Domain errors are first-class named concepts, not generic `Error` instances or string messages.

**How it works:** Each error scenario that the domain can raise gets its own class. This makes error handling explicit, searchable, and testable. The course pairs this with value objects because VOs throw these domain errors from their constructors.

**Example (TypeScript):**
```typescript
// Domain-specific error — not a generic Error("something went wrong")
export class UserAlreadyExistError extends Error {
  constructor(readonly email: string) {
    super(`The user ${email} already exist`);
  }
}

// Value object throws domain error, not a generic exception
export class UserEmail extends StringValueObject {
  constructor(readonly value: string) {
    super(value);
    if (!this.isValid(value)) {
      throw new InvalidArgumentError(`<${value}> is not a valid email`);
    }
  }
}
```

**Application layer usage:**
```typescript
async createUser(id: string, email: string): Promise<void> {
  const existing = await this.repository.searchByEmail(new UserEmail(email));
  if (existing) {
    throw new UserAlreadyExistError(email); // named, catchable, loggable
  }
  // ...
}
```

**Practical heuristic:** If you find yourself throwing `new Error("User already exists")` anywhere outside a dedicated error class, extract the error. The message and context belong to the error class constructor, not at the throw site.

---

## Complex Value Objects

**Intent:** A value object can compose multiple simpler value objects or contain richer behavioral logic beyond simple validation.

**How it works:** The course covers value objects that contain multiple fields (e.g., `Address` with street, city, country), value objects that reference other VOs, and typed collections. A complex VO still obeys immutability — to change it, you produce a new instance.

**Example — PhpDoc Admin with composite validation (PHP):**
```php
final readonly class Admin
{
    public function __construct(
        private string $username,
        private string $email,
        private string $code
    ) {
        $usernameLength = strlen($username);

        if ($usernameLength < 3) {
            throw new InvalidArgumentException('Username must be at least 3 characters long');
        }
        if ($usernameLength > 20) {
            throw new InvalidArgumentException('Username must be less than 20 characters long');
        }
    }
}
```

**Typed collection pattern (TypeScript):**
```typescript
// A collection that enforces its own invariants
class UserCollection {
  private constructor(private readonly items: ReadonlyArray<User>) {}

  static of(items: User[]): UserCollection {
    if (items.length === 0) {
      throw new InvalidArgumentError("UserCollection cannot be empty");
    }
    return new UserCollection(items);
  }

  add(user: User): UserCollection {
    return new UserCollection([...this.items, user]); // immutable — returns new instance
  }

  count(): number {
    return this.items.length;
  }
}
```

**Practical heuristic:** When a raw array has rules of its own (minimum size, uniqueness, ordering), extract a typed collection. The collection becomes a value object that owns those rules.

---

## Value Objects and the Law of Demeter

**Intent:** Value objects enable Demeter compliance by encapsulating display and transformation logic inside the concept.

**How it works:** Without VOs, callers must chain through primitive fields to build representations. With VOs, callers send a message to the object and receive the result.

**Before (Demeter violation):**
```python
# Deep chain into internal structure
f"{user.full_name.name.value} {user.full_name.last_name.value}'s products"
```

**After (Demeter compliant):**
```python
# User exposes only what callers need
user.display_saved_products()
```

The product value object does the same:
```python
class Product:
    def display_information(self):
        return f"Product ID: {self.id}, Name: {self.name}, Price: {self.price}"
```

**Practical heuristic:** If a caller accesses `.value` on a VO more than once in the same expression, move that expression into the VO as a method.

---

## Related Skills

- `oop-best-practices` — core value object principles and basic patterns
- `simple-design-rules` — Rule 3 (no duplication) is directly solved by value objects centralizing validation
- `oop-good-practices-examples` — Tell Don't Ask, Demeter, named constructors pair directly with VO patterns
