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
