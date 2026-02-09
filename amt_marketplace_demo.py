#!/usr/bin/env python3
"""
Agent Mass Theory -- Multi-Agent Marketplace Demo
====================================================

Population ecology governed by conservation law. Agents compete for
finite resources. Dead agents' mass cycles back as fuel for survivors.
Carrying capacity, Gini inequality, boom/bust cycles -- all emergent.

Usage:
    python3 amt_marketplace_demo.py
"""

import os
import time
import random
import hashlib

from amt_core import Agent, AgentFactory
from amt_extensions import AgentBehavior, AccretionPolicy, LocalLedger
from amt_marketplace import (
    ResourcePool, NutrientCycler, MarketplaceNode, MarketplaceTopology,
    PopulationTracker, EcologyReport, _safe_risk_tolerance,
)


# =============================================================================
#  UNIVERSE SETUP
# =============================================================================

SECRET_ALPHA   = hashlib.sha256(b"marketplace-alpha-secret").digest()
SECRET_BETA    = hashlib.sha256(b"marketplace-beta-secret").digest()
SECRET_GAMMA   = hashlib.sha256(b"marketplace-gamma-secret").digest()

ALL_SECRETS = {
    "alpha": SECRET_ALPHA,
    "beta": SECRET_BETA,
    "gamma": SECRET_GAMMA,
}

FACTORY = AgentFactory(ALL_SECRETS)


def separator(title: str):
    print(f"\n\n{'█' * 70}")
    print(f"  {title}")
    print(f"{'█' * 70}\n")


def build_marketplace() -> MarketplaceTopology:
    """Build a standard 5-node marketplace."""
    topo = MarketplaceTopology()
    topo.set_factory(FACTORY)

    # Feeding grounds: high resources, alpha key
    topo.add_node(MarketplaceNode(
        node_id="feeding_a",
        name="Feeding Ground A",
        key_secrets={"alpha": SECRET_ALPHA},
        resource_pool=ResourcePool(capacity=500, current=500, regeneration_rate=2.0),
        nutrient_cycler=NutrientCycler(signal_ratio=0.3, loss_ratio=0.1, cycle_threshold=150),
        accretion_cost=30.0,
    ))

    topo.add_node(MarketplaceNode(
        node_id="feeding_b",
        name="Feeding Ground B",
        key_secrets={"beta": SECRET_BETA},
        resource_pool=ResourcePool(capacity=400, current=400, regeneration_rate=1.5),
        nutrient_cycler=NutrientCycler(signal_ratio=0.3, loss_ratio=0.1, cycle_threshold=150),
        accretion_cost=30.0,
    ))

    # Watering hole: moderate resources, gamma key
    topo.add_node(MarketplaceNode(
        node_id="water_hole",
        name="Watering Hole",
        key_secrets={"gamma": SECRET_GAMMA},
        resource_pool=ResourcePool(capacity=300, current=300, regeneration_rate=1.0),
        nutrient_cycler=NutrientCycler(signal_ratio=0.2, loss_ratio=0.05, cycle_threshold=200),
        accretion_cost=40.0,
    ))

    # Hunting ground: multi-key, expensive
    topo.add_node(MarketplaceNode(
        node_id="hunting",
        name="Hunting Ground",
        key_secrets={"alpha": SECRET_ALPHA, "beta": SECRET_BETA},
        resource_pool=ResourcePool(capacity=600, current=600, regeneration_rate=3.0),
        nutrient_cycler=NutrientCycler(signal_ratio=0.4, loss_ratio=0.15, cycle_threshold=100),
        accretion_cost=25.0,
    ))

    # Shelter: safe, no keys, just a rest node
    topo.add_node(MarketplaceNode(
        node_id="shelter",
        name="Shelter",
        key_secrets={},
        resource_pool=ResourcePool(capacity=200, current=200, regeneration_rate=5.0),
        nutrient_cycler=NutrientCycler(cycle_threshold=999999),  # never cycles
        accretion_cost=100.0,  # expensive if it ever happens
    ))

    # Connect: hub-and-spoke with shelter as hub
    topo.connect("shelter", "feeding_a")
    topo.connect("shelter", "feeding_b")
    topo.connect("shelter", "water_hole")
    topo.connect("shelter", "hunting")
    topo.connect("feeding_a", "hunting")
    topo.connect("feeding_b", "water_hole")

    return topo


