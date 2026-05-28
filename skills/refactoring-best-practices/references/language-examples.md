# Language Examples

These examples show a refactoring move from branching logic toward role-based collaboration.

## Before

```typescript
function discountAmount(customerType: string, subtotalInCents: number): number {
  if (customerType === 'premium') {
    return Math.round(subtotalInCents * 0.8)
  }

  if (customerType === 'partner') {
    return Math.round(subtotalInCents * 0.85)
  }

  return subtotalInCents
}
```

## After in TypeScript

```typescript
interface PricingPolicy {
  apply(subtotalInCents: number): number
}

class StandardPricing implements PricingPolicy {
  apply(subtotalInCents: number): number {
    return subtotalInCents
  }
}

class PremiumPricing implements PricingPolicy {
  apply(subtotalInCents: number): number {
    return Math.round(subtotalInCents * 0.8)
  }
}

class PartnerPricing implements PricingPolicy {
  apply(subtotalInCents: number): number {
    return Math.round(subtotalInCents * 0.85)
  }
}
```

## After in Java

```java
public interface PricingPolicy {
    int apply(int subtotalInCents);
}

public final class StandardPricing implements PricingPolicy {
    public int apply(int subtotalInCents) {
        return subtotalInCents;
    }
}

public final class PremiumPricing implements PricingPolicy {
    public int apply(int subtotalInCents) {
        return Math.round(subtotalInCents * 0.8f);
    }
}
```

## After in Python

```python
class PricingPolicy:
    def apply(self, subtotal_in_cents: int) -> int:
        raise NotImplementedError


class StandardPricing(PricingPolicy):
    def apply(self, subtotal_in_cents: int) -> int:
        return subtotal_in_cents


class PremiumPricing(PricingPolicy):
    def apply(self, subtotal_in_cents: int) -> int:
        return round(subtotal_in_cents * 0.8)
```

## After in C#

```csharp
public interface IPricingPolicy
{
    int Apply(int subtotalInCents);
}

public sealed class StandardPricing : IPricingPolicy
{
    public int Apply(int subtotalInCents)
    {
        return subtotalInCents;
    }
}

public sealed class PremiumPricing : IPricingPolicy
{
    public int Apply(int subtotalInCents)
    {
        return (int)Math.Round(subtotalInCents * 0.8);
    }
}
```

## After in Ruby

```ruby
class StandardPricing
  def apply(subtotal_in_cents)
    subtotal_in_cents
  end
end

class PremiumPricing
  def apply(subtotal_in_cents)
    (subtotal_in_cents * 0.8).round
  end
end
```

## After in PHP

```php
interface PricingPolicy
{
    public function apply(int $subtotalInCents): int;
}

final class StandardPricing implements PricingPolicy
{
    public function apply(int $subtotalInCents): int
    {
        return $subtotalInCents;
    }
}

final class PremiumPricing implements PricingPolicy
{
    public function apply(int $subtotalInCents): int
    {
        return (int) round($subtotalInCents * 0.8);
    }
}
```

## What to Notice

- The variation becomes explicit.
- Adding a new pricing rule no longer requires editing a central conditional.
- The refactor is safest when protected by tests that captured the old behavior first.
- The same refactoring move works across mainstream object-oriented languages.
