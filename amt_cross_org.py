"""
Agent Mass Theory — Cross-Organization Accountability
=======================================================

Extension module for cross-organizational agent traversal and audit.

When an agent deployed by Org A traverses infrastructure owned by Orgs B
and C, the conservation law guarantees auditability across trust boundaries
without any party trusting any other. The math IS the trust.

Key Theorem:
    The conservation law C_{n+1} + S_{n+1} + L_n = C_n is LOCAL to each
    interaction. It does not know about organizations. Therefore it is
    invariant under organizational partitioning of the topology.

    Each org can independently verify conservation on its own nodes.
    No org can determine another org's consumption from the public ledger.
    The global conservation holds as a sum of local conservations.

New Abstractions:
    Organization        — A party that owns nodes and holds secrets
    TrustBoundary       — A crossing point between organizational domains
    CrossOrgTopology    — A topology partitioned by organization ownership
    CrossOrgAuditReport — Per-org audit with merkle verification

Dependencies: amt_core.py, amt_extensions.py

Author: Ravenhelm / Nathan Walker
Date: 2026-02-08
"""

import os
import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional

from amt_core import (
    Agent, Layer, Environment, AgentFactory,
    InteractionResult, interact, accrete,
)
from amt_extensions import (
    Node, AccretionPolicy, AgentBehavior, Topology,
    LocalLedger, PublicLedger, PublicCommitment,
    LedgerEntry, merkle_root,
)


# =============================================================================
# S1  ORGANIZATION -- A PARTY IN THE CROSS-ORG TOPOLOGY
# =============================================================================

@dataclass
class Organization:
    """
    An organization owns nodes and controls secrets.

    An org is NOT a trust anchor. It is a partition boundary.
    The conservation law does not care about org boundaries.
    It enforces accountability at every interaction regardless.

    The org CAN:
        - Create nodes with its own secrets
        - Audit interactions on its own nodes via its local ledger
        - Verify its own entries against the public ledger
        - See signal, loss, and delta_L for interactions on its nodes

    The org CANNOT:
        - See interactions on other orgs' nodes
        - Determine what another org extracted from the agent
        - Alter the conservation law
        - Forge ledger entries (merkle proof would fail)
    """
    org_id: str
    name: str
    _key_secrets: dict[str, bytes] = field(default_factory=dict, repr=False)

    # Internal state
    _nodes: dict[str, Node] = field(default_factory=dict, repr=False)
    _ledger: LocalLedger = field(default=None, repr=False)

    def __post_init__(self):
        if self._ledger is None:
            self._ledger = LocalLedger(node_id=f"org-{self.org_id}", batch_size=50)

    def create_node(
        self,
        node_id: str,
        name: str,
        key_classes: list[str] = None,
        mass_window: tuple[int, int] = (0, float('inf')),
        accretion_policy: AccretionPolicy = None,
    ) -> Node:
        """
        Create a node owned by this organization.

        The node's key secrets are derived from this org's secrets.
        Only key classes that this org holds secrets for can be assigned.
        """
        key_secrets = {}
        if key_classes:
            for cls in key_classes:
                if cls not in self._key_secrets:
                    raise ValueError(
                        f"Org '{self.name}' does not hold secret for class '{cls}'"
                    )
                key_secrets[cls] = self._key_secrets[cls]

        node = Node(
            node_id=node_id,
            name=name,
            _key_secrets=key_secrets,
            mass_window=mass_window,
            accretion_policy=accretion_policy or AccretionPolicy(),
            ledger=self._ledger,
        )
        self._nodes[node_id] = node
        return node

    @property
    def nodes(self) -> dict[str, Node]:
        return dict(self._nodes)

    @property
    def ledger(self) -> LocalLedger:
        return self._ledger

    def audit_own_consumption(self) -> dict:
        """
        Summarize all interactions recorded on this org's nodes.

        This is the org's PRIVATE view of what happened on its
        infrastructure. Other orgs cannot see this.
        """
        entries = self._ledger.entries
        if not entries:
            return {
                "org": self.name,
                "total_interactions": 0,
                "total_signal": 0,
                "total_loss": 0,
                "total_mass_consumed": 0,
                "conservation_valid": True,
                "node_breakdown": {},
            }

        total_signal = sum(e.signal for e in entries)
        total_loss = sum(e.loss for e in entries)
        total_consumed = total_signal + total_loss
        conservation_valid = all(e.conservation_valid for e in entries)

        # Per-node breakdown
        node_data = {}
        for e in entries:
            if e.node_id not in node_data:
                node_data[e.node_id] = {
                    "interactions": 0, "signal": 0, "loss": 0,
                }
            node_data[e.node_id]["interactions"] += 1
            node_data[e.node_id]["signal"] += e.signal
            node_data[e.node_id]["loss"] += e.loss

        return {
            "org": self.name,
            "total_interactions": len(entries),
            "total_signal": total_signal,
            "total_loss": total_loss,
            "total_mass_consumed": total_consumed,
            "conservation_valid": conservation_valid,
            "node_breakdown": node_data,
        }

    def verify_own_entries(self, public_ledger: PublicLedger) -> dict:
        """
        Verify this org's local entries against the public ledger.

        For each commitment this org has published, verify the merkle
        root matches. This proves the local ledger hasn't been tampered
        with since publication.
        """
        # Force commit any uncommitted entries
        self._ledger.commit()

        org_commitments = [
            c for c in public_ledger.commitments
            if c.node_id == self._ledger.node_id
        ]

        verified_count = 0
        failed_count = 0

        for commitment in org_commitments:
            # Find entries in this commitment's time range
            batch_entries = [
                e for e in self._ledger.entries
                if commitment.time_range[0] <= e.timestamp <= commitment.time_range[1]
            ]
            if batch_entries:
                hashes = [e.hash for e in batch_entries]
                computed_root = merkle_root(hashes)
                if computed_root == commitment.merkle_root:
                    verified_count += 1
                else:
                    failed_count += 1

        return {
            "org": self.name,
            "commitments_checked": len(org_commitments),
            "verified": verified_count,
            "failed": failed_count,
            "merkle_verified": failed_count == 0 and len(org_commitments) > 0,
        }

    def __repr__(self):
        return (f"Organization({self.name}, nodes={list(self._nodes.keys())}, "
                f"key_classes={set(self._key_secrets.keys())})")


