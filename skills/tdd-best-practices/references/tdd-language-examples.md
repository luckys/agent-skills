# TDD Language Examples

Each section shows a complete Red-Green-Refactor cycle for the same problem: a `Money` value object that rejects negative amounts and supports addition. Then a use case test showing test doubles.

---

## TypeScript (Jest / Vitest)

### Frameworks
- **Jest** — `jest`, `@types/jest`
- **Vitest** — `vitest` (faster, Vite-native)
- **ts-mockito** / `jest-mock-extended` — typed mocks

### Red — Failing test

```typescript
// money.test.ts
import { Money } from "./Money";

describe("Money", () => {
  it("should reject negative amounts", () => {
    expect(() => Money.of(-10, "EUR")).toThrow("Amount must be non-negative");
  });
});
```

### Green — Minimum code

```typescript
// Money.ts
export class Money {
  private constructor(
    private readonly amount: number,
    private readonly currency: string
  ) {}

  static of(amount: number, currency: string): Money {
    if (amount < 0) throw new Error("Amount must be non-negative");
    return new Money(amount, currency);
  }
}
```

### Next test — triangulate addition

```typescript
it("should add two amounts in the same currency", () => {
  const a = Money.of(10, "EUR");
  const b = Money.of(5, "EUR");
  expect(a.add(b).equals(Money.of(15, "EUR"))).toBe(true);
});

it("should reject addition of different currencies", () => {
  const eur = Money.of(10, "EUR");
  const usd = Money.of(5, "USD");
  expect(() => eur.add(usd)).toThrow("Currency mismatch");
});
```

### Refactor — complete implementation

```typescript
export class Money {
  private constructor(
    private readonly amount: number,
    private readonly currency: string
  ) {}

  static of(amount: number, currency: string): Money {
    if (amount < 0) throw new Error("Amount must be non-negative");
    return new Money(amount, currency);
  }

  add(other: Money): Money {
    if (this.currency !== other.currency) throw new Error("Currency mismatch");
    return Money.of(this.amount + other.amount, this.currency);
  }

  equals(other: Money): boolean {
    return this.amount === other.amount && this.currency === other.currency;
  }
}
```

### Use case test with test doubles

```typescript
// register-user.use-case.test.ts
import { mock } from "jest-mock-extended";
import { RegisterUserUseCase } from "./RegisterUserUseCase";
import { UserRepository } from "./UserRepository";
import { EventBus } from "../../shared/EventBus";

describe("RegisterUserUseCase", () => {
  const repo = mock<UserRepository>();
  const bus = mock<EventBus>();
  const useCase = new RegisterUserUseCase(repo, bus);

  it("should save the user and publish UserRegistered event", async () => {
    await useCase.execute({ email: "alice@example.com", name: "Alice" });

    expect(repo.save).toHaveBeenCalledOnce();
    expect(bus.publish).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ type: "UserRegistered" }),
      ])
    );
  });
});
```

---

## Java (JUnit 5 + Mockito)

### Frameworks
- **JUnit 5** — `org.junit.jupiter:junit-jupiter`
- **Mockito** — `org.mockito:mockito-core`
- **AssertJ** — fluent assertions: `org.assertj:assertj-core`

### Red — Failing test

```java
// MoneyTest.java
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.*;

class MoneyTest {

    @Test
    void shouldRejectNegativeAmount() {
        assertThatThrownBy(() -> Money.of(-10, "EUR"))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessage("Amount must be non-negative");
    }
}
```

### Green

```java
public final class Money {
    private final long amount;
    private final String currency;

    private Money(long amount, String currency) {
        this.amount = amount;
        this.currency = currency;
    }

    public static Money of(long amount, String currency) {
        if (amount < 0) throw new IllegalArgumentException("Amount must be non-negative");
        return new Money(amount, currency);
    }
}
```

### Next tests

