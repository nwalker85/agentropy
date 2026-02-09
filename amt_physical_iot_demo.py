#!/usr/bin/env python3
"""
Agent Mass Theory -- Physical IoT Demo: The Viking Route
==========================================================

Maps AMT conservation physics to physical resources on a smart RV
traveling through varying connectivity environments.

Five environments. Five resource types. One conservation law.
Zero violations. Physics IS resource management.

Usage:
    python3 amt_physical_iot_demo.py
"""

import os
import time
import random
import hashlib

from amt_core import Agent, AgentFactory
from amt_extensions import AgentBehavior, AccretionPolicy
from amt_physical_iot import (
    PhysicalResource, ConnectivityEnvironment, ResourceBudget,
    PhysicalTopology, ResourceAuditReport, generate_resource_audit,
    RESOURCE_MAP, _safe_risk_tolerance,
)


# =============================================================================
#  UNIVERSE SETUP -- SECRETS AND FACTORY
# =============================================================================

SECRET_ALPHA   = hashlib.sha256(b"battery-power-alpha-secret").digest()
SECRET_BETA    = hashlib.sha256(b"bandwidth-beta-secret").digest()
SECRET_GAMMA   = hashlib.sha256(b"storage-gamma-secret").digest()
SECRET_DELTA   = hashlib.sha256(b"cpu-compute-delta-secret").digest()
SECRET_EPSILON = hashlib.sha256(b"sensor-epsilon-secret").digest()

ALL_SECRETS = {
    "alpha": SECRET_ALPHA,
    "beta": SECRET_BETA,
    "gamma": SECRET_GAMMA,
    "delta": SECRET_DELTA,
    "epsilon": SECRET_EPSILON,
}

FACTORY = AgentFactory(ALL_SECRETS)


def separator(title: str):
    print(f"\n\n{'█' * 70}")
    print(f"  {title}")
    print(f"{'█' * 70}\n")


def build_route_topology() -> PhysicalTopology:
    """Build the standard 5-location Viking route."""
    topo = PhysicalTopology(ALL_SECRETS)
    topo.set_factory(FACTORY)

    # Location 1: Campsite with shore power + wifi
    # Primary consumption: bandwidth (wifi sync) + sensor reads
    topo.add_location(
        "campsite", "campsite_wifi",
        battery_wh=None,        # shore power = unlimited
        bandwidth_mbps=10.0,    # wifi
        storage_ops=500.0,
        cpu_seconds=30.0,
        sensor_reads=50,
        consumed=["bandwidth", "sensor"],  # wifi sync + sensor polling
    )

    # Location 2: Highway with cellular
    # Primary consumption: battery (driving) + bandwidth (cellular)
    topo.add_location(
        "highway", "cellular",
        battery_wh=50.0,        # on battery
        bandwidth_mbps=5.0,     # cellular
        storage_ops=200.0,
        cpu_seconds=15.0,
        sensor_reads=30,
        consumed=["battery", "bandwidth"],  # driving + cellular data
    )

    # Location 3: Mountain pass with satellite only
    # Primary consumption: battery (heavy) + bandwidth (satellite = expensive)
    topo.add_location(
        "mountain", "satellite",
        battery_wh=30.0,        # degraded battery
        bandwidth_mbps=0.5,     # satellite (expensive)
        storage_ops=100.0,
        cpu_seconds=5.0,
        sensor_reads=20,
        consumed=["battery", "bandwidth"],  # battery drain + satellite
    )

    # Location 4: Remote off-grid
    # Primary consumption: battery + cpu (local processing, no cloud)
    topo.add_location(
        "remote", "off_grid",
        battery_wh=10.0,        # critical battery
        # NO bandwidth -- off grid
        storage_ops=50.0,
        cpu_seconds=2.0,
        sensor_reads=10,
        consumed=["battery", "cpu"],  # battery drain + local compute
    )

    # Location 5: Destination with shore power
    # Primary consumption: bandwidth (upload results) + storage (save data)
    topo.add_location(
        "destination", "shore_power",
        battery_wh=None,        # shore power
        bandwidth_mbps=10.0,
        storage_ops=500.0,
        cpu_seconds=30.0,
        sensor_reads=50,
        consumed=["bandwidth", "storage"],  # upload + save
    )

    # Connect as linear route
    topo.connect_locations("campsite", "highway")
    topo.connect_locations("highway", "mountain")
    topo.connect_locations("mountain", "remote")
    topo.connect_locations("remote", "destination")

    return topo


