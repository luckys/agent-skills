# Strategic Design

Strategic DDD decisions define boundaries, relationships, and investment priorities across the domain. They are made before writing tactical code and shape the entire architecture.

---

## Ubiquitous Language

**Definition:** A shared, rigorous vocabulary co-created by developers and domain experts that is used consistently in conversation, code, diagrams, and documentation within a Bounded Context.

**Why it matters:** Without a shared language, developers translate between their mental model and the domain experts' language constantly — and every translation is a place where understanding is lost. When the model-based language is spoken pervasively, the model becomes a living artifact rather than a design document. A change in the Ubiquitous Language is a change in the model: the two must stay in sync.

**How to identify / apply:**
- Run collaborative modeling sessions (e.g., Event Storming) where domain experts and developers name things together out loud.
- Reject vague terms like "data," "record," or "process" — push until you get precise domain words (e.g., `BacklogItem`, `Sprint`, `Volunteer`).
- Use the exact same terms in class names, method names, variable names, test names, and spoken conversation — no synonyms.
- When a term feels awkward or is used inconsistently, treat it as a modeling signal: the model is incomplete or wrong.
- Domain experts should object to terms that fail to convey domain understanding; developers should flag ambiguity or inconsistency.
- Maintain a glossary in the project repository, but keep it lightweight — the code is the primary artifact.

**Common mistakes:**
- Developers invent technical names that domain experts never use ("UserRecord", "DataProcessor"), creating a silent translation layer.
- Using the same word with different meanings in different parts of the codebase without realizing it.
- Letting the language drift — the code uses old terms after the team agrees on new ones.
- Treating the Ubiquitous Language as documentation rather than as the actual operating vocabulary of daily work.

**Practical heuristic:** If a domain expert reads your class and method names and finds them foreign or imprecise, the Ubiquitous Language is broken — fix the names before writing more code.

---

## Bounded Context

**Definition:** A semantic boundary within which a specific domain model applies, every term has a precise meaning, and the model is consistently implemented as code.

**Why it matters:** In any large system, the same word means different things in different parts of the business ("Account" in billing is not the same as "Account" in identity). Forcing a single unified model across the entire organization produces a bloated, ambiguous mess. A Bounded Context enforces that one team, one model, one language applies within its boundary — model integrity is maintained by the boundary itself.

**How to identify / apply:**
- Look for places where the same term changes meaning: each distinct meaning signals a potential context boundary.
- Align Bounded Contexts with team ownership: one team should own one context; cross-team models become ambiguous quickly.
- Start conceptually (problem space) — what is this context responsible for? — then make it concrete in code (solution space).
- Each Bounded Context has its own codebase, its own schema, and deploys independently where possible.
- Name each context explicitly and add it to the Ubiquitous Language of the larger system.
- Example: a Scrum tool might have a `Project Management` context (BacklogItem, Sprint, Task) and a separate `Collaboration` context (Discussion, Forum, Post) — "Discussion" belongs in Collaboration, not in Project Management.

**Common mistakes:**
- Creating one giant shared model that tries to serve all contexts — it satisfies none of them well.
- Confusing a Bounded Context with a microservice — they are related but not the same; a context is a logical boundary, a service is a deployment unit.
- Letting two teams modify the same context, causing language and model drift.
- Failing to name the context explicitly, leaving its purpose ambiguous.

**Practical heuristic:** A Bounded Context is the right size when one small team can hold its entire model in their heads and speak its language fluently without a translation guide.

---

## Subdomain Types: Core, Supporting, and Generic

**Definition:** A subdomain is a distinct area of the business domain; it is classified as Core (competitive differentiator), Supporting (necessary but not differentiating), or Generic (commodity functionality used everywhere).

**Why it matters:** Not all parts of the domain deserve the same investment. Applying your best engineers and deepest modeling effort to generic infrastructure is waste; failing to invest heavily in your Core Domain cedes competitive advantage. Subdomain classification is how you decide where to spend money, time, and talent.

**How to identify / apply:**

