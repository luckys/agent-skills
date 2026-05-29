# Higher-Order Functions

Use this reference when replacing imperative loops with functional transforms, working with functors and monads, or choosing between map, filter, reduce, and flatMap.

## What Is a Higher-Order Function?

A higher-order function (HOF) either:
- takes one or more functions as arguments, or
- returns a function as its result (currying and partial application)

HOFs are the primary tool for abstraction in FP — they abstract over *behavior* rather than over *data*.

## The Core Trio: map, filter, reduce

### map — Transform Each Element

`map` applies a function to each element of a structure and returns a new structure of the same shape.

```javascript
// Imperative
const doubled = [];
for (const n of [1, 2, 3]) doubled.push(n * 2);

// Functional
const doubled = [1, 2, 3].map(n => n * 2); // [2, 4, 6]
```

`map` preserves structure. The output has the same number of elements as the input.

```typescript
// map on Option — only applies if Some
import { option as O } from "fp-ts";
const maybeDouble = O.map((n: number) => n * 2);
maybeDouble(O.some(5));  // Some(10)
maybeDouble(O.none);     // None
```

### filter — Select Elements by Predicate

`filter` returns a new collection containing only elements that satisfy a predicate.

```javascript
const activeUsers = users.filter(u => u.active);
const highValue = orders.filter(o => o.total > 1000);
```

### reduce / fold — Collapse to a Single Value

`reduce` collapses a collection into a single value by applying an accumulator function:

```javascript
// Sum
const total = [10, 20, 30].reduce((sum, n) => sum + n, 0); // 60

// Build an object from an array
const byId = users.reduce((acc, user) => ({ ...acc, [user.id]: user }), {});

// Reimplement map with reduce
const myMap = (arr, fn) => arr.reduce((acc, x) => [...acc, fn(x)], []);

// Reimplement filter with reduce
const myFilter = (arr, pred) =>
  arr.reduce((acc, x) => (pred(x) ? [...acc, x] : acc), []);
```

`reduce` is the most general of the three. Every transformation on a sequence can be expressed as a fold. Use `map` and `filter` when they express intent more clearly.

## flatMap / chain — Sequences That Produce Wrapped Values

`flatMap` = `map` + `flatten`. It sequences computations where each step returns a wrapped value.

```javascript
// map would give: [[1, 2], [3, 4], [5, 6]]
[[1, 2], [3, 4], [5, 6]].map(x => x);

// flatMap flattens one level: [1, 2, 3, 4, 5, 6]
[[1, 2], [3, 4], [5, 6]].flatMap(x => x);

// Practical use: expand each element into multiple elements
const words = ["hello world", "foo bar"].flatMap(s => s.split(" "));
// ["hello", "world", "foo", "bar"]
```

In monadic terms, `flatMap`/`chain` sequences `Option`, `Either`, `Result`, or `Promise` computations:

```typescript
// Short-circuits on the first None
const result = pipe(
  findUser(id),                          // Option<User>
  O.chain(user => findProfile(user.id)), // Option<Profile>
  O.chain(profile => findAvatar(profile.avatarId)) // Option<Avatar>
);
```

## zip and zipWith — Combine Two Collections

`zip` combines two arrays into pairs:

```javascript
const names = ["Alice", "Bob"];
const scores = [90, 85];
const combined = names.map((name, i) => [name, scores[i]]);
// [["Alice", 90], ["Bob", 85]]

// Ramda
R.zip(names, scores); // [["Alice", 90], ["Bob", 85]]
R.zipWith((name, score) => ({ name, score }), names, scores);
// [{ name: "Alice", score: 90 }, { name: "Bob", score: 85 }]
```

## groupBy — Partition by Key

```javascript
// Native (ES2024)
const byStatus = Map.groupBy(orders, o => o.status);

// Functional implementation
const groupBy = fn => arr =>
  arr.reduce((acc, item) => {
    const key = fn(item);
    return { ...acc, [key]: [...(acc[key] ?? []), item] };
  }, {});

const byStatus = groupBy(o => o.status)(orders);
```

