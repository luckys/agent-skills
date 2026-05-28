# Message-Based Design

Use this reference when object interactions are more important than class hierarchies.

## Think in Messages First

Ask:

- What message does this object need to send?
- What result or behavior does it expect back?
- Which collaborator should answer that message?

This perspective often reveals better boundaries than starting from class trees.

## Depend on Behavior, Not Data

Prefer this:

- asking an object to do something meaningful

Over this:

- fetching raw data and deciding elsewhere

Data-focused collaboration usually increases coupling because callers must know internal structure.

## Trust Collaborators Through Roles

Objects should collaborate through roles with clear expectations.

A role is useful when:

- several concrete objects can answer the same message
- the caller does not care about the exact class
- the variation is about behavior, not representation

This is the core design benefit behind duck typing and interface-based collaboration.

## Create Explicit Interfaces

A good public interface:

- is small
- expresses intent
- hides internal structure
- is stable enough for clients to depend on

A weak public interface:

- leaks implementation details
- forces callers to know too much context
- changes often because responsibilities are unclear

## Minimize Context

Objects become easier to reuse when they depend on less surrounding knowledge.

Reduce context by:

- injecting collaborators
- isolating volatile dependencies
- avoiding long navigation chains
- passing cohesive concepts instead of raw pieces

## Listen to the Law of Demeter

When you see navigation like `a.b().c().d()`, ask whether:

- the caller knows too much
- a responsibility is misplaced
- a message should be introduced instead

The goal is not blind rule-following, but lower coupling and better object conversations.

## Duck Typing as Role Discovery

Duck typing is useful because it highlights that the caller cares about a capability, not a class.

Use this idea when:

- several collaborators play the same role
- explicit inheritance would be too rigid
- the abstraction is behavioral rather than taxonomic

In statically typed languages, the same design often appears as a small interface or protocol.
