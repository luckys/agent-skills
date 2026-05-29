# Context Mapping

A Context Map documents the relationships between Bounded Contexts. Each relationship type has different implications for autonomy, coupling, and translation effort. The map is not just a technical diagram — it captures organizational dynamics, power structures, and integration strategies between teams.

---

## Partnership

**Relationship type:** Peer-to-peer, mutual dependency

**Intent:** Two teams with a mutual dependency cooperate closely so that neither can succeed without the other.

**How it works:** Both teams agree on an interface and coordinate their schedules so neither blocks the other. Failures in one context propagate to the other, so the relationship demands active ongoing collaboration. Teams hold joint planning sessions, share release cycles, and jointly own the integration points.

**When to use:**
- Two teams are building closely related contexts that must go live together
- Both teams have equal organizational standing and willingness to coordinate
- Tight coupling is genuinely necessary and unavoidable for the business goal

**When NOT to use:**
- One team has clear authority or control over the interface (use Customer-Supplier instead)
- Teams are geographically or organizationally distant with poor communication channels
- Long-term stability is required — Partnership is fragile if one team's priorities shift

**Key trade-off:** Highest integration fidelity, but shared fate. One team's dysfunction or delays immediately affect the other.

**Practical heuristic:** If you find yourself describing the relationship as "we rise or fall together," it is a Partnership. Document that explicitly — otherwise it defaults to an unacknowledged and fragile dependency.

---

## Shared Kernel

**Relationship type:** Peer-to-peer, shared code ownership

**Intent:** Two teams agree to share a small, explicitly defined subset of the domain model, jointly owning it and treating any change as requiring mutual consent.

**How it works:** A designated portion of code (entities, value objects, events, or a shared library) is jointly maintained. Neither team may change the shared subset without consulting the other. Both teams run their respective test suites against the shared kernel to detect breakage. This forms an intimate relationship that requires ongoing consultation.

**When to use:**
- Two contexts share a small, stable core that would be expensive to duplicate or translate
- Both teams have strong discipline and communication to enforce joint ownership
- The shared piece is truly domain-meaningful, not just a utility library

**When NOT to use:**
- The shared subset keeps growing — this is a signal that boundaries are wrong, not that sharing should expand
- Teams lack the discipline to enforce mutual consent on changes
- The contexts are owned by teams with different release cadences or priorities

**Key trade-off:** Reduces translation overhead for the shared part, but creates a tight coupling point that resists independent evolution.

**Practical heuristic:** Keep the Shared Kernel as small as possible. If you cannot put it on an index card, it is too large. Treat every addition to it as an architectural decision requiring both teams' approval.

---

## Customer-Supplier Development Teams

**Relationship type:** Upstream (Supplier) / downstream (Customer), negotiated

**Intent:** The downstream (Customer) team can influence the upstream (Supplier) team's planning, negotiating what features and interface changes are prioritized.

**How it works:** The upstream team acts as a supplier of services or APIs. The downstream team is the customer and has legitimate standing to raise requirements and place them in the upstream team's backlog. Planning happens collaboratively — the upstream team commits to meeting downstream needs within agreed timelines. Acceptance tests written by the downstream team validate that the upstream delivers what was promised.

**When to use:**
- The upstream team is inside the same organization and responsive to business pressure
- The downstream team needs specific functionality or interface changes from upstream
- There is a governance or product management structure that can enforce upstream accountability

**When NOT to use:**
- The upstream is a third-party vendor or external system that cannot be influenced (use Conformist or ACL instead)
- The upstream team has no incentive to prioritize downstream needs
- Negotiation overhead would exceed the cost of building a local solution (use Separate Ways)

**Key trade-off:** Gives downstream teams a voice, but requires trust, organizational support, and ongoing negotiation investment.

**Practical heuristic:** Write acceptance tests as the first artifact of every Customer-Supplier negotiation. If the upstream team will not run your tests, the relationship has silently become Conformist.

---

## Conformist

**Relationship type:** Upstream / downstream, upstream-controlled

**Intent:** The downstream team accepts and conforms to the upstream model entirely, with no translation layer and no ability to influence the upstream design.

**How it works:** The downstream team adopts the upstream's model as-is, using its types, structures, and language directly in their own code. There is no negotiation — the upstream publishes whatever it publishes, and the downstream adapts. This is common when integrating with external systems, SaaS platforms, or powerful internal platforms that dictate their own model.

**When to use:**
- The upstream team cannot or will not accommodate downstream needs
- The upstream model is close enough to the downstream's needs that translation would add more complexity than it removes
- Speed of integration matters more than model purity
- The upstream is a third-party system or a dominant platform within the organization

**When NOT to use:**
- The upstream model is a Big Ball of Mud that would corrupt the downstream's core domain
- The downstream is a Core Domain where model integrity is a competitive differentiator
- Concepts between contexts are semantically different despite sharing names

