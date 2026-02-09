# Physical IoT: Mapping Agent Mass Theory to Real-World Resources

**Conservation Law as Resource Management for The Viking**

*Nate Walker — Ravenhelm*
*February 2026*

---

## Abstract

Agent Mass Theory's conservation law `C_{n+1} + S_{n+1} + L_n = C_n` operates on abstract encrypted layers. We demonstrate that this abstraction maps directly to physical resources: battery capacity (watt-hours), network bandwidth (megabytes), storage I/O (operations), CPU time (cpu-seconds), and sensor access (reads). By assigning each resource type to a key class with a fixed conversion factor, an agent's mass profile becomes a physical resource budget. Mass gates become battery constraints. Layer stripping becomes resource consumption. Behavioral divergence emerges from power depletion, not hand-coded power management. We demonstrate this mapping on a five-location travel route simulating a smart RV (The Viking) traversing environments from shore-power campsite to off-grid remote location. At population scale (150 agents, 750 interactions), zero conservation violations occur. The conservation law IS the battery management system.

---

## 1. Introduction

### The Resource Management Problem

IoT systems — smart homes, vehicles, field sensors — face a fundamental resource management challenge. Multiple physical resources (power, connectivity, storage, compute, sensors) must be budgeted across varying environmental conditions. Traditional approaches use:

- **Power management daemons**: Monitor battery, trigger low-power modes
- **Bandwidth throttling**: Rate limiters based on connectivity type
- **Storage quotas**: Fixed allocation per application
- **CPU governors**: Frequency scaling based on thermal/power state

Each of these is a separate policy engine with separate configuration, separate failure modes, and no unified accounting. When an agent operates across these resources, there is no single framework that enforces: *"you have X watt-hours, Y megabytes, and Z CPU-seconds — spend them wisely."*

### Conservation as Unified Resource Accounting

AMT's conservation law provides exactly this unification. By mapping each physical resource to a key class:

| Resource | Key Class | Unit | Conversion |
|----------|-----------|------|------------|
| Battery | alpha | Wh | 1000 B/Wh |
| Bandwidth | beta | MB | 1 B/MB |
| Storage | gamma | ops | 100 B/op |
| CPU | delta | cpu-sec | 500 B/s |
| Sensor | epsilon | reads | 50 B/read |

An agent's mass profile becomes a physical resource budget. The conservation law enforces: every watt-hour consumed reduces alpha mass by 1000 bytes. Every megabyte transferred reduces beta mass. Every sensor read reduces epsilon mass. There is no separate accounting for each resource — mass IS the account.

---

## 2. Physical Resource as Key Class

### 2.1 The Conversion Factor

Each physical resource type maps to an AMT key class via a fixed conversion factor:

```
mass_bytes = physical_units × conversion_factor
```

This mapping is bidirectional:

```
physical_units = mass_bytes / conversion_factor
```

An agent with 50,000 bytes of alpha mass has a 50 Wh battery budget (50,000 / 1000). An agent with 100 bytes of beta mass has a 100 MB bandwidth budget (100 / 1). The conversion factors are design decisions frozen at system setup — they calibrate the relationship between abstract mass and physical reality.

### 2.2 Layer Composition as Resource Allocation

An agent's layers are organized by key class. The `ResourceBudget` class converts physical budgets into layer specifications:

```python
ResourceBudget(
    battery_wh=50.0,      # → alpha layers: 50,000 bytes
    bandwidth_mb=100.0,   # → beta layers: 100 bytes
    storage_ops=500.0,    # → gamma layers: 50,000 bytes
    cpu_seconds=30.0,     # → delta layers: 15,000 bytes
    sensor_reads=50,      # → epsilon layers: 2,500 bytes
)
```

Each resource is encoded as multiple layers — some carrying data (signal potential), some empty (pure cost). This mirrors reality: real resource consumption always has overhead.

### 2.3 Mass Profile as Physical Budget

An agent's `mass_profile()` returns mass by key class. This can be reverse-interpreted as physical budgets:

```
profile = {"alpha": 45000, "beta": 80, "gamma": 30000, "delta": 10000, "epsilon": 1500}
→ battery: 45.0 Wh, bandwidth: 80.0 MB, storage: 300 ops, cpu: 20.0 s, sensor: 30 reads
```

An external observer seeing the agent's mass profile knows exactly what physical resources remain — without knowing the agent's identity, intent, or history.

---

## 3. Connectivity Environments

### 3.1 Location as Physics

Each physical location is a `ConnectivityEnvironment` with:
- Available resources (which physical resources exist here)
- Consumed resources (which resources are actively consumed by visiting)
- Dynamic mass gate (based on battery state)

