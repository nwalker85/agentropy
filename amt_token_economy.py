"""
Agent Mass Theory — Token Economy Extension
=============================================

Every tool call costs mass. Conservation law IS the budget system.

When an agent calls a tool through a gateway, the gateway's environment
strips layers of the appropriate key class. This is the "payment."
The tool executes only after payment clears. If the agent can't pay
(no layers of that class), the tool doesn't run. If the agent dies
paying, the tool doesn't run.

Economic Properties (by construction, not protocol):
    - No inflation: Conservation law prevents mass creation
    - No double-spending: Layers destroyed on decryption (one-time use)
    - Perfect audit: Merkle-anchored ledger per gateway
    - Emergent pricing: Heavy tools cost more mass = natural market
    - Budget stratification: Layer composition determines tool access

Dependencies: amt_core.py, amt_extensions.py

Author: Ravenhelm / Nate Walker
Date: 2026-02-08
"""

import os
import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional
from collections import Counter

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
# S1  TOOL CLASS -- MAPPING TOOL CATEGORIES TO KEY CLASSES
# =============================================================================

@dataclass
class ToolClass:
    """
    Maps a tool category to an AMT key class with cost model.

    A tool class defines:
        - Which key class layers it consumes (the "currency")
        - How many layers per call (the "price")
        - What category of tool it represents

    The cost is measured in LAYERS, not bytes. Each layer consumed
    has a fixed encryption overhead (28 bytes for AES-256-GCM nonce+tag)
    plus whatever payload was encoded. The cost is deterministic.
    """
    name: str           # tool category (e.g., "api_call", "llm_inference")
    key_class: str      # AMT key class (e.g., "alpha", "beta")
    base_cost: int      # layers consumed per call
    description: str    # human-readable purpose

    def __repr__(self):
        return f"ToolClass({self.name}, class={self.key_class}, cost={self.base_cost} layers)"


# =============================================================================
# S2  STANDARD TOOL CLASS DEFINITIONS
# =============================================================================

STANDARD_TOOL_CLASSES = {
    "api_call": ToolClass(
        name="api_call",
        key_class="alpha",
        base_cost=1,
        description="Cheap external API call (weather, search, lookup)",
    ),
    "llm_inference": ToolClass(
        name="llm_inference",
        key_class="beta",
        base_cost=3,
        description="Expensive LLM inference (GPT-4, DeepSeek, Claude)",
    ),
    "storage_op": ToolClass(
        name="storage_op",
        key_class="gamma",
        base_cost=2,
        description="Database or storage operation (read/write)",
    ),
    "compute": ToolClass(
        name="compute",
        key_class="delta",
        base_cost=4,
        description="Heavy compute task (ML training, batch processing)",
    ),
    "admin": ToolClass(
        name="admin",
        key_class="epsilon",
        base_cost=1,
        description="Administrative/meta operation (config, status)",
    ),
}


# =============================================================================
# S3  TOOL GATEWAY -- A NODE THAT CHARGES FOR TOOL CALLS
# =============================================================================

