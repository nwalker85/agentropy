# Tool Calls as Conservation-Governed Payments: An Agent Token Economy

**Agent Mass Theory Applied to API Gateway Economics**

*Nathan Walker — Ravenhelm*
*February 2026*

---

## Abstract

When an autonomous agent calls a tool through a gateway, how should it be charged? Traditional approaches — API keys with rate limits, credit-based billing, token metering — all require external enforcement: a billing service, a rate limiter, a credit ledger. We present an alternative where every tool call is a conservation-governed payment. Under Agent Mass Theory (AMT), an agent's mass consists of encrypted layers organized by key class. A tool gateway holds secrets for exactly one key class. When an agent enters the gateway, layers of that class are decrypted and consumed — this decryption IS the payment. The conservation law `C_{n+1} + S_{n+1} + L_n = C_n` ensures that no mass is created outside the factory and that every consumed byte is accounted for. (v1.0.1 erratum: it does not, by itself, prevent double-spending — a copied agent holds copyable ciphertext; see §8.2.) An agent without layers of the required class simply cannot pay, and the gateway's price check — a rule layered on the conservation law, not the law itself — refuses the call. We demonstrate this with five tool classes at five price points (API calls: 1 layer, LLM inference: 3 layers, storage: 2 layers, compute: 4 layers, admin: 1 layer), showing that budget-constrained agents are physically unable to call expensive tools, that behavioral divergence emerges from budget composition alone, and that at population scale (200 agents, 2,113 tool calls), zero conservation violations occur. No pricing protocol. No credit system. No rate limiter. The physics IS the pricing.

---

## 1. Introduction

### The Tool-Cost Problem

Every agent platform faces the same question: how do you charge agents for tool usage? The problem has two dimensions:

**Accounting**: How do you track what each agent consumed?

**Enforcement**: How do you prevent an agent from consuming more than it should?

Current solutions treat these as separate concerns:

| Approach | Accounting | Enforcement | Trust Requirement |
|----------|-----------|-------------|-------------------|
| API keys + rate limits | Usage counters | Rate limiter service | Trusted gateway |
| Token metering | Token budget DB | Budget check middleware | Trusted budget service |
| Credit system | Credit ledger | Balance check | Trusted ledger |
| Blockchain billing | On-chain tx | Smart contract | Consensus mechanism |

Every approach requires a trusted external service. The rate limiter can be bypassed. The credit ledger can be corrupted. The billing service can go down. These are protocols — they can be violated.

### Conservation Laws Cannot Be Violated

A conservation law is not a protocol. It is a constraint that holds at every interaction, enforced by the structure of the system itself. Under AMT, the conservation law `C_{n+1} + S_{n+1} + L_n = C_n` states that at every interaction, the agent's mass after (`C_{n+1}`) plus the signal extracted (`S_{n+1}`) plus the loss incurred (`L_n`) equals the mass before (`C_n`). This holds because:

1. Layers are AES-256-GCM encrypted containers
2. Decryption destroys the encrypted form (the layer is consumed)
3. The signal (decrypted content) and loss (encryption overhead) account for all consumed mass
4. No mechanism exists to create mass outside the factory

If we map tool classes to key classes and require payment via layer consumption, we get a token economy where:

- **Accounting** is a consequence of conservation (every byte accounted for)
- **Enforcement** has two parts: no layers = no payment (a consequence of key affinity), and *exactly the declared price is charged* (a gateway rule, enforced in code since v1.0.1 — v1.0.0 stripped every matching layer and never consulted the price)
- **Trust** in the arithmetic is unnecessary (each party can recompute it); trust in the *executor's honesty* is assumed — see §11 and Walker 2026a §9

---

## 2. AMT Foundations

We briefly summarize the relevant AMT constructs (see Walker 2026a for the full treatment).

### 2.1 Agent Mass

An agent is a collection of encrypted layers. Each layer `l` is encrypted under a key class `k` with payload `p`:

```
l = AES-256-GCM(derive_key(master_secret_k, salt=k), p)
mass(l) = len(nonce) + len(ciphertext) + len(tag) = 12 + len(p) + 16
```

The agent's total mass is `C = Σ mass(l_i)` for all layers `l_i`.

### 2.2 Interaction

When an agent enters an environment holding secrets for key classes `K`, all layers encrypted under any `k ∈ K` are decrypted and consumed. The conservation law applies:

