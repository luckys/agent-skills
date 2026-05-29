# JavaScript — Functional Programming Examples

Concepts covered: pure functions, composition/pipe, currying, Maybe/Option, Either/Result, immutable updates, higher-order functions, sum types, side effect boundary.

Libraries: native ES2022+, [Ramda](https://ramdajs.com), [fp-ts](https://gcanti.github.io/fp-ts/).

---

## Pure Functions and Referential Transparency

```javascript
// Impure — side effects, depends on external state
let discount = 0.1;
function applyDiscount(price) {
  return price * (1 - discount); // depends on external variable
}

// Pure — same input always gives same output
const applyDiscount = (rate, price) => price * (1 - rate);

// Pure — immutable transform, no side effects
const addItem = (cart, item) => ({ ...cart, items: [...cart.items, item] });
```

---

## Function Composition and Pipe

```javascript
// Manual pipe (left-to-right)
const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x);

// Manual compose (right-to-left)
const compose = (...fns) => x => fns.reduceRight((v, f) => f(v), x);

// Usage
const normalizeEmail = email => email.toLowerCase().trim();
const validateEmail = email => email.includes("@") ? email : null;
const formatForDisplay = email => `<${email}>`;

const processEmail = pipe(normalizeEmail, validateEmail, formatForDisplay);

// With Ramda
const R = require("ramda");
const processOrder = R.pipe(
  R.filter(item => item.active),
  R.map(item => ({ ...item, total: item.price * item.qty })),
  R.sortBy(R.prop("total"))
);
```

---

## Currying and Partial Application

```javascript
// Manual currying
const multiply = a => b => a * b;
const double = multiply(2);
const triple = multiply(3);

double(5);  // 10
triple(5);  // 15

// With Ramda auto-curry
const R = require("ramda");

const applyDiscount = R.curry((rate, price) => price * (1 - rate));
const applyTenPercent = applyDiscount(0.1);
const applyTwentyPercent = applyDiscount(0.2);

[100, 200, 300].map(applyTenPercent); // [90, 180, 270]

// Partial application with bind
const greet = (greeting, name) => `${greeting}, ${name}!`;
const sayHello = greet.bind(null, "Hello");
sayHello("Alice"); // "Hello, Alice!"
```

---

## Maybe / Option — Safe Navigation (no library)

```javascript
// Simple Maybe implementation
const None = Object.freeze({ _tag: "None" });
const Some = value => Object.freeze({ _tag: "Some", value });

const isSome = m => m._tag === "Some";
const isNone = m => m._tag === "None";

const map = fn => maybe =>
  isSome(maybe) ? Some(fn(maybe.value)) : maybe;

const chain = fn => maybe =>
  isSome(maybe) ? fn(maybe.value) : maybe;

const getOrElse = fallback => maybe =>
  isSome(maybe) ? maybe.value : fallback;

// Usage — safe property access
const getCity = user =>
  pipe(
    () => user.address ? Some(user.address) : None,
    chain(addr => addr.city ? Some(addr.city) : None),
    getOrElse("Unknown city")
  )();

// With Ramda
const safeProp = R.curry((key, obj) =>
  obj && obj[key] !== undefined ? Some(obj[key]) : None
);

const getCity = R.pipe(
  safeProp("address"),
  chain(safeProp("city")),
  getOrElse("Unknown")
);
```

---

## Either / Result — Explicit Failure (no library)

```javascript
const Left = error => Object.freeze({ _tag: "Left", error });
const Right = value => Object.freeze({ _tag: "Right", value });

const isRight = e => e._tag === "Right";

const mapRight = fn => either =>
  isRight(either) ? Right(fn(either.value)) : either;

const chainRight = fn => either =>
  isRight(either) ? fn(either.value) : either;

const match = (onLeft, onRight) => either =>
  isRight(either) ? onRight(either.value) : onLeft(either.error);

// Validation functions
const validateEmail = email =>
  typeof email === "string" && email.includes("@")
    ? Right(email.toLowerCase().trim())
    : Left("Invalid email address");

const validateAge = age =>
  Number.isInteger(age) && age >= 0 && age <= 150
    ? Right(age)
    : Left("Age must be between 0 and 150");

// Chain validations
const parseUser = ({ email, age }) => {
  const emailResult = validateEmail(email);
  if (!isRight(emailResult)) return emailResult;

  const ageResult = validateAge(age);
  if (!isRight(ageResult)) return ageResult;

  return Right({ email: emailResult.value, age: ageResult.value });
};

// Usage
const result = parseUser({ email: "alice@example.com", age: 30 });
match(
  error => console.error("Error:", error),
  user => console.log("User:", user)
)(result);
```

---

## Immutable Data Transforms

```javascript
// Spread for shallow immutable updates
const updateEmail = (user, email) => ({ ...user, email });
const addItem = (cart, item) => ({ ...cart, items: [...cart.items, item] });
const removeItem = (cart, itemId) => ({
  ...cart,
  items: cart.items.filter(i => i.id !== itemId),
});

// Nested updates (manual)
const updateCity = (user, city) => ({
  ...user,
  address: { ...user.address, city },
});

// With Ramda lenses for deep updates
const R = require("ramda");
const cityLens = R.lensPath(["address", "city"]);
const updateCity = R.set(cityLens, "Madrid");
const updatedUser = updateCity(user); // user unchanged, new object returned
```

---

## Higher-Order Functions

```javascript
const orders = [
  { id: 1, status: "active", items: [{ price: 10 }, { price: 20 }] },
  { id: 2, status: "cancelled", items: [{ price: 15 }] },
  { id: 3, status: "active", items: [{ price: 5 }, { price: 30 }] },
];

// map — transform
const withTotals = orders.map(o => ({
  ...o,
  total: o.items.reduce((sum, i) => sum + i.price, 0),
}));

// filter — select
const activeOrders = orders.filter(o => o.status === "active");

// reduce — aggregate
const grandTotal = orders
  .filter(o => o.status === "active")
  .map(o => o.items.reduce((s, i) => s + i.price, 0))
  .reduce((sum, t) => sum + t, 0);

// flatMap — expand
const allItems = orders.flatMap(o => o.items);

// groupBy (ES2024)
const byStatus = Map.groupBy(orders, o => o.status);

// Transducer-style with Ramda (one pass, no intermediates)
const R = require("ramda");
const summarizeActive = R.pipe(
  R.filter(o => o.status === "active"),
  R.map(o => o.items.reduce((s, i) => s + i.price, 0)),
  R.sum
);
```

---

## Algebraic Data Types — Sum Types

```javascript
// Tagged union (no library)
const OrderStatus = {
  pending: () => ({ _tag: "pending" }),
  shipped: (trackingCode) => ({ _tag: "shipped", trackingCode }),
  delivered: (deliveredAt) => ({ _tag: "delivered", deliveredAt }),
  cancelled: (reason) => ({ _tag: "cancelled", reason }),
};

const describeStatus = status => {
  switch (status._tag) {
    case "pending": return "Awaiting shipment";
    case "shipped": return `Shipped (${status.trackingCode})`;
    case "delivered": return `Delivered on ${status.deliveredAt.toDateString()}`;
    case "cancelled": return `Cancelled: ${status.reason}`;
    default: throw new Error(`Unknown status: ${status._tag}`);
  }
};

const order = { id: "123", status: OrderStatus.shipped("TRACK-456") };
describeStatus(order.status); // "Shipped (TRACK-456)"
```

---

## Side Effect Boundary (Functional Core / Imperative Shell)

```javascript
// Pure core — all logic, no I/O
function processRegistration(existingEmails, input) {
  const email = input.email?.toLowerCase().trim();
  if (!email?.includes("@")) return Left("Invalid email");
  if (existingEmails.has(email)) return Left("Email already registered");
  return Right({ id: crypto.randomUUID(), email, createdAt: new Date() });
}

// Impure shell — only coordinates I/O
async function registerUser(input) {
  const existingEmails = await db.users.allEmails(); // I/O
  const result = processRegistration(existingEmails, input); // pure
  if (isRight(result)) {
    await db.users.save(result.value); // I/O
  }
  return result;
}
```

---

## Dependency Injection via Function Parameters

```javascript
// Hard-coded I/O — untestable
async function getActiveUsers() {
  return (await db.users.findAll()).filter(u => u.active);
}

// Injected — testable with any data source
const getActiveUsers = findAll => async () =>
  (await findAll()).filter(u => u.active);

// Production
const prodGetActiveUsers = getActiveUsers(() => db.users.findAll());

// Test
const fakeUsers = [{ id: "1", active: true }, { id: "2", active: false }];
const testGetActiveUsers = getActiveUsers(() => Promise.resolve(fakeUsers));
```
