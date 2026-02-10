# Agentropy: A Conservation Law That Induces Emergent Behavior Resembling Intelligence

**One Constraint. Four Domains. Zero Violations.**

*Nate Walker — Ravenhelm*
*February 2026*

---

## Abstract

We present a single conservation law for autonomous agents — `C_{n+1} + S_{n+1} + L_n = C_n` — and demonstrate that applying it unmodified across four unrelated domains produces emergent behaviors that no participant programmed, no policy engine configured, and no protocol specified. In cross-organizational accountability, the law produces independent auditability across trust boundaries without any party trusting any other. In token economics, it produces market stratification, budget-dependent behavioral divergence, and inflation-proof currency without any pricing protocol. In physical IoT resource management, it produces dynamic load-shedding and power conservation without any management daemon. In population ecology, it produces carrying capacity, boom/bust cycles, niche differentiation, and competitive exclusion without any ecological rules. Across all four domains — 750 agents, 5,415 interactions — zero conservation violations occur. The law is never modified, extended, or parameterized for any domain. It is the same five characters in every experiment. We argue that this is a demonstration of the minimal sufficient condition for intelligence-resembling behavior: not computation, not learning, not optimization — but constraint.

---

## 1. Introduction

### 1.1 The Question

What is the minimum you need to add to a system for intelligent-looking behavior to emerge?

The standard answers involve computation (neural networks, decision trees), learning (gradient descent, reinforcement), or optimization (utility maximization, evolutionary search). Each adds substantial machinery. Each requires domain-specific tuning. Each produces intelligence that is specific to the domain it was trained on.

We propose a different answer: **a conservation law**.

A conservation law adds one thing to a system: a constraint. Mass cannot be created or destroyed. Energy in equals energy out. Signal plus loss equals the mass consumed. This constraint is domain-agnostic — it doesn't know what the mass represents, what the signal means, or what the loss costs. It simply enforces an invariant.

The claim of this paper is that this constraint alone — applied without modification across domains — is sufficient to produce emergent behaviors that resemble intelligence: resource allocation, market dynamics, ecological balance, and trustless accountability. Not because the law is intelligent, but because the constraint forces the system into states that an observer would call intelligent.

### 1.2 The Conservation Law

Agent Mass Theory (AMT) defines a conservation law for digital agents:

```
C_{n+1} + S_{n+1} + L_n = C_n
```

Where:
- `C_n` is the agent's cipher mass at state *n* (total encrypted bytes across all layers)
- `C_{n+1}` is the cipher mass after interaction
- `S_{n+1}` is the signal extracted (information yield from non-empty layers)
- `L_n` is the loss incurred (mass consumed without information yield — encryption overhead, empty layers)

The law states: **an agent's mass after interaction, plus the signal extracted, plus the loss incurred, equals the mass before interaction.** Nothing is created. Nothing disappears. Every byte is accounted for.

This law is enforced by construction — it is an algebraic consequence of how AES-256-GCM decryption works. The encrypted layer has a known size. Decryption produces plaintext (signal) and reveals overhead (loss). The sum is exact. No party can violate it because no party controls it. It is not a protocol. It is arithmetic.

### 1.3 The Experiments

We applied this law, unmodified, to four domains:

| Domain | What mass represents | What emerges |
|--------|---------------------|-------------|
| Cross-org accountability | Encrypted agent payload | Trustless auditability |
| Token economy | Tool-call currency | Market stratification |
| Physical IoT | Battery, bandwidth, CPU | Resource conservation |
| Population ecology | Survival energy | Carrying capacity, speciation |

In each domain, we changed what the layers *mean*. We never changed how they *work*. The conservation law is identical in all four experiments. The `interact()` function is shared. The assertion `mass_before == mass_after + signal + loss` is the same line of code.

---

## 2. The Machinery

### 2.1 Agents

An agent is a collection of encrypted layers. Each layer is an AES-256-GCM ciphertext encrypted under a *key class*. The agent cannot decrypt its own layers, observe which layer was stripped, or know its own key class distribution. It can observe one thing: its total mass (a scalar). When mass reaches zero, the agent is dead.

The agent has no decision engine, no goal, no model of its environment. It is a payload. It is acted upon.

### 2.2 Environments

An environment holds secrets for one or more key classes. When an agent enters, the environment decrypts all layers matching its key classes. This interaction is not a negotiation — it is physics. The environment acts; the agent is stripped.