# =============================================================================
#  DEMO 1: ENVIRONMENT MAP
# =============================================================================

def demo_1_environment_map():
    separator("DEMO 1: PHYSICAL ENVIRONMENT MAP")

    print("Five locations. Decreasing connectivity. The Viking route.\n")

    topo = build_route_topology()
    print(topo.environment_map())

    print("\nRoute: campsite -> highway -> mountain -> remote -> destination")
    print("\nNotice:")
    print("  - campsite has NO battery resource (shore power = unlimited = no alpha key)")
    print("  - remote has NO bandwidth resource (off-grid = no beta key)")
    print("  - Mass gates tighten as battery depletes")
    print("  - Missing resources = safe passage for those layer types")


# =============================================================================
#  DEMO 2: FULL-BATTERY TRAVERSAL
# =============================================================================

def demo_2_full_battery():
    separator("DEMO 2: FULL-BATTERY TRAVERSAL")

    print("Well-resourced agent traverses the entire route.")
    print("Abundant battery, bandwidth, storage, CPU, sensors.\n")

    topo = build_route_topology()

    budget = ResourceBudget(
        battery_wh=50.0,
        bandwidth_mb=100.0,
        storage_ops=500.0,
        cpu_seconds=30.0,
        sensor_reads=50,
    )
    print(f"  Budget: {budget.summary()}")

    layer_specs = budget.to_layer_specs()
    agent = FACTORY.build_agent(layer_specs)
    print(f"  Agent: {agent}")
    print(f"  Layers: {agent.layer_count}, Mass: {agent.mass:,} B\n")

    route = ["campsite", "highway", "mountain", "remote", "destination"]
    history = topo.traverse_route(agent, route, verbose=True)

    # Conservation check
    violations = 0
    for entry in history:
        if entry["entered"]:
            lhs = entry["mass_before"]
            rhs = entry["mass_after"] + entry["signal"] + entry["loss"]
            if lhs != rhs:
                violations += 1

    print(f"\n  Conservation violations: {violations}")
    print(f"  Agent alive: {agent.alive}")
    print(f"  Final mass: {agent.mass:,} B")

    if agent.alive:
        remaining = ResourceBudget.interpret_agent_mass(agent)
        print(f"  Estimated remaining resources:")
        for res_type, amount in remaining.items():
            if amount > 0:
                _, (_, factor) = res_type, RESOURCE_MAP[res_type]
                print(f"    {res_type:>10s}: {amount:.1f}")


# =============================================================================
#  DEMO 3: LOW-BATTERY TRAVERSAL
# =============================================================================

def demo_3_low_battery():
    separator("DEMO 3: LOW-BATTERY TRAVERSAL")

    print("Minimal agent. Barely enough resources to start.")
    print("Will it survive the remote off-grid stretch?\n")

    topo = build_route_topology()

    budget = ResourceBudget(
        battery_wh=10.0,
        bandwidth_mb=5.0,
        storage_ops=20.0,
        cpu_seconds=2.0,
        sensor_reads=5,
    )
    print(f"  Budget: {budget.summary()}")

    layer_specs = budget.to_layer_specs()
    agent = FACTORY.build_agent(layer_specs)
    print(f"  Agent: {agent}")
    print(f"  Layers: {agent.layer_count}, Mass: {agent.mass:,} B\n")

    route = ["campsite", "highway", "mountain", "remote", "destination"]
    history = topo.traverse_route(agent, route, verbose=True)

    violations = 0
    entered_count = 0
    blocked_count = 0
    for entry in history:
        if entry["entered"]:
            entered_count += 1
            lhs = entry["mass_before"]
            rhs = entry["mass_after"] + entry["signal"] + entry["loss"]
            if lhs != rhs:
                violations += 1
        else:
            blocked_count += 1

    print(f"\n  Conservation violations: {violations}")
    print(f"  Locations entered: {entered_count}")
    print(f"  Locations blocked: {blocked_count}")
    print(f"  Agent alive: {agent.alive}")

    print("\nKEY INSIGHT:")
    print("  Low-budget agents die in the wilderness.")
    print("  No policy blocked them. Physics did.")
    print("  Battery depletion -> mass reduction -> conservation -> death.")


