# Concept Language and Precision

Use this reference when object-oriented design needs sharper concept names and clearer conceptual boundaries, without turning the problem into full strategic modeling.

## Everyday Code Still Needs Concept Precision

Even outside explicit domain-driven design work, code becomes harder to understand when concepts are:

- ambiguous
- overloaded
- generic without being helpful
- named differently in nearby places

Software design needs words that are precise enough to guide code and conversation.

## Prefer Fit-for-Purpose Concept Names

A good concept name:

- matches the responsibility the object owns
- highlights what makes the concept distinct
- stays understandable in the local context
- reduces the need for extra explanation

A weak concept name:

- sounds elegant but hides the real rule
- collapses several different ideas into one word
- uses technical noise instead of meaning

## Make Distinctions Explicit

If two nearby ideas behave differently, let the names show that difference.

Useful questions:

- Are two words being used for the same concept?
- Is one word hiding two different concepts?
- Would a more explicit name make the rule easier to place?

## Keep the Vocabulary Close to the Code

The best concept language for everyday OO design is:

- easy to change
- visible in names and interfaces
- refined as the team learns more

The goal is not theoretical purity.
The goal is code that communicates its model clearly.