The number of key classes an environment holds determines its *hazard*. A single-key environment strips one layer type. A multi-key environment strips multiple types simultaneously. An environment with no keys is inert — safe passage.

### 2.3 The Interaction

The `interact(agent, environment)` function:
1. Checks the mass gate (can the agent physically fit?)
2. Decrypts all layers the environment has affinity for
3. Measures signal and loss per layer
4. Removes decrypted layers from the agent
5. **Asserts the conservation law**

Step 5 is not a check — it is a hard assertion. If conservation is violated, the system crashes. In the reference implementation, across all experiments, all populations, and all scale tests, this assertion has never fired.

### 2.4 What the Law Constrains

The conservation law constrains the system in three ways:

**Monotonic depletion**: In the absence of accretion (external mass addition), agent mass can only decrease. Every interaction costs something. Signal costs mass. Even loss costs mass. Existence is expensive.

**Class-selective consumption**: Environments can only consume mass of key classes they hold secrets for. Alpha environments cannot touch beta layers. This creates natural resource partitioning — an agent's mass profile determines which environments can affect it.

**Budget-behavior coupling**: An agent's remaining mass, decomposed by key class, determines what it can afford to do next. This creates behavioral divergence — agents with different mass profiles make different choices even in identical topologies.

---

## 3. Domain 1: Cross-Organizational Accountability

### 3.1 The Problem

When an agent traverses infrastructure owned by multiple independent organizations, how does each verify consumption on its own nodes without trusting any other party?

### 3.2 The Setup

Three organizations — Aegis Corp (deployer), Bifrost Systems (processor), Verdant Labs (validator) — each own a set of nodes with distinct key class secrets. The agent carries layers across five key classes. Trust boundaries are recorded where the agent crosses organizational domains.

### 3.3 What Emerges

**Independent auditability**: Each organization audits its own local ledger. Conservation holds per-interaction, so each org can verify its own consumption without any other org's data. No shared audit framework. No mutually trusted third party.

**Non-disclosure**: The public ledger contains Merkle roots of batches — not individual transactions. An observer sees that Bifrost committed 3 transactions in a time window. They cannot determine what signal was extracted, what mass was consumed, or which agent transited.

**Budget-constrained routing**: Agents with insufficient delta layers (validation fuel) cannot reach Verdant Labs for validation. This isn't a policy — it's physics. The agent dies before reaching the validator because it ran out of mass. At scale, 71.5% of agents skip validation entirely. No one decided this. The conservation law decided it.

### 3.4 Results

| Metric | Value |
|--------|-------|
| Agents | 200 |
| Interactions | 457 |
| Conservation violations | 0 |
| Agents validated | 28.5% |

---

## 4. Domain 2: Token Economy

### 4.1 The Problem

How do you charge agents for tool usage without a billing service, a credit system, or a rate limiter?

### 4.2 The Setup

Five tool classes (API calls, LLM inference, storage, compute, admin) mapped to five key classes at five price points (1-4 layers per call). A tool gateway is an AMT environment that holds exactly one key secret. Payment is decryption. Conservation is enforcement.

### 4.3 What Emerges

**Natural currency**: Layers are atomic (consumed or not — no partial payment), class-specific (each denomination funds different tools), and conservation-governed (cannot be inflated, counterfeited, or double-spent).

**Market stratification**: Agents with 12 beta layers can make exactly 4 LLM calls. Agents with 1 beta layer can make zero. No access control list creates this stratification. The agent's mass profile IS its economic identity.

**Budget-behavior coupling**: Rich agents (>1,000 B) average 3.8 successful tool calls. Poor agents (<=500 B) average 1.8. The ratio (2.1x) emerged from conservation, not policy. Same topology. Same parameters. Different budgets. Different lives.

**Dynamic hazard pricing**: Environments under load don't raise prices per key — they arm themselves with additional keys, stripping more layer types per visit. Fixed unit prices with dynamic aggregate cost, governed by key rotation rather than rate negotiation.

### 4.4 Results

| Metric | Value |
|--------|-------|
| Agents | 200 |
| Tool calls | 2,113 |
| Conservation violations | 0 |
| Rich/poor call ratio | 2.1x |

---

## 5. Domain 3: Physical IoT Resource Management

### 5.1 The Problem

A smart RV has battery, bandwidth, storage, CPU, and sensors. Five resources, five independent management systems, no unified budget. How do you enforce "you have 50 Wh, 100 MB, and 30 CPU-seconds — spend them wisely" without five separate policy engines?

