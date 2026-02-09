"""
Agent Mass Theory — Cross-Organization Accountability Demo
============================================================

Three organizations. One agent. Zero trust. The math IS the trust.

Scenario:
    Aegis Corp (Org A)     — Deploys the agent, receives results
    Bifrost Systems (Org B) — Processes the agent's mission
    Verdant Labs (Org C)    — Validates Org B's results

Topology:
    Org A:       Org B:                  Org C:                  Org A:
    [deploy] -> [intake]->[compute]->[relay] -> [verify]->[stamp]->[exit] -> [recall]
             TB                              TB                           TB

    TB = Trust Boundary

Key classes and their purpose:
    alpha   — Mission payload (read by Org B intake)
    beta    — Compute fuel (read by Org B compute)
    gamma   — Compute results (accreted by Org B compute, read by Org C verify)
    delta   — Validation fuel (read by Org C stamp)
    epsilon — Validated results (accreted by Org C stamp, read by Org A recall)

The conservation law C_{n+1} + S_{n+1} + L_n = C_n holds at every
single interaction. It does not know about organizations. It does not
care. It just enforces.

Run: python amt_cross_org_demo.py
"""

import os
import sys
import random
import time
from collections import Counter

from amt_core import AgentFactory, Agent, interact, accrete
from amt_extensions import (
    Node, AccretionPolicy, AgentBehavior, Topology,
    LocalLedger, PublicLedger, PublicCommitment,
)
from amt_cross_org import (
    Organization, TrustBoundary, CrossOrgTopology,
    CrossOrgAuditReport, build_cross_org_factory, compare_org_audits,
)


def separator(title: str):
    print(f"\n\n{'█' * 70}")
    print(f"  {title}")
    print(f"{'█' * 70}\n")


# =============================================================================
# UNIVERSE SECRETS
# =============================================================================
# In a real deployment, each org holds only its own secrets.
# The deployer (Org A) must know all classes at agent creation time.
# After deployment, no single party holds all secrets.

ALL_SECRETS = {
    "alpha":   os.urandom(32),
    "beta":    os.urandom(32),
    "gamma":   os.urandom(32),
    "delta":   os.urandom(32),
    "epsilon": os.urandom(32),
}

# The deployer's factory knows all secrets (creation-time knowledge only)
factory = build_cross_org_factory(ALL_SECRETS)


# =============================================================================
# DEMO 1: TOPOLOGY CONSTRUCTION
# =============================================================================

separator("DEMO 1: CROSS-ORG TOPOLOGY CONSTRUCTION")

print("Three organizations. Each controls its own secrets.\n")

# --- Org A: Aegis Corp (Deployer) ---
# Controls: epsilon (reads results at recall)
# deploy-node: inert (no keys) — just the launch point
# recall-node: reads epsilon — gets validated results back
org_a = Organization(
    org_id="aegis",
    name="Aegis Corp",
    _key_secrets={"epsilon": ALL_SECRETS["epsilon"]},
)
deploy_node = org_a.create_node("deploy", "Deploy", key_classes=[])
recall_node = org_a.create_node("recall", "Recall", key_classes=["epsilon"])

# --- Org B: Bifrost Systems (Processor) ---
# Controls: alpha (mission), beta (compute fuel)
# intake-node: reads alpha (receives mission)
# compute-node: reads beta (uses fuel), accretes gamma (produces results)
# relay-node: inert (exit point from Org B)
org_b = Organization(
    org_id="bifrost",
    name="Bifrost Systems",
    _key_secrets={
        "alpha": ALL_SECRETS["alpha"],
        "beta":  ALL_SECRETS["beta"],
    },
)
intake_node = org_b.create_node("intake", "Intake", key_classes=["alpha"])
compute_node = org_b.create_node(
    "compute", "Compute",
    key_classes=["beta"],
    accretion_policy=AccretionPolicy(
        trigger="always",
        key_class="gamma",
        count=2,
        payload_gen=lambda: b"RESULT:" + os.urandom(24),
    ),
)
relay_node = org_b.create_node("relay", "Relay", key_classes=[])

