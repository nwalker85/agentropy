# Multi-Agent Marketplace: Population Ecology from Conservation Law

**Agent Mass Theory Applied to Resource Competition and Nutrient Cycling**

*Nathan Walker — Ravenhelm*
*February 2026*

---

## Abstract

When multiple agents compete for finite environmental resources under AMT's conservation law, population-level dynamics emerge. We present a marketplace extension where nodes have finite resource pools that regenerate over time, and a nutrient cycling mechanism converts consumed mass into new layers for survivors. The conservation law `C_{n+1} + S_{n+1} + L_n = C_n` governs every interaction — it is never modified. Resource pools are environmental capacity (not agent mass) that gate accretion. Nutrient cycling creates new mass through the factory (the only legitimate mass source). We demonstrate with 200 agents competing across 5 marketplace nodes: the population declines monotonically to a tail of 2–5 agents, nutrient cycling embodies 29.3 % of captured nutrients as new payload (v1.0.1 accounting; v1.0.0 reported 77.3 % by counting budget rather than accreted mass), and the two predefined agent profiles survive at different rates. Zero conservation violations across 1,942 interactions (v1.0.1 reference run). *v1.0.1 wording:* the model has no reproduction, so carrying capacity, boom/recovery, and speciation are not observable in it; what is observed is differential depletion of a fixed cohort.

---

## 1. Introduction

### From Single Agent to Population

Previous AMT work demonstrated conservation at the individual level: one agent, one interaction, one conservation check. But real agent systems involve populations — hundreds of agents competing for shared infrastructure, consuming finite resources, and creating externalities for each other.

The question is: does the conservation law scale to population dynamics? And if so, what emergent properties appear?

### The Marketplace Metaphor

A marketplace is a topology where:
- **Nodes have finite resources** (not infinite environments)
- **Resources regenerate** (but slower than consumption during population peaks)
- **Dead agents' mass recycles** (the food chain)
- **Competition is implicit** (shared resources, not explicit conflict)

No agent "knows" about other agents. Each agent simply interacts with nodes, losing mass per the conservation law. The population dynamics that *can* emerge in a model without births — differential depletion, resource contention, recycling — emerge from this micro-level physics. (v1.0.0 listed "carrying capacity, boom/bust, speciation" here; see §5 errata.)

---

## 2. Resource Pools

### 2.1 Finite Environmental Capacity

Each marketplace node has a `ResourcePool` with:
- **Capacity**: Maximum resource units (fixed)
- **Current**: Currently available units (depletes and regenerates)
- **Regeneration rate**: Units per second (passive environmental renewal)

Resources are NOT agent mass. They are environmental capacity that gates accretion (new mass creation for agents). When a pool is depleted, agents can still interact (conservation still works), but they cannot accrete new layers (no fuel for growth).

### 2.2 Regeneration

Resources regenerate passively over time:

```
current = min(capacity, current + regeneration_rate × elapsed_time)
```

This models natural resource renewal — a grazing field regrows, a power supply recharges, a compute cluster becomes available again. The regeneration rate bounds how often accretion can occur.

*v1.0.1 erratum — one-tick clock offset.* In v1.0.0 a pool's clock basis (`last_tick`) defaulted to wall-clock time while the simulation ticked from `t = 0`, so the first tick's regeneration was lost (elapsed clamped to zero) before the clock rebased; every later tick regenerated normally — 29 of 30 ticks in the reference run. The reviewer's single-tick probe therefore read zero and concluded regeneration "does not occur"; it does, minus one tick (Overmier 2026, marketplace section; verification item 16). v1.0.1 puts pools on the simulation clock when they join a topology.

### 2.3 Depletion Dynamics

When many agents consume resources faster than regeneration, the pool depletes. Depletion has two effects:
1. **No accretion**: Agents can't grow (no fuel)
2. **Starvation cascade**: Without accretion, agents deplete faster, die sooner

This creates boom/bust dynamics without any explicit population management.

---

## 3. Nutrient Cycling: The Food Chain

### 3.1 Signal and Loss as Nutrients

When an agent interacts with a node, the conservation law produces signal (S) and loss (L). The `NutrientCycler` captures a fraction of these as nutrients:

```
nutrients = signal × signal_ratio + loss × loss_ratio
```

Default ratios: 30% of signal, 10% of loss. The rest is truly lost (entropy).

### 3.2 Cycling Threshold

Nutrients accumulate until reaching a threshold, then cycle:

```python
if accumulated >= cycle_threshold:
    new_layers = factory.create_layers(accumulated)
    accrete(next_agent, new_layers)
```

