# C# Examples

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

```csharp
public sealed class Money
{
    private readonly int cents;

    public Money(int cents)
    {
        if (cents < 0)
        {
            throw new ArgumentException("Money cannot be negative");
        }

        this.cents = cents;
    }

    public Money Add(Money other)
    {
        return new Money(cents + other.cents);
    }

    public Money MultiplyBy(int percent)
    {
        return new Money((int)Math.Round(cents * percent / 100.0));
    }

    public int Value()
    {
        return cents;
    }
}
```

## First-Class Collections

```csharp
public sealed class OrderLine
{
    private readonly Money subtotalAmount;

    public OrderLine(Money subtotalAmount)
    {
        this.subtotalAmount = subtotalAmount;
    }

    public Money Subtotal()
    {
        return subtotalAmount;
    }
}

public sealed class OrderLines
{
    private readonly IReadOnlyCollection<OrderLine> items;

    public OrderLines(IReadOnlyCollection<OrderLine> items)
    {
        this.items = items;
    }

    public Money Total()
    {
        var total = new Money(0);
        foreach (var item in items)
        {
            total = total.Add(item.Subtotal());
        }
        return total;
    }

    public bool IsEmpty()
    {
        return items.Count == 0;
    }
}
```

## Tell, Don't Ask

```csharp
public sealed class Address
{
    private readonly string countryCode;

    public Address(string countryCode)
    {
        this.countryCode = countryCode;
    }

    public bool IsDomestic()
    {
        return countryCode == "ES";
    }
}

public sealed class Shipment
{
    private readonly Address address;

    public Shipment(Address address)
    {
        this.address = address;
    }

    public int DispatchWindowInDays()
    {
        return address.IsDomestic() ? 2 : 5;
    }
}
```

## Role-Based Collaboration

```csharp
public interface ICurrencyFormatter
{
    string Format(Money amount);
}

public sealed class OrderSummary
{
    private readonly ICurrencyFormatter formatter;

    public OrderSummary(ICurrencyFormatter formatter)
    {
        this.formatter = formatter;
    }

    public string TotalLabel(OrderLines lines)
    {
        return formatter.Format(lines.Total());
    }
}
```

## Dependency Injection

```csharp
public interface IMailer
{
    void Send(string to, string body);
}

public sealed class Invoice
{
    private readonly string recipient;
    private readonly string bodyText;

    public Invoice(string recipient, string bodyText)
    {
        this.recipient = recipient;
        this.bodyText = bodyText;
    }

    public string RecipientEmail()
    {
        return recipient;
    }

    public string Body()
    {
        return bodyText;
    }
}

public sealed class InvoiceSender
{
    private readonly IMailer mailer;

    public InvoiceSender(IMailer mailer)
    {
        this.mailer = mailer;
    }

    public void Send(Invoice invoice)
    {
        mailer.Send(invoice.RecipientEmail(), invoice.Body());
    }
}
```

## Explicit Interfaces

```csharp
public interface IPaymentGateway
{
    void Charge(string customerId, Money amount);
}

public sealed class SubscriptionActivator
{
    private readonly IPaymentGateway paymentGateway;

    public SubscriptionActivator(IPaymentGateway paymentGateway)
    {
        this.paymentGateway = paymentGateway;
    }

    public void Activate(string customerId, Money fee)
    {
        paymentGateway.Charge(customerId, fee);
    }
}
```

## Duck Typing / Protocol-Style Roles

```csharp
public interface IStockSource
{
    int AvailableUnits();
}

public sealed class InventoryReport
{
    private readonly IStockSource source;

    public InventoryReport(IStockSource source)
    {
        this.source = source;
    }

    public bool IsAvailable()
    {
        return source.AvailableUnits() > 0;
    }
}

public sealed class WarehouseBin : IStockSource
{
    private readonly int units;

    public WarehouseBin(int units)
    {
        this.units = units;
    }

    public int AvailableUnits()
    {
        return units;
    }
}
```

## Composition over Inheritance

```csharp
public interface IDiscountPolicy
{
    Money Apply(Money total);
}

public interface ITaxPolicy
{
    Money Apply(Money total);
}

public sealed class CartPricing
{
    private readonly IDiscountPolicy discountPolicy;
    private readonly ITaxPolicy taxPolicy;

    public CartPricing(IDiscountPolicy discountPolicy, ITaxPolicy taxPolicy)
    {
        this.discountPolicy = discountPolicy;
        this.taxPolicy = taxPolicy;
    }

    public Money Total(Money subtotal)
    {
        return taxPolicy.Apply(discountPolicy.Apply(subtotal));
    }
}
```

