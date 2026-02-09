"""
Agent Mass Theory (AMT) — Reference Implementation
====================================================

Mathematical Foundation for Finite-Energy Agent Existence

Conservation Law:
    C_{n+1} + S_{n+1} + L_n = C_n

Where:
    C_n  = cipher mass at state n (total encrypted bytes)
    S_n  = signal extracted (information yield from non-empty layers)
    L_n  = loss incurred (mass consumed without information yield)

Key Definitions:
    - Layer: The atomic unit of agent mass. An encrypted container that may
      or may not hold data. Encrypted under a key_class.
    - Key Class: A category identifier. Layers encrypted under class "alpha"
      can only be decrypted by environments holding the "alpha" secret.
    - Multi-Class Key (Hazardous): An environment holding secrets for multiple
      key classes. Can strip multiple layer types simultaneously.
    - Mass: Total bytes of all encrypted layers. This IS the agent.
    - Energy: Remaining decryptable potential. When mass = 0, the agent is dead.
    - Signal: Data extracted from non-empty decrypted layers.
    - Loss: Mass consumed from empty layers or encryption overhead.
    - ΔL: Loss differential vector across key classes between interactions.

Cryptographic Primitives:
    - AES-256-GCM per layer
    - Key derivation: HKDF-SHA256(master_secret, salt=key_class)
    - Each key_class maps to a deterministic symmetric key
    - Layers are independently encrypted — no nesting dependency

Author: Ravenhelm / Nate Walker
Date: 2026-02-08
"""

import os
import json
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


# =============================================================================
# §1  CRYPTOGRAPHIC PRIMITIVES
# =============================================================================

def derive_key(master_secret: bytes, key_class: str) -> bytes:
    """
    Derive a 256-bit AES key from a master secret and key class.
    
    K_c = HKDF-SHA256(master_secret, salt=SHA256(key_class), info=b"amt-layer")
    
    This ensures:
    - Same master_secret + same key_class → same key (deterministic)
    - Different key_classes → different keys (class isolation)
    - Environment must possess master_secret to derive any key
    """
    salt = hashlib.sha256(key_class.encode()).digest()
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"amt-layer",
    )
    return hkdf.derive(master_secret)


def encrypt_layer(key: bytes, plaintext: bytes) -> bytes:
    """
    Encrypt a layer payload using AES-256-GCM.
    
    Output format: nonce (12 bytes) || ciphertext+tag
    
    The encrypted output is the layer's contribution to agent mass.
    |encrypted_layer| > |plaintext| always (nonce + tag overhead).
    This overhead IS the entropy cost of existence.
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def decrypt_layer(key: bytes, encrypted: bytes) -> bytes:
    """
    Decrypt a layer. Returns plaintext (may be empty bytes b"").
    
    Raises InvalidTag if key doesn't match — the environment
    lacks affinity for this layer class.
    """
    aesgcm = AESGCM(key)
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)


# =============================================================================
# §2  LAYER — THE ATOMIC UNIT OF MASS
# =============================================================================

@dataclass
class Layer:
    """
    A single encrypted layer. The penny primitive.
    
    Properties:
        key_class:  Which environmental key can decrypt this layer
        encrypted:  The encrypted bytes (this IS the mass contribution)
        mass:       len(encrypted) — the physical weight in bytes
    
    A layer with empty payload (b"") still has mass due to encryption
    overhead. This mass is pure loss when decrypted — a toll, a tax,
    friction. But its absence is signal: "this class was represented
    but carried no information."
    """
    key_class: str
    encrypted: bytes
    
    @property
    def mass(self) -> int:
        """Mass in bytes. This is the layer's contribution to agent weight."""
        return len(self.encrypted)
    
    def __repr__(self):
        return f"Layer(class={self.key_class}, mass={self.mass}B)"


# =============================================================================
# §3  DECRYPTION RESULT — THE INTERACTION PRODUCT
# =============================================================================

