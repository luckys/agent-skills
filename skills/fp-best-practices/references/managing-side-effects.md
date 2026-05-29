# Managing Side Effects

Use this reference when deciding how to structure I/O, inject dependencies into pure functions, or design the boundary between pure logic and the outside world.

## Side Effects Are Not the Enemy

Every useful program has side effects: reading a database, writing to a file, sending HTTP requests, logging, generating random numbers. The functional approach is not to eliminate effects but to:

1. Make them visible in the type system
2. Isolate them to the boundary
3. Keep the core logic pure so it can be tested without them

## The Functional Core / Imperative Shell

(Gary Bernhardt's pattern — also known as "Ports and Adapters for FP")

```
                ┌──────────────────────────────┐
                │  Imperative Shell (impure)   │
                │  - reads from database       │
                │  - sends HTTP requests       │
                │  - writes to file system     │
                │  - generates random values   │
┌───────────────┼──────────────────────────────┤
│ Pure Core     │  calls into the core with    │
│               │  plain values                │
│ - all domain  ◄──────────────────────────────┤
│   logic       │  receives plain values back  │
│ - validation  ├──────────────────────────────┘
│ - transforms  │
└───────────────┘
```

The shell does the minimum: fetch data → call core with plain values → persist result.

```javascript
// Pure core — no I/O, fully testable
function processRegistration(existingEmails, rawInput) {
  if (existingEmails.has(rawInput.email)) {
    return { ok: false, error: "Email already registered" };
  }
  const user = { id: generateId(), ...normalize(rawInput), createdAt: new Date() };
  return { ok: true, user };
}

// Impure shell — orchestrates I/O
async function registerUser(rawInput) {
  const existingEmails = await db.users.allEmails(); // I/O
  const result = processRegistration(existingEmails, rawInput); // pure
  if (result.ok) await db.users.save(result.user); // I/O
  return result;
}
```

## Dependency Injection via Function Parameters

In FP, dependency injection is just passing functions as arguments. No DI container needed.

```javascript
// Hard-coded dependency — not testable
async function getActiveUsers() {
  const users = await db.users.findAll(); // coupled to the database
  return users.filter(u => u.active);
}

// Injected dependency — testable with any data source
async function getActiveUsers(findAllUsers) {
  const users = await findAllUsers();
  return users.filter(u => u.active);
}

// In tests
const fakeUsers = [{ id: "1", active: true }, { id: "2", active: false }];
await getActiveUsers(() => Promise.resolve(fakeUsers));

// In production
await getActiveUsers(() => db.users.findAll());
```

For multiple dependencies, group them into a "context" or "environment" object:

```typescript
type AppEnv = {
  db: Database;
  logger: Logger;
  clock: () => Date;
  idGenerator: () => string;
};

const createUser = (env: AppEnv) => async (input: CreateUserInput): Promise<User> => {
  const id = env.idGenerator();
  const createdAt = env.clock();
  const user = { id, ...input, createdAt };
  await env.db.users.save(user);
  env.logger.info("User created", { id });
  return user;
};
```

## Reader Monad Pattern

The Reader monad threads a shared environment through a computation without passing it explicitly at every step:

```typescript
// fp-ts Reader example
import { Reader } from "fp-ts/Reader";
import { pipe } from "fp-ts/function";
import * as R from "fp-ts/Reader";

type Config = { dbUrl: string; logLevel: string };

const readDbUrl: Reader<Config, string> = (config) => config.dbUrl;
const readLogLevel: Reader<Config, string> = (config) => config.logLevel;

const connectionString: Reader<Config, string> = pipe(
  readDbUrl,
  R.map(url => `Connected to ${url}`)
);

// Run with a concrete config
connectionString({ dbUrl: "postgres://localhost/mydb", logLevel: "info" });
```

In most practical codebases, plain dependency injection via parameters achieves the same effect with less ceremony.

## IO Monad (Haskell)

In Haskell, all I/O lives in the `IO` monad. The type system prevents side effects from escaping the IO context:

```haskell
-- Pure — no IO
add :: Int -> Int -> Int
add x y = x + y

-- Impure — IO in the type
getUser :: UserId -> IO (Maybe User)
getUser uid = do
  row <- queryDB "SELECT * FROM users WHERE id = ?" [uid]
  return (parseUser row)

-- Composition in IO
processUser :: UserId -> IO String
processUser uid = do
  maybeUser <- getUser uid
  return $ case maybeUser of
    Nothing   -> "Not found"
    Just user -> greet user
```

The IO monad makes impurity a type-level guarantee — a function without `IO` in its return type cannot perform side effects.

## Effect Systems (TypeScript: Effect-TS)

Effect-TS brings a typed effect system to TypeScript, making errors and dependencies visible in types:

```typescript
import { Effect, pipe } from "effect";

// Effect<Success, Error, Requirements>
const getUser = (id: string): Effect.Effect<User, UserNotFound, Database> =>
  Effect.tryPromise({
    try: () => db.users.findById(id),
    catch: () => new UserNotFound(id),
  });

const processUser = (id: string) =>
  pipe(
    getUser(id),
    Effect.map(user => ({ ...user, lastSeen: new Date() })),
    Effect.flatMap(saveUser),
  );
```

The `Requirements` type parameter tracks which services the effect needs — the compiler prevents running an effect without its dependencies.

## Separating Commands from Queries (CQRS for Functions)

Apply Command-Query Separation at the function level:

- **Query function**: pure, returns a value, no side effects
- **Command function**: produces side effects, returns unit (`void`, `()`, `IO ()`)

```javascript
// Query — pure, no side effects
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// Command — side effect, returns nothing meaningful
async function saveOrder(order) {
  await db.orders.insert(order);
  await eventBus.publish("OrderCreated", order);
}
```

Mixing a meaningful return value with side effects (returning the saved entity after mutating the database) creates coupling. Prefer returning the transformed value from the pure function and discarding it in the command.

## Handling Async Effects

Async operations are side effects. Manage them with:

```javascript
// Promise chain — sequential async pipeline
const orderSummary = (orderId) =>
  fetchOrder(orderId)
    .then(validateOrder)
    .then(applyDiscounts)
    .then(formatSummary)
    .catch(handleOrderError);

// async/await — cleaner for sequential effects with branching
async function processOrder(orderId) {
  const order = await fetchOrder(orderId);
  const validated = validateOrder(order); // pure
  const discounted = applyDiscounts(validated); // pure
  await saveOrder(discounted); // effect
  return formatSummary(discounted); // pure
}
```

Keep pure transformations (`validateOrder`, `applyDiscounts`, `formatSummary`) outside the async chain when possible — they do not need to be async.

## Warning Signs

- A "pure" function that reads from a global variable or module-level state.
- A function that catches an exception internally and returns null — use `Either`/`Result`.
- Logging or event publishing buried inside domain logic.
- Database calls inside functions described as business rules.
- A test that passes with real infrastructure but fails with mocks (hidden coupling).
- Deeply nested async chains where pure transformations are mixed with I/O.
