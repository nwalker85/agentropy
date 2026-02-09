"""
Agent Mass Theory — Extension Simulations
==========================================

Demonstrates:
    1. Ledger system (local + public commit)
    2. Formal node interactions
    3. BEHAVIORAL DIVERGENCE — same topology, different mass, different decisions
    4. Key rotation (temporal hazard)
    5. Full topology traversal with psychological state tracking
"""

import os
import random
from amt_core import AgentFactory, Agent, interact, hazard_rating
from amt_extensions import (
    Node, AccretionPolicy, AgentBehavior, Topology,
    LocalLedger, PublicLedger, PublicCommitment,
    merkle_root, schedule_key_rotation,
)


def separator(title: str):
    print(f"\n\n{'█' * 60}")
    print(f"  {title}")
    print(f"{'█' * 60}\n")


# =============================================================================
# UNIVERSE SETUP
# =============================================================================

MASTER_SECRETS = {
    "alpha":   os.urandom(32),
    "beta":    os.urandom(32),
    "gamma":   os.urandom(32),
    "delta":   os.urandom(32),
    "epsilon": os.urandom(32),
}

factory = AgentFactory(MASTER_SECRETS)


# =============================================================================
# SIM 1: LEDGER SYSTEM
# =============================================================================

separator("SIM 1: LEDGER ARCHITECTURE")

# Create a node with a local ledger
node = Node(
    node_id="node-001",
    name="Ledger-Test-Node",
    _key_secrets={"alpha": MASTER_SECRETS["alpha"]},
)

# Run several agents through it
print("Processing 5 agents through the node...\n")
for i in range(5):
    agent = factory.build_mixed_agent({
        "alpha": (3, 2),
        "beta": (2, 1),
    }, payload_size=32)
    
    result = node.process(agent, factory)
    print(f"  Agent {i+1}: mass {result.mass_before:,} → {result.mass_after:,} "
          f"(S={result.total_signal}, L={result.total_loss})")

# Show local ledger state
print(f"\n{node.ledger.summary()}")

# Commit to public ledger
public_ledger = PublicLedger()
commitment = node.ledger.commit()
public_ledger.publish(commitment)

print(f"\nPublic commitment published:")
print(f"  {commitment}")
print(f"  Merkle root: {commitment.merkle_root[:48]}...")
print(f"  Batch size:  {commitment.batch_size} transactions")

# Verify a specific entry
entry = node.ledger.entries[2]  # pick the 3rd entry
verified = node.ledger.verify_entry(entry, commitment)
print(f"\nAudit verification for entry {entry.entry_id[:12]}...:")
print(f"  Conservation valid: {entry.conservation_valid}")
print(f"  In public commit:   {verified}")
print(f"  Entry hash:         {entry.hash[:32]}...")

# Public audit (what anyone can see)
print(f"\nPublic audit of node-001:")
audit = public_ledger.audit_node("node-001")
for k, v in audit.items():
    print(f"  {k}: {v}")

print(f"\nNote: The public ledger reveals NOTHING about individual")
print(f"transactions, agent identities, signal content, or loss vectors.")
print(f"Only: 'this node committed N transactions in time range [a, b].'")


# =============================================================================
# SIM 2: BEHAVIORAL DIVERGENCE
# =============================================================================

separator("SIM 2: BEHAVIORAL DIVERGENCE")
print("Same topology. Same start. Different mass. Different fate.\n")

# Build a simple topology: three paths from center
#
#   [safe-A] ←→ [START] ←→ [risky-B]
#                  ↕
#              [deadly-C]
#

topo = Topology()

start_node = Node(
    node_id="start",
    name="Start",
    _key_secrets={},  # inert — no decryption
    mass_window=(0, float('inf')),
)

safe_node = Node(
    node_id="safe",
    name="Safe-Path",
    _key_secrets={"alpha": MASTER_SECRETS["alpha"]},
    mass_window=(0, float('inf')),
    accretion_policy=AccretionPolicy(
        trigger="always",
        key_class="beta",
        count=1,
        payload_gen=lambda: os.urandom(16),
    ),
)