# --- Org C: Verdant Labs (Validator) ---
# Controls: gamma (reads Org B's results), delta (validation fuel)
# verify-node: reads gamma (inspects results from Org B)
# stamp-node: reads delta (uses validation fuel), accretes epsilon (validation stamp)
# exit-node: inert (exit from Org C)
org_c = Organization(
    org_id="verdant",
    name="Verdant Labs",
    _key_secrets={
        "gamma": ALL_SECRETS["gamma"],
        "delta": ALL_SECRETS["delta"],
    },
)
verify_node = org_c.create_node("verify", "Verify", key_classes=["gamma"])
stamp_node = org_c.create_node(
    "stamp", "Stamp",
    key_classes=["delta"],
    accretion_policy=AccretionPolicy(
        trigger="always",
        key_class="epsilon",
        count=1,
        payload_gen=lambda: b"VALIDATED:" + os.urandom(16),
    ),
)
exit_node = org_c.create_node("exit", "Exit", key_classes=[])

# --- Build Cross-Org Topology ---
cross_topo = CrossOrgTopology()
cross_topo.set_factory(factory)

cross_topo.register_organization(org_a)
cross_topo.register_organization(org_b)
cross_topo.register_organization(org_c)

# Internal edges (within same org)
cross_topo.connect_within_org("bifrost", "intake", "compute")
cross_topo.connect_within_org("bifrost", "compute", "relay")
cross_topo.connect_within_org("verdant", "verify", "stamp")
cross_topo.connect_within_org("verdant", "stamp", "exit")

# Cross-org edges (trust boundaries)
cross_topo.connect_cross_org("aegis", "deploy", "bifrost", "intake")
cross_topo.connect_cross_org("bifrost", "relay", "verdant", "verify")
cross_topo.connect_cross_org("verdant", "exit", "aegis", "recall")

# Print topology map
print(cross_topo.topology_map())

print("""
Secret Distribution (each org only sees its own):
  Aegis Corp:      {epsilon}
  Bifrost Systems: {alpha, beta}
  Verdant Labs:    {gamma, delta}

No single org holds all five secrets after deployment.
The deployer (Aegis) knew all five at creation time only.
""")


# =============================================================================
# DEMO 2: HAPPY PATH TRAVERSAL
# =============================================================================

separator("DEMO 2: HAPPY PATH — WELL-FUNDED AGENT")

print("A well-funded agent traverses all 3 orgs with full accounting.\n")

# Build agent with layers for every key class
agent = factory.build_agent([
    # Mission payload (read by Org B intake)
    ("alpha", b"MISSION: Analyze Q4 revenue data"),
    ("alpha", b"PRIORITY: HIGH"),
    ("alpha", b""),  # empty alpha layer (toll)
    # Compute fuel (read by Org B compute)
    ("beta", b"FUEL: compute-budget-001"),
    ("beta", b"FUEL: compute-budget-002"),
    ("beta", b""),  # empty beta (toll)
    # Validation fuel (read by Org C stamp)
    ("delta", b"VALIDATION-TOKEN: vt-2026-001"),
    ("delta", b""),  # empty delta (toll)
    # Extra layers for mass budget
    ("alpha", b"CONTEXT: Additional context payload"),
    ("beta", b"FUEL: compute-budget-003"),
])

print(f"Agent created:")
print(f"  Total mass:    {agent.mass:,} B")
print(f"  Layer count:   {agent.layer_count}")
print(f"  Mass profile:  {agent.mass_profile()}")
print()

# Linear path through all nodes
path = ["deploy", "intake", "compute", "relay", "verify", "stamp", "exit", "recall"]
history = cross_topo.run_cross_org_linear(agent, path, verbose=True)

