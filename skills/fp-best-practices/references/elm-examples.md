# Elm — Functional Programming Examples

Concepts covered: pure functions, pipe operator, Maybe, Result, immutable records, higher-order functions, sum types (custom types), The Elm Architecture (TEA), no runtime exceptions.

Elm is a purely functional language for frontend. Side effects are modeled as commands and subscriptions managed by the Elm runtime — no explicit IO monad needed.

---

## Pure Functions and No Runtime Exceptions

```elm
-- All Elm functions are pure
-- There are no exceptions: impossible states are prevented by types

applyDiscount : Float -> Float -> Float
applyDiscount rate price =
    price * (1 - rate)

-- Elm has no null — use Maybe instead
safeDivide : Float -> Float -> Maybe Float
safeDivide _ 0 = Nothing
safeDivide a b = Just (a / b)
```

---

## Pipeline Operator (`|>`)

```elm
-- |> passes the value on the left as the last argument to the function on the right
processOrder : List Order -> Float
processOrder orders =
    orders
        |> List.filter isActive
        |> List.map orderTotal
        |> List.sum

-- Composition operators
-- (<<) right-to-left:  (f << g) x = f (g x)
-- (>>) left-to-right:  (f >> g) x = g (f x)

normalizeEmail : String -> String
normalizeEmail =
    String.trim >> String.toLower
```

---

## Currying (built-in)

```elm
-- All Elm functions are automatically curried
-- add : Int -> Int -> Int  is  Int -> (Int -> Int)

add : Int -> Int -> Int
add x y = x + y

add5 : Int -> Int
add5 = add 5   -- partial application

-- Sections with operators
double : List Int -> List Int
double = List.map ((*) 2)

greaterThan10 : List Int -> List Int
greaterThan10 = List.filter (\x -> x > 10)
```

---

## Maybe — Explicit Absence

```elm
-- type Maybe a = Nothing | Just a

findUser : UserId -> Dict UserId User -> Maybe User
findUser id db =
    Dict.get id db

-- Pattern matching — exhaustive
describeUser : Maybe User -> String
describeUser maybeUser =
    case maybeUser of
        Nothing ->
            "User not found"
        Just user ->
            "Found: " ++ user.name

-- Maybe.map — transform the value if present
getEmail : Maybe User -> Maybe String
getEmail maybeUser =
    Maybe.map .email maybeUser

-- Maybe.andThen — chain optional computations (like flatMap)
getCity : User -> Maybe String
getCity user =
    user.address
        |> Maybe.andThen .city

-- withDefault — provide a fallback
displayCity : User -> String
displayCity user =
    getCity user
        |> Maybe.withDefault "Unknown city"
```

---

## Result — Explicit Failure

```elm
-- type Result error value = Err error | Ok value

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

-- Result.andThen — chain dependent validations
parseUser : String -> Int -> Result ValidationError User
parseUser email age =
    validateEmail email
        |> Result.andThen
            (\validEmail ->
                validateAge age
                    |> Result.map (\validAge -> { email = validEmail, age = validAge })
            )

-- Result.map2 — combine two independent Results
parseUser2 : String -> Int -> Result ValidationError User
parseUser2 email age =
    Result.map2 (\e a -> { email = e, age = a })
        (validateEmail email)
        (validateAge age)

-- Pattern match at the view/update boundary
viewResult : Result ValidationError User -> Html msg
viewResult result =
    case result of
        Err InvalidEmail ->
            text "Please enter a valid email"
        Err InvalidAge ->
            text "Age must be between 0 and 150"
        Ok user ->
            text ("Welcome, " ++ user.email)
```

---

## Custom Types — Sum Types

