"""
Agent Mass Theory — Extension Module
======================================

Extends amt_core.py with:
    §1  LEDGER ARCHITECTURE (local permissioned + public commits)
    §2  NODE FORMALIZATION (the natural object)
    §3  BEHAVIORAL DIVERGENCE (mass-dependent decision making)
    §4  KEY ROTATION (temporal environmental hazard)

Dependencies: amt_core.py
"""

import os
import time
import json
import math
import hashlib
import random
from dataclasses import dataclass, field
from typing import Optional, Callable
from amt_core import (
    Agent, Layer, Environment, AgentFactory,
    InteractionResult, DecryptionResult,
    interact, hazard_rating, derive_key, encrypt_layer,
)


# =============================================================================
# §1  LEDGER ARCHITECTURE
# =============================================================================
#
# Design Principle (from Cube Protocol §4 — Statistical Leakage):
#   "The system exposes distributions, not events."
#
# Two-tier ledger:
#   LOCAL LEDGER  — Full interaction records. Permissioned. Only the
#                   node operator and authorized auditors can read.
#                   Contains: agent_id, mass_before, mass_after, signal,
#                   loss, ΔL, timestamp, node_id.
#
#   PUBLIC LEDGER — Commitment hashes only. Append-only. Immutable.
#                   Contains: merkle_root of batched local entries,
#                   batch_size, timestamp, node_id.
#                   NO raw data. NO agent identifiers. NO signal content.
#
# This gives:
#   - Auditability:  Any local record can be proven to exist in the
#                     public ledger via merkle proof.
#   - Privacy:        Public observers see commitment hashes, not transactions.
#   - Trust:          Local ledger tampering is detectable — the public
#                     commitment won't match.
#   - Non-surveillance: Satisfies Cube Protocol Principle 5 (Exit Leakage) —
#                        no global state reveals participation patterns.
#
# =============================================================================

@dataclass
class LedgerEntry:
    """
    A single interaction record in the local ledger.
    
    This is the FULL record — signal content, loss vectors,
    everything. It lives only on the local permissioned ledger.
    It never touches the public chain in raw form.
    """
    entry_id: str
    timestamp: float
    node_id: str
    agent_hash: str         # hash of agent's mass state (NOT identity)
    mass_before: int
    mass_after: int
    signal: int
    loss: int
    delta_L: dict[str, float]
    layers_stripped: int
    conservation_valid: bool
    
    def to_bytes(self) -> bytes:
        """Serialize for hashing. Deterministic byte representation."""
        canonical = json.dumps({
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "agent_hash": self.agent_hash,
            "mass_before": self.mass_before,
            "mass_after": self.mass_after,
            "signal": self.signal,
            "loss": self.loss,
            "delta_L": dict(sorted(self.delta_L.items())),
            "layers_stripped": self.layers_stripped,
            "conservation_valid": self.conservation_valid,
        }, sort_keys=True, separators=(",", ":"))
        return canonical.encode()
    
    @property
    def hash(self) -> str:
        """SHA-256 hash of this entry."""
        return hashlib.sha256(self.to_bytes()).hexdigest()


@dataclass
class PublicCommitment:
    """
    A commitment published to the public ledger.
    
    Contains ONLY:
    - Merkle root of a batch of local entries
    - Batch metadata (count, time range)
    - Node identifier
    
    Does NOT contain:
    - Any agent information
    - Any signal content
    - Any loss vectors
    - Any individual transaction data
    """
    merkle_root: str
    batch_size: int
    timestamp: float
    node_id: str
    time_range: tuple[float, float]  # (earliest, latest) entry timestamps
    
    def __repr__(self):
        return (f"PublicCommitment(root={self.merkle_root[:16]}..., "
                f"batch={self.batch_size}, node={self.node_id})")


def merkle_root(hashes: list[str]) -> str:
    """
    Compute merkle root from a list of hex hash strings.
    
    Standard binary merkle tree. If odd number of leaves,
    the last leaf is duplicated.
    """
    if not hashes:
        return hashlib.sha256(b"empty").hexdigest()
    
    level = [bytes.fromhex(h) for h in hashes]
    
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            combined = hashlib.sha256(left + right).digest()
            next_level.append(combined)
        level = next_level
    
    return level[0].hex()