### 5.2 The Setup

Each physical resource maps to a key class via a fixed conversion factor (1 Wh = 1000 B of alpha mass). An agent's mass profile IS its physical resource budget. Five locations (campsite, highway, mountain, remote, destination) hold keys for the resources they consume.

### 5.3 What Emerges

**Unified resource accounting**: One conservation law replaces five independent management systems. Battery depletion, bandwidth metering, CPU budgeting, and sensor access control are all the same operation: layer stripping of different key classes.

**Safe passage from key absence**: At an off-grid location (no beta key), bandwidth layers pass through unstripped. This isn't a "bandwidth preservation feature" — it's a consequence of key affinity. The conservation law doesn't know about bandwidth. It simply has no key to decrypt those layers.

**Dynamic load-shedding**: As battery (alpha mass) depletes, mass gates tighten. Heavier agents get blocked. Lighter agents pass. Load-shedding emerges from conservation, not from a load-balancing algorithm. No power management daemon. No priority queue. Just physics.

**Environmental coasting**: An agent that exhausts its alpha and beta layers at the highway "coasts" through mountain (which holds the same keys) — zero layers stripped. The conservation law produces energy-free traversal through environments whose hazard surface the agent has already survived.

### 5.4 Results

| Metric | Value |
|--------|-------|
| Agents | 150 |
| Interactions | 750 |
| Layers stripped | 32,486 |
| Conservation violations | 0 |

---

## 6. Domain 4: Population Ecology

### 6.1 The Problem

When hundreds of agents compete for finite resources, what population dynamics emerge?

### 6.2 The Setup

200 agents competing across 5 marketplace nodes with finite resource pools that regenerate over time. Dead agents' mass is recycled through a nutrient cycling mechanism that converts consumed mass into new layers for survivors via the factory.

### 6.3 What Emerges

**Carrying capacity**: The population stabilizes at 4-6 agents (2-3% of initial population). Not programmed. Emerges from regeneration rate / consumption rate balance.

**Boom/bust dynamics**: Population crashes when consumption exceeds regeneration. Exponential decay: 100 agents → 76 (step 5) → 44 (step 10) → 18 (step 15) → 0 (step 38). Classic overshoot-and-collapse, produced by conservation law + finite resources.

**Niche differentiation**: Alpha-heavy agents cluster at Feeding A (4.0% survival). Beta-heavy agents cluster at Feeding B (8.0% survival). Different mass profiles → different habitats → different survival outcomes. Gause's competitive exclusion principle, emergent from mass physics.

**Nutrient cycling**: 77.3% of dead agent mass is recycled to survivors. The food chain: Agent A dies → signal + loss deposited → nutrient cycler accumulates → factory creates new layers → Agent B accretes. Dead agents fuel living ones. Conservation governs every step.

**Resource partitioning**: The Shelter (no keys, safe passage) accounts for 31.6% of all interactions. Agents disproportionately route through safe zones — behavioral resource partitioning without ecological modeling.

### 6.4 Results

| Metric | Value |
|--------|-------|
| Agents | 200 |
| Interactions | 2,095 |
| Nutrient recycling rate | 77.3% |
| Conservation violations | 0 |

---

## 7. The Invariance Argument

### 7.1 Same Law, Four Costumes

The conservation law did not change between experiments. The line of code is the same:

```python
assert mass_before == mass_after + total_signal + total_loss
```

What changed is the *interpretation* of mass:

| Domain | Mass represents | Signal represents | Loss represents |
|--------|----------------|-------------------|-----------------|
| Cross-org | Agent payload | Information extracted | Encryption overhead |
| Token economy | Tool-call budget | Tool output | Payment overhead |
| Physical IoT | Resource budget (Wh, MB, ops) | Useful work | Resource waste |
| Ecology | Survival energy | Nutrient value | Entropy |

The law doesn't know which interpretation is active. It enforces `C + S + L = C_0` regardless. This is why it works across domains — it is operating below the semantic layer.

### 7.2 What the Constraint Forces

In each domain, the conservation law forces the system into a narrow corridor of possible states. Not all states are reachable. Not all behaviors are possible. The constraint eliminates:

- **Trust without trust (cross-org)**: Conservation eliminates the need for trusted intermediaries because the math self-enforces. The constraint forces auditability.
- **Markets without markets (token economy)**: Conservation eliminates inflation, double-spending, and unauthorized access because mass is physical. The constraint forces scarcity.
- **Management without managers (IoT)**: Conservation eliminates the need for resource governors because depletion is automatic. The constraint forces budgeting.
- **Ecology without ecology (marketplace)**: Conservation eliminates the need for population rules because mass depletion creates carrying capacity. The constraint forces balance.

