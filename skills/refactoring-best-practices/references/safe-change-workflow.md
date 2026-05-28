# Safe Change Workflow

Use this workflow when refactoring existing code under uncertainty.

## 1. Observe Before Editing

- Identify the entry points.
- Identify externally visible outcomes.
- Identify failure modes and side effects.
- Write down what must remain stable.

## 2. Add Characterization Tests

- Test current behavior before redesigning internals.
- Focus on outcomes, not private implementation.
- Capture edge cases that are easy to break accidentally.

## 3. Find Seams

A seam is a place where you can change behavior without editing everything around it.

Look for seams around:

- databases
- clocks and random generators
- file system access
- external APIs
- framework globals
- static singletons

## 4. Break Dependencies Narrowly

- Introduce a small adapter instead of a wide rewrite.
- Separate object construction from domain behavior.
- Move only enough code to make the next safe step possible.

## 5. Refactor in Small Moves

Good move sequence:

1. rename
2. extract method
3. move method
4. extract class
5. introduce value object
6. replace conditional with polymorphism

## 6. Recheck Constantly

After each meaningful step ask:

- Did behavior stay the same?
- Did the code become easier to change?
- Did the public API get simpler or more honest?
- Did I introduce accidental complexity?

## 7. Sensing and Separation

When breaking a dependency in legacy code, name which of two distinct problems you are solving:

- **Sensing** — you need to observe what the code does. The values it computes, the side effects it produces, or the calls it makes are invisible from the outside. Breaking the dependency lets you access or record those values so a test can verify them.
- **Separation** — you cannot even get the piece of code into a test harness to run. Hard dependencies (real database connections, live hardware, external processes) prevent instantiation or execution. Breaking the dependency replaces those collaborators so the code can run at all.

Most dependency-breaking techniques serve one or both purposes. Sensing problems are usually solved by substituting a fake collaborator that records calls or returns controlled values. Separation problems are solved by any technique that removes the obstacle to instantiation or execution. Knowing which problem you have helps you pick the right technique and avoid over-engineering the solution.

A single dependency can block you on both fronts at once. Solve separation first — you cannot sense anything from code you cannot run.

## 8. Finding Test Points

In code that has no tests, the first task is locating where a test can attach. Look in three directions:

- **Entry points** — public methods, event handlers, message handlers, and command dispatchers. These are the places where the system accepts input and begins executing the logic you want to cover.
- **Output points** — return values, written files, sent messages, database writes, and any other externally observable result. A test that drives an entry point and then checks an output point gives you direct behavioral coverage.
- **Effect points** — state that changes when the code runs: object fields, global variables, in-memory collections, and anything a collaborator records. When you cannot observe a return value or a file, a fake collaborator that records calls can expose the effect.

When direct tests on the target code are impossible, find the nearest observable point upstream or downstream and write tests there first. A test at an indirect point still catches regressions and gives you enough coverage to begin dependency-breaking work safely. As dependencies are removed, move the tests closer to the code under change.

## 9. The Legacy Code Change Algorithm

Feathers' algorithm from *Working Effectively with Legacy Code* structures every change in untested code as a five-step sequence:

1. **Identify the change points** — find the exact locations where the required change must happen. Understanding the architecture well enough to place the change correctly is a prerequisite; without this, dependency-breaking work may happen in the wrong place.
2. **Find the test points** — determine where tests can be written to cover the change points. Test points are often not the same locations as change points. Look for entry points, output points, and effect points nearby.
3. **Break dependencies** — remove the obstacles that prevent getting the code into a test harness and sensing its behavior. Apply the minimum change needed: introduce a seam, extract a collaborator, or substitute a fake. These steps are done without full test coverage and should be as mechanical and safe as possible.
4. **Write tests** — write characterization or pinch-point tests that cover the change points through the test points found in step 2. These tests document current behavior and protect against accidental regression during the actual change.
5. **Make changes and refactor** — with test coverage in place, make the functional change and then improve the surrounding structure. This is the only step where behavior is intentionally altered.

Steps 1 through 4 are setup. No functional change happens until step 5. The goal of each programming episode is to leave both new functionality and new tests behind, so that tested areas of the codebase grow over time.