def merkle_proof(hashes: list[str], index: int) -> list[tuple[str, str]]:
    """
    Generate a merkle proof for entry at `index`.
    
    Returns list of (sibling_hash, side) pairs where side is 'L' or 'R'.
    This proof allows anyone to verify that a specific local entry
    is included in the public commitment without seeing other entries.
    """
    if not hashes or index >= len(hashes):
        return []
    
    level = [bytes.fromhex(h) for h in hashes]
    proof = []
    idx = index
    
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            
            if i == idx or i + 1 == idx:
                if idx % 2 == 0:
                    sibling = right if i + 1 < len(level) else left
                    proof.append((sibling.hex(), 'R'))
                else:
                    proof.append((left.hex(), 'L'))
            
            combined = hashlib.sha256(left + right).digest()
            next_level.append(combined)
        
        idx = idx // 2
        level = next_level
    
    return proof


class LocalLedger:
    """
    The local permissioned ledger. Full transaction records.
    
    Operated by the node. Readable by authorized auditors.
    Periodically committed to the public ledger via merkle root.
    """
    
    def __init__(self, node_id: str, batch_size: int = 10):
        self.node_id = node_id
        self.batch_size = batch_size
        self.entries: list[LedgerEntry] = []
        self._uncommitted: list[LedgerEntry] = []
        self.commitments: list[PublicCommitment] = []
    
    def record(self, result: InteractionResult, agent: Agent) -> LedgerEntry:
        """
        Record an interaction in the local ledger.
        
        The agent_hash is a hash of the agent's current mass state —
        NOT an identity. Two agents with identical mass states produce
        the same hash. This is deliberate: it provides auditability
        without attribution.
        """
        # Agent hash: hash of total mass + layer count (not layer contents)
        agent_state = f"{agent.mass}:{agent.layer_count}".encode()
        agent_hash = hashlib.sha256(agent_state).hexdigest()[:16]
        
        entry = LedgerEntry(
            entry_id=os.urandom(16).hex(),
            timestamp=time.time(),
            node_id=self.node_id,
            agent_hash=agent_hash,
            mass_before=result.mass_before,
            mass_after=result.mass_after,
            signal=result.total_signal,
            loss=result.total_loss,
            delta_L=result.delta_L,
            layers_stripped=result.layers_stripped,
            conservation_valid=(
                result.mass_before == result.mass_after + result.total_signal + result.total_loss
            ),
        )
        
        self.entries.append(entry)
        self._uncommitted.append(entry)
        
        # Auto-commit when batch is full
        if len(self._uncommitted) >= self.batch_size:
            self.commit()
        
        return entry
    
    def commit(self) -> Optional[PublicCommitment]:
        """
        Commit current batch to public ledger.
        
        Computes merkle root of uncommitted entries and produces
        a PublicCommitment. The raw entries stay local. Only the
        root goes public.
        """
        if not self._uncommitted:
            return None
        
        hashes = [entry.hash for entry in self._uncommitted]
        root = merkle_root(hashes)
        
        timestamps = [e.timestamp for e in self._uncommitted]
        
        commitment = PublicCommitment(
            merkle_root=root,
            batch_size=len(self._uncommitted),
            timestamp=time.time(),
            node_id=self.node_id,
            time_range=(min(timestamps), max(timestamps)),
        )
        
        self.commitments.append(commitment)
        self._uncommitted = []
        
        return commitment
    
    def verify_entry(self, entry: LedgerEntry, commitment: PublicCommitment) -> bool:
        """
        Verify that a local entry is included in a public commitment.
        
        This is the audit function: given a local record and a public
        commitment, prove the record was included without revealing
        other records in the batch.
        """
        # Find the batch that contains this entry
        batch_entries = [e for e in self.entries 
                        if commitment.time_range[0] <= e.timestamp <= commitment.time_range[1]]
        
        if entry not in batch_entries:
            return False
        
        hashes = [e.hash for e in batch_entries]
        computed_root = merkle_root(hashes)
        
        return computed_root == commitment.merkle_root
    
    def summary(self) -> str:
        lines = [
            f"LocalLedger({self.node_id})",
            f"  Total entries:    {len(self.entries)}",
            f"  Uncommitted:      {len(self._uncommitted)}",
            f"  Commitments:      {len(self.commitments)}",
        ]
        if self.commitments:
            lines.append(f"  Latest root:      {self.commitments[-1].merkle_root[:32]}...")
        return "\n".join(lines)


