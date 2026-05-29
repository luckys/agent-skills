# Elixir — Functional Programming Examples

Concepts covered: pure functions, pipe operator, pattern matching, `with` expression, `{:ok, _}` / `{:error, _}` tuples, immutable data, higher-order functions, structs, side effect boundary.

Elixir is a functional language on the Erlang VM (BEAM). Designed for concurrency, fault tolerance, and distributed systems. Data is always immutable.

---

## Pure Functions and Referential Transparency

```elixir
# Elixir values are immutable by default
# Functions return new values — originals are never modified

defmodule Pricing do
  def apply_discount(rate, price), do: price * (1 - rate)

  def add_item(cart, item) do
    %{cart | items: [item | cart.items]}
  end
  # Map update syntax — returns a new map, cart is unchanged
end
```

---

## Pipe Operator (`|>`)

```elixir
# |> passes the value on the left as the first argument to the right

defmodule OrderPipeline do
  def process(orders) do
    orders
    |> Enum.filter(&active?/1)
    |> Enum.map(&calculate_total/1)
    |> Enum.sum()
  end

  defp active?(order), do: order.status == :active

  defp calculate_total(order) do
    order.items
    |> Enum.map(& &1.price)
    |> Enum.sum()
  end
end

# String pipeline
"  Alice@Example.COM  "
|> String.trim()
|> String.downcase()
|> String.replace(~r/\s+/, "")
# => "alice@example.com"
```

---

## Currying and Partial Application

```elixir
# Elixir is not auto-curried, but closures and & capture work for partial application

# Capture syntax — reference a named function
double = &(&1 * 2)
Enum.map([1, 2, 3], double)     # [2, 4, 6]

# Closure as partial application
apply_discount = fn rate -> fn price -> price * (1 - rate) end end
apply_ten_percent = apply_discount.(0.1)
apply_ten_percent.(200)         # 180.0

# Using Kernel.then/1 for inline chaining
result =
  100
  |> then(&(&1 * 2))
  |> then(&(&1 + 10))
# => 210

# Higher-order function with configuration
def make_tax_fn(rate) do
  fn price -> price * (1 + rate) end
end

add_vat = make_tax_fn(0.21)
add_vat.(100)   # 121.0
```

---

## Pattern Matching

```elixir
# Pattern matching is the primary control flow tool
# Match on structure, not just value

defmodule UserParser do
  def describe_user(user) do
    case user do
      %{name: name, role: :admin} -> "Admin: #{name}"
      %{name: name, active: true} -> "Active user: #{name}"
      %{name: name}               -> "Inactive: #{name}"
      _                           -> "Unknown"
    end
  end

  # Pattern matching in function clauses
  def greet(%{name: name, role: :admin}), do: "Hello, admin #{name}!"
  def greet(%{name: name}),              do: "Hello, #{name}!"
  def greet(_),                          do: "Hello, stranger!"
end

# Destructuring in function arguments
def order_total(%{items: items}) do
  Enum.sum(Enum.map(items, & &1.price))
end

# Pin operator — match against an existing value
expected_id = "user-123"
%{id: ^expected_id, name: name} = user  # fails unless id matches expected_id
```

---

## `{:ok, value}` / `{:error, reason}` — Elixir's Either

```elixir
# Elixir convention: functions return {:ok, value} or {:error, reason}
# This is idiomatic Elixir — no library required

defmodule Validation do
  def validate_email(email) when is_binary(email) do
    if String.contains?(email, "@"),
      do:   {:ok, String.downcase(email)},
      else: {:error, :invalid_email}
  end
  def validate_email(_), do: {:error, :invalid_email}

  def validate_age(age) when is_integer(age) and age >= 0 and age <= 150,
    do: {:ok, age}
  def validate_age(_), do: {:error, :invalid_age}
end

# Case for single Result handling
def process_email(raw) do
  case Validation.validate_email(raw) do
    {:ok, email}    -> IO.puts("Valid: #{email}")
    {:error, reason} -> IO.puts("Error: #{reason}")
  end
end

# with — sequential chaining, short-circuits on non-matching clause
def parse_user(email, age) do
  with {:ok, valid_email} <- Validation.validate_email(email),
       {:ok, valid_age}   <- Validation.validate_age(age) do
    {:ok, %{email: valid_email, age: valid_age}}
  end
  # If any clause doesn't match, with returns that value automatically
end

# with + else for custom error handling
def parse_user(email, age) do
  with {:ok, valid_email} <- Validation.validate_email(email),
       {:ok, valid_age}   <- Validation.validate_age(age) do
    {:ok, %{email: valid_email, age: valid_age}}
  else
    {:error, :invalid_email} -> {:error, "Email must contain @"}
    {:error, :invalid_age}   -> {:error, "Age must be between 0 and 150"}
  end
end
```

---

## Structs and Immutable Data