@dataclass
class DecryptionResult:
    """
    The product of an environmental interaction with a single layer.
    
    When the environment decrypts a layer:
        - signal:       bytes of meaningful data extracted (may be 0)
        - loss:         bytes of mass consumed without information yield
        - mass_consumed: total mass removed from the agent
        - key_class:    which class was decrypted
        - had_data:     whether the layer contained information
    
    Conservation per layer:
        mass_consumed = signal + loss
    
    Where:
        signal = len(plaintext) if plaintext != b"" else 0
        loss   = mass_consumed - signal
               = encryption_overhead + (len(plaintext) if empty else 0)
    """
    key_class: str
    mass_consumed: int
    signal: int
    loss: int
    had_data: bool
    plaintext: Optional[bytes] = None
    
    @property
    def signal_ratio(self) -> float:
        """S/M ratio. 1.0 = pure signal. 0.0 = pure loss."""
        if self.mass_consumed == 0:
            return 0.0
        return self.signal / self.mass_consumed


# =============================================================================
# §4  AGENT — THE MASS PAYLOAD
# =============================================================================

@dataclass
class Agent:
    """
    An agent is nothing but its layers. No core. No identity field.
    When the last layer is decrypted, the agent ceases to exist.
    
    The agent CANNOT:
        - decrypt its own layers
        - observe which layer was decrypted
        - know what data it carries
        - know its own key class distribution
    
    The agent CAN observe:
        - its total mass (scalar)
        - mass delta after interaction (scalar)
        - it is alive (mass > 0)
    
    Everything else is opaque to the agent.
    """
    layers: list[Layer] = field(default_factory=list)
    
    # --- Interaction history (observable by external systems, not the agent) ---
    _interaction_log: list[dict] = field(default_factory=list, repr=False)
    
    @property
    def mass(self) -> int:
        """Total mass in bytes. The agent's weight."""
        return sum(layer.mass for layer in self.layers)
    
    @property
    def alive(self) -> bool:
        """An agent exists if and only if it has mass."""
        return self.mass > 0
    
    @property
    def layer_count(self) -> int:
        """Number of remaining layers."""
        return len(self.layers)
    
    def mass_profile(self) -> dict[str, int]:
        """
        Distribution of mass by key class.
        
        NOTE: This is an EXTERNAL observation. The agent itself
        cannot call this. Only the system/creator can inspect
        the class distribution at build time.
        """
        profile = {}
        for layer in self.layers:
            profile[layer.key_class] = profile.get(layer.key_class, 0) + layer.mass
        return profile
    
    def __repr__(self):
        return f"Agent(layers={self.layer_count}, mass={self.mass}B, alive={self.alive})"


# =============================================================================
# §5  ENVIRONMENT — THE DECRYPTOR
# =============================================================================

@dataclass
class Environment:
    """
    An environment holds key class secrets and decrypts agent layers.
    
    The environment is the active party. The agent is passive.
    The agent does not choose what to spend. The environment
    chooses what to take.
    
    Properties:
        name:           Human-readable identifier
        secrets:        dict of {key_class: master_secret}
        mass_threshold: (min, max) — agents outside this range cannot enter
    
    A multi-class environment (len(secrets) > 1) is HAZARDOUS.
    It can strip multiple layer types simultaneously.
    The more classes an environment can decrypt, the more corrosive it is.
    
    Hazard Rating:
        H(env) = |secrets| / |all_possible_classes|
    
    H = 0: inert (no keys, no decryption, safe passage)
    H = 1: universal solvent (can decrypt everything, maximum corrosion)
    """
    name: str
    secrets: dict[str, bytes] = field(default_factory=dict)
    mass_threshold: tuple[int, int] = (0, float('inf'))  # (min, max) bytes
    
    @property
    def key_classes(self) -> set[str]:
        """Set of key classes this environment can decrypt."""
        return set(self.secrets.keys())
    
    @property
    def hazard_classes(self) -> int:
        """Number of key classes this environment can strip."""
        return len(self.secrets)
    
    def can_enter(self, agent: Agent) -> bool:
        """
        Mass-gated access. Pure physics, not permission.
        
        A 3GB agent cannot fit through a node sized for 50MB
        the same way a bowling ball can't fit through a garden hose.
        """
        min_mass, max_mass = self.mass_threshold
        return min_mass <= agent.mass <= max_mass
    
    def derive_key_for_class(self, key_class: str) -> Optional[bytes]:
        """Derive the AES key for a given class, if we hold the secret."""
        if key_class not in self.secrets:
            return None
        return derive_key(self.secrets[key_class], key_class)
    
    def __repr__(self):
        return (f"Environment({self.name}, classes={self.key_classes}, "
                f"hazard={self.hazard_classes}, "
                f"mass_window={self.mass_threshold})")


