# Testing Criteria and Query Adapters

Source: lessons and counterexamples from [CodelyTV/design_patterns-criteria-course](https://github.com/CodelyTV/design_patterns-criteria-course), corrected for behavior-focused tests.

## Test Layers

- Parser tests: strict fields/operators, typed values, complexity limits, page bounds, malformed cursors.
- AST tests: immutable construction and truth-table evaluation for `And`/`Or`/`Not` precedence.
- Application tests: exact Criteria intent passed to the query port, without reproducing converter logic.
- Shared semantics contract: the same dataset and expected IDs against every backend that claims support.
- Adapter integration: real SQL/search/ORM engine behavior, mappings, collation, nulls, joins, ordering, and pagination.

## Security Tests

Execute adversarial values containing quotes, comments, wildcard characters, backslashes, Unicode, and attempted stacked statements against disposable infrastructure. Assert result cardinality and schema/data integrity afterward.

Reject malicious/unknown identifiers, operators, sort directions, join aliases, excessive nesting, filter count, and page size before query execution. A query-string snapshot does not prove safety; placeholders cannot bind SQL identifiers.

## Pagination Tests

Seed deterministic rows and traverse every page. Assert no duplicates/omissions, stable ties using a unique secondary key, first/last/empty behavior, ascending and descending cursors, invalid/tampered cursors, and inserts/deletes between requests according to the documented consistency model. If nullable sort keys are supported, test the explicit null-ordering policy; otherwise test their rejection.

## Join and Boolean Tests

Test filtering and ordering on joined fields, missing relations, one-to-many cardinality, deduplication/count behavior, aliases, and page boundaries. Use boolean truth-table fixtures for multiple nesting levels, left/right groups, mixed precedence, `Not`, empty/invalid groups, and values containing operator words.

## Avoid False Confidence

- Round-trip saved records; an assertion-free save test can pass when save does nothing.
- Assert value equality, not mock reference identity.
- Keep exact SQL/DSL snapshots limited to stable serialization contracts.
- Do not infer Elasticsearch semantics from request-object equality.
- Do not infer production behavior from an in-memory Criteria evaluator.
- Run integration services through explicit, isolated test commands and lifecycle management.

## Course Caveats

The course adds tests incrementally but often commits implementation and tests together. It has no adversarial injection execution tests, limited cursor/join/nested-filter coverage, exact-string overspecification, assertion-free saves, and converter tests that lock in invalid identifier placeholders.