The factory is the ONLY legitimate mass source. Per-interaction conservation holds because:
1. Agent A loses mass via `interact()` (conservation verified ✓)
2. NutrientCycler captures a fraction of that mass
3. Factory creates new layers from the captured budget
4. Agent B accretes new layers (separate from conservation)

*v1.0.1 erratum — there is no system-level mass equation.* v1.0.0 said here "No mass is created from nothing." At the system boundary that is not what the code does: every layer the factory mints carries 28 bytes of fresh AES-GCM overhead that never came from a nutrient, and v1.0.0's cycler counted its whole budget as "cycled" while the node accreted at most the first three layers it generated. A 300-byte nutrient budget produced 356 bytes of new ciphertext with two key classes and 440 with five (Overmier 2026, items 17–18; reproduced). v1.0.1 counts as cycled only the payload bytes actually accreted, keeps the rest in the pool, and *reports* the minted overhead (§6.3) — it does not enforce a global equation tying created mass to lost mass. Writing that equation is v2 work.

### 3.3 The Food Chain

```
Agent A interacts → dies → signal + loss deposited
                              ↓
                        NutrientCycler accumulates
                              ↓
                        threshold reached → cycle()
                              ↓
                        factory.create_layer() (new mass)
                              ↓
                        accrete onto Agent B
```

Agent A's death fuels Agent B's survival. This is the conservation-governed food chain.

---

## 4. Marketplace Topology

### 4.1 Node Types

Our reference marketplace has five nodes:

| Node | Key Classes | Resources | Role |
|------|-----------|-----------|------|
| Feeding A | alpha | 500 cap, 2.0/s regen | Alpha-specialist habitat |
| Feeding B | beta | 400 cap, 1.5/s regen | Beta-specialist habitat |
| Water Hole | gamma | 300 cap, 1.0/s regen | Gamma resource, slow regen |
| Hunting Ground | alpha, beta | 600 cap, 3.0/s regen | Multi-key (dangerous), high reward |
| Shelter | (none) | 200 cap, 5.0/s regen | Safe passage, no keys stripped |

### 4.2 Hazard Differentiation