```
C_{n+1} + S_{n+1} + L_n = C_n
```

Where `S` = sum of non-empty decrypted payloads, `L` = sum of empty payloads + encryption overhead.

### 2.3 Key Affinity

An environment strips only layers whose key class matches its secrets. An environment with secret for class `alpha` cannot strip `beta` layers. This selective decryption is the foundation of the token economy.

---

## 3. Tool Class Architecture

### 3.1 Mapping Tools to Key Classes

A **tool class** maps a category of tools to a specific key class and price point:

| Tool Class | Key Class | Cost (layers) | Examples |
|-----------|-----------|--------------|---------|
| `api_call` | alpha | 1 | Weather, search, lookup |
| `llm_inference` | beta | 3 | GPT-4, DeepSeek, Claude |
| `storage_op` | gamma | 2 | Database read/write |
| `compute` | delta | 4 | ML training, batch jobs |
| `admin` | epsilon | 1 | Config, status |

The cost is measured in **layers**, not bytes. Each layer consumed has a fixed encryption overhead (28 bytes for AES-256-GCM nonce + tag) plus whatever payload was encoded. The cost is deterministic.

### 3.2 Why Layers, Not Bytes

Bytes would be a finer-grained currency, but layers have a critical property: **they are atomic**. A layer is either consumed or not. There is no partial consumption. This makes the budget model exact — an agent with 3 beta layers can make exactly 1 LLM inference call (3 layers / 3 layers per call), with zero ambiguity.

### 3.3 Price Differentiation

The cost reflects the computational expense of the tool:

- **API calls** (1 layer): Cheap, stateless, fast. An HTTP round-trip.
- **LLM inference** (3 layers): Expensive. GPU time, model loading, token generation.
- **Storage ops** (2 layers): Moderate. I/O latency, durability guarantees.
- **Compute** (4 layers): Very expensive. Sustained GPU/CPU allocation.
- **Admin** (1 layer): Cheap. Metadata operations.

These prices are not arbitrary. They are design decisions frozen into the agent's layer composition at creation time. Changing them requires building agents with different layer profiles — a factory-level decision, not a runtime negotiation.

---

## 4. The Tool Gateway

### 4.1 Gateway as Environment

A **tool gateway** is an AMT environment that holds exactly one secret — for its tool class's key class. When an agent enters:

1. The gateway counts the agent's layers of its key class against the declared price (`base_cost`)
2. Fewer layers than the price: the call is refused as `insufficient_funds` **before** any layer is consumed
3. Otherwise exactly `base_cost` matching layers are consumed (payment extracted); further layers of the class survive
4. The conservation law is verified on the consumed layers: `mass_before = mass_after + signal + loss`
5. If the agent survives payment: the tool call succeeds
6. If no layers matched (agent has no affinity): the call fails silently, nothing charged
7. If the agent dies during payment: the call fails

*v1.0.1 erratum.* In v1.0.0 the gateway stripped **every** layer of its class and reported success whenever at least one layer was removed and the agent survived; `base_cost` was never consulted. An agent holding one beta layer was charged one layer and recorded as a successful three-layer LLM call; an agent holding twelve was charged all twelve for one call (Overmier 2026, review items 3, 5–9). The list above describes the v1.0.1 implementation.

```
Gateway("GPT-4", key_class="beta", cost=3)
    holds: secret_beta
    strips: exactly 3 beta-class layers per call (refuses if fewer than 3 are held)
    ignores: alpha, gamma, delta, epsilon layers
```

### 4.2 Composition, Not Inheritance

The gateway wraps a standard AMT `Node` via composition. It delegates to `node.process(agent, max_layers=base_cost)` which calls `interact()`. The conservation law is enforced inside `interact()` — the gateway doesn't need to check it. What the gateway *does* own is the price: counting held layers against `base_cost` and bounding consumption to it. A gateway that skipped that check would still satisfy conservation and still overcharge — which is exactly what v1.0.0 did. Conservation constrains *how consumed bytes are accounted for*; it does not constrain *how many are consumed*. (v1.0.0 said here that "the gateway cannot cheat"; that was true of the arithmetic and false of the price.)

### 4.3 The Call Log

Each gateway maintains a call log recording:
- Agent hash (anonymized identifier)
- Mass before and after
- Layers charged
- Signal and loss
- Outcome (success, no_affinity, died_paying, blocked)
- Timestamp

