# Language Examples

Side-by-side examples of core FP patterns across JavaScript, TypeScript, Haskell, Elm, Clojure, F#, and Elixir.

## Problem: Parse and Validate User Input

Parse a raw input object, validate it, and return either an error or a valid domain object.

---

### JavaScript (with fp-ts)

```javascript
// Pure — no library, just functions returning plain objects
const validateEmail = (email) => {
  if (!email?.includes("@")) return { ok: false, error: "Invalid email" };
  return { ok: true, value: email.toLowerCase().trim() };
};

const validateAge = (age) => {
  const n = parseInt(age, 10);
  if (isNaN(n) || n < 0 || n > 150) return { ok: false, error: "Invalid age" };
  return { ok: true, value: n };
};

const parseUser = (input) => {
  const email = validateEmail(input.email);
  if (!email.ok) return email;
  const age = validateAge(input.age);
  if (!age.ok) return age;
  return { ok: true, value: { email: email.value, age: age.value } };
};

// With Ramda for pipelines
const R = require("ramda");
const normalizeInput = R.pipe(
  R.evolve({ email: R.toLower, name: R.trim }),
  R.pick(["email", "name", "age"])
);
```

---

### TypeScript (with fp-ts)

```typescript
import { pipe } from "fp-ts/function";
import * as E from "fp-ts/Either";

type ValidationError = string;
type User = { email: string; age: number };

const validateEmail = (email: string): E.Either<ValidationError, string> =>
  email.includes("@")
    ? E.right(email.toLowerCase().trim())
    : E.left("Invalid email");

const validateAge = (age: number): E.Either<ValidationError, number> =>
  age >= 0 && age <= 150
    ? E.right(age)
    : E.left("Age out of range");

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
const result = parseUser({ email: "alice@example.com", age: 30 });
pipe(
  result,
  E.match(
    (error) => console.error("Validation failed:", error),
    (user) => console.log("Valid user:", user)
  )
);
```

---

### Haskell

```haskell
module UserParser where

import Data.Char (toLower)
import Data.List (isInfixOf)

data ValidationError = InvalidEmail | InvalidAge deriving (Show)
data User = User { email :: String, age :: Int } deriving (Show)

validateEmail :: String -> Either ValidationError String
validateEmail email
  | "@" `isInfixOf` email = Right (map toLower email)
  | otherwise             = Left InvalidEmail

validateAge :: Int -> Either ValidationError Int
validateAge age
  | age >= 0 && age <= 150 = Right age
  | otherwise              = Left InvalidAge

parseUser :: String -> Int -> Either ValidationError User
parseUser rawEmail rawAge = do
  validEmail <- validateEmail rawEmail     -- do-notation is monadic chain
  validAge   <- validateAge rawAge
  return (User validEmail validAge)

-- Usage
-- parseUser "alice@example.com" 30  → Right (User "alice@example.com" 30)
-- parseUser "notanemail" 30         → Left InvalidEmail
```

---

### Elm

```elm
module UserParser exposing (..)

type alias User =
    { email : String, age : Int }

type ValidationError
    = InvalidEmail
    | InvalidAge

validateEmail : String -> Result ValidationError String
validateEmail email =
    if String.contains "@" email then
        Ok (String.toLower email)
    else
        Err InvalidEmail

validateAge : Int -> Result ValidationError Int
validateAge age =
    if age >= 0 && age <= 150 then
        Ok age
    else
        Err InvalidAge

parseUser : String -> Int -> Result ValidationError User
parseUser rawEmail rawAge =
    Result.map2 User
        (validateEmail rawEmail)
        (validateAge rawAge)

-- Usage in update function
case parseUser model.emailInput model.ageInput of
    Ok user -> { model | user = Just user, error = Nothing }
    Err InvalidEmail -> { model | error = Just "Invalid email" }
    Err InvalidAge -> { model | error = Just "Invalid age" }
```

---

### Clojure

```clojure
(ns user-parser.core)

(defn validate-email [email]
  (if (clojure.string/includes? email "@")
    {:ok true :value (clojure.string/lower-case email)}
    {:ok false :error "Invalid email"}))

(defn validate-age [age]
  (if (and (integer? age) (<= 0 age 150))
    {:ok true :value age}
    {:ok false :error "Invalid age"}))

(defn parse-user [{:keys [email age]}]
  (let [email-result (validate-email email)
        age-result   (validate-age age)]
    (if (and (:ok email-result) (:ok age-result))
      {:ok true :value {:email (:value email-result) :age (:value age-result)}}
      (first (filter #(not (:ok %)) [email-result age-result])))))

;; With threading macros
(defn process-orders [orders]
  (->> orders
       (filter :active)
       (map #(update % :total * 1.1))
       (sort-by :total >)
       (take 10)))
```

---

### F#

```fsharp
module UserParser

type ValidationError = InvalidEmail | InvalidAge
type User = { Email: string; Age: int }

let validateEmail (email: string) =
    if email.Contains("@") then Ok (email.ToLower())
    else Error InvalidEmail

let validateAge (age: int) =
    if age >= 0 && age <= 150 then Ok age
    else Error InvalidAge

let parseUser (email: string) (age: int) =
    result {
        let! validEmail = validateEmail email   // computation expression
        let! validAge   = validateAge age
        return { Email = validEmail; Age = validAge }
    }

// Pipeline with |> operator
let processOrders orders =
    orders
    |> List.filter (fun o -> o.Active)
    |> List.map (fun o -> { o with Total = o.Total * 1.1 })
    |> List.sortByDescending (fun o -> o.Total)
    |> List.truncate 10
```