### 7.3 Emergence, Not Intelligence

We do not claim that agents under the conservation law are intelligent. They are payloads. They have no goals, no models, no learning. What we claim is that the *system* exhibits behaviors that an observer would attribute to intelligent design:

- Budget-constrained agents "decide" to skip expensive operations
- Populations "find" equilibrium carrying capacity
- Resource budgets "adapt" to environmental conditions
- Trust relationships "emerge" from mass physics

These are not decisions. They are consequences of a constraint narrowing the state space until only "intelligent-looking" trajectories remain. Intelligence is what's left when you've eliminated all the stupid options. A conservation law eliminates them by arithmetic.

### 7.4 The Minimal Sufficient Condition

We hypothesize that a conservation law is the *minimal sufficient condition* for intelligence-resembling emergence. It is sufficient because it produces the behaviors listed above without any additional machinery. It is minimal because removing it — allowing mass creation, double-spending, or infinite energy — eliminates all emergent properties. Without the constraint, agents can do anything, which means nothing is interesting. Scarcity forces allocation. Allocation forces strategy. Strategy resembles intelligence.

This echoes a principle from thermodynamics: the Second Law doesn't make heat engines intelligent. It makes certain configurations of heat engines *inevitable*. The conservation law doesn't make agents intelligent. It makes certain configurations of agent behavior inevitable.

---

## 8. Aggregate Results

### 8.1 Cross-Domain Summary

| Domain | Agents | Interactions | Violations | Key Emergent Property |
|--------|--------|-------------|------------|----------------------|
| Cross-org | 200 | 457 | 0 | Trustless auditability |
| Token economy | 200 | 2,113 | 0 | Market stratification |
| Physical IoT | 150 | 750 | 0 | Unified resource management |
| Ecology | 200 | 2,095 | 0 | Carrying capacity + speciation |
| **Total** | **750** | **5,415** | **0** | |

Additionally, the core scale test (not domain-specific) verified conservation across 50,000 agents and 2.3 million interactions with zero violations.

### 8.2 The Number That Matters

**Zero.**

Zero conservation violations across 750 agents, 5,415 interactions, four domains, and zero parameter tuning between domains. The law was not adjusted, relaxed, approximated, or special-cased for any experiment. It held because it is an algebraic identity, not a heuristic.

### 8.3 What Zero Means

In protocol-based systems, the violation rate is the error rate — bugs in the billing service, race conditions in the rate limiter, edge cases in the access control logic. These systems aspire to low violation rates. AMT's violation rate is not low. It is structurally zero. A violation would require AES-256-GCM decryption to produce bytes from nowhere — a cryptographic impossibility.

This is the difference between a protocol and a law. A protocol says "don't create mass." A law says "mass cannot be created." The first can be violated. The second cannot.

---

## 9. Related Work

### 9.1 Conservation Laws in Other Computational Frameworks

**Petri nets** use token conservation to model concurrent systems. Tokens are produced and consumed by transitions, and place invariants enforce conservation across the net. AMT shares the token-conservation property but adds cryptographic enforcement — AMT tokens (layers) cannot be duplicated because they are AES-256-GCM ciphertexts, whereas Petri net tokens are abstract and can be trivially copied in implementation.

**Membrane computing (P systems)** models computation through objects passing between membrane-bounded regions. Objects are consumed and produced by rules, with conservation enforced by rule semantics. AMT's key class affinity is analogous to membrane selectivity — only certain objects (layers of matching class) can pass through certain membranes (be decrypted by environments holding matching keys).

**Chemical Abstract Machine (CHAM)** models concurrent computation as chemical reactions, with molecules (terms) reacting according to rules. Conservation of molecules is a design principle. AMT's conservation is stronger: it is enforced by cryptography rather than by programming convention.

### 9.2 Emergent Intelligence in Constrained Systems

**Cellular automata** (Conway's Game of Life, Wolfram's Rule 110) demonstrate that simple local rules produce complex global behavior. AMT's conservation law is a single local rule (per-interaction conservation) that produces complex global behavior (market dynamics, population ecology). The difference: cellular automata rules are chosen from a large rule space; AMT's rule is derived from the mathematics of symmetric encryption.

