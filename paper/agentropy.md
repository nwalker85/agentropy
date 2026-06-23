# Agentropy: A Conservation Law as a Necessary Condition for Life-Like Dynamics

**One Constraint. Four Domains. Zero Violations.**

*Nate Walker — Ravenhelm*
*February 2026*

---

## Abstract

We present a single conservation law for autonomous agents — `C_{n+1} + S_{n+1} + L_n = C_n` — and demonstrate that applying it unmodified across four unrelated domains produces life-like dynamics that no participant programmed, no policy engine configured, and no protocol specified. In cross-organizational accountability, the law produces independent auditability across trust boundaries without any party trusting any other. In token economics, it produces market stratification, budget-dependent behavioral divergence, and inflation-proof currency without any pricing protocol. In physical IoT resource management, it produces dynamic load-shedding and power conservation without any management daemon. In population ecology, it produces carrying capacity, boom/bust cycles, niche differentiation, and competitive exclusion without any ecological rules. Across all four domains — 750 agents, 5,415 interactions — zero conservation violations occur. The law is never modified, extended, or parameterized for any domain. It is the same five characters in every experiment. A systematic ablation study establishes necessity: removing either depletion or class-selective structure eliminates the emergent properties. We identify structured, irreversible depletion as a necessary condition for life-like dynamics in interacting systems. We do not claim this condition is sufficient for life.

---

## 1. Introduction

### 1.1 The Question

What does it take for a system of interacting agents to produce life-like dynamics — scarcity, niches, stratification, boom/bust cycles — without anyone programming those behaviors?

The standard answers involve computation (neural networks, decision trees), learning (gradient descent, reinforcement), or optimization (utility maximization, evolutionary search). Each adds substantial machinery. Each requires domain-specific tuning. Each produces behaviors specific to the domain it was trained on.

We propose a different answer: **a conservation law**.

A conservation law adds one thing to a system: a constraint. Mass cannot be created or destroyed. Energy in equals energy out. Signal plus loss equals the mass consumed. This constraint is domain-agnostic — it doesn't know what the mass represents, what the signal means, or what the loss costs. It simply enforces an invariant.

The claim of this paper is that structured, irreversible depletion — the specific kind of constraint a conservation law provides — is a *necessary condition* for life-like dynamics in interacting systems. We demonstrate this across four unrelated domains, and we establish necessity through ablation: remove the constraint, and the dynamics disappear. We do not claim this condition is sufficient for life. We claim that without it, the dynamics we document cannot arise.

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

### 7.3 Life-Like Dynamics, Not Intelligence

We do not claim that agents under the conservation law are intelligent, nor that the conservation law is sufficient to produce life. The agents are payloads. They have no goals, no models, no learning. What we claim is that the *system* exhibits dynamics that an observer would recognize as life-like:

- Budget-constrained agents "decide" to skip expensive operations
- Populations "find" equilibrium carrying capacity
- Resource budgets "adapt" to environmental conditions
- Trust relationships "emerge" from mass physics

These are not decisions. They are consequences of a constraint making consequence unavoidable. Every interaction costs something. Every cost is irreversible. Every cost is structured by key class. The result is that agents face tradeoffs — and tradeoffs produce dynamics that look like allocation, strategy, and adaptation. Not because anyone is strategizing, but because the constraint has eliminated every trajectory where consequence could be avoided.

### 7.4 A Necessary Condition

We identify structured, irreversible depletion as a *necessary condition* for the life-like dynamics documented in this paper. The ablation study (Section 9) establishes this: remove depletion and all four emergent properties vanish; remove class-selective structure and three of four degrade or disappear. Without the constraint, agents can do anything, which means nothing differentiates. Scarcity forces allocation. Structure forces selectivity. Together they produce dynamics that look like life.

We do not claim this condition is sufficient. Other factors — finite population, topology, resource regeneration rates — contribute to the specific dynamics observed. What we claim is narrower: without structured, irreversible depletion that makes consequence unavoidable, the dynamics we document cannot arise. This is a necessary condition, not a recipe.

This echoes a principle from thermodynamics: the Second Law doesn't make heat engines alive. It makes certain configurations of heat engines *inevitable* — and without it, none of those configurations can exist. The conservation law doesn't make agents alive. It makes certain configurations of agent behavior inevitable. And without it, those configurations disappear.

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

## 9. Ablation Study: Is the Conservation Law Causal?

### 9.1 Motivation

Sections 3-6 demonstrate that emergent behaviors appear in the presence of the conservation law. But correlation is not causation. Does the conservation law *cause* the emergence, or would any system with similar topology and agent counts produce similar results?