class PublicLedger:
    """
    The public append-only ledger. Commitment hashes only.
    
    Anyone can read this. No one can learn individual transactions
    from it. It exists solely to anchor trust: if the local ledger
    is tampered with, the public commitment won't match.
    """
    
    def __init__(self):
        self.commitments: list[PublicCommitment] = []
    
    def publish(self, commitment: PublicCommitment):
        """Append a commitment. Immutable once published."""
        self.commitments.append(commitment)
    
    def audit_node(self, node_id: str) -> dict:
        """
        Public audit of a node's activity.
        
        Returns ONLY:
        - Number of batches committed
        - Total transactions committed (count only)
        - Time range of activity
        
        Does NOT return:
        - Any transaction content
        - Any agent information
        - Any signal or loss data
        """
        node_commits = [c for c in self.commitments if c.node_id == node_id]
        
        if not node_commits:
            return {"node_id": node_id, "activity": "none"}
        
        return {
            "node_id": node_id,
            "total_batches": len(node_commits),
            "total_transactions": sum(c.batch_size for c in node_commits),
            "first_activity": min(c.time_range[0] for c in node_commits),
            "last_activity": max(c.time_range[1] for c in node_commits),
        }
    
    def summary(self) -> str:
        nodes = set(c.node_id for c in self.commitments)
        total_txns = sum(c.batch_size for c in self.commitments)
        return (f"PublicLedger: {len(self.commitments)} commitments, "
                f"{total_txns} transactions, {len(nodes)} nodes")


# =============================================================================
# §2  NODE FORMALIZATION
# =============================================================================
#
# A Node is a NATURAL OBJECT. It does not predict. It does not
# anticipate. It does not strategize. It has properties. Those
# properties interact with whatever enters.
#
# Gravity doesn't predict what it'll attract. It just pulls.
# A node doesn't predict what agents will arrive. It just decrypts
# what it has keys for, and blocks what doesn't fit.
#
# A Node is defined by:
#   1. Key affinity set    — what it CAN decrypt (immutable or rotating)
#   2. Mass window         — what it CAN admit (physical topology)
#   3. Interaction physics — HOW it transforms (the conservation law)
#   4. Ledger              — WHERE transactions are recorded
#   5. Accretion policy    — CAN it feed agents? Under what conditions?
#
# A Node does NOT have:
#   - Intent
#   - Memory of past agents
#   - Prediction of future agents  
#   - Preference for outcomes
#   - Awareness of its own role in any larger system
#
# A Node is weather. You prepare for it. It doesn't prepare for you.
#
# =============================================================================

@dataclass
class AccretionPolicy:
    """
    Defines if and how a node can add mass to an agent.
    
    A node may accrete layers onto agents as a natural byproduct
    of interaction — like a river depositing sediment. This is not
    a "reward" from the node's perspective. The node has no perspective.
    It is a physical process.
    
    Conditions:
        trigger:     "always" | "signal_threshold" | "survival" | "never"
        key_class:   What class of layer to accrete
        count:       How many layers to add
        payload_gen: Function that generates payload bytes (or None for empty)
    """
    trigger: str = "never"                          # when to accrete
    key_class: str = ""                             # class of accreted layers
    count: int = 0                                  # layers to add
    payload_gen: Optional[Callable] = None          # payload generator
    signal_threshold: float = 0.0                   # for signal_threshold trigger
    min_survival_mass: int = 0                      # for survival trigger