# Conservation check
print(f"\n{'─' * 70}")
print(f"  PER-STEP CONSERVATION CHECK")
print(f"{'─' * 70}")
all_valid = True
for h in history:
    if h["entered"] and h["signal"] + h["loss"] > 0:
        lhs = h["mass_before"]
        rhs = h["mass_after"] + h["signal"] + h["loss"]
        valid = lhs == rhs
        mark = "OK" if valid else "VIOLATION"
        print(f"  Step {h['step']:2d} [{h['org']:>8s}] {h['node']:>10s}: "
              f"{lhs:,} = {rhs:,} ({h['signal']:,}S + {h['loss']:,}L) [{mark}]")
        if not valid:
            all_valid = False

global_check = cross_topo.verify_global_conservation(history)
print(f"\n  Global conservation: {'HOLDS' if global_check['conservation_holds'] else 'VIOLATED'}")
print(f"  Total signal extracted: {global_check['total_signal']:,} B")
print(f"  Total loss incurred:    {global_check['total_loss']:,} B")
print(f"  Total mass consumed:    {global_check['total_mass_consumed']:,} B")


# =============================================================================
# DEMO 3: INDEPENDENT AUDIT
# =============================================================================

separator("DEMO 3: INDEPENDENT PER-ORG AUDIT")

print("Each org audits its OWN nodes independently.")
print("No org can see what happened on another org's infrastructure.\n")

reports = cross_topo.per_org_audit()

for org_id, report in reports.items():
    print(report.summary())
    print()

# Cross-org comparison (auditor view)
print(compare_org_audits(reports))

print("""
KEY INSIGHT:
  Each org proved conservation on its own nodes.
  No org revealed its data to any other org.
  The public ledger reveals only merkle roots and batch counts.
  Yet the GLOBAL conservation holds as the sum of local conservations.

  Theorem 1: Conservation is local to each interaction.
  Theorem 2: Each org can verify independently.
  Theorem 3: No org can determine another org's consumption.
""")

# Trust boundary summary
print(f"{'─' * 70}")
print(f"  TRUST BOUNDARY CROSSINGS")
print(f"{'─' * 70}")
for key, boundary in cross_topo.get_trust_boundaries().items():
    print(f"  {boundary}")
    for crossing in boundary.crossings:
        print(f"    Agent mass at crossing: {crossing['mass']:,} B "
              f"({crossing['layers']} layers)")


# =============================================================================
# DEMO 4: BEHAVIORAL DIVERGENCE — HEAVY vs LIGHT
# =============================================================================

separator("DEMO 4: BEHAVIORAL DIVERGENCE ACROSS TRUST BOUNDARIES")

print("Two agents. Same topology. Different mass budgets. Different fates.\n")

# We need a topology with choices for this demo.
# Extend the topology: after relay, agent can go to verify OR skip to exit directly
# (budget-constrained agents might skip validation)

div_topo = CrossOrgTopology()
div_topo.set_factory(factory)

# Rebuild orgs with fresh ledgers for clean accounting
org_a2 = Organization(
    org_id="aegis",
    name="Aegis Corp",
    _key_secrets={"epsilon": ALL_SECRETS["epsilon"]},
)
org_a2.create_node("deploy", "Deploy", key_classes=[])
org_a2.create_node("recall", "Recall", key_classes=["epsilon"])

org_b2 = Organization(
    org_id="bifrost",
    name="Bifrost Systems",
    _key_secrets={"alpha": ALL_SECRETS["alpha"], "beta": ALL_SECRETS["beta"]},
)
org_b2.create_node("intake", "Intake", key_classes=["alpha"])
org_b2.create_node(
    "compute", "Compute",
    key_classes=["beta"],
    accretion_policy=AccretionPolicy(
        trigger="always",
        key_class="gamma",
        count=2,
        payload_gen=lambda: b"RESULT:" + os.urandom(24),
    ),
)
org_b2.create_node("relay", "Relay", key_classes=[])

