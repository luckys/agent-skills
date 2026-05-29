# Hexagonal Architecture (Ports & Adapters)

Architectural pattern by Alistair Cockburn that isolates the application core from all external actors (UI, databases, message queues, external APIs) through ports (interfaces) and adapters (implementations). The goal: the application can be driven equally by users, automated tests, batch scripts, or other applications — and can work with any technology on its outside.

---

## The Core Problem: Coupling to Technology

**Definition:** The fundamental problem Hexagonal Architecture solves is business logic that leaks into UI or database code, and technology details that leak into the application core, making the system impossible to test or change without touching everything.

**How it works:** When business logic directly depends on a specific database, framework, or UI library, swapping that technology requires tearing apart the application. Tests must start the full infrastructure stack. Changing from one database to another can shut down a project for weeks. The application becomes non-interchangeable: it can only be driven one way and connected to one set of technologies.

**Key rule:** If you cannot substitute the production database with an in-memory stub to run your business logic tests without recompiling, you have a coupling problem that Hexagonal Architecture is designed to fix.

**Common mistake:** Treating the database as the "foundation" at the bottom of a layered stack — this is the root cause. The database is an external actor, not a foundation; it belongs outside the application boundary.

---

## Hexagon / Application as the Center

**Definition:** The hexagon (also called "the app," "the core," or "the system") is the software containing all business logic, with no reference to databases, networks, frameworks, or any external technology.

**How it works:** The hexagon is technology-agnostic. It is written entirely in terms of the business domain. It declares what services it provides (provided interfaces) and what services it needs from the outside world (required interfaces). It does not know or care what technology implements those required interfaces — that decision happens at wiring time. The hexagon is like a hardware chip in a catalog: its input and output pins are fully defined, and it is your job to meet those specifications.

**Key rule:** If any class inside the hexagon imports a framework, database driver, HTTP client, or any technology-specific library, that code does not belong inside the hexagon.

**Common mistake:** Placing adapters or infrastructure code inside the hexagon "for convenience." The hexagon should have zero compile-time dependencies on any external actor or technology.

---

## Ports (Primary/Driving Ports and Secondary/Driven Ports)

**Definition:** A port is a provided or required interface defined by the app that captures the idea of a conversation between an external actor and the app for some specific intention.

**How it works:** Ports define the true boundary of the hexagon. Every interaction between the app and the outside world happens at a port interface, using language the app itself defines — not the language of any external technology. Ports are named for their intention, not their implementation, using the convention "ForDoingSomething" (e.g., `ForCalculatingTaxes`, `ForGettingTaxRates`, `ForPlacingOrders`, `ForSendingNotifications`).

- **Primary (driving) port:** A port with one or more provided interfaces, used by driving actors (UI, tests, batch scripts) to make requests of the app. The app implements this interface.
- **Secondary (driven) port:** A port with one or more required interfaces, used by the app to make requests of driven actors (databases, email services, external APIs). Driven actors implement this interface.

**Key rule:** Name every port starting with "For" followed by a verb ending in "-ing" that describes the business intention. The app should have no idea what technology sits beyond the port.

**Common mistake:** Creating a driven port named after a domain concept (e.g., `UserRepository`) instead of after the external system conversation (e.g., `ForPersistingUsers`). A port represents the conversation with an external system, not the domain concept itself.

```
// Pseudocode — type-declared language style

// Primary (driving) port — app provides this
interface ForCalculatingTaxes {
    taxOn(amount): Money
}

// Secondary (driven) port — app requires this
interface ForGettingTaxRates {
    taxRate(amount): Percentage
}

// App implements the driving port, declares dependency on the driven port
class TaxCalculator implements ForCalculatingTaxes {
    taxRateRepository: ForGettingTaxRates  // held by interface, not by class

    constructor(taxRateRepository: ForGettingTaxRates)

    taxOn(amount): Money {
        return amount * taxRateRepository.taxRate(amount)
    }
}
```

---

## Adapters (Primary/Driving Adapters and Secondary/Driven Adapters)

**Definition:** An adapter is the code needed to fit the interfaces defined by the app with those of driving or driven actors — it translates between the technology-specific world and the technology-neutral port.

**How it works:** Adapters exist outside the hexagon. When an external actor already speaks the port's language (e.g., a test case coded directly against the provided interface), no adapter is needed. When an actor does not match the port's interface — for example, a human interacting through a REST controller, or a SQL database being called through a repository — an adapter translates between the two. A driving adapter receives a technology-specific request (HTTP, CLI, GUI event) and converts it into a call on the app's provided interface. A driven adapter receives a call through the app's required interface and translates it into a technology-specific action (SQL query, HTTP call, file write).

