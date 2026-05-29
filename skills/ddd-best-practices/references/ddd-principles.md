# DDD Principles and Application Patterns

Distilled from *Patterns, Principles, and Practices of Domain-Driven Design* by Scott Millett & Nick Tune. Complements the tactical and strategic reference files with practical guidance on applying DDD in real projects.

---

## Knowledge Crunching

**Intent:** Build a shared understanding of the problem domain by actively collaborating with domain experts to extract, refine, and model knowledge.

**How it works / How to apply:** Knowledge crunching is not a one-time phase — it is an ongoing process throughout the lifetime of a project. Deep insights and breakthroughs only emerge after many iterations of working with the domain. Focus sessions on the most important use cases; do not simply read requirements aloud and ask experts to comment. Ask powerful questions to understand the intent behind requirements, not just the requirements themselves.

**Practical heuristic:** Work *with* domain experts, not *for* them — the developer's job is to enable, not to execute requirements blindly.

---

## Impact Mapping

**Intent:** Clarify the business impact a product is trying to make before defining features, so that technical decisions remain aligned with business outcomes.

**How it works / How to apply:** Create a mind-map-like diagram with four levels: the business goal (impact), the actors who can affect it, the ways each actor can help, and the deliverables that enable those ways. This goes beyond requirements documents by surfacing assumptions about who, how, and why. It lets developers suggest superior technical alternatives that business stakeholders would never have thought of.

**Practical heuristic:** Before building any feature, ask: "What business impact does this make, and who does it affect?" — if you cannot trace the feature to the top-level goal, question whether it should be built.

---

## Business Model Canvas

**Intent:** Give developers a fast, structured way to understand the business model so they can ask more meaningful questions during knowledge crunching.

**How it works / How to apply:** Use Alexander Osterwalder's nine-block canvas (Customer Segments, Value Propositions, Channels, Customer Relationships, Revenue Streams, Key Resources, Key Activities, Key Partnerships, Cost Structure) to visualize how the business works. Understanding what the business values, who it serves, and how it makes money enables developers to ask domain-relevant questions and identify what is truly core.

**Practical heuristic:** Spend 30 minutes on a Business Model Canvas before the first knowledge-crunching session — it will transform the quality of questions you ask domain experts.

---

## Deliberate Discovery

**Intent:** Identify and tackle the areas of the problem domain the team is most ignorant about, rather than defaulting to comfortable, well-understood areas.

**How it works / How to apply:** Dan North's technique: at the start of a project, the team makes a concerted effort to identify what they do not know. Unknown unknowns are the single greatest impediment to throughput. Teams should use knowledge-crunching sessions specifically to surface and reduce these gaps, led by domain experts who can focus the team on areas of genuine importance.

**Practical heuristic:** Open each project inception by asking: "What are we most ignorant about?" — then schedule knowledge-crunching sessions specifically around those gaps.

---

## Model Exploration Whirlpool

**Intent:** Provide a structured recovery process when modeling is going wrong — communication is breaking down, designs are overly complex, or domain knowledge is insufficient.

**How it works / How to apply:** Eric Evans's method defines five activities to run in a cycle: Scenario Exploring (domain expert describes a concrete scenario the team is worried about), Modeling (team maps the scenario visually), Challenging the Model (test the model against further scenarios), Harvesting and Documenting (capture key scenarios as reference; do not document every decision), and Code Probing (prove the model can be implemented). Use it on demand, not as a fixed project phase.

**Practical heuristic:** When communication with the business feels strained or the design complexity is rising unexpectedly, invoke the whirlpool rather than pushing forward — the friction is the signal.

---

## Domain Vision Statement

**Intent:** Create a short, explicit statement of what is core to the product so the entire team — including business stakeholders — shares the same understanding of why the software is being built.

**How it works / How to apply:** At project inception, ask stakeholders: "What is the business goal? What value does this bring? How will we know it is a success? How is this different from what has been done before?" Capture the answers in a brief statement and make it visible (posted on the wall). Use it to guide descoping decisions when deadlines conflict with quality. Amazon's "working backwards" practice is a concrete example: write the internal press release first, then build the product.

**Practical heuristic:** If a feature cannot be traced back to the domain vision statement, challenge its inclusion before beginning development.

---

## Problem Domain Distillation (Core / Supporting / Generic)

