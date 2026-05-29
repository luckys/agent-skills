# Function Composition

Use this reference when designing pipelines, applying currying or partial application, or deciding between explicit and point-free style.

## Compose and Pipe

`compose` and `pipe` are the two core operators for building pipelines from small functions.

- `compose(f, g)(x)` → `f(g(x))` — right-to-left (mathematical order)
- `pipe(f, g)(x)` → `g(f(x))` — left-to-right (reading order)

```javascript
// Manual composition — hard to read at scale
const result = formatCurrency(applyTax(calculateSubtotal(activeItems)));

// compose — right-to-left, mathematical style
const summarize = compose(formatCurrency, applyTax, calculateSubtotal);
summarize(activeItems);

// pipe — left-to-right, reads as a pipeline
const summarize = pipe(calculateSubtotal, applyTax, formatCurrency);
summarize(activeItems);
```

Most teams prefer `pipe` because it reads in the direction of execution. Use whichever matches your codebase convention.

### Implementation

```javascript
const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x);
const compose = (...fns) => x => fns.reduceRight((v, f) => f(v), x);
```

Libraries: Ramda (`R.pipe`, `R.compose`), fp-ts (`pipe`, `flow`), Lodash/FP.

## Currying

A curried function takes arguments one at a time and returns a new function for each remaining argument:

```javascript
// Uncurried
const add = (a, b) => a + b;
add(2, 3); // 5

// Curried
const add = a => b => a + b;
add(2)(3); // 5
const add2 = add(2); // partially applied — waits for b
add2(3); // 5
add2(10); // 12
```

Currying enables partial application: fix some arguments now, supply the rest at the call site.

### Auto-curry with Ramda

```javascript
import * as R from "ramda";

const multiply = R.curry((factor, value) => value * factor);
const double = multiply(2);
const triple = multiply(3);

[1, 2, 3].map(double); // [2, 4, 6]
[1, 2, 3].map(triple); // [3, 6, 9]
```

## Partial Application

Partial application fixes a subset of a function's arguments, producing a function with fewer parameters:

```javascript
const applyDiscount = (rate, price) => price * (1 - rate);

// Partially apply the rate
const applyTenPercent = applyDiscount.bind(null, 0.1);
const applyTwentyPercent = applyDiscount.bind(null, 0.2);

// With Ramda
const applyDiscount = R.curry((rate, price) => price * (1 - rate));
const applyTenPercent = applyDiscount(0.1);
```

Partial application creates specialized functions without repeating arguments at every call site.

## Point-Free Style

A point-free (tacit) function is defined without explicitly mentioning the data it operates on:

```javascript
// Explicit style — data (`users`) is visible
const activeUsers = users => users.filter(u => u.active);

// Point-free — no explicit data argument
const activeUsers = R.filter(R.prop("active"));
```

Point-free reads well when the pipeline is the main story. It becomes a problem when the level of abstraction is hard to track.

### When to use point-free

Use point-free when:
- each step in a pipeline is a named function with a clear domain meaning
- removing the data argument makes the pipeline cleaner
- the reader can understand the transformation without the data parameter as a hint

Avoid point-free when:
- the function composition is deeply nested or complex
- readers need the data name to understand what flows through

## Pipeline Example End-to-End

### Problem: summarize active orders

```javascript
// Imperative
function summarize(orders) {
  const active = orders.filter(o => o.status === "active");
  const totals = active.map(o => o.items.reduce((sum, i) => sum + i.price, 0));
  const grandTotal = totals.reduce((sum, t) => sum + t, 0);
  return { count: active.length, grandTotal };
}

// Functional with pipe
const sumPrices = items => items.reduce((sum, i) => sum + i.price, 0);
const sumAll = nums => nums.reduce((a, b) => a + b, 0);

const summarize = (orders) => {
  const active = orders.filter(o => o.status === "active");
  const totals = active.map(sumPrices);
  return { count: active.length, grandTotal: sumAll(totals) };
};
```

## Monadic Chaining (flatMap / chain)

When each step in a pipeline can fail or produce a wrapped value, use `flatMap`/`chain` instead of `map`:

```javascript
// With Promise (async pipeline)
fetch("/api/orders")
  .then(parseJSON)       // returns Promise<Order[]>
  .then(filterActive)    // returns Promise<Order[]>
  .then(sumTotals)       // returns Promise<number>
  .catch(handleError);

// With Either (synchronous, explicit errors)
import { pipe } from "fp-ts/function";
import * as E from "fp-ts/Either";

const processOrder = pipe(
  parseOrder(rawInput),          // Either<Error, Order>
  E.chain(validateOrder),        // Either<Error, Order>
  E.chain(applyDiscount),        // Either<Error, Order>
  E.map(formatForResponse)       // Either<Error, Response>
);
```

`flatMap`/`chain` = `map` + `flatten`. It sequences computations where each step wraps its result.

## Haskell Style

```haskell
-- Composition with (.) operator (right-to-left)
summarize :: [Order] -> Summary
summarize = buildSummary . sumTotals . map orderTotal . filter isActive

-- Pipeline with (&) operator (left-to-right)
summarize orders = orders
  & filter isActive
  & map orderTotal
  & sum
  & buildSummary
```

## Elixir Style (|> pipeline operator)

```elixir
def summarize(orders) do
  orders
  |> Enum.filter(&active?/1)
  |> Enum.map(&order_total/1)
  |> Enum.sum()
end
```

## F# Style (|> pipeline operator)

```fsharp
let summarize orders =
  orders
  |> List.filter isActive
  |> List.map orderTotal
  |> List.sum
```

## Common Mistakes

- **Side effects inside a pipeline** — any step that mutates or performs I/O breaks composition guarantees. Extract it to the shell.
- **Too many arguments per step** — a step that takes 3+ arguments may need partial application or a config object.
- **Nesting pipelines** — if you need a pipeline inside a pipeline step, extract the inner pipeline to a named function.
- **Point-free with complex combinators** — when composition + map + filter are combined without names, extract intermediate steps.