This log enables per-gateway audit without revealing agent identities. The log entries can be committed to a public ledger via merkle root, providing third-party verifiability with zero information leakage about individual calls.

---

## 5. Agent Budget as Observer

### 5.1 Budget Is Not Enforcement

An `AgentBudget` is an external observer that computes what an agent can afford based on its current mass profile. It does not enforce anything. The conservation law handles enforcement.

This is like checking your bank balance. The balance doesn't prevent you from spending — it tells you what you can spend. The banking system (conservation law) prevents overdraft.

### 5.2 Budget Computation

For each tool class, the budget counts layers of the corresponding key class:

```
calls_remaining(tool_class) = layers_of(key_class) // base_cost
```

An agent with 12 beta layers can make 4 LLM inference calls (12 / 3 = 4). After 2 calls, it has 6 beta layers remaining: 2 more calls.

### 5.3 Budget Stratification

Agents with different layer compositions have different budget profiles. This creates natural economic stratification:

| Agent Type | Alpha | Beta | Gamma | Delta | Epsilon | Tool Access |
|-----------|-------|------|-------|-------|---------|-------------|
| Rich | 7 | 12 | 6 | 8 | 3 | All tools, multiple calls |
| Budget | 4 | 1 | 1 | 0 | 0 | API calls only |
| Specialist | 0 | 9 | 0 | 0 | 0 | LLM inference only (3 calls) |

No access control list creates this stratification. No policy engine evaluates it. The agent's mass profile IS its economic identity.

---

## 6. Behavioral Divergence from Budget

### 6.1 The Divergence Theorem

**Theorem (Budget-Behavior Coupling)**: Given two agents with identical behavioral parameters (risk tolerance, desperation curve, exploration rate) but different layer compositions, their tool usage patterns will diverge as a function of their mass profiles.