**Intent:** Break a large problem domain into subdomains to focus effort where it matters most and avoid spending quality on areas that do not need it.

**How it works / How to apply:** Identify three types of subdomains: Core domains — unique competitive differentiators, the reason the software is being written, requiring the best developers and the most investment. Supporting domains — enable core domains but offer no competitive edge; buy off-the-shelf or assign to junior developers. Generic domains — common to many businesses (e-mail, reporting); buy off-the-shelf. What is core to one business may be generic to another. Core domains change over time as competitors catch up.

**Practical heuristic:** Put your best developers on the core domain; for generic and supporting domains, "good is good enough" — perfection there is wasted effort.

---

## Build Subdomains for Replacement, Not Reuse

**Intent:** Keep non-core subdomains isolated and simple so they can be replaced cheaply when business needs change.

**How it works / How to apply:** When building supporting or generic domains, resist the urge to over-engineer. Code them in isolation from other models and legacy code using clean boundaries. Design with replacement in mind: in the future, these subdomains can be swapped for off-the-shelf packages or rewritten as the business evolves. A working but messy supporting subdomain isolated behind a clean boundary is acceptable; a tightly coupled one is not.

**Practical heuristic:** Never invest in reusability for a supporting or generic subdomain — invest in replacability instead.

---

## Treat the Core Domain as a Product, Not a Project

**Intent:** Shift the business and team mindset from delivering a project to investing in a long-lived product so that quality and iteration are sustained over time.

**How it works / How to apply:** Software for core domains is never truly finished; it lives through cycles of feature investment. Technical debt accumulated in a rush to launch becomes a serious liability in complex domains. Maintain a long-term vision shared with business sponsors, and use it to descope features rather than sacrifice code quality. If the business is uncertain whether a product will be successful, build a good-enough first version — but plan to refactor aggressively once it proves its value.

**Practical heuristic:** Ask business sponsors: "What is the three-year vision for this product?" — if they cannot answer, the core domain has not been identified correctly.

---

## Model-Driven Design (Code IS the Model)

**Intent:** Keep the code model and the analysis model in continuous sync by using the same language and concepts in both, so that the code is the authoritative expression of the domain.

**How it works / How to apply:** Traditional processes separate the analysis model (produced by architects) from the code model (built by developers), causing inevitable drift. DDD eliminates this separation: the code IS the model. Changes to domain understanding are immediately reflected in code structure, names, and concepts — and vice versa. When the code model diverges from the business model, it is a signal to re-engage with domain experts. The analysis model should be concrete enough to implement; overly abstract analysis models are not useful.

**Practical heuristic:** If you cannot explain a class or method name to a domain expert using the ubiquitous language, the code model has drifted from the analysis model.

---

## Application Architecture: Dependency Inversion for Domain Isolation

**Intent:** Ensure the domain and application layers remain independent of infrastructure, frameworks, and external systems by inverting all dependencies inward.

**How it works / How to apply:** The domain layer sits at the center and depends on nothing. The application service layer depends only on the domain layer. Outer layers (infrastructure, persistence, UI) depend on the inner layers — never the reverse. The application layer defines interfaces (for persistence, messaging, etc.) that the infrastructure layer implements. This means the domain and application logic can be tested in isolation using mocks/stubs, without touching a database or framework. Clean Architecture, Hexagonal (Ports and Adapters), and Onion Architecture all express this same pattern.

**Practical heuristic:** If a unit test of a domain object requires spinning up a database or framework, the dependency inversion has been violated.

---

## Application Service Layer

**Intent:** Expose the use cases of a bounded context through a coarse-grained, procedural facade that coordinates domain logic without containing any domain logic itself.

**How it works / How to apply:** Application services are thin orchestrators: they retrieve domain objects from persistence, delegate decisions to domain objects, save updated state, and publish notifications. They contain *application logic* (security, transactions, logging, coordination) but zero *domain logic*. They are named after business use cases (not CRUD operations), and their signatures represent the capabilities the system exposes. Application services are stateless except for the state needed to track task progression. They are the concrete implementation of the bounded context boundary — the "anti-corruption layer" protecting the domain from client concerns.

**Practical heuristic:** If an application service method contains an `if` statement that reflects a business rule, extract that rule into the domain layer.

---

## Bounded Context Autonomy: One Team, One Database Schema

