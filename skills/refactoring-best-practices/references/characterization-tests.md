# Characterization Tests

Use this reference when you need to add tests to existing, untested code before refactoring it.

## What a Characterization Test Is

A characterization test documents the actual current behavior of a piece of code. There is no "Well, it should do this" or "I think it does that." The test captures what the system does, not what it is supposed to do.

This is the opposite of a correctness test. A correctness test checks whether code matches a specification. A characterization test checks whether behavior has changed since the last time you looked. When you refactor legacy code, you are not fixing bugs — you are restructuring internals while keeping all observable behavior identical. Characterization tests are the net that catches you if restructuring accidentally changes behavior.

The distinction matters: if you write tests based on what you assume the code should do, you may discover bugs — but you will not get the safety net you need for refactoring. Bug discovery and refactoring safety are different goals that require different tests.

## Why Tests Are Required Before Touching Legacy Code

Legacy code changes without tests fall into a mode Feathers calls "Edit and Pray": you carefully plan your move, make it, and then poke around hoping nothing broke. This feels professional but provides no safety, because safety is not a function of care alone.

The alternative is "Cover and Modify": wrap the code in a test net first, then change it. When tests are in place, a refactoring step either stays green or goes red immediately. The feedback loop shrinks from days to seconds. Without that feedback, every change is a leap of faith.

The core dilemma in legacy work: to change code safely you need tests; but to write tests you often have to change code first. Resolve this by making the minimum structural changes needed to get the code into a test harness — using dependency-breaking moves that are mechanical and low-risk — and only then writing the characterization tests.

## How to Write Characterization Tests

The algorithm is deliberately mechanical:

1. Put the piece of code into a test harness.
2. Write an assertion you know will fail — assert a value you are sure the code does not return.
3. Run the test and let it fail. The failure message tells you what the code actually returns.
4. Change the assertion to expect the value the code produced.
5. Run again to confirm the test is now green.
6. Repeat for other inputs, branches, and edge cases.

This observe-then-assert loop is the key insight: you do not need to understand the code to write these tests. The code itself tells you what it does. You are a reporter, not a specifier.

Focus your tests on the areas you plan to change. Write as many cases as needed to feel confident that any unintended change in that area will show up as a failure. Concentrate especially on branches and paths that the refactoring will touch — extract, move, or inline operations are the riskiest.

Many characterization tests look like "sunny day" tests. They do not explore special conditions or edge cases exhaustively. Their purpose is to verify that particular behaviors are present and connected correctly after the refactoring, not to probe the full contract of the code.

## Finding Where to Test: Pinch Points

Before writing tests, identify a pinch point: a place in the code where a small number of assertions can detect a wide range of changes. A pinch point is a natural encapsulation boundary — a method or interface through which all the effects of a cluster of changes are visible.

Prefer interception points close to the change point. Every step between where you change code and where you observe the effect is a gap in which silent errors can hide. The fewer steps in that chain, the more confident you can be that a failing test actually points to your change.

If a class is hard to instantiate directly (because it pulls in databases, services, or framework globals), test at a higher-level interception point that is easier to reach. Once the refactoring stabilizes those inner classes, you can add narrower tests and eventually remove the broader ones.

## Golden Master / Approval Testing

When the code produces large or complex output — a report, a rendered document, a serialized data structure — writing field-by-field assertions is impractical. Golden master testing (also called approval testing) handles this at scale.

The process:

- Run the code and capture its full output as a stored snapshot file (the "golden master" or "approved" file).
- The test passes by comparing the current output against the stored snapshot. Any difference fails the test.
- When a deliberate change in behavior is correct, you update the snapshot to the new output and commit it.

Golden master testing is a characterization strategy, not a specification strategy. The snapshot records what the code did, not what it should do. It is especially useful for legacy report generators, template engines, serializers, and any code whose output is too large or variable to assert inline.

The risk of snapshot tests is that they can encode bugs alongside correct behavior. If the original output was wrong, your test protects the wrong behavior. Treat golden master tests as a refactoring scaffold, not as a permanent specification.

## Handling Side Effects and External Dependencies

Code that writes to files, sends email, calls databases, or invokes external services cannot be tested directly without setting up or mocking those systems. Two approaches:

**Sensing and separation.** Find a seam — a place where you can substitute the real collaborator with a fake one without editing the code under test. Inject the dependency through a constructor parameter, a method argument, or an interface. The fake records what the production code tried to do, so you can assert on that record rather than on the real side effect.

**Higher-level interception.** If breaking the dependency is too invasive for now, test through a higher-level interface that you can observe. A class that writes to a file might also return a status object or emit a log entry that is easier to check. Use whatever surface is available.

When sensing is genuinely impossible — the dependency is hard-coded, final, or sealed — write a thin wrapper around it, test through the wrapper, and break the hard-coded connection at the wrapper boundary. This is a mechanical move that does not change behavior.

The important constraint: any dependency-breaking change you make before writing characterization tests must itself be low-risk and mechanical. Keep those preliminary moves minimal. Their only purpose is to get the code into the test harness; do not redesign at this stage.

## When Characterization Tests Are Enough vs. When to Invest in Unit Tests

Characterization tests at a pinch point give you a broad safety net but coarse-grained feedback. They tell you that something changed inside a cluster of classes, not which class or which line. That is often sufficient for a refactoring that extracts or moves code without changing logic.

Invest in narrower unit tests when:

- You are about to change logic, not just structure.
- You need to understand what each individual class is responsible for.
- The characterization tests run slowly and would break the feedback loop.
- The refactoring involves splitting a class — at that point, tests at the old pinch point become useless and tests at each new class are needed.

The decision rule: characterization tests at the highest reachable pinch point are the cheapest way to start. Add narrower unit tests as you carve out and stabilize individual classes. Over time, the broad pinch-point tests become redundant and can be deleted.

## When to Delete Characterization Tests

Characterization tests are scaffolding, not permanent documentation. They exist to protect a specific refactoring and become a liability once that protection is no longer needed.

Delete a characterization test when:

- The class it was written for now has its own focused unit tests that cover the same paths.
- The refactoring is complete and the broad pinch-point test no longer covers any code path that a narrower test misses.
- The test is coupled to implementation details that you have since changed, causing it to break on unrelated future work.

Tests that are too tightly coupled to code create exactly the problem they were meant to prevent: every improvement breaks the test, making change painful instead of safe. A characterization test that outlives its usefulness becomes a burden to every developer who touches that code.

The signal to delete is not "the refactoring is done" but rather "the behavior this test captured is now fully covered by tests I trust more." Replace broad coverage with narrow, intention-revealing unit tests as the design improves.

## Decision Rule Summary

- Code with no tests and no imminent change: add no tests, make no structural changes.
- Code you need to refactor: write characterization tests at the nearest observable pinch point before touching anything.
- Side effects block you: make the minimum dependency-breaking move, then write characterization tests.
- Output is too large for inline assertions: use golden master / approval testing.
- Refactoring is structural only (extract, move, rename): characterization tests at a pinch point are sufficient.
- Refactoring changes logic: invest in narrower unit tests before and during the change.
- Refactoring is stable and unit tests are in place: delete the characterization tests.
