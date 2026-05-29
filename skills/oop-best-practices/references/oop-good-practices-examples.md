# OOP Good Practices — CodelyTV Examples

Source: CodelyTV `object_oriented_programming-good_practices-course`

Three core practices covered by the course: Law of Demeter, Tell Don't Ask, and Named Constructors for cohesive object creation.

---

## Law of Demeter (Principle of Least Knowledge)

**Intent:** An object should only talk to its direct collaborators, not to the collaborators of collaborators.

**How it works:** The "train wreck" pattern `a.getB().getC().doSomething()` couples you to the internal structure of A, B, and C. When any link in the chain changes, all callers break. The Demeter Law says a method may only call methods on: itself, its parameters, objects it creates, and its direct fields.

**Violation (Python):**
```python
# Bad: reaching into user's internal graph
saved_products_text = (
    f"{user.full_name.name.value} {user.full_name.last_name.value}'s saved products:\n"
)
for saved_product in user.saved_products:
    product_id = saved_product.id.value      # three levels deep
    product_name = saved_product.name.value
    product_price = saved_product.price.value
```

**Fixed (Python):**
```python
# Good: User encapsulates its own representation
print(user.display_saved_products())
```

**Practical heuristic:** Count the dots. More than one dot in a single expression is a warning sign. Move the behavior to the object that owns the data.

---

## Tell Don't Ask

**Intent:** Instead of querying an object's state and making decisions based on it, tell the object to make the decision itself.

**How it works:** "Ask" code extracts data and makes decisions outside the object, scattering the logic. "Tell" code sends a command and lets the object apply its own rules. This keeps the Single Responsibility Principle: the object that knows the data owns the behavior.

**Ask approach (bad):**
```python
# Caller reads internal state and mutates it directly
if product1 not in user.saved_products:
    user.saved_products.append(product1)

user.saved_products.remove(product1)
remaining_products = len(user.saved_products)
```

**Tell approach (good):**
```python
# Caller sends intent; User decides how to fulfill it
user.add_to_saved_products(product1)
user.remove_from_saved_products(product1)
print(user.display_saved_products())
```

The `User` class owns the rules about what "add to saved products" means (e.g., no duplicates), rather than leaking that logic to every caller.

**Practical heuristic:** If you call a getter and then immediately make a decision based on the result, you are asking. Move that decision into the object as a method that accepts the intent, not the implementation.

---

## Named Constructors for Cohesion

**Intent:** Replace overloaded or flag-driven constructors with static factory methods whose names express the creation intent.

**How it works:** A single constructor with many optional parameters or a `type` flag forces callers to know the internal structure. Named constructors are static methods that encapsulate creation variants under meaningful names. This is taught in the cohesion vs coupling section of the course.

**Before — primitive constructor:**
```java
// Caller must know which arguments each role needs
User user1 = new User("javier", "javier@codely.tv", "admin", null, "ADMIN_CODE");
User user2 = new User("maria",  "maria@codely.tv",  "user",  25,   null);
```

**After — named constructors:**
```typescript
class User {
  private constructor(
    private readonly id: UserId,
    private readonly email: UserEmail,
    private readonly role: UserRole
  ) {}

  static createAdmin(id: string, email: string, adminCode: string): User {
    return new User(new UserId(id), new UserEmail(email), UserRole.admin(adminCode));
  }

  static createStandardUser(id: string, email: string): User {
    return new User(new UserId(id), new UserEmail(email), UserRole.standard());
  }
}
```

Making the constructor `private` forces all creation through named constructors, ensuring invariants are always enforced.

**Practical heuristic:** If callers pass different combinations of nullable arguments depending on context, that is a signal to introduce named constructors — one per creation context.

---

## Cohesion vs Coupling

**Intent:** High cohesion means a class's parts all serve the same purpose. Low coupling means a class depends on as few external things as possible.

**How it works:** The course treats these as a pair. Adding responsibilities to a class raises coupling (it needs more collaborators) and lowers cohesion (it serves more masters). Named constructors and value objects are tools for improving both simultaneously: creation logic moves into the class (cohesion), and callers no longer need to know primitive construction details (coupling).

**Practical heuristic:** If you find yourself importing or injecting a new dependency to support a new method, ask whether that method belongs in this class or in the class that already owns the dependency.

---

## Related Skills

- `oop-best-practices` — naming, object boundaries, value objects
- `simple-design-rules` — Rule 2 (reveals intention) and Rule 3 (no duplication) complement Tell Don't Ask
