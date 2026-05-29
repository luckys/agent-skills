# Algebraic Data Types

Use this reference when choosing between null/undefined and explicit types, modeling domain variants, or making illegal states unrepresentable.

## What Are Algebraic Data Types?

Algebraic Data Types (ADTs) are composite types formed by combining simpler types in two ways:

- **Product types** — hold multiple values at once (records, tuples). Named "product" because the number of possible values is the product of each field's possibilities.
- **Sum types** — hold one of several variants (tagged unions, discriminated unions). Named "sum" because the total possibilities is the sum of each variant's possibilities.

Together they let you model exactly what is possible in the domain — no more, no less.

## Product Types (Records and Tuples)

A product type holds values for all its fields simultaneously:

```typescript
// TypeScript
type Point = { x: number; y: number };
type UserProfile = { id: UserId; name: string; email: Email; role: Role };
```

```haskell
-- Haskell
data Point = Point { x :: Double, y :: Double }
data UserProfile = UserProfile { userId :: UserId, name :: String, email :: Email, role :: Role }
```

Every combination of valid field values is a valid product type instance.

## Sum Types (Tagged Unions / Discriminated Unions)

A sum type holds exactly one of several possible variants. The tag (discriminant) identifies which variant it is:

```typescript
// TypeScript — discriminated union
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rectangle"; width: number; height: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle": return Math.PI * shape.radius ** 2;
    case "rectangle": return shape.width * shape.height;
    case "triangle": return 0.5 * shape.base * shape.height;
  }
}
```

```haskell
-- Haskell
data Shape
  = Circle Double
  | Rectangle Double Double
  | Triangle Double Double

area :: Shape -> Double
area (Circle r) = pi * r ^ 2
area (Rectangle w h) = w * h
area (Triangle b h) = 0.5 * b * h
```

The compiler enforces exhaustiveness: if a new variant is added, every switch/match must be updated.

## Maybe / Option — Explicit Absence

`Maybe`/`Option` replaces `null`/`undefined` with a type that forces callers to handle absence explicitly.

```typescript
// TypeScript with fp-ts
import { Option, some, none, match } from "fp-ts/Option";

function findUser(id: UserId): Option<User> {
  const user = db.users.get(id);
  return user ? some(user) : none;
}

// The caller cannot ignore the missing case
const displayName = pipe(
  findUser(id),
  match(
    () => "Anonymous",        // None case — user not found
    (user) => user.name       // Some case — user found
  )
);
```

```javascript
// JavaScript with union
const None = { _tag: "None" };
const Some = value => ({ _tag: "Some", value });

const findUser = id => {
  const user = db.get(id);
  return user ? Some(user) : None;
};
```

```elm
-- Elm
findUser : UserId -> Maybe User
findUser id = Dict.get id db

-- Pattern matching is exhaustive
displayName : UserId -> String
displayName id =
  case findUser id of
    Nothing -> "Anonymous"
    Just user -> user.name
```

### When to use Maybe/Option

- A lookup that may not find a result (`findById`, `Dict.get`, `Array.find`)
- An optional configuration field
- A value that is intentionally absent (not an error)

Do **not** use `Maybe` when absence is an error — use `Either`/`Result` instead.

## Either / Result — Explicit Failure

`Either`/`Result` replaces exceptions with a type that carries both the success value and the error, forcing callers to handle both.

```typescript
// TypeScript with fp-ts
import { Either, left, right } from "fp-ts/Either";

type ValidationError = { field: string; message: string };

function parseAge(raw: string): Either<ValidationError, number> {
  const n = parseInt(raw, 10);
  if (isNaN(n)) return left({ field: "age", message: "Must be a number" });
  if (n < 0 || n > 150) return left({ field: "age", message: "Out of range" });
  return right(n);
}

// Chain operations — short-circuits on the first Left
const processAge = pipe(
  parseAge(rawInput),
  E.chain(validateMinimumAge),
  E.map(ageToAgeGroup)
);
```

```haskell
-- Haskell — Either is built in
parseAge :: String -> Either String Int
parseAge s = case reads s of
  [(n, "")] | n >= 0 && n <= 150 -> Right n
  [(_, "")]                       -> Left "Out of range"
  _                               -> Left "Not a number"
```

```fsharp
// F# — Result type
let parseAge (raw: string) : Result<int, string> =
  match System.Int32.TryParse(raw) with
  | true, n when n >= 0 && n <= 150 -> Ok n
  | true, _  -> Error "Out of range"
  | false, _ -> Error "Not a number"
```

### When to use Either/Result

- Parsing or validation that can fail (parse user input, decode JSON)
- Operations that interact with external systems (database, HTTP, file system)
- Business rules that can be violated (`InsufficientFunds`, `ProductOutOfStock`)

## Making Illegal States Unrepresentable

The goal is to design types so that the invalid combinations simply cannot be constructed.

### Anti-pattern: optional flags create ambiguous states

```typescript
// What does it mean when both are set? Or neither?
type Order = {
  status: string; // "pending" | "shipped" | "delivered" | "cancelled"
  shippedAt?: Date;
  cancelledAt?: Date;
  cancelReason?: string;
};
```

### Better: each state carries only relevant data

```typescript
type Order =
  | { status: "pending"; createdAt: Date }
  | { status: "shipped"; createdAt: Date; shippedAt: Date; trackingCode: string }
  | { status: "delivered"; createdAt: Date; shippedAt: Date; deliveredAt: Date }
  | { status: "cancelled"; createdAt: Date; cancelledAt: Date; reason: string };
```

Now a `cancelled` order always has a `reason`. A `shipped` order always has a `trackingCode`. Invalid combinations do not type-check.

## Branded / Nominal Types

Prevent mixing up values of the same primitive type that represent different concepts:

```typescript
// Without branding — compiler accepts UserId where OrderId is expected
type UserId = string;
type OrderId = string;

// With branding — compiler rejects the wrong type
type UserId = string & { readonly _brand: "UserId" };
type OrderId = string & { readonly _brand: "OrderId" };

const makeUserId = (id: string): UserId => id as UserId;
const makeOrderId = (id: string): OrderId => id as OrderId;

function getUser(id: UserId): User { ... }
const orderId = makeOrderId("123");
getUser(orderId); // Type error — OrderId is not UserId
```

## Recursive Types

Sum types compose recursively to model tree-shaped data:

```typescript
// Binary tree
type Tree<A> =
  | { tag: "Leaf" }
  | { tag: "Node"; value: A; left: Tree<A>; right: Tree<A> };

// JSON value
type Json =
  | null
  | boolean
  | number
  | string
  | Json[]
  | { [key: string]: Json };
```

```haskell
-- Haskell
data Tree a = Leaf | Node a (Tree a) (Tree a)

data Json
  = JNull
  | JBool Bool
  | JNumber Double
  | JString String
  | JArray [Json]
  | JObject [(String, Json)]
```

## Decision Guide

| Situation | Type to use |
|---|---|
| Value may or may not exist (not an error) | `Maybe` / `Option` |
| Operation may fail; caller needs the error | `Either` / `Result` |
| Multiple exclusive domain states | Sum type / discriminated union |
| Multiple fields that always coexist | Product type / record |
| Two primitives that must not be confused | Branded / nominal type |
| Hierarchical / recursive data | Recursive sum type |