**Intent:** Give each bounded context full ownership of its own data schema so that models remain isolated and changes in one context cannot invalidate invariants in another.

**How it works / How to apply:** Integration databases — where multiple bounded contexts share a single schema — make it easy to bypass the application service layer and directly manipulate domain state, invalidating invariants. Each bounded context should own its schema; they may share the same physical database but must use separate schemas. When contexts need data from each other, they communicate through application service APIs, not database joins. Different bounded contexts can use different architectural styles (CRUD, layered DDD, CQRS) without consistency across contexts.

**Practical heuristic:** If two teams can write to the same database table, they are sharing a model and the boundary is not real.

---

## Composite UI

**Intent:** Decompose the user interface so that each region of the screen is owned by the bounded context responsible for that business capability, rather than having a single shared presentation layer.

**How it works / How to apply:** Each bounded context exposes application services with coarse-grained methods. A composite UI assembles views from multiple bounded contexts via multiple API calls (for example, Ajax). This protects model integrity because the UI adapts to the bounded context's API contract rather than the context exposing its internal model. Different bounded contexts can own different UI regions independently.

**Practical heuristic:** If changing the domain model of a bounded context forces a change in a shared presentation layer, the UI is not properly decomposed.

---

## Context Game

**Intent:** Reveal when a single term or concept means different things to different parts of the business, signaling the need for separate bounded contexts.

**How it works / How to apply:** Pioneered by Greg Young. During knowledge-crunching sessions, when you suspect a term is overloaded, split the group by business department or responsibility. Give each group 20 minutes to define the term from their perspective. Reassemble and compare definitions. Where the definitions diverge, draw a context boundary. This is a low-cost workshop exercise that surfaces model boundaries without requiring up-front architecture decisions.

**Practical heuristic:** Any term that business experts from different departments define differently is a candidate context boundary.

---

## Team Topology Aligned to Bounded Contexts

**Intent:** Assign bounded context ownership to individual teams so that autonomy in the model is matched by autonomy in the team structure.

**How it works / How to apply:** Following Amazon's "two-pizza team" rule, no development team should be so large that it cannot be fed by two pizzas. Each team owns one or a set of bounded contexts and is responsible for all layers (presentation, domain, persistence, database schema). This allows teams to move fast without coordinating with others. Teams should hold regular cross-team knowledge-sharing sessions and practice cross-team pair programming (moving a developer to another team for a few days) to maintain system-level understanding without tight coupling.

**Practical heuristic:** If a feature request requires a meeting between three or more teams before any code can be written, the bounded context boundaries are drawn in the wrong place.

---

## DDD Adoption Anti-Patterns

**Intent:** Avoid the failure modes that cause teams to get the cost of DDD without the benefit.

**How it works / How to apply:** Four primary anti-patterns: (1) *DDD Lite* — applying tactical patterns (Entity, Aggregate, Repository) without the strategic work (UL, bounded contexts, knowledge crunching). The patterns are a by-product of the collaboration, not its goal. (2) *Tactical pattern perfection* — spending energy ensuring every class conforms to a pattern rather than solving business problems. (3) *Applying DDD to simple domains* — full DDD is not appropriate for CRUD-heavy supporting domains; use Transaction Script or Active Record there. (4) *Seeking validation* — the DDD process is not a certification; blindly following a pattern language to comply with a methodology is the opposite of DDD's intent.

**Practical heuristic:** Before applying any DDD pattern, ask: "Is this extra complexity helping me deliver business value, or is it satisfying a methodology?"

---

## Conditions for DDD to Succeed

**Intent:** Identify the minimum set of prerequisites without which applying DDD will overcomplicate rather than simplify development.

**How it works / How to apply:** DDD requires four things to be in place simultaneously: (1) A complex, nontrivial problem domain important to the business. (2) Access to engaged domain experts who understand the intent of the project. (3) An iterative development methodology — models must evolve over many cycles. (4) A focused, motivated team with solid design skills and willingness to learn the domain. Without all four, simpler approaches (CRUD, Transaction Script) will outperform DDD. The right time to apply DDD is when you encounter complexity or ambiguity — start simple and apply practices as needed.

**Practical heuristic:** If any of the four prerequisites is missing, apply the strategic patterns of DDD (UL, subdomains, context map) but do not invest in the tactical domain model pattern.

---

## Nontechnical Refactoring