**Key trade-off:** Lowest integration effort, but the downstream model is permanently coupled to whatever the upstream publishes, including its deficiencies.

**Practical heuristic:** If you are conforming to an upstream you do not control and the upstream model is poor quality, switch to an Anticorruption Layer. Conformist is only appropriate when the upstream model is acceptable to live with long-term.

---

## Anticorruption Layer (ACL)

**Relationship type:** Upstream / downstream, downstream-protected

**Intent:** The downstream team builds an explicit translation layer that insulates its own model from the upstream's model, converting between representations at the boundary.

**How it works:** The ACL is a set of adapters, translators, and facades that sit between the downstream context and the upstream system. The downstream model never sees the upstream's types directly — all data flows through the ACL, which converts it into terms and structures that fit the downstream's Ubiquitous Language. The ACL is typically implemented as Domain Services, Anti-Corruption Services, or repository adapters that call upstream APIs and return local domain objects.

**When to use:**
- Integrating with a legacy system, Big Ball of Mud, or third-party API whose model does not align with your domain
- The upstream model would corrupt the semantics or integrity of the downstream Core Domain
- You want to be able to swap out the upstream system later without touching the rest of the downstream model
- The downstream context is a Core Domain whose model integrity must be preserved

**When NOT to use:**
- The upstream model is clean and the concepts genuinely align — an ACL adds complexity for no benefit
- The integration is trivial and temporary
- The downstream team is a Conformist context where model purity is not critical

**Key trade-off:** Maximum protection of the downstream model's integrity, at the cost of translation code that must be maintained as both models evolve.

**Practical heuristic:** Every integration with a legacy system or external API should default to an ACL until you have a concrete reason not to build one. The cost of building it is always less than the cost of retroactively removing corruption from your Core Domain.

---

## Open Host Service

**Relationship type:** Upstream / multiple downstream consumers, publisher-controlled

**Intent:** The upstream context defines an explicit protocol or API that any downstream consumer can use, removing the need for bespoke integrations for each consumer.

**How it works:** The upstream team designs a well-structured, versioned service interface — typically a REST API, gRPC contract, or messaging interface — and publishes it as a stable access point. Each downstream consumer integrates against this standard interface. The upstream team manages the protocol as a product, versioning it and maintaining backward compatibility. The interface may be described using a Published Language.

**When to use:**
- Multiple contexts or external consumers need to integrate with one upstream context
- The upstream team wants to support a variety of consumers without negotiating bespoke integrations for each
- A standardized, stable API surface reduces integration friction across the organization

**When NOT to use:**
- There is only one downstream consumer — bespoke integration is simpler
- The upstream model changes too rapidly to maintain a stable public protocol
- Consumers have radically different needs that a single protocol cannot serve well

**Key trade-off:** One well-maintained interface scales to many consumers, but the upstream team takes on the overhead of designing and versioning a public protocol.

**Practical heuristic:** An Open Host Service should be treated like a product with real API design discipline — versioning, documentation, deprecation policy. If those practices are absent, it will degrade into a poorly understood point-to-point integration.

---

## Published Language

**Relationship type:** Upstream / downstream, documentation-mediated

**Intent:** A well-documented, shared language (schema, format, or protocol) is defined and used as the medium of exchange between contexts, so that both sides can understand and validate the data independently.

**How it works:** Rather than relying on informal knowledge of each other's internal models, two or more contexts agree on a Published Language — a formally defined, versioned format such as JSON Schema, XML Schema, Avro schema, OpenAPI spec, or a domain event schema registry. Each context translates to and from this language at its boundary, rather than depending on the other context's internal representation directly. Published Language is often paired with Open Host Service.

**When to use:**
- The integration crosses organizational or system boundaries where informal knowledge sharing is unreliable
- Multiple consumers need to independently implement against the same data contract
- Long-term stability and clear versioning of the data exchange format are required
- The downstream context needs to validate incoming data against a known schema

**When NOT to use:**
- The integration is entirely internal, well-understood, and short-lived
- Both contexts are owned by the same team and can evolve the interface together informally
- The overhead of schema management outweighs the coordination benefit

**Key trade-off:** Explicit contracts enable independent evolution and validation, but require governance of the schema over time.

**Practical heuristic:** Publish the language in a schema registry or shared documentation repository. If the language only exists in team members' heads or in one team's code, it is not truly Published.

---

## Separate Ways

**Relationship type:** No integration, full independence

**Intent:** Two contexts have no meaningful relationship and should be kept entirely separate, with each team solving its needs independently.

**How it works:** The decision is made that integrating two contexts would cost more than duplicating the functionality or solving problems separately. Each context implements what it needs without coupling to the other. This is not an oversight or a temporary state — it is a deliberate architectural decision to keep two areas of the system fully decoupled.

**When to use:**
- The integration cost (translation, coordination, versioning) exceeds the benefit of sharing
- The two contexts address genuinely different problems with no meaningful overlap
- The functional duplication is small and cheap to maintain independently
- Teams are in entirely different business units with separate priorities and budgets