risky_node = Node(
    node_id="risky",
    name="Risky-Path",
    _key_secrets={
        "alpha": MASTER_SECRETS["alpha"],
        "beta": MASTER_SECRETS["beta"],
    },
    mass_window=(0, float('inf')),
    accretion_policy=AccretionPolicy(
        trigger="signal_threshold",
        signal_threshold=0.3,
        key_class="gamma",
        count=3,
        payload_gen=lambda: os.urandom(64),
    ),
)

deadly_node = Node(
    node_id="deadly",
    name="Deadly-Path",
    _key_secrets={
        "alpha": MASTER_SECRETS["alpha"],
        "beta": MASTER_SECRETS["beta"],
        "gamma": MASTER_SECRETS["gamma"],
    },
    mass_window=(0, float('inf')),
    accretion_policy=AccretionPolicy(
        trigger="survival",
        min_survival_mass=100,
        key_class="delta",
        count=5,
        payload_gen=lambda: os.urandom(128),
    ),
)

topo.add_node(start_node)
topo.add_node(safe_node)
topo.add_node(risky_node)
topo.add_node(deadly_node)
topo.connect("start", "safe")
topo.connect("start", "risky")
topo.connect("start", "deadly")
topo.connect("safe", "risky")
topo.connect("risky", "deadly")

print("Topology:")
print("  [Safe-Path] ←→ [START] ←→ [Risky-Path]")
print("                    ↕             ↕")
print("                [Deadly-Path] ←───┘")
print()
print("  Safe-Path:   decrypts alpha, always accretes beta")
print("  Risky-Path:  decrypts alpha+beta, accretes gamma if signal > 30%")
print("  Deadly-Path: decrypts alpha+beta+gamma, accretes delta if agent mass < 100B")
print()

# --- Agent A: Massive (healthy, conservative) ---
print(f"{'─' * 60}")
print("AGENT A: THE TITAN (massive, conservative)")
print(f"{'─' * 60}")

random.seed(42)  # reproducible
agent_a = factory.build_mixed_agent({
    "alpha": (10, 5),
    "beta":  (10, 5),
    "gamma": (5, 5),
    "delta": (5, 5),
}, payload_size=64)

behavior_a = AgentBehavior(risk_baseline=0.3, desperation_curve=2.0)

history_a = topo.run_agent(
    agent=agent_a,
    behavior=behavior_a,
    start_node_id="start",
    max_steps=15,
    factory=factory,
    verbose=True,
)

# --- Agent B: Small (resource-starved, desperate) ---
print(f"\n{'─' * 60}")
print("AGENT B: THE SCRAPPER (small, desperate)")
print(f"{'─' * 60}")

random.seed(42)  # same seed — differences come from mass, not randomness
agent_b = factory.build_mixed_agent({
    "alpha": (2, 1),
    "beta":  (1, 1),
    "gamma": (1, 1),
}, payload_size=32)

behavior_b = AgentBehavior(risk_baseline=0.3, desperation_curve=2.0)

history_b = topo.run_agent(
    agent=agent_b,
    behavior=behavior_b,
    start_node_id="start",
    max_steps=15,
    factory=factory,
    verbose=True,
)

# --- Comparison ---
separator("DIVERGENCE ANALYSIS")

print(f"{'Metric':<35s}  {'Titan':>12s}  {'Scrapper':>12s}")
print(f"{'─' * 65}")

def safe_last(history, key, default="N/A"):
    vals = [h[key] for h in history if h["entered"]]
    return vals[-1] if vals else default

