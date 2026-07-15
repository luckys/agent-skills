# Migrating Error Contracts Safely

Changing an exception, null, Result variant, status code, message, or throw timing can be externally observable. Treat error modernization as a behavior migration, not automatically as a refactoring.

## Migration Sequence

1. Characterize current success and every failure path: type, message, timing, side effects, logs, status, and response body.
2. Separate absence from outage and business rejection from validation/transport failure.
3. Introduce a typed internal failure alongside the old boundary contract.
4. Translate it at one adapter so external behavior remains stable.
5. Migrate callers from null/string/message parsing to type/code matching.
6. Introduce Result/Either only where failures are expected and callers compose/recover.
7. Add exhaustive mapping, redaction, and unknown-failure tests.
8. Change the public contract only as an explicit versioned behavior change.
9. Remove the compatibility adapter after all callers and contract tests migrate.

## Preserve Failure Timing

Moving validation earlier can prevent side effects; moving it later can leave partial state. Prove rejected operations remain atomic. A Result does not roll back writes performed before `error` is returned.

## Preserve Diagnostics

When translating vendor exceptions, preserve the original cause for logs/traces while exposing only a stable internal category. Do not replace every exception with a generic domain error and lose operational evidence.

## Red Flags

- Parsing exception messages during migration.
- Mapping database outage to not-found.
- Publishing class names as permanent API codes.
- Reflectively serializing all error properties.
- Big-bang conversion of every throw to a home-grown Result.
- Unchecked catch casts presented as exhaustive.
- Changing status/body/message without acceptance-contract tests.
