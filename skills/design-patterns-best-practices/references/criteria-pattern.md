# Criteria Pattern

A domain-level query abstraction that encapsulates filters, sorting, and pagination as first-class objects. Lets repositories accept rich query descriptions without leaking SQL or storage details into the domain layer.

Source: CodelyTV `design_patterns-criteria-course`.

---

## What Is the Criteria Pattern?

**Intent:** Encapsulate query filters, sorting, and pagination into composable domain objects so repositories can be queried without exposing SQL, ORM, or storage details to callers.

**How it works:** Instead of adding one repository method per query variant (`findByName`, `findByNameOrderedByDate`, `findActiveByCategory`…), you define a `Criteria` value object that carries filters, an order, and optional pagination. The repository accepts a single `matching(criteria: Criteria)` method. An infrastructure-side converter translates the `Criteria` into whatever the storage technology needs (SQL, Elasticsearch DSL, MongoDB query, etc.). The domain never sees SQL; the storage layer never sees domain objects.

**Core building blocks:**
- `FilterField` — the field name being tested (e.g., `"name"`, `"status"`)
- `FilterOperator` — the comparison operator (`=`, `!=`, `>`, `<`, `CONTAINS`, `NOT_CONTAINS`)
- `FilterValue` — the value to compare against
- `Filter` — one predicate: field + operator + value
- `Filters` — a collection of `Filter` objects (AND-combined by default)
- `Order` — a field name + direction (`ASC`, `DESC`, or `NONE`)
- `Criteria` — the top-level container: filters + order + optional pagination

**Practical heuristic:** If you have more than 2–3 repository methods that differ only by which fields they filter or how they sort, extract a `Criteria`-based `matching()` method and delete the specific ones.

---

## Core Domain Objects

**Example (TypeScript — from CodelyTV course):**

```typescript
// FilterOperator.ts
export enum Operator {
  EQUAL = "=",
  NOT_EQUAL = "!=",
  GT = ">",
  LT = "<",
  CONTAINS = "CONTAINS",
  NOT_CONTAINS = "NOT_CONTAINS",
}

export class FilterOperator {
  constructor(public readonly value: Operator) {
    if (!Object.values(Operator).includes(value)) {
      throw new Error(`Unsupported filter operator: ${value}`);
    }
  }

  isContains(): boolean { return this.value === Operator.CONTAINS; }
  isNotContains(): boolean { return this.value === Operator.NOT_CONTAINS; }
}

// Filter.ts
export class Filter {
  constructor(
    public readonly field: FilterField,
    public readonly operator: FilterOperator,
    public readonly value: FilterValue,
  ) {}
}

// Filter.ts — full implementation
export type FiltersPrimitives = {
  field: string;
  operator: string;
  value: string;
};

export class Filter {
  constructor(
    public readonly field: FilterField,
    public readonly operator: FilterOperator,
    public readonly value: FilterValue,
  ) {}

  static fromPrimitives(field: string, operator: string, value: string): Filter {
    const parsedOperator = Operator[operator as keyof typeof Operator];
    if (parsedOperator === undefined) throw new Error(`Unsupported filter operator: ${operator}`);

    return new Filter(
      new FilterField(field),
      new FilterOperator(parsedOperator),
      new FilterValue(value),
    );
  }

  toPrimitives(): FiltersPrimitives {
    return { field: this.field.value, operator: this.operator.value, value: this.value.value };
  }
}

// Filters.ts — collection wrapper
export class Filters {
  constructor(public readonly value: Filter[]) {}

  static fromPrimitives(filters: FiltersPrimitives[]): Filters {
    return new Filters(
      filters.map((f) => Filter.fromPrimitives(f.field, f.operator, f.value)),
    );
  }

  toPrimitives(): FiltersPrimitives[] {
    return this.value.map((f) => f.toPrimitives());
  }

  isEmpty(): boolean {
    return this.value.length === 0;
  }
}

// Order.ts
export class Order {
  constructor(
    public readonly orderBy: OrderBy,
    public readonly orderType: OrderType,
  ) {}

  static none(): Order {
    return new Order(new OrderBy(""), new OrderType(OrderTypes.NONE));
  }

  isNone(): boolean {
    return this.orderType.value === OrderTypes.NONE;
  }
}

// Criteria.ts
export class Criteria {
  constructor(
    public readonly filters: Filters,
    public readonly order: Order,
    public readonly pageSize: number | null = null,
    public readonly pageNumber: number | null = null,
  ) {
    if (pageNumber !== null && pageSize === null) {
      throw new Error("Page size is required when page number is defined");
    }
    if (pageSize !== null && (!Number.isInteger(pageSize) || pageSize < 1 || pageSize > 100)) {
      throw new Error("Page size must be an integer between 1 and 100");
    }
    if (pageNumber !== null && (!Number.isInteger(pageNumber) || pageNumber < 0)) {
      throw new Error("Page number must be a non-negative integer");
    }
  }

  static fromPrimitives(
    filters: FiltersPrimitives[],
    orderBy: string | null,
    orderType: string | null,
    pageSize: number | null,
    pageNumber: number | null,
  ): Criteria {
    return new Criteria(
      Filters.fromPrimitives(filters),
      Order.fromPrimitives(orderBy, orderType),
      pageSize,
      pageNumber,
    );
  }

  hasOrder(): boolean {
    return !this.order.isNone();
  }

  hasFilters(): boolean {
    return !this.filters.isEmpty();
  }
}
```

