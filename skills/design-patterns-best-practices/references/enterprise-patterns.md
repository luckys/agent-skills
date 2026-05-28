# Enterprise Application Patterns

Patterns from Martin Fowler's *Patterns of Enterprise Application Architecture* (PoEAA), organized by category. Use these when building layered enterprise applications with domain logic, database access, and web presentation concerns.

## How to Use This Reference

- Start with the **Domain Logic** section to decide the architecture tier.
- Move to **Data Source** patterns to choose the database access strategy.
- Use **ORM Behavioral** patterns to solve loading and caching issues.
- Use **ORM Structural/Metadata** patterns for inheritance and complex mapping.
- Use **Web Presentation** patterns to organize the HTTP layer.
- Use **Distribution and Concurrency** patterns for remote access and locking.
- Use **Base Patterns** for cross-cutting utilities.

---

## Domain Logic Patterns

## Transaction Script

**Category:** Domain Logic

**Intent:** Organizes business logic as a single procedure per transaction, making calls directly to the database or through a thin database wrapper.

**How it works:** Each user request or business transaction maps to one procedure that gets input, queries the database, munges the data, and saves results. Scripts are kept in classes separate from presentation and data source concerns. Common subtasks can be broken into subprocedures shared across scripts. The pattern has no notion of shared state between transactions — each script operates independently.

**When to use:**
- Applications with simple, low-volume business logic where the overhead of a Domain Model is not justified
- Small systems where getting up and running quickly matters more than long-term extensibility
- Teams unfamiliar with OO domain modeling who need a predictable, procedural structure

**When NOT to use:**
- Business logic is complex, with many rules, validations, calculations, and derivations that grow over time — duplication between scripts becomes increasingly hard to control

**Key trade-off:** Simplicity and low overhead vs. rapid degradation into duplicated, hard-to-maintain code as business complexity grows.

**Related patterns:** Domain Model (richer alternative for complex domains), Table Module (table-oriented middle ground), Service Layer (can wrap Transaction Scripts to expose a uniform boundary)

**Practical heuristic:** If you find yourself copy-pasting logic between transaction procedures, it is time to migrate toward a Domain Model.

---

## Domain Model

**Category:** Domain Logic

**Intent:** An object model of the domain that incorporates both data and behavior, creating a web of interconnected objects where each object represents a meaningful business concept.

**How it works:** A whole layer of objects mirrors the business area, combining data and process so that behavior clusters close to the data it operates on. A simple Domain Model has roughly one class per database table and can use Active Record for persistence. A rich Domain Model introduces inheritance, strategies, and complex object graphs, requiring a Data Mapper to keep the model independent of the database. The domain layer is kept maximally decoupled from other layers so it can be built, modified, and tested independently.

**When to use:**
- Business logic is complicated, with many rules, validations, calculations, and derivations that would produce painful duplication in procedural scripts
- The team is comfortable with OO design and willing to invest in learning the paradigm — the payoff scales with domain complexity
- Long-lived applications where the domain will keep evolving and extensibility through patterns (Strategy, Composite, etc.) is valuable

**When NOT to use:**
- Simple domains with only a few not-null checks and basic sums — a Transaction Script gets you running faster with less overhead
- Teams with no OO experience and no time for the paradigm shift

**Key trade-off:** Maximum expressiveness and extensibility for complex rules vs. significant upfront investment in design and a harder database-mapping problem.

**Related patterns:** Transaction Script (simpler procedural alternative), Table Module (table-oriented alternative), Data Mapper (preferred persistence mechanism for rich models), Active Record (usable for simple models), Service Layer (adds a distinct API boundary around the Domain Model)

**Practical heuristic:** Choose Domain Model when the business rules are complex enough that you would need to duplicate logic across Transaction Scripts — the complexity is the signal.

---

## Table Module

**Category:** Domain Logic

**Intent:** A single class instance handles all business logic for all rows in a database table or view, working directly against a table-oriented data structure (Record Set).

**How it works:** One class per table holds every procedure that acts on that table's data; instead of object identity, operations receive a primary key to identify which row to work with. The backing data structure is typically a Record Set (the result of a SQL query kept in memory), and multiple Table Modules can collaborate on the same Record Set. Because the data structure is table-oriented, it flows naturally into table-aware UI widgets without translation. Table Modules may be instances (initialized with a Record Set) or static method collections; the instance form allows inheritance to extend behavior.

**When to use:**
- The application is built around table-oriented data (e.g., ADO.NET / .NET DataSet ecosystem) and the UI widgets consume Record Sets directly
- Business logic is moderate — enough to need encapsulation above raw SQL, but not so complex that it demands instance-per-row polymorphism
- You want to package domain behavior with the data structure while keeping close integration with the relational database

**When NOT to use:**
- Domain logic is complex enough to require direct instance-to-instance relationships or polymorphism — Table Module cannot express these well, making Domain Model the better choice

**Key trade-off:** Easy integration with table-oriented data structures and platforms vs. inability to use object identity, polymorphism, or fine-grained inter-object relationships for complex logic.

**Related patterns:** Domain Model (richer OO alternative when complexity demands it), Record Set (the data structure Table Module operates on), Active Record (alternative when Domain Model objects map closely to tables), Table Data Gateway (often used alongside to assemble the Record Set)

**Practical heuristic:** Use Table Module when your platform's primary data currency is a Record Set (e.g., .NET DataSet) and most logic is per-table rather than per-instance.

---

## Service Layer

**Category:** Domain Logic

**Intent:** Defines an application's boundary with a layer of services that establishes a set of available operations and coordinates the application's response — including transactions, notifications, and integration — in each operation.

**How it works:** The Service Layer sits between client layers (UIs, data loaders, integration gateways) and the domain/data-source layers, encapsulating application logic (workflow, notifications, cross-resource transactions) while delegating pure domain logic to the Domain Model beneath. It can be implemented as a **domain facade** — thin classes that simply delegate all logic to the Domain Model — or as **operation scripts** — thicker classes that implement application logic directly and call domain objects for domain rules. Each service class groups related operations and its methods correspond closely to use cases. Operations are transacted atomically across all resources they touch.

**When to use:**
- The application has more than one kind of client (UI, batch loader, integration gateway) that needs to invoke the same business logic through a consistent, coarse-grained API
- Use case responses involve multiple transactional resources that must be coordinated atomically
- Application logic (notifications, messaging, integration calls) must be separated from pure domain logic to keep domain objects reusable across applications

**When NOT to use:**
- The application has only one kind of client and its use case responses do not involve multiple transactional resources — Page Controllers can manage transactions directly, and the extra layer adds complexity without benefit

**Key trade-off:** A clean, reusable application boundary with centralized transaction control vs. an extra architectural layer that adds indirection and design effort.

**Related patterns:** Domain Model (the layer Service Layer typically delegates domain logic to), Transaction Script (alternative when there is no Domain Model), Remote Facade (can be layered on top of Service Layer to add remotability), Data Transfer Object (needed when Service Layer is accessed remotely)

**Practical heuristic:** Add a Service Layer as soon as you anticipate a second kind of client or a second transactional resource in use case responses — retrofitting it later is harder than designing it in from the start.

---

## Data Source Patterns

---

## Table Data Gateway

**Category:** Data Source Architectural

**Intent:** Centralizes all SQL for a single database table or view into one object whose methods the rest of the application calls for all database interaction with that table.

**How it works:** A Table Data Gateway holds find, insert, update, and delete methods for one table (or view). Each method maps its arguments directly into a SQL call and executes it against a connection. The gateway is typically stateless. Results are returned as a Record Set, a Data Transfer Object, or a raw data structure — never as domain objects from inside the gateway itself. One gateway instance serves all rows; there is no per-row instance.

**When to use:**
- Building with a Table Module or Transaction Script where domain logic is thin and a table-centric data structure (Record Set) is a natural fit.
- You want all SQL for a table in one place so DBAs can find and tune it without reading business logic code.
- Stored procedures naturally map to gateway methods, making this a good encapsulation point for procedure-based data access.

**When NOT to use:**
- Your domain model is complex and diverges from the relational schema — Data Mapper gives better isolation in that case.
- You need domain objects to be completely ignorant of database structure; Table Data Gateway creates bidirectional coupling when it returns domain objects.

**Key trade-off:** Simplicity and centralized SQL control versus tight coupling to the table structure, which makes it harder to evolve the schema independently of the domain model.

**Related patterns:** Row Data Gateway (row-level variant), Table Module (natural consumer of its Record Set), Data Mapper (preferred alternative when using Domain Model), Transaction Script (natural pairing).

**Practical heuristic:** Prefer Table Data Gateway when your primary domain pattern is Table Module; switch to Data Mapper the moment your domain model starts diverging from your schema.

---

## Row Data Gateway

**Category:** Data Source Architectural

**Intent:** Provides an object that exactly mirrors a single database record, hiding all data-source access details behind a record-shaped interface, with one instance per row returned from a query.

**How it works:** A Row Data Gateway acts as a thin wrapper around one database row: each column becomes one field with getters and setters. A separate Finder object (or static find methods) executes queries and instantiates one gateway object per row. The gateway itself handles insert, update, and delete for its row but contains no domain logic — only database access and simple type conversion. It is often used as a data holder that a domain object delegates to for its field storage.

**When to use:**
- Using Transaction Script where you want database access factored out cleanly so multiple scripts can share the same access code.
- You want a strong candidate for code generation because the gateway mirrors the table structure exactly.
- You want to shield domain objects from direct SQL while keeping domain logic in separate scripts, not in the gateway itself.

**When NOT to use:**
- Using a Domain Model — Active Record handles simple cases without the extra layer, and Data Mapper handles complex cases with better decoupling.
- Mapping is complex enough that you would end up with three representations of the same data (business logic, gateway, database), which is one too many.

**Key trade-off:** Clean separation of database access from business code versus an extra object layer that adds complexity without adding much over Active Record for simple domain models.