@dataclass
class ToolGateway:
    """
    A gateway that processes tool calls with conservation-governed charging.

    Wraps a Node internally (composition, not inheritance). When an agent
    enters, the node's environment strips layers of the tool's key class.
    This IS the payment. The tool executes only after payment clears.

    A ToolGateway for "llm_inference" holds secrets for the "beta" key class.
    An agent carrying beta layers will have them stripped (charged).
    An agent without beta layers passes through uncharged (can't use the tool).
    """
    gateway_id: str
    name: str
    tool_class: ToolClass
    tool_name: str  # specific tool (e.g., "gpt-4", "open-meteo")

    # The underlying node (created in __post_init__)
    _node: Node = field(default=None, repr=False)
    _call_log: list[dict] = field(default_factory=list, repr=False)

    # Accretion policy for result delivery
    accretion_policy: AccretionPolicy = field(default_factory=AccretionPolicy)

    def initialize(self, secrets: dict[str, bytes], ledger: LocalLedger = None):
        """
        Initialize the gateway's underlying node with the appropriate secrets.

        The gateway only holds secrets for its tool class's key class.
        It can only strip layers of that one class.
        """
        key_class = self.tool_class.key_class
        if key_class not in secrets:
            raise ValueError(f"Secret for key class '{key_class}' not provided")

        self._node = Node(
            node_id=self.gateway_id,
            name=self.name,
            _key_secrets={key_class: secrets[key_class]},
            accretion_policy=self.accretion_policy,
            ledger=ledger or LocalLedger(self.gateway_id),
        )

    @property
    def node(self) -> Node:
        return self._node

    @property
    def ledger(self) -> LocalLedger:
        return self._node.ledger if self._node else None

    def process_tool_call(
        self,
        agent: Agent,
        factory: AgentFactory = None,
    ) -> dict:
        """
        Process a tool call: charge mass, execute tool, return result.

        Flow:
            1. Node.process(agent) -> interact() strips layers (payment)
            2. If agent survived and layers were stripped: tool succeeded
            3. If no layers stripped (no affinity): tool not available
            4. If agent died: tool failed (agent couldn't afford it)
            5. Record call in log
            6. Return result

        The conservation law is enforced inside interact().
        We don't need to check it. It just holds.
        """
        if self._node is None:
            raise RuntimeError(f"Gateway '{self.name}' not initialized. Call initialize() first.")

        mass_before = agent.mass
        agent_hash = hashlib.sha256(
            f"{agent.mass}:{agent.layer_count}".encode()
        ).hexdigest()[:16]

        # Payment via conservation-governed interaction
        result = self._node.process(agent, factory)

        # Determine outcome
        if not result.agent_could_enter:
            outcome = "blocked"
            success = False
        elif result.layers_stripped == 0:
            outcome = "no_affinity"
            success = False
        elif not result.agent_survived:
            outcome = "died_paying"
            success = False
        else:
            outcome = "success"
            success = True

        call_record = {
            "agent_hash": agent_hash,
            "tool_name": self.tool_name,
            "tool_class": self.tool_class.name,
            "gateway": self.name,
            "mass_before": mass_before,
            "mass_after": agent.mass,
            "layers_charged": result.layers_stripped,
            "mass_charged": result.total_consumed,
            "signal": result.total_signal,
            "loss": result.total_loss,
            "outcome": outcome,
            "success": success,
            "timestamp": time.time(),
        }
        self._call_log.append(call_record)

        return call_record

    @property
    def call_count(self) -> int:
        return len(self._call_log)

    @property
    def successful_calls(self) -> int:
        return sum(1 for c in self._call_log if c["success"])

    @property
    def total_mass_charged(self) -> int:
        return sum(c["mass_charged"] for c in self._call_log)

    def __repr__(self):
        return (f"ToolGateway({self.name}, tool={self.tool_name}, "
                f"class={self.tool_class.name}, cost={self.tool_class.base_cost} layers)")


# =============================================================================
# S4  AGENT BUDGET -- EXTERNAL OBSERVER
# =============================================================================

