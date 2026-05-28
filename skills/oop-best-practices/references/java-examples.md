# Java Examples

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

```java
public final class Money {
    private final int cents;

    public Money(int cents) {
        if (cents < 0) {
            throw new IllegalArgumentException("Money cannot be negative");
        }
        this.cents = cents;
    }

    public Money add(Money other) {
        return new Money(this.cents + other.cents);
    }

    public Money multiplyBy(int percent) {
        return new Money(Math.round(this.cents * percent / 100.0f));
    }

    public int value() {
        return cents;
    }
}
```

## First-Class Collections

```java
import java.util.List;

public final class OrderLine {
    private final Money subtotalAmount;

    public OrderLine(Money subtotalAmount) {
        this.subtotalAmount = subtotalAmount;
    }

    public Money subtotal() {
        return subtotalAmount;
    }
}

public final class OrderLines {
    private final List<OrderLine> items;

    public OrderLines(List<OrderLine> items) {
        this.items = List.copyOf(items);
    }

    public Money total() {
        Money total = new Money(0);
        for (OrderLine item : items) {
            total = total.add(item.subtotal());
        }
        return total;
    }

    public boolean isEmpty() {
        return items.isEmpty();
    }
}
```

## Tell, Don't Ask

```java
public final class Address {
    private final String countryCode;

    public Address(String countryCode) {
        this.countryCode = countryCode;
    }

    public boolean isDomestic() {
        return "ES".equals(countryCode);
    }
}

public final class Shipment {
    private final Address address;

    public Shipment(Address address) {
        this.address = address;
    }

    public int dispatchWindowInDays() {
        return address.isDomestic() ? 2 : 5;
    }
}
```

## Role-Based Collaboration

```java
public interface CurrencyFormatter {
    String format(Money amount);
}

public final class OrderSummary {
    private final CurrencyFormatter formatter;

    public OrderSummary(CurrencyFormatter formatter) {
        this.formatter = formatter;
    }

    public String totalLabel(OrderLines lines) {
        return formatter.format(lines.total());
    }
}
```

## Dependency Injection

```java
public interface Mailer {
    void send(String to, String body);
}

public final class Invoice {
    private final String recipient;
    private final String bodyText;

    public Invoice(String recipient, String bodyText) {
        this.recipient = recipient;
        this.bodyText = bodyText;
    }

    public String recipientEmail() {
        return recipient;
    }

    public String body() {
        return bodyText;
    }
}

public final class InvoiceSender {
    private final Mailer mailer;

    public InvoiceSender(Mailer mailer) {
        this.mailer = mailer;
    }

    public void send(Invoice invoice) {
        mailer.send(invoice.recipientEmail(), invoice.body());
    }
}
```

## Explicit Interfaces

```java
public interface PaymentGateway {
    void charge(String customerId, Money amount);
}

public final class SubscriptionActivator {
    private final PaymentGateway paymentGateway;

    public SubscriptionActivator(PaymentGateway paymentGateway) {
        this.paymentGateway = paymentGateway;
    }

    public void activate(String customerId, Money fee) {
        paymentGateway.charge(customerId, fee);
    }
}
```

## Duck Typing / Protocol-Style Roles

```java
public interface StockSource {
    int availableUnits();
}

public final class InventoryReport {
    private final StockSource source;

    public InventoryReport(StockSource source) {
        this.source = source;
    }

    public boolean isAvailable() {
        return source.availableUnits() > 0;
    }
}

public final class WarehouseBin implements StockSource {
    private final int units;

    public WarehouseBin(int units) {
        this.units = units;
    }

    public int availableUnits() {
        return units;
    }
}
```

## Composition over Inheritance

```java
public interface DiscountPolicy {
    Money apply(Money total);
}

public interface TaxPolicy {
    Money apply(Money total);
}

public final class CartPricing {
    private final DiscountPolicy discountPolicy;
    private final TaxPolicy taxPolicy;

    public CartPricing(DiscountPolicy discountPolicy, TaxPolicy taxPolicy) {
        this.discountPolicy = discountPolicy;
        this.taxPolicy = taxPolicy;
    }

    public Money total(Money subtotal) {
        return taxPolicy.apply(discountPolicy.apply(subtotal));
    }
}
```

## Message-Based Design

```java
public interface SeatInventory {
    void reserve(int seatCount);
}

public interface PaymentService {
    void charge(Money amount);
}

public final class Booking {
    private final int seats;
    private final Money amount;
    private final SeatInventory inventory;
    private final PaymentService payments;

    public Booking(int seats, Money amount, SeatInventory inventory, PaymentService payments) {
        this.seats = seats;
        this.amount = amount;
        this.inventory = inventory;
        this.payments = payments;
    }

    public void confirm() {
        inventory.reserve(seats);
        payments.charge(amount);
    }
}
```

## Law of Demeter Violation and Fix

### Before

```java
public final class CustomerRecord {
    private final Address address;

    public CustomerRecord(Address address) {
        this.address = address;
    }

    public Address shippingAddress() {
        return address;
    }
}

public final class Order {
    private final CustomerRecord customer;

    public Order(CustomerRecord customer) {
        this.customer = customer;
    }

    public CustomerRecord customerRecord() {
        return customer;
    }
}

boolean domestic = order.customerRecord().shippingAddress().isDomestic();
```

### After