```elm
-- Custom types are sum types with pattern matching
type OrderStatus
    = Pending
    | Shipped String           -- carries tracking code
    | Delivered Time.Posix
    | Cancelled String         -- carries reason

describeStatus : OrderStatus -> String
describeStatus status =
    case status of
        Pending ->
            "Awaiting shipment"
        Shipped trackingCode ->
            "Shipped — " ++ trackingCode
        Delivered deliveredAt ->
            "Delivered on " ++ formatTime deliveredAt
        Cancelled reason ->
            "Cancelled: " ++ reason

-- Recursive custom type
type Tree a
    = Leaf
    | Node a (Tree a) (Tree a)

depth : Tree a -> Int
depth tree =
    case tree of
        Leaf ->
            0
        Node _ left right ->
            1 + max (depth left) (depth right)
```

---

## Immutable Records

```elm
type alias User =
    { id : String
    , name : String
    , email : String
    , address : Maybe Address
    }

type alias Address =
    { street : String
    , city : String
    }

-- Record update syntax — creates a new record, original unchanged
updateEmail : User -> String -> User
updateEmail user newEmail =
    { user | email = newEmail }

-- Nested update (manual spreading required)
updateCity : User -> String -> User
updateCity user city =
    case user.address of
        Nothing ->
            user
        Just addr ->
            { user | address = Just { addr | city = city } }
```

---

## Higher-Order Functions

```elm
-- List.map :: (a -> b) -> List a -> List b
doubled : List Int
doubled = List.map ((*) 2) [ 1, 2, 3 ]  -- [2, 4, 6]

-- List.filter :: (a -> Bool) -> List a -> List a
activeOrders : List Order -> List Order
activeOrders = List.filter .active

-- List.foldl :: (a -> b -> b) -> b -> List a -> b
total : List Order -> Float
total = List.foldl (\order acc -> acc + order.total) 0.0

-- List.concatMap — flatMap equivalent
allTags : List Post -> List String
allTags = List.concatMap .tags

-- List.indexedMap — map with index
withIndex : List a -> List ( Int, a )
withIndex = List.indexedMap Tuple.pair

-- Dict.map, Dict.filter — work on dictionaries
activeCounts : Dict String Int -> Dict String Int
activeCounts = Dict.filter (\_ count -> count > 0)
```

---

## The Elm Architecture (TEA) — Side Effect Boundary

```elm
-- Side effects are commands (Cmd) and subscriptions (Sub)
-- Pure update function — testable without I/O
type Msg
    = EmailChanged String
    | SubmitForm
    | UserRegistered (Result Http.Error User)

type alias Model =
    { email : String
    , status : Status
    }

type Status
    = Idle
    | Loading
    | Success User
    | Failure String

-- Pure — no I/O, returns new model + a command (effect description)
update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        EmailChanged email ->
            ( { model | email = email }, Cmd.none )

        SubmitForm ->
            ( { model | status = Loading }
            , registerUser model.email   -- produces a Cmd, not a real HTTP call
            )

        UserRegistered (Ok user) ->
            ( { model | status = Success user }, Cmd.none )

        UserRegistered (Err _) ->
            ( { model | status = Failure "Registration failed" }, Cmd.none )

-- HTTP command builder (pure description of an effect)
registerUser : String -> Cmd Msg
registerUser email =
    Http.post
        { url = "/api/users"
        , body = Http.jsonBody (encodeEmail email)
        , expect = Http.expectJson UserRegistered userDecoder
        }
```

---

## Decoder Pattern — Safe JSON Parsing

```elm
import Json.Decode as Decode exposing (Decoder)

type alias User =
    { id : String
    , name : String
    , email : String
    }

-- Decoder is a description of how to parse JSON — pure and composable
userDecoder : Decoder User
userDecoder =
    Decode.map3 User
        (Decode.field "id" Decode.string)
        (Decode.field "name" Decode.string)
        (Decode.field "email" Decode.string)

-- Decode.andThen for validated parsing
ageDecoder : Decoder Int
ageDecoder =
    Decode.int
        |> Decode.andThen
            (\age ->
                if age >= 0 && age <= 150 then
                    Decode.succeed age
                else
                    Decode.fail "Age out of range"
            )
```
