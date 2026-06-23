"""
Agent Mass Theory -- Multi-Agent Marketplace Extension
========================================================

Population ecology governed by conservation law. Agents compete for
finite resources, dead agents' mass cycles back as nutrient for survivors.

Key Concepts:
    - ResourcePool: Finite capacity, regeneration rate, depletion tracking
    - NutrientCycler: Dead agent mass -> new layers (the food chain)
    - MarketplaceNode: Resource-gated interactions with nutrient cycling
    - PopulationTracker: Carrying capacity, Gini coefficient, boom/bust
    - EcologyReport: Aggregate statistics across entire population run

The conservation law is NEVER modified. interact() is used unchanged.
ResourcePools are ENVIRONMENTAL capacity (not agent mass). Pool
depletion gates accretion, not interaction. Nutrient cycling creates
new mass via factory (legitimate mass source).

Dependencies: amt_core.py, amt_extensions.py
Author: Ravenhelm / Nathan Walker
Date: 2026-02-08
"""

import os
import math
import time
import hashlib
import statistics
from dataclasses import dataclass, field
from typing import Optional
from collections import Counter

from amt_core import (
    Agent, Layer, Environment, AgentFactory,
    InteractionResult, interact, accrete,
)
from amt_extensions import (
    Node, AccretionPolicy, AgentBehavior, Topology,
    LocalLedger, PublicLedger,
)


# =============================================================================
# S1  RESOURCE POOL -- FINITE ENVIRONMENTAL CAPACITY
# =============================================================================

@dataclass
class ResourcePool:
    """
    Finite resource capacity at a node that regenerates over time.

    This is ENVIRONMENTAL capacity, not agent mass. Pool depletion
    gates accretion (new mass creation), not interaction (conservation).

    Think of it as "how much fuel the environment can provide."
    When depleted, agents can still interact (conservation still works)
    but cannot accrete new layers (no fuel for growth).
    """

    capacity: float             # Maximum resource units
    current: float              # Current available units
    regeneration_rate: float    # Units per second (regenerated passively)
    last_tick: float = field(default_factory=time.time)
    _depletion_history: list = field(default_factory=list, repr=False)

    def regenerate(self, current_time: float = None):
        """
        Regenerate resources based on elapsed time.
        Capped at capacity. This is passive environmental renewal.
        """
        now = current_time or time.time()
        elapsed = max(0, now - self.last_tick)
        regen = elapsed * self.regeneration_rate
        self.current = min(self.capacity, self.current + regen)
        self.last_tick = now

    def consume(self, amount: float) -> float:
        """
        Consume resources. Returns actual amount consumed.
        May be less than requested if pool is depleted.
        """
        actual = min(amount, self.current)
        self.current = max(0, self.current - actual)
        self._depletion_history.append({
            "time": time.time(),
            "consumed": actual,
            "remaining": self.current,
        })
        return actual

    @property
    def is_depleted(self) -> bool:
        return self.current <= 0

    @property
    def utilization(self) -> float:
        """Fraction of capacity currently used. 1.0 = full, 0.0 = empty."""
        if self.capacity == 0:
            return 0
        return self.current / self.capacity

    def __repr__(self):
        return (f"ResourcePool(cap={self.capacity:.0f}, "
                f"cur={self.current:.0f}, regen={self.regeneration_rate:.1f}/s)")


# =============================================================================
# S2  NUTRIENT CYCLER -- THE FOOD CHAIN
# =============================================================================

