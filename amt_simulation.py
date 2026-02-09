"""
Agent Mass Theory — Simulation Suite
=====================================

Demonstrates:
    1. Mass payload construction
    2. Environmental decryption
    3. Signal vs loss measurement
    4. ΔL vector computation
    5. Multi-class key hazard (the "static key" threat)
    6. Mass-gated access (too big / too small)
    7. Accretion (gaining mass)
    8. Agent death
    9. Conservation law verification
    10. Full lifecycle traversal

Run: python amt_simulation.py
"""

import os
from amt_core import (
    AgentFactory, Environment, Agent, Layer,
    interact, accrete, hazard_rating, traverse,
    verify_conservation, derive_key, encrypt_layer,
)


def separator(title: str):
    print(f"\n\n{'█' * 60}")
    print(f"  {title}")
    print(f"{'█' * 60}\n")


# =============================================================================
# SETUP: Define the universe's key classes and master secrets
# =============================================================================

# These are the "elements" of the agent universe.
# Each key class represents a type of environmental interaction.
MASTER_SECRETS = {
    "alpha":   os.urandom(32),   # e.g., computational capability
    "beta":    os.urandom(32),   # e.g., memory / knowledge
    "gamma":   os.urandom(32),   # e.g., communication channel
    "delta":   os.urandom(32),   # e.g., sensory input
    "epsilon": os.urandom(32),   # e.g., authorization token
}

factory = AgentFactory(MASTER_SECRETS)


# =============================================================================
# SIMULATION 1: Basic mass construction and inspection
# =============================================================================

separator("SIM 1: MASS PAYLOAD CONSTRUCTION")

agent = factory.build_agent([
    ("alpha", b"mission: observe target system"),
    ("alpha", b""),                                    # empty alpha (toll layer)
    ("beta",  b"knowledge: TCP/IP stack internals"),
    ("beta",  b"knowledge: Kubernetes API"),
    ("gamma", b""),                                    # empty gamma (toll)
    ("gamma", b""),                                    # empty gamma (toll)
    ("delta", b"sensor: network traffic"),
    ("epsilon", b""),                                  # empty epsilon (toll)
])

print(f"Agent constructed: {agent}")
print(f"Total mass: {agent.mass:,} bytes")
print(f"Layer count: {agent.layer_count}")
print(f"\nMass profile (EXTERNAL view only — agent cannot see this):")
for cls, mass in sorted(agent.mass_profile().items()):
    print(f"  {cls:>10s}: {mass:>6,} B")


# =============================================================================
# SIMULATION 2: Single-class environment (benign)
# =============================================================================

separator("SIM 2: BENIGN ENVIRONMENT (single key class)")

# This environment only has the "alpha" key — it can only strip alpha layers.
benign_env = Environment(
    name="Benign-Alpha-Node",
    secrets={"alpha": MASTER_SECRETS["alpha"]},
)

print(f"Environment: {benign_env}")
print(f"Hazard classes: {benign_env.hazard_classes}")

hazard = hazard_rating(benign_env, agent)
print(f"\nHazard analysis:")
print(f"  Vulnerable mass:  {hazard['vulnerable_mass']:,} B ({hazard['vulnerable_ratio']:.1%})")
print(f"  Safe mass:        {hazard['safe_mass']:,} B")
print(f"  Lethality:        {hazard['lethality']:.2f}")

result = interact(agent, benign_env)
print(result.summary())

print(f"\nConservation check: C_n = C_{{n+1}} + S_n + L_n")
print(f"  {result.mass_before} = {result.mass_after} + {result.total_signal} + {result.total_loss}")
print(f"  {result.mass_before} = {result.mass_after + result.total_signal + result.total_loss}  ✓")


# =============================================================================
# SIMULATION 3: Multi-class environment (HAZARDOUS)
# =============================================================================

separator("SIM 3: HAZARDOUS ENVIRONMENT (multi-class static key)")

# This environment holds keys for alpha, beta, AND gamma.
# It is CORROSIVE — strips three layer types simultaneously.
hazardous_env = Environment(
    name="Corrosive-Multi-Node",
    secrets={
        "alpha": MASTER_SECRETS["alpha"],
        "beta":  MASTER_SECRETS["beta"],
        "gamma": MASTER_SECRETS["gamma"],
    },
)

print(f"Environment: {hazardous_env}")
print(f"Key classes held: {hazardous_env.key_classes}")
print(f"Hazard rating: {hazardous_env.hazard_classes} classes (DANGEROUS)")

hazard = hazard_rating(hazardous_env, agent)
print(f"\nHazard analysis against current agent:")
print(f"  Vulnerable mass:  {hazard['vulnerable_mass']:,} B ({hazard['vulnerable_ratio']:.1%})")
print(f"  Vulnerable layers: {hazard['vulnerable_layers']}")
print(f"  Safe mass:        {hazard['safe_mass']:,} B")
print(f"  Lethality:        {hazard['lethality']:.2f}")
print(f"  Hazardous classes: {hazard['hazard_classes']}")
print(f"  Safe classes:      {hazard['safe_classes']}")