# =============================================================================
# S2  TRUST BOUNDARY -- THE CROSSING POINT
# =============================================================================

@dataclass
class TrustBoundary:
    """
    A crossing point between two organizational domains.

    When an agent moves from Org A's node to Org B's node, it crosses
    a trust boundary. The boundary records the agent's mass at the
    crossing point -- this is the handoff measurement.

    Neither org trusts the other. The conservation law doesn't care.
    It enforced accountability at Org A's node. It will enforce
    accountability at Org B's node. The boundary just records the
    mass at the handoff.

    Mass entering Org B = Mass leaving Org A's last node.
    This is observable, verifiable, and unforgeable.
    """
    boundary_id: str
    from_org: str
    to_org: str
    from_node: str
    to_node: str

    # Crossing records
    _crossings: list[dict] = field(default_factory=list, repr=False)

    def record_crossing(
        self,
        agent_hash: str,
        mass_at_crossing: int,
        layer_count: int,
        timestamp: float = None,
    ):
        """Record an agent crossing this boundary."""
        self._crossings.append({
            "agent_hash": agent_hash,
            "mass": mass_at_crossing,
            "layers": layer_count,
            "timestamp": timestamp or time.time(),
            "from_org": self.from_org,
            "to_org": self.to_org,
        })

    @property
    def crossings(self) -> list[dict]:
        return list(self._crossings)

    @property
    def total_crossings(self) -> int:
        return len(self._crossings)

    @property
    def total_mass_transferred(self) -> int:
        return sum(c["mass"] for c in self._crossings)

    def __repr__(self):
        return (f"TrustBoundary({self.from_org} -> {self.to_org}, "
                f"crossings={self.total_crossings})")


# =============================================================================
# S3  CROSS-ORG AUDIT REPORT
# =============================================================================

