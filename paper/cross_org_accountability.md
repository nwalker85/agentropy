# Cross-Organizational Agent Accountability Without Trust: A Conservation Law Approach

**Agent Mass Theory Applied to Multi-Party Agent Traversal**

*Nathan Walker — Ravenhelm*
*February 2026*

---

## Abstract

When an autonomous agent traverses infrastructure owned by multiple independent organizations, a fundamental problem arises: how does each organization verify the agent's consumption on its own infrastructure without trusting any other party? Traditional approaches — OAuth scoping, RBAC, smart contracts, distributed audit logs — all require some form of shared trust: a trusted identity provider, a shared ledger, a consensus mechanism, or a mutually agreed-upon audit framework. We present an alternative grounded in Agent Mass Theory (AMT), where a conservation law governs every agent-environment interaction. The law `C_{n+1} + S_{n+1} + L_n = C_n` — which states that an agent's cipher mass after interaction plus signal extracted plus loss incurred equals the cipher mass before interaction — is enforced locally at every interaction, with no knowledge of organizational boundaries. We prove three theorems: (1) conservation is invariant under organizational partitioning of the topology, (2) each organization can independently verify conservation on its own nodes without access to other organizations' data, and (3) no organization can determine another's consumption from the public ledger. We demonstrate these properties with a working implementation where three organizations — a deployer, a processor, and a validator — share no secrets after agent deployment, yet achieve full auditability through conservation law enforcement alone. At population scale (200 agents, 457 interactions), zero conservation violations occur. The math is the accountability.

---

## 1. Introduction

### The Cross-Org Trust Problem

Modern agent architectures increasingly require agents to traverse infrastructure owned by multiple parties. A customer deploys an agent that processes data through a vendor's compute nodes, gets validated by a third-party auditor, and returns results. Each party has legitimate interests:

- **The deployer** needs assurance that its agent was processed correctly and that no more resources were consumed than intended.
- **The processor** needs assurance that it can account for all resources consumed on its infrastructure.
- **The validator** needs assurance that its audit stamp means what it claims.
- **No party** wants to reveal its internal operations to any other party.

The standard approach is to layer trust mechanisms: OAuth tokens scope agent permissions, RBAC matrices control access, audit logs record transactions, and smart contracts enforce agreements. Each mechanism requires a shared trust anchor:

| Mechanism | Trust Requirement |
|-----------|-------------------|
| OAuth/OIDC | Trusted identity provider |
| RBAC | Mutually agreed permission schema |
| Smart contracts | Consensus mechanism (blockchain) |
| Audit logs | Tamper-evident shared storage |
| Zero-knowledge proofs | Trusted setup ceremony |

**The fundamental issue**: all of these are *protocols*. Protocols can be violated, evaded, or rendered irrelevant by implementation bugs. A conservation law cannot.

### Conservation Laws as Trust Substitutes

In physics, conservation laws do not require participants to agree on anything. Energy is conserved whether or not the particles involved have negotiated a protocol. Mass is conserved whether or not the chemical reactants trust each other.

Agent Mass Theory (AMT) establishes a conservation law for digital agents:

```
C_{n+1} + S_{n+1} + L_n = C_n
```

Where:
- `C_n` is the agent's cipher mass (total encrypted bytes) before interaction
- `C_{n+1}` is the cipher mass after interaction
- `S_{n+1}` is the signal extracted (information yield from non-empty layers)
- `L_n` is the loss incurred (mass consumed without information yield)

This law is enforced at every interaction by construction. It does not know about organizations. It does not require authentication, authorization, or agreement. It simply holds.

This paper demonstrates that this property — organizational-boundary invariance — makes AMT a natural framework for cross-organizational agent accountability.

---

## 2. AMT Foundations

### The Agent as Mass Payload

An AMT agent is nothing but encrypted layers. It has no identity field, no core process, no decision engine at the mass level. Each layer is encrypted under a *key class* using AES-256-GCM with keys derived via HKDF-SHA256:

```
K_c = HKDF-SHA256(master_secret, salt=SHA256(key_class), info="amt-layer")
```

The agent's total mass is the sum of all encrypted layer sizes in bytes. When the last layer is decrypted, the agent ceases to exist. The agent cannot decrypt its own layers, observe which layer was decrypted, or know its own key class distribution.

### The Environment as Decryptor

An environment holds secrets for one or more key classes. When an agent enters an environment, the environment decrypts all layers it has affinity for. This is not a negotiation — it is physics. The environment acts; the agent is acted upon.