- **Primary (driving) adapter:** Connects a driving actor to a driving port (e.g., HTTP controller, CLI parser, test harness).
- **Secondary (driven) adapter:** Connects a driven port to a driven actor (e.g., SQL repository, SMTP email sender, file reader).

**Key rule:** Adapters always depend on ports. Ports never depend on adapters. All compile-time arrows point inward toward the app.

**Common mistake:** Letting the driven adapter import or reference domain objects or business logic. An adapter is pure translation code; it should not contain any business rules.

```
// Pseudocode — driven adapter example

// Driven adapter: translates the port interface to a real technology
class PostgresTaxRateRepository implements ForGettingTaxRates {
    taxRate(amount): Percentage {
        // SQL query, ORM call, etc.
        result = db.query("SELECT rate FROM tax_rates WHERE ...")
        return result.rate
    }
}

// Test double (also a driven adapter, in-memory):
class FixedRateTaxRepository implements ForGettingTaxRates {
    taxRate(amount): Percentage {
        return 0.15
    }
}

// Driving adapter: translates HTTP into port calls
class TaxController {
    app: ForCalculatingTaxes

    constructor(app: ForCalculatingTaxes)

    handlePostRequest(request): Response {
        amount = parseAmount(request.body)
        tax = app.taxOn(amount)
        return Response.ok(tax)
    }
}
```

---

## Inside vs Outside the Hexagon

**Definition:** The hexagon boundary is the definitive line separating the application (inside) from all technology and external actors (outside), enforced by the port interfaces.

**How it works:** Inside the hexagon lives: business logic, domain model, use case implementations, and port interface declarations. The port interfaces themselves belong to the app — they are declared by the app and owned by it. Outside the hexagon lives: all adapters, all concrete technology implementations (databases, HTTP servers, message brokers), the configurator, and all driving actors (UI, tests, batch scripts). The pattern says nothing about how you organize the inside of the app or how you organize the outside — those are your choices. You can use DDD, Clean Architecture layers, or anything else inside. Outside is equally unconstrained.

**Key rule:** External actors may only interact with the app through its defined ports. No external actor is allowed to access anything inside the hexagon directly.

**Common mistake:** Thinking the pattern prescribes layers inside the hexagon. Hexagonal Architecture only mandates the inside/outside split at the ports — it is completely silent on how you structure the inside. You can use DDD, procedural code, or anything else.

---

## Dependency Direction: Adapters Depend on Ports, Never the Reverse

**Definition:** All compile-time dependencies point inward — toward the app. The app has zero source code dependencies on any primary or secondary actor.

**How it works:** The driving actor (or its driving adapter) must know the app's provided interface to call it — so the driving adapter depends on the driving port. The app must know the required interface to call driven actors — so the app depends on the driven port interface. But the driven adapter (the concrete implementation) depends on the driven port interface, not the other way around. The app never imports anything from outside the hexagon. This is the inversion of control that makes the whole pattern work: the app declares what it needs (required interfaces), and the outside world provides it.

**Key rule:** The app has no source code imports from any adapter, driver, database library, or external system. If you see the app importing a framework class, the dependency rule is violated.

**Common mistake:** Having the app call a concrete driven adapter class directly instead of calling through the required interface. The app must always hold a reference typed as the port interface, not as the concrete adapter class.

---

## Test Strategy with Hexagonal Architecture

**Definition:** Tests act as driving actors (or configurators), and test doubles (stubs, mocks, fakes) act as driven actors — substituting for production infrastructure without any code changes to the app.

**How it works:** Because the app depends only on port interfaces, you can wire the app to any implementation at test time. Test cases instantiate an in-memory driven interactor (implementing the driven port), instantiate the app passing that test double in the constructor, then call the app through its driving port. No database, no HTTP server, no external service is needed. The test case acts simultaneously as configurator and driving actor. System-level tests are pure and fast because there are no real connections. You can later write integration tests by connecting the same app to a real (or test) database, and end-to-end tests by connecting the production driver — all without changing the application code.

**Key rule:** Always include a test driver or test double at each port. Without them, a port is just a line on a diagram, not a real boundary.

**Common mistake:** Asserting that "we don't need to abstract the database because we can use an in-memory database in tests." Even if the technology allows fast in-memory variants, they still require the full driver stack, leak technology details into tests, and prevent swapping technologies later.