# =============================================================================
#  DEMO 4: BEHAVIORAL DIVERGENCE
# =============================================================================

def demo_4_behavioral_divergence():
    separator("DEMO 4: BEHAVIORAL DIVERGENCE — BATTERY SHAPES BEHAVIOR")

    print("Two agents. Same route. Different battery budgets.")
    print("The conservation law creates different outcomes.\n")

    route = ["campsite", "highway", "mountain", "remote", "destination"]

    # Agent Heavy: lots of battery
    topo_a = build_route_topology()
    budget_a = ResourceBudget(
        battery_wh=50.0, bandwidth_mb=50.0,
        storage_ops=200.0, cpu_seconds=20.0, sensor_reads=30,
    )
    agent_a = FACTORY.build_agent(budget_a.to_layer_specs())

    print(f"--- AGENT HEAVY (battery={budget_a.battery_wh} Wh, mass={agent_a.mass:,} B) ---")
    history_a = topo_a.traverse_route(agent_a, route, verbose=True)

    # Agent Light: minimal battery
    topo_b = build_route_topology()
    budget_b = ResourceBudget(
        battery_wh=8.0, bandwidth_mb=5.0,
        storage_ops=30.0, cpu_seconds=2.0, sensor_reads=5,
    )
    agent_b = FACTORY.build_agent(budget_b.to_layer_specs())

    print(f"\n--- AGENT LIGHT (battery={budget_b.battery_wh} Wh, mass={agent_b.mass:,} B) ---")
    history_b = topo_b.traverse_route(agent_b, route, verbose=True)

    # Compare
    entered_a = sum(1 for h in history_a if h["entered"])
    entered_b = sum(1 for h in history_b if h["entered"])

    print(f"\n{'─' * 70}")
    print(f"  DIVERGENCE COMPARISON")
    print(f"{'─' * 70}")
    print(f"  {'Metric':<25s} {'Heavy':>10s} {'Light':>10s}")
    print(f"  {'─' * 50}")
    print(f"  {'Initial mass (B)':<25s} {history_a[0]['mass_before']:>10,} {history_b[0]['mass_before']:>10,}")
    print(f"  {'Locations entered':<25s} {entered_a:>10d} {entered_b:>10d}")
    print(f"  {'Survived':<25s} {'Yes' if agent_a.alive else 'No':>10s} {'Yes' if agent_b.alive else 'No':>10s}")
    print(f"  {'Final mass (B)':<25s} {agent_a.mass:>10,} {agent_b.mass:>10,}")

    print("\nKEY INSIGHT:")
    print("  Same route. Same topology. Different battery budgets.")
    print("  Heavy agent passes through. Light agent strands.")
    print("  The conservation law IS the battery management system.")


# =============================================================================
#  DEMO 5: ENVIRONMENT TRANSITIONS
# =============================================================================