---

### Elixir

```elixir
defmodule UserParser do
  def validate_email(email) do
    if String.contains?(email, "@") do
      {:ok, String.downcase(email)}
    else
      {:error, :invalid_email}
    end
  end

  def validate_age(age) when is_integer(age) and age >= 0 and age <= 150 do
    {:ok, age}
  end
  def validate_age(_), do: {:error, :invalid_age}

  def parse_user(email, age) do
    with {:ok, valid_email} <- validate_email(email),
         {:ok, valid_age}   <- validate_age(age) do
      {:ok, %{email: valid_email, age: valid_age}}
    end
  end
end

# Pipeline with |> operator
def process_orders(orders) do
  orders
  |> Enum.filter(& &1.active)
  |> Enum.map(&%{&1 | total: &1.total * 1.1})
  |> Enum.sort_by(& &1.total, :desc)
  |> Enum.take(10)
end
```

---

## Pattern: Function Composition and Pipe

```javascript
// JavaScript — manual pipe
const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x);

const processOrder = pipe(
  filterActiveItems,
  calculateSubtotal,
  applyTax(0.21),
  formatCurrency
);
```

```typescript
// TypeScript — fp-ts pipe
import { pipe } from "fp-ts/function";

const processOrder = (order: Order) =>
  pipe(
    order,
    filterActiveItems,
    calculateSubtotal,
    applyTax(0.21),
    formatCurrency
  );
```

```haskell
-- Haskell — (.) composition operator
processOrder :: Order -> String
processOrder = formatCurrency . applyTax 0.21 . calculateSubtotal . filterActiveItems

-- Or with & (left-to-right)
processOrder order = order
  & filterActiveItems
  & calculateSubtotal
  & applyTax 0.21
  & formatCurrency
```

```clojure
;; Clojure — -> threading macro (left-to-right)
(defn process-order [order]
  (-> order
      filter-active-items
      calculate-subtotal
      (apply-tax 0.21)
      format-currency))
```

```elixir
# Elixir — |> pipeline operator
def process_order(order) do
  order
  |> filter_active_items()
  |> calculate_subtotal()
  |> apply_tax(0.21)
  |> format_currency()
end
```

---

## Pattern: Maybe / Option — Safe Navigation

```typescript
// TypeScript — fp-ts Option
import { pipe } from "fp-ts/function";
import * as O from "fp-ts/Option";

const getCity = (user: User): O.Option<string> =>
  pipe(
    O.fromNullable(user.address),
    O.chain(addr => O.fromNullable(addr.city))
  );
```

```haskell
-- Haskell — Maybe monad
getCity :: User -> Maybe String
getCity user = do
  address <- userAddress user
  city    <- addressCity address
  return city

-- Or with >>= (bind)
getCity user = userAddress user >>= addressCity
```

```elm
-- Elm — Maybe
getCity : User -> Maybe String
getCity user =
    user.address
        |> Maybe.andThen .city
```

---

## Pattern: Immutable Data Transforms

```javascript
// JavaScript — spread for immutable updates
const updateEmail = (user, newEmail) => ({ ...user, email: newEmail });
const addItem = (cart, item) => ({ ...cart, items: [...cart.items, item] });
```

```clojure
;; Clojure — persistent data structures by default
(defn update-email [user new-email]
  (assoc user :email new-email))

(defn add-item [cart item]
  (update cart :items conj item))
```

```haskell
-- Haskell — record update syntax
updateEmail :: User -> String -> User
updateEmail user newEmail = user { email = newEmail }
```

```elixir
# Elixir — Map.put / struct update
def update_email(user, new_email), do: %{user | email: new_email}
def add_item(cart, item), do: %{cart | items: [item | cart.items]}
```

---

## Framework Quick Reference

| Language | Pipe | Compose | Option | Either | HOF library |
|---|---|---|---|---|---|
| JavaScript | `pipe` (Ramda, fp-ts) | `compose` (Ramda) | `fp-ts/Option` | `fp-ts/Either` | Ramda, Lodash/FP |
| TypeScript | `pipe` (fp-ts) | `flow` (fp-ts) | `fp-ts/Option` | `fp-ts/Either` | fp-ts, Effect-TS |
| Haskell | `&` | `.` | `Maybe` (built-in) | `Either` (built-in) | Prelude, Data.List |
| Elm | `\|>` | `<<` / `>>` | `Maybe` (built-in) | `Result` (built-in) | elm/core |
| Clojure | `->` / `->>` | `comp` | `nil` + guards | `ex-info` / cats | clojure.core |
| F# | `\|>` | `>>` | `Option` (built-in) | `Result` (built-in) | FSharpPlus |
| Elixir | `\|>` | n/a | `:ok` / `:error` tuples | `with` expression | Enum, Stream |
| Scala | `\|>` (Cats) | `andThen` | `Option` (built-in) | `Either` (built-in) | Cats, ZIO |
