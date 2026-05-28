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

## SOLID — Open/Closed Principle

### Before

```java
public final class ShippingCalculator {
    public int calculate(Order order) {
        if (order.type().equals("standard")) {
            return 5;
        } else if (order.type().equals("express")) {
            return 15;
        } else if (order.type().equals("overnight")) {
            return 25;
        }
        throw new IllegalArgumentException("Unknown order type");
    }
}
```

### After

```java
public interface ShippingPolicy {
    int shippingCost(Order order);
}

public final class StandardShipping implements ShippingPolicy {
    public int shippingCost(Order order) { return 5; }
}

public final class ExpressShipping implements ShippingPolicy {
    public int shippingCost(Order order) { return 15; }
}

public final class OvernightShipping implements ShippingPolicy {
    public int shippingCost(Order order) { return 25; }
}

public final class ShippingCalculator {
    private final ShippingPolicy policy;

    public ShippingCalculator(ShippingPolicy policy) {
        this.policy = policy;
    }

    public int calculate(Order order) {
        return policy.shippingCost(order);
    }
}
// New shipping types are added by implementing ShippingPolicy — the calculator is never modified.
```

## SOLID — Liskov Substitution Principle

### Before

```java
// LSP violation: subtype throws where the parent promises it won't.
public class ReadOnlyCollection extends java.util.ArrayList<String> {
    @Override
    public boolean add(String element) {
        throw new UnsupportedOperationException("Collection is read-only");
    }
}
```

### After

```java
// Independent classes — no inheritance contract is broken.
public final class MutableCollection {
    private final java.util.List<String> items = new java.util.ArrayList<>();

    public void add(String item) {
        items.add(item);
    }

    public java.util.List<String> all() {
        return java.util.Collections.unmodifiableList(items);
    }
}

public final class ReadOnlyCollection {
    private final java.util.List<String> items;

    public ReadOnlyCollection(java.util.List<String> items) {
        this.items = java.util.List.copyOf(items);
    }

    public java.util.List<String> all() {
        return items;
    }
}
```

## SOLID — Interface Segregation Principle

### Before

```java
// Fat interface forces RobotWorker to throw on methods it cannot support.
public interface Worker {
    void work();
    void eat();
    void sleep();
}

public final class RobotWorker implements Worker {
    public void work() { /* performs task */ }
    public void eat() { throw new UnsupportedOperationException("Robots don't eat"); }
    public void sleep() { throw new UnsupportedOperationException("Robots don't sleep"); }
}
```

### After

```java
public interface Workable {
    void work();
}

public interface Eatable {
    void eat();
}

public interface Sleepable {
    void sleep();
}

public final class HumanWorker implements Workable, Eatable, Sleepable {
    public void work() { /* performs task */ }
    public void eat() { /* has lunch */ }
    public void sleep() { /* rests */ }
}

public final class RobotWorker implements Workable {
    public void work() { /* performs task */ }
}
```

## SOLID — Dependency Inversion Principle

### Before

```java
public final class OrderProcessor {
    private final PostgresDatabase database = new PostgresDatabase(); // hardcoded low-level detail

    public void process(Order order) {
        database.insert("orders", order);
    }
}
```

### After

```java
// Interface owned by the high-level module, not the low-level one.
public interface OrderStore {
    void save(Order order);
}

public final class PostgresOrderStore implements OrderStore {
    public void save(Order order) {
        // writes to Postgres
    }
}

public final class OrderProcessor {
    private final OrderStore store;

    public OrderProcessor(OrderStore store) {
        this.store = store;
    }

    public void process(Order order) {
        store.save(order);
    }
}
```

## Object Calisthenics — One Level of Indentation

### Before

```java
public String generateReport(java.util.List<Order> orders) {
    StringBuilder report = new StringBuilder();
    for (Order order : orders) {
        if (order.isComplete()) {
            for (OrderLine line : order.lines()) {
                if (line.subtotal().value() > 10000) {
                    report.append(line.name()).append(": ").append(line.subtotal().value()).append("\n");
                }
            }
        }
    }
    return report.toString();
}
```

### After

```java
public String generateReport(java.util.List<Order> orders) {
    return orders.stream()
        .filter(this::isComplete)
        .flatMap(order -> expensiveItems(order).stream())
        .map(this::formatItem)
        .collect(java.util.stream.Collectors.joining("\n"));
}

private boolean isComplete(Order order) {
    return order.isComplete();
}

private java.util.List<OrderLine> expensiveItems(Order order) {
    return order.lines().stream()
        .filter(line -> line.subtotal().value() > 10000)
        .collect(java.util.stream.Collectors.toList());
}

private String formatItem(OrderLine line) {
    return line.name() + ": " + line.subtotal().value();
}
```

## Object Calisthenics — No Getters/Setters

### Before

```java
public final class Rectangle {
    private final int width;
    private final int height;

    public Rectangle(int width, int height) {
        this.width = width;
        this.height = height;
    }

    public int getWidth() { return width; }
    public int getHeight() { return height; }
}

// Callers compute behaviour externally — knowledge leaks out of the object.
int area = rect.getWidth() * rect.getHeight();
int perimeter = 2 * (rect.getWidth() + rect.getHeight());
boolean square = rect.getWidth() == rect.getHeight();
```

### After

```java
public final class Rectangle {
    private final int width;
    private final int height;

    public Rectangle(int width, int height) {
        this.width = width;
        this.height = height;
    }

    public int area() {
        return width * height;
    }

    public int perimeter() {
        return 2 * (width + height);
    }

    public boolean isSquare() {
        return width == height;
    }
}
```

## Object Calisthenics — Don't Abbreviate

### Before

```java
public final class OrdMgr {
    public int calc(Order o) {
        int t = 0;
        for (OrderLine l : o.lines()) {
            t += l.subtotal().value();
        }
        return t;
    }

    public void proc(Order o) {
        int t = calc(o);
        // process with total t
    }
}
```

### After

```java
public final class OrderManager {
    public int calculateTotal(Order order) {
        return order.lines().stream()
            .mapToInt(line -> line.subtotal().value())
            .sum();
    }

    public void processOrder(Order order) {
        int total = calculateTotal(order);
        // process with total
    }
}
```

## Explaining Message

### Before

```java
public final class Subscription {
    private final long startedAtMillis;
    private final int durationDays;

    public Subscription(long startedAtMillis, int durationDays) {
        this.startedAtMillis = startedAtMillis;
        this.durationDays = durationDays;
    }

    public boolean isExpired() {
        return System.currentTimeMillis() > startedAtMillis + (long) durationDays * 24 * 60 * 60 * 1000;
    }
}
```

### After

```java
public final class Subscription {
    private final long startedAtMillis;
    private final int durationDays;

    public Subscription(long startedAtMillis, int durationDays) {
        this.startedAtMillis = startedAtMillis;
        this.durationDays = durationDays;
    }

    public boolean isExpired() {
        return System.currentTimeMillis() > expirationDate();
    }

    private long expirationDate() {
        return startedAtMillis + (long) durationDays * 24 * 60 * 60 * 1000;
    }
}
```

## What to Notice

- Rich models and clear object responsibilities help keep knowledge close to the concept.
- Java uses small interfaces to model both explicit contracts and protocol-style roles.
- Value objects, collection objects, and narrow collaborators keep responsibilities focused.
- Composition and message passing reduce the need for brittle inheritance trees.
- Wrapping primitives and splitting responsibilities keep each class focused on one reason to change.
- SOLID principles, Object Calisthenics rules, and extracted explaining messages each reduce a different kind of coupling or noise.