The separation between *available* and *consumed* is critical. A campsite has CPU available (you can compute there) but doesn't actively consume CPU (you're not driving). The node only holds key secrets for consumed resources — unconsumed resources pass through safely.

### 3.2 The Viking Route

We model five locations representing a smart RV travel route:

```
campsite     →     highway     →     mountain     →     remote     →     destination
[shore power]   [cellular]       [satellite]       [off-grid]       [shore power]
wifi+sensor    battery+bw       battery+bw        battery+cpu      bw+storage
```

**Campsite** (shore power): No battery key — shore power means unlimited electricity. Consumes bandwidth (wifi sync) and sensor reads. Battery layers pass through safely.

**Highway** (cellular): On battery. Consumes battery (alpha) and bandwidth (beta — cellular data). Storage, CPU, sensor layers are safe.

**Mountain** (satellite): Extreme conditions. Consumes battery and bandwidth (satellite is expensive). Same key set as highway but with tighter mass gates.

**Remote** (off-grid): No bandwidth at all. Consumes battery and CPU (local processing only). Bandwidth layers are completely safe — the off-grid environment has no beta key.

**Destination** (shore power): Arrived. Consumes bandwidth (uploading results) and storage (saving data). No battery key — shore power again.

### 3.3 Dynamic Mass Gates

Mass gates are computed from battery state:

| Battery Level | Max Agent Mass |
|--------------|---------------|
| > 80% | 10 MB |
| 50-80% | 5 MB |
| 20-50% | 2 MB |
| < 20% | 500 KB |
| Shore power | Unlimited |

As battery depletes at a location (from previous agents consuming it), the mass gate tightens. Heavier agents get blocked. This creates natural load-shedding without any load-balancing algorithm.

---

## 4. Selective Resource Consumption

### 4.1 The Consumed Parameter

Each location specifies which resources it actively consumes:

```python
topo.add_location("campsite", "campsite_wifi",
    bandwidth_mbps=10.0,    # available and consumed
    storage_ops=500.0,      # available but NOT consumed
    cpu_seconds=30.0,       # available but NOT consumed
    sensor_reads=50,        # available and consumed
    consumed=["bandwidth", "sensor"],  # only these strip layers
)
```

Resources not in the `consumed` list are tracked (for display and planning) but don't contribute their key secret to the node. An agent visiting the campsite keeps its storage, CPU, and battery layers intact.

### 4.2 Safe Passage

When a resource's key class is absent from the environment, layers of that class pass through unstripped. This has profound implications:

- **Off-grid** (no beta key): Bandwidth layers are preserved. An agent that carefully avoids off-grid locations retains its bandwidth budget. An agent forced through off-grid keeps bandwidth but loses battery and CPU.

- **Shore power** (no alpha key): Battery layers are preserved. Connecting to shore power "saves" your battery budget by not consuming it.

This isn't a feature — it's a consequence of key affinity. The conservation law doesn't know about "safe passage." It simply has no key to decrypt those layers.

---

## 5. Experimental Results

### 5.1 Full-Route Traversal

A well-resourced agent (50 Wh, 100 MB, 500 ops, 30 CPU-sec, 50 sensor reads; 458 layers, 106,603 B) traverses the full route:

| Location | Mass Before | Mass After | Layers Stripped | Key Insight |
|----------|------------|------------|----------------|-------------|
| Campsite | 106,603 | 104,284 | ~4 | Only beta+epsilon consumed (shore power) |
| Highway | 104,284 | 58,888 | ~117 | Heavy alpha+beta consumption (driving+cellular) |
| Mountain | 58,888 | 58,888 | 0 | No remaining alpha/beta layers to strip |
| Remote | 58,888 | 45,396 | ~19 | Alpha+delta consumed (battery+CPU) |
| Destination | 45,396 | 0 | ~78 | Beta+gamma consumed (upload+save), death |

Conservation violations: **0**

### 5.2 Environment Transition Analysis

The transition pattern reveals how resource classes are selectively consumed:

```
campsite:     4 layers stripped  (beta, epsilon)
highway:    117 layers stripped  (alpha, beta)
mountain:     0 layers stripped  (alpha, beta — already exhausted)
remote:      19 layers stripped  (alpha, delta)
destination: 78 layers stripped  (beta, gamma)
```

Notice: mountain strips zero layers because the agent already lost all its alpha and beta layers at highway. The agent "coasts" through mountain on inertia — its remaining mass is in gamma, delta, and epsilon classes that mountain doesn't consume.

### 5.3 Population Scale

150 agents with varied budgets (5-60 Wh battery, 1-80 MB bandwidth, 10-300 storage ops, 1-25 CPU-sec, 2-40 sensor reads):