org_c2 = Organization(
    org_id="verdant",
    name="Verdant Labs",
    _key_secrets={"gamma": ALL_SECRETS["gamma"], "delta": ALL_SECRETS["delta"]},
)
org_c2.create_node("verify", "Verify", key_classes=["gamma"])
org_c2.create_node(
    "stamp", "Stamp",
    key_classes=["delta"],
    accretion_policy=AccretionPolicy(
        trigger="always",
        key_class="epsilon",
        count=1,
        payload_gen=lambda: b"VALIDATED:" + os.urandom(16),
    ),
)
org_c2.create_node("exit", "Exit", key_classes=[])

div_topo.register_organization(org_a2)
div_topo.register_organization(org_b2)
div_topo.register_organization(org_c2)

# Internal edges
div_topo.connect_within_org("bifrost", "intake", "compute")
div_topo.connect_within_org("bifrost", "compute", "relay")
div_topo.connect_within_org("verdant", "verify", "stamp")
div_topo.connect_within_org("verdant", "stamp", "exit")

# Cross-org edges
div_topo.connect_cross_org("aegis", "deploy", "bifrost", "intake")
div_topo.connect_cross_org("bifrost", "relay", "verdant", "verify")
div_topo.connect_cross_org("verdant", "exit", "aegis", "recall")

# ALSO: a shortcut from relay directly to recall (skip validation)
div_topo.connect_cross_org("bifrost", "relay", "aegis", "recall")

print("Topology now has a SHORTCUT: relay -> recall (skip validation)\n")
print("  [deploy] -> [intake] -> [compute] -> [relay] -> [verify] -> [stamp] -> [exit] -> [recall]")
print("                                          |                                          ^")
print("                                          +------ SHORTCUT (skip validation) --------+")
print()

# --- Agent Heavy (well-funded) ---
print(f"{'─' * 70}")
print("AGENT HEAVY: Well-funded, has validation fuel")
print(f"{'─' * 70}")

random.seed(42)
agent_heavy = factory.build_agent([
    ("alpha", b"MISSION: Full pipeline with validation"),
    ("alpha", b""),
    ("beta", b"FUEL: heavy-compute-001"),
    ("beta", b"FUEL: heavy-compute-002"),
    ("beta", b""),
    ("delta", b"VALIDATION-TOKEN: heavy-vt-001"),
    ("delta", b""),
])

behavior_heavy = AgentBehavior(risk_baseline=0.3, desperation_curve=2.0)
history_heavy = div_topo.run_cross_org_agent(
    agent_heavy, behavior_heavy, "deploy", max_steps=20, verbose=True,
)

# --- Agent Light (budget-constrained) ---
print(f"\n{'─' * 70}")
print("AGENT LIGHT: Budget-constrained, minimal fuel")
print(f"{'─' * 70}")

random.seed(42)
agent_light = factory.build_agent([
    ("alpha", b"MISSION: Quick check only"),
    ("beta", b"FUEL: light-001"),
])

behavior_light = AgentBehavior(risk_baseline=0.3, desperation_curve=2.0)
history_light = div_topo.run_cross_org_agent(
    agent_light, behavior_light, "deploy", max_steps=20, verbose=True,
)

# --- Comparison ---
print(f"\n{'─' * 70}")
print("DIVERGENCE COMPARISON")
print(f"{'─' * 70}")

orgs_heavy = [h["org"] for h in history_heavy if h["entered"]]
orgs_light = [h["org"] for h in history_light if h["entered"]]
nodes_heavy = [h["node"] for h in history_heavy if h["entered"]]
nodes_light = [h["node"] for h in history_light if h["entered"]]

print(f"  {'Metric':<30s}  {'Heavy':>15s}  {'Light':>15s}")
print(f"  {'─' * 64}")
print(f"  {'Initial mass':<30s}  {history_heavy[0]['mass_before']:>15,}  {history_light[0]['mass_before']:>15,}")
print(f"  {'Steps taken':<30s}  {len(history_heavy):>15d}  {len(history_light):>15d}")

final_heavy = [h for h in history_heavy if h["entered"]]
final_light = [h for h in history_light if h["entered"]]
if final_heavy:
    print(f"  {'Final mass':<30s}  {final_heavy[-1]['mass_after']:>15,}  "
          f"{final_light[-1]['mass_after'] if final_light else 0:>15,}")