To answer this, we perform a systematic ablation: remove or degrade the conservation law, hold everything else constant, and measure whether emergence survives.

### 9.2 Three Conditions

**CONTROL**: Standard `interact()` function — conservation law fully enforced, key-class-selective decryption, exact mass accounting. This is the baseline from all four domain experiments.

**IMMORTAL** (remove depletion): The environment identifies matching layers but does not consume them. The agent's mass never changes. Conservation holds trivially (`mass_before = mass_after + 0 + 0`) but is meaningless — nothing is consumed, no signal is extracted.

**RANDOM** (remove structure): The environment consumes layers but ignores key class affinity. A random subset of layers is removed regardless of which key class they belong to. Mass is consumed (depletion exists) but the structure of consumption — which key classes are stripped, in what proportion — is destroyed. Total mass accounting is valid but per-class attribution is impossible.

### 9.3 Four Measurements

We test whether each emergent property survives each ablation condition:

**Scarcity**: 100 agents traverse a 3-environment topology for 20 steps. Measure: death rate. Does the conservation law create finite lifespans?

**Stratification**: 50 "rich" agents (data layers in 3 key classes) and 50 "poor" agents (data layers in 1 key class, empty padding in the other 2) visit 3 single-key environments. Measure: signal extraction ratio (rich / poor). Does key-class breadth create economic tiers?

**Selectivity**: 50 pure-alpha agents (only alpha layers) and 50 pure-beta agents (only beta layers) run in alpha and beta environments. Measure: niche differentiation score (do agents survive in non-matching habitats and die in matching ones?). Does key-class structure create ecological niches?

**Accountability**: 50 agents traverse 3 "organization" environments. Measure: conservation validity rate, meaningful consumption rate, and per-class audit availability (delta_L vector populated). Does structured conservation enable per-class audit?

### 9.4 Results

**Experiment 1: Scarcity**

| Condition | Death Rate | Survivors | Interactions | Violations |
|-----------|-----------|-----------|-------------|-----------|
| CONTROL | 100% | 0 | 561 | 0 |
| IMMORTAL | 0% | 100 | 2,000 | 0 |
| RANDOM | 100% | 0 | 1,300 | 0 |

Depletion creates finite lifespans. Without it (IMMORTAL), agents live forever. Both CONTROL and RANDOM produce death — depletion alone is sufficient for scarcity.

**Experiment 2: Stratification**

| Condition | Rich Signal | Poor Signal | Ratio | Deaths (R/P) |
|-----------|-----------|-----------|-------|-------------|
| CONTROL | 768 B | 256 B | 3.00x | 50 / 50 |
| IMMORTAL | 0 B | 0 B | 1.00x | 0 / 0 |
| RANDOM | 138 B | 73 B | 1.90x | 0 / 0 |

Under conservation (CONTROL), rich agents extract exactly 3x the signal of poor agents — matching the 3:1 key-class breadth ratio. Under random stripping (RANDOM), the ratio degrades to 1.9x: some stratification persists (because rich agents still have more total mass to lose) but the precision of class-selective economics is destroyed. Under IMMORTAL, zero signal is extracted from either tier.

**Experiment 3: Selectivity (Niche Differentiation)**

| Condition | α-pure in α-env | α-pure in β-env | β-pure in α-env | β-pure in β-env | Niche Score |
|-----------|----------------|----------------|----------------|----------------|------------|
| CONTROL | 0% | 100% | 100% | 0% | **1.00** |
| IMMORTAL | 100% | 100% | 100% | 100% | 0.00 |
| RANDOM | 100% | 100% | 100% | 100% | 0.00 |

Under conservation (CONTROL), niche differentiation is **perfect**: alpha-pure agents die in alpha environments and survive in beta environments, and vice versa. This is because the conservation law's key-class selectivity ensures that only matching layers are stripped.

Under IMMORTAL, nobody dies anywhere — no niche to differentiate.