# =============================================================================
# §6  INTERACTION — THE PHYSICS ENGINE
# =============================================================================

@dataclass 
class InteractionResult:
    """
    Complete result of an agent-environment interaction.
    
    Fields:
        agent_survived:     Agent still has mass after interaction
        mass_before:        Agent mass before interaction
        mass_after:         Agent mass after interaction
        total_signal:       Total information extracted (bytes)
        total_loss:         Total mass consumed without information (bytes)
        total_consumed:     Total mass removed from agent
        layers_stripped:     Number of layers decrypted
        per_layer:          Individual decryption results
        delta_L:            Loss differential vector by key class
        signal_ratio:       Overall S/(S+L) efficiency
        agent_could_enter:  Whether the agent fit through the mass gate
    """
    agent_survived: bool
    agent_could_enter: bool
    mass_before: int
    mass_after: int
    total_signal: int
    total_loss: int
    total_consumed: int
    layers_stripped: int
    per_layer: list[DecryptionResult]
    delta_L: dict[str, float]
    
    @property
    def signal_ratio(self) -> float:
        if self.total_consumed == 0:
            return 0.0
        return self.total_signal / self.total_consumed
    
    @property 
    def mass_delta(self) -> int:
        """How much lighter the agent got. Always >= 0."""
        return self.mass_before - self.mass_after
    
    def summary(self) -> str:
        lines = [
            f"{'═' * 60}",
            f"  INTERACTION REPORT",
            f"{'─' * 60}",
            f"  Could enter:     {self.agent_could_enter}",
            f"  Mass before:     {self.mass_before:,} B",
            f"  Mass after:      {self.mass_after:,} B",
            f"  Mass consumed:   {self.total_consumed:,} B",
            f"  Layers stripped:  {self.layers_stripped}",
            f"  Signal yield:    {self.total_signal:,} B",
            f"  Loss:            {self.total_loss:,} B",
            f"  Signal ratio:    {self.signal_ratio:.3f}",
            f"  Agent alive:     {self.agent_survived}",
            f"{'─' * 60}",
            f"  ΔL Vector (loss by class):",
        ]
        for cls, loss in sorted(self.delta_L.items()):
            lines.append(f"    {cls:>12s}: {loss:,.0f} B")
        lines.append(f"{'═' * 60}")
        return "\n".join(lines)


