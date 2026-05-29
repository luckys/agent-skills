# F# — Functional Programming Examples

Concepts covered: pure functions, pipe operator, currying, Option, Result, immutable records, higher-order functions, discriminated unions, computation expressions, side effect boundary.

F# is a functional-first language on .NET. It runs on the CLR and interoperates with C# and the full .NET ecosystem.

---

## Pure Functions and Referential Transparency

```fsharp
// All F# values are immutable by default
// let bindings cannot be reassigned (use mutable keyword to opt in, rarely needed)

let applyDiscount (rate: float) (price: float) : float =
    price * (1.0 - rate)

// Referentially transparent — (applyDiscount 0.1 100.0) = 90.0, always

// Record — immutable product type
type Cart = { Items: Item list; CouponCode: string option }

let addItem (cart: Cart) (item: Item) : Cart =
    { cart with Items = item :: cart.Items }
// with expression — creates a new Cart, original unchanged
```

---

## Pipe Operator (`|>`) and Composition (`>>`)

```fsharp
// |> — pipes the value on the left as the last argument to the right
let processOrder (orders: Order list) : float =
    orders
    |> List.filter (fun o -> o.Active)
    |> List.map (fun o -> o.Total)
    |> List.sum

// >> — right-to-left composition (f >> g = g(f(x)))
let normalizeEmail : string -> string =
    (fun s -> s.Trim()) >> (fun s -> s.ToLower())

// Multiple pipeline steps with named helpers
let filterActive    = List.filter (fun o -> o.Active)
let calculateTotals = List.map    (fun o -> o.Total)
let grandTotal      = List.sum

let summarize = filterActive >> calculateTotals >> grandTotal
```

---

## Currying (built-in)

```fsharp
// All F# functions are automatically curried
// add : int -> int -> int   is really   int -> (int -> int)

let add (x: int) (y: int) : int = x + y

let add5 : int -> int = add 5   // partial application — no special syntax

// Using partial application with pipeline
let applyDiscount (rate: float) (price: float) = price * (1.0 - rate)
let applyTenPercent = applyDiscount 0.1

[100.0; 200.0; 300.0] |> List.map applyTenPercent   // [90.0; 180.0; 270.0]
```

---

## Option — Explicit Absence

```fsharp
// type Option<'a> = None | Some of 'a

let findUser (id: string) (db: Map<string, User>) : User option =
    Map.tryFind id db

// Pattern matching — must handle both cases
let describeUser (maybeUser: User option) : string =
    match maybeUser with
    | None       -> "User not found"
    | Some user  -> sprintf "Found: %s" user.Name

// Option.map — transform if present
let getEmail (maybeUser: User option) : string option =
    Option.map (fun u -> u.Email) maybeUser
// or: maybeUser |> Option.map (fun u -> u.Email)

// Option.bind — chain optional computations (flatMap)
let getCity (user: User) : string option =
    user.Address |> Option.bind (fun addr -> addr.City)

// Option.defaultValue — provide a fallback
let displayCity (user: User) : string =
    getCity user |> Option.defaultValue "Unknown city"

// Computation expression for Option (with the FSharpPlus library)
let getCity user = option {
    let! address = user.Address
    let! city    = address.City
    return city
}
```

---

## Result — Explicit Failure

```fsharp
// type Result<'T,'E> = Ok of 'T | Error of 'E

type ValidationError =
    | InvalidEmail
    | InvalidAge

type User = { Email: string; Age: int }

let validateEmail (email: string) : Result<string, ValidationError> =
    if email.Contains("@") then Ok (email.ToLower())
    else Error InvalidEmail

let validateAge (age: int) : Result<int, ValidationError> =
    if age >= 0 && age <= 150 then Ok age
    else Error InvalidAge

// result computation expression — chains Result values, short-circuits on Error
let parseUser (email: string) (age: int) : Result<User, ValidationError> =
    result {
        let! validEmail = validateEmail email
        let! validAge   = validateAge age
        return { Email = validEmail; Age = validAge }
    }

// Pattern match at the call site
let showResult (res: Result<User, ValidationError>) : string =
    match res with
    | Error InvalidEmail -> "Bad email"
    | Error InvalidAge   -> "Bad age"
    | Ok user            -> sprintf "User: %s" user.Email

// Result.map and Result.bind for pipeline style
let processEmail email =
    email
    |> validateEmail
    |> Result.bind (fun e -> if e.Length > 5 then Ok e else Error InvalidEmail)
    |> Result.map  (fun e -> e.ToUpperInvariant())
```

---

## Discriminated Unions — Sum Types