## Transducers — Composable Transforms Without Intermediate Collections

Standard `map` + `filter` chains create intermediate arrays. Transducers compose the transforms before applying them, processing each element once:

```javascript
// Creates two intermediate arrays
const result = [1, 2, 3, 4, 5]
  .filter(n => n % 2 === 0)   // [2, 4]
  .map(n => n * 10);          // [20, 40]

// Transducer — one pass, no intermediates (Ramda)
import * as R from "ramda";
const xform = R.compose(
  R.filter(n => n % 2 === 0),
  R.map(n => n * 10)
);
R.transduce(xform, R.flip(R.append), [], [1, 2, 3, 4, 5]); // [20, 40]
```

Transducers matter for large collections or when the data source is a stream. For normal array sizes, the intermediate arrays are negligible.

## Functor — Anything You Can Map Over

A functor is any container that implements `map` in a lawful way:

- `map(id)` = identity: `[1, 2].map(x => x)` → `[1, 2]`
- `map(f).map(g)` = `map(compose(g, f))`: mapping twice = mapping once with the composed function

Arrays, `Option`/`Maybe`, `Either`/`Result`, `Promise`, and `Stream` are all functors.

```typescript
// All functors respond to map
[1, 2, 3].map(double);              // Array functor
option.some(5).map(double);         // Option functor
Promise.resolve(5).then(double);    // Promise functor (then ≈ map)
```

## Monad — Sequences That Can Short-Circuit

A monad is a functor that also has:
- `of`/`return` — wrap a plain value
- `chain`/`flatMap`/`bind` — sequence dependent computations

```typescript
// Promise is a monad
const result = Promise.resolve(userId)
  .then(findUser)           // string → Promise<User>
  .then(fetchProfile)       // User → Promise<Profile>
  .then(renderProfile);     // Profile → Promise<Html>

// Option is a monad (short-circuits on None)
const result = pipe(
  O.some(userId),
  O.chain(findUser),         // short-circuits if user not found
  O.chain(fetchProfile),     // short-circuits if profile not found
  O.map(renderProfile)
);
```

The monad laws ensure sequential composition is associative and has a neutral element — which is what makes `then` and `chain` predictable to use.

## Applicative — Independent Parallel Computations

Applicatives apply a wrapped function to a wrapped value. Useful when computations are independent (not sequential):

```typescript
// Sequential (monad): second depends on first
pipe(
  findUser(id),
  O.chain(user => findOrders(user.id))
);

// Parallel (applicative): both independent
import { applicative as A } from "fp-ts/Option";
// Applies `buildSummary` to user and orders independently
A.ap(userOpt)(ordersOpt.map(orders => user => buildSummary(user, orders)));
```

In practice, use monads for sequential dependent operations and `Promise.all` / `Effect.all` for parallel independent ones.

## Practical Heuristics

| Situation | Function |
|---|---|
| Transform each element | `map` |
| Keep only some elements | `filter` |
| Combine elements into one value | `reduce` / `fold` |
| Each step may produce multiple results | `flatMap` |
| Two collections, pair elements | `zip` / `zipWith` |
| Group elements by a key | `groupBy` |
| Large collection, no intermediate arrays | transducers |
| Lift a function into a context | functor `map` |
| Chain dependent wrapped computations | monad `chain` |
| Combine independent wrapped computations | applicative `ap` |

## Warning Signs

- Using `reduce` where `map` or `filter` would express intent more clearly.
- A `map` callback with side effects — extract the effect to the boundary.
- A `for` loop that builds up a result array — usually replaceable with `map`/`filter`/`reduce`.
- Nested `flatMap` calls that form a staircase — consider `do`-notation (Haskell) or sequential `pipe` with `chain`.
- Chaining `map` on `null`/`undefined` — replace with `Option` first.