*Proof sketch*: AgentBehavior's `choose_node()` evaluates candidate nodes by estimated hazard (layers likely to be stripped). A gateway holding secrets for key class `k` has hazard proportional to the agent's layers of class `k`. An agent with zero `delta` layers perceives the `compute` gateway as zero-hazard (nothing to lose) but also zero-value (no payment possible, tool won't execute). The behavioral function routes the agent away from gateways it cannot pay for — not because it's told to, but because the mass-dependent risk calculus makes those gateways non-viable.

### 6.2 Experimental Observation

In our demonstration, two agents traverse the same topology with the same behavioral seed:

**Agent A** (well-funded, 2,360 B): Uses LLM inference, storage, and API calls freely. Its budget enables diverse tool usage.

**Agent B** (budget, 388 B): Clusters on cheap API calls. Cannot afford LLM inference (needs 3 beta layers, has 1) or compute (needs 4 delta, has 0). Its tool usage is shaped entirely by its layer composition.

Same parameters. Same topology. Same seed. Different budgets. Different tool usage. Different outcomes.

This is not a bug. This is emergent economics. Budget IS behavior.

---

## 7. Experimental Results

### 7.1 Setup

We implement the token economy with:
- 5 tool classes (api_call, llm_inference, storage_op, compute, admin)
- 7 gateways (Weather API, Web Search, GPT-4, DeepSeek, Database, GPU Compute, Config)
- A hub-and-spoke topology connecting gateways through a central routing node

### 7.2 Individual Agent Scenarios

**Rich Agent** (36 layers, 2,208 B): Successfully calls Config (1 epsilon), Weather (1 alpha), GPT-4 (3 beta), Database (2 gamma) and Batch Compute (4 delta) — exactly the declared price each time — and finishes alive at 1,372 B with budget to spare. Conservation verified at every step: 5 interactions, 0 violations. *(v1.0.0 reported this agent being drained of 7, 12, 6 and 8 layers respectively and dying at Batch Compute; that was the gateway stripping every layer of its class, not the price.)*

**Budget Agent** (6 layers, 328 B): Passes through Config (no epsilon affinity — no charge), calls Weather (1 alpha), is **refused** at GPT-4 (holds 1 beta, price 3 — `insufficient_funds`, nothing consumed), refused at Database (holds 1 gamma, price 2), and has no affinity for Batch Compute. One successful call versus the rich agent's five; it survives with its unspent layers. *(v1.0.0 recorded the one-layer GPT-4 payment as a success and then printed that the agent "couldn't afford" it — the log and the prose disagreed. Overmier 2026, item 7.)*

### 7.3 Population Scale

200 agents with Pareto-distributed budgets (reflecting real-world wealth distribution):

| Metric | v1.0.1 reference run | v1.0.0 |
|--------|-------|-------|
| Total agents | 200 | 200 |
| Total tool calls (all outcomes) | 2,574 | 2,113 |
| Successful calls | 468 | 449 |
| Refused — insufficient funds | 728 | (not an outcome in v1.0.0) |
| No affinity | 1,373 | — |
| Died paying | 5 | — |
| Survival rate | 97.5% (195) | 45.5% (91) |
| **Conservation violations** | **0** | **0** |

*The v1.0.1 column is deterministic across processes (hash-seed-independent neighbour order). The v1.0.0 column was one draw: the reviewer observed 2,090–2,206 calls and 100–106 survivors across three `PYTHONHASHSEED` values; the author 2,093–2,125 and 88–107. Survival rose because the gateway no longer drains every layer of its class.*

**Tool usage by class (successful calls, v1.0.1):**

| Class | Calls | Mass Consumed | v1.0.0 calls / mass |
|-------|-------|---------------|------|
| admin | 97 | 6,364 B | 53 / 14,196 B |
| api_call | 211 | 13,620 B | 109 / 19,872 B |
| compute | 23 | 6,096 B | 74 / 11,036 B |
| llm_inference | 60 | 11,200 B | 115 / 23,436 B |
| storage_op | 77 | 9,240 B | 98 / 17,144 B |

**Budget-behavior correlation (v1.0.1):**
- Rich agents (>1,000 B): average 10.0 successful calls (v1.0.0: 3.8)
- Poor agents (≤500 B): average 1.0 successful calls (v1.0.0: 1.8)
- Rich agents make **9.8x** more successful tool calls (v1.0.0: 2.1x). The gap widened because refused payments leave poor agents' layers unspent and unusable, while rich agents are no longer drained to death.

### 7.4 Conservation Proof

Every tool call is a conservation-governed interaction. At population scale:

```
For all 2,574 tool calls (v1.0.1; 2,113 in v1.0.0):
    C_{n+1} + S_{n+1} + L_n = C_n
    Verified. Zero violations.
```

This is an accounting identity (Walker 2026 Appendix B): `loss` is defined as the consumed mass not returned as signal, so the equation cannot fail in a correct implementation. Zero violations confirms the bookkeeping, not a law of nature (*v1.0.1 wording*).

The conservation law holds regardless of:
- Agent budget level
- Tool class
- Gateway configuration
- Behavioral parameters
- Population size

---

## 8. Economic Properties

The token economy exhibits five fundamental economic properties, all emerging from the conservation law rather than from protocol design.

### 8.1 No Inflation

Conservation prevents mass creation. The total mass in the system can only decrease (via signal extraction and loss) or remain constant (when no interactions occur). New mass enters only through the factory — the monetary authority — which creates agents with specific layer compositions. There is no mechanism for agents, gateways, or any system component to create mass ex nihilo.

### 8.2 Local Destruction, Not Double-Spend Resistance

*Rewritten in v1.0.1; the v1.0.0 heading was "No Double-Spending" and the paragraph was wrong as written.*

When a layer is decrypted, the reference implementation removes it from the agent's layer list. Within one honest process the agent cannot present that layer again, and the plaintext becomes signal (if non-empty) or loss (if empty/overhead). That is all AES-256-GCM gives: confidentiality and integrity of the bytes. It does not give a byte string uniqueness, custody, or one-time existence. The ciphertext is ordinary data; a copy of the agent taken before decryption still holds it, and a gateway that receives the copy will accept the same payment a second time. The reference implementation demonstrates this directly (`tests/test_known_limitations.py`, `docs/reviews/2026-08-22-overmier-v1.0.0/`). Walker 2026a §9 already listed "clone the agent (copy layers before decrypting)" as a move available to a dishonest environment; this section previously claimed the opposite.

Preventing replay requires an authority outside the encryption scheme that can answer whether a specific capability is valid *now* and whether it has already been consumed — a transactional ledger, signed state, secure hardware, or a settlement protocol. That is v2 work, with its own threat model. The v1.0.x claim is narrower: **destruction is irreversible within the holder's process, and every byte consumed is accounted for.**

### 8.3 Perfect Audit

Every gateway maintains a call log with per-call mass accounting. These logs commit to a public ledger via merkle root. Any observer can verify:
- Per-gateway: total calls, mass consumed, success rates
- Per-tool-class: aggregate usage statistics

No observer can determine:
- Which agent made which call
- What signal content was extracted
- Individual agent budgets or mass profiles

### 8.4 Emergent Pricing

Per-key pricing is structural, not transactional. A 3-layer LLM call costs exactly 3 layers of the appropriate key class — enforced by the gateway since v1.0.1 (`ToolGateway.process_tool_call`; asserted in `tests/test_price_enforcement.py`). This cost does not fluctuate with demand, time of day, or agent identity.

However, per-visit pricing is dynamic. An environment's total cost is determined by how many key classes it holds — its hazard surface. Under load, an environment can arm itself with additional keys, stripping more layer types per visit without changing the cost of any individual key class. This creates a natural throttle: fixed unit prices with dynamic aggregate cost, governed entirely by key rotation rather than rate negotiation.

### 8.5 Budget Stratification

An agent's tool access is determined by its layer composition and the gateway's declared price. No access control list, permission matrix, or role-based policy intervenes. An agent with zero delta layers simply cannot call compute tools. An agent with 12 beta layers has exactly 4 LLM calls (true since v1.0.1; in v1.0.0 it had one call that cost all twelve). This creates natural economic tiers without any tier-management infrastructure — but note that the price check is a gateway rule; what the conservation law contributes is that the tiers cannot be inflated from inside the agent.

---

## 9. Cube Protocol Mapping

The token economy implements three of the five Cube Protocol principles (Walker 2026b):

**Presence not Identification**: Agents are identified by hash, not identity. A gateway sees `agent_hash: 7a2f...` — it knows something paid, but not who.

**Capability Leakage not Authority**: An agent's tool access leaks through its layer composition. An observer seeing 12 beta layers knows the agent can make 4 LLM calls. But this leaks capability (what it *can* do), not authority (what it's *allowed* to do). The distinction is fundamental: capability is a physical property; authority is a social convention.