result = interact(agent, hazardous_env)
print(result.summary())

print(f"\nΔL Vector breakdown (loss direction):")
for cls, loss in result.delta_L.items():
    print(f"  {cls:>10s}: {loss:>6,.0f} B lost")
print(f"\nThis shows WHERE the agent lost mass — the environment's")
print(f"corrosion pattern. Different environments corrode differently.")


# =============================================================================
# SIMULATION 4: Mass-gated access
# =============================================================================

separator("SIM 4: MASS-GATED ACCESS (too big / too small)")

print(f"Current agent mass: {agent.mass:,} B\n")

# Environment that only admits agents < 100 bytes
tiny_gate = Environment(
    name="Micro-Node",
    secrets={"delta": MASTER_SECRETS["delta"]},
    mass_threshold=(0, 100),
)

print(f"Micro-Node gate: max {tiny_gate.mass_threshold[1]}B")
result = interact(agent, tiny_gate)
print(f"  Agent mass {agent.mass}B → {'BLOCKED' if not result.agent_could_enter else 'ENTERED'}")

# Environment that only admits agents > 10,000 bytes
heavy_gate = Environment(
    name="Heavy-Node",
    secrets={"delta": MASTER_SECRETS["delta"]},
    mass_threshold=(10000, float('inf')),
)

print(f"\nHeavy-Node gate: min {heavy_gate.mass_threshold[0]:,}B")
result = interact(agent, heavy_gate)
print(f"  Agent mass {agent.mass}B → {'BLOCKED' if not result.agent_could_enter else 'ENTERED'}")

# Environment with a window the agent fits
fitting_gate = Environment(
    name="Fitting-Node",
    secrets={"delta": MASTER_SECRETS["delta"]},
    mass_threshold=(0, 5000),
)

print(f"\nFitting-Node gate: 0-{fitting_gate.mass_threshold[1]:,}B")
result = interact(agent, fitting_gate)
print(f"  Agent mass was {result.mass_before}B → {'ENTERED' if result.agent_could_enter else 'BLOCKED'}")
if result.agent_could_enter:
    print(f"  After interaction: {result.mass_after}B (stripped delta layers)")


# =============================================================================
# SIMULATION 5: Accretion (gaining mass)
# =============================================================================

separator("SIM 5: ACCRETION (gaining energy)")

print(f"Agent before accretion: {agent}")

# Environment rewards the agent with new layers
reward_layers = [
    factory.create_layer("epsilon", b"reward: elevated access token"),
    factory.create_layer("epsilon", b""),  # empty buffer layer
    factory.create_layer("alpha", b"refreshed capability: observe"),
]

added = accrete(agent, reward_layers)
print(f"Accreted {added:,} bytes across {len(reward_layers)} layers")
print(f"Agent after accretion: {agent}")
print(f"\nNew mass profile:")
for cls, mass in sorted(agent.mass_profile().items()):
    print(f"  {cls:>10s}: {mass:>6,} B")


# =============================================================================
# SIMULATION 6: Full lifecycle — traversal to death
# =============================================================================

separator("SIM 6: FULL LIFECYCLE (birth → traversal → death)")

# Build a fresh agent with limited mass
mortal_agent = factory.build_mixed_agent({
    "alpha": (3, 2),   # 3 data + 2 empty
    "beta":  (2, 1),   # 2 data + 1 empty
    "gamma": (1, 3),   # 1 data + 3 empty
})

print(f"Mortal agent born: {mortal_agent}")
print(f"Mass profile:")
for cls, mass in sorted(mortal_agent.mass_profile().items()):
    print(f"  {cls:>10s}: {mass:>6,} B")

# Define a hostile corridor of environments
corridor = [
    Environment("Node-1-Alpha", {"alpha": MASTER_SECRETS["alpha"]}),
    Environment("Node-2-Beta", {"beta": MASTER_SECRETS["beta"]}),
    Environment("Node-3-Gamma", {"gamma": MASTER_SECRETS["gamma"]}),
    # This one is a kill zone — has all remaining keys
    Environment("Kill-Zone", {
        "alpha": MASTER_SECRETS["alpha"],
        "beta": MASTER_SECRETS["beta"],
        "gamma": MASTER_SECRETS["gamma"],
    }),
]

results = traverse(mortal_agent, corridor, verbose=True)

# Verify conservation across all interactions
separator("CONSERVATION LAW VERIFICATION")
all_valid = verify_conservation(results)
print(f"\nAll interactions conserve mass: {'✓ YES' if all_valid else '✖ NO'}")