*Core Domain:*
- The part of the business that provides unique competitive advantage — what the organization does better than anyone else.
- If a competitor had this capability, it would significantly erode your market position.
- Invest here: best engineers, richest models, most rigorous testing, highest code quality.
- Examples: a recommendation engine at a streaming company, a pricing algorithm at an insurance firm, a routing optimizer at a logistics company.

*Supporting Subdomain:*
- Necessary for the Core Domain to function, but does not differentiate the business on its own.
- Custom development is still needed because off-the-shelf solutions do not fit, but it does not need your best engineers.
- Examples: HR management for a software company, an internal notification system, a custom reporting module.

*Generic Subdomain:*
- Standard functionality that every business needs and that is solved well by existing products.
- Do not build it — buy or adopt an existing solution (identity providers, payment processors, email delivery, calendar services).
- Examples: authentication/authorization, PDF generation, accounting ledgers.

**Common mistakes:**
- Treating everything as Core Domain and over-investing everywhere equally.
- Building a Generic Subdomain from scratch because "we want control" — this is almost always waste.
- Misclassifying a Supporting Subdomain as Core because domain experts are enthusiastic about it.
- Not revisiting classifications — what is Generic today may become Core as the market evolves, or vice versa.

**Practical heuristic:** Ask "If we bought this capability off-the-shelf, would we lose competitive advantage?" Yes → Core. No, but we still need custom code → Supporting. No, and a product already solves it well → Generic.

---

## Relationship Between Subdomains and Bounded Contexts

**Definition:** A Subdomain is a problem-space concept (a slice of the business domain); a Bounded Context is a solution-space concept (a boundary around a model in code). In an ideal design they align one-to-one, but in practice they often do not.

**Why it matters:** Confusing the two leads to architectural mistakes: you might force multiple subdomains into one context (creating a muddled model) or split a single subdomain across many contexts (making integration painful). Understanding the relationship helps you reason about design trade-offs clearly.

**How to identify / apply:**
- Start by identifying subdomains in the problem space through domain exploration with stakeholders.
- Then design Bounded Contexts in the solution space, aiming for one context per subdomain as the default.
- When legacy systems exist, one Bounded Context may contain multiple subdomains — recognize this as technical debt and work to separate them.
- When a team is small, one team may own multiple contexts — that is acceptable as long as each context's model stays distinct.
- Use a Context Map to make the relationships between all contexts explicit and visible.

**Common mistakes:**
- Designing Bounded Contexts before understanding the subdomains — you get boundaries in the wrong places.
- Assuming one-to-one alignment always exists — legacy systems and organizational realities often prevent it.
- Ignoring the subdomain classification when sizing the Bounded Context — Generic Subdomains should get minimal custom modeling.

**Practical heuristic:** Draw the subdomain map first (problem space), draw the context map second (solution space), then compare them — gaps and misalignments are architectural risks that need a decision, not an assumption.

---

## Context Mapping

**Definition:** A context map is an explicit document (or diagram) that identifies all Bounded Contexts in a system and describes the relationships and integration patterns between them.

**Why it matters:** Most systems have multiple Bounded Contexts that must exchange data. Without a map, integration patterns are implicit and ad-hoc, leading to tight coupling, model pollution, and unclear team responsibilities. The map makes dependencies a first-class architectural concern.

**How to identify / apply:**
- Identify every context boundary in the system and give each a name.
- For each pair of contexts that exchange data, choose an integration pattern:
  - **Partnership:** two teams coordinate closely and evolve their models together.
  - **Shared Kernel:** two contexts share a small, explicitly agreed-upon subset of the model — changes require joint approval.
  - **Customer/Supplier (Upstream/Downstream):** the upstream context produces; the downstream context consumes. The upstream can influence but does not own the downstream's needs.
  - **Conformist:** the downstream simply conforms to the upstream's model with no negotiation (common with third-party systems).
  - **Anti-Corruption Layer (ACL):** the downstream context builds a translation layer to protect its model from the upstream's concepts bleeding in.
  - **Open Host Service:** the upstream publishes a stable, versioned protocol for many consumers.
  - **Published Language:** a shared, documented interchange format (e.g., JSON schema, Protobuf) agreed upon by multiple contexts.
- Draw the map and review it with all team leads — disagreements reveal real architectural tensions.