**Intent:** Continuously update code structure, names, and namespaces to reflect deepening domain knowledge, not just technical quality improvements.

**How it works / How to apply:** As knowledge-crunching sessions reveal new domain concepts and more insightful abstractions, the codebase must be updated to reflect those discoveries. Class names, method names, and namespaces should evolve to match the growing ubiquitous language. When a grouping of implicit code logic represents a domain concept without an explicit name, name it, inform the domain expert, and wrap it in a concept. This "nontechnical refactoring" is distinct from technical refactoring and is the primary mechanism by which a domain model stays relevant and expressive over time.

**Practical heuristic:** After every knowledge-crunching session, schedule a refactoring session to rename and restructure code to reflect any new domain concepts that emerged.

---

## Supple Design via Delayed Refactoring

**Intent:** Avoid premature refactoring by letting the code live long enough to reveal which areas change most often — then refactor to address real friction, not imagined future needs.

**How it works / How to apply:** Martin Fowler's principle (from *Analysis Patterns*): "Design a model so that the most frequent modification of the model causes changes to the least number of types." A supple design is one that accommodates change with minimal ripple effects. Premature refactoring, driven by aesthetic preferences rather than evidence of friction, wastes effort and can obscure real change patterns. Let code accumulate enough change requests to reveal natural seams, then refactor with confidence. TDD enables safe exploration because tests survive refactoring.

**Practical heuristic:** Do not refactor for elegance until you have seen the same area of code change at least twice — let reality reveal the seams.

---

## Making the Implicit Explicit

**Intent:** Surface hidden domain concepts buried in code as ad-hoc conditionals and logic blocks, name them, and make them first-class citizens of the domain model.

**How it works / How to apply:** Implicit domain logic disguised as generic programming constructs (long `if` chains, flag fields, complex conditional expressions) hides important details from the model. When you find such a grouping, ask the domain expert what it represents, name the concept in the UL, and wrap the logic in a named class or method. This is how the model grows richer over time. Every implicit concept made explicit is a breakthrough that enables further discoveries and deeper collaboration.

**Practical heuristic:** When a domain expert cannot explain what a code block does without you first translating it into business terms, that block contains an implicit concept that needs to be named.

---

## Modeling Around Concrete Scenarios, Not Abstract Reality

**Intent:** Prevent overengineering by driving model design from specific, concrete business scenarios rather than from abstract representations of the entire domain.

**How it works / How to apply:** Select a behavior the product needs to implement, define two to four concrete scenarios for that behavior (using BDD-style Given/When/Then), and model only enough to satisfy those scenarios. This prevents developers from producing a one-model-to-rule-them-all view that reflects reality but is not useful as an abstraction. After the model satisfies the scenarios, challenge it with additional scenarios from the domain expert to verify its usefulness before committing to the application namespace.

**Practical heuristic:** If a model element cannot be validated against at least one concrete business scenario, it is speculative — do not commit it to the codebase yet.

---

## Process Manager

**Intent:** Coordinate long-running business processes that span multiple bounded contexts without embedding cross-context orchestration logic inside any single context.

**How it works / How to apply:** When a business process (for example, an order fulfillment workflow) touches multiple bounded contexts, a process manager (also known as a saga coordinator) tracks the state of the overall business task and delegates individual steps back to the relevant bounded contexts via messaging or web service calls. The process manager is stateless except for the state required to track task progression. It does not contain domain logic — only coordination logic. It is similar to an application service but operates at the inter-context level.

**Practical heuristic:** If an application service in one bounded context is directly calling the domain layer of another bounded context, extract the coordination into a process manager.

---

## DDD Is a Learning Process, Not a Destination

**Intent:** Establish the correct philosophical frame for DDD adoption: it is a continuous journey of learning, refining, and experimenting — not a methodology to be implemented and certified.

**How it works / How to apply:** A useful domain model is the product of hundreds of small refactorings, experiments, and conversations. The first model will be wrong. The second will be closer. For a complex core domain, a team should expect to produce at least three models before arriving at something genuinely useful. Wrong models have value: they reveal what does not work and sharpen understanding. Exploration and experimentation are the engine; the code artifact is just the current iteration. Challenge assumptions constantly; a model that was useful last sprint may be inadequate for the next set of features.

**Practical heuristic:** If your team has not thrown away at least one model on a complex domain, you probably stopped exploring too early.
