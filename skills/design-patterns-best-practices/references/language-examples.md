# Language Examples

These examples show a small Strategy pattern because it is one of the safest and most common pattern introductions when replacing unstable branching logic.

## TypeScript

```typescript
interface TaxPolicy {
  calculate(subtotalInCents: number): number
}

class StandardTaxPolicy implements TaxPolicy {
  calculate(subtotalInCents: number): number {
    return Math.round(subtotalInCents * 0.21)
  }
}

class ReducedTaxPolicy implements TaxPolicy {
  calculate(subtotalInCents: number): number {
    return Math.round(subtotalInCents * 0.1)
  }
}

class Invoice {
  constructor(private readonly taxPolicy: TaxPolicy) {}

  tax(subtotalInCents: number): number {
    return this.taxPolicy.calculate(subtotalInCents)
  }
}
```

## Java

```java
public interface TaxPolicy {
    int calculate(int subtotalInCents);
}

public final class StandardTaxPolicy implements TaxPolicy {
    public int calculate(int subtotalInCents) {
        return Math.round(subtotalInCents * 0.21f);
    }
}

public final class Invoice {
    private final TaxPolicy taxPolicy;

    public Invoice(TaxPolicy taxPolicy) {
        this.taxPolicy = taxPolicy;
    }

    public int tax(int subtotalInCents) {
        return taxPolicy.calculate(subtotalInCents);
    }
}
```

## Python

```python
class TaxPolicy:
    def calculate(self, subtotal_in_cents: int) -> int:
        raise NotImplementedError


class StandardTaxPolicy(TaxPolicy):
    def calculate(self, subtotal_in_cents: int) -> int:
        return round(subtotal_in_cents * 0.21)


class Invoice:
    def __init__(self, tax_policy: TaxPolicy) -> None:
        self._tax_policy = tax_policy

    def tax(self, subtotal_in_cents: int) -> int:
        return self._tax_policy.calculate(subtotal_in_cents)
```

## C#

```csharp
public interface ITaxPolicy
{
    int Calculate(int subtotalInCents);
}

public sealed class StandardTaxPolicy : ITaxPolicy
{
    public int Calculate(int subtotalInCents)
    {
        return (int)Math.Round(subtotalInCents * 0.21);
    }
}

public sealed class Invoice
{
    private readonly ITaxPolicy taxPolicy;

    public Invoice(ITaxPolicy taxPolicy)
    {
        this.taxPolicy = taxPolicy;
    }

    public int Tax(int subtotalInCents)
    {
        return taxPolicy.Calculate(subtotalInCents);
    }
}
```

## Ruby

```ruby
class StandardTaxPolicy
  def calculate(subtotal_in_cents)
    (subtotal_in_cents * 0.21).round
  end
end

class Invoice
  def initialize(tax_policy)
    @tax_policy = tax_policy
  end

  def tax(subtotal_in_cents)
    @tax_policy.calculate(subtotal_in_cents)
  end
end
```

## PHP

```php
interface TaxPolicy
{
    public function calculate(int $subtotalInCents): int;
}

final class StandardTaxPolicy implements TaxPolicy
{
    public function calculate(int $subtotalInCents): int
    {
        return (int) round($subtotalInCents * 0.21);
    }
}

final class Invoice
{
    public function __construct(private TaxPolicy $taxPolicy)
    {
    }

    public function tax(int $subtotalInCents): int
    {
        return $this->taxPolicy->calculate($subtotalInCents);
    }
}
```

## What to Notice

- The variation is isolated behind a small role.
- `Invoice` depends on the behavior it needs, not on concrete branching details.
- Adding another tax policy becomes an additive change.
- The pattern shape remains recognizable across object-oriented languages.