Nodes with more key classes are more hazardous — they strip more layer types per visit. The Hunting Ground holds both alpha and beta secrets, stripping both layer types simultaneously. In the v1.0.1 reference run it is the second-deadliest node (51 deaths; the Water Hole's slow regeneration makes it deadliest at 102) and the most nutritious (25 accretions, the highest).

The Shelter holds no keys. Agents pass through unstripped. It serves as a refugium — a safe resting point in an otherwise hazardous ecology.

### 4.3 Connectivity

```
           [Feeding A]
          /            \
[Shelter] --- [Hunting Ground]
          \            /
           [Feeding B]
          \
           [Water Hole]
```

Hub-and-spoke with the Shelter as the central hub. Agents route through the Shelter between feeding grounds. The Hunting Ground connects directly to both feeding grounds — a shortcut that costs more mass.

---

## 5. Population Dynamics

*v1.0.1: this section is rewritten. The v1.0.0 headings were "Carrying Capacity", "Boom/Bust" and "Speciation". None of the three is observable in a model with no reproduction (§9), and the reviewer was right to say so (Overmier 2026, marketplace section; item 19). The ecological vocabulary is replaced by what the code measures.*

### 5.1 Tail Population (v1.0.0: "Carrying Capacity")

The implementation reports `carrying_capacity_estimate`, which is the mean of the last 30 % of alive-counts in the population trace (`PopulationTracker`). With no births the population can only stay level or decline, so this is a **tail average of a declining cohort**, not an equilibrium the topology sustains. In the v1.0.1 reference runs it is 4 agents (100-agent run) and the 200-agent run ends with 4 alive (2.0 %); across other seeds the estimate ranges 1–5. Whether a regenerating topology would sustain a population is a question the model cannot answer until agents can be born (§9).

### 5.2 Monotonic Decline (v1.0.0: "Boom/Bust")

The 100-agent reference run (v1.0.1, `AMT_SEED=42`):

```
Step  0: 100 alive
Step  4:  82 alive
Step  8:  49 alive
Step 12:  34 alive
Step 16:  17 alive
Step 20:  11 alive
Step 28:   5 alive
Step 36:   3 alive
end:       2 alive  (2 % survival at 40 steps)
```

This is monotonic decline from a starting maximum. There is no boom (the population never grows), no peak (the start is the peak by construction), and no recovery (nothing is born). What the run shows is that consumption outpaces the accretion that regenerating pools and nutrient cycling can fund; calling it "overshoot-and-collapse" imported a cycle the model cannot produce. v1.0.0's curve (76/44/18/11 → extinction at step 38) was one process-dependent draw; v1.0.1's is deterministic.

### 5.3 Niche-Differential Survival (v1.0.0: "Speciation")

Two **predefined** agent profiles are run in the mixed topology:

| Profile | Composition | v1.0.1 survival (of 25) | v1.0.0 |
|---------|------------|-------------|------|
| Alpha-heavy | 5-10 alpha, 1-2 beta, 1-2 gamma | 3 (12.0 %) | 1 (4.0 %) |
| Beta-heavy | 1-2 alpha, 5-10 beta, 1-2 gamma | 1 (4.0 %) | 2 (8.0 %) |

The direction reversed between versions, and across other seeds the alpha-heavy count is 0, 1 or 2 — the reviewer saw 0/0 and then 2/1 on consecutive runs. What is measured is **differential survival of two hand-built profiles** in a topology whose key layout favours one of them; it is not speciation, because no profile can arise, spread, or be selected for. The demo's v1.0.0 text printed that each profile "thrives" in its niche regardless of the numbers; v1.0.1 states the measured result. Differential depletion by key class *is* demonstrated; that is the defensible claim.

---

## 6. Experimental Results

### 6.1 Scale Run (200 Agents)

| Metric | v1.0.1 reference run | v1.0.0 |
|--------|-------|-------|
| Agents | 200 | 200 |
| Total interactions | 1,942 | 2,095 |
| Deaths | 196 | 194 |
| Survival rate | 2.0% | 3.0% |
| **Conservation violations** | **0** | **0** |
| Nutrient deposited | 48,757 B | 48,539 B |
| Nutrient cycled (embodied as payload) | 14,267 B | 37,530 B (counted budget, not accreted mass) |
| Recycling rate | 29.3% | 77.3% |
| New ciphertext minted (payload + overhead) | 16,871 B = 14,267 + 2,604 | not measured |
| Total accretions | 62 | 62 |

*The v1.0.1 run is deterministic (`AMT_SEED=42`; the demo's behaviour RNG was unseeded in v1.0.0, so every run differed). Sampling other seeds gives 2,085–2,145 interactions and 29.2–29.8 % recycling. The v1.0.0 row is one draw from that unseeded distribution.*

### 6.2 Per-Node Analysis

| Node | Interactions | Deaths | Accretions | Death Rate |
|------|-------------|--------|-----------|-----------|
| Feeding A | 316 | 35 | 17 | 11.1% |
| Feeding B | 336 | 8 | 13 | 2.4% |
| Water Hole | 348 | 102 | 7 | 29.3% |
| Hunting Ground | 328 | 51 | 25 | 15.5% |
| Shelter | 614 | 0 | 0 | 0.0% |

The Water Hole is the deadliest node by rate because it has the slowest regeneration. The Hunting Ground has the most accretions (25) because its high nutrient cycling threshold (100) combined with multi-key stripping produces more nutrients per interaction. The Shelter accounts for 614 of 1,942 interactions (31.6 %).

### 6.3 Nutrient Cycling Efficiency (*rewritten in v1.0.1*)

The 29.3 % recycling rate means that of all nutrient bytes captured from signal and loss, 29.3 % were embodied as payload in layers that reached a surviving agent. The rest either remains in nutrient pools (never reached a cycler's threshold, or was generated and not accreted under the three-layer-per-visit cap) or was the 70 % / 90 % of signal / loss that the cycler's ratios discard by design.

v1.0.0 reported 77.3 % here. That figure counted the cycler's whole budget as "cycled" the moment it cycled, while the node accreted at most three of the layers generated (Overmier 2026, item 17). It measured intent, not delivery.

**System-level mass, measured not enforced.** The factory minted 16,871 B of new ciphertext in this run: 14,267 B of payload drawn from nutrients plus 2,604 B of AES-GCM overhead (28 B × 93 layers) that came from nowhere. The per-interaction identity `C_{n+1} + S_{n+1} + L_n = C_n` is untouched by this — it governs consumption, not creation — but there is no equation in v1.0.x tying created mass to lost mass across the whole system. Writing one (factory, accretion, discarded layers, overhead, environmental pools) is the reviewer's recommendation #7 and is v2 work.

---

## 7. Observed Properties (*v1.0.1: "Ecological Properties", rewritten*)

The following are observed in the reference runs. They arise from the conservation identity plus the mechanisms this extension adds — finite regenerating pools, a nutrient cycler with fixed retention ratios, accretion capped at three layers per visit, mass-dependent routing, and two hand-built agent profiles — so none is attributable to the conservation law alone (Overmier 2026: "the observed behavior does not arise from one constraint").

### 7.1 Tail Population
A declining cohort's alive-count settles into a tail (1–5 agents across seeds) whose level depends on regeneration and consumption rates. Without births this is not a carrying capacity (§5.1).

### 7.2 Recycling Loop
Signal and loss flow from agents to nutrient cyclers and back to agents via factory-minted layers. A simplified trophic loop — with the caveat that the minted layers carry overhead the loop did not supply (§6.3).

### 7.3 Differential Depletion by Profile
Alpha-heavy and beta-heavy profiles lose mass at different nodes and survive at different rates. This is not competitive exclusion: no profile can grow, and the direction of the difference flips between runs (§5.3). Gause's principle is not invoked in v1.0.1.

### 7.4 Route Concentration at the Safe Node
The Shelter (no keys) serves as a neutral zone. Agents spend disproportionate time there (614 of 1,942 interactions = 31.6 %) because mass-dependent routing prefers low-hazard nodes. This is a behavioural consequence of the routing rule and the key layout.

---

## 8. Related Work

### Agent-Based Ecological Models
NetLogo, GAMA, and other ABM platforms model population dynamics with explicit rules for birth, death, and resource consumption. AMT's approach is fundamentally different: population dynamics emerge from a conservation law, not from hand-coded rules.

### Token Economics
Blockchain-based token economies (DeFi, NFTs) use scarcity to create market dynamics. AMT provides scarcity through conservation law enforcement — no consensus mechanism, no smart contracts, just physics.

### Digital Ecology
Artificial Life research (Tierra, Avida) simulates evolution in digital environments. AMT's nutrient cycling is analogous to Tierra's reaper queue; unlike Tierra, v1.0.x has no reproduction and therefore no evolution to observe (§9). The per-interaction accounting identity is explicit and asserted; it is not a guarantee over the whole system's mass (§6.3).

---

## 9. Limitations and Future Work

### Population Size
Our current simulation handles hundreds of agents. Scaling to thousands would require parallel processing (as demonstrated in `amt_scale.py`).

### Reproduction
The current model has no explicit reproduction. Nutrient cycling creates mass for existing agents but doesn't create new agents. Adding reproduction (where well-fed agents spawn children with subset layers) is the prerequisite for any claim of carrying capacity, boom/recovery, or speciation (§5); without it the model is a declining cohort by construction.

### Global Mass Equation
The per-interaction identity governs consumption. Creation (factory, accretion, minted overhead) and environmental pools are not tied to it by any equation. Writing and enforcing one is v2 work (§6.3; Overmier 2026, recommendation #7).

### Predation
Agent-to-agent interactions (one agent "consuming" another) are not yet modeled. This would create explicit trophic levels and predator-prey dynamics.

### Dynamic Topology
The current topology is fixed. Real ecosystems have habitat creation and destruction. Adding dynamic nodes (seasonal resources, habitat degradation) would enrich the model.

---

## 10. Conclusion

We have demonstrated that AMT's conservation law, combined with finite environmental resources and nutrient cycling, produces a **declining-cohort agent-based model** with the following measured properties (*v1.0.1 wording; v1.0.0 claimed "a complete population ecology"*):

- **A tail population** of a few agents, determined by regeneration/consumption balance — not a carrying capacity, because nothing is born
- **Monotonic decline** from the starting maximum — not boom/bust, because the population never grows
- **Differential survival** of two predefined profiles by key-class composition — not speciation, because no profile can arise or spread
- **Nutrient cycling** that embodies 29.3 % of captured nutrients as new payload for survivors (v1.0.0's 77.3 % counted budget, not delivery), while minting fresh overhead the system does not account for
- **Implicit competition** — agents never interact with each other, only with shared environments

200 agents, 1,942 interactions, zero conservation violations (v1.0.1 reference run).

No birth rules. No death rules. No population caps. No resource allocation algorithms. No competition protocols. Finite pools, a cycler, an accretion cap and a routing rule — all of which shape the result alongside conservation.

Boom-and-recovery, a stable carrying capacity and speciation are the properties an ecology would need to show; this model cannot show them until it has reproduction (§9). That is the honest boundary of what v1.0.x demonstrates.

---

## Appendix A: Implementation

Reference implementation:

- `amt_marketplace.py`: Extension module (ResourcePool, NutrientCycler, MarketplaceNode, MarketplaceTopology, PopulationTracker, EcologyReport)
- `amt_marketplace_demo.py`: Seven-demo demonstration script

Key design decisions:
- Resource pools are environmental capacity, not agent mass
- Nutrient cycling uses factory as the only legitimate mass source
- Accretion is gated on resource availability (not automatic)
- Conservation check skips accreted entries (accretion is separate from conservation)
