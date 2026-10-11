# Behavioral Feedback and Test Evidence

Use when choosing a test seam, reviewing test quality, or verifying that a regression check actually detects the defect.

## Discover the feedback loop

Read the repository's scripts/wrappers, test configuration, CI gates, and neighboring tests. Use its focused command during a cycle, then the broader checks justified by the change and required by the project. Do not assume a framework, package manager, browser tool, test ratio, or time budget.

Select the narrowest meaningful behavior boundary: a public function, aggregate operation, module contract, route, component, or external adapter. Confirm a boundary with the user only when a consequential contract is unclear; normal test placement does not require an approval round.

Implement one behavior vertically: a failing test, the code that passes it, then a behavior-preserving refactor while green. A scenario list can guide the work, but writing all speculative tests before any implementation loses feedback from each cycle.

## Check the oracle, not just the runner

Choose expected values from the requirement, a worked example, or an independently trusted implementation. Copying the production algorithm into an assertion reproduces the same bug. Ask which plausible wrong result would fail this test.

For a total of 10 and 5 with a specified 20% tax, assert the independently worked total 18, not a reduce and tax helper copied from production. A second case with a different result can reject a hard-coded answer.

Absence, an empty collection, or no external call can be a valid requirement. Pair it with a discriminating positive/control scenario where useful; do not ban assertion methods by name. For a command with no return value, assert its externally observable effect, including the meaningful payload and count when multiplicity matters.

For a bug fix, reproduce the defect before changing production code and keep the regression test. A missing symbol/compilation failure can start a new-feature cycle, but it does not reproduce an existing runtime bug. If a proposed regression test already passes, investigate the reproduction or coverage gap rather than making it fail artificially.

## Preserve independent evidence

Keep real pure/domain collaborators. Substitute unstable boundaries, and use real adapters to prove database, serialization, and transport claims. A fake database does not establish production isolation. Document skipped adapter checks explicitly.

Keep fixtures descriptive: a reader should see the scenario's relevant values without following a generic fixture maze. Existing unit, integration, and E2E roles remain useful; boundary placement does not impose a percentage quota or ban focused domain tests.

Report the failing-before signal, passing-after command, and material limitations. Change an assertion when the authorized behavior changes or the test proves an obsolete internal detail, not simply to make a failing build green.

## Sources and adaptation

Adapted from Matt Pocock's `tdd`, Addy Osmani's `test-driven-development`, and pstack's `tdd` and `principle-test-behavior-not-implementation`. Keeps Red–Green–Refactor and risk-based test selection. See [third-party-notices.md](third-party-notices.md).