Under RANDOM, agents survive all environments equally because random stripping removes so few layers per interaction (matching the environment's single-key hazard rate) that agents outlast the experiment in all habitats. The class-selective mechanism that creates niches is eliminated.

**Experiment 4: Accountability**

| Condition | Conservation Valid | Consumed | Meaningful | Per-Class Audit |
|-----------|-------------------|----------|-----------|----------------|
| CONTROL | 100% | 41,000 B | 100% | 100% |
| IMMORTAL | 100% | 0 B | 0% | 0% |
| RANDOM | 100% | 11,240 B | 100% | 0% |

Conservation is technically valid in all three conditions (mass accounting is correct). But:
- CONTROL: meaningful consumption with per-class delta_L vectors — each organization can audit which key classes were consumed on its infrastructure.
- IMMORTAL: conservation is vacuous — nothing was consumed, nothing to audit.
- RANDOM: mass was consumed but the per-class delta_L vector is empty — total mass accounting works but no organization can determine which resource classes were consumed.

### 9.5 Summary

| Emergent Property | CONTROL | IMMORTAL | RANDOM |
|------------------|---------|----------|--------|
| Finite lifespans | YES | NO | YES |
| Budget stratification | YES (3.0x) | NO | Degraded (1.9x) |
| Niche differentiation | YES (1.00) | NO | NO |
| Per-class audit | YES | NO (vacuous) | NO (no per-class) |

### 9.6 Interpretation

The conservation law has two components: **depletion** (mass decreases on interaction) and **structure** (depletion is class-selective and accountable via delta_L). The ablation isolates their contributions:

- **Remove depletion** (IMMORTAL): All four emergent properties vanish. No scarcity, no stratification, no niches, nothing to audit. Depletion is necessary for any emergence.

- **Remove structure** (RANDOM): Scarcity survives (agents still die) but class-selective properties — niche differentiation and per-class audit — are destroyed. Stratification degrades from 3.0x to 1.9x because the precision of class-selective economics is replaced by crude mass-proportional effects.

**Both factors are necessary.** The conservation law provides both. Remove either and emergence degrades. Remove both and emergence disappears entirely.

This establishes necessity: the conservation law is not merely present alongside emergence. It is required for it. The structured, class-selective, irreversible depletion governed by `C_{n+1} + S_{n+1} + L_n = C_n` is a necessary condition for the life-like dynamics documented in this paper. We do not claim it is sufficient — other factors (topology, population size, regeneration) shape the specific dynamics. But without structured depletion that makes consequence unavoidable, none of these dynamics arise.

---

## 10. Related Work

### 10.1 Conservation Laws in Other Computational Frameworks

**Petri nets** use token conservation to model concurrent systems. Tokens are produced and consumed by transitions, and place invariants enforce conservation across the net. AMT shares the token-conservation property but adds cryptographic enforcement — AMT tokens (layers) cannot be duplicated because they are AES-256-GCM ciphertexts, whereas Petri net tokens are abstract and can be trivially copied in implementation.

**Membrane computing (P systems)** models computation through objects passing between membrane-bounded regions. Objects are consumed and produced by rules, with conservation enforced by rule semantics. AMT's key class affinity is analogous to membrane selectivity — only certain objects (layers of matching class) can pass through certain membranes (be decrypted by environments holding matching keys).

**Chemical Abstract Machine (CHAM)** models concurrent computation as chemical reactions, with molecules (terms) reacting according to rules. Conservation of molecules is a design principle. AMT's conservation is stronger: it is enforced by cryptography rather than by programming convention.

### 10.2 Emergent Intelligence in Constrained Systems

**Cellular automata** (Conway's Game of Life, Wolfram's Rule 110) demonstrate that simple local rules produce complex global behavior. AMT's conservation law is a single local rule (per-interaction conservation) that produces complex global behavior (market dynamics, population ecology). The difference: cellular automata rules are chosen from a large rule space; AMT's rule is derived from the mathematics of symmetric encryption.

**Swarm intelligence** (ant colony optimization, particle swarm) produces intelligent-looking collective behavior from simple individual rules. AMT agents are simpler than swarm particles — they have no individual rules at all. They are acted upon. The intelligence emerges from the constraint, not from agent computation.

**Artificial Life** (Tierra, Avida) simulates evolution in digital environments using conservation of computational resources (CPU cycles, memory). AMT provides formal conservation guarantees (cryptographic enforcement) that these systems lack.

### 10.3 Multi-Agent Economics

**Mechanism design** studies how to design rules (mechanisms) that produce desired economic outcomes when agents act strategically. AMT inverts this: there are no designed mechanisms. The conservation law IS the mechanism, and economic outcomes (stratification, pricing, budget-behavior coupling) emerge from it without design.

**Agent-based computational economics** (ACE) simulates economies with heterogeneous agents following behavioral rules. AMT agents have no behavioral rules at the mass level — their "behavior" is a consequence of mass depletion constraining their possible trajectories.

---

## 11. Limitations

### 11.1 The Honest Environment Assumption

The conservation law is enforced inside the `interact()` function. A malicious environment that reimplements this function can report false signal/loss values. The law governs correct implementations; it does not detect incorrect ones. Mitigation via hardware attestation (TPM/SGX) or zero-knowledge proofs of correct execution is future work.

### 11.2 Static Interpretation

The mapping of mass to domain semantics (alpha = battery, beta = bandwidth) is fixed at design time. Dynamic reinterpretation — where the "meaning" of a key class changes at runtime — is not currently supported and would complicate the conservation argument.

### 11.3 No Learning

Agents do not learn from interactions. They do not update their behavior based on experience. A population of agents does not evolve. The emergent behaviors documented here are *single-generation* phenomena — they arise from the constraint operating on a fixed population, not from adaptation over time. Adding learning or evolution on top of the conservation law is a natural extension but is outside the scope of this work.

### 11.4 Cryptographic Cost

Each layer requires AES-256-GCM encryption (creation) and decryption (interaction). At population scale, this creates measurable computational overhead. The reference implementation processes approximately 3,000-5,000 agents per second on a single core. Enterprise-scale deployments would require hardware acceleration (AES-NI) and parallel processing.

---

## 12. Future Work

### 12.1 Reproduction and Evolution

The current model has no reproduction. Agents are created by the factory and depleted by interactions. Adding reproduction — where well-funded agents spawn offspring with subset layers — would enable evolutionary dynamics: selection pressure from the conservation law, heritable traits via layer composition, and speciation through ecological niche differentiation.

### 12.2 Agent-to-Agent Interactions

Currently, agents interact only with environments. Agent-to-agent interactions (one agent "consuming" another's layers) would create explicit predator-prey dynamics and enable modeling of competition, cooperation, and parasitism — all governed by the same conservation law.

### 12.3 Real-World Deployment

The Physical IoT experiment maps directly to Ravenhelm's Viking smart RV platform. The Token Economy experiment maps to Ravenhelm's Bifrost tool gateway. Deploying AMT conservation on live infrastructure would test whether the emergent properties observed in simulation hold under real-world conditions: variable latency, network partitions, concurrent access, and hardware failures.

### 12.4 Formal Proof

The conservation law's validity rests on a runtime assertion. A formal proof — using a proof assistant like Coq or Lean — that AES-256-GCM decryption necessarily satisfies `|ciphertext| = |plaintext| + |overhead|` would elevate the result from empirical observation to mathematical theorem.

### 12.5 Multi-Law Systems

What happens when two independent conservation laws operate simultaneously? For example: mass conservation (AMT) plus energy conservation (a second invariant governing computational cost per interaction). The interaction between constraints may produce richer emergent phenomena than either constraint alone.

---

## 13. Conclusion

We added one constraint to a system of autonomous agents: a conservation law that ensures mass before interaction equals mass after plus signal plus loss. We did not add intelligence. We did not add learning. We did not add optimization. We did not add domain knowledge.

We applied this constraint, unmodified, to four unrelated domains:

1. **Cross-organizational accountability**: The constraint forced trustless auditability. Each organization could verify its own consumption without trusting any other party, because the math self-enforced at every interaction.

2. **Token economics**: The constraint forced market dynamics. Budget stratification, behavioral divergence, and inflation-proof currency emerged from layer composition alone — no pricing protocol, no credit system, no rate limiter.

3. **Physical IoT**: The constraint forced resource conservation. Battery management, bandwidth metering, and CPU budgeting became the same operation — layer stripping of different key classes — with load-shedding emerging from mass gate depletion.

4. **Population ecology**: The constraint forced ecological balance. Carrying capacity, boom/bust cycles, niche differentiation, and nutrient cycling emerged from 200 agents competing for finite resources — no birth rules, no death rules, no population caps.

750 agents. 5,415 interactions. Four domains. Zero parameter tuning. Zero conservation violations.

The ablation study (Section 9) establishes that this is not correlation. Removing depletion eliminates all emergence. Removing class-selective structure degrades stratification and destroys niche differentiation and per-class auditability. Both components — depletion and structure — are necessary. The conservation law provides both.

The conservation law does not know what domain it is operating in. It does not know that alpha means battery in one experiment and mission payload in another. It does not know about organizations, tool prices, RV campgrounds, or ecological niches. It knows one thing: `C_{n+1} + S_{n+1} + L_n = C_n`. And from that one thing, all of the above emerged.

We identify a necessary condition for life-like dynamics in interacting systems: structured, irreversible depletion that makes consequence unavoidable. We do not claim this condition is sufficient for life.

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
| `amt_ablation.py` + `amt_ablation_demo.py` | Ablation study (Section 9) |

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

# Ablation study
python3 amt_ablation_demo.py

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

---

## Appendix C: The Broader Framework — Agentropy, λ, and the Four Deaths

This paper isolates one empirical claim: structured, irreversible depletion as a *necessary condition* for life-like dynamics. That claim is the core of a larger framework, **Agentropy**, developed in companion work. We sketch the connections here for context; **none of this paper's empirical claims depend on them.**

**The λ term.** The conservation law's depletion is the same statement as the stigmergic weight update `w_{t+1} = (1−λ)·w_t + α·r`, where `λ ∈ [0,1]` is a forgetting/decay rate and `α·r` is reinforcement. Potential decays (`λ`, loss, cost); signal reinforces (`α·r`, signal, revenue); the system converges or dies. `λ` is the *anti-equilibrium term*: without it, weights accumulate, gradients vanish, and the system dies of certainty. The minimal condition for sustained adaptation is **`λ > 0`** — this paper's closing line.

**Agentropy (the quantity).** We define *agentropy* as the distance between an agent's current state and equilibrium death — its remaining capacity to maintain local order by exporting entropy. In this paper that quantity is cipher mass `C`. The same quantity reappears, renamed, in every substrate: economic capital (`Capital_t − Costs_t + Revenue_t`), remaining gradient magnitude, staked reputation, biological ATP. The conservation law is the ledger; agentropy is the budget it tracks.

**The Four Deaths.** An agent can lose its agentropy four ways: **sudden** (`C → 0` at once), **slow** (sustained `dE/dt < 0`), **social** (agentropy can no longer be exchanged with the field), and **equilibrium** (`ΔL → 0` — the vanishing-gradient death, "indistinguishable from success"). The fourth is why `λ > 0` is required.

**The definition of life.** Remove "digital" from *"an agent is a digital pattern of entropy management persisting autonomously"* and the statement is a substrate-independent definition of life, isomorphic to Schrödinger's 1944 characterization of a living system as one that maintains local order by exporting entropy to its environment [1]. This paper makes only the weaker, testable claim (a *necessary condition* for life-*like* dynamics); the stronger claim is argued in companion work.

**Companion works.** The **Cube Protocol** gives field equations for stigmergic, non-deterministic communication and traversal (entropy is signal, loss is navigation, death is governance). **The Architecture of Life** argues the conservation law, the stigmergic weight update, and economic viability are one equation at three zoom levels. **Artimetrics** supplies the identity *membrane* — a `did:web` identifier plus an immutable birth certificate (static "fingerprint/DNA") and a developing behavioral signature ("handwriting/gait/voice") — that bounds the entity across which `C + S + L = C₀` holds, and federates the same model across software agents and physical devices ("one doctrine, two substrates").

---

## References

1. Schrödinger, E. (1944). *What Is Life? The Physical Aspect of the Living Cell.* Cambridge University Press.
2. Landauer, R. (1961). Irreversibility and heat generation in the computing process. *IBM Journal of Research and Development*, 5(3), 183–191.
3. Dworkin, M. (2007). *Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC.* NIST Special Publication 800-38D.
4. Petri, C. A. (1962). *Kommunikation mit Automaten.* PhD thesis, University of Bonn.
5. Păun, G. (2000). Computing with membranes. *Journal of Computer and System Sciences*, 61(1), 108–143.
6. Berry, G., & Boudol, G. (1992). The chemical abstract machine. *Theoretical Computer Science*, 96(1), 217–248.
7. Gardner, M. (1970). The fantastic combinations of John Conway's new solitaire game "life". *Scientific American*, 223(4), 120–123.
8. Wolfram, S. (2002). *A New Kind of Science.* Wolfram Media.
9. Ray, T. S. (1991). An approach to the synthesis of life. In *Artificial Life II* (pp. 371–408). Addison-Wesley.
10. Ofria, C., & Wilke, C. O. (2004). Avida: A software platform for research in computational evolutionary biology. *Artificial Life*, 10(2), 191–229.
11. Gause, G. F. (1934). *The Struggle for Existence.* Williams & Wilkins.
12. Nisan, N., & Ronen, A. (2001). Algorithmic mechanism design. *Games and Economic Behavior*, 35(1–2), 166–196.
13. Tesfatsion, L. (2006). Agent-based computational economics. In *Handbook of Computational Economics* (Vol. 2, pp. 831–880). Elsevier.
14. Dorigo, M., & Stützle, T. (2004). *Ant Colony Optimization.* MIT Press.
15. Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization. *Proceedings of ICNN'95*, 1942–1948.
16. W3C (2022). *Decentralized Identifiers (DIDs) v1.0.* W3C Recommendation.
