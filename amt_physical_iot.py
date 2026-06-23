"""
Agent Mass Theory -- Physical IoT / The Viking Experiment
===========================================================

Maps AMT's abstract conservation physics to REAL physical resources on a
smart RV (The Viking). Sleipner manages battery, bandwidth, storage, CPU,
and sensor budgets across varying connectivity environments.

Physical Resource Classes:
    battery   (alpha)   -- Electrical energy budget (watt-hours)
    bandwidth (beta)    -- Network data budget (megabytes)
    storage   (gamma)   -- Disk I/O budget (operations)
    cpu       (delta)   -- Compute cycles budget (cpu-seconds)
    sensor    (epsilon) -- Sensor access budget (reads)

Unit Conversions (physical -> AMT mass in bytes):
    1 watt-hour     = 1000 bytes of alpha mass
    1 megabyte      = 1 byte of beta mass (1:1)
    1 I/O operation = 100 bytes of gamma mass
    1 CPU-second    = 500 bytes of delta mass
    1 sensor read   = 50 bytes of epsilon mass

Key insight: mass gates become literal physical constraints.
A low-battery system cannot support power-hungry operations because of
physics, not policy. Behavioral divergence emerges from resource
depletion, not hand-coded power management rules.

Dependencies: amt_core.py, amt_extensions.py
Author: Ravenhelm / Nathan Walker
Date: 2026-02-08
"""

import os
import hashlib
from dataclasses import dataclass, field
from typing import Optional

from amt_core import (
    Agent, Layer, Environment, AgentFactory,
    InteractionResult, interact,
)
from amt_extensions import (
    Node, AgentBehavior, Topology, AccretionPolicy,
    LocalLedger,
)


# =============================================================================
# S1  PHYSICAL RESOURCE -- THE BRIDGE BETWEEN ATOMS AND BITS
# =============================================================================

@dataclass
class PhysicalResource:
    """
    Maps a real physical resource to an AMT key class.

    Each resource type (battery, bandwidth, storage, etc.) is represented
    as a key class. Mass in that class = available budget in physical units.

    The conversion factor bridges physical units to AMT mass:
        mass_bytes = physical_units * conversion_factor

    This is the fundamental mapping that lets conservation law
    enforce real-world resource limits.
    """

    resource_type: str          # "battery", "bandwidth", "storage", "cpu", "sensor"
    key_class: str              # AMT key class ("alpha", "beta", etc.)
    unit: str                   # Physical unit name ("Wh", "MB", etc.)
    conversion_factor: float    # Physical unit -> bytes
    max_physical: float         # Maximum physical capacity
    current_physical: float     # Current available capacity

    @property
    def current_mass_bytes(self) -> int:
        """Current resource translated to AMT mass."""
        return int(self.current_physical * self.conversion_factor)

    @property
    def max_mass_bytes(self) -> int:
        """Max resource capacity as mass."""
        return int(self.max_physical * self.conversion_factor)

    @property
    def depletion_ratio(self) -> float:
        """Fraction of resource consumed. 0.0 = full, 1.0 = empty."""
        if self.max_physical == 0:
            return 1.0
        return 1.0 - (self.current_physical / self.max_physical)

    def consume_physical(self, physical_units: float) -> float:
        """
        Consume physical units (e.g., 5 watt-hours).
        Returns actual units consumed (may be less if resource exhausted).
        """
        actual = min(physical_units, self.current_physical)
        self.current_physical = max(0, self.current_physical - actual)
        return actual

    def mass_to_physical(self, mass_bytes: int) -> float:
        """Convert AMT mass back to physical units."""
        if self.conversion_factor == 0:
            return 0
        return mass_bytes / self.conversion_factor


# =============================================================================
# S2  CONNECTIVITY ENVIRONMENT -- LOCATION AS PHYSICS
# =============================================================================

# Standard resource-to-key mappings
RESOURCE_MAP = {
    "battery":   ("alpha",   1000.0),    # 1 Wh = 1000 bytes
    "bandwidth": ("beta",    1.0),       # 1 MB = 1 byte
    "storage":   ("gamma",   100.0),     # 1 op = 100 bytes
    "cpu":       ("delta",   500.0),     # 1 CPU-sec = 500 bytes
    "sensor":    ("epsilon", 50.0),      # 1 read = 50 bytes
}


