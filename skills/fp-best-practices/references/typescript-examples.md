# TypeScript — Functional Programming Examples

Concepts covered: pure functions, pipe/compose, currying, Option, Either, immutable updates, higher-order functions, branded types, sum types, side effect boundary.

Libraries: [fp-ts](https://gcanti.github.io/fp-ts/), [Effect-TS](https://effect.website/), [Ramda](https://ramdajs.com).

---

## Pure Functions and Referential Transparency

```typescript
// Impure — depends on external state
let taxRate = 0.21;
function calculateTax(price: number): number {
  return price * taxRate; // hidden dependency
}

// Pure — all inputs explicit
const calculateTax = (rate: number, price: number): number => price * rate;

// Pure — immutable transform
type Cart = { items: Item[]; couponCode?: string };
const addItem = (cart: Cart, item: Item): Cart => ({
  ...cart,
  items: [...cart.items, item],
});
```

---

## Pipe and Compose (fp-ts)

```typescript
import { pipe, flow } from "fp-ts/function";

// pipe — apply a value through a sequence of functions (left-to-right)
const result = pipe(
  "  alice@example.com  ",
  (s) => s.trim(),
  (s) => s.toLowerCase(),
  (s) => s.replace(/\s+/g, "")
);

// flow — create a reusable pipeline (same as pipe without the initial value)
const normalizeEmail = flow(
  (s: string) => s.trim(),
  (s) => s.toLowerCase()
);

// Named functions compose cleanly
const processOrder = flow(filterActiveItems, calculateSubtotal, applyTax(0.21), formatCurrency);
```

---

## Currying and Partial Application

```typescript
// Manual currying
const multiply = (a: number) => (b: number): number => a * b;
const double = multiply(2);
const triple = multiply(3);

// With fp-ts
import { pipe } from "fp-ts/function";
import * as R from "ramda";

const applyDiscount = R.curry((rate: number, price: number) => price * (1 - rate));
const applyTenPercent = applyDiscount(0.1);

[100, 200, 300].map(applyTenPercent); // [90, 180, 270]

// Partial application pattern for dependency injection
const createUserService = (db: Database) => ({
  findById: (id: UserId) => db.users.findById(id),
  save: (user: User) => db.users.save(user),
});
```

---

## Branded / Nominal Types

```typescript
// Without branding — compiler accepts wrong types silently
type UserId = string;
type OrderId = string;
const getUser = (id: UserId): Promise<User> => db.users.findById(id);
const orderId: OrderId = "order-123";
getUser(orderId); // No error — but wrong!

// With branding — compiler rejects wrong types
type UserId = string & { readonly _brand: "UserId" };
type OrderId = string & { readonly _brand: "OrderId" };

const makeUserId = (id: string): UserId => id as UserId;
const makeOrderId = (id: string): OrderId => id as OrderId;

const getUser = (id: UserId): Promise<User> => db.users.findById(id);
const orderId = makeOrderId("order-123");
getUser(orderId); // Type error! OrderId is not UserId
```

---

## Option — Explicit Absence (fp-ts)

```typescript
import { pipe } from "fp-ts/function";
import * as O from "fp-ts/Option";

type Address = { street: string; city?: string };
type User = { name: string; address?: Address };

// Wrap nullable values
const findUser = (id: string): O.Option<User> =>
  O.fromNullable(db.users.get(id));

// Chain optional access — short-circuits on None
const getCity = (user: User): O.Option<string> =>
  pipe(
    O.fromNullable(user.address),
    O.chain((addr) => O.fromNullable(addr.city))
  );

// Match to extract the value
const displayCity = (userId: string): string =>
  pipe(
    findUser(userId),
    O.chain(getCity),
    O.match(
      () => "City unknown",
      (city) => city
    )
  );

// getOrElse for a default
const cityOrDefault = (user: User): string =>
  pipe(getCity(user), O.getOrElse(() => "Unknown"));
```

---

## Either — Explicit Failure (fp-ts)

```typescript
import { pipe } from "fp-ts/function";
import * as E from "fp-ts/Either";

type ValidationError = { field: string; message: string };
type User = { email: string; age: number };

const validateEmail = (email: string): E.Either<ValidationError, string> =>
  email.includes("@")
    ? E.right(email.toLowerCase().trim())
    : E.left({ field: "email", message: "Must contain @" });

const validateAge = (age: number): E.Either<ValidationError, number> =>
  age >= 0 && age <= 150
    ? E.right(age)
    : E.left({ field: "age", message: "Must be between 0 and 150" });

// Do-notation style — fails on first error
const parseUser = (input: {
  email: string;
  age: number;
}): E.Either<ValidationError, User> =>
  pipe(
    E.Do,
    E.bind("email", () => validateEmail(input.email)),
    E.bind("age", () => validateAge(input.age))
  );

// Usage
pipe(
  parseUser({ email: "alice@example.com", age: 30 }),
  E.match(
    (err) => console.error(`${err.field}: ${err.message}`),
    (user) => console.log("Valid:", user)
  )
);
```

---

## Sum Types — Discriminated Unions

```typescript
// Each variant carries only its relevant data
type OrderStatus =
  | { kind: "pending"; createdAt: Date }
  | { kind: "shipped"; createdAt: Date; trackingCode: string }
  | { kind: "delivered"; createdAt: Date; deliveredAt: Date }
  | { kind: "cancelled"; createdAt: Date; reason: string };

function describeStatus(status: OrderStatus): string {
  switch (status.kind) {
    case "pending":
      return "Awaiting shipment";
    case "shipped":
      return `Shipped — tracking: ${status.trackingCode}`;
    case "delivered":
      return `Delivered on ${status.deliveredAt.toDateString()}`;
    case "cancelled":
      return `Cancelled: ${status.reason}`;
  }
  // TypeScript exhaustiveness — if a new case is added, this becomes unreachable
  // Add: default: status satisfies never; to enforce it at compile time
}
```

---

## Immutable Data Transforms

```typescript
// Spread for shallow updates
const updateEmail = (user: User, email: string): User => ({ ...user, email });

// Nested immutable update
type Profile = { user: User; address: Address };
const updateCity = (profile: Profile, city: string): Profile => ({
  ...profile,
  address: { ...profile.address, city },
});

// With Ramda lenses — deep updates without manual spread nesting
import * as R from "ramda";
const cityLens = R.lensPath<Profile, string>(["address", "city"]);
const moveToMadrid = R.set(cityLens, "Madrid");
const updated = moveToMadrid(profile); // original profile unchanged

// readonly enforces immutability at the type level
type ReadonlyUser = Readonly<User>;
type ReadonlyCart = { readonly items: ReadonlyArray<Item> };
```

---

## Higher-Order Functions

```typescript
type Order = { id: string; status: string; total: number; items: Item[] };

// map, filter, reduce
const activeOrders = orders.filter((o) => o.status === "active");
const totals = activeOrders.map((o) => o.items.reduce((s, i) => s + i.price, 0));
const grandTotal = totals.reduce((a, b) => a + b, 0);

// flatMap — expand nested arrays
const allItems: Item[] = orders.flatMap((o) => o.items);

// Generic HOF
const groupBy =
  <T, K extends string>(fn: (item: T) => K) =>
  (items: T[]): Record<K, T[]> =>
    items.reduce(
      (acc, item) => {
        const key = fn(item);
        return { ...acc, [key]: [...(acc[key] ?? []), item] };
      },
      {} as Record<K, T[]>
    );

const byStatus = groupBy((o: Order) => o.status)(orders);
```

---

## Side Effect Boundary

```typescript
// Pure core — no I/O, fully testable
type RegistrationInput = { email: string; name: string };
type RegistrationResult = E.Either<string, User>;

function processRegistration(
  existingEmails: Set<string>,
  input: RegistrationInput,
  now: Date,
  id: string
): RegistrationResult {
  const email = input.email.toLowerCase().trim();
  if (!email.includes("@")) return E.left("Invalid email");
  if (existingEmails.has(email)) return E.left("Already registered");
  return E.right({ id, email, name: input.name, createdAt: now });
}

// Impure shell — minimal I/O coordination
async function registerUser(input: RegistrationInput): Promise<RegistrationResult> {
  const existingEmails = await db.users.allEmails();     // I/O
  const id = crypto.randomUUID();                         // I/O (randomness)
  const now = new Date();                                 // I/O (time)
  const result = processRegistration(existingEmails, input, now, id); // pure
  if (E.isRight(result)) await db.users.save(result.right);           // I/O
  return result;
}
```

---

## Effect-TS (typed effects and dependencies)

```typescript
import { Effect, pipe } from "effect";
import { Layer } from "effect";

// Effect<Success, Error, Requirements>
interface Database {
  findUser: (id: string) => Effect.Effect<User, UserNotFound>;
}

const getUser = (id: string): Effect.Effect<User, UserNotFound, Database> =>
  Effect.serviceWith(
    (db: Database) => db.findUser(id)
  );

const program = pipe(
  getUser("user-123"),
  Effect.map((user) => ({ ...user, lastSeen: new Date() })),
  Effect.flatMap(saveUser)
);

// Run with a concrete database implementation
Effect.runPromise(Effect.provide(program, DatabaseLive));
```