For each decrypted layer:
- If the plaintext is non-empty: **signal** = `len(plaintext)` bytes
- The remaining mass consumed is **loss**: encryption overhead (nonce + tag) and empty-layer mass
- `mass_consumed = signal + loss` (per layer)

### The Conservation Law

Summing across all layers decrypted in a single interaction:

```
mass_before = mass_after + total_signal + total_loss
```

This is verified by assertion in the `interact()` function. In the reference implementation, this assertion has never been violated — not in unit tests, not in simulation, and not at population scale (50,000 agents, 2.3 million interactions).

### Key Classes and Information Asymmetry

Key classes create *information asymmetry by design*. An environment that holds the secret for class `alpha` can decrypt alpha layers but cannot even detect the existence of `beta` layers (they are indistinguishable from random bytes). This means:

- An agent carrying layers for classes `{alpha, beta, gamma}` traversing an environment with keys for `{alpha}` will lose only its alpha layers.
- The environment cannot determine that beta and gamma layers exist.
- The agent cannot determine which layers were stripped (it only observes total mass change).

### Mass Gates

Environments have mass thresholds: `(min_mass, max_mass)`. An agent outside this range cannot enter. This is physical topology, not permission — a bowling ball cannot fit through a garden hose regardless of its access control list.

---

## 3. Two-Tier Ledger Architecture

AMT employs a two-tier ledger system that separates detailed records from public commitments:

### Local Ledger (Permissioned)

Each node maintains a local ledger containing full interaction records:
- Agent hash (mass-state hash, NOT identity)
- Mass before and after interaction
- Signal extracted, loss incurred
- Loss differential vector (delta_L) by key class
- Conservation validity flag
- Timestamp

The local ledger is readable only by the node operator and authorized auditors. It never leaves the operator's control.

### Public Ledger (Commitments Only)

Periodically, the local ledger produces a *commitment*: a Merkle root computed over a batch of local entries. The public ledger contains:
- Merkle root of the batch
- Batch size (transaction count)
- Time range
- Node identifier

The public ledger does NOT contain:
- Any agent information
- Any signal content
- Any loss vectors
- Any individual transaction data

### Audit via Merkle Proof

An authorized auditor can verify that a specific local entry exists in a public commitment by recomputing the Merkle path. This provides:

- **Tamper evidence**: If a local entry is modified after publication, the Merkle root won't match.
- **Selective disclosure**: The auditor can verify one entry without seeing the rest of the batch.
- **Non-repudiation**: The operator cannot deny a committed transaction.

### Connection to Cube Protocol S4

This architecture implements Cube Protocol Principle 4 — *Statistical Leakage, Not Raw Data*: "The system exposes distributions, not events." The public ledger exposes batch-level statistics (count, time range) without exposing individual events.

---

## 4. Formalizing Cross-Organizational Boundaries

### Definitions

**Organization**: A party that owns a set of nodes and holds secrets for a set of key classes. Formally:

```
Org = (org_id, name, key_secrets: {class -> secret}, nodes: {node_id -> Node}, ledger: LocalLedger)
```

**Trust Boundary**: A directed edge between nodes owned by different organizations, where the agent's mass at the crossing point is recorded.

```
TrustBoundary = (from_org, to_org, from_node, to_node, crossings: [{agent_hash, mass, layers, timestamp}])
```

**Cross-Org Topology**: A standard topology (graph of nodes) with organizational ownership annotations and trust boundary tracking on cross-org edges.

### The Three Theorems

#### Theorem 1: Conservation Across Boundaries

**Statement**: The conservation law `C_{n+1} + S_{n+1} + L_n = C_n` is invariant under organizational partitioning of the topology.

**Proof**: The conservation law is enforced inside the `interact(agent, environment)` function, which takes an agent and a single environment. It does not receive, inspect, or depend on any organizational identifier. The function:

1. Records `mass_before = agent.mass`
2. Decrypts all layers the environment has affinity for
3. Sums signal and loss across decrypted layers
4. Asserts `mass_before == mass_after + total_signal + total_loss`

Since the function's inputs are (agent, environment) and organizations are a partitioning of environments, the conservation law holds for each interaction regardless of which organization owns the environment. Partitioning environments into organizational groups does not alter any interaction — it is a labeling operation on a structure that the conservation law is already oblivious to. QED.

**Corollary**: Global conservation across a multi-org traversal is the sum of local conservations:

```
Sum over all interactions i:
  mass_before_i = mass_after_i + signal_i + loss_i
```

This holds because each term is independently enforced.

#### Theorem 2: Independent Auditability

**Statement**: Each organization can verify conservation on its own nodes without access to any other organization's ledger entries, key secrets, or interaction data.

**Proof**: An organization's audit procedure is:

1. Query its own local ledger for all entries
2. For each entry, verify `conservation_valid` flag (which was computed at interaction time from `mass_before == mass_after + signal + loss`)
3. Verify its entries against the public ledger via Merkle proof

Step (1) requires only the organization's own ledger — no other organization's data.
Step (2) uses only data recorded in the organization's local entries — the conservation check was performed by `interact()` at the time of the interaction using only the agent's mass state and the local environment's keys.
Step (3) requires the public ledger (which is readable by anyone) and the organization's own entries — no other organization's entries.

At no point does the organization require data from any other organization. QED.

**Demonstration**: In the reference implementation, Aegis Corp, Bifrost Systems, and Verdant Labs each independently produced audit reports showing conservation validity and Merkle verification, with zero data shared between them.

#### Theorem 3: Non-Disclosure

**Statement**: No organization can determine another organization's consumption (signal, loss, or delta_L) from the public ledger alone.

**Proof**: The public ledger contains only:
- Merkle root (a SHA-256 hash of hashes — computationally irreversible)
- Batch size (integer count)
- Time range (two timestamps)
- Node identifier (which reveals org identity, but not transaction content)

From these, an observer can determine:
- How many transactions an organization committed in a time window
- That the organization was active during that window

The observer CANNOT determine:
- Individual agent mass values (hidden inside the Merkle tree)
- Signal extracted (not present in any public field)
- Loss incurred (not present in any public field)
- Delta_L vectors (not present in any public field)
- Agent identity or hash (not present in any public field)
- Whether any specific agent transited the organization

The Merkle root is a one-way function over the concatenated hashes of individual entries. Even if an attacker knew all but one entry in a batch, they could not determine the remaining entry from the root without brute-forcing SHA-256. QED.

---

## 5. The Scenario: Three Orgs, One Agent, Zero Trust

### Organization Setup

| Organization | Role | Secrets | Nodes |
|-------------|------|---------|-------|
| Aegis Corp | Deployer | {epsilon} | Deploy (inert), Recall (reads epsilon) |
| Bifrost Systems | Processor | {alpha, beta} | Intake (reads alpha), Compute (reads beta, accretes gamma), Relay (inert) |
| Verdant Labs | Validator | {gamma, delta} | Verify (reads gamma), Stamp (reads delta, accretes epsilon), Exit (inert) |

### Agent Composition