**Related patterns:** Table Data Gateway (table-level alternative), Active Record (adds domain logic to the same structure), Data Mapper (preferred when domain diverges from schema), Metadata Mapping (good basis for code-generating Row Data Gateways).

**Practical heuristic:** If you notice business logic migrating into your Row Data Gateway, stop and rename it Active Record — that is exactly the natural evolution Fowler describes.

---

## Active Record

**Category:** Data Source Architectural

**Intent:** Wraps a database row in a domain object that carries both the data and the domain logic operating on it, and knows how to save and load itself from the database.

**How it works:** An Active Record class mirrors one database table or view: each column maps to one field. The class provides static finder methods that execute SQL and construct Active Record instances, instance methods for insert/update/delete, getters/setters with optional type conversion, and methods implementing domain logic directly in the same class. The database structure and the object structure are intentionally isomorphic (one-to-one). Foreign keys may be left as raw values or resolved to related Active Record objects on demand.

**When to use:**
- Domain logic is not too complex — primarily CRUD operations, simple validations, and derivations based on a single record.
- Your schema is under your control and can stay in sync with your object model (isomorphic schema).
- You are transitioning from Transaction Script and want to start adding behavior incrementally without the overhead of a full mapping layer.

**When NOT to use:**
- Business logic is complex enough to need inheritance hierarchies, collections, and rich associations — these do not map cleanly to Active Record and force you toward Data Mapper.
- You need to evolve the schema and the object model independently; Active Record's direct coupling makes refactoring both harder.

**Key trade-off:** Simplicity and low ceremony versus tight coupling between the object design and the database design, which constrains both as the application grows.

**Related patterns:** Row Data Gateway (structurally identical but without domain logic), Data Mapper (next step when Active Record becomes too coupled), Domain Model (Active Record is one implementation strategy for a Domain Model).

**Practical heuristic:** Start with Active Record for simple domains; when you find yourself working around the database schema to express domain concepts, that is the signal to refactor toward Data Mapper.

---

## Data Mapper

**Category:** Data Source Architectural

**Intent:** Provides a layer of Mapper objects that moves data between in-memory domain objects and a relational database while keeping both completely independent of each other and of the mapper itself.

**How it works:** A Data Mapper is a separate object — not a domain object, not a table — responsible for all SQL needed to load and save a domain class. Domain objects have no knowledge of the database schema or of SQL; the database schema has no knowledge of the objects. When loading, the mapper checks an Identity Map first (to avoid duplicates and extra queries), then queries the database and constructs a domain object. When saving, it reads data from the domain object and issues the appropriate INSERT or UPDATE. Finders are often exposed through a Separated Interface so the domain layer can invoke them without depending on the mapper package. A Unit of Work typically orchestrates when mappers are called at commit time.

**When to use:**
- Using a Domain Model whose object schema diverges significantly from the relational schema (inheritance, complex associations, value objects).
- You need to be able to modify the domain model and the database schema independently — for example when working with a legacy database.
- You want domain objects to be testable without a database, because the mapper layer is the only place the database is referenced.

**When NOT to use:**
- Domain logic is simple and the schema is isomorphic — Active Record provides the same result with far less infrastructure.
- You are on a tight timeline and cannot afford to build or procure a mapping layer; for simple cases Active Record is a perfectly valid shortcut.

**Key trade-off:** Maximum decoupling between domain and database (enabling independent evolution of both) versus significant additional complexity — the mapper layer is the most complex of the four data source patterns.

**Related patterns:** Active Record (simpler alternative for isomorphic schemas), Unit of Work (coordinates when mapper writes happen), Identity Map (prevents duplicate object loading within a session), Lazy Load (controls how much related data the mapper pulls in one go), Metadata Mapping (drives mapper configuration from data rather than code).

**Practical heuristic:** Never choose Data Mapper without also choosing Domain Model; and if your Domain Model is simple enough for Active Record, use Active Record — Data Mapper pays off only when the complexity of the domain justifies the extra layer.

---

## Unit of Work

**Category:** ORM Behavioral

**Intent:** Maintains a list of all objects affected by a business transaction and coordinates writing changes to the database — and resolving concurrency problems — in a single commit at the end of the transaction.

**How it works:** As a business transaction begins, a Unit of Work object is created. Every object that is read is registered as "clean"; every object that is created is registered as "new"; every object whose state is mutated is registered as "dirty"; every object that is deleted is registered as "removed." Application code never calls database methods directly. At commit time, the Unit of Work opens a database transaction, performs concurrency checks (optimistic or pessimistic), and issues the minimum set of SQL statements needed — in the correct dependency order — to persist all changes. Two registration strategies exist: caller registration (the calling code explicitly registers changes) and object registration (the domain objects register themselves via setter hooks or load-time instrumentation).

**When to use:**
- Using a Domain Model or any pattern where many objects can change during a single business transaction and you need a single atomic commit.
- You need to minimize database round-trips by batching all writes into one transaction at the end.
- You need to handle referential integrity ordering automatically or manage optimistic/pessimistic locking across a session.

**When NOT to use:**
- Your interaction with the database is simple enough that explicitly saving each changed object one at a time is manageable — a valid approach for simple Transaction Script work.
- Every change in the session is immediately written to the database and you have a long-open database transaction covering the whole request (acceptable only for very short, simple requests).

**Key trade-off:** Clean, centralized change tracking and atomic commit versus the complexity of maintaining registration discipline — forgetting to register a changed object means the change is silently lost.

**Related patterns:** Data Mapper (Unit of Work calls mappers at commit time), Identity Map (usually lives inside the Unit of Work), Optimistic Offline Lock / Pessimistic Offline Lock (concurrency strategies coordinated at commit time), Domain Model (primary beneficiary of Unit of Work).

**Practical heuristic:** Embed the Unit of Work in the session or request scope and use object registration (setter-based) rather than caller registration — it removes the burden from calling code and makes silent-miss bugs impossible.

---

## Identity Map

**Category:** ORM Behavioral

**Intent:** Ensures that each database record is loaded into memory only once per business transaction by keeping every loaded object in a keyed map and consulting the map before hitting the database.

**How it works:** An Identity Map is a dictionary keyed by primary key, maintained for the duration of a session or business transaction. Before any finder issues a SQL query, it checks the map; if the object is already there, it is returned directly without a database round-trip. When an object is freshly loaded, it is immediately placed in the map. This prevents two different in-memory objects from representing the same database row, which would lead to conflicting updates. One map per class (or per inheritance root) is the common structure; a single session-wide map works if database keys are globally unique. The Identity Map is best stored inside the Unit of Work if one is present; otherwise a session-scoped Registry.

**When to use:**
- Any time you are loading domain objects from a database within a session and those objects can be modified — you need the guarantee that there is at most one in-memory instance per record.
- As a performance optimization: acting as a transaction-scoped cache to avoid redundant database reads for the same record within a request.
- When using Data Mapper, where the mapper infrastructure naturally owns and consults the map during load.

**When NOT to use:**
- Immutable Value Objects — since they cannot be modified, duplicate instances cause no consistency problem, and you do not need the overhead of the map (though a cache can still help performance).
- Dependent objects whose lifecycle is controlled entirely by their parent (Dependent Mapping) — identity is managed by the parent and an additional map adds no value.

**Key trade-off:** Correctness guarantee (no duplicate mutable instances) and a performance bonus (cache hits) versus the added complexity of maintaining the map and ensuring it is properly scoped to the session, not shared across sessions.

**Related patterns:** Unit of Work (natural home for Identity Maps), Data Mapper (always uses Identity Map during loading), Optimistic Offline Lock (Identity Map helps detect stale reads within a session), Registry (fallback location for the map if no Unit of Work is present).

**Practical heuristic:** Place your Identity Maps inside your Unit of Work; if you have no Unit of Work, tie them to the session object — never let them be process-wide unless the objects are guaranteed read-only.

---

## Lazy Load

**Category:** ORM Behavioral

**Intent:** Marks a field or association on a domain object so that its data is not fetched from the database when the object is first loaded, but only when that field is actually accessed.

**How it works:** Four implementation strategies exist. (1) **Lazy initialization**: the getter checks if the field is null and loads it on first access — simple but introduces a dependency on the data source from within the domain object. (2) **Virtual proxy**: a stand-in object that looks like the real object but defers loading until one of its methods is called — transparent to callers but introduces identity hazards (the proxy and the real object are not `==` equal). (3) **Value holder**: a generic wrapper object whose `getValue()` triggers the load on first call — the domain class must be aware a value holder is in play. (4) **Ghost**: the real object is created immediately but in a "ghost" (partially loaded) state containing only its ID; any field access triggers a full load of all fields at once. Ghosts avoid identity problems and integrate well with Identity Map.

**When to use:**
- An association or collection is large and expensive to load, but frequently not needed for the current use case (e.g., loading an Order without immediately needing all its OrderLines).
- The data lives in a separate table that requires an additional SQL query, making eager loading costly when the data is often unused.
- You have multiple distinct use-case profiles requiring different subgraphs of the object graph.

**When NOT to use:**
- The field is stored in the same database row as the rest of the object — it is almost always free to load it eagerly.
- You risk "ripple loading": iterating a lazily-loaded collection and triggering one database call per element instead of a single bulk query. Prefer making the collection itself a single Lazy Load that fetches all its contents at once.
- Your codebase is simple enough that the extra complexity is not justified — Fowler's preference is to avoid Lazy Load unless he has a specific performance reason.

**Key trade-off:** Avoiding unnecessary database round-trips and memory consumption versus added complexity, the risk of N+1 query problems (ripple loading), and the intrusive changes to domain objects required by some implementations.

**Related patterns:** Data Mapper (most natural host for installing Lazy Load behavior), Identity Map (ghost implementation registers immediately into the map to maintain identity), Virtual Proxy / Ghost (specific implementation forms).

**Practical heuristic:** Default to eager loading; add Lazy Load only when a profiler shows that a specific association is causing measurable unnecessary database calls — and when you add it, load the entire collection at once to avoid ripple loading.

---

## ORM Structural Patterns

---

## Identity Field

**Category:** ORM Structural