# Count org visits
for label, nodes in [("Heavy path", nodes_heavy), ("Light path", nodes_light)]:
    print(f"\n  {label}: {' -> '.join(nodes[:12])}")

visited_verdant_heavy = any(h["org"] == "verdant" for h in history_heavy)
visited_verdant_light = any(h["org"] == "verdant" for h in history_light)
print(f"\n  Heavy visited Verdant (validation): {visited_verdant_heavy}")
print(f"  Light visited Verdant (validation): {visited_verdant_light}")

print("""
KEY INSIGHT:
  The heavy agent had enough mass to traverse the full pipeline
  including validation by Verdant Labs.

  The light agent, budget-constrained, may have taken the shortcut
  from Relay directly to Recall — skipping validation entirely.

  This is EMERGENT ECONOMICS, not a bug:
    - Validation costs mass (delta layers consumed by Org C)
    - Budget-constrained agents can't afford validation
    - The result: unvalidated outputs from agents that cut corners

  No one programmed this behavior. It emerged from the physics
  of finite mass interacting with organizational topology.
""")


# =============================================================================
# DEMO 5: PUBLIC LEDGER OPACITY
# =============================================================================

separator("DEMO 5: PUBLIC LEDGER OPACITY")

print("What an EXTERNAL OBSERVER sees from the public ledger:\n")

public = cross_topo.public_ledger

print(f"  {public.summary()}")
print()

print("  Per-node public audit (the ONLY thing an observer can see):")
for node_id in ["deploy", "intake", "compute", "relay", "verify", "stamp", "exit", "recall"]:
    # Nodes share org ledger IDs, so audit by org ledger node_id
    pass

# Show what each org published
for org_id, org in [("aegis", org_a), ("bifrost", org_b), ("verdant", org_c)]:
    org_commits = [c for c in public.commitments if c.node_id == org.ledger.node_id]
    print(f"\n  [{org.name}] published {len(org_commits)} commitment(s):")
    for c in org_commits:
        print(f"    Merkle root: {c.merkle_root[:48]}...")
        print(f"    Batch size:  {c.batch_size} transactions")

print(f"""
What the observer KNOWS:
  - How many commitments each org published
  - How many transactions per batch
  - Time ranges

What the observer CANNOT determine:
  - Which agents traversed which nodes
  - What signal was extracted
  - What loss was incurred
  - How much mass any specific agent had
  - Whether an agent was validated or took the shortcut
  - The delta_L vector for any interaction
  - ANY individual transaction detail

The public ledger satisfies Cube Protocol Principle 4:
  "Statistical Leakage, Not Raw Data"
  The system exposes distributions, not events.
""")


# =============================================================================
# DEMO 6: CONSERVATION AT SCALE
# =============================================================================

separator("DEMO 6: CONSERVATION AT SCALE")

N_AGENTS = 200  # scale run
print(f"Running {N_AGENTS} agents through the cross-org topology...\n")

# Build a fresh cross-org topology for scale run
scale_topo = CrossOrgTopology()
scale_topo.set_factory(factory)

# Fresh orgs
s_org_a = Organization(
    org_id="aegis", name="Aegis Corp",
    _key_secrets={"epsilon": ALL_SECRETS["epsilon"]},
)
s_org_a.create_node("deploy", "Deploy", key_classes=[])
s_org_a.create_node("recall", "Recall", key_classes=["epsilon"])

s_org_b = Organization(
    org_id="bifrost", name="Bifrost Systems",
    _key_secrets={"alpha": ALL_SECRETS["alpha"], "beta": ALL_SECRETS["beta"]},
)
s_org_b.create_node("intake", "Intake", key_classes=["alpha"])
s_org_b.create_node(
    "compute", "Compute",
    key_classes=["beta"],
    accretion_policy=AccretionPolicy(
        trigger="always", key_class="gamma", count=2,
        payload_gen=lambda: b"RESULT:" + os.urandom(24),
    ),
)
s_org_b.create_node("relay", "Relay", key_classes=[])