```java
@Test
void shouldAddTwoAmountsInSameCurrency() {
    Money a = Money.of(10, "EUR");
    Money b = Money.of(5, "EUR");
    assertThat(a.add(b)).isEqualTo(Money.of(15, "EUR"));
}

@Test
void shouldRejectAdditionOfDifferentCurrencies() {
    Money eur = Money.of(10, "EUR");
    Money usd = Money.of(5, "USD");
    assertThatThrownBy(() -> eur.add(usd))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessage("Currency mismatch");
}
```

### Use case test with Mockito

```java
@ExtendWith(MockitoExtension.class)
class RegisterUserUseCaseTest {

    @Mock UserRepository repository;
    @Mock EventBus eventBus;
    @InjectMocks RegisterUserUseCase useCase;

    @Test
    void shouldSaveUserAndPublishEvent() {
        RegisterUserCommand command = new RegisterUserCommand("alice@example.com", "Alice");

        useCase.execute(command);

        verify(repository, times(1)).save(any(User.class));
        verify(eventBus, times(1)).publish(argThat(events ->
            events.stream().anyMatch(e -> e instanceof UserRegistered)
        ));
    }
}
```

---

## Python (pytest)

### Frameworks
- **pytest** — `pytest`
- **pytest-mock** — `pytest-mock` (wraps `unittest.mock`)
- **unittest.mock** — built-in

### Red — Failing test

```python
# test_money.py
import pytest
from money import Money

def test_rejects_negative_amount():
    with pytest.raises(ValueError, match="Amount must be non-negative"):
        Money(-10, "EUR")
```

### Green

```python
# money.py
class Money:
    def __init__(self, amount: float, currency: str) -> None:
        if amount < 0:
            raise ValueError("Amount must be non-negative")
        self._amount = amount
        self._currency = currency
```

### Next tests

```python
def test_adds_two_amounts_in_same_currency():
    a = Money(10, "EUR")
    b = Money(5, "EUR")
    assert a.add(b) == Money(15, "EUR")

def test_rejects_addition_of_different_currencies():
    eur = Money(10, "EUR")
    usd = Money(5, "USD")
    with pytest.raises(ValueError, match="Currency mismatch"):
        eur.add(usd)
```

### Refactor

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount must be non-negative")

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount + other.amount, self.currency)
```

### Use case test with pytest-mock

```python
# test_register_user.py
def test_saves_user_and_publishes_event(mocker):
    repo = mocker.Mock()
    event_bus = mocker.Mock()
    use_case = RegisterUserUseCase(repo, event_bus)

    use_case.execute(RegisterUserCommand(email="alice@example.com", name="Alice"))

    repo.save.assert_called_once()
    event_bus.publish.assert_called_once()
    published = event_bus.publish.call_args[0][0]
    assert any(isinstance(e, UserRegistered) for e in published)
```

---

## C# (xUnit + Moq)

### Frameworks
- **xUnit** — `xunit`, `xunit.runner.visualstudio`
- **Moq** — `Moq`
- **FluentAssertions** — `FluentAssertions`

### Red — Failing test

```csharp
// MoneyTests.cs
using Xunit;
using FluentAssertions;

public class MoneyTests
{
    [Fact]
    public void ShouldRejectNegativeAmount()
    {
        Action act = () => Money.Of(-10, "EUR");
        act.Should().Throw<ArgumentException>()
           .WithMessage("Amount must be non-negative*");
    }
}
```

### Green

```csharp
public sealed record Money
{
    public decimal Amount { get; }
    public string Currency { get; }

    private Money(decimal amount, string currency)
    {
        Amount = amount;
        Currency = currency;
    }

    public static Money Of(decimal amount, string currency)
    {
        if (amount < 0)
            throw new ArgumentException("Amount must be non-negative");
        return new Money(amount, currency);
    }
}
```

### Next tests

```csharp
[Fact]
public void ShouldAddTwoAmountsInSameCurrency()
{
    var a = Money.Of(10, "EUR");
    var b = Money.Of(5, "EUR");
    a.Add(b).Should().Be(Money.Of(15, "EUR"));
}