**Intent:** Save a database primary key field in an in-memory object to maintain the correspondence between the object and its database row.

**How it works:** Every domain object holds a field storing the primary key of its corresponding database row. When loading from the database the mapper reads the key column and stores it in this field; when inserting, the mapper reads the field to generate the INSERT. The key can be a simple integer, a GUID, or a compound key object. Key generation strategies include database auto-increment, a shared key table, or a GUID generator.

**When to use:**
- You are using Domain Model or Row Data Gateway and need to write objects back to the database.
- You need to correlate in-memory objects with database rows for update, delete, or association traversal.

**When NOT to use:**
- Simple value objects (money, date range) that map via Embedded Value and never have their own table row.
- Objects whose graph is so complex it is better serialised as a Serialized LOB — no row identity needed.

**Key trade-off:** Meaningful keys (e.g. SSN) are readable but fragile; meaningless surrogate keys are robust but opaque. Database-unique keys simplify Identity Map but require cross-table uniqueness management.

**Related patterns:** Identity Map (uses the Identity Field value as its lookup key), Embedded Value (alternative for small value objects), Serialized LOB (alternative for complex object graphs), Concrete Table Inheritance (requires hierarchy-wide key uniqueness).

**Practical heuristic:** Default to a database-unique auto-generated long integer; only reach for GUIDs when you need key generation before the INSERT, or for distributed systems.

---

## Foreign Key Mapping

**Category:** ORM Structural

**Intent:** Map an object association to a foreign key in the database by storing the related object's Identity Field as a column in the owning table.

**How it works:** When an object holds a reference to another object, the mapper stores the referenced object's primary key as a foreign key column in the owning table. On load, the mapper reads the foreign key, looks up the referenced object (possibly via Identity Map), and sets the reference. On save, it writes the referenced object's key back into the foreign key column. Collections (one-to-many) are handled by placing the foreign key on the "many" side table.

**When to use:**
- Mapping a single-valued object reference (many-to-one or one-to-one) to a relational table.
- Mapping a one-to-many collection where the "many" side can carry a back-reference foreign key.

**When NOT to use:**
- Many-to-many associations — use Association Table Mapping instead.
- When the referenced objects have no identity of their own — use Embedded Value or Dependent Mapping.

**Key trade-off:** Loading related objects on demand avoids unnecessary queries but risks N+1 query problems; eager loading via JOIN is efficient but may load data that is not needed.

**Related patterns:** Association Table Mapping (for many-to-many), Dependent Mapping (for owned value-like objects), Identity Map (avoids duplicate object creation during foreign key resolution), Lazy Load (defers loading of referenced objects).

**Practical heuristic:** For single-valued references, put the foreign key on the side that "owns" the relationship; always check the Identity Map before issuing a SELECT for the referenced object to prevent redundant database hits.

---

## Association Table Mapping

**Category:** ORM Structural

**Intent:** Map a many-to-many association between two classes by introducing a dedicated link table that holds foreign keys to both associated tables.

**How it works:** A separate join table (link table) holds two foreign key columns, one for each end of the association. Each row in the link table represents one association instance. When loading, the mapper queries the link table and reconstructs the in-memory collections. When saving, it compares the current in-memory collection against the persisted link rows, deleting removed associations and inserting new ones.

**When to use:**
- Two domain classes have a many-to-many relationship that cannot be represented by a single foreign key on either table.
- The association itself carries no extra attributes (if it does, promote it to its own domain class with Foreign Key Mapping on both sides).

**When NOT to use:**
- The relationship is actually one-to-many — Foreign Key Mapping is simpler and avoids the join table overhead.
- The association has attributes of its own — model it as an explicit association class instead.

**Key trade-off:** The link table is pure database infrastructure with no corresponding domain class, which keeps the domain model clean but requires additional mapper logic and an extra table join on every load.

**Related patterns:** Foreign Key Mapping (simpler alternative for one-to-many), Dependent Mapping (when one side owns the other completely).

**Practical heuristic:** If the link table ever needs an extra column (e.g. a date or a quantity), stop using Association Table Mapping and introduce a proper domain class for the association with two Foreign Key Mappings.

---

## Dependent Mapping

**Category:** ORM Structural

**Intent:** Have one class perform the database mapping for a child class whose lifecycle is entirely controlled by a single owning object, so the child has no independent identity or mapper.

**How it works:** The owner's mapper is responsible for loading, inserting, updating, and deleting the dependent objects. Dependents are identified only through their owner; they do not need their own Identity Field for in-memory use (though the database row may still carry a key). When the owner is saved, the mapper deletes all existing dependent rows and re-inserts the current collection, or performs a diff and issues targeted updates and deletes.

**When to use:**
- A child object only ever belongs to one parent and has no meaningful existence outside that parent (e.g. line items belonging to an order when there is no other reference to them).
- You want to avoid the complexity of a full mapper and Identity Map for objects that are always loaded together with their parent.

**When NOT to use:**
- The child can be referenced from more than one parent — it needs its own identity and mapper.
- You need to query for child objects independently of their parent.

**Key trade-off:** Simplifies the mapping layer by eliminating a separate mapper and Identity Map for the child, but the delete-all-and-reinsert approach can be costly for large collections and loses fine-grained change tracking.