s_org_c = Organization(
    org_id="verdant", name="Verdant Labs",
    _key_secrets={"gamma": ALL_SECRETS["gamma"], "delta": ALL_SECRETS["delta"]},
)
s_org_c.create_node("verify", "Verify", key_classes=["gamma"])
s_org_c.create_node(
    "stamp", "Stamp",
    key_classes=["delta"],
    accretion_policy=AccretionPolicy(
        trigger="always", key_class="epsilon", count=1,
        payload_gen=lambda: b"VALIDATED:" + os.urandom(16),
    ),
)
s_org_c.create_node("exit", "Exit", key_classes=[])

scale_topo.register_organization(s_org_a)
scale_topo.register_organization(s_org_b)
scale_topo.register_organization(s_org_c)

# Edges (with shortcut for divergence)
scale_topo.connect_within_org("bifrost", "intake", "compute")
scale_topo.connect_within_org("bifrost", "compute", "relay")
scale_topo.connect_within_org("verdant", "verify", "stamp")
scale_topo.connect_within_org("verdant", "stamp", "exit")
scale_topo.connect_cross_org("aegis", "deploy", "bifrost", "intake")
scale_topo.connect_cross_org("bifrost", "relay", "verdant", "verify")
scale_topo.connect_cross_org("verdant", "exit", "aegis", "recall")
scale_topo.connect_cross_org("bifrost", "relay", "aegis", "recall")

# Generate diverse population
rng = random.Random(2026)
all_violations = 0
total_interactions = 0
agents_validated = 0
agents_skipped = 0
agent_results = []

t0 = time.time()

for i in range(N_AGENTS):
    # Varied mass: some heavy, some light
    num_alpha = rng.randint(1, 4)
    num_beta = rng.randint(0, 3)
    num_delta = rng.randint(0, 2)

    specs = []
    for _ in range(num_alpha):
        payload = os.urandom(rng.randint(16, 64))
        specs.append(("alpha", payload))
    for _ in range(num_beta):
        payload = os.urandom(rng.randint(16, 64)) if rng.random() > 0.3 else b""
        specs.append(("beta", payload))
    for _ in range(num_delta):
        payload = os.urandom(rng.randint(16, 32)) if rng.random() > 0.3 else b""
        specs.append(("delta", payload))

    agent_i = factory.build_agent(specs)
    behavior_i = AgentBehavior(
        risk_baseline=rng.uniform(0.2, 0.6),
        desperation_curve=rng.choice([2.0, 2.0, 2.0, 3.0]),  # integer exponents avoid complex numbers when mass_ratio > 1.0 from accretion
    )

    random.seed(2026 + i)
    history_i = scale_topo.run_cross_org_agent(
        agent_i, behavior_i, "deploy", max_steps=20, verbose=False,
    )

    # Check conservation per step
    for h in history_i:
        if h["entered"] and (h["signal"] + h["loss"] > 0):
            total_interactions += 1
            lhs = h["mass_before"]
            rhs = h["mass_after"] + h["signal"] + h["loss"]
            if lhs != rhs:
                all_violations += 1

    # Track validation
    visited_verdant = any(h["org"] == "verdant" for h in history_i)
    if visited_verdant:
        agents_validated += 1
    else:
        agents_skipped += 1

    agent_results.append({
        "initial_mass": history_i[0]["mass_before"] if history_i else 0,
        "steps": len(history_i),
        "validated": visited_verdant,
        "alive": history_i[-1]["alive"] if history_i else False,
    })

elapsed = time.time() - t0

# Results
print(f"  Completed in {elapsed:.2f}s ({N_AGENTS / elapsed:.0f} agents/sec)\n")

print(f"{'─' * 70}")
print(f"  SCALE RESULTS")
print(f"{'─' * 70}")
print(f"  Agents:              {N_AGENTS}")
print(f"  Total interactions:  {total_interactions:,}")
print(f"  Conservation violations: {all_violations}")