**Swarm intelligence** (ant colony optimization, particle swarm) produces intelligent-looking collective behavior from simple individual rules. AMT agents are simpler than swarm particles — they have no individual rules at all. They are acted upon. The intelligence emerges from the constraint, not from agent computation.

**Artificial Life** (Tierra, Avida) simulates evolution in digital environments using conservation of computational resources (CPU cycles, memory). AMT provides formal conservation guarantees (cryptographic enforcement) that these systems lack.

### 9.3 Multi-Agent Economics

**Mechanism design** studies how to design rules (mechanisms) that produce desired economic outcomes when agents act strategically. AMT inverts this: there are no designed mechanisms. The conservation law IS the mechanism, and economic outcomes (stratification, pricing, budget-behavior coupling) emerge from it without design.

**Agent-based computational economics** (ACE) simulates economies with heterogeneous agents following behavioral rules. AMT agents have no behavioral rules at the mass level — their "behavior" is a consequence of mass depletion constraining their possible trajectories.

---

## 10. Limitations

### 10.1 The Honest Environment Assumption

The conservation law is enforced inside the `interact()` function. A malicious environment that reimplements this function can report false signal/loss values. The law governs correct implementations; it does not detect incorrect ones. Mitigation via hardware attestation (TPM/SGX) or zero-knowledge proofs of correct execution is future work.

### 10.2 Static Interpretation

The mapping of mass to domain semantics (alpha = battery, beta = bandwidth) is fixed at design time. Dynamic reinterpretation — where the "meaning" of a key class changes at runtime — is not currently supported and would complicate the conservation argument.

### 10.3 No Learning

Agents do not learn from interactions. They do not update their behavior based on experience. A population of agents does not evolve. The emergent behaviors documented here are *single-generation* phenomena — they arise from the constraint operating on a fixed population, not from adaptation over time. Adding learning or evolution on top of the conservation law is a natural extension but is outside the scope of this work.

### 10.4 Cryptographic Cost

Each layer requires AES-256-GCM encryption (creation) and decryption (interaction). At population scale, this creates measurable computational overhead. The reference implementation processes approximately 3,000-5,000 agents per second on a single core. Enterprise-scale deployments would require hardware acceleration (AES-NI) and parallel processing.

### 10.5 Conservation vs. Emergence Causality

We demonstrate correlation: the conservation law is present, and emergent behaviors appear. We do not prove that the conservation law is the *cause* of emergence in a formal sense. It is possible that other constraints (e.g., finite population, fixed topology) contribute to the emergent properties. Isolating the conservation law's contribution from environmental factors is an open research question.

---

## 11. Future Work

### 11.1 Reproduction and Evolution

The current model has no reproduction. Agents are created by the factory and depleted by interactions. Adding reproduction — where well-funded agents spawn offspring with subset layers — would enable evolutionary dynamics: selection pressure from the conservation law, heritable traits via layer composition, and speciation through ecological niche differentiation.

### 11.2 Agent-to-Agent Interactions

