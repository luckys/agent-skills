# TDD Schools: London vs Chicago, BDD, and ATDD

## Two Schools of TDD

TDD practitioners disagree on one key question: how much should unit tests isolate collaborators? Two schools emerged from the XP community.

---

## Chicago / Detroit School (Inside-Out, Classicist)

Associated with Kent Beck and the original XP community in Detroit.

**Approach:**
- Start from the inside — the domain model, the core business logic.
- Build outward: domain → application services → infrastructure.
- Use real objects wherever they are fast and deterministic.
- Replace only I/O-bound or non-deterministic collaborators.

**Test strategy:**
- Assert on state: what is the object's state after the operation?
- Integration is natural — multiple real objects collaborate in tests.
- Few mocks; more Fakes for external dependencies.

**Strengths:**
- Tests survive refactoring because they test behavior, not structure.
- Less test maintenance when internals change.
- Simpler setup — no mock configuration for every collaborator.

**Weaknesses:**
- Slower feedback loop when building toward external boundaries.
- Harder to pinpoint failure when many collaborators are real.

**Typical test structure:**

```typescript
// Chicago: real objects, assert on state
it("places an order when inventory is available", () => {
  const inventory = new InMemoryInventory({ "ITEM-1": 10 });
  const repo = new InMemoryOrderRepository();
  const service = new OrderService(inventory, repo);

  service.placeOrder(new Order("ITEM-1", 2));

  expect(repo.findAll()).toHaveLength(1);
  expect(inventory.stockFor("ITEM-1")).toBe(8);
});
```

---

## London School (Outside-In, Mockist)

Associated with Steve Freeman, Nat Pryce, and the GOOS book (*Growing Object-Oriented Software, Guided by Tests*). Emerged from the London XP community.

**Approach:**
- Start from the outside — acceptance tests define the feature.
- Drive design inward: discover collaborators by mocking the interfaces you wish existed.
- Use mocks for all collaborators, even ones you own.
- Interactions between objects are first-class behavior.

**Test strategy:**
- Assert on behavior: did the SUT send the right messages to collaborators?
- Mocks double as design tools — if a mock is hard to set up, the object has too many dependencies.
- Acceptance test stays red until the full feature is complete.

**Strengths:**
- Continuous design pressure — forces small, focused objects.
- Acceptance test gives a clear "done" signal.
- Natural fit for use cases with multiple external side effects.

**Weaknesses:**
- Tests are coupled to implementation — refactoring collaborators breaks tests.
- Over-mocking leads to tests that verify mocks, not behavior.
- Requires discipline to avoid the mockery anti-pattern.

**Typical test structure:**

```typescript
// London: mock collaborators, assert on interaction
it("publishes UserRegistered event when user signs up", async () => {
  const repo = mock<UserRepository>();
  const eventBus = mock<EventBus>();
  const useCase = new RegisterUserUseCase(repo, eventBus);

  await useCase.execute(new RegisterUserCommand("alice@example.com"));

  expect(repo.save).toHaveBeenCalledTimes(1);
  expect(eventBus.publish).toHaveBeenCalledWith(
    expect.arrayContaining([expect.objectContaining({ type: "UserRegistered" })])
  );
});
```

---

## Outside-In TDD Workflow (London)

```
1. Write a failing acceptance test (full system, from user's perspective).
2. Write a failing unit test for the outermost object (controller, use case).
3. Mock the next collaborator — this defines the interface you need.
4. Implement the unit to make the unit test pass.
5. Repeat inward: write unit test for the mocked collaborator.
6. Continue until all layers are implemented.
7. The acceptance test now passes — feature complete.
```

The acceptance test acts as the outer loop. Unit tests are the inner loop.

---

## BDD — Behaviour-Driven Development

Dan North extended TDD by focusing on *behavior* language. BDD is TDD with better naming conventions and a customer-facing layer.

**Key ideas:**
- Name tests after behaviors, not methods: `"should reject orders when inventory is empty"`.
- Use Given/When/Then to structure the test narrative.
- Tests become executable specifications — they document expected behavior.
- Ubiquitous language from DDD maps naturally into test descriptions.

**Given / When / Then:**

```gherkin
Feature: Order placement
  Scenario: Reject order when inventory is empty
    Given the inventory has 0 units of "ITEM-1"
    When a customer tries to order 1 unit of "ITEM-1"
    Then the order should be rejected with "InsufficientStock"
```

**In code (RSpec style):**

```ruby
describe OrderService do
  context "when inventory is empty" do
    it "rejects the order" do
      inventory = instance_double(Inventory, stock_for: 0)
      service = OrderService.new(inventory)

      expect { service.place_order(Order.new("ITEM-1", 1)) }
        .to raise_error(InsufficientStock)
    end
  end
end
```

**Tools:** Cucumber (Gherkin), SpecFlow (.NET), Behave (Python), Behat (PHP), RSpec (Ruby).

**When to use BDD's Given/When/Then:**
- Domain logic with clear scenarios.
- Stakeholder-visible behavior.
- When the test reads as a specification the product owner can understand.

---

## ATDD — Acceptance Test-Driven Development

ATDD (also called Specification by Example) is the practice of writing acceptance tests *before* implementation, in collaboration with business stakeholders.

**Process:**
1. Define acceptance criteria as executable tests before any code is written.
2. Automate the acceptance tests (Cucumber, Selenium, Playwright, API tests).
3. Implement the feature until the acceptance tests pass.
4. Acceptance tests become the regression suite.

**Key benefit:** Acceptance tests expose misunderstandings early — before implementation. A failing acceptance test found during development costs 10× less than one found in QA.

**Scope:** ATDD acceptance tests should test system behavior at the boundary — what the user sees or what the API returns — not internal implementation.

---

## Choosing a School

| Situation | Recommendation |
|---|---|
| Domain model is the core of the feature | Chicago (inside-out) |
| Building a use case with multiple external side effects | London (outside-in) |
| Feature has a clear user-facing scenario | BDD (Given/When/Then naming) |
| Team collaborates with non-technical stakeholders on requirements | ATDD |
| Refactoring existing code | Chicago — fewer mock expectations to update |
| New greenfield service with unclear API design | London — mocks force interface discovery |

In practice, most teams mix: use London for application/infrastructure layers, Chicago for domain logic.

---

## Sources

- Steve Freeman & Nat Pryce, *Growing Object-Oriented Software, Guided by Tests* (GOOS)
- Kent Beck, *Test Driven Development: By Example*
- Dan North, "Introducing BDD" (dannorth.net)
- Martin Fowler, "Mocks Aren't Stubs" (martinfowler.com)
- Josh Justice, *Outside-In Frontend Development* (outsidein.dev)