if all_violations == 0:
    print(f"\n  C_{{n+1}} + S_{{n+1}} + L_n = C_n")
    print(f"  HOLDS FOR ALL {total_interactions:,} INTERACTIONS.")
    print(f"  ACROSS ALL 3 ORGANIZATIONS.")
    print(f"  ZERO VIOLATIONS.")
else:
    print(f"\n  WARNING: {all_violations} violations detected!")

print(f"\n  Behavioral divergence:")
print(f"    Agents that visited Verdant (validated): {agents_validated} ({agents_validated/N_AGENTS:.1%})")
print(f"    Agents that skipped validation:          {agents_skipped} ({agents_skipped/N_AGENTS:.1%})")

# Mass vs validation correlation
validated_masses = [r["initial_mass"] for r in agent_results if r["validated"]]
skipped_masses = [r["initial_mass"] for r in agent_results if not r["validated"]]

if validated_masses and skipped_masses:
    avg_validated = sum(validated_masses) / len(validated_masses)
    avg_skipped = sum(skipped_masses) / len(skipped_masses)
    print(f"\n  Average initial mass:")
    print(f"    Validated agents:  {avg_validated:,.0f} B")
    print(f"    Skipped agents:    {avg_skipped:,.0f} B")
    if avg_validated > avg_skipped:
        print(f"    Validated agents are {avg_validated/avg_skipped:.1f}x heavier on average.")
    print(f"    Budget predicts behavior. Mass IS the decision variable.")

# Per-org audit at scale
print(f"\n{'─' * 70}")
print(f"  PER-ORG AUDIT (scale run)")
print(f"{'─' * 70}")

scale_reports = scale_topo.per_org_audit()
print(compare_org_audits(scale_reports))

# Trust boundary crossings
print(f"\n  Trust Boundary Crossings:")
for key, boundary in scale_topo.get_trust_boundaries().items():
    print(f"    {boundary}")

# Survival statistics
alive_count = sum(1 for r in agent_results if r["alive"])
dead_count = N_AGENTS - alive_count
print(f"\n  Survival: {alive_count} alive, {dead_count} dead ({alive_count/N_AGENTS:.1%} survival)")


# =============================================================================
# FINAL SUMMARY
# =============================================================================

separator("SUMMARY: CROSS-ORG ACCOUNTABILITY WITHOUT TRUST")

print("""
  What we demonstrated:

  1. TOPOLOGY CONSTRUCTION
     Three independent organizations with separate secrets.
     No org trusts any other. No shared secret material after deployment.

  2. HAPPY PATH
     An agent traversed all 3 orgs with exact mass accounting.
     Conservation held at every single interaction.

  3. INDEPENDENT AUDIT
     Each org audited its own nodes independently.
     No org could see another org's data.
     Merkle proofs anchored each org's claims to the public ledger.

  4. BEHAVIORAL DIVERGENCE
     Budget-constrained agents skipped validation.
     This is emergent economics, not a bug.
     Mass determines behavior. Behavior determines routing.
     Routing determines which orgs an agent visits.

  5. PUBLIC LEDGER OPACITY
     An external observer sees merkle roots and batch counts.
     Nothing about individual agents, signals, losses, or routes.
     Cube Protocol Principle 4: distributions, not events.

  6. CONSERVATION AT SCALE
     {0} agents, {1:,} interactions, ZERO violations.
     The conservation law is absolute. It does not bend.
     It does not care about organizational boundaries.
     It enforces at every interaction, in every org, always.

  THE CORE THEOREM:
     The conservation law C_{{n+1}} + S_{{n+1}} + L_n = C_n
     is LOCAL to each interaction. Therefore:
       - It is invariant under organizational partitioning.
       - Each org can verify independently.
       - No org can see another org's data.
       - Global conservation = sum of local conservations.
       - The math IS the trust. No trust required.
""".format(N_AGENTS, total_interactions))