@dataclass
class AgentBudget:
    """
    Tracks remaining budget by tool class. This is an OBSERVER.

    The budget does not enforce anything. It computes what the agent
    CAN afford based on current mass profile and known tool costs.
    The conservation law handles enforcement: no layers = no payment.

    This is like checking your bank balance. The balance doesn't
    prevent you from spending. It tells you what you can spend.
    """
    tool_classes: dict[str, ToolClass]

    def budget_for(self, agent: Agent) -> dict[str, dict]:
        """
        Compute remaining budget for an agent.

        Returns:
            {tool_class_name: {
                "key_class": str,
                "layers_remaining": int,
                "calls_remaining": int,
                "mass_remaining": int,
            }}

        Note: This counts layers of each key class in the agent.
        Layer count / base_cost = remaining calls for that tool class.
        """
        # Count layers by key class
        layer_counts = Counter(layer.key_class for layer in agent.layers)
        mass_by_class = {}
        for layer in agent.layers:
            mass_by_class[layer.key_class] = mass_by_class.get(layer.key_class, 0) + layer.mass

        budget = {}
        for tc_name, tc in self.tool_classes.items():
            layers = layer_counts.get(tc.key_class, 0)
            budget[tc_name] = {
                "key_class": tc.key_class,
                "layers_remaining": layers,
                "calls_remaining": layers // tc.base_cost if tc.base_cost > 0 else 0,
                "mass_remaining": mass_by_class.get(tc.key_class, 0),
            }
        return budget

    def can_afford(self, agent: Agent, tool_class_name: str, count: int = 1) -> bool:
        """Check if agent can afford N calls to a tool class."""
        budget = self.budget_for(agent)
        if tool_class_name not in budget:
            return False
        return budget[tool_class_name]["calls_remaining"] >= count

    def budget_report(self, agent: Agent) -> str:
        """Human-readable budget breakdown."""
        budget = self.budget_for(agent)
        lines = [
            f"{'─' * 60}",
            f"  AGENT BUDGET (total mass: {agent.mass:,} B, layers: {agent.layer_count})",
            f"{'─' * 60}",
            f"  {'Tool Class':<15s} {'Key':>6s} {'Layers':>8s} {'Calls':>8s} {'Mass':>8s}",
            f"  {'─' * 50}",
        ]
        for tc_name, b in budget.items():
            lines.append(
                f"  {tc_name:<15s} {b['key_class']:>6s} "
                f"{b['layers_remaining']:>8d} {b['calls_remaining']:>8d} "
                f"{b['mass_remaining']:>8,}"
            )
        lines.append(f"{'─' * 60}")
        return "\n".join(lines)


# =============================================================================
# S5  TOKEN ECONOMY TOPOLOGY
# =============================================================================

