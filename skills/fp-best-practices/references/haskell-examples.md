# Haskell — Functional Programming Examples

Concepts covered: pure functions, function composition, currying, Maybe, Either, immutable records, higher-order functions, sum types, IO boundary, typeclasses.

Haskell is a purely functional language — all these patterns are idiomatic, not add-ons.

---

## Pure Functions and Referential Transparency

```haskell
-- All Haskell functions are pure by default
-- A function cannot access external state unless IO is in its type

applyDiscount :: Double -> Double -> Double
applyDiscount rate price = price * (1 - rate)

-- Referentially transparent — can substitute call with its result
-- applyDiscount 0.1 100.0  ≡  90.0   everywhere

addItem :: Cart -> Item -> Cart
addItem cart item = cart { items = item : items cart }
-- Record update syntax — produces a new Cart, original unchanged
```

---

## Function Composition

```haskell
-- (.) operator — right-to-left composition
processEmail :: String -> String
processEmail = formatForDisplay . validate . normalize
  where
    normalize  = map toLower . strip
    validate e = if '@' `elem` e then e else error "Invalid"
    formatForDisplay e = "<" ++ e ++ ">"

-- (&) operator — left-to-right (like pipe)
processOrder :: [Order] -> Summary
processOrder orders = orders
  & filter isActive
  & map orderTotal
  & sum
  & buildSummary

-- ($) — function application, avoids parentheses
-- map double $ filter even [1..10]
-- is equivalent to: map double (filter even [1..10])
```

---

## Currying (built into the language)

```haskell
-- Every function in Haskell is curried by default
-- add :: Int -> Int -> Int   is actually  Int -> (Int -> Int)
add :: Int -> Int -> Int
add x y = x + y

add5 :: Int -> Int
add5 = add 5      -- partial application — no special syntax needed

-- Sections: partially apply an operator
double :: [Int] -> [Int]
double = map (* 2)

greaterThan10 :: [Int] -> [Int]
greaterThan10 = filter (> 10)

-- Flip argument order
flippedDiv :: Int -> Int -> Int
flippedDiv = flip div
-- flippedDiv 2 10 = 10 `div` 2 = 5
```

---

## Maybe — Explicit Absence

```haskell
-- Maybe is built into Prelude
-- data Maybe a = Nothing | Just a

findUser :: UserId -> Maybe User
findUser uid = Map.lookup uid userDatabase

-- Pattern matching — must handle both cases
describeUser :: UserId -> String
describeUser uid =
  case findUser uid of
    Nothing   -> "User not found"
    Just user -> "Found: " ++ userName user

-- Functor — map over the value inside Maybe
getEmail :: UserId -> Maybe String
getEmail uid = fmap userEmail (findUser uid)
-- or:  userEmail <$> findUser uid

-- Monad — chain Maybe computations (short-circuits on Nothing)
getCity :: UserId -> Maybe String
getCity uid = do
  user    <- findUser uid
  address <- userAddress user
  city    <- addressCity address
  return city

-- With >>= (bind) — same as do-notation
getCity' :: UserId -> Maybe String
getCity' uid = findUser uid >>= userAddress >>= addressCity

-- fromMaybe — provide a default
displayCity :: UserId -> String
displayCity uid = fromMaybe "Unknown city" (getCity uid)
```

---

## Either — Explicit Failure

```haskell
-- data Either e a = Left e | Right a
-- Left = error, Right = success (mnemonic: "right" = correct)

data ValidationError = InvalidEmail | InvalidAge deriving (Show)
data User = User { email :: String, age :: Int } deriving (Show)

validateEmail :: String -> Either ValidationError String
validateEmail email
  | '@' `elem` email = Right (map toLower email)
  | otherwise        = Left InvalidEmail

validateAge :: Int -> Either ValidationError Int
validateAge age
  | age >= 0 && age <= 150 = Right age
  | otherwise              = Left InvalidAge

-- do-notation chains Either (short-circuits on Left)
parseUser :: String -> Int -> Either ValidationError User
parseUser rawEmail rawAge = do
  validEmail <- validateEmail rawEmail
  validAge   <- validateAge rawAge
  return (User validEmail validAge)

-- Pattern matching at the call site
showResult :: Either ValidationError User -> String
showResult (Left InvalidEmail) = "Bad email"
showResult (Left InvalidAge)   = "Bad age"
showResult (Right user)        = "User: " ++ email user
```

---

## Sum Types — Algebraic Data Types