def interact(agent: Agent, env: Environment) -> InteractionResult:
    """
    The fundamental operation: environment acts upon agent.
    
    Algorithm:
        1. Check mass gate — can the agent physically enter?
        2. For each layer the environment has affinity for:
           a. Decrypt the layer
           b. Measure signal (non-empty plaintext) and loss
           c. Remove the layer from the agent
        3. Compute ΔL vector — loss distribution across key classes
        4. Record interaction
        5. Return complete measurement
    
    The agent does NOT participate in this process.
    The agent is acted upon.
    
    Conservation law verified per interaction:
        mass_before = mass_after + total_signal + total_loss
    """
    mass_before = agent.mass
    
    # --- Mass gate check ---
    if not env.can_enter(agent):
        return InteractionResult(
            agent_survived=agent.alive,
            agent_could_enter=False,
            mass_before=mass_before,
            mass_after=mass_before,
            total_signal=0,
            total_loss=0,
            total_consumed=0,
            layers_stripped=0,
            per_layer=[],
            delta_L={},
        )
    
    # --- Decrypt all layers the environment has affinity for ---
    results = []
    surviving_layers = []
    
    for layer in agent.layers:
        key = env.derive_key_for_class(layer.key_class)
        
        if key is None:
            # Environment has no affinity for this class — layer survives
            surviving_layers.append(layer)
            continue
        
        # Decryption — the environment acts
        try:
            plaintext = decrypt_layer(key, layer.encrypted)
        except Exception:
            # Key derivation mismatch — shouldn't happen with correct secrets
            surviving_layers.append(layer)
            continue
        
        # Measure signal and loss
        signal = len(plaintext) if plaintext != b"" else 0
        loss = layer.mass - signal  # Encryption overhead + empty payload cost
        
        result = DecryptionResult(
            key_class=layer.key_class,
            mass_consumed=layer.mass,
            signal=signal,
            loss=loss,
            had_data=(plaintext != b""),
            plaintext=plaintext if plaintext != b"" else None,
        )
        results.append(result)
    
    # --- Update agent (layer removal) ---
    agent.layers = surviving_layers
    
    # --- Compute totals ---
    total_signal = sum(r.signal for r in results)
    total_loss = sum(r.loss for r in results)
    total_consumed = sum(r.mass_consumed for r in results)
    
    # --- Compute ΔL vector (loss by key class) ---
    delta_L = {}
    for r in results:
        delta_L[r.key_class] = delta_L.get(r.key_class, 0) + r.loss
    
    # --- Conservation law assertion ---
    mass_after = agent.mass
    assert mass_before == mass_after + total_signal + total_loss, (
        f"Conservation violation: {mass_before} != {mass_after} + {total_signal} + {total_loss}"
    )
    
    # --- Log interaction (external record, not agent-visible) ---
    agent._interaction_log.append({
        "environment": env.name,
        "mass_before": mass_before,
        "mass_after": mass_after,
        "signal": total_signal,
        "loss": total_loss,
        "layers_stripped": len(results),
        "delta_L": delta_L,
    })
    
    return InteractionResult(
        agent_survived=agent.alive,
        agent_could_enter=True,
        mass_before=mass_before,
        mass_after=mass_after,
        total_signal=total_signal,
        total_loss=total_loss,
        total_consumed=total_consumed,
        layers_stripped=len(results),
        per_layer=results,
        delta_L=delta_L,
    )


# =============================================================================
# §7  AGENT FACTORY — CONSTRUCTING MASS PAYLOADS
# =============================================================================