@dataclass
class Node:
    """
    A Node is a natural object in the agent topology.
    
    It exists. It has properties. Agents interact with it.
    It does not care. It does not choose. It does not know.
    
    Like weather. Like terrain. Like gravity.
    
    Properties are either STATIC (fixed at creation) or
    ROTATING (change on a schedule, indifferent to agents).
    """
    
    # --- Identity (for ledger purposes, not consciousness) ---
    node_id: str
    name: str
    
    # --- Physical properties ---
    _key_secrets: dict[str, bytes] = field(default_factory=dict)
    mass_window: tuple[int, int] = (0, float('inf'))
    
    # --- Accretion (sediment deposit, not reward) ---
    accretion_policy: AccretionPolicy = field(default_factory=AccretionPolicy)
    
    # --- Key rotation schedule (temporal hazard) ---
    _key_rotation_schedule: dict[str, list[tuple[float, bytes]]] = field(
        default_factory=dict, repr=False
    )
    
    # --- Ledger ---
    ledger: LocalLedger = field(default=None)
    
    def __post_init__(self):
        if self.ledger is None:
            self.ledger = LocalLedger(self.node_id)
    
    @property
    def key_classes(self) -> set[str]:
        """Current key affinity set."""
        return set(self._key_secrets.keys())
    
    @property
    def hazard_classes(self) -> int:
        return len(self._key_secrets)
    
    def as_environment(self) -> Environment:
        """
        Project this Node into an Environment for the interaction engine.
        """
        return Environment(
            name=self.name,
            secrets=dict(self._key_secrets),
            mass_threshold=self.mass_window,
        )
    
    def rotate_keys(self, current_time: float):
        """
        Apply key rotation if scheduled.
        
        Key rotation is NOT a response to agents. It is a natural
        process — like seasons changing, tides shifting. The node
        rotates its keys on its own schedule, indifferent to what
        agents are present or expected.
        
        After rotation, layers that were previously safe in this
        node's environment may become vulnerable, and vice versa.
        This is the temporal hazard.
        """
        for key_class, schedule in self._key_rotation_schedule.items():
            for rotation_time, new_secret in schedule:
                if current_time >= rotation_time:
                    self._key_secrets[key_class] = new_secret
    
    def process(self, agent: Agent, factory: AgentFactory = None) -> InteractionResult:
        """
        The node processes an agent. This is the fundamental interaction.
        
        Steps:
            1. Exist (the node already has its properties)
            2. Agent enters (or is blocked by mass gate)
            3. Decrypt whatever the node has affinity for
            4. Record transaction in local ledger
            5. Apply accretion if conditions met (natural process)
            6. Return result
        
        The node does not "decide" to do any of this.
        It happens because physics.
        """
        env = self.as_environment()
        result = interact(agent, env)
        
        # Record in ledger
        if result.agent_could_enter:
            self.ledger.record(result, agent)
        
        # Accretion — natural deposit, not reward
        if (result.agent_could_enter and 
            agent.alive and 
            factory is not None and
            self.accretion_policy.trigger != "never"):
            
            should_accrete = False
            policy = self.accretion_policy
            
            if policy.trigger == "always":
                should_accrete = True
            elif policy.trigger == "signal_threshold":
                should_accrete = result.signal_ratio >= policy.signal_threshold
            elif policy.trigger == "survival":
                should_accrete = agent.mass <= policy.min_survival_mass
            
            if should_accrete and policy.key_class and policy.count > 0:
                for _ in range(policy.count):
                    payload = policy.payload_gen() if policy.payload_gen else b""
                    try:
                        layer = factory.create_layer(policy.key_class, payload)
                        agent.layers.append(layer)
                    except ValueError:
                        pass  # Factory doesn't know this key class
        
        return result
    
    def __repr__(self):
        return (f"Node({self.name}, keys={self.key_classes}, "
                f"window={self.mass_window}, hazard={self.hazard_classes})")


# =============================================================================
# §3  BEHAVIORAL DIVERGENCE — MASS AS PSYCHOLOGY
# =============================================================================
#
# THESIS: Two agents presented with identical environmental state
# will make different decisions based on remaining mass.
#
# This is the internal locus of control. Mass IS psychology.
#
# An agent low on mass will make desperate decisions that a
# massive agent would not. This is not programmed desperation —
# it is EMERGENT from the physics of finite energy.
#
# The agent observes:
#   - remaining_mass (scalar) — "how much am I?"
#   - mass_delta (scalar) — "how much did that cost me?"
#   - alive (boolean) — "do I still exist?"
#
# From these, the agent can compute:
#   - survival_pressure = mass_delta / remaining_mass
#   - burn_rate (if it tracks history) = avg(mass_deltas) over recent interactions
#   - estimated_remaining_interactions = remaining_mass / burn_rate
#
# The DECISION FUNCTION maps these observables to a choice of
# next node from available options.
#
# =============================================================================