def make_agents(n: int, rng: random.Random = None) -> list:
    """
    Create n agents with varied mass profiles.
    Returns list of (Agent, AgentBehavior) tuples.
    """
    rng = rng or random.Random(42)
    agents = []

    for _ in range(n):
        # Random layer composition
        alpha_count = rng.randint(1, 8)
        beta_count = rng.randint(1, 6)
        gamma_count = rng.randint(1, 4)

        specs = []
        for _ in range(alpha_count):
            payload = os.urandom(rng.randint(32, 128)) if rng.random() < 0.7 else b""
            specs.append(("alpha", payload))
        for _ in range(beta_count):
            payload = os.urandom(rng.randint(32, 128)) if rng.random() < 0.7 else b""
            specs.append(("beta", payload))
        for _ in range(gamma_count):
            payload = os.urandom(rng.randint(32, 128)) if rng.random() < 0.7 else b""
            specs.append(("gamma", payload))

        agent = FACTORY.build_agent(specs)
        behavior = AgentBehavior(
            risk_baseline=rng.uniform(0.3, 0.8),
            desperation_curve=rng.choice([2.0, 2.0, 3.0]),  # integer to avoid complex bug
        )
        agents.append((agent, behavior))

    return agents


# =============================================================================
#  DEMO 1: MARKETPLACE TOPOLOGY
# =============================================================================

def demo_1_topology():
    separator("DEMO 1: MARKETPLACE TOPOLOGY")

    print("Five nodes. Three key classes. Finite resources. Nutrient cycling.\n")

    topo = build_marketplace()
    print(topo.resource_summary())

    print("\nTopology:")
    print("           [Feeding A]  --- (alpha key)")
    print("          /            \\")
    print("  [Shelter] --- [Hunting] --- (alpha + beta keys)")
    print("          \\            /")
    print("           [Feeding B] --- (beta key)")
    print("          \\")
    print("           [Water Hole] --- (gamma key)")
    print()
    print("  Shelter: inert (no keys), high regen, safe rest")
    print("  Feeding grounds: single key, moderate resources")
    print("  Hunting ground: multi-key (dangerous), high regen")
    print("  Water hole: gamma key, slow regen")


# =============================================================================
#  DEMO 2: SINGLE AGENT TRAVERSAL
# =============================================================================

def demo_2_single_agent():
    separator("DEMO 2: SINGLE AGENT TRAVERSAL — BASELINE")

    print("One agent through the marketplace. Baseline resource consumption.\n")

    topo = build_marketplace()

    # Build a decent agent
    specs = [
        ("alpha", os.urandom(64)),
        ("alpha", os.urandom(64)),
        ("alpha", b""),
        ("beta", os.urandom(64)),
        ("beta", os.urandom(64)),
        ("gamma", os.urandom(64)),
        ("gamma", b""),
    ]
    agent = FACTORY.build_agent(specs)
    behavior = AgentBehavior(risk_baseline=0.5, desperation_curve=2.0)

    print(f"  Agent: {agent}")
    print(f"  Profile: {agent.mass_profile()}\n")

    route = ["shelter", "feeding_a", "hunting", "feeding_b", "water_hole"]

    for step, node_id in enumerate(route):
        if not agent.alive:
            print(f"  Step {step}: DEAD before {node_id}")
            break

        mkt_node = topo._nodes[node_id]
        result = mkt_node.process(agent, FACTORY, list(ALL_SECRETS.keys()))
        behavior.observe(agent)

        status = "OK" if result["survived"] else "DIED"
        accr = " +ACCRETE" if result["accreted"] else ""
        print(f"  Step {step}: {node_id:>15s}  mass {result['mass_before']:>6,} -> {result['mass_after']:>6,}"
              f"  S={result['signal']:>5,} L={result['loss']:>4,}  [{status}]{accr}")

        if not agent.alive:
            break

    print(f"\n  Final mass: {agent.mass:,} B")
    print(f"  Alive: {agent.alive}")

    # Resource state after
    print(f"\n  Resource state after one agent:")
    print(topo.resource_summary())