print(f"{'Initial mass':<35s}  {history_a[0]['mass_before']:>12,}  {history_b[0]['mass_before']:>12,}")
print(f"{'Steps survived':<35s}  {len(history_a):>12d}  {len(history_b):>12d}")
print(f"{'Final mass':<35s}  {safe_last(history_a, 'mass_after', 0):>12,}  {safe_last(history_b, 'mass_after', 0):>12,}")
print(f"{'Final alive':<35s}  {str(safe_last(history_a, 'alive')):>12s}  {str(safe_last(history_b, 'alive')):>12s}")
print(f"{'Peak risk tolerance':<35s}  {max(h['risk_tolerance'] for h in history_a):>12.3f}  {max(h['risk_tolerance'] for h in history_b):>12.3f}")
print(f"{'Peak survival pressure':<35s}  {max(h['survival_pressure'] for h in history_a if h['survival_pressure'] != float('inf')):>12.3f}  {max(h['survival_pressure'] for h in history_b if h['survival_pressure'] != float('inf')):>12.3f}")

nodes_a = [h['node'] for h in history_a if h['entered']]
nodes_b = [h['node'] for h in history_b if h['entered']]
print(f"\n{'Path taken (Titan):':<35s}  {' → '.join(nodes_a[:10])}")
print(f"{'Path taken (Scrapper):':<35s}  {' → '.join(nodes_b[:10])}")

risky_a = sum(1 for n in nodes_a if n in ("Risky-Path", "Deadly-Path"))
risky_b = sum(1 for n in nodes_b if n in ("Risky-Path", "Deadly-Path"))
safe_a = sum(1 for n in nodes_a if n == "Safe-Path")
safe_b = sum(1 for n in nodes_b if n == "Safe-Path")

print(f"\n{'Safe choices':<35s}  {safe_a:>12d}  {safe_b:>12d}")
print(f"{'Risky/deadly choices':<35s}  {risky_a:>12d}  {risky_b:>12d}")

print(f"""
KEY INSIGHT:
  Both agents started at the same node with the same behavioral
  parameters (risk_baseline=0.3, desperation_curve=2.0).
  
  The ONLY difference was mass.
  
  Mass shaped psychology. Psychology shaped decisions.
  Decisions shaped trajectory. Trajectory shaped fate.
  
  The Titan's risk tolerance stayed low — it could afford caution.
  The Scrapper's risk tolerance spiked — desperation drove it
  toward high-variance nodes that a healthy agent would avoid.
  
  This is the internal locus of control:
    identical inputs → different outputs → because different mass.
  
  Mass IS psychology. Mass IS the decision function's hidden variable.
""")


# =============================================================================
# SIM 3: KEY ROTATION (temporal hazard)
# =============================================================================

separator("SIM 3: KEY ROTATION (temporal hazard)")

print("A node that changes what it can decrypt over time.")
print("Like seasons changing. The node doesn't care. It just shifts.\n")

import time

rotating_node = Node(
    node_id="rotating",
    name="Rotating-Hazard",
    _key_secrets={"alpha": MASTER_SECRETS["alpha"]},  # starts with alpha only
    mass_window=(0, float('inf')),
)

# Schedule: at time T+0.1, gain beta key. At T+0.2, gain gamma key.
now = time.time()
schedule_key_rotation(rotating_node, "beta", [now - 1], lambda: MASTER_SECRETS["beta"])
schedule_key_rotation(rotating_node, "gamma", [now + 100], lambda: MASTER_SECRETS["gamma"])

# Before rotation
print(f"Before rotation: keys = {rotating_node.key_classes}")

agent1 = factory.build_mixed_agent({"alpha": (3, 0), "beta": (3, 0), "gamma": (3, 0)}, payload_size=32)
print(f"  Agent mass: {agent1.mass}")
result1 = rotating_node.process(agent1, factory)
print(f"  After interaction: mass={result1.mass_after} (stripped alpha only)")

# Apply rotation (beta key activates)
rotating_node.rotate_keys(now)
print(f"\nAfter rotation: keys = {rotating_node.key_classes}")

agent2 = factory.build_mixed_agent({"alpha": (3, 0), "beta": (3, 0), "gamma": (3, 0)}, payload_size=32)
print(f"  Agent mass: {agent2.mass}")
result2 = rotating_node.process(agent2, factory)
print(f"  After interaction: mass={result2.mass_after} (stripped alpha + beta)")

