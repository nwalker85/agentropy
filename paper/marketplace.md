# Multi-Agent Marketplace: Population Ecology from Conservation Law

**Agent Mass Theory Applied to Resource Competition and Nutrient Cycling**

*Nate Walker — Ravenhelm*
*February 2026*

---

## Abstract

When multiple agents compete for finite environmental resources under AMT's conservation law, population ecology emerges. We present a marketplace extension where nodes have finite resource pools that regenerate over time, and a nutrient cycling mechanism converts dead agents' consumed mass into new layers for survivors. The conservation law `C_{n+1} + S_{n+1} + L_n = C_n` governs every interaction — it is never modified. Resource pools are environmental capacity (not agent mass) that gate accretion. Nutrient cycling creates new mass through the factory (the only legitimate mass source). We demonstrate with 200 agents competing across 5 marketplace nodes: carrying capacity stabilizes at 4-6 agents, nutrient cycling achieves 77.3% recycling rate, and niche differentiation emerges from key class composition alone. Zero conservation violations across 2,095 interactions. The conservation law is the ecosystem.

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

No agent "knows" about other agents. Each agent simply interacts with nodes, losing mass per the conservation law. The population dynamics — carrying capacity, boom/bust, speciation — emerge from this micro-level physics.

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

This models natural resource renewal — a grazing field regrows, a power supply recharges, a compute cluster becomes available again. The regeneration rate determines the environment's carrying capacity.

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

The factory is the ONLY legitimate mass source. This is critical: conservation holds because:
1. Agent A loses mass via `interact()` (conservation verified ✓)
2. NutrientCycler captures a fraction of that mass
3. Factory creates new layers from the captured budget
4. Agent B accretes new layers (separate from conservation)

No mass is created from nothing. Dead agents' mass flows to living agents through the factory.

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

Nodes with more key classes are more hazardous — they strip more layer types per visit. The Hunting Ground holds both alpha and beta secrets, stripping both layer types simultaneously. This makes it the deadliest node (54 deaths in our scale run) but also the most nutritious (highest nutrient cycling).

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

### 5.1 Carrying Capacity

Carrying capacity is the equilibrium population that a topology can sustain. It emerges from:
- Resource regeneration rate (how fast the environment recovers)
- Agent mass consumption rate (how fast agents deplete resources)
- Nutrient cycling efficiency (how much dead mass recycles)

In our scale run (200 agents, 5 nodes), carrying capacity stabilizes at approximately 4-6 agents — about 2-3% of the initial population. This is not programmed. It emerges from conservation law + finite resources.

### 5.2 Boom/Bust

When population exceeds carrying capacity:
1. **Boom**: Many agents, resources abundant, accretion supports growth
2. **Peak**: Resources deplete faster than regeneration
3. **Bust**: No accretion fuel, agents die in waves
4. **Recovery**: Resources regenerate, survivors stabilize

Our 100-agent run shows clear exponential decay:

```
Step  0: 100 alive
Step  5:  76 alive  (24% die-off)
Step 10:  44 alive  (56% total)
Step 15:  18 alive  (82% total)
Step 20:  11 alive  (89% total)
Step 38:   0 alive  (complete extinction)
```

The population crashes because nutrient cycling cannot keep pace with consumption. The ecosystem is overshoot-and-collapse.

### 5.3 Speciation

Agents with different key class compositions occupy different ecological niches:

| Species | Composition | Best Habitat | Survival Rate |
|---------|------------|-------------|---------------|
| Alpha-heavy | 5-10 alpha, 1-2 beta, 1-2 gamma | Feeding A | 4.0% |
| Beta-heavy | 1-2 alpha, 5-10 beta, 1-2 gamma | Feeding B | 8.0% |

Beta-heavy agents survive longer because:
1. Feeding B has fewer deaths (10 vs 44 at Feeding A)
2. Beta layers are not stripped at the Shelter
3. The Hunting Ground strips both alpha and beta — alpha-heavy agents lose more there

This is niche differentiation. Different mass profiles lead to different survival outcomes in different habitats. No agent "chooses" a niche — the conservation law routes them by mass-dependent behavioral choices.

---

## 6. Experimental Results

### 6.1 Scale Run (200 Agents)