## Message-Based Design

```csharp
public interface ISeatInventory
{
    void Reserve(int seatCount);
}

public interface IPaymentService
{
    void Charge(Money amount);
}

public sealed class Booking
{
    private readonly int seats;
    private readonly Money amount;
    private readonly ISeatInventory inventory;
    private readonly IPaymentService payments;

    public Booking(int seats, Money amount, ISeatInventory inventory, IPaymentService payments)
    {
        this.seats = seats;
        this.amount = amount;
        this.inventory = inventory;
        this.payments = payments;
    }

    public void Confirm()
    {
        inventory.Reserve(seats);
        payments.Charge(amount);
    }
}
```

## Law of Demeter Violation and Fix

### Before

```csharp
public sealed class CustomerRecord
{
    private readonly Address address;

    public CustomerRecord(Address address)
    {
        this.address = address;
    }

    public Address ShippingAddress()
    {
        return address;
    }
}

public sealed class Order
{
    private readonly CustomerRecord customer;

    public Order(CustomerRecord customer)
    {
        this.customer = customer;
    }

    public CustomerRecord CustomerRecord()
    {
        return customer;
    }
}

var domestic = order.CustomerRecord().ShippingAddress().IsDomestic();
```

### After

```csharp
public sealed class Customer
{
    private readonly Address address;

    public Customer(Address address)
    {
        this.address = address;
    }

    public bool ShipsDomestically()
    {
        return address.IsDomestic();
    }
}

public sealed class PurchaseOrder
{
    private readonly Customer customer;

    public PurchaseOrder(Customer customer)
    {
        this.customer = customer;
    }

    public bool ShipsDomestically()
    {
        return customer.ShipsDomestically();
    }
}

var domestic = order.ShipsDomestically();
```

## Immutable Objects

```csharp
using System.Collections.Generic;

public sealed class Rooms
{
    private readonly IReadOnlyCollection<string> items;

    public Rooms(IReadOnlyCollection<string> items)
    {
        this.items = items;
    }

    public Rooms Add(string room)
    {
        var copy = new List<string>(items) { room };
        return new Rooms(copy);
    }

    public int Count()
    {
        return items.Count;
    }
}
```

## Null Object

```csharp
public interface ILogger
{
    void Info(string message);
}

public sealed class NullLogger : ILogger
{
    public void Info(string message)
    {
    }
}
```

## Anemic versus Rich Model

### Anemic

```csharp
public sealed class ScoreData
{
    public int Value { get; set; }

    public ScoreData(int value)
    {
        Value = value;
    }
}

public sealed class ScoreService
{
    public void Increase(ScoreData score, int points)
    {
        score.Value = score.Value + points;
    }
}
```

### Rich

```csharp
public sealed class Score
{
    private readonly int value;

    public Score(int value)
    {
        this.value = value;
    }

    public Score Increase(int points)
    {
        return new Score(value + points);
    }

    public int Value()
    {
        return value;
    }
}
```

## SOLID — Single Responsibility Violation and Fix

### Before

```csharp
public sealed class Report
{
    private readonly string title;
    private readonly string body;

    public Report(string title, string body)
    {
        this.title = title;
        this.body = body;
    }

    public string Title()
    {
        return title;
    }

    public string Body()
    {
        return body;
    }

    public void Save(DbConnection connection)
    {
        // mixes persistence concern into the data object
        var cmd = connection.CreateCommand();
        cmd.CommandText = "INSERT INTO reports (title, body) VALUES (@title, @body)";
        cmd.ExecuteNonQuery();
    }
}
```

### After

```csharp
public sealed class Report
{
    private readonly string title;
    private readonly string body;

    public Report(string title, string body)
    {
        this.title = title;
        this.body = body;
    }

    public string Title()
    {
        return title;
    }

    public string Body()
    {
        return body;
    }
}

public sealed class ReportRepository
{
    private readonly DbConnection connection;

    public ReportRepository(DbConnection connection)
    {
        this.connection = connection;
    }

    public void Save(Report report)
    {
        var cmd = connection.CreateCommand();
        cmd.CommandText = "INSERT INTO reports (title, body) VALUES (@title, @body)";
        cmd.ExecuteNonQuery();
    }
}
```

## Object Calisthenics — Wrap Primitive