@dataclass
class ConnectivityEnvironment:
    """
    Represents a physical location with varying resource availability.

    Location types:
        campsite_wifi  -- Shore power (unlimited), abundant bandwidth
        cellular       -- Battery drain, limited bandwidth
        satellite      -- Extreme bandwidth cost, critical battery drain
        off_grid       -- No bandwidth at all, battery only
        shore_power    -- Unlimited power, bandwidth varies
    """

    name: str
    location_type: str
    resources: dict = field(default_factory=dict)  # resource_type -> PhysicalResource
    consumed_types: set = field(default_factory=set)  # which resource types are actively consumed

    def compute_mass_threshold(self) -> tuple:
        """
        Dynamic mass gate based on battery state.

        Battery > 80%:   max_mass = 10 MB (heavy agents allowed)
        Battery 50-80%:  max_mass = 5 MB
        Battery 20-50%:  max_mass = 2 MB
        Battery < 20%:   max_mass = 500 KB (critical)
        No battery:      unlimited (shore power)
        """
        battery = self.resources.get("battery")
        if battery is None:
            return (0, float('inf'))

        depletion = battery.depletion_ratio

        if depletion < 0.2:     # > 80% charge
            max_mass = 10 * 1024 * 1024
        elif depletion < 0.5:   # 50-80%
            max_mass = 5 * 1024 * 1024
        elif depletion < 0.8:   # 20-50%
            max_mass = 2 * 1024 * 1024
        else:                   # < 20%
            max_mass = 500 * 1024

        return (0, max_mass)

    def record_consumption(self, result: InteractionResult):
        """
        After interaction, update physical resource states from mass consumed.

        For each layer stripped, find the corresponding physical resource
        and deduct the physical equivalent.
        """
        for layer_result in result.per_layer:
            key_class = layer_result.key_class
            mass_consumed = layer_result.mass_consumed

            for res in self.resources.values():
                if res.key_class == key_class:
                    physical_units = res.mass_to_physical(mass_consumed)
                    res.consume_physical(physical_units)
                    break

    def resource_summary(self) -> str:
        """Human-readable summary of resource states."""
        lines = []
        for res in self.resources.values():
            pct = (1.0 - res.depletion_ratio) * 100
            lines.append(
                f"      {res.resource_type:>10s}: "
                f"{res.current_physical:.1f} / {res.max_physical:.1f} "
                f"{res.unit} ({pct:.0f}%)"
            )
        return "\n".join(lines)


# =============================================================================
# S3  RESOURCE BUDGET -- AGENT MASS AS PHYSICAL ALLOCATION
# =============================================================================