| Metric | Value |
|--------|-------|
| Agents | 200 |
| Total interactions | 2,095 |
| Deaths | 194 |
| Survival rate | 3.0% |
| **Conservation violations** | **0** |
| Nutrient deposited | 48,539 B |
| Nutrient cycled | 37,530 B |
| Recycling rate | 77.3% |
| Total accretions | 62 |
| Processing speed | 3,389 agents/sec |

### 6.2 Per-Node Analysis

| Node | Interactions | Deaths | Accretions | Death Rate |
|------|-------------|--------|-----------|-----------|
| Feeding A | 355 | 44 | 17 | 12.4% |
| Feeding B | 366 | 10 | 13 | 2.7% |
| Water Hole | 388 | 86 | 7 | 22.2% |
| Hunting Ground | 325 | 54 | 25 | 16.6% |
| Shelter | 661 | 0 | 0 | 0.0% |

The Water Hole is the deadliest node by rate (22.2%) because it has the slowest regeneration. The Hunting Ground has the most accretions (25) because its high nutrient cycling threshold (100) combined with multi-key stripping produces more nutrients per interaction.

### 6.3 Nutrient Cycling Efficiency

The 77.3% recycling rate means that of all mass deposited as nutrients, 77.3% was successfully cycled into new layers for surviving agents. The remaining 22.7% is "stuck" in nutrient pools that haven't reached their cycling threshold — unrealized potential, waiting for more deposits.

---

## 7. Ecological Properties

All of the following are emergent from conservation law + finite resources. None are programmed:

### 7.1 Carrying Capacity
The population stabilizes at a level determined by regeneration rate / consumption rate. Higher regeneration → higher carrying capacity.

### 7.2 Trophic Levels
Signal flows from agents (consumers) to environments (decomposers) and back to agents (producers via accretion). This is a simplified trophic web.

### 7.3 Competitive Exclusion
In our speciation demo, alpha-heavy and beta-heavy agents compete for different resources. Given enough time, one type dominates each niche — this is Gause's competitive exclusion principle, emergent from mass physics.

### 7.4 Resource Partitioning
The Shelter (no keys) serves as a neutral zone. Agents spend disproportionate time there (661 of 2,095 interactions = 31.6%) because it's safe. This is behavioral resource partitioning.

---

## 8. Related Work

### Agent-Based Ecological Models
NetLogo, GAMA, and other ABM platforms model population dynamics with explicit rules for birth, death, and resource consumption. AMT's approach is fundamentally different: population dynamics emerge from a conservation law, not from hand-coded rules.

### Token Economics
Blockchain-based token economies (DeFi, NFTs) use scarcity to create market dynamics. AMT provides scarcity through conservation law enforcement — no consensus mechanism, no smart contracts, just physics.

### Digital Ecology
Artificial Life research (Tierra, Avida) simulates evolution in digital environments. AMT's nutrient cycling is analogous to Tierra's reaper queue, but AMT's conservation law provides formal guarantees that Tierra's heuristics cannot.

---

## 9. Limitations and Future Work

### Population Size
Our current simulation handles hundreds of agents. Scaling to thousands would require parallel processing (as demonstrated in `amt_scale.py`).

### Reproduction
The current model has no explicit reproduction. Nutrient cycling creates mass for existing agents but doesn't create new agents. Adding reproduction (where well-fed agents spawn children with subset layers) would complete the ecological model.

### Predation
Agent-to-agent interactions (one agent "consuming" another) are not yet modeled. This would create explicit trophic levels and predator-prey dynamics.

### Dynamic Topology
The current topology is fixed. Real ecosystems have habitat creation and destruction. Adding dynamic nodes (seasonal resources, habitat degradation) would enrich the model.

---

## 10. Conclusion

We have demonstrated that AMT's conservation law, combined with finite environmental resources and nutrient cycling, produces a complete population ecology:

- **Carrying capacity** emerges from regeneration/consumption balance
- **Boom/bust dynamics** emerge from overshoot of carrying capacity
- **Niche differentiation** emerges from key class composition
- **Nutrient cycling** recycles 77.3% of dead agent mass to survivors
- **Competition** is implicit — agents never interact with each other, only with shared environments

200 agents, 2,095 interactions, zero conservation violations.

No birth rules. No death rules. No population caps. No resource allocation algorithms. No competition protocols.

Just conservation.

The math is the ecosystem.

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