@dataclass
class CrossOrgAuditReport:
    """
    Per-organization audit report for cross-org traversal.

    Each org receives its own report containing ONLY information
    about interactions on its own nodes. The org learns nothing
    about what happened on other orgs' infrastructure.
    """
    org_name: str
    total_interactions: int
    total_signal: int
    total_loss: int
    total_mass_consumed: int
    conservation_valid: bool
    merkle_verified: bool
    trust_boundary_crossings_in: int   # agents entering this org's domain
    trust_boundary_crossings_out: int  # agents leaving this org's domain
    delta_L_aggregate: dict[str, float] = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            f"{'═' * 60}",
            f"  AUDIT REPORT: {self.org_name}",
            f"{'─' * 60}",
            f"  Interactions:        {self.total_interactions}",
            f"  Signal extracted:    {self.total_signal:,} B",
            f"  Loss incurred:       {self.total_loss:,} B",
            f"  Mass consumed:       {self.total_mass_consumed:,} B",
            f"  Conservation valid:  {self.conservation_valid}",
            f"  Merkle verified:     {self.merkle_verified}",
            f"  Boundary crossings:  {self.trust_boundary_crossings_in} in, "
            f"{self.trust_boundary_crossings_out} out",
        ]
        if self.delta_L_aggregate:
            lines.append(f"  Loss by class:")
            for cls, loss in sorted(self.delta_L_aggregate.items()):
                lines.append(f"    {cls:>12s}: {loss:,.0f} B")
        lines.append(f"{'═' * 60}")
        return "\n".join(lines)


# =============================================================================
# S4  CROSS-ORG TOPOLOGY
# =============================================================================