[Fact]
public void ShouldRejectAdditionOfDifferentCurrencies()
{
    var eur = Money.Of(10, "EUR");
    var usd = Money.Of(5, "USD");
    Action act = () => eur.Add(usd);
    act.Should().Throw<InvalidOperationException>().WithMessage("Currency mismatch*");
}
```

### Use case test with Moq

```csharp
public class RegisterUserUseCaseTests
{
    private readonly Mock<IUserRepository> _repoMock = new();
    private readonly Mock<IEventBus> _busMock = new();

    [Fact]
    public async Task ShouldSaveUserAndPublishEvent()
    {
        var useCase = new RegisterUserUseCase(_repoMock.Object, _busMock.Object);
        var command = new RegisterUserCommand("alice@example.com", "Alice");

        await useCase.Execute(command);

        _repoMock.Verify(r => r.Save(It.IsAny<User>()), Times.Once);
        _busMock.Verify(b => b.Publish(
            It.Is<IEnumerable<IDomainEvent>>(events =>
                events.Any(e => e is UserRegistered)
            )), Times.Once);
    }
}
```

---

## Ruby (RSpec)

### Frameworks
- **RSpec** — `rspec`
- **RSpec Mocks** — built into RSpec
- **FactoryBot** — test data factories

### Red — Failing test

```ruby
# spec/money_spec.rb
require "money"

RSpec.describe Money do
  describe ".new" do
    it "rejects negative amounts" do
      expect { Money.new(-10, "EUR") }.to raise_error(ArgumentError, "Amount must be non-negative")
    end
  end
end
```

### Green

```ruby
# lib/money.rb
class Money
  attr_reader :amount, :currency

  def initialize(amount, currency)
    raise ArgumentError, "Amount must be non-negative" if amount < 0
    @amount = amount
    @currency = currency
  end
end
```

### Next tests

```ruby
describe "#add" do
  it "adds two amounts in the same currency" do
    a = Money.new(10, "EUR")
    b = Money.new(5, "EUR")
    expect(a.add(b)).to eq(Money.new(15, "EUR"))
  end

  it "rejects addition of different currencies" do
    eur = Money.new(10, "EUR")
    usd = Money.new(5, "USD")
    expect { eur.add(usd) }.to raise_error(ArgumentError, "Currency mismatch")
  end
end
```

### Use case test with RSpec doubles

```ruby
# spec/use_cases/register_user_spec.rb
RSpec.describe RegisterUserUseCase do
  let(:repository) { instance_double(UserRepository) }
  let(:event_bus)  { instance_double(EventBus) }
  let(:use_case)   { described_class.new(repository, event_bus) }

  describe "#call" do
    it "saves the user and publishes UserRegistered event" do
      allow(repository).to receive(:save)
      allow(event_bus).to receive(:publish)

      use_case.call(email: "alice@example.com", name: "Alice")

      expect(repository).to have_received(:save).once
      expect(event_bus).to have_received(:publish).with(
        include(an_instance_of(UserRegistered))
      )
    end
  end
end
```

---

## PHP (PHPUnit)

### Frameworks
- **PHPUnit** — `phpunit/phpunit`
- **Mockery** — `mockery/mockery` (expressive mocks)
- **Prophecy** — built into older PHPUnit

### Red — Failing test

```php
// tests/Unit/MoneyTest.php
use PHPUnit\Framework\TestCase;

class MoneyTest extends TestCase
{
    public function test_rejects_negative_amount(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Amount must be non-negative');

        Money::of(-10, 'EUR');
    }
}
```

### Green

```php
// src/Money.php
final class Money
{
    private function __construct(
        private readonly float $amount,
        private readonly string $currency
    ) {}

    public static function of(float $amount, string $currency): self
    {
        if ($amount < 0) {
            throw new \InvalidArgumentException('Amount must be non-negative');
        }
        return new self($amount, $currency);
    }
}
```

### Next tests

```php
public function test_adds_two_amounts_in_same_currency(): void
{
    $a = Money::of(10, 'EUR');
    $b = Money::of(5, 'EUR');

    $this->assertTrue($a->add($b)->equals(Money::of(15, 'EUR')));
}