def demo_5_environment_transitions():
    separator("DEMO 5: ENVIRONMENT TRANSITIONS — LOSING RESOURCE CLASSES")

    print("Watch how the agent loses access to entire resource classes")
    print("as connectivity degrades along the route.\n")

    topo = build_route_topology()

    budget = ResourceBudget(
        battery_wh=30.0, bandwidth_mb=50.0,
        storage_ops=200.0, cpu_seconds=10.0, sensor_reads=20,
    )
    agent = FACTORY.build_agent(budget.to_layer_specs())

    route = ["campsite", "highway", "mountain", "remote", "destination"]

    print(f"  Budget: {budget.summary()}")
    print(f"  Agent: {agent}\n")

    print("  Environment key class affinity (consumed vs safe):")
    for loc_id in route:
        env = topo._environments[loc_id]
        consumed_keys = sorted(
            res.key_class for res in env.resources.values()
            if res.resource_type in env.consumed_types
        )
        safe_keys = sorted(
            set(["alpha", "beta", "gamma", "delta", "epsilon"]) - set(consumed_keys)
        )
        print(f"    {loc_id:>15s} [{env.location_type:>14s}]: "
              f"consumes {{{', '.join(consumed_keys)}}}"
              + (f"  safe: {{{', '.join(safe_keys)}}}" if safe_keys else ""))

    print()

    history = topo.traverse_route(agent, route, verbose=True)

    print("\nTRANSITION ANALYSIS:")
    for h in history:
        if not h["entered"]:
            print(f"  {h['location']:>15s}: BLOCKED")
            continue
        env = topo._environments[h["location"]]
        consumed_keys = [res.key_class for res in env.resources.values()
                         if res.resource_type in env.consumed_types]
        print(f"  {h['location']:>15s}: stripped {h['layers_stripped']} layers "
              f"(consumed keys: {{{', '.join(consumed_keys)}}})")

    print("\nKEY INSIGHT:")
    print("  At 'campsite': no alpha key (shore power), so battery layers are SAFE.")
    print("  At 'remote': no beta key (off-grid), so bandwidth layers are SAFE.")
    print("  Missing key classes = safe passage = resource preservation.")
    print("  The environment's physics determines what gets consumed.")


# =============================================================================
#  DEMO 6: CONSERVATION AT SCALE
# =============================================================================

def demo_6_scale():
    separator("DEMO 6: CONSERVATION AT SCALE")

    num_agents = 150
    print(f"Running {num_agents} agents through the Viking route...\n")

    rng = random.Random(42)
    route = ["campsite", "highway", "mountain", "remote", "destination"]

    results = []
    total_interactions = 0
    total_violations = 0
    survivors = 0
    total_layers_stripped = 0

    t0 = time.time()

    for i in range(num_agents):
        # Vary budgets: some rich, some poor
        battery = rng.uniform(5.0, 60.0)
        bandwidth = rng.uniform(1.0, 80.0)
        storage = rng.uniform(10.0, 300.0)
        cpu = rng.uniform(1.0, 25.0)
        sensors = rng.randint(2, 40)

        budget = ResourceBudget(
            battery_wh=battery,
            bandwidth_mb=bandwidth,
            storage_ops=storage,
            cpu_seconds=cpu,
            sensor_reads=sensors,
        )

        topo = build_route_topology()
        agent = FACTORY.build_agent(budget.to_layer_specs())
        initial_mass = agent.mass

        history = topo.traverse_route(agent, route, verbose=False)

        # Check conservation
        agent_violations = 0
        agent_interactions = 0
        agent_layers = 0
        locations_entered = 0
        for entry in history:
            if entry["entered"]:
                agent_interactions += 1
                agent_layers += entry["layers_stripped"]
                lhs = entry["mass_before"]
                rhs = entry["mass_after"] + entry["signal"] + entry["loss"]
                if lhs != rhs:
                    agent_violations += 1
                locations_entered += 1

        total_interactions += agent_interactions
        total_violations += agent_violations
        total_layers_stripped += agent_layers

        if agent.alive:
            survivors += 1

        results.append({
            "battery": battery,
            "initial_mass": initial_mass,
            "final_mass": agent.mass,
            "alive": agent.alive,
            "locations_entered": locations_entered,
            "interactions": agent_interactions,
            "violations": agent_violations,
        })

    elapsed = time.time() - t0

    print(f"  Completed in {elapsed:.2f}s ({num_agents/elapsed:.0f} agents/sec)\n")

    print(f"{'─' * 70}")
    print(f"  SCALE RESULTS")
    print(f"{'─' * 70}")
    print(f"  Agents:              {num_agents}")
    print(f"  Total interactions:  {total_interactions:,}")
    print(f"  Total layers stripped: {total_layers_stripped:,}")
    print(f"  Agents surviving:    {survivors} ({survivors/num_agents*100:.1f}%)")
    print(f"  Conservation violations: {total_violations}")
    print()

    if total_violations == 0:
        print(f"  C_{{n+1}} + S_{{n+1}} + L_n = C_n")
        print(f"  HOLDS FOR ALL {total_interactions:,} INTERACTIONS.")
        print(f"  ZERO VIOLATIONS. Physics enforces resource limits.")
    else:
        print(f"  WARNING: {total_violations} conservation violations detected!")

    # Survival analysis by battery level
    bins = {"<10 Wh": [], "10-25 Wh": [], "25-40 Wh": [], ">40 Wh": []}
    for r in results:
        if r["battery"] < 10:
            bins["<10 Wh"].append(r)
        elif r["battery"] < 25:
            bins["10-25 Wh"].append(r)
        elif r["battery"] < 40:
            bins["25-40 Wh"].append(r)
        else:
            bins[">40 Wh"].append(r)

    print(f"\n  Survival by Battery Level:")
    print(f"  {'Battery':<12s} {'Count':>6s} {'Survived':>10s} {'Rate':>8s} {'Avg Locations':>15s}")
    print(f"  {'─' * 55}")
    for label, agents in bins.items():
        if not agents:
            continue
        survived = sum(1 for a in agents if a["alive"])
        avg_loc = sum(a["locations_entered"] for a in agents) / len(agents)
        rate = survived / len(agents) * 100
        bar = "█" * int(rate / 5)
        print(f"  {label:<12s} {len(agents):>6d} {survived:>10d} {rate:>7.1f}% {avg_loc:>13.1f}  {bar}")

    print(f"\nKEY INSIGHT:")
    print(f"  Battery budget directly predicts survival distance.")
    print(f"  No hand-coded power management. No battery alerts.")
    print(f"  Conservation law IS the battery management system.")