class AgentFactory:
    """
    Builds agents by stacking encrypted layers.
    
    The factory holds the master secrets for all key classes.
    This is the GOD ROLE — it knows everything about the agent
    at creation time. Once deployed, this knowledge is irrelevant.
    The agent is on its own. The environment decides its fate.
    """
    
    def __init__(self, master_secrets: dict[str, bytes]):
        """
        Args:
            master_secrets: {key_class: master_secret} for all classes
                           the factory can encode.
        """
        self.master_secrets = master_secrets
    
    def create_layer(self, key_class: str, payload: bytes = b"") -> Layer:
        """
        Create a single encrypted layer (one penny).
        
        Args:
            key_class: Which environmental key class can decrypt this
            payload:   Data to encode. b"" = empty layer (pure cost, but signal in absence)
        
        Returns:
            Layer with encrypted payload. Mass = len(encrypted).
        """
        if key_class not in self.master_secrets:
            raise ValueError(f"Unknown key class: {key_class}")
        
        key = derive_key(self.master_secrets[key_class], key_class)
        encrypted = encrypt_layer(key, payload)
        return Layer(key_class=key_class, encrypted=encrypted)
    
    def build_agent(self, layer_specs: list[tuple[str, bytes]]) -> Agent:
        """
        Build an agent from a list of (key_class, payload) tuples.
        
        Example:
            factory.build_agent([
                ("alpha", b"mission: observe"),
                ("alpha", b""),                    # empty alpha layer
                ("beta", b"capability: search"),
                ("gamma", b""),                    # empty gamma layer
                ("gamma", b""),                    # another empty gamma
            ])
        
        The agent's total mass = sum of all encrypted layer sizes.
        The agent cannot see any of this.
        """
        layers = [self.create_layer(cls, payload) for cls, payload in layer_specs]
        return Agent(layers=layers)
    
    def build_uniform_agent(
        self, 
        key_class: str, 
        data_layers: int, 
        empty_layers: int,
        payload_size: int = 64,
    ) -> Agent:
        """
        Build an agent with uniform layers of a single class.
        
        Args:
            key_class:    Key class for all layers
            data_layers:  Number of layers containing random data
            empty_layers: Number of empty layers (pure cost)
            payload_size: Bytes per data layer
        """
        specs = []
        for _ in range(data_layers):
            specs.append((key_class, os.urandom(payload_size)))
        for _ in range(empty_layers):
            specs.append((key_class, b""))
        return Agent(layers=specs and [self.create_layer(c, p) for c, p in specs])
    
    def build_mixed_agent(
        self,
        class_distribution: dict[str, tuple[int, int]],
        payload_size: int = 64,
    ) -> Agent:
        """
        Build an agent with layers across multiple key classes.
        
        Args:
            class_distribution: {key_class: (data_layers, empty_layers)}
            payload_size:       Bytes per data layer
        
        Example:
            factory.build_mixed_agent({
                "alpha": (5, 3),   # 5 data + 3 empty alpha layers
                "beta":  (2, 1),   # 2 data + 1 empty beta layer
                "gamma": (0, 10),  # 10 empty gamma layers (pure toll)
            })
        """
        layers = []
        for key_class, (data_count, empty_count) in class_distribution.items():
            for _ in range(data_count):
                layers.append(self.create_layer(key_class, os.urandom(payload_size)))
            for _ in range(empty_count):
                layers.append(self.create_layer(key_class, b""))
        return Agent(layers=layers)


# =============================================================================
# §8  ACCRETION — GAINING MASS
# =============================================================================

def accrete(agent: Agent, new_layers: list[Layer]) -> int:
    """
    Add layers to an agent. This is how agents gain energy.
    
    The environment (or a factory, or another agent's exhaust) can
    wrap new encrypted layers around the agent's existing stack.
    
    Args:
        agent:      The agent to add mass to
        new_layers: Layers to wrap around the agent
    
    Returns:
        Mass added in bytes
    
    Note: The agent doesn't know what was added. It only knows
    it got heavier.
    """
    mass_before = agent.mass
    agent.layers.extend(new_layers)
    return agent.mass - mass_before


# =============================================================================
# §9  STATIC KEY HAZARD ANALYSIS
# =============================================================================