The deployer (Aegis Corp) creates an agent with layers across all five key classes:
- **alpha** layers: mission payload (read by Bifrost's Intake)
- **beta** layers: compute fuel (read by Bifrost's Compute)
- **delta** layers: validation fuel (read by Verdant's Stamp)

The agent also carries no gamma or epsilon layers at creation — these are accreted during traversal:
- **gamma** layers: accreted by Bifrost's Compute (processing results)
- **epsilon** layers: accreted by Verdant's Stamp (validation stamp)

### Traversal With Exact Mass Accounting

From the reference implementation (Demo 2):

```
Step 0: [Aegis Corp]       Deploy      462B -> 462B  (inert, S=0, L=0)
        >>> TRUST BOUNDARY: Aegis -> Bifrost (mass=462B)
Step 1: [Bifrost Systems]  Intake      462B -> 269B  (S=81, L=112)
Step 2: [Bifrost Systems]  Compute     269B ->  85B  (S=72, L=112) + accretion: 2 gamma layers
Step 3: [Bifrost Systems]  Relay       203B -> 203B  (inert, S=0, L=0)
        >>> TRUST BOUNDARY: Bifrost -> Verdant (mass=203B)
Step 4: [Verdant Labs]     Verify      203B ->  85B  (S=62, L=56)
Step 5: [Verdant Labs]     Stamp        85B ->   0B  (S=29, L=56) -> DEATH
```

Conservation check at every step:

| Step | Node | C_n | C_{n+1} | S | L | C_n = C_{n+1} + S + L |
|------|------|-----|---------|---|---|------------------------|
| 1 | Intake | 462 | 269 | 81 | 112 | 462 = 462 OK |
| 2 | Compute | 269 | 85 | 72 | 112 | 269 = 269 OK |
| 4 | Verify | 203 | 85 | 62 | 56 | 203 = 203 OK |
| 5 | Stamp | 85 | 0 | 29 | 56 | 85 = 85 OK |

Note: After Step 2, the Compute node accreted 2 gamma layers (118B), increasing the agent from 85B to 203B before Step 3. Accretion is a separate operation from the conservation-governed interaction — it is additive mass, not a conservation violation.

### Per-Organization Audit Results

Each organization independently audited its own interactions:

| Organization | Interactions | Signal | Loss | Mass Consumed | Conserved | Merkle OK |
|-------------|-------------|--------|------|---------------|-----------|-----------|
| Aegis Corp | 1 | 0 | 0 | 0 | Yes | Yes |
| Bifrost Systems | 3 | 153 | 224 | 377 | Yes | Yes |
| Verdant Labs | 2 | 91 | 112 | 203 | Yes | Yes |
| **Total** | **6** | **244** | **336** | **580** | **Yes** | -- |

Aegis Corp knows: it sent an agent and nothing happened at its inert Deploy node.
Bifrost Systems knows: it consumed 377B across 3 interactions (153B signal, 224B loss).
Verdant Labs knows: it consumed 203B across 2 interactions (91B signal, 112B loss).

No organization knows what any other organization consumed. Global conservation holds.

---

## 6. Behavioral Divergence Across Trust Boundaries

### The Phenomenon

In AMT, an agent's remaining mass shapes its behavioral decisions through a desperation curve. Two agents with identical behavioral parameters but different mass budgets will make different choices at decision points in the topology.

When this property interacts with cross-organizational boundaries, an emergent economic phenomenon appears: **budget-constrained agents skip expensive organizational domains.**

### Demonstration

From the reference implementation (Demo 4):

| Metric | Agent Heavy (310B) | Agent Light (96B) |
|--------|-------------------|-------------------|
| Initial mass | 310B | 96B |
| Layers | 7 | 2 |
| Steps survived | 6 | 3 |
| Final mass | 0B | 0B |
| Reached Verdant (validation) | Yes | No |
| Death location | Verdant/Stamp | Bifrost/Compute |

Agent Heavy had sufficient mass (including delta layers for validation fuel) to traverse the full pipeline: Aegis -> Bifrost -> Verdant -> Aegis. It received validation from Verdant Labs.

Agent Light had only alpha and beta layers. After Bifrost consumed its alpha and beta layers, it had no mass left to reach Verdant. It died at Bifrost's Compute node — never validated.

### Emergent Economics

This is not a programmed policy. No one wrote a rule that says "agents under 200B skip validation." It emerged from the physics:

1. Validation requires delta layers (consumed by Verdant's Stamp node)
2. Delta layers have mass (encryption overhead + payload)
3. Agents with insufficient mass budget cannot carry delta layers
4. Therefore, budget-constrained agents cannot be validated
5. Therefore, organizational trust relationships are modulated by agent mass

**The implication**: In a real deployment, the quality of service (validated vs. unvalidated) is determined by the deployer's investment in agent mass. This creates a natural economic incentive structure without any pricing protocol.

### At Scale

From the scale demonstration (200 agents):
- 28.5% of agents reached Verdant Labs (were validated)
- 71.5% of agents either died before reaching Verdant or took the shortcut

---

## 7. Cube Protocol Mapping

AMT implements all five principles of the Cube Protocol:

### Principle 1: Presence, Not Identification

Agents are identified by mass-state hashes, not persistent identities. Two agents with identical mass states produce identical hashes. The `agent_hash` in ledger entries is `SHA256(mass:layer_count)` — a transient observation, not an enrollment.

**AMT implementation**: The agent has no identity field. The factory creates it. The environment processes it. The ledger records a hash of its mass state. At no point does any party assign, store, or verify an identity.

### Principle 2: Capability Leakage, Not Authority

Nodes advertise what they CAN decrypt (key affinity set), not who MAY enter. The mass gate is a physical constraint (too large to fit), not an access control decision. An agent carrying alpha layers is vulnerable to alpha-keyed environments — this is capability exposure, not authority grant.

**AMT implementation**: `Environment.key_classes` is the set of classes the environment can decrypt. There is no ACL, no permission check, no identity-based gate. If you fit through the mass window and you carry vulnerable layers, you interact. Period.

### Principle 3: Outcome Leakage, Not Intent

The ledger records outcomes (signal extracted, loss incurred, conservation valid) but not intent (why the agent was deployed, what the deployer hoped to achieve, what the processor intended to extract).

**AMT implementation**: `InteractionResult` contains `total_signal`, `total_loss`, `delta_L`, `agent_survived`. It does not contain mission objectives, processing goals, or validation criteria.

### Principle 4: Statistical Leakage, Not Raw Data

The public ledger exposes Merkle roots of transaction batches — distributions (batch sizes, time ranges) without individual events.

**AMT implementation**: `PublicCommitment` contains `merkle_root`, `batch_size`, `timestamp`, `time_range`. An observer learns "this node processed N transactions in window [a, b]" and nothing more. This was verified in Demo 5: even knowing the number of commitments per org, an observer cannot determine which agents traversed which nodes, what signal was extracted, or what routes agents took.

### Principle 5: Exit Leakage (The Most Important)

Agent death is local. When an agent's mass reaches zero, it simply ceases to exist. There is no death notification, no teardown event, no final state mutation visible to non-local observers. Non-participation (agent is dead) is indistinguishable from absence (agent was never here).

**AMT implementation**: When `agent.alive` becomes `False`, the agent has no layers. The last environment that decrypted layers recorded the interaction in its local ledger, but no other node in the topology is notified. If the agent was expected at a downstream node and never arrives, the downstream node cannot distinguish "agent died" from "agent was never sent" from "agent took a different path."

---

## 8. Related Work

### Homomorphic Encryption

Fully homomorphic encryption (FHE) allows computation on encrypted data without decryption. In principle, an agent could carry FHE-encrypted payloads that processors compute on without seeing plaintext. However:

- FHE requires a shared encryption scheme and key management protocol
- Computational overhead is orders of magnitude higher than AMT's symmetric encryption
- FHE does not provide a conservation law — there is no built-in accountability for resource consumption
- FHE is a protocol (can be violated); AMT conservation is a mathematical invariant

### Secure Multi-Party Computation (MPC)

MPC allows multiple parties to jointly compute a function over their inputs without revealing those inputs. This is conceptually aligned with AMT's non-disclosure property, but:

- MPC requires protocol coordination between all parties
- MPC assumes honest-but-curious or malicious-but-minority adversary models
- AMT requires no coordination — conservation is enforced locally at each interaction
- AMT works with zero parties cooperating: the math enforces itself

### Blockchain-Based Audit

Distributed ledgers provide tamper-evident transaction records across trust boundaries. However:

- Blockchain requires consensus (proof-of-work, proof-of-stake, PBFT)
- Consensus mechanisms are protocols with known attack vectors
- Blockchain stores transaction data on-chain (privacy concern) or requires additional privacy layers
- AMT's public ledger contains only Merkle roots — no transaction data

### Zero-Knowledge Proofs (ZKPs)

ZKPs allow proving statements without revealing the underlying data. ZK-SNARKs and ZK-STARKs could in principle prove conservation without revealing mass values. However:

- ZKPs require trusted setup (SNARKs) or larger proof sizes (STARKs)
- ZKPs prove specific statements about specific computations — they are generated, not inherent
- AMT conservation is not a statement that needs proving — it is an invariant that holds by construction

### Key Differentiator

All of the above are *protocols*: sets of rules that parties must follow. They can be implemented correctly or incorrectly. They can be violated by bugs, malice, or operational error.

AMT conservation is not a protocol. It is a mathematical property of the `interact()` function. It holds because `mass_before - mass_after = signal + loss` is an algebraic identity enforced by the structure of AES-GCM decryption. No party can violate it because no party controls it.

---

## 9. Limitations and Future Work

### Honest Environment Assumption

The current model assumes environments correctly implement the `interact()` function. A malicious environment could:

- Decrypt layers but report false signal/loss values
- Clone the agent (copy layers before decrypting)
- Inject layers without going through the accretion mechanism

Mitigation: The Merkle commitment to the public ledger makes post-hoc falsification detectable, but does not prevent real-time lying. Future work could explore hardware attestation (TPM/SGX) for environment integrity.

### Accretion Across Organizational Boundaries

When Bifrost's Compute node accretes gamma layers onto the agent, Verdant Labs must hold the gamma secret to decrypt them. This requires that gamma's secret was shared between the factory (who encrypted the accretion template) and Verdant (who decrypts it).

In the current model, the factory holds all secrets at creation time. In a more adversarial model, accretion secrets could be negotiated via key exchange protocols. This is an area for future work.

### Key Class Namespace Governance

If Bifrost Systems and Verdant Labs independently define a key class named "result", their secrets will differ, and layers encrypted by one cannot be decrypted by the other. This is safe but potentially confusing.

A namespace governance mechanism — perhaps a registry of key class names and their semantic meanings — would improve interoperability. However, any such registry introduces a trust anchor, which partially undermines the trust-free nature of the system.

### Real-Time vs. Batch Audit

The current Merkle commitment is batch-oriented: entries accumulate, then a root is published. Real-time audit would require streaming commitments, which increases public ledger volume. The trade-off between audit latency and ledger bloat is unexplored.

### Scalability

The reference implementation processes approximately 5,000 agents per second on a single core. For enterprise-scale deployments (millions of agents), the cryptographic operations (AES-256-GCM per layer, SHA-256 for Merkle trees) may become a bottleneck. Hardware acceleration (AES-NI, SHA extensions) and parallel processing would be required.

---

## 10. Conclusion

We have demonstrated that the AMT conservation law provides cross-organizational agent accountability without trust. The key properties:

1. **Conservation is local**: The law holds at every interaction, enforced by the mathematics of symmetric decryption. It does not know about organizations.

2. **Partitioning is labeling**: Assigning nodes to organizations is a labeling operation on a structure that conservation is already invariant over. No new mechanisms are needed.

3. **Audit is independent**: Each organization can verify its own consumption without access to any other organization's data, secrets, or ledger entries.

4. **The public ledger is opaque**: External observers see Merkle roots and batch counts. They learn nothing about individual agents, signals, losses, or routes.

5. **Behavior is emergent**: Budget-constrained agents skip expensive organizational domains. This creates natural economic incentive structures without pricing protocols.

6. **The math is the accountability**: No trust, no protocol, no consensus mechanism, no identity provider. The conservation law holds because it is an algebraic identity, not because anyone agreed to follow it.

In an era where multi-party agent deployments are becoming standard — agents traversing cloud providers, compliance validators, data processors, and result aggregators — the question of accountability is usually answered with more protocols. We propose answering it with less: a single conservation law, enforced by construction, invariant across all boundaries.

The math does not care about your organizational chart. That is precisely why it can be trusted.

---

## Appendix A: Reference Implementation

The complete reference implementation is available at:

- `amt_core.py` — Conservation law, Agent, Environment, interact(), AgentFactory
- `amt_extensions.py` — LocalLedger, PublicLedger, Node, AgentBehavior, Topology
- `amt_cross_org.py` — Organization, TrustBoundary, CrossOrgTopology, audit functions
- `amt_cross_org_demo.py` — 6-demo scenario (topology, happy path, audit, divergence, opacity, scale)

### Running the Demo

```bash
python3 amt_cross_org_demo.py
```

### Scale Results (from reference run)

| Metric | Value |
|--------|-------|
| Agents | 200 |
| Total interactions | 457 |
| Conservation violations | 0 |
| Agents validated (reached Verdant) | 57 (28.5%) |
| Agents that skipped validation | 143 (71.5%) |
| Survival rate | 40.5% |
| Throughput | ~5,300 agents/sec |

### Verification Command

```bash
# Verify no regressions in existing simulations
python3 amt_ext_simulation.py
python3 amt_scale.py --agents 1000 --steps 30
```

---

## Appendix B: Formal Notation

### Conservation Law

For interaction `i` at environment `e`:

```
C_i(before) = C_i(after) + S_i + L_i
```

Where:
- `C_i(before) = sum(len(layer.encrypted) for layer in agent.layers)` before interaction
- `C_i(after) = sum(len(layer.encrypted) for layer in surviving_layers)` after interaction
- `S_i = sum(len(plaintext) for layer in decrypted_layers if plaintext != b"")`
- `L_i = C_i(before) - C_i(after) - S_i`

### Cross-Org Conservation

For a traversal across organizations `{O_1, ..., O_k}`, where each organization owns interactions `I(O_j)`:

```
For all j in {1, ..., k}:
  For all i in I(O_j):
    C_i(before) = C_i(after) + S_i + L_i    [Theorem 1]

O_j can verify all i in I(O_j) independently  [Theorem 2]

For j != m:
  O_j cannot determine {S_i, L_i : i in I(O_m)} from public ledger  [Theorem 3]
```
