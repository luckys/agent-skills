# Core Principles

Use these principles to guide normal coding work. They are meant to improve readability, flexibility, and locality of change.

## Write for Change

- Prefer designs that make the next likely change local.
- Keep public interfaces narrow.
- Delay abstraction until it removes real duplication or stabilizes recurring variation.

## Model Concepts, Not Containers

- Keep behavior close to the data that gives it meaning.
- Avoid turning objects into passive records manipulated elsewhere.
- Let meaningful concepts protect their own invariants when practical.

## Optimize for Cohesion

- Split classes when different methods change for different reasons.
- Split methods when they mix setup, decisions, and side effects.
- Keep each method at one main level of abstraction.

## Use Meaningful Names

- Prefer full names instead of abbreviations.
- Name classes by responsibility and methods by intent.
- Keep terms consistent across the model.

## Prefer Telling Over Asking

- Send messages to collaborators instead of navigating through their internals.
- Avoid train wrecks and deep object graph traversal.
- Keep decisions with the object that has the relevant knowledge.

## Make Values Explicit

- Introduce Value Objects when a cohesive value needs semantic type safety, intrinsic rules, normalization, comparison, formatting, or behavior.
- Base equality and hashing on all defining values, and protect invariants with deeply immutable observation and defensive copies.
- Introduce first-class collections when the collection has rules of its own.
- Keep intrinsic validation and formatting close to the concept; pass contextual policy explicitly.

## Use Composition Carefully

- Reach for composition when behavior varies independently.
- Keep inheritance narrow and honest.
- Prefer small roles over broad concrete dependencies.