@dataclass
class ResourceBudget:
    """
    Interprets an agent's mass as a physical resource allocation.

    Specify physical budgets (watt-hours, megabytes, etc.) and convert
    them to AMT layer specs for AgentFactory.build_agent().
    """

    battery_wh: float = 0.0
    bandwidth_mb: float = 0.0
    storage_ops: float = 0.0
    cpu_seconds: float = 0.0
    sensor_reads: int = 0

    def to_layer_specs(self) -> list:
        """
        Convert physical budgets to (key_class, payload) tuples
        for AgentFactory.build_agent().

        Each resource is allocated as multiple layers. Some carry
        data (signal), some are empty (pure cost/toll).
        """
        specs = []

        def _make_layers(resource_type, physical_value):
            if physical_value <= 0:
                return
            key_class, factor = RESOURCE_MAP[resource_type]
            total_mass = int(physical_value * factor)
            num_layers = max(1, total_mass // 256)
            payload_per = max(1, total_mass // max(1, num_layers))

            data_count = max(1, int(num_layers * 0.8))
            empty_count = num_layers - data_count

            for _ in range(data_count):
                specs.append((key_class, os.urandom(min(payload_per, 512))))
            for _ in range(empty_count):
                specs.append((key_class, b""))

        _make_layers("battery", self.battery_wh)
        _make_layers("bandwidth", self.bandwidth_mb)
        _make_layers("storage", self.storage_ops)
        _make_layers("cpu", self.cpu_seconds)
        _make_layers("sensor", self.sensor_reads)

        return specs

    def summary(self) -> str:
        """Human-readable budget summary."""
        parts = []
        if self.battery_wh > 0:
            parts.append(f"{self.battery_wh:.0f} Wh battery")
        if self.bandwidth_mb > 0:
            parts.append(f"{self.bandwidth_mb:.0f} MB bandwidth")
        if self.storage_ops > 0:
            parts.append(f"{self.storage_ops:.0f} storage ops")
        if self.cpu_seconds > 0:
            parts.append(f"{self.cpu_seconds:.0f} CPU-sec")
        if self.sensor_reads > 0:
            parts.append(f"{self.sensor_reads} sensor reads")
        return ", ".join(parts) if parts else "(empty budget)"

    @staticmethod
    def interpret_agent_mass(agent: Agent) -> dict:
        """
        Reverse: given an agent, estimate physical budgets from mass profile.
        """
        profile = agent.mass_profile()
        budgets = {}
        for resource_type, (key_class, factor) in RESOURCE_MAP.items():
            mass = profile.get(key_class, 0)
            budgets[resource_type] = mass / factor if factor > 0 else 0
        return budgets


# =============================================================================
# S4  PHYSICAL TOPOLOGY -- THE TRAVEL ROUTE
# =============================================================================

class PhysicalTopology:
    """
    Topology representing a travel route with varying physical conditions.

    Wraps amt_extensions.Topology internally. Each node is a location
    with specific connectivity and power state. Edges are travel segments.

    Composition, not modification. The internal Topology handles
    routing; this class adds physical resource tracking.
    """

    def __init__(self, all_secrets: dict):
        """
        Args:
            all_secrets: {key_class: master_secret} for all resource classes.
        """
        self._topology = Topology()
        self._environments: dict = {}
        self._all_secrets = all_secrets
        self._factory: Optional[AgentFactory] = None

    def set_factory(self, factory: AgentFactory):
        """Set the agent factory for accretion support."""
        self._factory = factory

    @property
    def environments(self) -> dict:
        return dict(self._environments)

    def add_location(
        self,
        location_id: str,
        location_type: str,
        battery_wh: Optional[float] = None,
        bandwidth_mbps: Optional[float] = None,
        storage_ops: Optional[float] = None,
        cpu_seconds: Optional[float] = None,
        sensor_reads: Optional[int] = None,
        consumed: Optional[list] = None,
    ):
        """
        Add a physical location to the topology.

        bandwidth_mbps is converted to a 1-minute MB budget:
            mb_budget = mbps * 60 / 8

        consumed: list of resource types actively consumed at this location.
            Only these resources contribute their key class to the node.
            Other resources are tracked (for display) but don't strip layers.
            If None, all specified resources are consumed (legacy behavior).
        """
        resources = {}

        if battery_wh is not None:
            resources["battery"] = PhysicalResource(
                resource_type="battery", key_class="alpha",
                unit="Wh", conversion_factor=1000.0,
                max_physical=battery_wh, current_physical=battery_wh,
            )

        if bandwidth_mbps is not None:
            mb_budget = bandwidth_mbps * 60 / 8
            resources["bandwidth"] = PhysicalResource(
                resource_type="bandwidth", key_class="beta",
                unit="MB", conversion_factor=1.0,
                max_physical=mb_budget, current_physical=mb_budget,
            )

        if storage_ops is not None:
            resources["storage"] = PhysicalResource(
                resource_type="storage", key_class="gamma",
                unit="ops", conversion_factor=100.0,
                max_physical=storage_ops, current_physical=storage_ops,
            )

        if cpu_seconds is not None:
            resources["cpu"] = PhysicalResource(
                resource_type="cpu", key_class="delta",
                unit="cpu-sec", conversion_factor=500.0,
                max_physical=cpu_seconds, current_physical=cpu_seconds,
            )

        if sensor_reads is not None:
            resources["sensor"] = PhysicalResource(
                resource_type="sensor", key_class="epsilon",
                unit="reads", conversion_factor=50.0,
                max_physical=float(sensor_reads), current_physical=float(sensor_reads),
            )

        consumed_types = set(consumed) if consumed else set(resources.keys())
        env = ConnectivityEnvironment(
            name=location_id,
            location_type=location_type,
            resources=resources,
            consumed_types=consumed_types,
        )
        self._environments[location_id] = env

        # Build key_secrets: only consumed resources have their keys revealed
        # Resources not consumed are tracked but don't strip layers
        key_secrets = {}
        for res in resources.values():
            if res.resource_type in consumed_types:
                if res.key_class in self._all_secrets:
                    key_secrets[res.key_class] = self._all_secrets[res.key_class]

        node = Node(
            node_id=location_id,
            name=location_id,
            _key_secrets=key_secrets,
            mass_window=env.compute_mass_threshold(),
        )
        self._topology.add_node(node)

    def connect_locations(self, from_id: str, to_id: str, bidirectional: bool = False):
        """Connect two locations (travel route segment)."""
        self._topology.connect(from_id, to_id, bidirectional=bidirectional)

    def traverse_route(
        self,
        agent: Agent,
        route: list,
        verbose: bool = True,
    ) -> list:
        """
        Traverse a fixed route through physical locations.

        At each location:
            1. Recompute mass gate from current resource state
            2. Interact via AMT core (conservation law enforced)
            3. Update environment resource states
            4. Record physical metrics
        """
        history = []

        if verbose:
            print(f"\n{'=' * 70}")
            print(f"  PHYSICAL IOT TRAVERSAL")
            print(f"  Route: {' -> '.join(route)}")
            print(f"  Agent: {agent}")
            print(f"{'=' * 70}\n")

        for step, location_id in enumerate(route):
            if not agent.alive:
                if verbose:
                    print(f"  Step {step}: AGENT DEAD before reaching {location_id}")
                break

            env_config = self._environments.get(location_id)
            if env_config is None:
                if verbose:
                    print(f"  Step {step}: Location {location_id} not found.")
                break

            # Recompute mass gate from current resource state
            node = self._topology.nodes[location_id]
            node.mass_window = env_config.compute_mass_threshold()

            # Interact via AMT core
            result = node.process(agent, self._factory)

            # Update resource states from consumption
            if result.agent_could_enter:
                env_config.record_consumption(result)

            # Collect physical metrics snapshot
            resource_snapshot = {}
            for res_type, res in env_config.resources.items():
                resource_snapshot[res_type] = {
                    "current": res.current_physical,
                    "max": res.max_physical,
                    "unit": res.unit,
                    "depletion": res.depletion_ratio,
                }

            if verbose:
                print(f"  Step {step}: {location_id} [{env_config.location_type}]")
                if result.agent_could_enter:
                    print(f"    Mass: {result.mass_before:,} -> {result.mass_after:,} "
                          f"(S={result.total_signal:,}, L={result.total_loss:,})")
                    if env_config.resources:
                        print(f"    Resources after:")
                        print(env_config.resource_summary())
                else:
                    gate = node.mass_window
                    print(f"    BLOCKED (mass {agent.mass:,} outside gate "
                          f"[{gate[0]:,}, {gate[1]:,}])")

            history.append({
                "step": step,
                "location": location_id,
                "location_type": env_config.location_type,
                "entered": result.agent_could_enter,
                "mass_before": result.mass_before,
                "mass_after": result.mass_after,
                "signal": result.total_signal,
                "loss": result.total_loss,
                "layers_stripped": result.layers_stripped,
                "resources": resource_snapshot,
                "mass_gate": node.mass_window,
                "alive": agent.alive,
            })

            if not agent.alive and verbose:
                print(f"\n  DEATH at {location_id}")

        return history

    def environment_map(self) -> str:
        """Human-readable map of all physical environments."""
        lines = [
            f"{'=' * 70}",
            f"  PHYSICAL ENVIRONMENT MAP",
            f"{'=' * 70}",
        ]

        for loc_id, env in self._environments.items():
            lines.append(f"\n  {loc_id} [{env.location_type}]")
            if env.resources:
                lines.append(f"    Resources:")
                for res in env.resources.values():
                    pct = (1.0 - res.depletion_ratio) * 100
                    lines.append(
                        f"      {res.resource_type:>10s}: "
                        f"{res.current_physical:.1f} / {res.max_physical:.1f} "
                        f"{res.unit} ({pct:.0f}%)"
                    )
            else:
                lines.append(f"    Resources: (none)")

            gate = env.compute_mass_threshold()
            if gate[1] != float('inf'):
                lines.append(f"    Mass gate: max {gate[1]:,} bytes")
            else:
                lines.append(f"    Mass gate: unlimited")

            key_classes = [res.key_class for res in env.resources.values()]
            if key_classes:
                lines.append(f"    Consumes: {{{', '.join(key_classes)}}}")
            else:
                lines.append(f"    Consumes: (inert)")

        lines.append(f"\n{'=' * 70}")
        return "\n".join(lines)


# =============================================================================
# S5  RESOURCE AUDIT REPORT
# =============================================================================

@dataclass
class ResourceAuditReport:
    """
    Per-location audit showing both physical and AMT metrics.
    Every watt-hour accounted for.
    """

    location_id: str
    location_type: str
    interactions: int = 0
    total_signal: int = 0
    total_loss: int = 0
    total_mass_consumed: int = 0
    conservation_valid: bool = True
    resource_deltas: dict = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            f"{'=' * 60}",
            f"  RESOURCE AUDIT: {self.location_id} [{self.location_type}]",
            f"{'─' * 60}",
            f"  Interactions:      {self.interactions}",
            f"  AMT metrics:",
            f"    Signal:          {self.total_signal:,} B",
            f"    Loss:            {self.total_loss:,} B",
            f"    Mass consumed:   {self.total_mass_consumed:,} B",
            f"    Conservation:    {'VALID' if self.conservation_valid else 'VIOLATED'}",
        ]
        if self.resource_deltas:
            lines.append(f"  Physical consumption:")
            for res_type, delta in self.resource_deltas.items():
                lines.append(
                    f"    {res_type:>10s}: {delta['consumed']:.2f} {delta['unit']}"
                )
        lines.append(f"{'=' * 60}")
        return "\n".join(lines)


def generate_resource_audit(history: list, environments: dict = None) -> dict:
    """
    Generate per-location resource audit from traversal history.

    Returns: {location_id: ResourceAuditReport}
    """
    reports = {}

    for entry in history:
        loc = entry["location"]
        if loc not in reports:
            reports[loc] = ResourceAuditReport(
                location_id=loc,
                location_type=entry["location_type"],
            )

        report = reports[loc]
        report.interactions += 1

        if not entry["entered"]:
            continue

        report.total_signal += entry["signal"]
        report.total_loss += entry["loss"]
        report.total_mass_consumed += entry["signal"] + entry["loss"]

        # Conservation check
        lhs = entry["mass_before"]
        rhs = entry["mass_after"] + entry["signal"] + entry["loss"]
        if lhs != rhs:
            report.conservation_valid = False

    # Physical deltas from environments
    if environments:
        for loc_id, report in reports.items():
            env = environments.get(loc_id)
            if env is None:
                continue
            deltas = {}
            for res in env.resources.values():
                consumed = res.max_physical - res.current_physical
                deltas[res.resource_type] = {
                    "consumed": consumed,
                    "unit": res.unit,
                    "remaining": res.current_physical,
                    "max": res.max_physical,
                }
            report.resource_deltas = deltas

    return reports


# =============================================================================
# S6  HELPER -- SAFE RISK TOLERANCE (complex number bug workaround)
# =============================================================================

def _safe_risk_tolerance(behavior: AgentBehavior) -> float:
    """
    Workaround for fractional exponent bug in AgentBehavior.risk_tolerance.

    When accretion causes mass_ratio > 1.0, depletion goes negative, and
    fractional desperation_curve exponents produce complex numbers.
    """
    try:
        return behavior.risk_tolerance
    except TypeError:
        return behavior.risk_baseline