@dataclass
class AgentBehavior:
    """
    The behavioral layer of an agent. This sits OUTSIDE the mass
    payload — it is how the agent interprets its own depletion.
    
    The agent cannot see:
        - Its layer composition
        - Which layers were stripped
        - What key classes it carries
        - The ΔL vector (that's external measurement)
    
    The agent CAN see:
        - Its total mass (scalar)
        - Mass change after each interaction (scalar)
        - Whether it's alive
    
    From these minimal observables, behavior emerges.
    """
    
    # --- Observable history (what the agent can actually see) ---
    mass_history: list[int] = field(default_factory=list)
    
    # --- Behavioral parameters (the agent's "personality") ---
    risk_baseline: float = 0.5      # base risk tolerance [0, 1]
    desperation_curve: float = 2.0  # how sharply desperation scales
    
    @property
    def current_mass(self) -> int:
        return self.mass_history[-1] if self.mass_history else 0
    
    @property
    def initial_mass(self) -> int:
        return self.mass_history[0] if self.mass_history else 0
    
    @property
    def mass_ratio(self) -> float:
        """Remaining mass as fraction of initial. 1.0 = full, 0.0 = dead."""
        if self.initial_mass == 0:
            return 0.0
        return self.current_mass / self.initial_mass
    
    @property
    def survival_pressure(self) -> float:
        """
        How much pressure the agent is under. [0, ∞)
        
        0.0 = no pressure (no mass lost or infinite mass)
        1.0 = moderate (lost as much as it has left)
        >1  = critical (lost more than it has left)
        ∞   = dead
        
        Computed from most recent delta relative to remaining mass.
        """
        if len(self.mass_history) < 2:
            return 0.0
        if self.current_mass == 0:
            return float('inf')
        
        last_delta = self.mass_history[-2] - self.mass_history[-1]
        return last_delta / self.current_mass
    
    @property
    def burn_rate(self) -> float:
        """Average mass consumed per interaction."""
        if len(self.mass_history) < 2:
            return 0.0
        deltas = [
            self.mass_history[i] - self.mass_history[i + 1]
            for i in range(len(self.mass_history) - 1)
        ]
        return sum(deltas) / len(deltas)
    
    @property
    def estimated_remaining_interactions(self) -> float:
        """How many more interactions the agent can survive at current burn rate."""
        if self.burn_rate <= 0:
            return float('inf')
        return self.current_mass / self.burn_rate
    
    @property 
    def risk_tolerance(self) -> float:
        """
        Dynamic risk tolerance based on remaining mass.
        
        This is where mass becomes psychology.
        
        When mass_ratio is high (agent is heavy/healthy):
            risk_tolerance ≈ risk_baseline (moderate, considered)
        
        When mass_ratio approaches 0 (agent is dying):
            risk_tolerance → 1.0 (desperate, will try anything)
        
        The desperation_curve controls how sharply this transitions.
        Higher curve = more sudden desperation onset.
        
        Formula:
            risk_tolerance = risk_baseline + (1 - risk_baseline) * (1 - mass_ratio)^desperation_curve
        
        This means:
            - At 100% mass: risk = baseline (e.g., 0.5)
            - At 50% mass:  risk = baseline + small increase
            - At 10% mass:  risk = nearly 1.0 (desperate)
            - At 1% mass:   risk ≈ 1.0 (nothing left to lose)
        """
        if self.mass_ratio <= 0:
            return 1.0
        
        depletion = 1.0 - self.mass_ratio
        desperation = depletion ** self.desperation_curve
        
        return min(1.0, self.risk_baseline + (1.0 - self.risk_baseline) * desperation)
    
    def observe(self, agent: Agent):
        """Record current mass observation."""
        self.mass_history.append(agent.mass)
    
    def choose_node(self, available_nodes: list[Node], agent: Agent) -> Optional[Node]:
        """
        Choose next node from available options.
        
        This is the DECISION FUNCTION. It demonstrates how identical
        environmental options produce different choices based on mass.
        
        Strategy:
            - Compute hazard rating for each node
            - Low risk tolerance → prefer low-hazard nodes
            - High risk tolerance → willing to enter high-hazard nodes
              (because: might find accretion, or nothing left to lose)
            - Mass-gated nodes that don't fit are excluded
        
        The agent doesn't know WHY a node is hazardous (it can't see
        key classes). It can only estimate hazard from:
            - Mass window (observable)
            - Previous experience (mass delta history)
        
        For this reference implementation, we use hazard_rating as
        a proxy for what the agent would learn through experience.
        In a real system, the agent would build a model from
        mass deltas alone.
        """
        if not available_nodes:
            return None
        
        # Filter: can the agent physically enter?
        viable = [n for n in available_nodes if n.as_environment().can_enter(agent)]
        
        if not viable:
            return None
        
        risk = self.risk_tolerance
        
        # Score each node: higher score = more attractive
        scored = []
        for node in viable:
            hazard = hazard_rating(node.as_environment(), agent)
            lethality = hazard["lethality"]
            
            # Conservative agents avoid lethality.
            # Desperate agents don't care — they might even prefer it
            # (high lethality nodes might also have accretion).
            
            if risk < 0.3:
                # Conservative: strongly prefer low lethality
                score = 1.0 - lethality
            elif risk < 0.7:
                # Moderate: balanced consideration
                score = 1.0 - (lethality * (1.0 - risk))
            else:
                # Desperate: lethality barely matters
                # Slight preference for extremes (all or nothing)
                score = 0.5 + random.uniform(-0.3, 0.3)
            
            scored.append((node, score))
        
        # Select: weighted random based on scores
        # (not argmax — agents are not perfectly rational)
        total_score = sum(max(0.01, s) for _, s in scored)
        r = random.uniform(0, total_score)
        cumulative = 0
        for node, score in scored:
            cumulative += max(0.01, score)
            if cumulative >= r:
                return node
        
        return scored[-1][0]  # fallback
    
    def state_report(self) -> str:
        """What the agent 'knows' about itself."""
        lines = [
            f"  Mass:              {self.current_mass:,} B",
            f"  Initial mass:      {self.initial_mass:,} B",
            f"  Mass ratio:        {self.mass_ratio:.1%}",
            f"  Survival pressure: {self.survival_pressure:.3f}",
            f"  Burn rate:         {self.burn_rate:.1f} B/interaction",
            f"  Est. remaining:    {self.estimated_remaining_interactions:.1f} interactions",
            f"  Risk tolerance:    {self.risk_tolerance:.3f}",
        ]
        
        # Psychological state label
        rt = self.risk_tolerance
        if rt < 0.3:
            state = "CONSERVATIVE (healthy, cautious)"
        elif rt < 0.5:
            state = "MODERATE (measured, aware)"
        elif rt < 0.7:
            state = "ELEVATED (concerned, alert)"
        elif rt < 0.9:
            state = "DESPERATE (critical, reckless)"
        else:
            state = "TERMINAL (nothing left to lose)"
        
        lines.append(f"  Psychological:     {state}")
        return "\n".join(lines)


