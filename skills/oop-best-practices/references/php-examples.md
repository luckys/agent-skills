# PHP Examples

These examples cover the same core concepts as the other language-specific example files.

## Concepts Covered

- Value Objects and Invariants
- First-Class Collections
- Tell, Don't Ask
- Role-Based Collaboration
- Dependency Injection
- Explicit Interfaces
- Duck Typing / Protocol-Style Roles
- Composition over Inheritance
- Message-Based Design
- Law of Demeter Violation and Fix
- Immutable Objects
- Null Object
- Anemic versus Rich Model

## Value Objects and Invariants

```php
final class Money
{
    public function __construct(private int $cents)
    {
        if ($cents < 0) {
            throw new InvalidArgumentException('Money cannot be negative');
        }
    }

    public function add(Money $other): Money
    {
        return new Money($this->cents + $other->value());
    }

    public function multiplyBy(int $percent): Money
    {
        return new Money((int) round($this->cents * $percent / 100));
    }

    public function value(): int
    {
        return $this->cents;
    }
}
```

## First-Class Collections

```php
final class OrderLine
{
    public function __construct(private Money $subtotalAmount)
    {
    }

    public function subtotal(): Money
    {
        return $this->subtotalAmount;
    }
}

final class OrderLines
{
    public function __construct(private array $items)
    {
    }

    public function total(): Money
    {
        $total = new Money(0);
        foreach ($this->items as $item) {
            $total = $total->add($item->subtotal());
        }
        return $total;
    }

    public function isEmpty(): bool
    {
        return count($this->items) === 0;
    }
}
```

## Tell, Don't Ask

```php
final class Address
{
    public function __construct(private string $countryCode)
    {
    }

    public function isDomestic(): bool
    {
        return $this->countryCode === 'ES';
    }
}

final class Shipment
{
    public function __construct(private Address $address)
    {
    }

    public function dispatchWindowInDays(): int
    {
        return $this->address->isDomestic() ? 2 : 5;
    }
}
```

## Role-Based Collaboration

```php
interface CurrencyFormatter
{
    public function format(Money $amount): string;
}

final class OrderSummary
{
    public function __construct(private CurrencyFormatter $formatter)
    {
    }

    public function totalLabel(OrderLines $lines): string
    {
        return $this->formatter->format($lines->total());
    }
}
```

## Dependency Injection

```php
interface Mailer
{
    public function send(string $to, string $body): void;
}

final class Invoice
{
    public function __construct(
        private string $recipient,
        private string $bodyText,
    ) {
    }

    public function recipientEmail(): string
    {
        return $this->recipient;
    }

    public function body(): string
    {
        return $this->bodyText;
    }
}

final class InvoiceSender
{
    public function __construct(private Mailer $mailer)
    {
    }

    public function send(Invoice $invoice): void
    {
        $this->mailer->send($invoice->recipientEmail(), $invoice->body());
    }
}
```

## Explicit Interfaces

```php
interface PaymentGateway
{
    public function charge(string $customerId, Money $amount): void;
}

final class SubscriptionActivator
{
    public function __construct(private PaymentGateway $paymentGateway)
    {
    }

    public function activate(string $customerId, Money $fee): void
    {
        $this->paymentGateway->charge($customerId, $fee);
    }
}
```

## Duck Typing / Protocol-Style Roles

```php
interface StockSource
{
    public function availableUnits(): int;
}

final class InventoryReport
{
    public function __construct(private StockSource $source)
    {
    }

    public function isAvailable(): bool
    {
        return $this->source->availableUnits() > 0;
    }
}

final class WarehouseBin implements StockSource
{
    public function __construct(private int $units)
    {
    }

    public function availableUnits(): int
    {
        return $this->units;
    }
}
```

## Composition over Inheritance

```php
interface DiscountPolicy
{
    public function apply(Money $total): Money;
}

interface TaxPolicy
{
    public function apply(Money $total): Money;
}

final class CartPricing
{
    public function __construct(
        private DiscountPolicy $discountPolicy,
        private TaxPolicy $taxPolicy,
    ) {
    }

    public function total(Money $subtotal): Money
    {
        $discounted = $this->discountPolicy->apply($subtotal);
        return $this->taxPolicy->apply($discounted);
    }
}
```