```
// Pseudocode — test wiring

test "calculates 15% tax on 100" {
    // Test double acts as driven actor
    rateRepo = FixedRateTaxRepository(rate: 0.15)

    // App wired with test double (configurator role)
    app = TaxCalculator(taxRateRepository: rateRepo)

    // Test case acts as driving actor
    result = app.taxOn(100)
    assert result == 15
}

test "calculates 30% tax for France" {
    rateRepo = FixedRateTaxRepository(rate: 0.30)
    app = TaxCalculator(taxRateRepository: rateRepo)
    result = app.taxOn(100)
    assert result == 30
}
```

---

## Comparison with Layered Architecture (Why Layers Fail)

**Definition:** Traditional layered architecture organizes code by concern level (Presentation → Business Logic → Data Access), where higher layers depend on lower layers — placing the database at the foundation.

**How it works:** In a layered architecture, the business logic layer depends on the data access layer, which depends on the specific database technology. Swapping the database requires changing the data access layer, which can ripple up into business logic. Running business logic tests requires the database to be present. The UI layer at the top and the database at the bottom are both considered "layers of the same stack," rather than both being external actors. Hexagonal Architecture differs in two fundamental ways: it has exactly two layers (inside the app, and outside), and it requires that all external actors — including both the UI and the database — connect only through ports. The database is not at the bottom; it is outside, on equal footing with the UI.

**Key rule:** In Hexagonal Architecture, the UI and the database are symmetric — both are external actors that connect through ports. Neither is "above" or "below" the other.

**Common mistake:** Implementing only the "top" side (UI → app) with an interface, but leaving the "bottom" side (app → database) as a direct dependency. Patterns like MVC solve only the driving side; they leave the driven side tightly coupled. Hexagonal Architecture is symmetric — both sides need ports.

---

## Relationship to Clean Architecture and Onion Architecture

**Definition:** Clean Architecture (Robert C. Martin) and Onion Architecture (Jeffrey Palermo) are related approaches that share the same inversion of dependency direction as Hexagonal Architecture but prescribe specific internal layering of the application core.

**How it works:** All three architectures agree on the key principle: external technologies (UI, database, frameworks) belong outside the domain/business logic, and all dependencies point inward. They look "upside down" compared to traditional layered architectures because the application core is at the center or bottom, not at the top. The difference is that Clean Architecture prescribes four internal rings (Entities, Use Cases, Interface Adapters, Frameworks & Drivers) and Onion Architecture prescribes internal rings (Domain Model, Domain Services, Application Services, UI/Infrastructure). Hexagonal Architecture says nothing about internal structure — it only mandates the inside/outside split at ports. You are free to apply Clean or Onion Architecture's internal layering inside your hexagon.

**Key rule:** If you want Clean or Onion Architecture's internal structure, use it inside the hexagon. Hexagonal Architecture is not in conflict with either — it is the external boundary mechanism that enables both to function without infrastructure entanglement.

**Common mistake:** Treating Clean Architecture and Hexagonal Architecture as competing alternatives. They operate at different levels: Hexagonal defines the external boundary; Clean and Onion define internal organization. They compose rather than compete.

---

## How to Implement Step by Step

**Definition:** The development sequence for Hexagonal Architecture starts with the smallest possible skeleton that exercises the full architecture, then grows incrementally.

**How it works:** The recommended sequence follows a "Walking Skeleton" approach — establish the architecture with minimal behavior before adding real functionality:

**Step 0 — Set up folder structure first:**
```
app/
  business-logic/
  driving-ports/       # port interface declarations (type-declared languages)
  driven-ports/        # port interface declarations
driving-adapters/      # one subfolder per adapter
driven-adapters/       # one subfolder per adapter
tests/
```

**Step 1 — Driving side, app returning a constant:**
- Declare the first driving port interface: `ForAccomplishingSomething`
- Write the simplest app that implements the driving port and returns a hardcoded constant
- Write a test that calls the driving port and expects that constant
- Run and pass the test — the driving side architecture is established

**Step 2 — Driven side, connect a test double:**
- Declare the first driven port interface: `ForAccomplishingXYZ`
- Write a test double (in-memory class implementing the driven port) and place it in driven-adapters
- Add an instance variable typed as the driven port interface to the app
- Add a constructor that accepts the driven port interface (not the concrete class)
- Change the app to call the driven actor for the result instead of returning a constant
- Update the test: instantiate the test double, pass it to the app constructor, verify the result
- The full Ports & Adapters architecture is now established

**Step 3 — Driving side, add real driving actor:**
- Add a real UI, web controller, or CLI adapter to driving-adapters
- Connect it to the driving port; it still uses the test double on the driven side

