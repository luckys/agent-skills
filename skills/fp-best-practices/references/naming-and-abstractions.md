# Naming and Abstractions

Use this reference when naming quality, over-generalization, or weak abstractions are the main design problem.

## Name Functions by the Transformation They Perform

A function name should describe what goes in and what comes out, not the mechanism.

```javascript
// Weak — describes the mechanism
function doStringProcessing(str) { ... }
function handleUser(user) { ... }
function processData(data) { ... }

// Strong — describes the transformation
function normalizeEmail(email) { ... }
function activateUser(user) { ... }
function aggregateSalesByRegion(sales) { ... }
```

If a function's name cannot describe its input-output contract, the function probably mixes several transformations.

## Name Types by What They Represent

In typed FP (TypeScript, Haskell, Elm, F#, Scala), type names define the abstraction the reader will model.

```typescript
// Weak — too generic
type Data = Record<string, unknown>;
type Result = { value: any; error?: string };

// Strong — describes the domain concept
type OrderId = string & { readonly _brand: "OrderId" };
type ValidationError = { field: string; message: string };
type ParseResult<T> = { ok: true; value: T } | { ok: false; error: string };
```

Branded/nominal types catch category errors at compile time. A function expecting `UserId` should not silently accept an `OrderId`.

## Avoid Generic Names

Generic names hide intent and merge distinct concepts:

| Avoid | Prefer |
|---|---|
| `process` | `validate`, `transform`, `aggregate`, `normalize` |
| `handle` | `onPaymentReceived`, `onUserCreated` |
| `data` | `order`, `invoice`, `userProfile` |
| `result` | `parsedDate`, `discountedTotal`, `activeUsers` |
| `helper` / `utils` | a module name that describes what it helps with |
| `Manager` | the concept it manages |

A name like `processData` forces every reader to read the function body to understand what it does.

## If a Name Is Hard to Find, Recheck the Abstraction

The difficulty of naming is data about the design:

- Cannot name it without "and" → it does two things (split it)
- Falling back to `process`, `handle`, `do` → the concept is unclear (rethink the boundary)
- The name conflicts with another in the same module → the module has mixed responsibilities (separate them)

## DRY Means Shared Logic, Not Identical Syntax

Extract a function when multiple callsites express the same transformation for the same reason.
Do not extract when the code only looks similar but represents different domain rules.

```javascript
// These look similar but represent different business rules — do not merge
const applyEmployeeDiscount = (price) => price * 0.85;
const applyLoyaltyDiscount = (price) => price * 0.85;

// These are the same rule — extract
const applyStandardDiscount = (price) => price * 0.85;
```

If one copy changes, should the others always change too? If not, they are not the same knowledge.

## Avoid Clever Point-Free When It Obscures Meaning

Point-free (tacit) style removes the data argument from function definitions. It is useful when the pipeline reads naturally — it becomes a smell when the reader has to mentally reconstruct what data flows through.

```javascript
// Clear point-free — each step is named and reads like a pipeline
const summarizeOrder = pipe(
  filterActiveItems,
  calculateSubtotal,
  applyTax,
  formatCurrency
);

// Obscure point-free — the combination of partial application is harder to read
const process = compose(
  map(compose(prop("value"), filter(Boolean))),
  reduce(mergeWith(add), {})
);
```

Rule: use point-free when it makes the pipeline more readable, not just shorter.

## Pipeline Vocabulary Should Match the Domain

Name pipeline steps after domain operations, not after the functions used to implement them:

```javascript
// Technical vocabulary dominates
pipe(
  xs => xs.filter(x => x.status === "active"),
  xs => xs.map(x => ({ ...x, score: x.value * 1.1 })),
  xs => xs.reduce((acc, x) => acc + x.score, 0)
)(orders);

// Domain vocabulary is visible
pipe(
  filterActiveOrders,
  applyLoyaltyBonus,
  sumScores
)(orders);
```

The second version reads as a specification. A domain expert can follow it.

## Magic Values Are Unnamed Concepts

An inline literal is a concept without a name:

```javascript
// What does 0.21 mean?
const tax = subtotal * 0.21;

// Named — the business rule is explicit
const VAT_RATE = 0.21;
const tax = subtotal * VAT_RATE;
```

Apply the same rule to string patterns, thresholds, and format strings.

## Avoid Overloaded Parameter Names

In curried or higher-order functions, parameter names compound: outer function parameters shadow inner ones. Name each level so readers can track data flow:

```javascript
// Confusing — `x` used at multiple levels with different meanings
const transform = x => y => x + y;

// Clear — each level named for its role
const addBase = base => increment => base + increment;
```