## Message-Based Design

```php
interface SeatInventory
{
    public function reserve(int $seatCount): void;
}

interface PaymentService
{
    public function charge(Money $amount): void;
}

final class Booking
{
    public function __construct(
        private int $seats,
        private Money $amount,
        private SeatInventory $inventory,
        private PaymentService $payments,
    ) {
    }

    public function confirm(): void
    {
        $this->inventory->reserve($this->seats);
        $this->payments->charge($this->amount);
    }
}
```

## Law of Demeter Violation and Fix

### Before

```php
final class CustomerRecord
{
    public function __construct(private Address $address)
    {
    }

    public function shippingAddress(): Address
    {
        return $this->address;
    }
}

final class Order
{
    public function __construct(private CustomerRecord $customer)
    {
    }

    public function customerRecord(): CustomerRecord
    {
        return $this->customer;
    }
}

$domestic = $order->customerRecord()->shippingAddress()->isDomestic();
```

### After

```php
final class Customer
{
    public function __construct(private Address $address)
    {
    }

    public function shipsDomestically(): bool
    {
        return $this->address->isDomestic();
    }
}

final class PurchaseOrder
{
    public function __construct(private Customer $customer)
    {
    }

    public function shipsDomestically(): bool
    {
        return $this->customer->shipsDomestically();
    }
}

$domestic = $order->shipsDomestically();
```

## Immutable Objects

```php
final class Rooms
{
    public function __construct(private array $items)
    {
    }

    public function add(string $room): Rooms
    {
        return new Rooms([...$this->items, $room]);
    }

    public function count(): int
    {
        return count($this->items);
    }
}
```

## Null Object

```php
interface Logger
{
    public function info(string $message): void;
}

final class NullLogger implements Logger
{
    public function info(string $message): void
    {
    }
}
```

## Anemic versus Rich Model

### Anemic

```php
final class ScoreData
{
    public function __construct(public int $value)
    {
    }
}

function increaseScore(ScoreData $score, int $points): void
{
    $score->value = $score->value + $points;
}
```

### Rich

```php
final class Score
{
    public function __construct(private int $value)
    {
    }

    public function increase(int $points): Score
    {
        return new Score($this->value + $points);
    }

    public function value(): int
    {
        return $this->value;
    }
}
```

## SOLID — Single Responsibility Violation and Fix

### Before

```php
final class Report
{
    public function __construct(
        private readonly string $title,
        private readonly string $content,
    ) {
    }

    public function title(): string
    {
        return $this->title;
    }

    public function content(): string
    {
        return $this->content;
    }

    public function save(\PDO $pdo): void
    {
        $stmt = $pdo->prepare('INSERT INTO reports (title, content) VALUES (?, ?)');
        $stmt->execute([$this->title, $this->content]);
    }
}
```

### After

```php
final class Report
{
    public function __construct(
        private readonly string $title,
        private readonly string $content,
    ) {
    }

    public function title(): string
    {
        return $this->title;
    }

    public function content(): string
    {
        return $this->content;
    }
}

final class ReportRepository
{
    public function __construct(private readonly \PDO $pdo)
    {
    }

    public function save(Report $report): void
    {
        $stmt = $this->pdo->prepare('INSERT INTO reports (title, content) VALUES (?, ?)');
        $stmt->execute([$report->title(), $report->content()]);
    }
}
```

## Object Calisthenics — Wrap Primitive

```php
final class Percentage
{
    public function __construct(private readonly int $value)
    {
        if ($value < 0 || $value > 100) {
            throw new \InvalidArgumentException(
                "Percentage must be between 0 and 100, got {$value}."
            );
        }
    }

    public function of(int $amount): int
    {
        return (int) round($amount * $this->value / 100);
    }

    public function value(): int
    {
        return $this->value;
    }
}

final class Price
{
    public function __construct(private readonly int $cents)
    {
        if ($cents < 0) {
            throw new \InvalidArgumentException('Price cannot be negative.');
        }
    }

    public function applyDiscount(Percentage $discount): Price
    {
        return new Price($this->cents - $discount->of($this->cents));
    }

    public function cents(): int
    {
        return $this->cents;
    }
}
```