**Step 4 — Driven side, add real repository or receiver:**
- Choose the production technology (database, file, API)
- Write a driven adapter in driven-adapters that implements the driven port using real technology
- Wire production driver to production driven actor via the configurator (main, DI container, or composition root)

**Key rule:** Always declare the app's dependency on a driven actor using the port interface type — never the concrete adapter class. The configurator is the only place that knows about concrete implementations.

**Common mistake:** Building the full application before establishing the architecture. The architecture should be established in step 1-2 with minimal behavior, so that every subsequent feature addition inherits the correct structure automatically.

---

## The Configurator (Fifth Element)

**Definition:** The configurator is the piece of code — outside the pattern itself — that wires all players together: it instantiates driven adapters, instantiates the app (injecting driven adapters), and instantiates driving adapters (injecting the app).

**How it works:** The configurator is the "know-it-all" element. It is the only place in the system that knows about concrete adapter classes. In production, this is typically `main`, a composition root, or a dependency injection framework like Spring. In tests, the test case itself acts as the configurator. The configurator always follows this order: (1) instantiate driven adapters, (2) instantiate the app with driven adapters injected, (3) instantiate driving adapters with the app injected.

**Key rule:** The configurator must be the only place that references concrete adapter classes. Every other piece of code should reference only port interfaces.

**Common mistake:** Letting the app look up its own driven actors (service locator antipattern without isolation). If the app calls a service locator that returns concrete types, the app now has a hidden dependency on concrete infrastructure, defeating the purpose of the driven port.

---

## Hexagonal Architecture in the Frontend

Source: https://github.com/CodelyTV/frontend-hexagonal_architecture-course

The same Ports & Adapters principles that govern a backend service apply identically to a frontend application. The UI framework (React, Vue, Angular) is a driving adapter. The HTTP API, localStorage, and browser APIs are driven adapters. The application use cases and domain model live inside the hexagon, with zero framework imports.

---

### The Frontend Hexagon

**Intent:** Keep UI components thin by pushing all decision logic into framework-agnostic use case functions inside the hexagon.

**How it works:** The frontend hexagon contains: domain model types (`Course`, `User`), repository port interfaces (`CourseRepository`), and use case functions (`getAllCourses`, `createCourse`). The UI component (React, Vue, etc.) acts as a driving adapter — it calls a use case and renders the result. No fetch calls, no localStorage reads, no API URLs appear inside the hexagon.

**Folder structure:**
```
src/
  modules/
    courses/
      domain/
        Course.ts             # Domain type (interface or class)
        CourseRepository.ts   # Driven port (interface)
      application/
        get-all/
          getAllCourses.ts     # Use case function
        create/
          createCourse.ts     # Use case function
      infrastructure/
        HttpCourseRepository.ts          # Driven adapter (fetch API)
        LocalStorageCourseRepository.ts  # Driven adapter (localStorage)
        InMemoryCourseRepository.ts      # Test double
  sections/
    courses/
      CoursesSection.tsx   # Driving adapter (React component)
```

**Practical heuristic:** If your React/Vue component imports `fetch`, `axios`, or `localStorage` directly, the hexagon boundary has been broken. The component should only import use case functions.

---

### Domain Model in the Frontend

**Intent:** Define what the application cares about as a pure TypeScript type — no framework, no HTTP, no DOM.

**How it works:** A frontend domain model is typically a plain TypeScript interface. Unlike backend DDD where the aggregate has rich behavior, the frontend domain model often represents a read model: the data shape the UI needs to display or manipulate. The key rule is that it must be definable without importing any framework.

**Example:**
```typescript
// src/modules/courses/domain/Course.ts
export interface Course {
  id: string;
  title: string;
  imageUrl: string;
}
```

**Practical heuristic:** If your domain type imports anything from `react`, `vue`, `axios`, or your HTTP client, it belongs in infrastructure, not domain. A domain type should be portable to a CLI, a test, or a different framework without changes.

---

### Repository Port in the Frontend

**Intent:** Declare what the application layer needs from data sources using a domain-language interface, with no technology details.

**How it works:** The `CourseRepository` interface lives in `domain/` and describes the operations the use cases need. The interface uses domain types as parameters and return values. Multiple adapters can implement the same port: one fetches from an HTTP API, another reads from localStorage, a third uses in-memory data for tests. The use case never knows which adapter it has.

**Example:**
```typescript
// src/modules/courses/domain/CourseRepository.ts
import { Course } from './Course';

export interface CourseRepository {
  save(course: Course): void;
  getAll(): Promise<Course[]>;
}
```