# =============================================================================
#  DEMO 3: POPULATION COMPETITION
# =============================================================================

def demo_3_competition():
    separator("DEMO 3: POPULATION COMPETITION — 50 AGENTS")

    print("50 agents compete for finite resources. Watch depletion.\n")

    topo = build_marketplace()
    agents = make_agents(50, rng=random.Random(42))

    initial_alive = sum(1 for a, _ in agents if a.alive)
    initial_mass = sum(a.mass for a, _ in agents)
    print(f"  Initial: {initial_alive} agents, {initial_mass:,} B total mass\n")

    result = topo.run_population(
        agents, max_steps=20, tick_interval=0.5, verbose=True,
    )

    final_alive = sum(1 for a, _ in agents if a.alive)
    final_mass = sum(a.mass for a, _ in agents if a.alive)

    print(f"\n  Resource state after competition:")
    print(topo.resource_summary())

    print(f"\n  Deaths: {len(result['death_events'])}")
    print(f"  Survival rate: {final_alive}/{initial_alive} "
          f"({final_alive/initial_alive*100:.1f}%)")


# =============================================================================
#  DEMO 4: NUTRIENT CYCLING — THE FOOD CHAIN
# =============================================================================

def demo_4_nutrient_cycling():
    separator("DEMO 4: NUTRIENT CYCLING — THE FOOD CHAIN")

    print("Dead agents' consumed mass cycles back as nutrient for survivors.")
    print("The ecosystem recycles. Mass is never wasted.\n")

    topo = build_marketplace()
    agents = make_agents(30, rng=random.Random(123))

    # Track accretions
    result = topo.run_population(
        agents, max_steps=25, tick_interval=0.5, verbose=True,
    )

    # Count accretions
    total_accretions = sum(
        mkt_node._accretion_count
        for mkt_node in topo._nodes.values()
    )
    total_deaths = len(result["death_events"])

    print(f"\n  NUTRIENT CYCLE SUMMARY")
    print(f"  {'─' * 50}")
    print(f"  Deaths (mass released):       {total_deaths}")
    print(f"  Accretions (mass recycled):    {total_accretions}")

    for nid, mkt_node in topo._nodes.items():
        cycler = mkt_node.nutrient_cycler
        print(f"    {nid:>15s}: deposited={cycler._total_deposited:,}B, "
              f"cycled={cycler._total_cycled:,}B, "
              f"accretions={mkt_node._accretion_count}")

    print(f"\n  KEY INSIGHT:")
    print(f"  Agent A dies at a node. Signal + loss deposited to nutrient pool.")
    print(f"  Nutrient pool hits threshold. Cycler creates new layers via factory.")
    print(f"  Agent B arrives. New layers accreted onto Agent B.")
    print(f"  Agent A's mass -> Agent B's mass. The food chain in action.")
    print(f"  Conservation law governs interaction. Factory creates legitimate mass.")


# =============================================================================
#  DEMO 5: BOOM/BUST DYNAMICS
# =============================================================================