**Common mistakes:**
- Not drawing the map at all and letting integrations grow organically.
- Letting a dominant upstream context's model bleed into downstream contexts without an ACL, polluting their Ubiquitous Language.
- Using Shared Kernel too broadly — it creates tight coupling between teams.
- Forgetting to update the Context Map as the system evolves.

**Practical heuristic:** Every integration between two Bounded Contexts needs a named pattern on the Context Map — if you cannot name it, the integration is unplanned and therefore a risk.

---

## Core Domain Distillation

**Definition:** Distillation is the process of identifying, isolating, and emphasizing the Core Domain so that the most valuable parts of the system receive the most investment and remain clearly separated from supporting and generic concerns.

**Why it matters:** In any large system, the Core Domain tends to become buried under layers of infrastructure, generic utilities, and supporting logic. Distillation keeps it visible, protected, and well-funded. It is the strategic answer to the question: "What is this software for, and what must it do extraordinarily well?"

**How to identify / apply:**
- Write a Core Domain statement — one paragraph that says exactly what the Core Domain does and why it matters competitively. If you cannot write it, you have not found it yet.
- Create a Core Domain map or highlight document that marks which models, aggregates, and services belong to the Core and which do not.
- Move generic concerns (logging, authentication, email) out of Core Domain code into their own modules or external services.
- Move Supporting Subdomain logic into separate contexts rather than co-locating it with Core Domain models.
- Protect Core Domain vocabulary: the Ubiquitous Language of the Core must not be contaminated by terms from generic or supporting subdomains.
- Assign your most skilled engineers to Core Domain work. Delegate Generic Subdomain work to less senior engineers or third-party products.
- For Generic Subdomains: default to buying (SaaS, open source, vendor libraries). Build only when no adequate solution exists or when the subdomain is on a path to becoming Core.

**Common mistakes:**
- Building all subdomains to the same quality bar — over-engineering Generic Subdomains and under-engineering the Core.
- Allowing the Core Domain to accumulate generic utilities until it becomes unclear what is Core.
- Buying off-the-shelf for a subdomain that is actually Core (ceding competitive advantage to a vendor).
- Failing to maintain the Core Domain statement — as the market changes, what is Core changes.

**Practical heuristic:** If you stripped out everything except the Core Domain code and showed it to a domain expert, they should recognize immediately what the software is for and what makes it valuable — if not, the Core has been obscured.

---

## Large-Scale Structure

**Definition:** A large-scale structure is a set of high-level rules and patterns (such as responsibility layers or a knowledge-level model) that organizes the entire system and gives it a coherent shape across all Bounded Contexts.

**Why it matters:** As systems grow, individual Bounded Contexts and their Context Maps can become difficult to reason about without an overarching structural metaphor. A large-scale structure gives every team a mental model for where things belong, reducing the cognitive overhead of navigating the full system.

**How to identify / apply:**
- Identify whether a layering metaphor fits: e.g., Responsibility Layers (Operational, Capability, Policy, Decision Support) where each layer depends only on layers below it.
- Apply the structure loosely — it is a guide, not a rigid constraint. Contexts that do not fit neatly should still be mapped, and the mismatch surfaced for a deliberate decision.
- Evolve the structure as the system evolves; do not freeze it early.
- Use the structure to explain the system to new team members: "All policy logic lives in the Policy Layer; all operational models live in the Operational Layer."
- Only introduce a large-scale structure when the system is large enough that navigation without it becomes a real problem.

**Common mistakes:**
- Inventing an elaborate large-scale structure before the system is complex enough to need one.
- Enforcing the structure rigidly, causing teams to fight the structure instead of modeling their domain naturally.
- Conflating large-scale structure with microservice topology — they are different concerns.

**Practical heuristic:** A large-scale structure is worth defining when a new team member asks "where does X belong?" and the answer requires more than a five-minute conversation — at that point, make the structure explicit.

---

## Related Skills

- `design-patterns-best-practices` — tactical patterns for implementing models within a Bounded Context (Aggregate, Repository, Domain Event).
- `oop-best-practices` — object boundaries, value objects, and cohesion within a single context's model.
- `refactoring-best-practices` — incremental extraction of Core Domain code from legacy monoliths.
