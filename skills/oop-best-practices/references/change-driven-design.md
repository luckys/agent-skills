# Avoid Speculative Abstraction

Use this reference when everyday object-oriented design starts drifting toward abstractions that current knowledge does not justify.

## Start with Understandable Code

A first version does not need to be highly extensible if there is no confirmed variation yet.

Prefer:

- straightforward code
- explicit intent
- minimal abstractions
- collaborators with obvious responsibilities

Avoid:

- speculative hierarchies
- abstract base classes created for future guesses
- factories that hide no meaningful construction choice

## Let Stable Variation Earn Structure

When new variation appears, ask:

- Is this variation likely to persist?
- Does the current object model make the variation noisy or scattered?
- Would naming the role make the design easier to explain?

If the answer is no, keep the code simple.
If the answer is yes, introduce the lightest abstraction that makes the model clearer.

## Treat Growing Conditionals as a Signal

Conditionals are not always wrong, but they deserve attention when:

- they keep growing with each new case
- they branch on roles or types
- they spread the same decision across many callers

At that point, a better object boundary or role may be more expressive than another branch.

## Decision Rule

Do not design all variation up front.
Design just enough structure so that the current model remains readable and honest.
