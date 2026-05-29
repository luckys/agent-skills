# Kent Beck's 4 Rules of Simple Design

Source: CodelyTV `four_rules_of_simple_design-course`

The four rules are applied in priority order. A design is simple when it satisfies all four, and you resolve conflicts by favoring the higher-ranked rule.

1. **Passes Tests** — every behavior is verified
2. **Reveals Intention** — the code communicates its purpose clearly
3. **No Duplication** — no knowledge exists in more than one place
4. **Fewest Elements** — no unnecessary classes, methods, or abstractions

---

## Rule 1: Passes Tests

**Intent:** Every behavior has a corresponding test that documents and protects it.

**How it works:** Tests act as a safety net for the other three rules. You cannot refactor with confidence (rules 2–4) without a passing test suite. The course structures lessons starting from working code: reproduce a bug with a failing test first, then fix the production code.

**Practical heuristic:** Before touching any code, write a test that fails for the reason you expect. If you cannot, you do not yet understand the change.

---

## Rule 2: Reveals Intention

**Intent:** Names and structure communicate what the code does without requiring the reader to execute it mentally.

**How it works:** The course teaches two main techniques: ubiquitous language in naming, and semantic differentiation between operations that always return a value versus those that may not.

### Effective Naming — Ubiquitous Language

Use the vocabulary of the domain, not the vocabulary of the implementation.

**Example (PHP):**
```php
// Bad: technical name, no domain meaning
final readonly class Admin
{
    public function __construct(
        private string $username,
        private string $email,
        private string $code  // "code" — what does it mean?
    ) {}
}

// Better: names that match the domain glossary
final readonly class Admin
{
    public function __construct(
        private string $username,
        private string $email,
        private string $adminCode  // intent is clear
    ) {}
}
```

### search vs find — Communicating Return Semantics

The `search` / `find` naming convention encodes whether absence is valid.

- `search*(...)` — may return `null` / empty; absence is a normal outcome
- `find*(...)` — always returns a value; throws if absent

**Example (TypeScript):**
```typescript
// find — throws if not found; caller is guaranteed a result
findUserById(id: UserId): User {
  const user = this.repository.get(id);
  if (!user) throw new UserNotFoundError(id);
  return user;
}

// search — returns null/undefined; caller must handle absence
searchUserByEmail(email: UserEmail): User | null {
  return this.repository.getByEmail(email) ?? null;
}
```

**Practical heuristic:** If a method name starts with `get` for two different semantics (nullable and non-nullable), split it into `search*` and `find*`.

---

## Rule 3: No Duplication

**Intent:** Every piece of knowledge lives in exactly one place in the code.

**How it works:** The course distinguishes three levels of duplication, each requiring a different fix.

### Literal Duplication — copy-pasted code

The most obvious form. Same logic repeated verbatim.

**Example (PHP) — before:**
```php
// UsersController.php
public function usersPost(string $username, string $email, ...): void
{
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        throw new InvalidArgumentException('Invalid email format');
    }
    // create user...
}

public function adminsPost(string $username, string $email, ...): void
{
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {  // duplicated!
        throw new InvalidArgumentException('Invalid email format');
    }
    // create admin...
}
```

**After — extract to a value object:**
```php
// Email validation lives once, inside the value object
final class Email
{
    public function __construct(private readonly string $value)
    {
        if (!filter_var($value, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException('Invalid email format');
        }
    }
}
```

### Structural Duplication — same shape, different types

Two classes share the same internal structure (e.g., both validate a length range) but are not literally identical. Fix by extracting a base class or trait that owns the structure.

### Conceptual Duplication — same rule, different expressions

The hardest to spot. The same business rule is expressed differently in two places. Example: age validation in a form controller and in a domain object. Fix by finding the canonical owner of that rule and deleting the other expression.

**Practical heuristic:** When you copy-paste, you have literal duplication. When two classes look alike structurally, you have structural duplication. When two distant pieces of code enforce the same business constraint, you have conceptual duplication — and conceptual duplication is the most dangerous.

---

## Rule 4: Fewest Elements

**Intent:** Do not add classes, interfaces, or methods that are not needed right now.

**How it works:** Governed by YAGNI (You Ain't Gonna Need It). Interfaces are only justified when there are multiple concrete implementations or when inversion of control requires decoupling. A single-implementation interface is unnecessary structure.

**Example:**
```typescript
// Bad: interface with a single implementation — unnecessary element
interface UserRepository {
  save(user: User): void;
}
class InMemoryUserRepository implements UserRepository { ... }

// If InMemoryUserRepository is the only implementation,
// delete the interface until a second implementation exists.
```

**Practical heuristic:** Before adding a new abstraction (interface, base class, helper), ask: "Which two concrete things does this unify right now?" If the answer is "none yet," delete it.

---

## Interaction Between the Rules

The rules frequently interact. Applying rule 3 (no duplication) via a value object simultaneously satisfies rule 2 (reveals intention) by naming the concept, and often reduces elements (rule 4) by consolidating scattered validation. The test suite (rule 1) makes all refactoring safe.

## Related Skills

- `oop-best-practices` — naming, value objects, cohesion
- `refactoring-best-practices` — safe incremental refactoring while keeping tests green