```java
public final class Customer {
    private final Address address;

    public Customer(Address address) {
        this.address = address;
    }

    public boolean shipsDomestically() {
        return address.isDomestic();
    }
}

public final class PurchaseOrder {
    private final Customer customer;

    public PurchaseOrder(Customer customer) {
        this.customer = customer;
    }

    public boolean shipsDomestically() {
        return customer.shipsDomestically();
    }
}

boolean domestic = order.shipsDomestically();
```

## Immutable Objects

```java
import java.util.ArrayList;
import java.util.List;

public final class Rooms {
    private final List<String> items;

    public Rooms(List<String> items) {
        this.items = List.copyOf(items);
    }

    public Rooms add(String room) {
        List<String> copy = new ArrayList<>(items);
        copy.add(room);
        return new Rooms(copy);
    }

    public int count() {
        return items.size();
    }
}
```

## Null Object

```java
public interface Logger {
    void info(String message);
}

public final class NullLogger implements Logger {
    public void info(String message) {
    }
}
```

## Anemic versus Rich Model

### Anemic

```java
public final class ScoreData {
    public int value;

    public ScoreData(int value) {
        this.value = value;
    }
}

public final class ScoreService {
    public void increase(ScoreData score, int points) {
        score.value = score.value + points;
    }
}
```

### Rich

```java
public final class Score {
    private final int value;

    public Score(int value) {
        this.value = value;
    }

    public Score increase(int points) {
        return new Score(value + points);
    }

    public int value() {
        return value;
    }
}
```

## SOLID — Single Responsibility Violation and Fix

### Before

```java
public final class Report {
    private final String title;
    private final String content;

    public Report(String title, String content) {
        this.title = title;
        this.content = content;
    }

    public String title() {
        return title;
    }

    public void save() {
        // writing to database — second unrelated responsibility
        database.insert("reports", title, content);
    }
}
```

### After

```java
public final class Report {
    private final String title;
    private final String content;

    public Report(String title, String content) {
        this.title = title;
        this.content = content;
    }

    public String title() {
        return title;
    }

    public String body() {
        return content;
    }
}

public final class ReportRepository {
    public void save(Report report) {
        database.insert("reports", report.title(), report.body());
    }
}
```

## Object Calisthenics — Wrap Primitive

### Before

```java
public int applyDiscount(int priceInCents, int discountPercent) {
    if (discountPercent < 0 || discountPercent > 100) {
        throw new IllegalArgumentException("Invalid discount");
    }
    return Math.round(priceInCents * (1 - discountPercent / 100.0f));
}
```

### After

```java
public final class Percentage {
    private final int value;

    public Percentage(int value) {
        if (value < 0 || value > 100) {
            throw new IllegalArgumentException("Percentage must be between 0 and 100");
        }
        this.value = value;
    }

    public int of(int amount) {
        return Math.round(amount * (value / 100.0f));
    }
}

public final class Price {
    private final int cents;

    public Price(int cents) {
        this.cents = cents;
    }

    public Price applyDiscount(Percentage discount) {
        return new Price(cents - discount.of(cents));
    }

    public int value() {
        return cents;
    }
}
```

## Object Calisthenics — No Else Rule

### Before

```java
public int shippingCost(Order order) {
    if (order.isExpress()) {
        return 15;
    } else {
        if (order.totalWeight() > 10) {
            return 8;
        } else {
            return 3;
        }
    }
}
```

### After

```java
public int shippingCost(Order order) {
    if (order.isExpress()) return 15;
    if (order.totalWeight() > 10) return 8;
    return 3;
}
```

## Dependency Direction

### Before

```java
public final class InvoiceExporter {
    public void export(Invoice invoice) {
        FileSystem fs = new FileSystem();
        fs.write("invoices/" + invoice.id() + ".txt", invoice.body());
    }
}
```

### After

```java
public interface DocumentStorage {
    void write(String path, String content);
}

public final class InvoiceExporter {
    private final DocumentStorage storage;

    public InvoiceExporter(DocumentStorage storage) {
        this.storage = storage;
    }

    public void export(Invoice invoice) {
        storage.write("invoices/" + invoice.id() + ".txt", invoice.body());
    }
}
```

## Composed Method

### Before

```java
public final class RegistrationService {
    public void register(String email, String password) {
        if (!email.contains("@")) throw new IllegalArgumentException("Invalid email");
        if (password.length() < 8) throw new IllegalArgumentException("Password too short");
        String hashed = hashPassword(password);
        userRepository.save(new User(email, hashed));
        mailer.send(email, "Welcome!");
    }
}
```

### After

```java
public final class RegistrationService {
    public void register(String email, String password) {
        validate(email, password);
        User user = buildUser(email, password);
        persist(user);
        welcome(user);
    }

    private void validate(String email, String password) {
        if (!email.contains("@")) throw new IllegalArgumentException("Invalid email");
        if (password.length() < 8) throw new IllegalArgumentException("Password too short");
    }

    private User buildUser(String email, String password) {
        return new User(email, hashPassword(password));
    }

    private void persist(User user) {
        userRepository.save(user);
    }

    private void welcome(User user) {
        mailer.send(user.email(), "Welcome!");
    }
}
```

## What to Notice

- Rich models and clear object responsibilities help keep knowledge close to the concept.
- Java uses small interfaces to model both explicit contracts and protocol-style roles.
- Value objects, collection objects, and narrow collaborators keep responsibilities focused.
- Composition and message passing reduce the need for brittle inheritance trees.
- Wrapping primitives and splitting responsibilities keep each class focused on one reason to change.
