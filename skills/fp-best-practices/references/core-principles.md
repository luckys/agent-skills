# Core Principles

Use these principles to guide everyday functional programming decisions. They improve predictability, testability, and composability.

## Pure Functions

A pure function:
- returns the same output for the same input, always
- produces no side effects (no I/O, no mutation, no randomness, no throwing)

Pure functions are the unit of functional design. They can be tested without setup, composed freely, memoized safely, and parallelized without locks.

```javascript
// Impure — depends on external state, mutates
let total = 0;
function addToTotal(amount) {
  total += amount; // mutation of external state
  return total;
}

// Pure — same input always produces same output
function add(a, b) {
  return a + b;
}
```

## Referential Transparency

An expression is referentially transparent when it can be replaced by its value without changing the program's behavior.

Pure functions are referentially transparent. Impure functions are not.

```javascript
// Referentially transparent — can substitute the call with its result
const doubled = [1, 2, 3].map(x => x * 2); // always [2, 4, 6]

// Not referentially transparent — result depends on when you call it
const now = () => new Date(); // different every call
```

Referential transparency makes code easier to reason about: you can evaluate any subexpression independently.

## Immutability

Never mutate data in place. Produce new values instead.

```javascript
// Mutable — modifies the original
const items = [1, 2, 3];
items.push(4); // side effect

// Immutable — produces a new array
const moreItems = [...items, 4];
```

Immutability eliminates a whole class of bugs: no hidden shared state, no surprising changes at a distance, no need for defensive copying.

Immutability is the default in pure FP languages (Haskell, Elm, Clojure). In multi-paradigm languages, enforce it explicitly with `const`, `Object.freeze`, `readonly`, or immutable data libraries.

## Separation of Pure and Impure

Every program has side effects — reading files, writing to the database, printing output. The FP approach is not to eliminate effects but to isolate and control them.

```
┌───────────────────────────────────────┐
│  Pure core                            │
│  (transforms, validations, business   │
│  rules — no I/O, no mutation)         │
└───────────────┬───────────────────────┘
                │ data in / data out
┌───────────────▼───────────────────────┐
│  Impure shell                         │
│  (database, HTTP, file system, clock, │
│  logging, randomness)                 │
└───────────────────────────────────────┘
```

The functional core / imperative shell pattern (Gary Bernhardt):
- The core holds all logic and produces new values.
- The shell reads from the world, calls the core, and writes the result back.

```javascript
// Pure core — testable without any I/O
function applyDiscount(order, discountRate) {
  return { ...order, total: order.total * (1 - discountRate) };
}

// Impure shell — orchestrates I/O and calls the pure core
async function processOrder(orderId) {
  const order = await db.orders.find(orderId); // I/O
  const discounted = applyDiscount(order, 0.1); // pure
  await db.orders.save(discounted); // I/O
}
```

## Composition as the Primary Tool

Small functions composed into pipelines replace complex procedures.

The two composition operators:
- `compose(f, g)(x)` = `f(g(x))` — right-to-left, mathematical convention
- `pipe(f, g)(x)` = `g(f(x))` — left-to-right, reads like a pipeline

```javascript
// Imperative
function processUser(user) {
  const normalized = normalize(user);
  const validated = validate(normalized);
  const enriched = enrich(validated);
  return enriched;
}

// Functional with pipe
const processUser = pipe(normalize, validate, enrich);
```

A pipeline is a description of the transformation. Each step is independently testable and reusable.

## Totality

A total function is defined for all possible inputs — it never throws, never returns null, never produces undefined behavior.

Partial functions (those that crash or return undefined for some inputs) are a source of runtime errors.

Make functions total by:
- returning `Maybe`/`Option` when a result may not exist
- returning `Either`/`Result` when a computation may fail
- using types that restrict input to valid values

```typescript
// Partial — crashes on null or negative
function divide(a: number, b: number): number {
  return a / b; // Infinity or NaN if b === 0
}

// Total — makes the failure explicit in the type
function divide(a: number, b: number): Option<number> {
  return b === 0 ? None : Some(a / b);
}
```

## Write for Change

- Prefer designs where change is local.
- Keep pipelines narrow — each function does one transformation.
- Delay abstraction until stable patterns emerge under real use.
- Remove duplication of logic, not just duplication of syntax.