print(f"\n  Same node. Same agent composition. Different time. Different outcome.")
print(f"  The node didn't 'decide' to become more dangerous. It just... changed.")
print(f"  Weather doesn't decide to storm. It storms.")


# =============================================================================
# SIM 4: FULL LEDGER AUDIT
# =============================================================================

separator("SIM 4: FULL LEDGER AUDIT TRAIL")

# Commit everything
topo.commit_all()

print(f"Public Ledger State:")
print(f"  {topo.public_ledger.summary()}")

print(f"\nPer-node audit (PUBLIC VIEW — no transaction details):")
for node_id in ["start", "safe", "risky", "deadly"]:
    audit = topo.public_ledger.audit_node(node_id)
    if audit.get("activity") == "none":
        print(f"  {node_id}: no recorded activity")
    else:
        print(f"  {node_id}: {audit['total_transactions']} txns "
              f"in {audit['total_batches']} batches")

print(f"""
LEDGER ARCHITECTURE SUMMARY:
  ┌─────────────────────────────────────────────┐
  │  LOCAL LEDGER (per node, permissioned)       │
  │  Contains: full interaction records           │
  │  - agent_hash (not identity)                  │
  │  - mass_before, mass_after                    │
  │  - signal, loss, ΔL vector                    │
  │  - conservation validity                      │
  │  - timestamp                                  │
  │  Readable by: node operator, authorized audit │
  └───────────────────┬─────────────────────────┘
                      │ merkle root commit
                      ▼
  ┌─────────────────────────────────────────────┐
  │  PUBLIC LEDGER (append-only, immutable)       │
  │  Contains: commitment hashes ONLY             │
  │  - merkle_root of batch                       │
  │  - batch_size (transaction count)             │
  │  - time_range                                 │
  │  - node_id                                    │
  │  Readable by: anyone                          │
  │  Reveals: NOTHING about individual txns       │
  └─────────────────────────────────────────────┘

  Auditability:  Local entry → merkle proof → public root → trust
  Privacy:       Public sees hashes, not transactions
  Tamper-proof:  Modified local entry breaks merkle proof
  Non-surveillance: No agent identity in public ledger
""")


# =============================================================================
# SIM 5: NODE FORMALIZATION SUMMARY
# =============================================================================

separator("NODE: THE NATURAL OBJECT")

print("""
  A NODE IS:
  ══════════
  A location in topology with fixed (or rotating) physical properties.
  
  It has:
    1. Key affinity set    → what it CAN decrypt
    2. Mass window         → what it CAN admit  
    3. Interaction physics → the conservation law (C = C' + S + L)
    4. Ledger endpoint     → where transactions are recorded
    5. Accretion rules     → CAN it deposit mass? Under what conditions?
  
  It does NOT have:
    ✗ Intent
    ✗ Memory of past agents
    ✗ Prediction of future agents
    ✗ Preference for outcomes
    ✗ Awareness of its role
  
  A node is WEATHER.
  You prepare for weather. Weather doesn't prepare for you.
  
  Nature doesn't predict our behavior.
  Nature exists. We must be mindful.
  Nodes exist. Agents must be mindful.
  
  The node doesn't know what key classes an agent carries.
  The agent doesn't know what key classes a node holds.
  They interact. Conservation law governs. Physics decides.
  
  
  MULTI-CLASS KEY = HAZARDOUS ENVIRONMENT
  ═══════════════════════════════════════
  A node holding keys for multiple classes is like acid:
  it dissolves more of the agent per interaction.
  
  Hazard rating H = |node_keys| / |all_classes|
  
  H = 0.0 : Inert (safe passage, no decryption)
  H = 0.2 : Mild (decrypts one class)
  H = 0.6 : Corrosive (decrypts several classes)
  H = 1.0 : Universal solvent (decrypts everything → death)
  
  The node doesn't CHOOSE to be hazardous.
  It just IS. Like a volcano. Like deep water. Like vacuum.
""")