def hazard_rating(env: Environment, agent: Agent) -> dict:
    """
    Compute the hazard an environment poses to a specific agent.
    
    A "static key" (multi-class key) is hazardous because it can
    decrypt multiple layer types simultaneously. An environment
    with keys for classes {alpha, beta, gamma} will strip ALL
    layers of those classes in a single interaction.
    
    Returns:
        {
            "can_enter": bool,
            "vulnerable_mass": int,      # bytes at risk
            "vulnerable_ratio": float,   # fraction of total mass at risk
            "vulnerable_layers": int,    # layer count at risk
            "safe_mass": int,            # bytes safe from this env
            "hazard_classes": set,       # which classes are threatened
            "safe_classes": set,         # which classes are safe
            "lethality": float,          # 0.0 = harmless, 1.0 = instant death
        }
    """
    if not env.can_enter(agent):
        return {
            "can_enter": False,
            "vulnerable_mass": 0,
            "vulnerable_ratio": 0.0,
            "vulnerable_layers": 0,
            "safe_mass": agent.mass,
            "hazard_classes": set(),
            "safe_classes": set(),
            "lethality": 0.0,
        }
    
    vulnerable_mass = 0
    vulnerable_layers = 0
    safe_mass = 0
    hazard_classes = set()
    safe_classes = set()
    
    for layer in agent.layers:
        if layer.key_class in env.key_classes:
            vulnerable_mass += layer.mass
            vulnerable_layers += 1
            hazard_classes.add(layer.key_class)
        else:
            safe_mass += layer.mass
            safe_classes.add(layer.key_class)
    
    total_mass = agent.mass
    vulnerable_ratio = vulnerable_mass / total_mass if total_mass > 0 else 0.0
    
    return {
        "can_enter": True,
        "vulnerable_mass": vulnerable_mass,
        "vulnerable_ratio": vulnerable_ratio,
        "vulnerable_layers": vulnerable_layers,
        "safe_mass": safe_mass,
        "hazard_classes": hazard_classes,
        "safe_classes": safe_classes,
        "lethality": vulnerable_ratio,  # 1.0 = all mass at risk = potential death
    }


# =============================================================================
# §10  TRAJECTORY — MULTI-ENVIRONMENT TRAVERSAL
# =============================================================================

def traverse(agent: Agent, environments: list[Environment], verbose: bool = True) -> list[InteractionResult]:
    """
    Send an agent through a sequence of environments.
    
    This simulates the agent's lifecycle: creation → traversal → death.
    At each environment:
        1. Check mass gate
        2. Decrypt vulnerable layers
        3. Measure signal, loss, ΔL
        4. Check survival
    
    Returns the full interaction history.
    """
    results = []
    
    if verbose:
        print(f"\n{'▓' * 60}")
        print(f"  TRAVERSAL START")
        print(f"  Agent: {agent}")
        print(f"  Environments: {len(environments)}")
        print(f"{'▓' * 60}\n")
    
    for i, env in enumerate(environments):
        if not agent.alive:
            if verbose:
                print(f"  ✖ Agent is DEAD. Traversal halted at environment {i}.")
            break
        
        if verbose:
            print(f"  → Entering: {env.name}")
        
        result = interact(agent, env)
        results.append(result)
        
        if verbose:
            if not result.agent_could_enter:
                print(f"    ✖ BLOCKED — agent mass {result.mass_before}B "
                      f"outside window {env.mass_threshold}")
            else:
                print(result.summary())
            
            if not result.agent_survived:
                print(f"\n  ╔{'═' * 56}╗")
                print(f"  ║  AGENT DEATH — all layers consumed.{' ' * 18}║")
                print(f"  ║  No mass. No energy. No existence.{' ' * 19}║")
                print(f"  ╚{'═' * 56}╝\n")
    
    return results


# =============================================================================
# §11  CONSERVATION LAW VERIFICATION
# =============================================================================

def verify_conservation(results: list[InteractionResult]) -> bool:
    """
    Verify the conservation law across a full traversal.
    
    For each interaction:
        C_n = C_{n+1} + S_n + L_n
        mass_before = mass_after + signal + loss
    
    This is the second law of thermodynamics for digital agents.
    Potential always decreases. Signal costs energy.
    """
    all_valid = True
    for i, r in enumerate(results):
        if not r.agent_could_enter:
            continue
        lhs = r.mass_before
        rhs = r.mass_after + r.total_signal + r.total_loss
        valid = (lhs == rhs)
        if not valid:
            print(f"  ✖ Conservation VIOLATED at interaction {i}: {lhs} != {rhs}")
            all_valid = False
    return all_valid
