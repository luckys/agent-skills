# Gradual Abstraction

Introduce abstraction incrementally — start with the simplest working code and let real change pressure reveal where structure belongs.

## Shameless Green: Green Is the Goal, Not Cleverness

The first version of any code should reach green as quickly and directly as possible. Shameless Green prioritizes understandability over changeability. It accumulates concrete examples, duplicates where necessary, and defers structural insight until the code teaches you what it needs.

Shameless Green is not careless — it is deliberate. It refuses to speculate. The code might be duplicative and far from object-oriented, but if nothing ever changes, it is the most cost-effective solution. Embarrassing duplication is acceptable when the abstractions that would remove it are not yet visible.

Write Shameless Green because:

- You do not yet have enough concrete examples to see the right abstraction
- An incorrect abstraction is harder to recover from than temporary duplication
- The simplest code that passes the tests is the safest foundation for future refactoring

## The Cost of Duplication vs. The Cost of a Wrong Abstraction

Duplication has a cost. But a wrong abstraction has a higher one.

When you abstract too early, you lock in a model before you understand the problem. That model then shapes every future addition. Changing a wrong abstraction requires undoing both the abstraction and everything built on top of it. Temporary duplication only requires a refactoring once the right concept becomes clear.

When weighing duplication against abstraction, ask:

- Does removing this duplication make the code easier or harder to understand?
- Will a change here cost the same regardless of whether I act now or wait?
- Am I seeing enough concrete examples to be confident about what they have in common?

If abstracting now would muddy the waters or require naming something you do not yet fully understand, wait. If the future cost of doing nothing is low, do nothing. Time often delivers better information — and sometimes the change never arrives at all.

Codigo Sostenible frames this as designing for the present: code written to anticipate unknown future scenarios becomes a liability. Writing generic, reusable structures before any real use has happened is the recipe for complexity that is harder to maintain than it would have been to simply rewrite. The bottleneck in large projects is not typing new lines — it is understanding and modifying existing ones.

## Flocking Rules: The Step-by-Step Process for Finding Abstraction

When a new requirement arrives and the code begins to feel like it needs structure, apply the Flocking Rules. These rules guide you from concrete duplication toward an abstraction you can name and trust:

1. Select the things that are most alike.
2. Find the smallest difference between them.
3. Make the simplest change that removes that difference.

Each change should be small enough that the tests remain green throughout. If they go red, undo and return to green before continuing.

The Flocking Rules work because they do not ask you to see the abstraction in advance. You discover it incrementally. Each small step makes two things slightly more alike. When two things are identical, you have found the shared concept and can name it. The name is the abstraction.

Refactoring changes are broken into four sequential steps:

- Parse the new code
- Parse and execute it
- Parse, execute, and use its result
- Delete unused code

Working at this level of granularity gives you precise feedback. When something goes wrong, you know exactly which step caused it. As you gain experience, you take larger steps — but only after you have earned the right by doing small ones first.

When confused, do not try to solve the whole problem at once. The more uncertain you are, the smaller the steps should be. Nibble away. Cutting small things down often reduces the large ones to manageable size.

## Message-Driven Abstraction: Let What You Say Guide What Should Exist

A deeply object-oriented signal is when code examines an argument to supply behavior on its behalf. That pattern reveals a missing object. In object-oriented design, behavior belongs to the thing that holds the data, not to the caller that inspects it.

When you find yourself writing a method that takes an argument, tests it, and then returns different behavior depending on its value — a new object is asking to exist. The argument is not data to be interrogated; it is a stand-in for an object that should be responsible for its own behavior.

This is message-driven design: the message you want to send reveals the object that should receive it. Let the messages you need to express guide what classes and roles belong in the system.

The Flocking Rules often expose this pattern. After iteratively reducing duplication, the code converges on a shape where the extracted methods all take an argument they examine with a conditional. At that point, the argument is no longer just a value — it is the responsibility of a new object.

Do not race to create this object prematurely. Let the Flocking Rules surface the pattern first. Once the shape becomes unmistakable and consistent, the object's identity is clear enough to name and extract safely.

## Signals That Abstraction Is Ready

Not every duplication signals a missing abstraction. But some do. The code is ready for abstraction when:

- The same structure appears in multiple places and each instance responds to the same change in the same way
- A conditional keeps growing with new cases that all follow the same shape
- Extracted methods show a consistent structure — same number of branches, same argument form, same return type — suggesting they all express the same underlying concept
- You can name what the variants have in common using a word from the domain, not a technical word invented for the code
- A change to one instance always requires a matching change to the others

The concept is not ready when:

- You can only see one or two concrete examples
- The name you would give it does not belong to the domain
- Making the abstraction now would require naming something at the wrong level — either too specific or too general

When the right name arrives naturally from the domain, the abstraction is ready.

## Stable Landing Points and Safe Progress

The Flocking Rules guide you through intermediate states that are consistent enough to deploy. Each small step leaves the code at a stable landing point — green, coherent, ready to continue or to stop.

This is the safety mechanism of gradual abstraction. You do not need to know the final design before you begin. Good practices reveal design as you go. Every refactoring that isolates a single responsibility makes the next decision clearer. Small, isolated methods are easy to move later. Large, entangled ones are not.

POODR's TRUE heuristic — Transparent, Reasonable, Usable, Exemplary — describes the goal of code that can absorb change. These qualities are not designed in one stroke; they accumulate through a discipline of deferring decisions until they are forced, isolating responsibilities as they become apparent, and making each incremental change the simplest one that moves the design forward.

Postpone design decisions until you are forced to make them. Any decision made before an explicit requirement arrives is a guess. Preserve your ability to decide later by keeping intermediate states clean and coherent.

## Decision Rule

When facing a decision about whether to introduce an abstraction now or wait:

- If you cannot yet name the concept using domain language, wait.
- If you have fewer than two or three concrete examples of the repeated structure, wait.
- If removing the duplication would require a name you are not confident in, wait.
- If a real change request has just arrived and it reveals exactly how the code should move, act — and follow the Flocking Rules one small step at a time.
- If the same shape keeps appearing and the next change always requires touching the same set of places, the abstraction is ready.

Start with the simplest code that works. Let change pressure accumulate. Apply small, methodical steps when it does. Name concepts only when the examples make the name obvious. The abstraction will emerge — do not force it to arrive before the code is ready to show you what it is.