# Print full trajectory
print(f"\nTrajectory summary:")
print(f"{'Step':>6s}  {'Environment':<20s}  {'Mass Before':>12s}  {'Mass After':>12s}  {'Signal':>8s}  {'Loss':>8s}  {'S/M':>6s}")
print(f"{'─' * 80}")
for i, r in enumerate(results):
    if r.agent_could_enter:
        print(f"{i:>6d}  {corridor[i].name:<20s}  {r.mass_before:>12,}  {r.mass_after:>12,}  "
              f"{r.total_signal:>8,}  {r.total_loss:>8,}  {r.signal_ratio:>6.3f}")
    else:
        print(f"{i:>6d}  {corridor[i].name:<20s}  {'BLOCKED':>12s}")


# =============================================================================
# SIMULATION 7: ΔL vector as navigation signal
# =============================================================================

separator("SIM 7: ΔL VECTOR AS NAVIGATION SIGNAL")

print("Demonstrating how loss differential reveals environment character.\n")

scout = factory.build_mixed_agent({
    "alpha": (5, 5),
    "beta":  (5, 5),
    "gamma": (5, 5),
}, payload_size=32)

# Three different environments with different corrosion patterns
envs = [
    ("Narrow-Alpha",  Environment("Narrow-Alpha", {"alpha": MASTER_SECRETS["alpha"]})),
    ("Narrow-Beta",   Environment("Narrow-Beta", {"beta": MASTER_SECRETS["beta"]})),
    ("Broad-Corrosive", Environment("Broad-Corrosive", {
        "alpha": MASTER_SECRETS["alpha"],
        "beta": MASTER_SECRETS["beta"],
        "gamma": MASTER_SECRETS["gamma"],
    })),
]

# Test each environment against identical agents
for label, env in envs:
    test_agent = factory.build_mixed_agent({
        "alpha": (5, 5),
        "beta":  (5, 5),
        "gamma": (5, 5),
    }, payload_size=32)
    
    result = interact(test_agent, env)
    
    print(f"  {label}:")
    print(f"    Layers stripped: {result.layers_stripped}")
    print(f"    Mass consumed:   {result.total_consumed:,} B")
    print(f"    Signal ratio:    {result.signal_ratio:.3f}")
    print(f"    ΔL vector:")
    for cls in ["alpha", "beta", "gamma"]:
        loss = result.delta_L.get(cls, 0)
        bar = "█" * int(loss / 10) if loss > 0 else "·"
        print(f"      {cls:>8s}: {loss:>6,.0f} B  {bar}")
    print()

print("The ΔL vector reveals the environment's corrosion signature.")
print("Narrow environments show single-dimension loss.")
print("Broad environments show multi-dimensional loss.")
print("An agent observing its mass delta (but not ΔL directly)")
print("can infer environment hostility but not direction —")
print("that's the information asymmetry by design.")


# =============================================================================
# SIMULATION 8: Penny scaling demonstration
# =============================================================================

separator("SIM 8: PENNY SCALING (micro to macro)")

for label, data, empty, payload_sz in [
    ("Micro-agent (drone)",     2,    3,   16),
    ("Small-agent (scout)",     10,   10,  32),
    ("Medium-agent (worker)",   50,   50,  64),
    ("Large-agent (architect)", 200,  100, 128),
    ("Massive-agent (titan)",   1000, 500, 256),
]:
    a = factory.build_uniform_agent("alpha", data, empty, payload_sz)
    print(f"  {label:30s}  layers={a.layer_count:>5,}  "
          f"mass={a.mass:>12,} B  ({a.mass/1024:.1f} KB)")

print(f"\nMass scales linearly with layer count × payload size.")
print(f"A 'penny' (empty layer) ≈ {factory.create_layer('alpha', b'').mass} bytes of overhead.")
print(f"This is the minimum cost of existence per layer.")


# =============================================================================
# FINAL SUMMARY
# =============================================================================

separator("MATHEMATICAL SUMMARY")

print("""
  AGENT MASS THEORY — Conservation Law
  ═════════════════════════════════════

  C_{n+1} + S_{n+1} + L_n = C_n

  Where:
    C_n     = cipher mass at state n (total encrypted bytes)
    C_{n+1} = cipher mass after environmental interaction
    S_{n+1} = signal extracted (information yield)
    L_n     = loss incurred (entropy cost)

  Boundary Conditions:
    C_n = 0  →  agent death (no mass, no existence)
    S/C → 0  →  diminishing returns (all toll, no signal)
    L/C → 1  →  hostile environment (all loss)

  Key Properties:
    1. Agents do NOT decrypt themselves
    2. Environments are the active party
    3. Multi-class keys are hazardous (corrosive)
    4. Empty layers carry meaning through absence
    5. Mass gates enforce topology physically
    6. Conservation is absolute — no mass created or destroyed,
       only transformed between cipher, signal, and loss
    7. ΔL is a vector, not a scalar — loss has direction
    8. The agent observes consequences, not mechanism

  This is the second law of thermodynamics for digital agents.
  Potential always decreases. Signal costs energy.
  The agent persists by acquiring new energy or it dies.
""")