**When NOT to use:**
- There is actual shared domain data that must remain consistent across both contexts
- The duplication leads to divergence that will confuse users or create data integrity issues
- The choice is driven by convenience or avoidance of coordination rather than a genuine analysis

**Key trade-off:** Maximum autonomy and zero coupling, but potential duplication of effort and loss of consistency if the "separate" assumption later proves wrong.

**Practical heuristic:** Document the Separate Ways decision explicitly on the Context Map with a brief rationale. Without documentation, future teams will not understand why integration was not built and may add it inappropriately — or waste time investigating a gap that was intentional.

---

## Big Ball of Mud

**Relationship type:** No clear boundaries, legacy/unstructured

**Intent:** Acknowledges the existence of a large, legacy, unstructured system with no clear internal model boundaries, so that new systems can plan accordingly.

**How it works:** The Big Ball of Mud is not a pattern to build — it is a pattern to recognize and document. It describes a legacy system or module where internal models are tangled, terminology is inconsistent, and boundaries between concerns have eroded over time. When a new Bounded Context must integrate with a Big Ball of Mud, it draws a hard boundary around the mud and uses an Anticorruption Layer to prevent the disorder from leaking in. The Big Ball of Mud itself is acknowledged on the Context Map as a zone of known disorder.

**When to use:**
- Documenting the reality of a legacy system that cannot be immediately refactored
- Planning an integration with an existing unstructured system so the new context can protect itself
- Communicating to stakeholders the scope and risk of legacy integration work

**When NOT to use:**
- As a justification for building new systems without boundaries ("it will just grow")
- As a permanent state — the goal is always to strangle or refactor the mud over time

**Key trade-off:** Acknowledging the Big Ball of Mud prevents teams from pretending it is a clean context. The risk is that recognizing it makes it easy to leave it in place indefinitely.

**Practical heuristic:** Draw a Big Ball of Mud on the Context Map whenever a legacy system is involved. Pair it with an ACL on the downstream side. Plan incremental strangling to reduce its footprint over time.

---

## How to Draw a Context Map

Drawing a Context Map is a collaborative, discovery-driven activity — not a documentation task done in isolation after the fact.

**Steps:**

1. **Identify all Bounded Contexts.** List every system, subsystem, module, or application that has its own Ubiquitous Language and team ownership. Include third-party systems, legacy platforms, SaaS products, and external APIs.

2. **Identify all integration points.** For each pair of contexts that exchange data or call each other, draw a line. Do not assume integration exists — verify it by talking to the teams and reading the code.

3. **Determine upstream and downstream direction.** Ask: whose model influences the other? The upstream team publishes; the downstream team consumes and must adapt. Upstream is typically the one with less need to change. Mark direction with arrows (U → D).

4. **Name the relationship pattern.** For each integration line, assign one of the nine patterns based on organizational dynamics and technical reality. Discuss with both teams — they often have different perceptions of the relationship type.

5. **Note translation mechanisms.** For each integration, mark whether an ACL, Published Language, or Open Host Service is in place — or whether the downstream is conforming directly to the upstream model.

6. **Mark organizational dynamics.** Note which contexts are Core Domains, Supporting Subdomains, and Generic Subdomains. The relationship pattern should generally protect Core Domains from upstream corruption.

7. **Post it visibly.** A Context Map should be a physical or wiki artifact visible to all teams. It is a living document — update it when teams change, systems are integrated, or relationship patterns shift.

---

## Reading a Context Map

**Upstream / downstream arrows** indicate the direction of model influence, not necessarily data flow. The upstream team's model shapes what the downstream must adapt to. An upstream team with no accountability to downstream consumers is a signal of either Conformist or ACL, not Customer-Supplier.

**Translation responsibility** always falls on the downstream side. If a downstream context integrates with an upstream without an ACL, it is either Conformist (intentional) or an undetected corruption risk (a problem). The presence of an ACL on the map signals the downstream team is actively protecting its model.

**Coupling signals.** Partnership and Shared Kernel indicate the highest coupling — both teams are mutually affected by changes. Customer-Supplier is asymmetric but negotiated. Conformist and ACL are asymmetric with no upstream accountability. Open Host Service and Published Language decouple via contracts. Separate Ways means no coupling. Big Ball of Mud means unknown or unmapped coupling.

**Interpreting risk.** A Core Domain downstream of a Big Ball of Mud with no ACL is a high-risk integration — corruption will spread. A Core Domain using Separate Ways for non-essential functionality is healthy autonomy. Multiple Conformist relationships in a Core Domain are a warning that the team has lost control of its model.

**Map evolution.** Context Map relationships change as organizations evolve. A Partnership that becomes a Customer-Supplier after a reorg is not a failure — it is normal. The map must be updated to reflect reality, or it becomes misleading. Treat relationship pattern changes as architectural decisions worth recording.