```fsharp
// Discriminated union — exactly one variant at a time
type OrderStatus =
    | Pending
    | Shipped   of trackingCode: string
    | Delivered of deliveredAt: System.DateTime
    | Cancelled of reason: string

// Exhaustive pattern matching — compiler warns on missing cases
let describeStatus (status: OrderStatus) : string =
    match status with
    | Pending             -> "Awaiting shipment"
    | Shipped code        -> sprintf "Shipped — %s" code
    | Delivered delivAt   -> sprintf "Delivered on %s" (delivAt.ToShortDateString())
    | Cancelled reason    -> sprintf "Cancelled: %s" reason

// Recursive discriminated union
type Tree<'a> =
    | Leaf
    | Node of value: 'a * left: Tree<'a> * right: Tree<'a>

let rec depth (tree: Tree<'a>) : int =
    match tree with
    | Leaf              -> 0
    | Node (_, l, r)   -> 1 + max (depth l) (depth r)
```

---

## Immutable Records

```fsharp
type Address = { Street: string; City: string }
type User    = { Id: string; Name: string; Email: string; Address: Address option }

// Record copy-and-update expression
let updateEmail (user: User) (newEmail: string) : User =
    { user with Email = newEmail }

// Nested update
let updateCity (user: User) (city: string) : User =
    match user.Address with
    | None         -> user
    | Some address -> { user with Address = Some { address with City = city } }

// Single-case DU for nominal typing (equivalent to branded types in TS)
type UserId  = UserId  of string
type OrderId = OrderId of string

let makeUserId  (id: string) : UserId  = UserId id
let makeOrderId (id: string) : OrderId = OrderId id

let getUser (UserId id) = db.Users.FindById(id)

let orderId = makeOrderId "order-123"
// getUser orderId  — type error! OrderId ≠ UserId
```

---

## Higher-Order Functions

```fsharp
// List.map :: ('a -> 'b) -> 'a list -> 'b list
let doubled = List.map ((*) 2) [1; 2; 3]   // [2; 4; 6]

// List.filter :: ('a -> bool) -> 'a list -> 'a list
let evens = List.filter (fun n -> n % 2 = 0) [1..10]  // [2; 4; 6; 8; 10]

// List.fold :: ('b -> 'a -> 'b) -> 'b -> 'a list -> 'b
let total = List.fold (+) 0 [1; 2; 3; 4; 5]   // 15

// List.collect — flatMap
let allTags = posts |> List.collect (fun p -> p.Tags)

// List.groupBy :: ('a -> 'Key) -> 'a list -> ('Key * 'a list) list
let byStatus = orders |> List.groupBy (fun o -> o.Status)

// List.sortBy :: ('a -> 'Key) -> 'a list -> 'a list
let sorted = orders |> List.sortBy (fun o -> o.Total)
let sortedDesc = orders |> List.sortByDescending (fun o -> o.Total)

// Seq — lazy evaluation (infinite sequences possible)
let naturals = Seq.initInfinite id
let firstTenEvens = naturals |> Seq.filter (fun n -> n % 2 = 0) |> Seq.take 10
```

---

## Side Effect Boundary

```fsharp
open System

// Pure core — all logic, no I/O
let processRegistration
    (existingEmails: Set<string>)
    (input: RegistrationInput)
    (id: string)
    (now: DateTime)
    : Result<User, string> =
    let email = input.Email.ToLower().Trim()
    if not (email.Contains("@")) then
        Error "Invalid email"
    elif Set.contains email existingEmails then
        Error "Email already registered"
    else
        Ok { Id = id; Email = email; CreatedAt = now }

// Impure shell — thin I/O layer
let registerUser (input: RegistrationInput) : Async<Result<User, string>> =
    async {
        let! existingEmails = db.Users.AllEmails()                         // I/O
        let id  = Guid.NewGuid().ToString()                                 // I/O
        let now = DateTime.UtcNow                                           // I/O
        let result = processRegistration existingEmails input id now        // pure
        match result with
        | Ok user -> do! db.Users.Save(user)                               // I/O
        | Error _ -> ()
        return result
    }
```

---

## Async Computation Expression

```fsharp
// async {} desugars to Async<'T> — similar to Promise or IO
let fetchAndProcess (userId: string) : Async<string> =
    async {
        let! user    = db.Users.FindById(userId)    // await — non-blocking
        let! profile = db.Profiles.FindByUserId(userId)
        return sprintf "%s (%s)" user.Name profile.City
    }

// Railway-oriented programming with Result + async
let registerAsync input = async {
    let! emails = db.AllEmails()
    return
        input
        |> validateInput               // Result<ValidInput, Error>
        |> Result.bind (buildUser emails)  // Result<User, Error>
}
```