# =============================================================================
#  SUMMARY
# =============================================================================

def summary():
    separator("SUMMARY: PHYSICAL RESOURCES AS CONSERVATION-GOVERNED MASS")

    print("""
  What we demonstrated:

  1. ENVIRONMENT MAP
     Five physical locations with varying resources.
     Each resource type maps to a key class.
     Missing resources = safe passage (no key = no consumption).

  2. FULL-BATTERY TRAVERSAL
     Well-resourced agent traverses the entire route.
     Resource consumption tracked in physical units.
     Conservation verified at every location.

  3. LOW-BATTERY TRAVERSAL
     Minimal agent strands in the wilderness.
     No policy blocks it. Physics does.
     Battery depletion -> mass reduction -> death.

  4. BEHAVIORAL DIVERGENCE
     Same route. Different batteries.
     Heavy agent passes through. Light agent dies.
     Battery budget IS behavioral destiny.

  5. ENVIRONMENT TRANSITIONS
     Agent loses resource classes as connectivity degrades.
     Shore power -> cellular -> satellite -> off-grid.
     Missing keys = preserved layers = resource conservation.

  6. CONSERVATION AT SCALE
     150 agents, varied budgets, zero violations.
     Survival correlates with battery level.
     The conservation law IS the battery management system.

  PHYSICAL PROPERTIES (by construction, not policy):
    - Battery limits are mass gates:   No charge = no heavy operations
    - Bandwidth loss is layer stripping: Off-grid = beta layers preserved
    - Storage I/O costs mass:           Every read/write is accountable
    - CPU time costs mass:              Compute budget is physical
    - Sensor access costs mass:         Every reading has a price

  Mass is energy.
  Layers are resource allocation.
  Conservation is physics.
  The math is the resource manager.
""")


# =============================================================================
#  MAIN
# =============================================================================

if __name__ == "__main__":
    demo_1_environment_map()
    demo_2_full_battery()
    demo_3_low_battery()
    demo_4_behavioral_divergence()
    demo_5_environment_transitions()
    demo_6_scale()
    summary()