class TokenEconomyTopology:
    """
    A topology of tool gateways with economic tracking.

    Wraps a standard Topology and adds:
        - Tool class registry
        - Gateway creation with proper secret wiring
        - Economic audit reporting (calls per class, mass consumed)
        - Budget-aware agent traversal
    """

    def __init__(self):
        self._topology = Topology()
        self._tool_classes: dict[str, ToolClass] = {}
        self._gateways: dict[str, ToolGateway] = {}
        self._secrets: dict[str, bytes] = {}
        self._factory: Optional[AgentFactory] = None
        self._shared_ledger = LocalLedger("economy", batch_size=100)

    def set_secrets(self, secrets: dict[str, bytes]):
        """Set the master secrets for all key classes."""
        self._secrets = secrets

    def set_factory(self, factory: AgentFactory):
        """Set the agent factory for accretion support."""
        self._factory = factory

    def register_tool_class(self, tool_class: ToolClass):
        """Register a tool class definition."""
        self._tool_classes[tool_class.name] = tool_class

    def register_standard_classes(self):
        """Register all standard tool classes."""
        for tc in STANDARD_TOOL_CLASSES.values():
            self.register_tool_class(tc)

    def create_gateway(
        self,
        gateway_id: str,
        name: str,
        tool_class_name: str,
        tool_name: str,
        accretion_policy: AccretionPolicy = None,
    ) -> ToolGateway:
        """Create, initialize, and register a tool gateway."""
        tc = self._tool_classes.get(tool_class_name)
        if tc is None:
            raise ValueError(f"Unknown tool class: {tool_class_name}")

        gateway = ToolGateway(
            gateway_id=gateway_id,
            name=name,
            tool_class=tc,
            tool_name=tool_name,
            accretion_policy=accretion_policy or AccretionPolicy(),
        )
        gateway.initialize(self._secrets, self._shared_ledger)
        self._gateways[gateway_id] = gateway
        self._topology.add_node(gateway.node)
        return gateway

    def create_hub(self, hub_id: str, name: str) -> Node:
        """Create an inert hub node (no keys, no charge). For routing."""
        hub = Node(
            node_id=hub_id,
            name=name,
            _key_secrets={},
            ledger=self._shared_ledger,
        )
        self._topology.add_node(hub)
        return hub

    def connect(self, from_id: str, to_id: str, bidirectional: bool = True):
        """Connect two nodes/gateways."""
        self._topology.connect(from_id, to_id, bidirectional=bidirectional)

    def get_budget_tracker(self) -> AgentBudget:
        """Get a budget tracker configured for this economy's tool classes."""
        return AgentBudget(tool_classes=self._tool_classes)

    def run_agent_linear(
        self,
        agent: Agent,
        path: list[str],
        verbose: bool = True,
    ) -> list[dict]:
        """
        Run an agent through a fixed sequence of gateways.

        At each gateway, process the tool call and record results.
        Returns the call history.
        """
        history = []
        budget = self.get_budget_tracker()

        if verbose:
            print(f"\n{'▓' * 60}")
            print(f"  TOKEN ECONOMY: LINEAR TRAVERSAL")
            print(f"  Path: {' -> '.join(path)}")
            print(f"  Agent: {agent}")
            print(f"{'▓' * 60}\n")
            print(budget.budget_report(agent))
            print()

        for step, node_id in enumerate(path):
            if not agent.alive:
                if verbose:
                    print(f"  Step {step}: AGENT DEAD (budget exhausted)")
                break

            gateway = self._gateways.get(node_id)
            if gateway:
                call = gateway.process_tool_call(agent, self._factory)
                call["step"] = step

                if verbose:
                    status = call["outcome"].upper()
                    print(f"  Step {step}: [{gateway.tool_class.name}] {gateway.name} "
                          f"({gateway.tool_name})")
                    print(f"    {status}: mass {call['mass_before']:,} -> {call['mass_after']:,} "
                          f"({call['layers_charged']} layers, "
                          f"S={call['signal']:,}, L={call['loss']:,})")

                history.append(call)
            else:
                # Hub node — pass through
                node = self._topology.nodes.get(node_id)
                if node:
                    result = node.process(agent, self._factory)
                    if verbose:
                        print(f"  Step {step}: [hub] {node.name} (pass-through)")

            if verbose and agent.alive:
                b = budget.budget_for(agent)
                remaining = {k: v["calls_remaining"] for k, v in b.items() if v["calls_remaining"] > 0}
                if remaining:
                    print(f"    Budget: {remaining}")
                else:
                    print(f"    Budget: EMPTY")
                print()

        # Commit ledger
        self._commit()

        return history

    def run_agent_behavioral(
        self,
        agent: Agent,
        behavior: AgentBehavior,
        start_id: str,
        max_steps: int = 50,
        verbose: bool = True,
    ) -> list[dict]:
        """
        Run an agent through the economy with behavioral choices.

        The agent chooses which gateway to visit based on mass-dependent
        risk tolerance. Budget-constrained agents naturally avoid expensive
        gateways (high hazard = many layers stripped).
        """
        history = []
        budget = self.get_budget_tracker()
        current_id = start_id
        behavior.observe(agent)

        if verbose:
            print(f"\n{'▓' * 60}")
            print(f"  TOKEN ECONOMY: BEHAVIORAL TRAVERSAL")
            print(f"  Start: {start_id}")
            print(f"  Agent: {agent}")
            print(f"{'▓' * 60}\n")
            print(budget.budget_report(agent))
            print()

        for step in range(max_steps):
            if not agent.alive:
                if verbose:
                    print(f"  Step {step}: AGENT DEAD")
                break

            node = self._topology.nodes.get(current_id)
            if node is None:
                break

            # Process at current node
            gateway = self._gateways.get(current_id)
            if gateway:
                call = gateway.process_tool_call(agent, self._factory)
                call["step"] = step
                history.append(call)
                behavior.observe(agent)

                if verbose:
                    status = call["outcome"].upper()
                    print(f"  Step {step}: [{gateway.tool_class.name}] {gateway.name}")
                    print(f"    {status}: mass {call['mass_before']:,} -> {call['mass_after']:,}")
            else:
                result = node.process(agent, self._factory)
                behavior.observe(agent)
                if verbose:
                    print(f"  Step {step}: [hub] {node.name}")

            if not agent.alive:
                if verbose:
                    print(f"    DIED")
                break

            # Choose next
            neighbors = self._topology.reachable_from(current_id)
            if not neighbors:
                if verbose:
                    print(f"    End of path.")
                break

            next_node = behavior.choose_node(neighbors, agent)
            if next_node is None:
                if verbose:
                    print(f"    No viable nodes.")
                break

            if verbose:
                print(f"    -> {next_node.name}")
                print()

            current_id = next_node.node_id

        self._commit()
        return history

    def _commit(self):
        """Commit shared ledger to public ledger."""
        commitment = self._shared_ledger.commit()
        if commitment:
            self._topology.public_ledger.publish(commitment)

    def economy_audit(self) -> dict:
        """
        Generate economic audit report across all gateways.

        Returns aggregate statistics: calls per class, mass consumed,
        average cost, success rates.
        """
        calls_by_class = Counter()
        mass_by_class = Counter()
        success_by_class = Counter()
        total_by_class = Counter()

        for gw in self._gateways.values():
            for call in gw._call_log:
                tc = call["tool_class"]
                total_by_class[tc] += 1
                mass_by_class[tc] += call["mass_charged"]
                if call["success"]:
                    calls_by_class[tc] += 1
                    success_by_class[tc] += 1

        return {
            "total_calls": sum(total_by_class.values()),
            "successful_calls": sum(success_by_class.values()),
            "calls_by_class": dict(calls_by_class),
            "mass_consumed_by_class": dict(mass_by_class),
            "success_rate_by_class": {
                tc: success_by_class[tc] / total_by_class[tc]
                if total_by_class[tc] > 0 else 0
                for tc in total_by_class
            },
            "per_gateway": {
                gw.gateway_id: {
                    "name": gw.name,
                    "tool": gw.tool_name,
                    "class": gw.tool_class.name,
                    "total_calls": gw.call_count,
                    "successful_calls": gw.successful_calls,
                    "mass_charged": gw.total_mass_charged,
                }
                for gw in self._gateways.values()
            },
        }

    def economy_report(self) -> str:
        """Human-readable economy audit."""
        audit = self.economy_audit()
        lines = [
            f"\n{'█' * 60}",
            f"  TOKEN ECONOMY AUDIT",
            f"{'█' * 60}",
            f"  Total calls:      {audit['total_calls']}",
            f"  Successful:       {audit['successful_calls']}",
            f"",
            f"  {'Tool Class':<15s} {'Calls':>8s} {'Mass':>10s} {'Success':>10s}",
            f"  {'─' * 48}",
        ]
        for tc in sorted(audit["calls_by_class"].keys()):
            lines.append(
                f"  {tc:<15s} {audit['calls_by_class'][tc]:>8d} "
                f"{audit['mass_consumed_by_class'].get(tc, 0):>10,} "
                f"{audit['success_rate_by_class'].get(tc, 0):>10.1%}"
            )

        lines.extend([
            f"",
            f"  Per-Gateway Breakdown:",
        ])
        for gw_id, gw_data in audit["per_gateway"].items():
            lines.append(
                f"    {gw_data['name']:<20s} ({gw_data['tool']}) "
                f"calls={gw_data['total_calls']}, "
                f"mass={gw_data['mass_charged']:,}"
            )

        lines.append(f"{'█' * 60}")
        return "\n".join(lines)

    @property
    def public_ledger(self) -> PublicLedger:
        return self._topology.public_ledger

    def cost_matrix(self) -> str:
        """Display the tool cost matrix."""
        lines = [
            f"{'═' * 60}",
            f"  TOOL COST MATRIX",
            f"{'─' * 60}",
            f"  {'Tool Class':<15s} {'Key':>6s} {'Cost':>8s} {'Description'}",
            f"  {'─' * 56}",
        ]
        for tc in self._tool_classes.values():
            lines.append(
                f"  {tc.name:<15s} {tc.key_class:>6s} "
                f"{tc.base_cost:>5d} L   {tc.description}"
            )
        lines.append(f"{'═' * 60}")
        return "\n".join(lines)