## Object Calisthenics — No Else Rule

### Before

```php
final class ShippingCalculator
{
    public function shippingCost(Order $order): int
    {
        if ($order->isPremiumMember()) {
            return 0;
        } else {
            if ($order->totalCents() >= 5000) {
                return 0;
            } else {
                if ($order->isInternational()) {
                    return 1500;
                } else {
                    return 500;
                }
            }
        }
    }
}
```

### After

```php
final class ShippingCalculator
{
    public function shippingCost(Order $order): int
    {
        if ($order->isPremiumMember()) {
            return 0;
        }

        if ($order->totalCents() >= 5000) {
            return 0;
        }

        if ($order->isInternational()) {
            return 1500;
        }

        return 500;
    }
}
```

## Dependency Direction

### Before

```php
final class InvoiceExporter
{
    public function export(string $path, string $content): void
    {
        $fs = new FileSystem();
        $fs->write($path, $content);
    }
}

final class FileSystem
{
    public function write(string $path, string $content): void
    {
        file_put_contents($path, $content);
    }
}
```

### After

```php
interface DocumentStorage
{
    public function write(string $path, string $content): void;
}

final class FileSystemStorage implements DocumentStorage
{
    public function write(string $path, string $content): void
    {
        file_put_contents($path, $content);
    }
}

final class InvoiceExporter
{
    public function __construct(private readonly DocumentStorage $storage)
    {
    }

    public function export(string $path, string $content): void
    {
        $this->storage->write($path, $content);
    }
}
```

## Composed Method

### Before

```php
final class RegistrationService
{
    public function register(string $email, string $password): void
    {
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throw new \InvalidArgumentException('Invalid email address.');
        }
        if (strlen($password) < 8) {
            throw new \DomainException('Password must be at least 8 characters.');
        }

        $hash = password_hash($password, PASSWORD_BCRYPT);
        $user = ['email' => $email, $hash => $hash, 'created_at' => date('Y-m-d H:i:s')];

        $this->pdo->prepare('INSERT INTO users (email, password_hash, created_at) VALUES (?,?,?)')
            ->execute([$user['email'], $user['hash'], $user['created_at']]);

        mail($email, 'Welcome!', 'Thanks for signing up.');
    }
}
```

### After

```php
final class RegistrationService
{
    public function __construct(
        private readonly \PDO $pdo,
        private readonly Mailer $mailer,
    ) {
    }

    public function register(string $email, string $password): void
    {
        $this->validate($email, $password);
        $user = $this->buildUser($email, $password);
        $this->persist($user);
        $this->welcome($email);
    }

    private function validate(string $email, string $password): void
    {
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throw new \InvalidArgumentException('Invalid email address.');
        }
        if (strlen($password) < 8) {
            throw new \DomainException('Password must be at least 8 characters.');
        }
    }

    private function buildUser(string $email, string $password): array
    {
        return [
            'email'         => $email,
            'password_hash' => password_hash($password, PASSWORD_BCRYPT),
            'created_at'    => date('Y-m-d H:i:s'),
        ];
    }

    private function persist(array $user): void
    {
        $this->pdo->prepare('INSERT INTO users (email, password_hash, created_at) VALUES (?,?,?)')
            ->execute([$user['email'], $user['password_hash'], $user['created_at']]);
    }

    private function welcome(string $email): void
    {
        $this->mailer->send($email, 'Welcome!', 'Thanks for signing up.');
    }
}
```

## What to Notice

- Rich models and clear object responsibilities help keep knowledge close to the concept.
- PHP can model the same object boundaries with final classes and small interfaces.
- Explicit contracts, injected collaborators, and composition help PHP stay object-oriented instead of procedural.
- Delegating through meaningful messages reduces train-wreck navigation.
- Wrapping primitives and splitting responsibilities keep each class focused on one reason to change.