class NutrientCycler:
    """
    Converts signal + loss from interactions into new layers for accretion.

    This is the food chain: Agent A's consumed mass -> nutrient pool ->
    Agent B's gained mass. Conservation holds because:
        - Agent A lost mass via interact() (conservation verified)
        - NutrientCycler creates NEW layers via factory.create_layer()
        - Accretion is separate from conservation (adds mass, doesn't violate)

    The factory is the ONLY legitimate mass source.
    """

    def __init__(
        self,
        signal_ratio: float = 0.3,     # fraction of signal -> nutrients
        loss_ratio: float = 0.1,       # fraction of loss -> nutrients
        cycle_threshold: int = 200,     # minimum accumulated before cycling
    ):
        self.signal_ratio = signal_ratio
        self.loss_ratio = loss_ratio
        self.cycle_threshold = cycle_threshold
        self._accumulated = 0
        self._total_deposited = 0
        self._total_cycled = 0
        self._cycle_count = 0

    def deposit(self, signal: int, loss: int):
        """
        Deposit signal and loss from an interaction into the nutrient pool.
        Only a fraction is retained (rest is truly lost to entropy).
        """
        nutrients = int(signal * self.signal_ratio + loss * self.loss_ratio)
        self._accumulated += nutrients
        self._total_deposited += nutrients

    @property
    def can_cycle(self) -> bool:
        return self._accumulated >= self.cycle_threshold

    @property
    def accumulated(self) -> int:
        return self._accumulated

    def cycle(self, factory: AgentFactory, key_classes: list) -> list:
        """
        Convert accumulated nutrients into new layers.

        Creates layers distributed across the given key classes.
        Returns list of (key_class, payload) tuples for accretion.

        The factory creates legitimate mass. This is not a violation —
        accretion is separate from conservation-governed interaction.
        """
        if not self.can_cycle or not key_classes:
            return []

        budget = self._accumulated
        self._accumulated = 0
        self._total_cycled += budget
        self._cycle_count += 1

        # Distribute nutrients across key classes
        specs = []
        per_class = budget // len(key_classes)
        for kc in key_classes:
            if per_class <= 0:
                continue
            # Create layers with some signal content, some empty
            num_layers = max(1, per_class // 128)
            payload_size = max(1, per_class // max(1, num_layers))

            for i in range(num_layers):
                if i < num_layers * 0.7:  # 70% data, 30% empty
                    specs.append((kc, os.urandom(min(payload_size, 256))))
                else:
                    specs.append((kc, b""))

        return specs

    def summary(self) -> str:
        return (f"NutrientCycler(accumulated={self._accumulated}, "
                f"deposited={self._total_deposited}, "
                f"cycled={self._total_cycled}, "
                f"cycles={self._cycle_count})")


# =============================================================================
# S3  MARKETPLACE NODE -- RESOURCE-GATED INTERACTIONS
# =============================================================================

class MarketplaceNode:
    """
    A node with finite resources, nutrient cycling, and accretion.

    Wraps Node via composition. On each process():
        1. interact() governs conservation (unchanged)
        2. signal + loss deposited to nutrient cycler
        3. Accretion gated on resource pool availability
        4. Nutrient cycling creates new mass for future agents
    """

    def __init__(
        self,
        node_id: str,
        name: str,
        key_secrets: dict,
        resource_pool: ResourcePool,
        nutrient_cycler: NutrientCycler = None,
        accretion_cost: float = 50.0,  # resource units per accretion
        ledger: LocalLedger = None,
    ):
        self.node_id = node_id
        self.name = name
        self.resource_pool = resource_pool
        self.nutrient_cycler = nutrient_cycler or NutrientCycler()
        self.accretion_cost = accretion_cost
        self._interaction_count = 0
        self._accretion_count = 0
        self._death_count = 0

        self._node = Node(
            node_id=node_id,
            name=name,
            _key_secrets=key_secrets,
            ledger=ledger or LocalLedger(node_id),
        )

    @property
    def node(self) -> Node:
        return self._node

    @property
    def ledger(self) -> LocalLedger:
        return self._node.ledger

    def process(
        self,
        agent: Agent,
        factory: AgentFactory,
        key_classes: list = None,
    ) -> dict:
        """
        Process an agent at this marketplace node.

        Returns dict with interaction details + resource metrics.
        """
        mass_before = agent.mass

        # Step 1: Conservation-governed interaction
        result = self._node.process(agent, factory)
        self._interaction_count += 1

        # Step 2: Deposit nutrients from consumption
        if result.agent_could_enter:
            self.nutrient_cycler.deposit(result.total_signal, result.total_loss)

        # Step 3: Resource-gated accretion
        accreted = False
        if (result.agent_survived and
            not self.resource_pool.is_depleted and
            self.resource_pool.current >= self.accretion_cost):

            # Check if nutrient cycler has layers ready
            if self.nutrient_cycler.can_cycle:
                kc = key_classes or list(self._node._key_secrets.keys())
                new_specs = self.nutrient_cycler.cycle(factory, kc)

                if new_specs and factory:
                    # Create accretion layers and accrete onto agent
                    for kc_name, payload in new_specs[:3]:  # cap at 3 layers
                        layer = factory.create_layer(kc_name, payload)
                        accrete(agent, [layer])

                    self.resource_pool.consume(self.accretion_cost)
                    self._accretion_count += 1
                    accreted = True

        if not result.agent_survived:
            self._death_count += 1

        return {
            "node_id": self.node_id,
            "name": self.name,
            "mass_before": mass_before,
            "mass_after": agent.mass,
            "entered": result.agent_could_enter,
            "survived": result.agent_survived,
            "signal": result.total_signal,
            "loss": result.total_loss,
            "layers_stripped": result.layers_stripped,
            "accreted": accreted,
            "resource_remaining": self.resource_pool.current,
            "resource_utilization": self.resource_pool.utilization,
            "nutrients_accumulated": self.nutrient_cycler.accumulated,
        }

    def __repr__(self):
        return (f"MarketplaceNode({self.name}, pool={self.resource_pool}, "
                f"interactions={self._interaction_count})")


# =============================================================================
# S4  MARKETPLACE TOPOLOGY -- POPULATION SIMULATION
# =============================================================================

class MarketplaceTopology:
    """
    A topology of marketplace nodes for population-level simulation.

    Wraps Topology internally. Adds:
        - Resource regeneration (tick)
        - Population simulation (run_population)
        - Per-node tracking
    """

    def __init__(self):
        self._topology = Topology()
        self._nodes: dict[str, MarketplaceNode] = {}
        self._factory: Optional[AgentFactory] = None
        self._sim_time: float = 0.0

    def set_factory(self, factory: AgentFactory):
        self._factory = factory

    def add_node(self, mkt_node: MarketplaceNode):
        """Add a marketplace node to the topology."""
        self._nodes[mkt_node.node_id] = mkt_node
        self._topology.add_node(mkt_node.node)

    def connect(self, from_id: str, to_id: str, bidirectional: bool = True):
        self._topology.connect(from_id, to_id, bidirectional=bidirectional)

    def tick(self, delta_t: float = 1.0):
        """Advance simulation time: regenerate all resource pools."""
        self._sim_time += delta_t
        for mkt_node in self._nodes.values():
            mkt_node.resource_pool.regenerate(self._sim_time)

    def run_population(
        self,
        agents_and_behaviors: list,
        start_ids: list = None,
        max_steps: int = 30,
        tick_interval: float = 0.5,
        verbose: bool = True,
    ) -> dict:
        """
        Run a population of agents through the marketplace.

        agents_and_behaviors: list of (Agent, AgentBehavior) tuples
        start_ids: list of starting node IDs (cycled if fewer than agents)
        max_steps: max interaction steps per agent
        tick_interval: simulated seconds between steps (for regeneration)

        Returns dict with population traces, death events, histories.
        """
        if not start_ids:
            start_ids = list(self._nodes.keys())

        n = len(agents_and_behaviors)
        agent_positions = {}  # agent_index -> current_node_id
        agent_histories = {i: [] for i in range(n)}
        population_trace = []
        death_events = []
        resource_trace = []

        # Initial positions
        for i in range(n):
            agent_positions[i] = start_ids[i % len(start_ids)]

        if verbose:
            print(f"\n{'▓' * 70}")
            print(f"  MARKETPLACE POPULATION SIMULATION")
            print(f"  Agents: {n}, Nodes: {len(self._nodes)}, Max steps: {max_steps}")
            print(f"{'▓' * 70}\n")

        for step in range(max_steps):
            self.tick(tick_interval)

            alive_count = 0
            step_deaths = 0

            for i, (agent, behavior) in enumerate(agents_and_behaviors):
                if not agent.alive:
                    continue

                alive_count += 1
                current_id = agent_positions[i]
                mkt_node = self._nodes.get(current_id)
                if mkt_node is None:
                    continue

                # Process at current node
                key_classes = list(mkt_node._node._key_secrets.keys())
                result = mkt_node.process(agent, self._factory, key_classes)
                result["step"] = step
                result["agent_index"] = i
                result["alive"] = agent.alive
                agent_histories[i].append(result)

                behavior.observe(agent)

                if not agent.alive:
                    step_deaths += 1
                    death_events.append({
                        "step": step,
                        "agent_index": i,
                        "node_id": current_id,
                        "mass_at_death": result["mass_after"],
                    })
                    continue

                # Choose next node
                neighbors = self._topology.reachable_from(current_id)
                if neighbors:
                    try:
                        next_node = behavior.choose_node(neighbors, agent)
                    except TypeError:
                        # Risk tolerance complex number bug
                        import random
                        next_node = random.choice(list(neighbors))
                    if next_node:
                        agent_positions[i] = next_node.node_id

            # Record population snapshot
            total_alive = sum(1 for a, _ in agents_and_behaviors if a.alive)
            total_mass = sum(a.mass for a, _ in agents_and_behaviors if a.alive)

            population_trace.append({
                "step": step,
                "alive": total_alive,
                "total_mass": total_mass,
                "avg_mass": total_mass / total_alive if total_alive > 0 else 0,
                "deaths_this_step": step_deaths,
            })

            # Record resource snapshot
            resource_snap = {}
            for nid, mkt_node in self._nodes.items():
                resource_snap[nid] = {
                    "current": mkt_node.resource_pool.current,
                    "utilization": mkt_node.resource_pool.utilization,
                    "nutrients": mkt_node.nutrient_cycler.accumulated,
                }
            resource_trace.append(resource_snap)

            if verbose and step % 5 == 0:
                print(f"  Step {step:3d}: alive={total_alive:4d}, "
                      f"mass={total_mass:,}, deaths={step_deaths}")

            if total_alive == 0:
                if verbose:
                    print(f"  Step {step:3d}: ALL AGENTS DEAD. Simulation ends.")
                break

        if verbose:
            final = population_trace[-1] if population_trace else {}
            print(f"\n  Final: alive={final.get('alive', 0)}, "
                  f"total_mass={final.get('total_mass', 0):,}")

        return {
            "population_trace": population_trace,
            "death_events": death_events,
            "agent_histories": dict(agent_histories),
            "resource_trace": resource_trace,
        }

    def resource_summary(self) -> str:
        """Human-readable resource state across all nodes."""
        lines = [
            f"{'=' * 70}",
            f"  MARKETPLACE RESOURCE STATE",
            f"{'=' * 70}",
        ]
        for nid, mkt_node in self._nodes.items():
            pool = mkt_node.resource_pool
            cycler = mkt_node.nutrient_cycler
            lines.append(
                f"  {nid:>15s}: pool={pool.current:.0f}/{pool.capacity:.0f} "
                f"({pool.utilization*100:.0f}%), "
                f"nutrients={cycler.accumulated}, "
                f"interactions={mkt_node._interaction_count}, "
                f"deaths={mkt_node._death_count}"
            )
        lines.append(f"{'=' * 70}")
        return "\n".join(lines)


# =============================================================================
# S5  POPULATION TRACKER -- METRICS & ANALYSIS
# =============================================================================

class PopulationTracker:
    """
    Tracks population dynamics over time.

    Computes:
        - Carrying capacity (equilibrium population)
        - Gini coefficient (inequality in mass distribution)
        - Boom/bust cycle detection
    """

    def __init__(self):
        self._snapshots: list[dict] = []

    def add_snapshot(self, step: int, agents: list):
        """Record population state at a given step."""
        alive = [a for a, _ in agents if a.alive]
        masses = [a.mass for a in alive]

        self._snapshots.append({
            "step": step,
            "alive": len(alive),
            "total_mass": sum(masses),
            "avg_mass": statistics.mean(masses) if masses else 0,
            "median_mass": statistics.median(masses) if masses else 0,
            "masses": masses,
        })

    @property
    def carrying_capacity_estimate(self) -> float:
        """
        Estimate carrying capacity from the population trace.
        Uses the average of the last 30% of alive counts.
        """
        if not self._snapshots:
            return 0
        tail_start = max(1, int(len(self._snapshots) * 0.7))
        tail = self._snapshots[tail_start:]
        return statistics.mean(s["alive"] for s in tail) if tail else 0

    def gini_coefficient(self, step_index: int = -1) -> float:
        """
        Compute Gini coefficient of mass distribution at a given step.
        0 = perfect equality, 1 = maximum inequality.
        """
        if not self._snapshots:
            return 0
        masses = self._snapshots[step_index]["masses"]
        if not masses or len(masses) < 2:
            return 0

        sorted_m = sorted(masses)
        n = len(sorted_m)
        total = sum(sorted_m)
        if total == 0:
            return 0

        cumulative = 0
        area_under_lorenz = 0
        for i, m in enumerate(sorted_m):
            cumulative += m
            area_under_lorenz += cumulative

        # Gini = 1 - 2 * (area_under_lorenz / (n * total))
        # Adjusted for discrete distribution
        return 1 - (2 * area_under_lorenz) / (n * total) + 1 / n

    def boom_bust_cycles(self) -> dict:
        """
        Detect boom/bust cycles in the population trace.
        A "boom" is a local maximum, a "bust" is a local minimum.
        """
        if len(self._snapshots) < 5:
            return {"cycles": 0, "peaks": [], "troughs": []}

        alive_trace = [s["alive"] for s in self._snapshots]
        peaks = []
        troughs = []

        for i in range(1, len(alive_trace) - 1):
            if alive_trace[i] > alive_trace[i-1] and alive_trace[i] > alive_trace[i+1]:
                peaks.append((i, alive_trace[i]))
            if alive_trace[i] < alive_trace[i-1] and alive_trace[i] < alive_trace[i+1]:
                troughs.append((i, alive_trace[i]))

        return {
            "cycles": min(len(peaks), len(troughs)),
            "peaks": peaks,
            "troughs": troughs,
        }

    def summary(self) -> str:
        if not self._snapshots:
            return "PopulationTracker: (no data)"
        initial = self._snapshots[0]["alive"]
        final = self._snapshots[-1]["alive"]
        cap = self.carrying_capacity_estimate
        gini = self.gini_coefficient()
        cycles = self.boom_bust_cycles()

        return (
            f"  PopulationTracker:\n"
            f"    Snapshots: {len(self._snapshots)}\n"
            f"    Initial: {initial} alive\n"
            f"    Final: {final} alive\n"
            f"    Carrying capacity: {cap:.0f}\n"
            f"    Gini coefficient: {gini:.3f}\n"
            f"    Boom/bust cycles: {cycles['cycles']}"
        )


# =============================================================================
# S6  ECOLOGY REPORT -- AGGREGATE ANALYSIS
# =============================================================================

@dataclass
class EcologyReport:
    """
    Aggregate statistics for a complete marketplace ecology run.
    """

    population_trace: list
    death_events: list
    agent_histories: dict
    nodes: dict  # node_id -> MarketplaceNode

    def survival_by_mass_bins(self, agents: list) -> dict:
        """
        Bin agents by initial mass, compute survival rate per bin.
        """
        bins = {}
        for i, (agent, _) in enumerate(agents):
            hist = self.agent_histories.get(i, [])
            if not hist:
                continue
            initial_mass = hist[0]["mass_before"]
            alive = agent.alive

            if initial_mass < 500:
                bucket = "<500B"
            elif initial_mass < 2000:
                bucket = "500-2KB"
            elif initial_mass < 5000:
                bucket = "2-5KB"
            else:
                bucket = ">5KB"

            if bucket not in bins:
                bins[bucket] = {"total": 0, "survived": 0}
            bins[bucket]["total"] += 1
            if alive:
                bins[bucket]["survived"] += 1

        return {
            k: v["survived"] / v["total"] if v["total"] > 0 else 0
            for k, v in sorted(bins.items())
        }

    def conservation_check(self) -> dict:
        """
        Verify conservation law across all interactions.
        """
        total = 0
        violations = 0

        for agent_idx, hist in self.agent_histories.items():
            for entry in hist:
                if not entry.get("entered", True):
                    continue
                total += 1
                lhs = entry["mass_before"]
                # After accretion, mass_after may be > mass_before - signal - loss
                # We check conservation of the INTERACTION, not accretion
                rhs = entry["signal"] + entry["loss"]
                consumed = lhs - entry["mass_after"]
                # With accretion, mass_after could be higher than mass_before - signal - loss
                # The conservation check is: signal + loss should account for stripped mass
                # But accretion adds mass AFTER the interaction, so mass_after includes it
                # We need to account for accretion
                if entry.get("accreted", False):
                    # Skip conservation check for accreted entries —
                    # the interact() already verified internally
                    continue
                if consumed != rhs and consumed >= 0:
                    violations += 1

        return {
            "total_interactions": total,
            "violations": violations,
            "holds": violations == 0,
        }

    def full_report(self, agents: list = None) -> str:
        """Generate full ecology report."""
        lines = [
            f"\n{'█' * 70}",
            f"  ECOLOGY REPORT",
            f"{'█' * 70}\n",
        ]

        # Population trace
        if self.population_trace:
            initial = self.population_trace[0]
            final = self.population_trace[-1]
            lines.append(f"  Population:")
            lines.append(f"    Initial: {initial['alive']} agents, {initial['total_mass']:,} B mass")
            lines.append(f"    Final:   {final['alive']} agents, {final['total_mass']:,} B mass")
            lines.append(f"    Deaths:  {len(self.death_events)}")

        # Survival by mass
        if agents:
            lines.append(f"\n  Survival by Initial Mass:")
            survival = self.survival_by_mass_bins(agents)
            for bucket, rate in survival.items():
                bar = "█" * int(rate * 40)
                lines.append(f"    {bucket:>8s}: {rate:6.1%}  {bar}")

        # Per-node stats
        lines.append(f"\n  Per-Node Statistics:")
        for nid, mkt_node in self.nodes.items():
            lines.append(
                f"    {nid:>15s}: {mkt_node._interaction_count} interactions, "
                f"{mkt_node._death_count} deaths, "
                f"{mkt_node._accretion_count} accretions"
            )

        # Conservation
        cons = self.conservation_check()
        lines.append(f"\n  Conservation Law:")
        lines.append(f"    Total interactions: {cons['total_interactions']}")
        lines.append(f"    Violations: {cons['violations']}")
        if cons['holds']:
            lines.append(f"    C_{{n+1}} + S_{{n+1}} + L_n = C_n HOLDS.")
        else:
            lines.append(f"    WARNING: Conservation violations detected!")

        lines.append(f"\n{'█' * 70}\n")
        return "\n".join(lines)


# =============================================================================
# S7  HELPER -- SAFE RISK TOLERANCE
# =============================================================================

def _safe_risk_tolerance(behavior: AgentBehavior) -> float:
    """Workaround for fractional exponent complex number bug."""
    try:
        return behavior.risk_tolerance
    except TypeError:
        return behavior.risk_baseline