```elixir
defmodule User do
  defstruct [:id, :name, :email, address: nil]

  # Struct update — returns a new struct
  def update_email(%User{} = user, new_email) do
    %{user | email: new_email}
  end

  # Nested update (no deep-merge built-in — manual)
  def update_city(%User{address: nil} = user, _city), do: user
  def update_city(%User{address: address} = user, city) do
    %{user | address: %{address | city: city}}
  end
end

# Map update syntax works on any map
user = %{id: "1", name: "Alice", email: "alice@example.com"}
updated = %{user | email: "new@example.com"}
# user is unchanged — updated is a new map

# Map.update/4 — apply a function to an existing value
cart = %{items: []}
Map.update(cart, :items, [], fn items -> [new_item | items] end)
```

---

## Higher-Order Functions (Enum and Stream)

```elixir
orders = [
  %{id: 1, status: :active,    total: 150.0},
  %{id: 2, status: :cancelled, total:  80.0},
  %{id: 3, status: :active,    total: 200.0}
]

# Enum.map — transform each element
Enum.map(orders, & &1.total)              # [150.0, 80.0, 200.0]

# Enum.filter — select by predicate
Enum.filter(orders, &(&1.status == :active))

# Enum.reduce — fold to a single value
Enum.reduce(orders, 0, fn o, acc -> acc + o.total end)  # 430.0

# Enum.flat_map — map then flatten (flatMap)
Enum.flat_map(orders, & &1.items)

# Enum.group_by — partition by key
Enum.group_by(orders, & &1.status)
# %{active: [...], cancelled: [...]}

# Enum.sort_by — sort by key
Enum.sort_by(orders, & &1.total)
Enum.sort_by(orders, & &1.total, :desc)

# Enum.zip
Enum.zip(["Alice", "Bob"], [90, 85])   # [{"Alice", 90}, {"Bob", 85}]

# Stream — lazy evaluation (no intermediate lists)
Stream.unfold(0, fn n -> {n, n + 1} end)  # infinite stream of naturals
|> Stream.filter(&Integer.is_even/1)
|> Stream.take(5)
|> Enum.to_list()   # [0, 2, 4, 6, 8]
```

---

## Pattern Matching on Sum Types (tagged tuples and structs)

```elixir
defmodule OrderStatus do
  def describe({:pending, _created_at}),
    do: "Awaiting shipment"

  def describe({:shipped, _created_at, tracking_code}),
    do: "Shipped — #{tracking_code}"

  def describe({:delivered, _created_at, delivered_at}),
    do: "Delivered on #{Date.to_string(delivered_at)}"

  def describe({:cancelled, _created_at, reason}),
    do: "Cancelled: #{reason}"
end

# Usage
OrderStatus.describe({:shipped, ~D[2026-05-01], "TRACK-456"})
# => "Shipped — TRACK-456"

# Using structs + protocols for more formal sum types
defprotocol Describable do
  def describe(status)
end

defmodule Pending   do defstruct [:created_at] end
defmodule Shipped   do defstruct [:created_at, :tracking_code] end
defmodule Cancelled do defstruct [:created_at, :reason] end

defimpl Describable, for: Pending do
  def describe(_), do: "Awaiting shipment"
end

defimpl Describable, for: Shipped do
  def describe(%{tracking_code: code}), do: "Shipped — #{code}"
end
```

---

## Side Effect Boundary

```elixir
defmodule Registration do
  # Pure core — all logic, no I/O
  def process(existing_emails, input, id, now) do
    email = input |> Map.get(:email, "") |> String.downcase() |> String.trim()

    cond do
      not String.contains?(email, "@") ->
        {:error, "Invalid email"}
      MapSet.member?(existing_emails, email) ->
        {:error, "Email already registered"}
      true ->
        {:ok, %{id: id, email: email, created_at: now}}
    end
  end

  # Impure shell — thin I/O coordination
  def register(input) do
    existing_emails = Db.all_emails()                      # I/O
    id = Ecto.UUID.generate()                              # I/O (randomness)
    now = DateTime.utc_now()                               # I/O (time)

    case process(existing_emails, input, id, now) do       # pure
      {:ok, user} ->
        Db.save_user(user)                                 # I/O
        {:ok, user}
      {:error, _} = error ->
        error
    end
  end
end

# Dependency injection via function arguments (for testing)
def register(input, fetch_emails \\ &Db.all_emails/0, save_user \\ &Db.save_user/1) do
  existing = fetch_emails.()
  # ...
end
```

---

## GenServer (stateful process — FP + OTP)

```elixir
# GenServer separates pure message handling from process lifecycle
defmodule Counter do
  use GenServer

  # Pure callbacks — handle state transitions
  def handle_call(:get, _from, state), do: {:reply, state, state}
  def handle_cast(:increment, state),  do: {:noreply, state + 1}
  def handle_cast(:reset, _state),     do: {:noreply, 0}

  # Client API
  def start_link(initial), do: GenServer.start_link(__MODULE__, initial, name: __MODULE__)
  def get,                  do: GenServer.call(__MODULE__, :get)
  def increment,            do: GenServer.cast(__MODULE__, :increment)
  def reset,                do: GenServer.cast(__MODULE__, :reset)
end
```