**Practical heuristic:** A repository port should read like a domain vocabulary list — `save`, `getAll`, `findById`. If you see `get('/api/courses')` or `localStorage.getItem()` in an interface, it belongs in the adapter, not the port.

---

### Use Case Functions in the Frontend

**Intent:** Express application behavior as pure functions that depend only on the repository port interface, making them testable without any infrastructure.

**How it works:** A frontend use case accepts the repository as a parameter (dependency injection by argument) and returns the domain result. Two styles appear in the CodelyTV course: a simple function that directly accepts the repository and arguments, and a curried function that closes over the repository and returns an executable function. Both keep the use case 100% framework-free.

**Example:**
```typescript
// Simple style — src/modules/courses/application/create/createCourse.ts
import { Course } from '../../domain/Course';
import { CourseRepository } from '../../domain/CourseRepository';

export function createCourse(
  courseRepository: CourseRepository,
  course: Course
): void {
  courseRepository.save(course);
}

// Curried style — src/modules/courses/application/get-all/getAllCourses.ts
import { Course } from '../../domain/Course';
import { CourseRepository } from '../../domain/CourseRepository';

export function getAllCourses(courseRepository: CourseRepository) {
  return async function (): Promise<Course[]> {
    return courseRepository.getAll();
  };
}
```

**Practical heuristic:** If the use case function body contains `fetch`, `axios`, `useState`, or any framework API, it has leaked into infrastructure. The function should only call methods on the port interface it received.

---

### Driven Adapters: Infrastructure Implementations

**Intent:** Implement the repository port for a specific technology, keeping all technology-specific code — URLs, HTTP clients, storage keys — in one isolated class or factory function.

**How it works:** Each adapter implements the `CourseRepository` interface using a concrete technology. The `LocalStorageCourseRepository` uses `localStorage`; an `HttpCourseRepository` would use `fetch`. Adapters created as factory functions (rather than classes) are idiomatic in functional TypeScript. The adapter is wired to the use case in the component or a composition root — never inside the use case itself.

**Example:**
```typescript
// src/modules/courses/infrastructure/LocalStorageCourseRepository.ts
import { Course } from '../domain/Course';
import { CourseRepository } from '../domain/CourseRepository';

export function createLocalStorageCourseRepository(): CourseRepository {
  return { save };
}

function save(course: Course): void {
  const courses = getAllFromLocalStorage();
  courses.set(course.id, course);
  localStorage.setItem('courses', JSON.stringify(Array.from(courses.entries())));
}

function getAllFromLocalStorage(): Map<string, Course> {
  const courses = localStorage.getItem('courses');
  if (courses === null) return new Map();
  return new Map(JSON.parse(courses) as Iterable<[string, Course]>);
}
```

**Practical heuristic:** Every line in an adapter that references a technology-specific API (`fetch`, `localStorage`, `indexedDB`, `axios`) is correct and expected there. Any such line found outside an adapter is a boundary violation.

---

### Testing Frontend Hexagonal Code

**Intent:** Test use cases in complete isolation from the browser, network, and UI framework by substituting real adapters with in-memory test doubles.

**How it works:** The in-memory repository implements the same `CourseRepository` interface using a plain JavaScript `Map`. The test instantiates the in-memory repository, calls the use case passing that repository, then asserts against the repository's state. No browser APIs, no mocking frameworks, no HTTP servers are needed. The test is a fast, deterministic unit test.

**Example:**
```typescript
// src/modules/courses/infrastructure/InMemoryCourseRepository.ts
import { Course } from '../domain/Course';
import { CourseRepository } from '../domain/CourseRepository';

export function createInMemoryCourseRepository(): CourseRepository & {
  getStoredCourses(): Map<string, Course>;
} {
  const store = new Map<string, Course>();

  return {
    save(course: Course): void {
      store.set(course.id, course);
    },
    async getAll(): Promise<Course[]> {
      return Array.from(store.values());
    },
    getStoredCourses() {
      return store;
    },
  };
}

// createCourse.test.ts
import { createCourse } from '../application/create/createCourse';
import { createInMemoryCourseRepository } from '../infrastructure/InMemoryCourseRepository';

describe('createCourse use case', () => {
  it('saves the course to the repository', () => {
    const repository = createInMemoryCourseRepository();
    const course = { id: '1', title: 'DDD Course', imageUrl: '/img.png' };

    createCourse(repository, course);

    expect(repository.getStoredCourses().get('1')).toEqual(course);
  });
});
```

**Practical heuristic:** If your use case test imports anything from a browser API, a framework, or a network library, the hexagon boundary is broken and the test is testing more than one thing. Fix the boundary first, then the test becomes trivial.