**Outcome Leakage not Intent**: The audit log reveals aggregate outcomes (N calls to GPT-4, M bytes consumed) but not intent (why the agent called GPT-4, what it was trying to accomplish). Statistical leakage via merkle roots makes even the aggregate sparse.

---

## 10. Related Work

### Token-Based API Billing

Most AI platforms (OpenAI, Anthropic, Google) bill by token count — input tokens + output tokens × price per token. This requires a trusted billing service, a credit system, and rate limiting. AMT replaces all three with a conservation law.

### Blockchain-Based Micropayments

Projects like Filecoin and Helium use blockchain for resource payments. These require consensus mechanisms, gas fees, and transaction finality delays. AMT has zero consensus overhead — the conservation law is verified locally at each interaction.

### Agent Budgeting Frameworks

LangChain's callback system and AutoGPT's budget tracking monitor agent spending externally. These are observational — they track but don't enforce. AMT's conservation law both tracks and enforces, inseparably.

### Key Differentiator

All related systems are **protocols** — agreements about how accounting should work. AMT's token economy rests on an **accounting identity** — `loss` is defined as `mass − signal`, so the books balance by construction (Walker 2026 Appendix B: "It holds because subtraction works"). The distinction the v1.0.0 text drew — that a protocol can be violated and a conservation law cannot — is true of the arithmetic and only the arithmetic. The identity does not prevent a copied agent from paying twice, a gateway from ignoring its price, or an executor from lying about what it consumed; those are protocol-level properties and need protocol-level (or ledger-level) enforcement. *(Rewritten in v1.0.1.)*

---

## 11. Limitations and Future Work

### Fixed Pricing Per Key — Dynamic Hazard Via Key Count

Tool costs per key class are fixed at agent creation time. The cost of one beta layer is always one beta layer. This favors predictability over market efficiency: you cannot surge-price a single key.

But this does not mean environments cannot react to load. The actual cost of visiting a node is determined by **how many key classes** the environment holds — its hazard surface. An environment under pressure doesn't raise the price per key. It **arms itself with more keys**.

```
Normal load:    Gateway holds [alpha]         → strips alpha layers only
High load:      Gateway adds [alpha, beta]    → strips alpha AND beta per visit
Critical load:  Gateway adds [alpha, beta, gamma] → three classes stripped simultaneously
```