class CrossOrgTopology:
    """
    A topology partitioned by organizational ownership.

    Wraps a standard Topology internally and adds:
        - Organization registration and node ownership
        - Trust boundary tracking at cross-org edges
        - Per-org independent audit
        - Global conservation verification

    The internal Topology does the actual routing and interaction.
    This class adds the organizational lens without changing the physics.
    """

    def __init__(self):
        self._topology = Topology()
        self._orgs: dict[str, Organization] = {}
        self._node_ownership: dict[str, str] = {}  # node_id -> org_id
        self._trust_boundaries: dict[str, TrustBoundary] = {}  # edge_key -> boundary
        self._factory: Optional[AgentFactory] = None

    @property
    def topology(self) -> Topology:
        return self._topology

    @property
    def public_ledger(self) -> PublicLedger:
        return self._topology.public_ledger

    def set_factory(self, factory: AgentFactory):
        """Set the agent factory for accretion support."""
        self._factory = factory

    def register_organization(self, org: Organization):
        """
        Register an org and all its nodes into the topology.
        """
        self._orgs[org.org_id] = org
        for node_id, node in org.nodes.items():
            self._topology.add_node(node)
            self._node_ownership[node_id] = org.org_id

    def connect_within_org(
        self,
        org_id: str,
        from_node: str,
        to_node: str,
        bidirectional: bool = False,
    ):
        """Connect two nodes within the same org. No trust boundary."""
        self._topology.connect(from_node, to_node, bidirectional=bidirectional)

    def connect_cross_org(
        self,
        from_org_id: str,
        from_node: str,
        to_org_id: str,
        to_node: str,
    ):
        """
        Connect nodes across organizational boundaries.

        Creates a directional edge with a trust boundary record.
        The trust boundary logs every agent crossing.
        """
        edge_key = f"{from_node}->{to_node}"
        boundary = TrustBoundary(
            boundary_id=edge_key,
            from_org=from_org_id,
            to_org=to_org_id,
            from_node=from_node,
            to_node=to_node,
        )
        self._trust_boundaries[edge_key] = boundary
        self._topology.connect(from_node, to_node, bidirectional=False)

    def _agent_hash(self, agent: Agent) -> str:
        """Compute agent hash (mass state, not identity)."""
        state = f"{agent.mass}:{agent.layer_count}".encode()
        return hashlib.sha256(state).hexdigest()[:16]

    def _record_boundary_crossing(
        self,
        from_node: str,
        to_node: str,
        agent: Agent,
    ):
        """Record a trust boundary crossing if one exists for this edge."""
        edge_key = f"{from_node}->{to_node}"
        boundary = self._trust_boundaries.get(edge_key)
        if boundary:
            boundary.record_crossing(
                agent_hash=self._agent_hash(agent),
                mass_at_crossing=agent.mass,
                layer_count=agent.layer_count,
            )

    def run_cross_org_agent(
        self,
        agent: Agent,
        behavior: AgentBehavior,
        start_node_id: str,
        max_steps: int = 100,
        verbose: bool = True,
    ) -> list[dict]:
        """
        Run an agent through the cross-org topology.

        Like Topology.run_agent(), but additionally records trust
        boundary crossings when the agent moves between orgs.
        """
        history = []
        current_node_id = start_node_id
        behavior.observe(agent)

        if verbose:
            print(f"\n{'▓' * 60}")
            print(f"  CROSS-ORG TRAVERSAL")
            print(f"  Start: {start_node_id}")
            print(f"  Agent: {agent}")
            print(f"  Orgs:  {', '.join(o.name for o in self._orgs.values())}")
            print(f"{'▓' * 60}\n")

        for step in range(max_steps):
            if not agent.alive:
                if verbose:
                    print(f"  Step {step}: AGENT DEAD")
                break

            current_node = self._topology.nodes.get(current_node_id)
            if current_node is None:
                if verbose:
                    print(f"  Step {step}: Node {current_node_id} doesn't exist.")
                break

            current_org_id = self._node_ownership.get(current_node_id, "unknown")
            current_org = self._orgs.get(current_org_id)

            # --- Interact with current node ---
            result = current_node.process(agent, self._factory)
            behavior.observe(agent)

            if verbose:
                org_label = current_org.name if current_org else "???"
                print(f"  Step {step}: [{org_label}] {current_node.name}")
                if result.agent_could_enter:
                    print(f"    Mass: {result.mass_before:,} -> {result.mass_after:,} "
                          f"(S={result.total_signal:,}, L={result.total_loss:,})")
                else:
                    print(f"    BLOCKED (mass {agent.mass})")

            history.append({
                "step": step,
                "node": current_node.name,
                "node_id": current_node_id,
                "org": current_org_id,
                "entered": result.agent_could_enter,
                "mass_before": result.mass_before,
                "mass_after": result.mass_after,
                "signal": result.total_signal,
                "loss": result.total_loss,
                "alive": agent.alive,
                "risk_tolerance": _safe_risk_tolerance(behavior),
            })

            if not agent.alive:
                if verbose:
                    print(f"\n  DEATH at [{current_org.name if current_org else '???'}] "
                          f"{current_node.name}")
                break

            # --- Choose next node ---
            neighbors = self._topology.reachable_from(current_node_id)
            if not neighbors:
                if verbose:
                    print(f"    End of path. No reachable nodes.")
                break

            next_node = behavior.choose_node(neighbors, agent)
            if next_node is None:
                if verbose:
                    print(f"    No viable nodes. Trapped.")
                break

            # --- Record trust boundary crossing ---
            next_org_id = self._node_ownership.get(next_node.node_id, "unknown")
            if next_org_id != current_org_id:
                self._record_boundary_crossing(
                    current_node_id, next_node.node_id, agent,
                )
                if verbose:
                    next_org = self._orgs.get(next_org_id)
                    print(f"    >>> TRUST BOUNDARY: {current_org.name if current_org else '???'}"
                          f" -> {next_org.name if next_org else '???'} "
                          f"(mass={agent.mass:,})")

            if verbose and next_node:
                print(f"    -> {next_node.name}")
                print()

            current_node_id = next_node.node_id

        # Commit all ledgers
        self._commit_all()

        return history

    def run_cross_org_linear(
        self,
        agent: Agent,
        path: list[str],
        verbose: bool = True,
    ) -> list[dict]:
        """
        Run an agent through a fixed linear path (no behavioral choices).

        Useful for deterministic demos where we want to show exact
        mass accounting at every step.
        """
        history = []

        if verbose:
            print(f"\n{'▓' * 60}")
            print(f"  CROSS-ORG LINEAR TRAVERSAL")
            print(f"  Path: {' -> '.join(path)}")
            print(f"  Agent: {agent}")
            print(f"{'▓' * 60}\n")

        prev_node_id = None

        for step, node_id in enumerate(path):
            if not agent.alive:
                if verbose:
                    print(f"  Step {step}: AGENT DEAD before reaching {node_id}")
                break

            node = self._topology.nodes.get(node_id)
            if node is None:
                if verbose:
                    print(f"  Step {step}: Node {node_id} doesn't exist.")
                break

            org_id = self._node_ownership.get(node_id, "unknown")
            org = self._orgs.get(org_id)

            # Record trust boundary crossing
            if prev_node_id is not None:
                prev_org_id = self._node_ownership.get(prev_node_id, "unknown")
                if prev_org_id != org_id:
                    self._record_boundary_crossing(prev_node_id, node_id, agent)
                    if verbose:
                        prev_org = self._orgs.get(prev_org_id)
                        print(f"  >>> TRUST BOUNDARY: "
                              f"{prev_org.name if prev_org else '???'} -> "
                              f"{org.name if org else '???'} "
                              f"(mass={agent.mass:,})")

            # Interact
            result = node.process(agent, self._factory)

            if verbose:
                org_label = org.name if org else "???"
                print(f"  Step {step}: [{org_label}] {node.name}")
                if result.agent_could_enter:
                    print(f"    Mass: {result.mass_before:,} -> {result.mass_after:,} "
                          f"(S={result.total_signal:,}, L={result.total_loss:,})")
                    if result.per_layer:
                        for pl in result.per_layer:
                            status = "DATA" if pl.had_data else "EMPTY"
                            print(f"      [{pl.key_class}] {status}: "
                                  f"consumed={pl.mass_consumed}B "
                                  f"signal={pl.signal}B loss={pl.loss}B")
                else:
                    print(f"    PASSED THROUGH (inert node, no matching keys)")

            history.append({
                "step": step,
                "node": node.name,
                "node_id": node_id,
                "org": org_id,
                "entered": result.agent_could_enter,
                "mass_before": result.mass_before,
                "mass_after": result.mass_after,
                "signal": result.total_signal,
                "loss": result.total_loss,
                "layers_stripped": result.layers_stripped,
                "alive": agent.alive,
                "conservation_valid": (
                    result.mass_before == result.mass_after +
                    result.total_signal + result.total_loss
                ),
            })

            if not agent.alive:
                if verbose:
                    print(f"\n  DEATH at [{org.name if org else '???'}] {node.name}")

            prev_node_id = node_id

        # Commit all ledgers
        self._commit_all()

        return history

    def _commit_all(self):
        """Commit all org ledgers to public ledger."""
        for org in self._orgs.values():
            commitment = org.ledger.commit()
            if commitment:
                self._topology.public_ledger.publish(commitment)

    def per_org_audit(self) -> dict[str, CrossOrgAuditReport]:
        """
        Generate independent audit reports for each organization.

        Each org's report contains ONLY data from its own nodes.
        No org can see another org's consumption, signal, or loss.
        """
        reports = {}

        for org_id, org in self._orgs.items():
            consumption = org.audit_own_consumption()

            # Compute boundary crossings
            crossings_in = 0
            crossings_out = 0
            for boundary in self._trust_boundaries.values():
                if boundary.to_org == org_id:
                    crossings_in += boundary.total_crossings
                if boundary.from_org == org_id:
                    crossings_out += boundary.total_crossings

            # Aggregate delta_L from ledger entries
            delta_L_agg = {}
            for entry in org.ledger.entries:
                for cls, loss in entry.delta_L.items():
                    delta_L_agg[cls] = delta_L_agg.get(cls, 0) + loss

            # Verify merkle
            verification = org.verify_own_entries(self._topology.public_ledger)

            report = CrossOrgAuditReport(
                org_name=org.name,
                total_interactions=consumption["total_interactions"],
                total_signal=consumption["total_signal"],
                total_loss=consumption["total_loss"],
                total_mass_consumed=consumption["total_mass_consumed"],
                conservation_valid=consumption["conservation_valid"],
                merkle_verified=verification["merkle_verified"],
                trust_boundary_crossings_in=crossings_in,
                trust_boundary_crossings_out=crossings_out,
                delta_L_aggregate=delta_L_agg,
            )
            reports[org_id] = report

        return reports

    def verify_global_conservation(self, history: list[dict]) -> dict:
        """
        Verify conservation law across the entire cross-org traversal.

        The key theorem: conservation is local to each interact() call.
        Summing across all interactions in all orgs, the global
        conservation must hold.

        Global law:
            initial_mass = final_mass + sum(all_signal) + sum(all_loss) - sum(all_accreted)
        """
        entered = [h for h in history if h["entered"]]

        total_signal = sum(h["signal"] for h in entered)
        total_loss = sum(h["loss"] for h in entered)

        violations = 0
        for h in entered:
            lhs = h["mass_before"]
            rhs = h["mass_after"] + h["signal"] + h["loss"]
            if lhs != rhs:
                violations += 1

        return {
            "interactions": len(entered),
            "total_signal": total_signal,
            "total_loss": total_loss,
            "total_mass_consumed": total_signal + total_loss,
            "per_step_violations": violations,
            "conservation_holds": violations == 0,
        }

    def get_trust_boundaries(self) -> dict[str, TrustBoundary]:
        return dict(self._trust_boundaries)

    def get_org(self, org_id: str) -> Optional[Organization]:
        return self._orgs.get(org_id)

    def topology_map(self) -> str:
        """Human-readable topology map with org ownership."""
        lines = [
            f"{'═' * 60}",
            f"  CROSS-ORG TOPOLOGY MAP",
            f"{'─' * 60}",
        ]

        for org_id, org in self._orgs.items():
            lines.append(f"\n  [{org.name}] (org_id={org_id})")
            for node_id, node in org.nodes.items():
                keys = node.key_classes if node.key_classes else "{inert}"
                edges_out = self._topology.edges.get(node_id, set())
                lines.append(f"    {node.name} ({node_id})")
                lines.append(f"      Keys: {keys}")
                if edges_out:
                    for target in edges_out:
                        target_org = self._node_ownership.get(target, "???")
                        boundary_marker = ""
                        edge_key = f"{node_id}->{target}"
                        if edge_key in self._trust_boundaries:
                            boundary_marker = " [TRUST BOUNDARY]"
                        lines.append(f"      -> {target}{boundary_marker}")

        lines.append(f"\n  Trust Boundaries:")
        for key, boundary in self._trust_boundaries.items():
            from_org = self._orgs.get(boundary.from_org)
            to_org = self._orgs.get(boundary.to_org)
            lines.append(f"    {from_org.name if from_org else '???'} "
                         f"({boundary.from_node}) -> "
                         f"{to_org.name if to_org else '???'} "
                         f"({boundary.to_node})")

        lines.append(f"{'═' * 60}")
        return "\n".join(lines)