**Related patterns:** Foreign Key Mapping (the more general pattern when children have independent identity), Identity Map (not needed for dependents), Embedded Value (for dependents that collapse into the parent's own row).

**Practical heuristic:** Use Dependent Mapping when you always load the child collection with its parent and the collection is small enough that a full delete-and-reinsert is acceptable; switch to Foreign Key Mapping the moment another object needs to reference the child directly.

---

## Embedded Value

**Category:** ORM Structural

**Intent:** Map the fields of a small value object into columns of its owner's table rather than giving the value object its own table row.

**How it works:** The columns that would belong to the value object (e.g. amount and currency for a Money object, or startDate and endDate for a DateRange) are stored as additional columns in the owning table's row. The owner's mapper reads these columns and constructs the value object when loading, and writes the value object's fields back to those columns when saving. The value object has no Identity Field.

**When to use:**
- The object is a true value object — immutable, no identity, always accessed through its owner (e.g. Money, Address, DateRange, Quantity).
- The value object's data is always needed whenever the owner is needed, so no lazy loading or separate query is required.

**When NOT to use:**
- Multiple owners need to share or reference the same value object instance with its own key.
- The value object is complex enough that it warrants its own query, reporting view, or independent lifecycle.

**Key trade-off:** Eliminates a join and simplifies the schema, but the owner's table grows wider, and if the value object structure is shared across many owners the column definitions are duplicated.

**Related patterns:** Serialized LOB (when the value object graph is too complex for column-per-field), Foreign Key Mapping (when the embedded object must become a proper entity), Dependent Mapping (similar intent but the child has its own row).

**Practical heuristic:** Embed when the value object has three or fewer simple fields that are always loaded with the owner; reach for Serialized LOB once the structure becomes a graph, and for a separate table once it needs its own identity.

---

## Serialized LOB

**Category:** ORM Structural

**Intent:** Save a graph of objects into a single large object field (LOB) in the database by serialising the entire graph to XML, JSON, or binary, stored in one column.

**How it works:** The mapper serialises an object graph (or a complex value) into a text or binary representation and stores it in a single CLOB/BLOB/TEXT/JSONB column in the owner's row. On load the mapper reads the column and deserialises the graph back into in-memory objects. The internal structure of the graph is invisible to the database and cannot be queried via SQL.

**When to use:**
- The object graph is complex (deeply nested or highly variable) and does not need to be queried at the field level by the database.
- Mapping every node of the graph to its own table would produce an unmanageable number of tables and joins.

**When NOT to use:**
- Individual fields inside the graph must be filterable or sortable in SQL queries.
- The serialised data must be readable or reportable by tools outside the application.

**Key trade-off:** Dramatically reduces schema complexity and eliminates joins, but completely sacrifices database-level queryability and referential integrity for the serialised content.

**Related patterns:** Embedded Value (lighter alternative when the structure is flat and small), Foreign Key Mapping (when parts of the graph need relational identity), Metadata Mapping (can describe which fields are LOBs).

**Practical heuristic:** Use Serialized LOB for hierarchical configuration, preference trees, or document-like structures that are always loaded and saved as a whole; never use it for data that a DBA or reporting query will ever need to filter on.

---

## Single Table Inheritance

**Category:** ORM Structural

**Intent:** Represent an entire inheritance hierarchy of classes with a single database table that has a column for every field of every class in the hierarchy, plus a type discriminator column.

**How it works:** One table holds all rows for all classes in the hierarchy. A type-code column indicates which concrete class each row represents. Columns belonging to fields of subclasses are null for rows of other classes. The mapper reads the type code to determine which domain object to instantiate, then loads only the relevant columns.

**When to use:**
- The inheritance hierarchy is shallow and the subclasses differ by only a few fields, so the number of null columns stays manageable.
- You want the simplest possible SQL — all data in one table, no joins needed.
- You frequently query across the whole hierarchy (polymorphic queries are a single SELECT).

**When NOT to use:**
- Subclasses have many unique fields, leading to a wide table mostly filled with nulls.
- Database-level NOT NULL constraints are important for subclass-specific fields (nullability cannot be enforced).

**Key trade-off:** Maximum query simplicity and no joins, but the table becomes wide and sparse as the hierarchy grows, and schema intent is obscured because many columns are irrelevant for most rows.

**Related patterns:** Class Table Inheritance (one table per class), Concrete Table Inheritance (one table per concrete class), Inheritance Mappers (the mapper structure that sits above all three strategies).

**Practical heuristic:** Start with Single Table Inheritance when first mapping a hierarchy; switch to Class Table or Concrete Table Inheritance only when the null-column sprawl or integrity concerns become a real problem.

---

## Class Table Inheritance

**Category:** ORM Structural

**Intent:** Represent an inheritance hierarchy of classes with one database table per class, where each table holds only the fields defined by that class.

**How it works:** There is one table for each class in the hierarchy. The superclass table holds fields common to all classes; each subclass table holds only the fields introduced by that subclass. Rows are linked by sharing the same primary key value across tables, or by a foreign key from the subclass table to the superclass table. Loading an object requires joining all relevant tables (or multiple queries), and the mapper assembles the full object from the combined result.

**When to use:**
- The domain model has a clear, well-understood inheritance hierarchy and you want the schema to mirror it closely.
- Many subclass fields must carry NOT NULL constraints or foreign key references that Single Table Inheritance cannot enforce.
- Reporting or DBA tooling needs to query each class independently.

**When NOT to use:**
- The hierarchy is deep — each load requires joining many tables, which degrades performance.
- Polymorphic queries across the hierarchy are common and the multiple joins make them too slow.

**Key trade-off:** The cleanest schema-to-model correspondence and best support for relational integrity, but every object load requires multiple table accesses and the supertype table becomes a hotspot.

**Related patterns:** Single Table Inheritance (simpler, no joins), Concrete Table Inheritance (no joins but duplicates superclass columns), Inheritance Mappers (organises the mapper code for all three strategies).

**Practical heuristic:** Use Class Table Inheritance when the hierarchy is stable, shallow (two or three levels), and the schema needs to be legible and integrity-enforced by the database; avoid it when polymorphic searches dominate.

---

## Concrete Table Inheritance

**Category:** ORM Structural

**Intent:** Represent an inheritance hierarchy by giving each concrete class its own table that contains columns for all fields of that class including all inherited superclass fields.

**How it works:** Each concrete (non-abstract) class maps to exactly one table containing all the columns it needs — both its own fields and the duplicated fields from every superclass. There is no superclass table. Objects are loaded from a single table without joins. The trade-off is that superclass fields are physically duplicated across all subclass tables, and finding all instances of an abstract supertype requires querying every concrete table.

**When to use:**
- You need the fastest possible single-table reads for concrete subclass objects (no joins).
- The inheritance hierarchy is wide and flat (few levels of inheritance) with distinct, self-contained subclasses.
- Each concrete table is accessed by systems that don't know about the hierarchy and need a self-contained schema.

**When NOT to use:**
- Polymorphic queries across the full hierarchy are common — they require querying every concrete table with a UNION or multiple round trips.
- Referential integrity to the abstract superclass is required — there is no superclass table to reference.
- Superclass fields change frequently — every change must be propagated to all concrete tables.

**Key trade-off:** Excellent read performance for known concrete types with no joins, but primary key uniqueness must be enforced across all concrete tables by the application (the database cannot enforce it), and polymorphic queries are expensive.

**Related patterns:** Single Table Inheritance (one table, simplest queries), Class Table Inheritance (one table per class, cleanest schema), Inheritance Mappers (the organising structure for all three strategies).

**Practical heuristic:** Prefer Concrete Table Inheritance when subclass tables are accessed by external tools or reports that need self-contained, all-columns tables; always use database-unique (hierarchy-wide) keys rather than table-unique keys to avoid identity collisions across the hierarchy.

---

## Inheritance Mappers

**Category:** ORM Structural

**Intent:** Organise a family of mapper classes into a hierarchy that mirrors the domain class hierarchy so that each mapper handles only the fields of its own class while delegating to superclass mappers for inherited fields.

**How it works:** There is one concrete mapper for each concrete domain class in the hierarchy and one abstract mapper for each abstract domain class. Each concrete mapper's `load` method loads only the fields defined by its class, then calls `super.load()` to let the superclass mapper load the inherited fields — building the object cooperatively up the inheritance chain. Similarly, `save` delegates upward. A separate "interface mapper" for the abstract superclass provides `find`, `insert`, and `update` operations; these delegate to the correct concrete mapper based on a type code or runtime type inspection.

**When to use:**
- Any time you are mapping an inheritance hierarchy to a relational database using Single Table, Class Table, or Concrete Table Inheritance — the structural organisation of the mappers is the same regardless of which table strategy is chosen.
- You want to avoid duplicating superclass field mapping code across every concrete mapper.

**When NOT to use:**
- There is no inheritance in the domain model — the pattern is unnecessary complexity for flat class structures.

**Key trade-off:** Centralises superclass field mapping and eliminates duplication, but the two-class structure (abstract player mapper + interface player mapper) is conceptually subtle and easy to confuse.

**Related patterns:** Single Table Inheritance, Class Table Inheritance, Concrete Table Inheritance (Inheritance Mappers is the mapper-organisation layer on top of all three), Layer Supertype (provides a common base for all mappers).

**Practical heuristic:** Always implement Inheritance Mappers when you have a hierarchy of three or more classes; the small up-front cost of structuring the mapper hierarchy eliminates a large amount of duplicated field-mapping code in every concrete subclass mapper.

---

## Metadata Mapping

**Category:** ORM Metadata Mapping

**Intent:** Hold the details of how object fields correspond to database columns in a metadata structure (a data map), and use generic code driven by that metadata to perform all reading, inserting, and updating, eliminating repetitive hand-written mapping code.

**How it works:** A `DataMap` object describes a domain class: which table it maps to, and a list of `ColumnMap` entries that pair each database column name with the corresponding object field name. Generic mapper code reads the `DataMap` at runtime and uses either reflection (to set/get fields dynamically) or code generation (to produce explicit mapper classes at build time) to carry out all CRUD operations. Mappers become trivial: they define their `DataMap` and inherit all database behaviour from the generic superclass.

**When to use:**
- You have a large number of classes to map and the hand-written field-by-field mapping code is repetitive and error-prone.
- You want database schema changes to be reflected by changing a single metadata file rather than hunting for every affected mapper method.
- You are building a reusable O/R mapping framework (all commercial ORM tools are built this way).

**When NOT to use:**
- You have very few classes to map — the setup cost of the metadata framework exceeds the benefit.
- Reflection-based access causes a measurable performance problem in your environment and code generation is not practical.

**Key trade-off:** Reduces mapper boilerplate dramatically and centralises schema change impact, but breaks automated refactoring tools (renaming a field does not update string-based metadata), and special-case mappings must be handled by overriding the generic code in subclass hooks.

**Related patterns:** Query Object (works with Metadata Mapping to translate field names to column names in generated SQL), Repository (uses Metadata Mapping to generate queries from criteria), Data Mapper (the architectural layer that Metadata Mapping makes generic).

**Practical heuristic:** Prefer Metadata Mapping once you have more than five or six classes to map; keep a subclass override hook for each mapper so that the 10% of mappings that don't fit the generic model can be handled without polluting the metadata with special-case flags.

---

## Query Object

**Category:** ORM Metadata Mapping

**Intent:** Represent a database query as an object — a tree of Criteria objects that can be built up programmatically using field names rather than column names, and that generates the appropriate SQL string when executed.

**How it works:** A `QueryObject` holds the domain class it targets and a collection of `Criteria` objects. Each `Criterion` encapsulates a SQL operator (e.g. `=`, `>`, `LIKE`), a field name on the domain object, and a value. When executed, the `QueryObject` translates field names to database column names (using Metadata Mapping), combines the criteria into a WHERE clause, issues the SQL query, and returns domain objects. Clients compose queries in terms of object fields rather than table columns, so they are insulated from schema changes.

**When to use:**
- You are using Domain Model and Data Mapper and need flexible, ad-hoc querying without scattering SQL strings throughout the codebase.
- Metadata Mapping is already in place and you want to encapsulate schema knowledge in one location.
- Multiple databases or schemas must be supported and the SQL dialect must be abstracted.

**When NOT to use:**
- Your data source layer is handwritten and simple — specialised finder methods on mappers are sufficient and easier to understand.
- The team is comfortable with SQL and the queries are stable; a Query Object adds complexity for little gain.

**Key trade-off:** Completely encapsulates the database schema from client code and enables sophisticated features like redundant-query elimination and multi-database support, but building and maintaining a full Query Object implementation is significant work; most teams rely on a commercial tool rather than building it themselves.

**Related patterns:** Metadata Mapping (required for translating field names to column names), Repository (wraps Query Object behind a collection-like interface), Specification pattern (the criteria object is a form of Specification), Identity Map (a sophisticated Query Object can serve results from the map to avoid database round trips).

**Practical heuristic:** Build the minimal Query Object that satisfies your current querying needs and evolve it as requirements grow; if you already have Metadata Mapping, adding a basic Query Object is a small incremental step that pays off quickly in query centralisation.

---

## Repository

**Category:** ORM Metadata Mapping

**Intent:** Mediate between the domain and data mapping layers using a collection-like interface for accessing domain objects, so that client code interacts with a repository as if it were an in-memory set of objects rather than a database.

**How it works:** Client code creates a Criteria object specifying what objects it needs (e.g. `criteria.equals(Person.LAST_NAME, "Fowler")`), then calls `repository.matching(criteria)` to receive a collection of domain objects. The Repository internally uses a Query Object and/or Metadata Mapping to translate the criteria into SQL, execute it, and return hydrated domain objects. Objects can be added or removed from the Repository like a collection. The Repository hides all details of the database, query construction, and mapping from the client, maintaining a clean one-way dependency from the domain toward the data layer.

**When to use:**
- The system has a complex domain model with many domain object types and many query variations.
- Multiple data sources (databases, in-memory objects for testing, caches) must be substituted transparently.
- You want to eliminate duplicated query construction logic spread across many finder methods on Data Mapper classes.

**When NOT to use:**
- The domain is simple and a handful of explicit finder methods on a Data Mapper are sufficient.
- Query Object is not available — Repository's power is greatly reduced without it, since criteria cannot be translated automatically.

**Key trade-off:** Makes client code completely agnostic of the persistence mechanism and promotes the Specification pattern for queries, but requires Query Object and Metadata Mapping as prerequisites, making it the most infrastructure-intensive of the three metadata mapping patterns.

**Related patterns:** Query Object (the mechanism Repository uses internally to execute criteria), Metadata Mapping (translates field names to column names for the Query Object), Data Mapper (Repository replaces or wraps the finder methods on the mapper layer), Specification pattern (criteria objects are a form of Specification).

**Practical heuristic:** Introduce Repository when you find yourself writing the same querying logic in multiple places or when you need to swap the persistence mechanism during testing; if Query Object is already in place, adding a Repository is a thin layer that provides large returns in testability and readability.

---

## Web Presentation Patterns

## Model View Controller

**Category:** Web Presentation

**Intent:** Splits user interface interaction into three distinct roles — model, view, and controller — to separate presentation from domain logic.

**How it works:** The model holds domain data and behavior with no knowledge of the UI. The view renders the model's data for display and observes the model for changes. The controller receives user input, manipulates the model, and causes the view to update. The presentation depends on the model, but the model never depends on the presentation; this one-way dependency is the pattern's core discipline.

**When to use:**
- When the same domain data must be displayed in multiple formats (web page, rich client, API, CLI) from a single model.
- When you want to test domain logic without involving UI machinery or scripting tools.

**When NOT to use:**
- In very simple systems where the model has no real behavior — the overhead of the separation adds no value when there is nothing non-visual to protect.

**Key trade-off:** Enforcing the view/controller split is less important than enforcing the model/presentation split; combining view and controller (as most frameworks do) is usually fine, but collapsing model into presentation is always a mistake.

**Related patterns:** Page Controller, Front Controller (both implement the controller role); Template View, Transform View (both implement the view role); Application Controller (a separate pattern often confused with the MVC controller).

**Practical heuristic:** If domain logic is starting to appear in your view or controller code, stop and push it into the model — that boundary is non-negotiable.

---

## Page Controller

**Category:** Web Presentation

**Intent:** An object that handles a request for a specific page or action on a Web site, acting as the controller for that one URL or action.

**How it works:** Each logical page or action on the site has a dedicated handler — either a script (CGI, servlet) or a server page (ASP, PHP, JSP). The handler decodes the URL and form data, creates and invokes the relevant model objects, then decides which view to forward to, passing the model information along. Common behavior across handlers can be factored into a superclass or helper object so it is not duplicated across every page.

**When to use:**
- When most pages have simple, independent controller logic and a straightforward one-URL-to-one-handler mapping is easy to maintain.
- When you want designer-friendly URLs that correspond directly to server page files.

**When NOT to use:**
- When the site has heavy navigational complexity, cross-cutting concerns (authentication, i18n, audit logging) that must apply uniformly, or behavior that needs to change at runtime — Front Controller handles these better.

**Key trade-off:** Page Controller is simpler to understand and requires no central configuration, but it scatters cross-cutting logic across handlers and makes runtime behavioral changes difficult.

**Related patterns:** Front Controller (the alternative for more complex navigation); Template View (commonly combined with Page Controller in server-page environments); Application Controller (can be used alongside either controller style).

**Practical heuristic:** Use Page Controller by default; switch to Front Controller only when you find yourself duplicating the same cross-cutting code in every handler.

---

## Front Controller

**Category:** Web Presentation

**Intent:** A controller that handles all requests for a Web site through a single entry point, then dispatches to command objects for request-specific behavior.

**How it works:** A single Web handler (typically a servlet or equivalent class) receives every incoming request, pulls just enough information from the URL to identify which command to run, instantiates the command, and delegates to it. The command carries out the action-specific work — invoking model objects and forwarding to a view — without needing to know anything about the Web framework. The handler can be wrapped with decorators (Intercepting Filter) to add cross-cutting behavior such as authentication, logging, and locale detection at configuration time without touching command code.

**When to use:**
- When the site has significant cross-cutting concerns (security, i18n, audit) that must apply uniformly and be modifiable at runtime without changing every handler.
- When Web server configuration is awkward and you want only one entry point registered.

**When NOT to use:**
- When controller logic per page is simple — the added indirection of a command hierarchy and central dispatch introduces unnecessary complexity compared to Page Controller.

**Key trade-off:** Front Controller centralizes and simplifies cross-cutting concerns and runtime reconfiguration, but it is a more complex design that requires more upfront infrastructure before the first page works.

**Related patterns:** Page Controller (simpler alternative); Intercepting Filter (decorates the handler for cross-cutting behavior); Template View / Transform View (used by commands to render responses); Application Controller (can sit between the handler and commands to manage navigation state).

**Practical heuristic:** Reach for Front Controller when you catch yourself copy-pasting the same authentication or logging block into every Page Controller handler.

---

## Template View

**Category:** Web Presentation

**Intent:** Renders information into HTML by embedding markers in an otherwise static HTML page that are replaced with dynamic data at request time.

**How it works:** A page is authored as static HTML with special markers (HTML-like tags, custom tags, or text placeholders) at positions where dynamic content should appear. When a request arrives, the template engine replaces the markers with results of calls to a helper object that holds all real programming logic. The page itself stays as close to plain HTML as possible so that WYSIWYG editors and non-programmer designers can work on it; the helper object handles domain interaction, keeping logic out of the page.

**When to use:**
- When graphic designers or non-programmers need to edit page layout without touching code, making the page-as-template model natural.
- When building the view in Model View Controller for most mainstream server-side web development where familiar tooling (JSP, ASP, PHP, Razor) is already in use.

**When NOT to use:**
- When testability of the view is a high priority — Template Views tightly coupled to a Web server are hard to test in isolation; Transform View is easier to test outside a running server.

**Key trade-off:** Template View is easier for most teams to author and learn, but its common implementations make it dangerously easy to embed logic in the page, undermining maintainability.

**Related patterns:** Transform View (the alternative rendering approach, easier to test); Two Step View (adds a second rendering stage on top of either Template View or Transform View); Page Controller / Front Controller (supply the helper and forward to the Template View).

**Practical heuristic:** Put all conditionals, loops, and domain calls in the helper object — if you find yourself writing a scriptlet or complex expression directly in the page, move it to the helper.

---

## Transform View

**Category:** Web Presentation

**Intent:** A view that processes domain data element by element and transforms it into HTML, typically using XSLT applied to a domain-oriented XML document.

**How it works:** The controller retrieves domain data and produces (or receives) an XML representation of it. A transformer program — most commonly an XSLT stylesheet — walks the XML structure and, as it recognizes each domain element, writes out the appropriate HTML fragment. Because the transform rules are organized around input element types rather than the output page structure, the rules can appear in any order and the transform can be run and tested without a Web server.

**When to use:**
- When the team is comfortable with XSLT and the domain layer naturally returns XML or data easily serialized to XML.
- When testability of the view layer matters — Transform View implementations can be exercised without a running Web server.

**When NOT to use:**
- When designers need WYSIWYG HTML editors to lay out pages — XSLT tooling is far less mature than HTML editors; Template View is a better fit for design-heavy workflows.

**Key trade-off:** Transform View is easier to test and harder to pollute with logic, but XSLT is an awkward functional language with little tool support, and global look-and-feel changes still require editing every transform file unless Two Step View is used.

**Related patterns:** Template View (the alternative, more designer-friendly rendering approach); Two Step View (extends Transform View with a two-stage process to centralize global appearance); Front Controller (commonly used to invoke the transform command).

**Practical heuristic:** Choose Transform View over Template View when your integration tests must run without a Web server, or when your data layer already speaks XML natively.

---

## Two Step View

**Category:** Web Presentation

**Intent:** Turns domain data into HTML in two distinct stages — first assembling a logical, format-neutral screen structure, then rendering that structure into HTML — so that global appearance changes require editing only the second stage.

**How it works:** The first stage reads from the domain model and constructs a presentation-oriented intermediate structure (logical screen) that represents what should appear — fields, tables, headers — but contains no HTML. The second stage knows how to render each element of the logical screen into HTML and is shared across all pages. A global site redesign therefore touches only the single second-stage component. The two stages can be implemented as two XSLT stylesheets, two sets of class hierarchies, or a combination of server-page first stages and custom-tag second stages.

**When to use:**
- When a large web application needs a consistent look and feel across many pages and global appearance changes must be cheap to make.
- When the same screens must be served to multiple output targets (browser, PDA) that share a common logical structure but require different HTML formatting.

**When NOT to use:**
- When page designs are intentionally varied and design-heavy, making it hard to find enough commonality across pages to define a shared logical screen structure.
- When the team needs WYSIWYG HTML tools — the logical screen intermediate format typically precludes standard HTML editor support.

**Key trade-off:** Two Step View dramatically reduces the cost of global appearance changes but constrains page design to what the presentation-oriented structure can express, and it introduces a more complex programming model.

**Related patterns:** Template View / Transform View (Two Step View is built on top of either); Front Controller (commonly used to orchestrate the two-stage process).

**Practical heuristic:** If changing the site's color scheme or header layout requires editing a dozen files, Two Step View will pay off; if each page is intentionally unique, it will fight you.

---

## Application Controller

**Category:** Web Presentation

**Intent:** A centralized point for handling screen navigation and application flow, deciding which domain command to run and which view to display based on the current application state.

**How it works:** The Application Controller holds two structured collections of references: one mapping application states or events to domain commands (Transaction Scripts or domain object methods), and another mapping states to views. When an input controller (Page Controller or Front Controller) receives a request, it asks the Application Controller for the appropriate domain command and view rather than hard-coding that decision itself. The Application Controller can be implemented as a state machine driven by metadata, making it possible to represent complex wizard-style flows and context-dependent navigation in a single, testable place.

**When to use:**
- When the application enforces a definite order of screens (wizard flows, multi-step processes) and the navigation logic is complex enough that duplicating it across individual input controllers becomes a maintenance problem.
- When different views or commands must be selected based on the state of domain objects, and that logic is changing frequently.

**When NOT to use:**
- When users can visit any screen in any order freely — if navigation is unconstrained, Application Controller adds infrastructure with no benefit.

**Key trade-off:** Application Controller centralizes and simplifies flow logic but introduces an additional layer between input and domain that can blur the boundary between application flow logic and true domain logic.

**Related patterns:** Page Controller / Front Controller (delegate to the Application Controller for navigation decisions); Model View Controller (Application Controller is often confused with the MVC controller but is a separate, higher-level concept); Transaction Script / Domain Model (supply the domain commands that Application Controller invokes).

**Practical heuristic:** If making a change to the application's navigation flow requires touching more than one input controller class, extract the flow logic into an Application Controller.

---

## Distribution, Concurrency and Session State Patterns

# Distribution, Session State, and Concurrency Patterns
> Source: Patterns of Enterprise Application Architecture — Martin Fowler, Chapters 15–17 (pp. 409–485)

---

## Remote Facade

**Category:** Distribution

**Intent:** Provide a coarse-grained interface over a fine-grained object model to minimize the cost of remote calls.

**How it works:** Fine-grained object models excel within a single process, but inter-process calls are orders of magnitude more expensive than in-process calls. A Remote Facade sits in front of the domain model and exposes chunky methods that bundle together what would otherwise be many small calls. Each facade method does little more than delegate to the underlying fine-grained objects; all business logic stays in the domain model. A separate assembler object translates between domain objects and Data Transfer Objects used as the method payload.

**When to use:**
- A presentation tier (e.g., Swing UI, browser client) runs in a different process from the domain model and needs to read or write data across that boundary.
- Any two components communicate across process boundaries — even on the same machine, inter-process cost is high enough to require coarse-grained interfaces.

**When NOT to use:**
- All access is within a single process — the pattern adds needless complexity with no performance benefit.
- The back-end is already a Transaction Script, which is inherently coarse-grained and does not need an additional facade layer.

**Key trade-off:** Coarse-grained calls reduce network round-trips but force you to design large, less flexible interfaces; the fine-grained domain model retains its design quality behind the facade.

**Related patterns:** Data Transfer Object (carries payloads across the facade boundary); Domain Model (the fine-grained model being wrapped); Transaction Script (usually does not need a Remote Facade).

**Practical heuristic:** Keep facade methods as short as possible — a list of one- or two-line delegation calls. If logic creeps into the facade, push it back into the domain model.

---

## Data Transfer Object

**Category:** Distribution

**Intent:** Carry data between processes in a single call to reduce the number of remote method invocations.

**How it works:** When a Remote Facade is in play, each call is expensive, so data that would otherwise require multiple calls is packed into a single serializable object — the DTO. The DTO holds no behavior beyond serialization and deserialization (e.g., to/from XML or binary). A separate assembler object (a Mapper) is responsible for creating DTOs from domain objects and updating the domain model from incoming DTOs; neither side depends on the other directly. A single DTO type can be served by multiple assemblers for different use-case semantics.

**When to use:**
- Multiple items of data must cross a process boundary in one method call.
- You need an explicit, stable interface to XML or another wire format — a DTO encapsulates the representation so the rest of the system is insulated from format changes.
- A DTO serves as a common data bag passed through multiple layers, each enriching it before passing it on.

**When NOT to use:**
- All communication is in-process — the overhead of DTO creation and assembly adds complexity with no benefit.

**Key trade-off:** DTOs reduce remote call count and decouple wire format from domain logic, but introduce a parallel object graph and require assembler code that must be kept in sync with both sides.

**Related patterns:** Remote Facade (the facade boundary that DTOs cross); Mapper / Assembler (the object that translates between DTOs and domain objects).

**Practical heuristic:** Never put business logic in a DTO — it is a data container only. Keep the assembler separate from both the DTO and the domain object so neither depends on the other.

---

## Optimistic Offline Lock

**Category:** Concurrency

**Intent:** Prevent conflicts between concurrent business transactions by detecting collisions at commit time rather than preventing them upfront.

**How it works:** Each record carries a version stamp (typically an integer counter). When a session loads a record it captures the version. At commit time, within a single system transaction, the session validates that the current database version matches the captured version before applying its changes — if another session has incremented the version in the meantime, the commit fails and the user must retry. The version is incremented on every successful write. Optimistic Offline Lock can also guard against inconsistent reads: a session that reads but does not write a record can still check its version at commit time to ensure the read was consistent.

**When to use:**
- The probability of two sessions conflicting on the same data is low.
- Business transactions span multiple system transactions (offline concurrency) and long system transactions are not viable.
- You want maximum concurrency and can tolerate the rare case where a user must retry after a conflict.

**When NOT to use:**
- Conflict probability is high, or the cost of discarding a long business transaction is unacceptable — use Pessimistic Offline Lock instead.
- The business transaction fits within a single system transaction — rely on the database's built-in locking.

**Key trade-off:** Maximum concurrency and simplicity at the cost of late conflict detection — users do all their work before finding out they must redo it.

**Related patterns:** Pessimistic Offline Lock (the alternative for high-conflict scenarios); Coarse-Grained Lock (locks groups of objects with a shared version); Implicit Lock (automates version checking in a framework).

**Practical heuristic:** Include the version check in every UPDATE and DELETE SQL statement (`WHERE id = ? AND version = ?`) so a zero-rows-affected result immediately signals a conflict.

---

## Pessimistic Offline Lock

**Category:** Concurrency

**Intent:** Prevent conflicts between concurrent business transactions by allowing only one business transaction at a time to access data.

**How it works:** Before a session can read or modify a piece of data it must acquire a lock from a lock manager. Three lock types are typical: exclusive read (only one reader, no writers), exclusive write (only one writer, no readers), and read/write (many readers or one writer — a shared read lock). The lock manager stores locks in a persistent table (so they survive server restarts) keyed by the record identity and the session or owner. Locks must be released when the business transaction completes or the session times out; timeout detection is essential to prevent abandoned locks from blocking the system indefinitely.

**When to use:**
- The chance of concurrent sessions conflicting on the same data is high.
- The cost of a conflict — discarding a long business transaction — is unacceptable regardless of probability.
- Use selectively alongside Optimistic Offline Lock: apply pessimistic locks only where truly required.

**When NOT to use:**
- The business transaction fits within a single system transaction — the database's built-in locking (e.g., `SELECT FOR UPDATE`) is simpler and sufficient.
- Conflict probability is low — pessimistic locks create data contention and hurt throughput unnecessarily.

**Key trade-off:** Eliminates wasted work from conflicts at the cost of reduced concurrency and the operational complexity of managing lock timeouts and deadlocks.

**Related patterns:** Optimistic Offline Lock (the complementary, lower-contention alternative); Coarse-Grained Lock (lock an aggregate with one lock acquisition); Implicit Lock (automate lock acquisition in a framework).

**Practical heuristic:** Always implement lock timeouts and a background process to reap expired locks — an unreclaimed lock from a crashed session can block other users indefinitely.

---

## Coarse-Grained Lock

**Category:** Concurrency

**Intent:** Lock a group of related objects with a single lock to simplify concurrency management for aggregates.

**How it works:** Two implementations exist. In the *shared lock* approach, every object in the group points to the same shared version object; incrementing that version (for Optimistic Offline Lock) or acquiring a lock on it (for Pessimistic Offline Lock) simultaneously locks all group members without loading them. In the *root lock* approach (aligned with Domain-Driven Design aggregates), the aggregate root is locked, and by definition locking the root locks all members — the lock manager only needs to know about the root. The choice between the two involves a trade-off: shared locks require a join to the version table on nearly every query; root locks require navigating to the root, which may force additional object loads.

**When to use:**
- Business rules require that an entire aggregate be treated as a single unit for locking (e.g., a lease and its assets must always be locked together).
- You want to avoid the code complexity and performance cost of acquiring individual locks on every object in a related group.
- Using Optimistic or Pessimistic Offline Lock on an aggregate and want a single point of contention.

**When NOT to use:**
- Objects in the group are independently editable with no atomicity requirement — coarse-grained locking reduces concurrency unnecessarily.

**Key trade-off:** Simpler lock acquisition and clearer business semantics at the cost of reduced concurrency — locking the group blocks access to all members even if only one is needed.

**Related patterns:** Optimistic Offline Lock (shared version implements a coarse-grained optimistic lock); Pessimistic Offline Lock (shared lockable token implements a coarse-grained pessimistic lock); Implicit Lock (ensures group locking rules are never accidentally bypassed).

**Practical heuristic:** Model your aggregate boundary carefully before choosing a lock granularity — an overly broad aggregate creates a hot spot; an overly narrow one misses atomicity guarantees.

---

## Implicit Lock

**Category:** Concurrency

**Intent:** Allow framework or layer supertype code to acquire offline locks automatically so application developers cannot accidentally omit locking steps.

**How it works:** The most dangerous property of any locking scheme is a gap — one place in the codebase that forgets to acquire a lock can invalidate the entire strategy. Implicit Lock moves mandatory locking mechanics into framework infrastructure (Layer Supertypes, base mapper classes, Unit of Work commit hooks, code generation) so that they happen automatically whenever data is loaded or committed. For Optimistic Offline Lock this means the framework stores, checks, and increments version counts; for Pessimistic Offline Lock it means the framework acquires read locks on load and releases all locks at session end. Only optional locks (e.g., an explicit write lock chosen by business logic) remain in application code.

**When to use:**
- The application uses Optimistic or Pessimistic Offline Lock and you want to guarantee no developer can accidentally skip a locking step.
- The locking logic is repetitive enough that it has already been copy-pasted multiple times across the codebase.

**When NOT to use:**
- The locking scheme is so simple or the codebase so small that framework infrastructure would be over-engineering.

**Key trade-off:** Eliminates entire categories of locking bugs at the cost of less visible, more implicit behavior that can be harder to debug when something goes wrong.

**Related patterns:** Optimistic Offline Lock (the scheme Implicit Lock most commonly automates); Pessimistic Offline Lock (the mandatory read-lock/release steps are ideal candidates); Coarse-Grained Lock (root-lock acquisition on Unit of Work commit is a natural Implicit Lock integration point).

**Practical heuristic:** Put the locking invariants — "always version-check on update", "always release locks on session end" — in the framework's commit and load hooks, not in individual use-case code.

---

## Client Session State

**Category:** Session State

**Intent:** Store all session data on the client so the server remains stateless between requests.

**How it works:** With each request the client sends the full session state to the server, and the server sends the full updated state back with each response. For rich clients this is straightforward (in-memory objects or a local domain model). For HTML clients three mechanisms are common: URL parameters (small amounts of data appended to every link), hidden form fields (data embedded in the page and submitted with forms), and cookies (data stored in the browser, sent automatically with every HTTP request). Data Transfer Objects simplify serialization of complex state. At minimum, a session identifier must always be stored on the client.

**When to use:**
- You want fully stateless server objects with maximum clustering and failover resilience.
- The volume of session data is small (a handful of fields or just a session ID).

**When NOT to use:**
- Session data is large — the per-request transfer cost becomes prohibitive.
- The data is sensitive — anything sent to the client is exposed to inspection and tampering; encryption is the only mitigation, and it carries its own performance cost.

**Key trade-off:** Simple, stateless servers with excellent scalability, but all session data is exposed on the client and lost if the client fails or manipulates it maliciously.

**Related patterns:** Server Session State (keeps data on the server to avoid exposure); Database Session State (persists data across server restarts); Data Transfer Object (bundles session data for transfer).

**Practical heuristic:** Always use Client Session State for the session identifier (one opaque token), but keep sensitive business data server-side — never trust data returned from the client without full re-validation.

---

## Server Session State

**Category:** Session State

**Intent:** Keep session data in memory on the server between client requests, associated with a session object.

**How it works:** The server holds a session object (e.g., an HttpSession, a stateful session bean) keyed by a session ID stored on the client. When a request arrives, the server retrieves the session object and makes its data available for the duration of the request. To support clustering and failover, the session object can be *passivated* — serialized and written to a shared store (file system, shared database, or a Serialized LOB in a session table) — and *activated* (deserialized) when needed. Binary serialization is fast but fragile across schema changes; XML serialization is more tolerant. The boundary with Database Session State is where the data transitions from serialized object blobs to decomposed, queryable relational rows.

**When to use:**
- Session data is too large or too sensitive to send to the client on every request.
- The platform provides a session management container (e.g., EJB stateful session beans, HttpSession) that handles passivation transparently.
- You want simplicity over maximum scalability.

**When NOT to use:**
- You require strict stateless server nodes with aggressive load-balancing across many machines — server affinity issues make this difficult without extra infrastructure.
- Session data must survive server upgrades where serialization format changes are likely.

**Key trade-off:** Simpler programming model and no client-side exposure, at the cost of server-side memory consumption and potential clustering/failover complexity.

**Related patterns:** Client Session State (offloads state to the client); Database Session State (stores state in structured database tables); Serialized LOB (the persistence mechanism for passivated session objects).

**Practical heuristic:** Load-test your specific environment before assuming stateful sessions are a performance problem — the difference between stateful and stateless beans only matters at high concurrency, and the simplicity of stateful sessions often wins at moderate load.

---

## Database Session State

**Category:** Session State

**Intent:** Store session data as committed or pending rows in the database so it is available to any server in a cluster and survives server restarts.

**How it works:** Instead of holding session data in server memory, the application writes it to regular database tables between requests. Two variants exist: *pending* data (rows flagged as belonging to an in-progress session, not yet visible as committed business data) and *committed* data (rows written immediately to the main tables, with a session identifier column distinguishing in-progress edits from finalized records). The session ID stored on the client is used to query the appropriate rows on each request. This approach naturally supports clustering — any server can handle any request — and is resilient to server failure. The trade-off versus Server Session State using a serialized session table is that here the data is decomposed into relational columns rather than stored as an opaque blob.

**When to use:**
- You need full clustering and failover without server affinity.
- Session data must survive server restarts or software upgrades.
- The session data naturally maps to relational tables and may need to be queried or reported on.

**When NOT to use:**
- Session data is complex or deeply object-graph-shaped — relational decomposition is awkward and a Serialized LOB (Server Session State) may be simpler.
- Database write throughput for transient session rows creates unacceptable load on the primary database.

**Key trade-off:** Perfect scalability and durability at the cost of database load for transient session data and the complexity of distinguishing pending session rows from committed business data.

**Related patterns:** Server Session State (stores session data as serialized blobs rather than relational rows); Client Session State (eliminates server-side state entirely); Optimistic/Pessimistic Offline Lock (manage concurrent access to session data across requests).

**Practical heuristic:** Use a clear, indexed `session_id` column on every pending-data table and include a cleanup job that purges orphaned session rows after session timeout — without it, the database fills with abandoned data.

---

## Base Patterns

# Chapter 18: Base Patterns — Fowler, Patterns of Enterprise Application Architecture

## Gateway

**Category:** Base Patterns

**Intent:** Wrap access to an external system or resource behind a simple object that looks like a regular object to its callers.

**How it works:** You wrap all the special API code for an external resource into a class whose interface looks like a regular object. Other objects access the external resource through this Gateway, which translates the simple method calls into the appropriate specialized API calls. The Gateway should be as simple as possible — its only roles are adapting the external interface and providing a clean point for stubbing. A two-object form (back-end wrapper + front-end adapter) can be used when wrapping complexity and adapting to your needs are both significant.

**When to use:**
- You need to access an external resource (database, messaging system, XML service, external API) from application code.
- You want a clean point at which to apply a Service Stub for testing without the external dependency.
- You anticipate possibly swapping one kind of external resource for another.

**When NOT to use:**
- Both subsystems must remain completely unaware of each other and of the isolation element — use Mapper instead, which is more complex but achieves full mutual ignorance.

**Key trade-off:** Simplicity and testability gained by containing the awkward API vs. a thin layer that does not attempt mutual ignorance between caller and resource.

**Related patterns:** Mapper (stronger decoupling, more complex), Service Stub (deploy at the Gateway boundary for testing), Separated Interface (the Gateway interface can be defined separately from its implementation), Facade (similar wrapping, but Facade is written by the service provider for general use; Gateway is written by the client for its own needs).

**Practical heuristic:** Every external resource access should go through a Gateway — if you can see a vendor API anywhere other than inside a Gateway class, move it.

---

## Mapper

**Category:** Base Patterns

**Intent:** An object that sets up communication between two independent objects without either subsystem being aware of the other or of the Mapper.

**How it works:** A Mapper is an insulating layer that controls all communication between two subsystems and keeps them completely ignorant of each other. It often shuffles data from one layer to another. Because neither subsystem can invoke the Mapper directly (that would create a dependency), a third subsystem typically drives the mapping, or the Mapper is made an observer of one of the subsystems so it can be triggered by events. The most common enterprise use is Data Mapper, which maps between domain objects and the database.

**When to use:**
- Neither subsystem should have any dependency on the interaction between them — not even knowledge that the interaction exists.
- The interaction is particularly complex and somewhat independent of the main purpose of both subsystems.

**When NOT to use:**
- The simpler Gateway will do — Gateway is far easier to write and use and is the default choice for the vast majority of external resource access.

**Key trade-off:** Complete mutual ignorance of both subsystems vs. significantly higher complexity than Gateway.

**Related patterns:** Gateway (simpler alternative where the client is aware of the interaction), Data Mapper (the most common concrete application of Mapper), Mediator (similar but objects that use a Mediator are aware of it; objects that a Mapper separates are not even aware of the Mapper).

**Practical heuristic:** Reach for Mapper only when you cannot afford any dependency between the two subsystems; use Gateway for everything else.

---

## Layer Supertype

**Category:** Base Patterns

**Intent:** A type that acts as the supertype for all types in its layer, consolidating common behavior in one place.

**How it works:** You create a single superclass for all objects in a given layer — for example, a `DomainObject` base class for all domain objects in a Domain Model, or a base Data Mapper class for all mappers. Common features such as identity field handling, dirty tracking, and common query infrastructure live in this superclass. If a layer has more than one kind of object, it is useful to have more than one Layer Supertype.

**When to use:**
- All or most objects in a layer share common behavior (ID handling, persistence hooks, event dispatch) that you do not want duplicated.
- You make heavy use of common infrastructure features that benefit from a single place to evolve.

**When NOT to use:**
- The shared behavior is so thin or varies so much across objects in the layer that a shared superclass creates more coupling than it removes.

**Key trade-off:** Reduced duplication and a single place to evolve layer-wide behavior vs. increased coupling through inheritance across the whole layer.

**Related patterns:** Domain Model (Layer Supertype is the natural home for identity and persistence concerns shared by all domain objects), Data Mapper (mappers can share a supertype that handles common mapping infrastructure).

**Practical heuristic:** If you find yourself copying the same ID-handling or tracking code into every class in a layer, create a Layer Supertype and move it there immediately.

---

## Separated Interface

**Category:** Base Patterns

**Intent:** Define an interface in a separate package from its implementation so that clients depend only on the interface and have no compile-time dependency on the implementing package.

**How it works:** The pattern exploits the fact that an implementation has a dependency on its interface, but not vice versa. You place the interface in the client's package (or a neutral third package) and the implementation in its own package. The implementation package depends on the interface package, but the interface package has no dependency on any implementation. Callers that use only the interface never see the implementation package. At runtime something must wire a concrete implementation to the interface — either a startup assembly step or a Plugin.

**When to use:**
- A framework package needs to call application code without depending on it.
- Code in one layer must call code in another layer that the layering rules forbid it to see (e.g., domain code calling a Data Mapper).
- You need multiple independent implementations and want to enforce that callers cannot reach any specific one.

**When NOT to use:**
- There is only one implementation and no architectural need to break the dependency — interface and implementation can live together until the need arises.

**Key trade-off:** Clean enforcement of layering and dependency rules vs. added complexity (extra packages, factory objects, or Plugin wiring).

**Related patterns:** Plugin (a good mechanism for binding an implementation to a Separated Interface at configuration time), Gateway (a Separated Interface provides a natural plug point for a Gateway), Dependency Injection (modern frameworks achieve the same binding goal).

**Practical heuristic:** Do not create a Separated Interface by default for every class; apply it only when you need to break a real dependency or support multiple independent implementations.

---

## Registry

**Category:** Base Patterns

**Intent:** A well-known object that other objects can use to find common objects and services when you cannot navigate to them through normal inter-object references.

**How it works:** A Registry is essentially a controlled global object — it looks global but can be encapsulated and substituted. The preferred interface style is static methods (easy to find anywhere in the application) delegating to an underlying instance, keeping data off static fields so it can be replaced. Data scope matters: process-scoped Registries use a singleton; thread-scoped Registries use thread-local storage; session-scoped Registries use a thread-local dictionary keyed by session ID. For testing, you replace the singleton instance with a stub subclass.

**When to use:**
- An object needs a service or finder but cannot receive it through constructor or method parameters without polluting every call site in a deep call tree.
- You need a well-known place to hold finders, connection factories, or configuration objects shared across many objects.

**When NOT to use:**
- You can pass the dependency through the call chain or inject it at construction — prefer that; a Registry is always a last resort because it is global data.

**Key trade-off:** Convenient universal access to shared objects vs. global state that is hard to reason about, test, and keep thread-safe.

**Related patterns:** Singleton (one common implementation strategy), Plugin (a good way to swap Registry contents for testing), Service Stub (substitute into the Registry during tests).

**Practical heuristic:** Before introducing a Registry, try passing the object as a constructor or method parameter; add a Registry only when parameter passing genuinely becomes impractical.

---

## Value Object

**Category:** Base Patterns

**Intent:** A small, simple object — like a date range or money amount — whose equality is based on field values rather than object identity.

**How it works:** A Value Object defines equality by comparing all its fields, not by object reference or ID. Because multiple copies of the same value are considered equal, Value Objects are passed by value (copied) rather than by reference, and should be made immutable to prevent aliasing bugs — where one owner unexpectedly mutates a shared instance. They should not be persisted as standalone records; use Embedded Value to store their fields inline in a parent table. In C# they map naturally to structs.

**When to use:**
- Equality of two instances should be determined by their data, not by which object in memory they are (dates, money amounts, coordinates, ranges, quantities).
- The object is small, easily created, and has no meaningful identity beyond its value.

**When NOT to use:**
- The object has a long lifecycle, needs database identity, or must be tracked as a distinct entity over time — use a reference object with an ID instead.

**Key trade-off:** Clean value semantics and no aliasing bugs vs. the overhead of copying and the discipline of immutability.

**Related patterns:** Money (the canonical example of Value Object), Embedded Value (persistence strategy for Value Objects), Data Transfer Object (different concept — do not confuse the two terms).

**Practical heuristic:** Make every Value Object immutable from the moment of creation; if a caller needs a different value, they construct a new instance rather than mutating the existing one.

---

## Money

**Category:** Base Patterns

**Intent:** Represent a monetary value as an object that pairs an amount with a currency, encapsulating rounding and currency-aware arithmetic.

**How it works:** A Money class holds an integral amount (stored in the smallest currency unit, e.g., cents) and a Currency. All arithmetic is currency-aware: adding two Money values of different currencies is an error. Multiplication by a scalar requires an explicit rounding mode. For proportional allocation across multiple targets (e.g., splitting a sum 70/30), use an `allocate` method that distributes remainders one unit at a time to avoid losing or gaining pennies. Money is a Value Object: equality checks both amount and currency; the object is immutable. Persist using Embedded Value.

**When to use:**
- Any code that performs monetary calculation, comparison, formatting, or multi-currency conversion.
- You need to prevent floating-point rounding errors in financial computations.

**When NOT to use:**
- Performance profiling has shown the Money class is a genuine bottleneck and the encapsulation overhead outweighs the correctness benefit — rare in practice.

**Key trade-off:** Correct handling of rounding and multi-currency arithmetic vs. slightly more ceremony when doing monetary math.

**Related patterns:** Value Object (Money is the canonical example), Embedded Value (persistence strategy for Money), Quantity (a similar pattern for any measurable amount with a unit).

**Practical heuristic:** Never use a floating-point type for money; store amounts as integers in the smallest currency unit (cents, pence) and let the Money class handle all formatting and rounding.

---

## Special Case

**Category:** Base Patterns

**Intent:** A subclass that provides special behavior for particular corner cases — most often null — so callers never need to check for that case explicitly.

**How it works:** Instead of returning null (or a magic sentinel value) when a lookup or operation has no meaningful result, return an instance of a Special Case subclass that overrides all methods with harmless, context-appropriate default behavior. Multiple distinct special cases (e.g., MissingCustomer vs. UnknownCustomer) can coexist as separate subclasses. Because all Special Cases of the same type behave identically, they are often implemented as flyweights. A Special Case method that would normally return a related object can return another Special Case.

**When to use:**
- Multiple call sites contain the same conditional logic to handle null or a specific sentinel value for a particular class.
- A missing, unknown, or inapplicable instance should produce a predictable default behavior rather than propagating null.

**When NOT to use:**
- The "special" behavior varies widely per call site — a generic null object cannot capture that variability and callers will still need conditionals.

**Key trade-off:** Elimination of repetitive null checks and conditional code vs. a proliferation of subclasses if many distinct special cases exist.

**Related patterns:** Null Object (a well-known specific form of Special Case), Strategy (similarly avoids conditionals by encapsulating behavior in objects).

**Practical heuristic:** When you find yourself writing the same null check three or more times for the same type, introduce a Special Case subclass and return it instead of null.

---

## Plugin

**Category:** Base Patterns

**Intent:** Link classes to their implementations during configuration rather than compilation, so that deployment environment can be changed without a code rebuild.

**How it works:** You define the behavior that needs environment-specific implementations as a Separated Interface. A Plugin factory reads a single external configuration file (e.g., a properties file) mapping interface names to implementation class names, and uses reflection to instantiate the correct implementation at runtime. Because all configuration is centralized and read at startup, switching from test to production environment means swapping one config file, not editing factory methods scattered across the codebase. Without reflection, a factory with conditional logic achieves the same centralization at the cost of requiring a recompile when new implementations are added.

**When to use:**
- Behaviors need different implementations in different runtime environments (test, staging, production) and you want zero-rebuild reconfiguration.
- You have multiple Separated Interfaces that all need consistent environment-aware binding in one place.

**When NOT to use:**
- There is only one implementation and no realistic prospect of needing another — the extra indirection is unnecessary overhead.

**Key trade-off:** Centralized, rebuild-free reconfiguration vs. indirection and the loss of compile-time checks on implementation bindings.

**Related patterns:** Separated Interface (prerequisite — define the interface before applying Plugin), Registry (Plugin is often used to populate Registry entries), Service Stub (Plugin loads the stub during test runs), Dependency Injection (modern frameworks achieve the same goal with more infrastructure).

**Practical heuristic:** Put the Plugin factory in its own package so that enforcing layer dependencies via build-time checks does not require the factory to change when new implementations are added.

---

## Service Stub

**Category:** Base Patterns

**Intent:** Replace a problematic external service dependency with a local, in-process stub during development and testing so that tests can run without the real service.

**How it works:** First, access to the real service is wrapped behind a Gateway defined as a Separated Interface. You then write a stub implementation of that Gateway interface that runs locally, fast, and in memory — returning hardcoded or test-configured responses. A Plugin or test-setup routine substitutes the stub for the real implementation. Keep the stub as simple as possible: two or three lines of code for a flat-rate response is ideal. For more nuanced behavior (e.g., tax exemptions), a dynamic stub maintains a small in-memory list that test cases populate via setup methods.

**When to use:**
- Development or tests depend on an external service that is unreliable, slow, costly per call, or not yet delivered.
- You want tests to run offline and deterministically without live network calls.

**When NOT to use:**
- The external service is fully under your control, reliably available in the test environment, and fast — integration tests against the real service may be preferable.

**Key trade-off:** Fast, reliable, offline tests vs. the risk that the stub diverges from the real service's behavior.

**Related patterns:** Gateway (wraps the real service; the stub implements the same Gateway interface), Separated Interface (prerequisite — enables substituting the stub without the caller knowing), Plugin (loads the stub at test configuration time), Mock Object (the XP community's term for essentially the same concept).

**Practical heuristic:** Keep Service Stubs ruthlessly simple — complexity in a stub defeats its purpose; if your stub grows large, the Gateway interface is probably doing too much.

---

## Record Set

**Category:** Base Patterns

**Intent:** An in-memory representation of tabular data that mimics the interface of a database query result, allowing the same UI and business logic to work with data regardless of whether it came from a database or was constructed in memory.

**How it works:** A Record Set is an in-memory data structure that looks like the result of a SQL query — a collection of rows, each with named columns accessible by field name. Application code (especially UI controls and report generators) is written against the generic Record Set interface rather than against specific objects, so it can consume data from any source that can produce a Record Set. The Record Set may be populated directly by database drivers, constructed by business logic, or assembled from multiple sources. Some platforms (ADO.NET DataSet, JDBC ResultSet) provide a Record Set as a first-class platform type.

**When to use:**
- You are working with a platform (e.g., .NET, classic ADO) that makes Record Sets a natural data-passing currency between database, business, and UI layers.
- UI controls or reporting tools are designed to bind directly to tabular data structures rather than domain objects.
- You need to pass query results across process or tier boundaries without materializing full domain objects.

**When NOT to use:**
- You are building a rich domain model — Record Sets bypass the domain model and couple the UI directly to a relational structure, undermining encapsulation and behavior.
- The data is complex or behavior-rich enough that a typed domain object is clearer and safer.

**Key trade-off:** Easy data binding and platform integration vs. an anemic, schema-coupled data structure that weakens the domain model and type safety.

**Related patterns:** Table Module (a natural companion — Table Module operates on a Record Set as its primary data structure), Data Transfer Object (a typed alternative for passing data across boundaries), Domain Model (the richer alternative when behavior matters more than data binding convenience).

**Practical heuristic:** Use Record Set when the platform demands it or when you are in Table Module territory; switch to typed domain objects as soon as behavior and encapsulation requirements outgrow what a generic tabular structure can express.