The conservation law doesn't change. The cost per layer doesn't change. But the agent pays more mass per visit because more of its layers have key affinity with the environment. This is surge pricing expressed as environmental adaptation, not rate negotiation.

Key rotation — the mechanism for adding and removing keys at runtime — already exists in the AMT extensions layer (temporal hazard). An environment recovering from load drops keys, becoming safer. An environment under stress adds keys, becoming more hazardous.

The analogy is not "raise the toll." It is "add more toll booths on the same road." Each booth costs the same. But you go through more of them. Fixed pricing per key is a feature — predictability. Dynamic hazard via key count is the throttle.

### Single-Class Gateways

Each gateway holds secrets for exactly one key class. A multi-class gateway (holding secrets for alpha AND beta) would charge agents for multiple layer types simultaneously — a "bundled tool call." The conservation law permits this, but the economic semantics need formalization.

### Cross-Organization Tool Economies

Combining this work with cross-organizational accountability (Walker 2026c) would enable multi-party tool marketplaces where different organizations operate different gateways, each with independent accounting, unified by the conservation law.

### Real-World Integration

The natural next step is mapping this token economy onto Ravenhelm's Bifrost tool gateway, where each MCP tool registration defines a tool class and Freyr agents are built with layer compositions reflecting their tool budgets.

---

## 12. Conclusion

We have demonstrated that conservation-governed agent mass provides a complete token economy without any pricing protocol, credit system, or rate limiter:

- **Tool calls are interactions.** A gateway is an environment. Payment is decryption. Conservation is the accounting; the price check is the enforcement.
- **Layers are currency.** Each key class is a denomination. Each tool class has a price in layers, charged exactly (v1.0.1).
- **Budget is mass profile.** An agent's economic identity is its layer composition.
- **Behavioral divergence is emergent.** Same topology, same parameters, different budgets → different tool usage patterns.
- **The accounting identity held on every call.** 200 agents, 2,574 tool calls (v1.0.1 reference run; 2,113 in v1.0.0), zero violations.

What this does not provide, and v1.0.0 claimed it did: double-spend resistance across copies, and price enforcement without a gateway rule. See §8.2 and the v1.0.1 errata (`paper/ERRATA-v1.0.1.md`).

---

## Appendix A: Implementation

The reference implementation is available in the AMT codebase:

- `amt_token_economy.py`: Extension module (ToolClass, ToolGateway, AgentBudget, TokenEconomyTopology)
- `amt_token_economy_demo.py`: Six-demo demonstration script

Key classes:
- **ToolClass**: Maps tool category → key class + cost
- **ToolGateway**: Wraps Node, delegates to `interact()` for conservation-governed payment
- **AgentBudget**: Observer computing remaining budget from mass profile
- **TokenEconomyTopology**: Wraps Topology with gateway registry and economic audit

## Appendix B: Full Scale Results

Population: 200 agents, Pareto-distributed budgets

v1.0.1 reference run (`python3 amt_token_economy_demo.py`, any `PYTHONHASHSEED`):

```
Agents:              200
Total tool calls:    2,574
Successful calls:    468
Agents surviving:    195 (97.5%)
Conservation violations: 0
Calls by outcome:
  died_paying               5
  insufficient_funds      728
  no_affinity           1,373
  success                 468

Tool Usage by Class:
  Class              Calls       Mass
  admin                 97      6,364
  api_call             211     13,620
  compute               23      6,096
  llm_inference         60     11,200
  storage_op            77      9,240

Budget-Calls Correlation:
  Rich agents (>1000B):  avg 10.0 successful calls
  Poor agents (<=500B):  avg 1.0 successful calls
  Rich agents make 9.8x more tool calls.
```

v1.0.0 reference run, retained for the record (one process-dependent draw):

```
Agents:              200
Total tool calls:    2,113
Successful calls:    449
Agents surviving:    91 (45.5%)
Conservation violations: 0

Tool Usage by Class:
  Class              Calls       Mass
  admin                 53     14,196
  api_call             109     19,872
  compute               74     11,036
  llm_inference        115     23,436
  storage_op            98     17,144

Budget-Calls Correlation:
  Rich agents (>1000B):  avg 3.8 successful calls
  Poor agents (<=500B):  avg 1.8 successful calls
  Rich agents make 2.1x more tool calls.
```