# =============================================================================
# S5  UTILITY FUNCTIONS
# =============================================================================

def _safe_risk_tolerance(behavior: AgentBehavior) -> float:
    """
    Safely compute risk_tolerance, handling the edge case where
    accretion causes mass_ratio > 1.0. When mass_ratio > 1.0,
    depletion is negative, and fractional exponents produce complex
    numbers. We clamp to risk_baseline in this case (agent is
    heavier than when it started — no desperation).
    """
    try:
        return behavior.risk_tolerance
    except TypeError:
        # mass_ratio > 1.0 with fractional desperation_curve
        return behavior.risk_baseline

def build_cross_org_factory(all_secrets: dict[str, bytes]) -> AgentFactory:
    """
    Build a factory that knows all secrets across all orgs.

    This is the DEPLOYER role -- the party that creates the agent.
    At creation time, the deployer must know all key classes the
    agent will encounter. After deployment, the deployer's knowledge
    is irrelevant. The agent is on its own.
    """
    return AgentFactory(all_secrets)


def compare_org_audits(reports: dict[str, CrossOrgAuditReport]) -> str:
    """
    Compare audit reports across orgs (external auditor view).

    The auditor can see:
        - Total mass consumed per org
        - Conservation validity per org
        - Trust boundary crossing counts

    The auditor CANNOT see:
        - Signal content
        - Which key classes were stripped
        - Individual transaction details
    """
    lines = [
        f"\n{'█' * 60}",
        f"  CROSS-ORG AUDIT COMPARISON",
        f"{'█' * 60}",
        "",
        f"  {'Org':<20s} {'Interactions':>12s} {'Consumed':>12s} "
        f"{'Conserved':>10s} {'Merkle':>8s}",
        f"  {'─' * 66}",
    ]

    total_interactions = 0
    total_consumed = 0
    all_conserved = True

    for org_id, report in reports.items():
        total_interactions += report.total_interactions
        total_consumed += report.total_mass_consumed
        if not report.conservation_valid:
            all_conserved = False

        lines.append(
            f"  {report.org_name:<20s} {report.total_interactions:>12d} "
            f"{report.total_mass_consumed:>12,} "
            f"{'YES' if report.conservation_valid else 'NO':>10s} "
            f"{'YES' if report.merkle_verified else 'NO':>8s}"
        )

    lines.extend([
        f"  {'─' * 66}",
        f"  {'TOTAL':<20s} {total_interactions:>12d} {total_consumed:>12,} "
        f"{'YES' if all_conserved else 'NO':>10s}",
        "",
        f"  Global conservation: {'HOLDS' if all_conserved else 'VIOLATED'}",
        f"  Theorem: Sum of local conservations = global conservation.",
        f"{'█' * 60}",
    ])

    return "\n".join(lines)