public function test_rejects_addition_of_different_currencies(): void
{
    $this->expectException(\InvalidArgumentException::class);
    $this->expectExceptionMessage('Currency mismatch');

    Money::of(10, 'EUR')->add(Money::of(5, 'USD'));
}
```

### Use case test with PHPUnit mocks

```php
class RegisterUserUseCaseTest extends TestCase
{
    private UserRepository $repository;
    private EventBus $eventBus;
    private RegisterUserUseCase $useCase;

    protected function setUp(): void
    {
        $this->repository = $this->createMock(UserRepository::class);
        $this->eventBus   = $this->createMock(EventBus::class);
        $this->useCase    = new RegisterUserUseCase($this->repository, $this->eventBus);
    }

    public function test_saves_user_and_publishes_event(): void
    {
        $this->repository->expects($this->once())->method('save');
        $this->eventBus->expects($this->once())->method('publish')
            ->with($this->callback(fn($events) =>
                collect($events)->contains(fn($e) => $e instanceof UserRegistered)
            ));

        ($this->useCase)(new RegisterUserCommand('alice@example.com', 'Alice'));
    }
}
```

---

## Go (testing + testify)

### Frameworks
- **testing** — stdlib, zero dependencies
- **testify** — `github.com/stretchr/testify` (assert, require, suite, mock)
- **mockery** — generates mocks from interfaces

### Red — Failing test

```go
// money_test.go
package domain_test

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "myapp/internal/domain"
)

func TestMoney_RejectsNegativeAmount(t *testing.T) {
    _, err := domain.NewMoney(-10, "EUR")
    assert.EqualError(t, err, "amount must be non-negative")
}
```

### Green — Minimum code

```go
// money.go
package domain

import "errors"

type Money struct {
    amount   int64
    currency string
}

func NewMoney(amount int64, currency string) (Money, error) {
    if amount < 0 {
        return Money{}, errors.New("amount must be non-negative")
    }
    return Money{amount: amount, currency: currency}, nil
}
```

### Next tests — triangulate addition

```go
func TestMoney_AddsSameCurrency(t *testing.T) {
    a, _ := domain.NewMoney(10, "EUR")
    b, _ := domain.NewMoney(5, "EUR")
    result, err := a.Add(b)
    assert.NoError(t, err)
    assert.Equal(t, int64(15), result.Amount())
}

func TestMoney_RejectsDifferentCurrencies(t *testing.T) {
    eur, _ := domain.NewMoney(10, "EUR")
    usd, _ := domain.NewMoney(5, "USD")
    _, err := eur.Add(usd)
    assert.EqualError(t, err, "currency mismatch")
}
```

### Use case test with testify mocks

```go
// register_user_test.go
package application_test

import (
    "context"
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "myapp/internal/application"
    "myapp/internal/domain"
)

// Mock generated by mockery or hand-written
type MockUserRepository struct{ mock.Mock }