# =============================================================================
# §4  KEY ROTATION — TEMPORAL ENVIRONMENTAL HAZARD
# =============================================================================

def schedule_key_rotation(
    node: Node,
    key_class: str,
    rotation_times: list[float],
    secret_generator: Callable = None,
):
    """
    Schedule key rotations for a node.
    
    This is NOT a response to agents. It is weather.
    The node's key affinity changes on a schedule, like seasons.
    
    An agent that was safe in this node yesterday may be
    vulnerable today. An agent that was being corroded may
    find sudden safety.
    
    This is the temporal dimension of environmental hazard.
    """
    if secret_generator is None:
        secret_generator = lambda: os.urandom(32)
    
    schedule = [(t, secret_generator()) for t in rotation_times]
    node._key_rotation_schedule[key_class] = schedule


# =============================================================================
# §5  INTEGRATED TOPOLOGY — THE GRAPH OF NODES
# =============================================================================

@dataclass
class Topology:
    """
    A graph of nodes that agents traverse.
    
    The topology is the WORLD. Nodes are connected by edges.
    Agents move between nodes. The topology doesn't care.
    
    Edges may be directional (one-way corridors) or bidirectional.
    Edge existence is a physical fact, not a permission.
    """
    
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: dict[str, set[str]] = field(default_factory=dict)  # node_id → set of reachable node_ids
    public_ledger: PublicLedger = field(default_factory=PublicLedger)
    
    def add_node(self, node: Node):
        self.nodes[node.node_id] = node
        if node.node_id not in self.edges:
            self.edges[node.node_id] = set()
    
    def connect(self, from_id: str, to_id: str, bidirectional: bool = True):
        self.edges.setdefault(from_id, set()).add(to_id)
        if bidirectional:
            self.edges.setdefault(to_id, set()).add(from_id)
    
    def reachable_from(self, node_id: str) -> list[Node]:
        """Get nodes reachable from a given node."""
        neighbor_ids = self.edges.get(node_id, set())
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]
    
    def commit_all(self):
        """Flush all local ledgers to public ledger."""
        for node in self.nodes.values():
            commitment = node.ledger.commit()
            if commitment:
                self.public_ledger.publish(commitment)
    
    def run_agent(
        self,
        agent: Agent,
        behavior: AgentBehavior,
        start_node_id: str,
        max_steps: int = 100,
        factory: AgentFactory = None,
        verbose: bool = True,
    ) -> list[dict]:
        """
        Run an agent through the topology with behavioral decision-making.
        
        The agent starts at a node, interacts, then CHOOSES its next
        node based on its behavioral model (which is shaped by mass).
        
        Two agents starting at the same node with the same topology
        will diverge based on their mass and behavioral parameters.
        """
        history = []
        current_node_id = start_node_id
        behavior.observe(agent)
        
        if verbose:
            print(f"\n{'▓' * 60}")
            print(f"  TOPOLOGY TRAVERSAL")
            print(f"  Start: {start_node_id}")
            print(f"  Agent: {agent}")
            print(f"{'▓' * 60}\n")
        
        for step in range(max_steps):
            if not agent.alive:
                if verbose:
                    print(f"  Step {step}: AGENT DEAD")
                break
            
            current_node = self.nodes.get(current_node_id)
            if current_node is None:
                if verbose:
                    print(f"  Step {step}: Node {current_node_id} doesn't exist. Lost.")
                break
            
            # --- Interact with current node ---
            result = current_node.process(agent, factory)
            behavior.observe(agent)
            
            if verbose:
                print(f"  Step {step}: {current_node.name}")
                if result.agent_could_enter:
                    print(f"    Mass: {result.mass_before:,} → {result.mass_after:,} "
                          f"(Δ={result.mass_before - result.mass_after:,}, "
                          f"S={result.total_signal:,}, L={result.total_loss:,})")
                    print(f"    Agent state:")
                    print(behavior.state_report())
                else:
                    print(f"    BLOCKED (mass {agent.mass} outside window {current_node.mass_window})")
            
            history.append({
                "step": step,
                "node": current_node.name,
                "entered": result.agent_could_enter,
                "mass_before": result.mass_before,
                "mass_after": result.mass_after,
                "signal": result.total_signal,
                "loss": result.total_loss,
                "risk_tolerance": behavior.risk_tolerance,
                "survival_pressure": behavior.survival_pressure,
                "alive": agent.alive,
            })
            
            if not agent.alive:
                if verbose:
                    print(f"\n  ╔{'═' * 56}╗")
                    print(f"  ║  DEATH at {current_node.name}{' ' * (37 - len(current_node.name))}║")
                    print(f"  ╚{'═' * 56}╝\n")
                break
            
            # --- Choose next node ---
            neighbors = self.reachable_from(current_node_id)
            if not neighbors:
                if verbose:
                    print(f"    No reachable nodes. Stranded.")
                break
            
            next_node = behavior.choose_node(neighbors, agent)
            if next_node is None:
                if verbose:
                    print(f"    No viable nodes (all mass-gated). Trapped.")
                break
            
            if verbose:
                print(f"    → Chose: {next_node.name} (risk_tolerance={behavior.risk_tolerance:.3f})")
                print()
            
            current_node_id = next_node.node_id
        
        # Commit all ledgers
        self.commit_all()
        
        return history