Currently, agents interact only with environments. Agent-to-agent interactions (one agent "consuming" another's layers) would create explicit predator-prey dynamics and enable modeling of competition, cooperation, and parasitism — all governed by the same conservation law.

### 11.3 Real-World Deployment

The Physical IoT experiment maps directly to Ravenhelm's Viking smart RV platform. The Token Economy experiment maps to Ravenhelm's Bifrost tool gateway. Deploying AMT conservation on live infrastructure would test whether the emergent properties observed in simulation hold under real-world conditions: variable latency, network partitions, concurrent access, and hardware failures.

### 11.4 Formal Proof

The conservation law's validity rests on a runtime assertion. A formal proof — using a proof assistant like Coq or Lean — that AES-256-GCM decryption necessarily satisfies `|ciphertext| = |plaintext| + |overhead|` would elevate the result from empirical observation to mathematical theorem.

### 11.5 Multi-Law Systems

What happens when two independent conservation laws operate simultaneously? For example: mass conservation (AMT) plus energy conservation (a second invariant governing computational cost per interaction). The interaction between constraints may produce richer emergent phenomena than either constraint alone.

---

## 12. Conclusion

We added one constraint to a system of autonomous agents: a conservation law that ensures mass before interaction equals mass after plus signal plus loss. We did not add intelligence. We did not add learning. We did not add optimization. We did not add domain knowledge.

We applied this constraint, unmodified, to four unrelated domains:

1. **Cross-organizational accountability**: The constraint forced trustless auditability. Each organization could verify its own consumption without trusting any other party, because the math self-enforced at every interaction.

2. **Token economics**: The constraint forced market dynamics. Budget stratification, behavioral divergence, and inflation-proof currency emerged from layer composition alone — no pricing protocol, no credit system, no rate limiter.

3. **Physical IoT**: The constraint forced resource conservation. Battery management, bandwidth metering, and CPU budgeting became the same operation — layer stripping of different key classes — with load-shedding emerging from mass gate depletion.

4. **Population ecology**: The constraint forced ecological balance. Carrying capacity, boom/bust cycles, niche differentiation, and nutrient cycling emerged from 200 agents competing for finite resources — no birth rules, no death rules, no population caps.

750 agents. 5,415 interactions. Four domains. Zero parameter tuning. Zero conservation violations.

The conservation law does not know what domain it is operating in. It does not know that alpha means battery in one experiment and mission payload in another. It does not know about organizations, tool prices, RV campgrounds, or ecological niches. It knows one thing: `C_{n+1} + S_{n+1} + L_n = C_n`. And from that one thing, all of the above emerged.

Intelligence is not what you add to a system. It is what remains when a constraint has eliminated everything that doesn't work.

**`λ > 0`. The signal continues.**

---

## Appendix A: Reference Implementation

The complete reference implementation is available at [github.com/nwalker85/agentropy](https://github.com/nwalker85/agentropy):

### Core

| File | Purpose |
|------|---------|
| `amt_core.py` | Conservation law, Agent, Environment, interact(), AgentFactory |
| `amt_extensions.py` | LocalLedger, PublicLedger, Node, AgentBehavior, Topology |
| `amt_simulation.py` | Base simulation framework |
| `amt_ext_simulation.py` | Extended simulation with behavioral divergence |
| `amt_scale.py` | Population-scale verification (50,000 agents) |

### Domain Extensions

| File | Domain |
|------|--------|
| `amt_cross_org.py` + `amt_cross_org_demo.py` | Cross-organizational accountability |
| `amt_token_economy.py` + `amt_token_economy_demo.py` | Token economy |
| `amt_physical_iot.py` + `amt_physical_iot_demo.py` | Physical IoT resource management |
| `amt_marketplace.py` + `amt_marketplace_demo.py` | Population ecology |

### Domain Papers

| Paper | Citation |
|-------|----------|
| `paper/cross_org_accountability.md` | Walker 2026a |
| `paper/token_economy.md` | Walker 2026b |
| `paper/physical_iot.md` | Walker 2026c |
| `paper/marketplace.md` | Walker 2026d |

### Running the Experiments

```bash
# Individual domain demos
python3 amt_cross_org_demo.py
python3 amt_token_economy_demo.py
python3 amt_physical_iot_demo.py
python3 amt_marketplace_demo.py

# Scale verification
python3 amt_scale.py --agents 50000 --steps 50
```

---

## Appendix B: The Conservation Law — Formal Statement

### Definition

For an agent with cipher mass `C` consisting of layers `{l_1, ..., l_n}` encrypted under key classes `{k_1, ..., k_m}`, and an environment `E` holding secrets for key classes `K_E ⊆ {k_1, ..., k_m}`:

**Interaction**: The environment decrypts all layers `l_i` where `class(l_i) ∈ K_E`.

For each decrypted layer:
```
signal(l_i) = len(decrypt(l_i))  if decrypt(l_i) ≠ ∅
            = 0                   if decrypt(l_i) = ∅

loss(l_i)   = mass(l_i) - signal(l_i)
```

**Conservation Law**:
```
C_after + Σ signal(l_i) + Σ loss(l_i) = C_before

where the sums range over all decrypted layers
```

**Equivalently**:
```
C_after + S + L = C_before

where S = Σ signal(l_i), L = Σ loss(l_i)
```

### Why It Holds

`mass(l_i) = len(encrypted_i) = 12 + len(plaintext_i) + 16` (AES-256-GCM: 12-byte nonce + ciphertext + 16-byte tag)

`signal(l_i) + loss(l_i) = signal(l_i) + (mass(l_i) - signal(l_i)) = mass(l_i)`

Therefore: `Σ (signal(l_i) + loss(l_i)) = Σ mass(l_i) = C_before - C_after`

Therefore: `C_after + S + L = C_before`. QED.

The conservation law is a tautology of symmetric encryption. It holds because subtraction works.
