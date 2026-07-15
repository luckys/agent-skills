# Criteria Pattern

Source: principles and counterexamples reviewed from [CodelyTV/design_patterns-criteria-course](https://github.com/CodelyTV/design_patterns-criteria-course), corrected and generalized for production use.

Criteria is a typed Query Object that carries predicates, ordering, and pagination without exposing SQL, ORM, or search-engine syntax to callers.

## When to Use It

Use Criteria when callers genuinely compose dynamic filter/order/page combinations. Keep explicit repository/query methods when a search has stable business meaning, such as `pendingForRoute(routeId)`. Use a dedicated read-model query port when results join Aggregates, compute reports, or return projection DTOs.

Method count is not the decision rule. Criteria reduces accidental combinations; it should not erase Ubiquitous Language.

Criteria belongs in the domain only when fields/operators are domain-named concepts. A generic technical query language normally belongs in the application/query core. HTTP parameters and database columns belong at adapters.

## Model an AST, Not a String DSL

Represent boolean structure explicitly. Do not split an untrusted string on `AND`, `OR`, spaces, or parentheses.

```typescript
type Scalar = string | number | boolean | Date;
type LogicalField = "id" | "name" | "registeredAt";
type Cursor = { readonly values: readonly Scalar[] };

class InvalidCriteria extends Error {}

function freezePredicate(node: Predicate): Predicate {
  if (node.kind === "and" || node.kind === "or") {
    return Object.freeze({ ...node, operands: Object.freeze(node.operands.map(freezePredicate)) });
  }
  if (node.kind === "not") return Object.freeze({ ...node, operand: freezePredicate(node.operand) });
  if (node.kind === "in") return Object.freeze({ ...node, values: Object.freeze([...node.values]) });
  return Object.freeze({ ...node });
}

type Predicate =
  | { readonly kind: "comparison"; readonly field: LogicalField; readonly operator: ScalarOperator; readonly value: Scalar }
  | { readonly kind: "in"; readonly field: LogicalField; readonly values: readonly Scalar[] }
  | { readonly kind: "isNull"; readonly field: LogicalField }
  | { readonly kind: "and"; readonly operands: readonly Predicate[] }
  | { readonly kind: "or"; readonly operands: readonly Predicate[] }
  | { readonly kind: "not"; readonly operand: Predicate };

type ScalarOperator = "eq" | "neq" | "gt" | "gte" | "lt" | "lte" | "contains";
type Operator = ScalarOperator | "in" | "isNull";
type Direction = "asc" | "desc";

type Sort = {
  readonly field: LogicalField;
  readonly direction: Direction;
};

type OffsetPage = { readonly kind: "offset"; readonly limit: number; readonly offset: number };
type CursorPage = { readonly kind: "cursor"; readonly limit: number; readonly after: Cursor | null };
type Pagination = OffsetPage | CursorPage;

class Criteria {
  readonly predicate: Predicate | null;
  readonly sort: readonly Sort[];
  readonly pagination: Pagination;

  constructor(
    predicate: Predicate | null,
    sort: readonly Sort[],
    pagination: Pagination,
  ) {
    if (!Number.isInteger(pagination.limit) || pagination.limit < 1 || pagination.limit > 100) {
      throw new InvalidCriteria("limit must be an integer between 1 and 100");
    }
    if (pagination.kind === "offset" && (!Number.isInteger(pagination.offset) || pagination.offset < 0)) {
      throw new InvalidCriteria("offset must be a non-negative integer");
    }
    if (sort.length === 0) {
      throw new InvalidCriteria("pagination requires a stable total order");
    }
    if (sort.at(-1)?.field !== "id") {
      throw new InvalidCriteria("the final sort field must be the unique id tie-breaker");
    }
    if (pagination.kind === "cursor" && pagination.after !== null && pagination.after.values.length !== sort.length) {
      throw new InvalidCriteria("cursor values must match the complete sort order");
    }

    this.predicate = predicate ? freezePredicate(predicate) : null;
    this.sort = Object.freeze(sort.map((item) => Object.freeze({ ...item })));
    this.pagination = pagination.kind === "cursor"
      ? Object.freeze({ ...pagination, after: pagination.after ? Object.freeze({ values: Object.freeze([...pagination.after.values]) }) : null })
      : Object.freeze({ ...pagination });
  }
}
```

Use immutable arrays/objects. Parse primitive wire values through validated factories rather than enum casts or non-null assertions. Preserve number, boolean, date, null, and list types instead of coercing every filter value to string.

## Logical Field Registry

Callers use stable logical fields. Each adapter owns a closed mapping to storage identifiers and capabilities:

```typescript
type FieldDefinition = {
  readonly sql: string;
  readonly type: "string" | "number" | "boolean" | "instant" | "uuid";
  readonly operators: ReadonlySet<Operator>;
  readonly sortable: boolean;
  readonly nullable: false;
};

const userFields: Readonly<Record<LogicalField, FieldDefinition>> = {
  id: { sql: "u.id", type: "uuid", operators: new Set(["eq", "neq", "in"]), sortable: true, nullable: false },
  name: { sql: "u.name", type: "string", operators: new Set(["eq", "neq", "contains"]), sortable: true, nullable: false },
  registeredAt: { sql: "u.registered_at", type: "instant", operators: new Set(["eq", "gt", "gte", "lt", "lte"]), sortable: true, nullable: false },
};
```

Reject unknown fields, incompatible operators, wrong value types, and unsupported sorting before query execution. Never accept table names, selected columns, aliases, joins, operators, or sort directions directly from user input.

Values use bound parameters. SQL identifiers and keywords cannot be placeholders; resolve them only through application-owned mappings.

## Backend-Specific Conversion

Converters preserve Criteria semantics or reject unsupported operations. Silent approximation is incorrect.

```typescript
type SqlQuery = { readonly text: string; readonly params: readonly unknown[] };

declare function escapeLikeLiteral(value: string): string;

abstract class UserCriteriaToPostgres {
  protected abstract order(sort: readonly Sort[]): string;
  protected abstract pagination(page: Pagination, params: unknown[], sort: readonly Sort[]): string;
  protected abstract requireField(field: LogicalField, operator: Operator, value: unknown): FieldDefinition;
  protected abstract sqlOperator(operator: ScalarOperator): string;

  protected predicate(node: Predicate, params: unknown[]): string {
    switch (node.kind) {
      case "comparison": return this.comparison(node, params);
      case "isNull": return `${this.requireField(node.field, "isNull", null).sql} IS NULL`;
      case "in": {
        if (node.values.length === 0) throw new InvalidCriteria("in requires at least one value");
        const field = this.requireField(node.field, "in", node.values).sql;
        const placeholders = node.values.map((value) => { params.push(value); return `$${params.length}`; });
        return `${field} IN (${placeholders.join(", ")})`;
      }
      case "not": return `NOT (${this.predicate(node.operand, params)})`;
      case "and":
      case "or": {
        if (node.operands.length === 0) throw new InvalidCriteria(`${node.kind} requires operands`);
        return `(${node.operands.map((operand) => this.predicate(operand, params)).join(` ${node.kind.toUpperCase()} `)})`;
      }
    }
  }

  convert(criteria: Criteria): SqlQuery {
    const params: unknown[] = [];
    const where = criteria.predicate
      ? this.predicate(criteria.predicate, params)
      : "TRUE";
    const order = this.order(criteria.sort);
    const page = this.pagination(criteria.pagination, params, criteria.sort);

    return {
      text: `SELECT u.id, u.name, u.registered_at FROM users u WHERE ${where}${order}${page}`,
      params,
    };
  }

  protected comparison(node: Extract<Predicate, { kind: "comparison" }>, params: unknown[]): string {
    const definition = this.requireField(node.field, node.operator, node.value);
    const value = node.operator === "contains"
      ? `%${escapeLikeLiteral(String(node.value))}%`
      : node.value;
    params.push(value);
    return `${definition.sql} ${this.sqlOperator(node.operator)} $${params.length}`;
  }
}
```

The remaining abstract helpers are repository/backend-specific. Cursor parsing must validate each decoded value against its sort field type. This example permits only non-null sortable fields; supporting nullable sort keys requires an explicit, backend-consistent null ordering encoded in the cursor. `contains` needs an explicit contract: literal substring, prefix, token match, or full-text search. SQL `LIKE`, Elasticsearch `match`, Mongo regex, and ORM `Like` are not automatically equivalent.

Backend capability examples:

- SQL: collation, null ordering, `LIKE` escaping, and transaction isolation matter.
- Elasticsearch: exact equality generally uses `term` on a keyword field; range uses `range`; analyzed `match` is not equality.
- Mongo: escape literal regex input or use another indexed search strategy; merging objects can overwrite same-field predicates.
- ORMs: use native expression APIs, but still validate logical fields/operators and test generated semantics.

## Joins and Projections

Do not smuggle a complete `JOIN` clause through a table-name argument. A repository-specific adapter may own fixed joins and qualified field mappings. If joins are caller-composable, model a validated join/projection AST with aliases and cardinality, but prefer a dedicated read-model query port for cross-Aggregate results.

Pagination after one-to-many joins can duplicate roots. Decide whether pagination applies before or after deduplication and test missing relations, cardinality, qualified fields, sorting, and count semantics.

## Pagination

Offset and cursor pagination are different variants, not nullable fields on one bag.

### Offset

Translate one-based HTTP pages explicitly:

```text
HTTP page N, perPage P -> internal limit P, offset (N - 1) * P
```

Require a bounded limit and deterministic total order, including a unique tie-breaker. Offset pages can drift under concurrent inserts/deletes and become expensive at large offsets.

### Cursor

Cursor pagination requires a stable total order. Include every sort field plus a unique tie-breaker:

```sql
WHERE (published_at, id) < ($1, $2)
ORDER BY published_at DESC, id DESC
LIMIT $3
```

Reverse comparisons consistently for ascending order. Decode and validate opaque cursors at the delivery boundary; sign them when tampering changes authorization/scope. Bind cursor values, test duplicate sort keys and nulls, and return `nextCursor`/`hasMore` or equivalent navigation metadata.

## Boundary Translation

HTTP parsing must use a strict allow-listed schema, then translate public query vocabulary to Criteria. Unknown parameters produce a controlled client error rather than being stripped silently. Preserve current filters/order in navigation links or cursor context.

Do not expose a generic field/operator DSL publicly unless its grammar, limits, authorization, complexity budget, and compatibility are deliberate API contracts. Purpose-specific parameters are usually safer.

## Named Searches

When a Criteria composition gains business meaning, give it a name:

```typescript
class PossibleScamUsersCriteria {
  static create(now: Instant): Criteria {
    return new Criteria(/* named, tested predicate tree */, /* order */, /* bounded page */);
  }
}
```

If this becomes a stable capability rather than dynamic query composition, an explicit query method/service may communicate better than exposing the Criteria factory.

## Testing Strategy

Use separate layers:

1. Parser/validation tests reject unknown fields/operators, wrong types, malformed nesting, excessive depth/filters, invalid page sizes, and bad cursors.
2. AST tests prove immutable construction and boolean truth tables.
3. Application tests assert the intended Criteria reaches the query port.
4. Shared semantics contracts run representative datasets against each backend adapter.
5. Backend integration tests prove every supported operator, null/collation behavior, wildcard escaping, same-field predicates, ordering, joins, and pagination.
6. Adversarial tests execute quote/wildcard/identifier payloads against disposable infrastructure and prove they remain data.

Keep a few exact converter serialization tests, but do not rely on whitespace-sensitive strings as evidence of behavior. An in-memory fake cannot prove SQL, analyzer, collation, ORM, index, or cursor semantics.

## Review Checklist

- Is Criteria justified by dynamic combinations rather than method count?
- Does its layer match its vocabulary?
- Is boolean structure a typed AST rather than a raw string?
- Are collections immutable and values correctly typed?
- Are fields/operators/sorts allow-listed per adapter?
- Are only values parameterized while identifiers come from mappings?
- Does every backend preserve or explicitly reject each operator?
- Are joins and projections repository/read-model owned?
- Is pagination bounded, deterministic, and represented by distinct variants?
- Do real-adapter tests cover security and semantic edge cases?

## Course Caveats

Use the course for its evolution across SQL, Elasticsearch, joins, nested filters, ORMs, Mongo, Doctrine, Hibernate, and extracted libraries. Reviewed snapshots also include SQL interpolation, invalid identifier placeholders (`ORDER BY ? ?`), wrong `toPrimitives()` values, unchecked enum casts, untyped string DSL parsing, unstable cursors, join fragments hidden as table names, backend operator drift, regex injection risk, ignored ORM pagination, incomplete package migration, and tests that codify invalid query shapes.