func (m *MockUserRepository) Save(ctx context.Context, user *domain.User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

func (m *MockUserRepository) ExistsByEmail(ctx context.Context, email domain.Email) (bool, error) {
    args := m.Called(ctx, email)
    return args.Bool(0), args.Error(1)
}

type MockEventBus struct{ mock.Mock }

func (m *MockEventBus) Publish(ctx context.Context, events ...domain.DomainEvent) error {
    args := m.Called(ctx, events)
    return args.Error(0)
}

func TestRegisterUser_SavesAndPublishesEvent(t *testing.T) {
    repo := new(MockUserRepository)
    bus  := new(MockEventBus)

    repo.On("ExistsByEmail", mock.Anything, mock.Anything).Return(false, nil)
    repo.On("Save", mock.Anything, mock.AnythingOfType("*domain.User")).Return(nil)
    bus.On("Publish", mock.Anything, mock.Anything).Return(nil)

    uc := application.NewRegisterUserUseCase(repo, bus)
    err := uc.Execute(context.Background(), application.RegisterUserCommand{
        Email: "alice@example.com",
        Name:  "Alice",
    })

    assert.NoError(t, err)
    repo.AssertExpectations(t)
    bus.AssertExpectations(t)
}
```

---

## Rust (built-in `#[test]` + mockall)

### Frameworks
- **`#[test]`** — built-in, zero dependencies
- **mockall** — `mockall = "0.13"` (generates mocks via `#[automock]`)
- **rstest** — parametrized tests
- **assert_matches** — pattern-based assertions

### Red — Failing test

```rust
// src/domain/money.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_negative_amount() {
        let result = Money::new(-10, "EUR");
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "amount must be non-negative");
    }
}
```

### Green — Minimum code

```rust
#[derive(Debug, Clone, PartialEq)]
pub struct Money {
    amount: i64,
    currency: String,
}

impl Money {
    pub fn new(amount: i64, currency: impl Into<String>) -> Result<Self, &'static str> {
        if amount < 0 {
            return Err("amount must be non-negative");
        }
        Ok(Self { amount, currency: currency.into() })
    }
}
```

### Next tests — triangulate addition

```rust
#[test]
fn adds_same_currency() {
    let a = Money::new(10, "EUR").unwrap();
    let b = Money::new(5, "EUR").unwrap();
    let result = a.add(&b).unwrap();
    assert_eq!(result, Money::new(15, "EUR").unwrap());
}

#[test]
fn rejects_different_currencies() {
    let eur = Money::new(10, "EUR").unwrap();
    let usd = Money::new(5, "USD").unwrap();
    let err = eur.add(&usd).unwrap_err();
    assert_eq!(err, "currency mismatch");
}
```

### Refactor — complete implementation

```rust
impl Money {
    pub fn new(amount: i64, currency: impl Into<String>) -> Result<Self, &'static str> {
        if amount < 0 { return Err("amount must be non-negative"); }
        let currency = currency.into();
        if currency.is_empty() { return Err("currency required"); }
        Ok(Self { amount, currency })
    }

    pub fn add(&self, other: &Money) -> Result<Money, &'static str> {
        if self.currency != other.currency { return Err("currency mismatch"); }
        Ok(Money { amount: self.amount + other.amount, currency: self.currency.clone() })
    }

    pub fn amount(&self) -> i64    { self.amount }
    pub fn currency(&self) -> &str { &self.currency }
}
```

### Use case test with mockall

```rust
// src/application/register_user_test.rs
#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;
    use crate::domain::MockUserRepository;
    use crate::domain::MockEventBus;

    #[test]
    fn saves_user_and_publishes_event() {
        let mut repo = MockUserRepository::new();
        let mut bus  = MockEventBus::new();

        repo.expect_exists_by_email()
            .returning(|_| Ok(false));

        repo.expect_save()
            .once()
            .returning(|_| Ok(()));

        bus.expect_publish()
            .once()
            .returning(|_| Ok(()));

        let uc = RegisterUserUseCase::new(Box::new(repo), Box::new(bus));
        let result = uc.execute(RegisterUserCommand {
            email: "alice@example.com".into(),
            name: "Alice".into(),
        });

        assert!(result.is_ok());
    }
}
```

---

## Test Framework Quick Reference

| Language | Unit | Mocking | Assertions |
|---|---|---|---|
| TypeScript | Jest / Vitest | jest-mock-extended | expect() |
| Java | JUnit 5 | Mockito | AssertJ |
| Python | pytest | pytest-mock / unittest.mock | assert / pytest.raises |
| C# | xUnit | Moq / NSubstitute | FluentAssertions |
| Ruby | RSpec | RSpec Mocks | expect().to |
| PHP | PHPUnit | PHPUnit Mocks / Mockery | assertX() |
| Go | testing + testify | testify/mock + mockery | assert.X() / require.X() |
| Rust | #[test] built-in | mockall #[automock] | assert_eq! / assert! |