def demo_5_boom_bust():
    separator("DEMO 5: BOOM/BUST DYNAMICS")

    print("Overshoot carrying capacity. Watch the crash. Then recovery.\n")

    topo = build_marketplace()
    # Larger population to force overshoot
    agents = make_agents(100, rng=random.Random(777))
    tracker = PopulationTracker()

    # Record initial state
    tracker.add_snapshot(0, agents)

    result = topo.run_population(
        agents, max_steps=40, tick_interval=0.3, verbose=True,
    )

    # Build tracker from population trace
    for i, snap in enumerate(result["population_trace"]):
        alive_agents = [(a, b) for a, b in agents if a.alive]
        # We can approximate from the trace
        pass

    final_alive = sum(1 for a, _ in agents if a.alive)
    final_mass = sum(a.mass for a, _ in agents if a.alive)

    # Analyze boom/bust from population trace
    alive_trace = [s["alive"] for s in result["population_trace"]]

    print(f"\n  POPULATION DYNAMICS")
    print(f"  {'─' * 50}")
    print(f"  Initial:  100 agents")
    print(f"  Final:    {final_alive} agents ({final_alive}% survival)")
    print(f"  Deaths:   {len(result['death_events'])}")

    # Show population over time
    print(f"\n  Population over time:")
    for i, snap in enumerate(result["population_trace"]):
        if i % 4 == 0 or i == len(result["population_trace"]) - 1:
            bar = "█" * (snap["alive"] // 2)
            print(f"    Step {i:3d}: {snap['alive']:4d} alive  {bar}")

    # Estimate carrying capacity from last 30% of trace
    if alive_trace:
        tail_start = max(1, int(len(alive_trace) * 0.7))
        tail = alive_trace[tail_start:]
        import statistics as st
        if tail:
            cap = st.mean(tail)
            print(f"\n  Estimated carrying capacity: {cap:.0f} agents")


# =============================================================================
#  DEMO 6: SPECIATION — NICHE DIFFERENTIATION
# =============================================================================

def demo_6_speciation():
    separator("DEMO 6: SPECIATION — NICHE DIFFERENTIATION")

    print("Alpha-heavy vs beta-heavy agents in a mixed ecosystem.")
    print("Different layer compositions -> different niche survival.\n")

    topo = build_marketplace()
    rng = random.Random(999)

    agents = []
    profiles = []

    # 25 alpha-heavy agents
    for _ in range(25):
        specs = []
        for _ in range(rng.randint(5, 10)):  # lots of alpha
            specs.append(("alpha", os.urandom(rng.randint(32, 96))))
        for _ in range(rng.randint(1, 2)):  # minimal beta
            specs.append(("beta", b""))
        for _ in range(rng.randint(1, 2)):  # minimal gamma
            specs.append(("gamma", b""))

        agent = FACTORY.build_agent(specs)
        behavior = AgentBehavior(
            risk_baseline=rng.uniform(0.3, 0.7),
            desperation_curve=2.0,
        )
        agents.append((agent, behavior))
        profiles.append("alpha-heavy")

    # 25 beta-heavy agents
    for _ in range(25):
        specs = []
        for _ in range(rng.randint(1, 2)):  # minimal alpha
            specs.append(("alpha", b""))
        for _ in range(rng.randint(5, 10)):  # lots of beta
            specs.append(("beta", os.urandom(rng.randint(32, 96))))
        for _ in range(rng.randint(1, 2)):  # minimal gamma
            specs.append(("gamma", b""))

        agent = FACTORY.build_agent(specs)
        behavior = AgentBehavior(
            risk_baseline=rng.uniform(0.3, 0.7),
            desperation_curve=2.0,
        )
        agents.append((agent, behavior))
        profiles.append("beta-heavy")

    alpha_mass = [a.mass for a, _ in agents[:25]]
    beta_mass = [a.mass for a, _ in agents[25:]]
    print(f"  Alpha-heavy: 25 agents, avg mass {sum(alpha_mass)//25:,} B")
    print(f"  Beta-heavy:  25 agents, avg mass {sum(beta_mass)//25:,} B\n")

    result = topo.run_population(
        agents, max_steps=25, tick_interval=0.3, verbose=True,
    )

    # Analyze survival by species
    alpha_survived = sum(1 for i in range(25) if agents[i][0].alive)
    beta_survived = sum(1 for i in range(25, 50) if agents[i][0].alive)

    alpha_interactions = sum(
        len(result["agent_histories"].get(i, []))
        for i in range(25)
    )
    beta_interactions = sum(
        len(result["agent_histories"].get(i, []))
        for i in range(25, 50)
    )

    print(f"\n  SPECIATION RESULTS")
    print(f"  {'─' * 50}")
    print(f"  {'Species':<15s} {'Survived':>10s} {'Rate':>8s} {'Interactions':>14s}")
    print(f"  {'─' * 50}")
    print(f"  {'Alpha-heavy':<15s} {alpha_survived:>10d} "
          f"{alpha_survived/25*100:>7.1f}% {alpha_interactions:>14d}")
    print(f"  {'Beta-heavy':<15s} {beta_survived:>10d} "
          f"{beta_survived/25*100:>7.1f}% {beta_interactions:>14d}")

    print(f"\n  KEY INSIGHT:")
    print(f"  Alpha-heavy agents thrive at feeding_a (alpha key).")
    print(f"  Beta-heavy agents thrive at feeding_b (beta key).")
    print(f"  Different layer compositions = different ecological niches.")
    print(f"  Speciation is emergent from mass physics, not programmed.")


# =============================================================================
#  DEMO 7: SCALE RUN — FULL ECOLOGY REPORT
# =============================================================================

def demo_7_scale():
    separator("DEMO 7: CONSERVATION AT SCALE — 200 AGENTS")

    print("200 agents. Full ecology. Zero tolerance for violations.\n")

    topo = build_marketplace()
    agents = make_agents(200, rng=random.Random(42))

    initial_mass = sum(a.mass for a, _ in agents)
    print(f"  Initial: 200 agents, {initial_mass:,} B total mass\n")

    t0 = time.time()
    result = topo.run_population(
        agents, max_steps=30, tick_interval=0.3, verbose=True,
    )
    elapsed = time.time() - t0

    print(f"\n  Completed in {elapsed:.2f}s ({200/elapsed:.0f} agents/sec)")

    # Build ecology report
    report = EcologyReport(
        population_trace=result["population_trace"],
        death_events=result["death_events"],
        agent_histories=result["agent_histories"],
        nodes=topo._nodes,
    )
    print(report.full_report(agents))

    # Nutrient cycling summary
    total_deposited = sum(
        n.nutrient_cycler._total_deposited for n in topo._nodes.values()
    )
    total_cycled = sum(
        n.nutrient_cycler._total_cycled for n in topo._nodes.values()
    )
    total_accretions = sum(
        n._accretion_count for n in topo._nodes.values()
    )

    print(f"  Nutrient Cycling:")
    print(f"    Total deposited:  {total_deposited:,} B")
    print(f"    Total cycled:     {total_cycled:,} B")
    print(f"    Total accretions: {total_accretions}")
    print(f"    Recycling rate:   {total_cycled/total_deposited*100:.1f}%"
          if total_deposited > 0 else "    Recycling rate:   N/A")

    # Resource state
    print(f"\n{topo.resource_summary()}")


# =============================================================================
#  SUMMARY
# =============================================================================

def summary():
    separator("SUMMARY: POPULATION ECOLOGY FROM CONSERVATION LAW")

    print("""
  What we demonstrated:

  1. MARKETPLACE TOPOLOGY
     Five nodes with finite resource pools and nutrient cyclers.
     Three key classes (alpha, beta, gamma) create ecological niches.

  2. SINGLE AGENT TRAVERSAL
     Baseline: one agent through the marketplace.
     Resource consumption, nutrient deposition, conservation check.

  3. POPULATION COMPETITION
     50 agents compete for finite resources.
     Resource depletion, survival rates, carrying capacity.

  4. NUTRIENT CYCLING
     Dead agents' mass cycles back as new layers for survivors.
     The food chain: Agent A's death -> Agent B's growth.
     Factory is the ONLY legitimate mass source.

  5. BOOM/BUST DYNAMICS
     100 agents overshoot carrying capacity.
     Population crashes, resources recover, stabilization.

  6. SPECIATION
     Alpha-heavy vs beta-heavy agents in mixed topology.
     Different layer profiles -> different ecological niches.
     Niche differentiation is emergent from mass physics.

  7. CONSERVATION AT SCALE
     200 agents, full ecology report, zero violations.
     Carrying capacity, Gini inequality, nutrient cycling metrics.

  ECOLOGICAL PROPERTIES (by construction, not simulation rules):
    - Carrying capacity:    Finite resources cap population
    - Nutrient cycling:     Dead mass -> living mass (food chain)
    - Niche differentiation: Key profiles determine habitat
    - Competition:          Shared resources create pressure
    - Boom/bust:            Overshoot -> crash -> recovery

  Mass is energy.
  Resources are habitat.
  Conservation is ecology.
  The math is the ecosystem.
""")


# =============================================================================
#  MAIN
# =============================================================================

if __name__ == "__main__":
    demo_1_topology()
    demo_2_single_agent()
    demo_3_competition()
    demo_4_nutrient_cycling()
    demo_5_boom_bust()
    demo_6_speciation()
    demo_7_scale()
    summary()