```csharp
public sealed class Percentage
{
    private readonly int value;

    public Percentage(int value)
    {
        if (value < 0 || value > 100)
        {
            throw new ArgumentOutOfRangeException(nameof(value), "Percentage must be between 0 and 100");
        }

        this.value = value;
    }

    public int Of(int amount)
    {
        return (int)Math.Round(amount * value / 100.0);
    }
}

public sealed class Price
{
    private readonly int cents;

    public Price(int cents)
    {
        if (cents < 0)
        {
            throw new ArgumentException("Price cannot be negative");
        }

        this.cents = cents;
    }

    public Price ApplyDiscount(Percentage discount)
    {
        return new Price(cents - discount.Of(cents));
    }

    public int InCents()
    {
        return cents;
    }
}
```

## Object Calisthenics — No Else Rule

### Before

```csharp
public sealed class ShippingCalculator
{
    public Money ShippingCost(Order order)
    {
        if (order.IsPremiumMember())
        {
            return new Money(0);
        }
        else
        {
            if (order.TotalValue().Value() > 10000)
            {
                return new Money(0);
            }
            else
            {
                if (order.ShipsDomestically())
                {
                    return new Money(500);
                }
                else
                {
                    return new Money(1500);
                }
            }
        }
    }
}
```

### After

```csharp
public sealed class ShippingCalculator
{
    public Money ShippingCost(Order order)
    {
        if (order.IsPremiumMember())
        {
            return new Money(0);
        }

        if (order.TotalValue().Value() > 10000)
        {
            return new Money(0);
        }

        if (order.ShipsDomestically())
        {
            return new Money(500);
        }

        return new Money(1500);
    }
}
```

## Dependency Direction

### Before

```csharp
public sealed class InvoiceExporter
{
    public void Export(string path, string content)
    {
        // depends directly on a concrete infrastructure class
        var fileSystem = new FileSystem();
        fileSystem.WriteAllText(path, content);
    }
}
```

### After

```csharp
public interface IDocumentStorage
{
    void Write(string path, string content);
}

public sealed class InvoiceExporter
{
    private readonly IDocumentStorage storage;

    public InvoiceExporter(IDocumentStorage storage)
    {
        this.storage = storage;
    }

    public void Export(string path, string content)
    {
        storage.Write(path, content);
    }
}

public sealed class FileDocumentStorage : IDocumentStorage
{
    public void Write(string path, string content)
    {
        File.WriteAllText(path, content);
    }
}
```

## Composed Method

### Before

```csharp
public sealed class RegistrationService
{
    public void Register(string email, string password)
    {
        if (string.IsNullOrWhiteSpace(email) || !email.Contains('@'))
        {
            throw new ArgumentException("Invalid email");
        }

        if (password.Length < 8)
        {
            throw new ArgumentException("Password too short");
        }

        var hash = BCrypt.Net.BCrypt.HashPassword(password);

        var user = new User(email, hash);
        userRepository.Save(user);

        mailer.Send(email, "Welcome! Your account is ready.");
    }
}
```

### After

```csharp
public sealed class RegistrationService
{
    private readonly IUserRepository userRepository;
    private readonly IMailer mailer;

    public RegistrationService(IUserRepository userRepository, IMailer mailer)
    {
        this.userRepository = userRepository;
        this.mailer = mailer;
    }

    public void Register(string email, string password)
    {
        Validate(email, password);
        var user = BuildUser(email, password);
        Persist(user);
        Welcome(user);
    }

    private void Validate(string email, string password)
    {
        if (string.IsNullOrWhiteSpace(email) || !email.Contains('@'))
        {
            throw new ArgumentException("Invalid email");
        }

        if (password.Length < 8)
        {
            throw new ArgumentException("Password too short");
        }
    }

    private User BuildUser(string email, string password)
    {
        var hash = BCrypt.Net.BCrypt.HashPassword(password);
        return new User(email, hash);
    }

    private void Persist(User user)
    {
        userRepository.Save(user);
    }

    private void Welcome(User user)
    {
        mailer.Send(user.Email(), "Welcome! Your account is ready.");
    }
}
```

## What to Notice

- Rich models and clear object responsibilities help keep knowledge close to the concept.
- C# makes explicit interfaces, injected collaborators, and small role objects easy to model.
- Protocol-style roles appear as narrow interfaces instead of broad inheritance trees.
- Composition and message passing keep dependencies understandable.
- Wrapping primitives and splitting responsibilities keep each class focused on one reason to change.