| Metric | Value |
|--------|-------|
| Agents | 150 |
| Total interactions | 750 |
| Total layers stripped | 32,486 |
| Conservation violations | **0** |

Every agent completes the full 5-location route. Resource consumption varies by budget size but conservation holds universally.

---

## 6. The Viking Integration (Future Work)

The reference implementation maps directly to The Viking's Sleipner server:

### 6.1 Real-Time Resource Sources

| AMT Resource | Viking Source | API |
|-------------|-------------|-----|
| Battery (alpha) | Anker F3800 | Home Assistant sensor `sensor.f3800_battery_level` |
| Bandwidth (beta) | Starlink + Cellular | Home Assistant + bandwidth monitoring |
| Storage (gamma) | NVMe SSD | System disk I/O counters |
| CPU (delta) | Sleipner AMD | System CPU time accounting |
| Sensor (epsilon) | Zigbee sensors | Zigbee2MQTT via Home Assistant |

### 6.2 Dynamic Mass Gate from Battery

The Anker F3800's SOC (state of charge) maps directly to mass gate thresholds:

```
SOC > 80%:   max_mass = 10 MB  (full operations)
SOC 50-80%:  max_mass = 5 MB   (moderate operations)
SOC 20-50%:  max_mass = 2 MB   (conservation mode)
SOC < 20%:   max_mass = 500 KB (emergency only)
```

Home Assistant automation updates the mass gate in real time:

```yaml
automation:
  - trigger:
      - platform: numeric_state
        entity_id: sensor.f3800_battery_level
        below: 20
    action:
      - service: amt.update_mass_gate
        data:
          max_mass: 512000  # 500 KB
```

### 6.3 Connectivity-Based Key Rotation

When The Viking moves from wifi to cellular to satellite to off-grid, the available key classes change:

- **Shore power + wifi**: All keys available
- **Battery + cellular**: Alpha + beta keys
- **Battery + satellite**: Alpha + beta keys (different beta cost)
- **Battery only**: Alpha + delta + epsilon keys (no network)

This is exactly the travel route modeled in our demo. Real-time connectivity transitions trigger key class rotation in the environment.

---

## 7. Discussion

### 7.1 Advantages

**Unified accounting**: One conservation law governs all resource types. No separate power manager, bandwidth throttler, and storage quota system.

**Physical enforcement**: Conservation prevents overconsumption by construction. An agent with zero alpha mass cannot consume battery — not because a policy blocks it, but because there are no layers to decrypt.

**Auditability**: Every watt-hour, megabyte, CPU-second, and sensor read is accounted for via merkle-anchored ledger. Perfect resource accounting without surveillance.

### 7.2 Limitations

**Calibration**: The conversion factors (1 Wh = 1000 B) are design decisions. Real-world calibration requires measuring actual resource consumption per layer interaction.

**Static conversion**: The current model uses fixed conversion factors. Dynamic pricing (battery cheaper during solar charging) would require runtime factor adjustment.

**Environmental modeling**: Real environments have continuous resource availability changes, not discrete location-based transitions. A moving RV's connectivity changes continuously.

### 7.3 Generalization

This mapping applies to any resource-constrained system:

- **Spacecraft**: Power budget, comms window, attitude control fuel, instrument time
- **Field sensors**: Battery, cellular data plan, flash wear, sensor lifetime
- **Mobile robots**: Battery, wireless bandwidth, onboard storage, actuator cycles

The conservation law doesn't know about watts, bytes, or CPU seconds. It knows about mass, signal, and loss. The mapping is in the conversion factor.

---

## 8. Conclusion

AMT's conservation law enforces physical resource limits through mass physics. By mapping each resource type to a key class with a fixed conversion factor:

- **Battery management** becomes alpha-mass conservation
- **Bandwidth metering** becomes beta-layer stripping
- **Storage accounting** becomes gamma-mass tracking
- **CPU budgeting** becomes delta-layer consumption
- **Sensor access** becomes epsilon-mass depletion

No power management daemon. No bandwidth throttler. No storage quota. No CPU governor. Just conservation.

At population scale (150 agents, 750 interactions), zero conservation violations occur. The conservation law is the resource manager. The math is the physics. The physics is the budget.

---

## Appendix A: Implementation

Reference implementation:

- `amt_physical_iot.py`: Extension module (PhysicalResource, ConnectivityEnvironment, ResourceBudget, PhysicalTopology, ResourceAuditReport)
- `amt_physical_iot_demo.py`: Six-demo demonstration script

Key design decisions:
- `consumed` parameter separates resource availability from consumption
- Dynamic mass gates computed from battery state
- `_safe_risk_tolerance()` handles complex number bug from fractional exponents