---

## Converting Criteria to SQL

**Intent:** Keep SQL generation in the infrastructure layer while the domain only works with `Criteria` objects.

**How it works:** A `CriteriaToSqlConverter` reads the `Criteria` and generates a parameterized SQL query. The domain repository interface accepts `Criteria`; the infrastructure implementation calls the converter and runs the query.

**Example:**

```typescript
// infrastructure/criteria/CriteriaToSqlConverter.ts
type SqlQuery = { text: string; params: unknown[] };

interface SqlAllowList {
  fields(fields: string[]): string;
  field(field: string): string;
  table(table: string): string;
  operator(operator: Operator): string;
  direction(direction: OrderTypes): string;
}

export class CriteriaToSqlConverter {
  constructor(private readonly allowed: SqlAllowList) {}

  convert(fieldsToSelect: string[], tableName: string, criteria: Criteria): SqlQuery {
    const params: unknown[] = [];
    let query = `SELECT ${this.allowed.fields(fieldsToSelect)} FROM ${this.allowed.table(tableName)}`;

    if (criteria.hasFilters()) {
      query += " WHERE ";
      const conditions = criteria.filters.value.map((filter) => {
        const field = this.allowed.field(filter.field.value);
        const operator = this.allowed.operator(filter.operator.value);
        const value = filter.operator.isContains() || filter.operator.isNotContains()
          ? `%${filter.value.value}%`
          : filter.value.value;
        params.push(value);
        return `${field} ${operator} $${params.length}`;
      });
      query += conditions.join(" AND ");
    }

    if (criteria.hasOrder()) {
      const field = this.allowed.field(criteria.order.orderBy.value);
      const direction = this.allowed.direction(criteria.order.orderType.value);
      query += ` ORDER BY ${field} ${direction}`;
    }

    if (criteria.pageSize !== null) {
      params.push(criteria.pageSize);
      query += ` LIMIT $${params.length}`;
      if (criteria.pageNumber !== null) {
        params.push(criteria.pageSize * criteria.pageNumber);
        query += ` OFFSET $${params.length}`;
      }
    }

    return { text: `${query};`, params };
  }
}
```

`SqlAllowList` must reject unknown identifiers and map domain operators such as `CONTAINS`/`NOT_CONTAINS` to the database dialect's `LIKE`/`NOT LIKE`. If `%` and `_` should be literal characters, escape them and declare the SQL escape character explicitly.

**Practical heuristic:** The converter is an infrastructure concern — it belongs next to the repository implementation, not in the domain. If you need to support Elasticsearch or MongoDB later, you write a new converter, not a new domain interface.

---

## Repository Interface with Criteria

**Intent:** Expose a single `matching()` method on the repository instead of one method per query combination.

**Example:**

```typescript
// domain/CourseRepository.ts
export interface CourseRepository {
  save(course: Course): Promise<void>;
  search(id: CourseId): Promise<Course | null>;
  matching(criteria: Criteria): Promise<Course[]>;  // replaces findByName, findByCategory, etc.
}

// infrastructure/PostgresCourseRepository.ts
export class PostgresCourseRepository implements CourseRepository {
  constructor(
    private readonly connection: PostgresConnection,
    private readonly converter: CriteriaToSqlConverter,
  ) {}

  async matching(criteria: Criteria): Promise<Course[]> {
    const query = this.converter.convert(
      ["id", "name", "summary", "categories", "published_at"],
      "mooc.courses",
      criteria,
    );
    const rows = await this.connection.query(query.text, query.params);
    return rows.map(this.toAggregate);
  }
}
```

---

## Using Criteria from the Application Layer

**Intent:** Allow controllers and use cases to build queries in domain terms, with HTTP query params translated at the boundary.

**How it works:** The HTTP controller receives raw query string parameters and converts them to `Criteria` using `fromPrimitives`. The use case (or repository) receives a strongly-typed `Criteria` object and never sees the HTTP request.

**Example:**

```typescript
// app/CoursesGetController.ts
export class CoursesGetController {
  async handle(req: Request): Promise<Response> {
    const input = criteriaRequestSchema.parse(req.query); // validates JSON shape and allow-lists
    const criteria = Criteria.fromPrimitives(
      input.filters,
      input.orderBy,
      input.order,
      input.pageSize,
      input.pageNumber,
    );
    const courses = await this.repository.matching(criteria);
    return Response.json(courses.map((c) => c.toPrimitives()));
  }
}
```

**Practical heuristic:** Parse and validate `Criteria` at the controller boundary. Validate JSON shape, recognized fields/operators, integer ranges, and a maximum page size before constructing the Value Object. Translate validation failures into a controlled client error rather than a database error.

