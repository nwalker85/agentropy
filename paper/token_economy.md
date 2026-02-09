# Tool Calls as Conservation-Governed Payments: An Agent Token Economy

**Agent Mass Theory Applied to API Gateway Economics**

*Nate Walker — Ravenhelm*
*February 2026*

---

## Abstract

When an autonomous agent calls a tool through a gateway, how should it be charged? Traditional approaches — API keys with rate limits, credit-based billing, token metering — all require external enforcement: a billing service, a rate limiter, a credit ledger. We present an alternative where every tool call is a conservation-governed payment. Under Agent Mass Theory (AMT), an agent's mass consists of encrypted layers organized by key class. A tool gateway holds secrets for exactly one key class. When an agent enters the gateway, layers of that class are decrypted and consumed — this decryption IS the payment. The conservation law `C_{n+1} + S_{n+1} + L_n = C_n` ensures that mass cannot be created, double-spent, or inflated. An agent without layers of the required class simply cannot pay, and the conservation law — not a policy engine — prevents the call. We demonstrate this with five tool classes at five price points (API calls: 1 layer, LLM inference: 3 layers, storage: 2 layers, compute: 4 layers, admin: 1 layer), showing that budget-constrained agents are physically unable to call expensive tools, that behavioral divergence emerges from budget composition alone, and that at population scale (200 agents, 2,113 tool calls), zero conservation violations occur. No pricing protocol. No credit system. No rate limiter. The physics IS the pricing.

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
- **Enforcement** is a consequence of physics (no layers = no payment = no tool call)
- **Trust** is unnecessary (the math enforces itself)

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

1. The environment attempts to decrypt all layers matching its key class
2. Matching layers are consumed (payment extracted)
3. The conservation law is verified: `mass_before = mass_after + signal + loss`
4. If layers were stripped: the tool call succeeds
5. If no layers matched (agent has no affinity): the call fails silently
6. If the agent dies during payment: the call fails

```
Gateway("GPT-4", key_class="beta", cost=3)
    holds: secret_beta
    strips: all beta-class layers
    ignores: alpha, gamma, delta, epsilon layers
```

### 4.2 Composition, Not Inheritance

The gateway wraps a standard AMT `Node` via composition. It delegates to `node.process()` which calls `interact()`. The conservation law is enforced inside `interact()` — the gateway doesn't even need to check it. This is critical: **the gateway cannot cheat**. Even a malicious gateway implementation cannot violate conservation because the law is enforced at the interaction level, not the gateway level.

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

**Rich Agent** (36 layers, 2,208 B): Successfully calls Config (1 epsilon), Weather (7 alpha), GPT-4 (12 beta), Database (6 gamma), and dies paying for Batch Compute (8 delta). Conservation verified at every step: 5 interactions, 0 violations.

**Budget Agent** (6 layers, 328 B): Passes through Config (no epsilon affinity — no charge), calls Weather (4 alpha layers), partially pays for GPT-4 (1 beta layer stripped, but needs 3 — partial payment, tool still fires), dies paying for Database (1 gamma). Only 2 successful calls versus the rich agent's 4.

### 7.3 Population Scale

200 agents with Pareto-distributed budgets (reflecting real-world wealth distribution):

| Metric | Value |
|--------|-------|
| Total agents | 200 |
| Total tool calls | 2,113 |
| Successful calls | 449 |
| Survival rate | 45.5% |
| **Conservation violations** | **0** |

**Tool usage by class:**

| Class | Calls | Mass Consumed |
|-------|-------|---------------|
| admin | 53 | 14,196 B |
| api_call | 109 | 19,872 B |
| compute | 74 | 11,036 B |
| llm_inference | 115 | 23,436 B |
| storage_op | 98 | 17,144 B |

**Budget-behavior correlation:**
- Rich agents (>1,000 B): average 3.8 successful calls
- Poor agents (≤500 B): average 1.8 successful calls
- Rich agents make **2.1x** more successful tool calls

### 7.4 Conservation Proof

Every tool call is a conservation-governed interaction. At population scale:

```
For all 2,113 tool calls:
    C_{n+1} + S_{n+1} + L_n = C_n
    Verified. Zero violations.
```

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

### 8.2 No Double-Spending

Layers are destroyed upon decryption. An AES-256-GCM ciphertext, once decrypted, ceases to exist as a layer. The plaintext becomes signal (if non-empty) or loss (if empty/overhead). The encrypted form is gone. An agent cannot present the same layer twice because after the first presentation, the layer no longer exists.

### 8.3 Perfect Audit

Every gateway maintains a call log with per-call mass accounting. These logs commit to a public ledger via merkle root. Any observer can verify:
- Per-gateway: total calls, mass consumed, success rates
- Per-tool-class: aggregate usage statistics

No observer can determine:
- Which agent made which call
- What signal content was extracted
- Individual agent budgets or mass profiles

### 8.4 Emergent Pricing

Tool costs are not dynamically negotiated. They are frozen into the system architecture via tool class definitions and agent layer compositions. A 3-layer LLM call costs exactly 3 layers of the appropriate key class. This cost does not fluctuate with demand, time of day, or agent identity. Pricing is structural, not transactional.

### 8.5 Budget Stratification

An agent's tool access is determined entirely by its layer composition. No access control list, permission matrix, or role-based policy intervenes. An agent with zero delta layers simply cannot call compute tools. An agent with 12 beta layers has exactly 4 LLM calls. This creates natural economic tiers without any tier-management infrastructure.

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

All related systems are **protocols** — agreements about how accounting should work. AMT's token economy is a **conservation law** — a physical constraint on how accounting *must* work. The distinction: a protocol can be violated by a sufficiently creative adversary; a conservation law cannot, because it is enforced by the mathematical structure of the interaction itself.

---

## 11. Limitations and Future Work

### Fixed Pricing

Tool costs are set at agent creation time. Dynamic pricing (surge pricing, market-based rates) would require a mechanism to modify layer compositions at runtime, which conflicts with the one-way nature of encryption-based mass. Future work could explore accretion-based price adjustment, where gateways accrete "discount layers" onto agents during low-demand periods.

### Single-Class Gateways

Each gateway holds secrets for exactly one key class. A multi-class gateway (holding secrets for alpha AND beta) would charge agents for multiple layer types simultaneously — a "bundled tool call." The conservation law permits this, but the economic semantics need formalization.

### Cross-Organization Tool Economies

Combining this work with cross-organizational accountability (Walker 2026c) would enable multi-party tool marketplaces where different organizations operate different gateways, each with independent accounting, unified by the conservation law.

### Real-World Integration

The natural next step is mapping this token economy onto Ravenhelm's Bifrost tool gateway, where each MCP tool registration defines a tool class and Freyr agents are built with layer compositions reflecting their tool budgets.

---

## 12. Conclusion

We have demonstrated that conservation-governed agent mass provides a complete token economy without any pricing protocol, credit system, or rate limiter:

- **Tool calls are interactions.** A gateway is an environment. Payment is decryption. Conservation is enforcement.
- **Layers are currency.** Each key class is a denomination. Each tool class has a price in layers.
- **Budget is mass profile.** An agent's economic identity is its layer composition.
- **Behavioral divergence is emergent.** Same topology, same parameters, different budgets → different tool usage patterns.
- **Conservation is absolute.** 200 agents, 2,113 tool calls, zero violations.

The math is the market. The physics is the pricing. No protocol needed.

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