```haskell
-- Sum type: a value is exactly one variant
data OrderStatus
  = Pending  { createdAt :: UTCTime }
  | Shipped  { createdAt :: UTCTime, trackingCode :: String }
  | Delivered { createdAt :: UTCTime, deliveredAt :: UTCTime }
  | Cancelled { createdAt :: UTCTime, reason :: String }

-- Pattern matching is exhaustive — GHC warns if a case is missing
describeStatus :: OrderStatus -> String
describeStatus (Pending _)           = "Awaiting shipment"
describeStatus (Shipped _ code)      = "Shipped: " ++ code
describeStatus (Delivered _ delAt)   = "Delivered: " ++ show delAt
describeStatus (Cancelled _ reason)  = "Cancelled: " ++ reason

-- Recursive sum type
data Tree a = Leaf | Node a (Tree a) (Tree a)

depth :: Tree a -> Int
depth Leaf         = 0
depth (Node _ l r) = 1 + max (depth l) (depth r)
```

---

## Immutable Records

```haskell
data User = User
  { userId    :: UserId
  , userEmail :: String
  , userName  :: String
  } deriving (Show, Eq)

-- Record update syntax — creates a new value, original unchanged
updateEmail :: User -> String -> User
updateEmail user newEmail = user { userEmail = newEmail }

-- Lens-based deep updates (with the `lens` library)
import Control.Lens

data Profile = Profile { _user :: User, _address :: Address }
makeLenses ''Profile  -- generates user and address lenses

data Address = Address { _city :: String }
makeLenses ''Address

-- Update nested field without manual spreading
updateCity :: Profile -> String -> Profile
updateCity profile city = profile & user . address . city .~ city
-- original profile is unchanged; a new Profile is returned
```

---

## Higher-Order Functions

```haskell
-- map :: (a -> b) -> [a] -> [b]
doubled :: [Int]
doubled = map (* 2) [1, 2, 3]  -- [2, 4, 6]

-- filter :: (a -> Bool) -> [a] -> [a]
evens :: [Int]
evens = filter even [1..10]     -- [2, 4, 6, 8, 10]

-- foldl / foldr :: (b -> a -> b) -> b -> [a] -> b
total :: Int
total = foldl (+) 0 [1, 2, 3, 4, 5]  -- 15

-- concatMap (equivalent to flatMap)
allWords :: [String]
allWords = concatMap words ["hello world", "foo bar"]
-- ["hello", "world", "foo", "bar"]

-- zipWith :: (a -> b -> c) -> [a] -> [b] -> [c]
combined :: [(String, Int)]
combined = zipWith (,) ["Alice", "Bob"] [90, 85]

-- Custom HOF — takes a function as argument
applyTwice :: (a -> a) -> a -> a
applyTwice f x = f (f x)
applyTwice (+ 3) 10  -- 16
```

---

## Typeclasses (Functor, Applicative, Monad)

```haskell
-- Functor: anything you can map over
-- fmap :: Functor f => (a -> b) -> f a -> f b
fmap (* 2) (Just 5)     -- Just 10
fmap (* 2) Nothing      -- Nothing
fmap (* 2) [1, 2, 3]    -- [2, 4, 6]
fmap (* 2) (Right 5)    -- Right 10

-- Applicative: apply a wrapped function to a wrapped value
-- (<*>) :: Applicative f => f (a -> b) -> f a -> f b
Just (* 2) <*> Just 5   -- Just 10
(+) <$> Just 3 <*> Just 5  -- Just 8  (parallel: both must be Just)

-- Monad: sequencing dependent computations
-- (>>=) :: Monad m => m a -> (a -> m b) -> m b
Just 5 >>= \x -> Just (x * 2)   -- Just 10
Nothing >>= \x -> Just (x * 2)  -- Nothing  (short-circuits)

-- do-notation desugars to >>= and >>
processUser :: UserId -> IO String
processUser uid = do
  maybeUser <- findUserIO uid          -- IO (Maybe User)
  case maybeUser of
    Nothing   -> return "Not found"
    Just user -> return (userName user)
```

---

## IO Boundary

```haskell
-- In Haskell, IO in the type signature is the explicit marker for side effects
-- Functions without IO are pure — enforced by the compiler

-- Pure — no IO
calculateTotal :: [Item] -> Double
calculateTotal = sum . map itemPrice

-- Impure — IO in the type
loadAndProcess :: FilePath -> IO Double
loadAndProcess path = do
  contents <- readFile path            -- IO — reads file
  let items = parseItems contents      -- pure
  return (calculateTotal items)        -- pure, lifted into IO

-- The shell is a thin layer; the core is pure
main :: IO ()
main = do
  total <- loadAndProcess "orders.csv"
  putStrLn ("Total: " ++ show total)
```