---

## Composable Criteria and Complex Filters

**Intent:** Support complex queries (OR conditions, nested filters, joins) by extending the `Criteria` model.

**How it works:** The `Filters` collection can be enhanced to support `OR` groups, not just `AND`. The course repo (`06-joins_with_criteria`, `07-complex_filters`) shows how to add a `FilterGroup` concept where each group's filters are ANDed and groups are ORed.

**Practical heuristic:** Start with AND-only filters — they handle 90% of real use cases. Add OR/nested support only when a concrete query requires it, not speculatively.

---

## Pagination Strategies

**Intent:** Attach pagination to `Criteria` without leaking `LIMIT`/`OFFSET` into domain code.

Two pagination strategies from the course:

- **Offset pagination** (`pageSize` + `pageNumber`): Simple, works with any storage. Suffers from page drift on high-write collections (rows inserted between page 1 and page 2 fetches cause items to shift). Add `pageSize` and `pageNumber` to `Criteria`.

- **Pointer/cursor pagination** (`pageSize` + cursor): Avoids offset drift when the cursor encodes every field in a stable total order. A timestamp alone is insufficient when values can tie; use a deterministic tie-breaker such as `(publishedAt, id)`.

**Example (offset pagination in Criteria):**
```typescript
const criteria = Criteria.fromPrimitives(
  [{ field: "status", operator: "=", value: "published" }],
  "published_at",  // orderBy
  "DESC",          // orderType
  20,              // pageSize
  0,               // pageNumber (first page)
);
```

**Cursor/pointer pagination — production correction to the course's single-field example:**

The simplified course variant replaces `pageNumber` with a `cursor: string | null` field and emits `WHERE orderBy < cursor` instead of `OFFSET`. In production, encode and validate all ordered values in the cursor, bind them as parameters, and include a unique tie-breaker. The shortened example below focuses on safe conversion; cursor encoding belongs at the delivery boundary.

```sql
-- PostgreSQL, descending compound cursor (all values are bound parameters)
SELECT id, name, published_at
FROM courses
WHERE (published_at, id) < ($1, $2)
ORDER BY published_at DESC, id DESC
LIMIT $3;
```

The cursor should encode both `$1` and `$2`; the delivery boundary decodes and validates it before constructing the Criteria. For ascending order, reverse the comparison consistently. Other databases may require the equivalent expanded predicate: `published_at < $1 OR (published_at = $1 AND id < $2)`.

**Client usage — reading the next page (pseudocode; names depend on the delivery adapter):**
```text
// First page: no cursor
const page1 = CompoundCursorCriteria.descending(
  [], ["published_at", "id"], 20, null,
);

// Next page: cursor includes every ordered field.
const last = results.at(-1);
if (last !== undefined) {
  const cursor = encodeAndSignCursor({ publishedAt: last.publishedAt, id: last.id });
  const page2 = CompoundCursorCriteria.descending(
    [], ["published_at", "id"], 20, cursor,
  );
}
```

**Practical heuristic:** Use offset pagination by default. Switch to cursor pagination only when the collection is large and high-write, or when "infinite scroll" UX requires stable results between fetches. Cursor pagination requires a mandatory `orderBy` — enforce this at construction time (as the course does).

---

## Testing Criteria-Based Repositories

**Intent:** Verify that a `Criteria` produces the correct results without coupling tests to SQL strings.

**How it works:** Write tests against the in-memory fake repository that implements the same `Criteria`-based filtering in memory (useful for unit tests), plus integration tests against the real database implementation. The Criteria objects themselves are Value Objects and can be equality-tested directly.

**Example:**
```typescript
// Unit test — Criteria construction and filtering
it("filters courses by status", async () => {
  const repo = new InMemoryCourseRepository();
  await repo.save(aCourseWith({ id: "1", status: "published" }));
  await repo.save(aCourseWith({ id: "2", status: "draft" }));

  const criteria = Criteria.fromPrimitives(
    [{ field: "status", operator: "=", value: "published" }],
    null, null, null, null,
  );

  const results = await repo.matching(criteria);
  expect(results).toHaveLength(1);
  expect(results[0].id.value).toBe("1");
});
```

**Practical heuristic:** Integration-test every supported operator and pagination strategy against the real database, including injection attempts and tied cursor fields. Use an in-memory implementation for fast application tests, but do not treat it as proof of SQL conversion, collation, null ordering, constraints, or transaction behavior.

---

## Related Patterns

- **Specification** (Evans DDD): Criteria is a generalization of Specification that adds sorting and pagination to the predicate concept. Use Specification for boolean pass/fail checks within the domain; use Criteria for repository queries.
- **Repository**: The natural consumer of Criteria — the `matching(criteria)` method replaces ad-hoc query methods.
- **Query Object** (PoEAA Fowler): Criteria is a domain-idiomatic Query Object — same structural idea but expressed in domain terms rather than raw SQL fragments.
