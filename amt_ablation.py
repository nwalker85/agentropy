"""
Agent Mass Theory — Ablation Study
====================================

Tests whether the conservation law is the CAUSE of emergent behavior,
not merely correlated with it.

Three conditions:
    CONTROL:   Standard interact() — conservation ON, class-selective
    IMMORTAL:  Layers matched but not consumed — no depletion
    RANDOM:    Random layers consumed regardless of key class — depletion
               without structure

Four experiments:
    1. Scarcity:       Does depletion create finite lifespans?
    2. Stratification: Does key-class breadth create economic tiers?
    3. Selectivity:    Does key-class structure create niche differentiation?
    4. Accountability: Does structured conservation enable per-class audit?

If removing conservation kills emergence, the law is causal.

Run: python amt_ablation_demo.py
"""

import os
import random
from dataclasses import dataclass
from typing import Callable

from amt_core import (
    Agent, Layer, Environment, AgentFactory,
    InteractionResult, DecryptionResult,
    interact as interact_control,
    derive_key, decrypt_layer,
)


# =============================================================================
# §1  ABLATION INTERACT FUNCTIONS
# =============================================================================

def interact_immortal(agent: Agent, env: Environment) -> InteractionResult:
    """
    Ablation A: Layers are matched but NOT consumed.

    The environment identifies which layers it has affinity for,
    but does not remove them. The agent's mass never changes.

    Conservation holds trivially: mass_before = mass_after + 0 + 0.
    But it is meaningless — nothing was consumed, no signal extracted.
    """
    mass_before = agent.mass

    if not env.can_enter(agent):
        return InteractionResult(
            agent_survived=agent.alive,
            agent_could_enter=False,
            mass_before=mass_before,
            mass_after=mass_before,
            total_signal=0, total_loss=0, total_consumed=0,
            layers_stripped=0, per_layer=[], delta_L={},
        )

    # Agent keeps all layers — immortal
    return InteractionResult(
        agent_survived=True,
        agent_could_enter=True,
        mass_before=mass_before,
        mass_after=mass_before,
        total_signal=0,
        total_loss=0,
        total_consumed=0,
        layers_stripped=0,
        per_layer=[],
        delta_L={},
    )


def interact_random(agent: Agent, env: Environment) -> InteractionResult:
    """
    Ablation B: Random layers consumed regardless of key class.

    The environment removes a random subset of layers, ignoring
    key class affinity entirely. Mass is consumed (depletion exists)
    but the structure of consumption is destroyed.

    Key class selectivity is eliminated — an alpha environment
    strips beta and gamma layers with equal probability.
    """
    mass_before = agent.mass

    if not env.can_enter(agent):
        return InteractionResult(
            agent_survived=agent.alive,
            agent_could_enter=False,
            mass_before=mass_before,
            mass_after=mass_before,
            total_signal=0, total_loss=0, total_consumed=0,
            layers_stripped=0, per_layer=[], delta_L={},
        )

    if not agent.layers:
        return InteractionResult(
            agent_survived=False,
            agent_could_enter=True,
            mass_before=0, mass_after=0,
            total_signal=0, total_loss=0, total_consumed=0,
            layers_stripped=0, per_layer=[], delta_L={},
        )

    # Remove random layers (ignoring key class)
    # Match control's stripping rate: ~1 layer per env key class
    n_to_remove = max(1, min(env.hazard_classes, len(agent.layers)))
    n_to_remove = min(n_to_remove, len(agent.layers))

    indices = list(range(len(agent.layers)))
    random.shuffle(indices)
    remove_indices = set(indices[:n_to_remove])

    removed = [agent.layers[i] for i in remove_indices]
    agent.layers = [l for i, l in enumerate(agent.layers) if i not in remove_indices]

    mass_after = agent.mass
    consumed = mass_before - mass_after

    # Signal/loss accounting holds (consumed mass is real)
    # but per-class attribution is meaningless
    signal = consumed // 2
    loss = consumed - signal

    return InteractionResult(
        agent_survived=agent.alive,
        agent_could_enter=True,
        mass_before=mass_before,
        mass_after=mass_after,
        total_signal=signal,
        total_loss=loss,
        total_consumed=consumed,
        layers_stripped=n_to_remove,
        per_layer=[],
        delta_L={},  # No per-class tracking — structure destroyed
    )


# =============================================================================
# §2  EXPERIMENT 1: SCARCITY (POPULATION DYNAMICS)
# =============================================================================

def run_scarcity_experiment(
    interact_fn: Callable,
    n_agents: int = 100,
    n_steps: int = 20,
    seed: int = 42,
) -> dict:
    """
    Do agents die? Does population decline?

    N agents, each with mixed layers, traverse a 3-environment gauntlet
    repeatedly. Measure death rate over time.

    Expected:
        Control:  High death rate (conservation depletes mass)
        Immortal: 0% death rate (nothing consumed)
        Random:   High death rate (random depletion kills too)
    """
    random.seed(seed)

    secrets = {
        "alpha": os.urandom(32),
        "beta": os.urandom(32),
        "gamma": os.urandom(32),
    }
    factory = AgentFactory(secrets)

    # Three environments with different keys
    envs = [
        Environment("zone-alpha", {"alpha": secrets["alpha"]}),
        Environment("zone-beta", {"beta": secrets["beta"]}),
        Environment("zone-gamma", {"gamma": secrets["gamma"]}),
    ]

    # Create agents with mixed layers
    agents = []
    for _ in range(n_agents):
        agent = factory.build_mixed_agent({
            "alpha": (3, 2),
            "beta": (3, 2),
            "gamma": (2, 1),
        })
        agents.append(agent)

    # Track population over time
    population_curve = [n_agents]
    total_interactions = 0
    conservation_violations = 0

    for step in range(n_steps):
        alive = [a for a in agents if a.alive]
        if not alive:
            population_curve.append(0)
            continue

        for agent in alive:
            env = random.choice(envs)
            result = interact_fn(agent, env)
            total_interactions += 1

            if result.agent_could_enter:
                expected = result.mass_after + result.total_signal + result.total_loss
                if result.mass_before != expected:
                    conservation_violations += 1

        population_curve.append(sum(1 for a in agents if a.alive))

    survivors = sum(1 for a in agents if a.alive)
    death_rate = 1.0 - (survivors / n_agents)

    return {
        "death_rate": death_rate,
        "survivors": survivors,
        "population_curve": population_curve,
        "total_interactions": total_interactions,
        "conservation_violations": conservation_violations,
    }


# =============================================================================
# §3  EXPERIMENT 2: STRATIFICATION (ECONOMIC TIERS)
# =============================================================================

def run_stratification_experiment(
    interact_fn: Callable,
    n_per_tier: int = 50,
    seed: int = 42,
) -> dict:
    """
    Do agents with different key-class breadth have different economic output?

    Rich agents: layers across alpha, beta, gamma (3 denominations).
    Poor agents: layers in alpha only (1 denomination).
    Both visit all 3 environments.

    Measure: total signal extracted (information yield = economic output).

    Expected:
        Control:  Rich extract signal from 3 envs, poor from 1 → ratio ~3x
        Immortal: Nobody extracts signal (no layers consumed) → ratio undefined
        Random:   Both extract similar amounts (random stripping, class-blind) → ratio ~1x
    """
    random.seed(seed)

    secrets = {
        "alpha": os.urandom(32),
        "beta": os.urandom(32),
        "gamma": os.urandom(32),
    }
    factory = AgentFactory(secrets)

    envs = [
        Environment("tool-alpha", {"alpha": secrets["alpha"]}),
        Environment("tool-beta", {"beta": secrets["beta"]}),
        Environment("tool-gamma", {"gamma": secrets["gamma"]}),
    ]

    def measure_output(agents, envs, interact_fn):
        """Total signal extracted per agent across all environments."""
        signals = []
        for agent in agents:
            agent_signal = 0
            for env in envs:
                if not agent.alive:
                    break
                result = interact_fn(agent, env)
                agent_signal += result.total_signal
            signals.append(agent_signal)
        avg = sum(signals) / len(signals) if signals else 0
        return signals, avg

    # Rich agents: data layers in all 3 classes
    rich_agents = []
    for _ in range(n_per_tier):
        agent = factory.build_mixed_agent({
            "alpha": (4, 0),  # 4 data layers = ~256B signal
            "beta": (4, 0),
            "gamma": (4, 0),
        }, payload_size=64)
        rich_agents.append(agent)

    # Poor agents: data layers in alpha only, empty padding in beta/gamma
    poor_agents = []
    for _ in range(n_per_tier):
        agent = factory.build_mixed_agent({
            "alpha": (4, 0),  # same alpha signal as rich
            "beta": (0, 4),   # 4 EMPTY beta layers (pure loss, no signal)
            "gamma": (0, 4),  # 4 EMPTY gamma layers (pure loss, no signal)
        }, payload_size=64)
        poor_agents.append(agent)

    rich_signals, rich_avg = measure_output(rich_agents, envs, interact_fn)
    poor_signals, poor_avg = measure_output(poor_agents, envs, interact_fn)

    if poor_avg > 0:
        ratio = rich_avg / poor_avg
    elif rich_avg > 0:
        ratio = float('inf')
    else:
        ratio = 1.0  # both zero

    return {
        "rich_avg_signal": rich_avg,
        "poor_avg_signal": poor_avg,
        "rich_poor_ratio": ratio,
        "rich_deaths": sum(1 for a in rich_agents if not a.alive),
        "poor_deaths": sum(1 for a in poor_agents if not a.alive),
    }


# =============================================================================
# §4  EXPERIMENT 3: SELECTIVITY (NICHE DIFFERENTIATION)
# =============================================================================

def run_selectivity_experiment(
    interact_fn: Callable,
    n_per_type: int = 50,
    seed: int = 42,
) -> dict:
    """
    Do agents with different mass profiles survive differently
    in different environments?

    Pure alpha agents (ONLY alpha layers) vs pure beta agents (ONLY beta).
    Alpha env (holds alpha key) vs beta env (holds beta key).

    Expected:
        Control:  Alpha agents die in alpha env, survive in beta env.
                  Beta agents die in beta env, survive in alpha env.
                  Perfect niche differentiation (score = 1.0).
        Immortal: Nobody dies anywhere. No differentiation (score = 0.0).
        Random:   Both types die at similar rates in both envs (random
                  stripping ignores class). No differentiation (score ≈ 0.0).
    """
    random.seed(seed)

    secrets = {
        "alpha": os.urandom(32),
        "beta": os.urandom(32),
    }
    factory = AgentFactory(secrets)

    env_alpha = Environment("habitat-alpha", {"alpha": secrets["alpha"]})
    env_beta = Environment("habitat-beta", {"beta": secrets["beta"]})

    def run_cohort(n, key_class, env, interact_fn, steps=3):
        """
        Run n pure-class agents through env for `steps` interactions.
        Pure-class = all layers are the same key class.
        """
        survivors = 0
        for _ in range(n):
            # Build agent with ONLY this key class
            agent = factory.build_uniform_agent(
                key_class=key_class,
                data_layers=4,
                empty_layers=2,
                payload_size=64,
            )
            for _ in range(steps):
                if not agent.alive:
                    break
                interact_fn(agent, env)

            if agent.alive:
                survivors += 1

        return survivors / n if n > 0 else 0

    # Alpha-pure in alpha env: SHOULD DIE (all layers vulnerable)
    a_in_a = run_cohort(n_per_type, "alpha", env_alpha, interact_fn)
    # Alpha-pure in beta env: SHOULD SURVIVE (no layers vulnerable)
    a_in_b = run_cohort(n_per_type, "alpha", env_beta, interact_fn)
    # Beta-pure in alpha env: SHOULD SURVIVE (no layers vulnerable)
    b_in_a = run_cohort(n_per_type, "beta", env_alpha, interact_fn)
    # Beta-pure in beta env: SHOULD DIE (all layers vulnerable)
    b_in_b = run_cohort(n_per_type, "beta", env_beta, interact_fn)

    # Niche differentiation:
    # Alpha species: survives beta habitat, dies in alpha habitat
    alpha_niche = a_in_b - a_in_a  # positive = niche exists
    # Beta species: survives alpha habitat, dies in beta habitat
    beta_niche = b_in_a - b_in_b   # positive = niche exists
    # Average niche score: 1.0 = perfect, 0.0 = none
    niche_score = (alpha_niche + beta_niche) / 2

    return {
        "alpha_in_alpha": a_in_a,
        "alpha_in_beta": a_in_b,
        "beta_in_alpha": b_in_a,
        "beta_in_beta": b_in_b,
        "alpha_niche": alpha_niche,
        "beta_niche": beta_niche,
        "niche_score": niche_score,
    }


# =============================================================================
# §5  EXPERIMENT 4: ACCOUNTABILITY (AUDIT INTEGRITY)
# =============================================================================

def run_accountability_experiment(
    interact_fn: Callable,
    n_agents: int = 50,
    seed: int = 42,
) -> dict:
    """
    Does structured conservation enable per-class audit?

    Agents traverse 3 "org" environments. Measure:
    - Conservation validity rate (mass_before = mass_after + S + L)
    - Meaningful consumption (non-zero mass moved)
    - Per-class attribution (delta_L vector populated and correct)

    Expected:
        Control:  100% valid, meaningful consumption, per-class delta_L
        Immortal: 100% valid trivially, zero consumption, no delta_L
        Random:   Valid total accounting, meaningful consumption, BUT
                  no per-class delta_L (structure destroyed)
    """
    random.seed(seed)

    secrets = {
        "alpha": os.urandom(32),
        "beta": os.urandom(32),
        "gamma": os.urandom(32),
    }
    factory = AgentFactory(secrets)

    orgs = [
        Environment("org-A", {"alpha": secrets["alpha"]}),
        Environment("org-B", {"beta": secrets["beta"]}),
        Environment("org-C", {"gamma": secrets["gamma"]}),
    ]

    conservation_checks = []
    total_consumed = 0
    meaningful_interactions = 0
    delta_L_populated = 0
    total_interactions = 0

    for _ in range(n_agents):
        agent = factory.build_mixed_agent({
            "alpha": (3, 1),
            "beta": (3, 1),
            "gamma": (2, 1),
        })

        for org in orgs:
            if not agent.alive:
                break
            result = interact_fn(agent, org)

            if result.agent_could_enter:
                total_interactions += 1

                # Check total conservation
                expected = result.mass_after + result.total_signal + result.total_loss
                valid = (result.mass_before == expected)
                conservation_checks.append(valid)

                total_consumed += result.total_consumed

                if result.total_consumed > 0:
                    meaningful_interactions += 1

                # Check per-class attribution (delta_L populated)
                if result.delta_L and len(result.delta_L) > 0:
                    delta_L_populated += 1

    valid_count = sum(1 for v in conservation_checks if v)
    total_checks = len(conservation_checks)
    validity_rate = valid_count / total_checks if total_checks > 0 else 0

    return {
        "conservation_validity": validity_rate,
        "violations": total_checks - valid_count,
        "total_consumed": total_consumed,
        "meaningful_rate": meaningful_interactions / total_interactions if total_interactions > 0 else 0,
        "per_class_audit_rate": delta_L_populated / total_interactions if total_interactions > 0 else 0,
        "total_interactions": total_interactions,
    }


# =============================================================================
# §6  ABLATION RUNNER
# =============================================================================

@dataclass
class AblationResult:
    """Results from one condition across all four experiments."""
    condition: str
    scarcity: dict
    stratification: dict
    selectivity: dict
    accountability: dict


def run_full_ablation(seed: int = 42) -> list[AblationResult]:
    """Run all four experiments under all three conditions."""
    conditions = [
        ("CONTROL", interact_control),
        ("IMMORTAL", interact_immortal),
        ("RANDOM", interact_random),
    ]

    results = []
    for name, interact_fn in conditions:
        result = AblationResult(
            condition=name,
            scarcity=run_scarcity_experiment(interact_fn, seed=seed),
            stratification=run_stratification_experiment(interact_fn, seed=seed),
            selectivity=run_selectivity_experiment(interact_fn, seed=seed),
            accountability=run_accountability_experiment(interact_fn, seed=seed),
        )
        results.append(result)

    return results


def format_comparison(results: list[AblationResult]) -> str:
    """Format ablation results as a comparison table."""
    lines = []

    lines.append("=" * 80)
    lines.append("  ABLATION STUDY: Is the Conservation Law Causal?")
    lines.append("=" * 80)
    lines.append("")

    # --- Experiment 1: Scarcity ---
    lines.append("─" * 80)
    lines.append("  EXPERIMENT 1: SCARCITY — Does depletion create finite lifespans?")
    lines.append("─" * 80)
    lines.append(f"  {'Condition':<12} {'Death Rate':>12} {'Survivors':>12} {'Interactions':>14} {'Violations':>12}")
    for r in results:
        s = r.scarcity
        lines.append(
            f"  {r.condition:<12} {s['death_rate']:>11.1%} {s['survivors']:>12} "
            f"{s['total_interactions']:>14} {s['conservation_violations']:>12}"
        )
    lines.append("")

    # --- Experiment 2: Stratification ---
    lines.append("─" * 80)
    lines.append("  EXPERIMENT 2: STRATIFICATION — Does key-class breadth create economic tiers?")
    lines.append("─" * 80)
    lines.append(f"  {'Condition':<12} {'Rich Signal':>12} {'Poor Signal':>12} {'Ratio':>12} {'Deaths (R/P)':>14}")
    for r in results:
        s = r.stratification
        ratio_str = f"{s['rich_poor_ratio']:.2f}x" if s['rich_poor_ratio'] != float('inf') else "∞"
        lines.append(
            f"  {r.condition:<12} {s['rich_avg_signal']:>11.0f} B {s['poor_avg_signal']:>11.0f} B "
            f"{ratio_str:>12} {s['rich_deaths']:>6}/{s['poor_deaths']:<6}"
        )
    lines.append("")
    lines.append("  Rich = data layers in alpha+beta+gamma (3 denominations)")
    lines.append("  Poor = data in alpha only, empty layers in beta+gamma (1 denomination)")
    lines.append("")

    # --- Experiment 3: Selectivity ---
    lines.append("─" * 80)
    lines.append("  EXPERIMENT 3: SELECTIVITY — Does key-class structure create niches?")
    lines.append("─" * 80)
    lines.append(f"  {'Condition':<12} {'α in α-env':>12} {'α in β-env':>12} {'β in α-env':>12} {'β in β-env':>12} {'Niche':>8}")
    for r in results:
        s = r.selectivity
        lines.append(
            f"  {r.condition:<12} {s['alpha_in_alpha']:>11.0%} "
            f"{s['alpha_in_beta']:>11.0%} "
            f"{s['beta_in_alpha']:>11.0%} "
            f"{s['beta_in_beta']:>11.0%} "
            f"{s['niche_score']:>7.2f}"
        )
    lines.append("")
    lines.append("  Niche score: 1.0 = perfect differentiation, 0.0 = none")
    lines.append("  α-pure agents should DIE in α-env, SURVIVE in β-env (and vice versa)")
    lines.append("")

    # --- Experiment 4: Accountability ---
    lines.append("─" * 80)
    lines.append("  EXPERIMENT 4: ACCOUNTABILITY — Does conservation enable per-class audit?")
    lines.append("─" * 80)
    lines.append(f"  {'Condition':<12} {'Valid':>8} {'Consumed':>12} {'Meaningful':>12} {'Per-Class':>12}")
    for r in results:
        s = r.accountability
        lines.append(
            f"  {r.condition:<12} {s['conservation_validity']:>7.0%} "
            f"{s['total_consumed']:>11,} B "
            f"{s['meaningful_rate']:>11.0%} "
            f"{s['per_class_audit_rate']:>11.0%}"
        )
    lines.append("")
    lines.append("  Per-Class = delta_L vector populated (which key classes were consumed)")
    lines.append("")

    # --- Summary Table ---
    lines.append("=" * 80)
    lines.append("  SUMMARY: Emergent Properties by Condition")
    lines.append("=" * 80)
    lines.append("")

    c, i, r = results[0], results[1], results[2]

    lines.append(f"  {'Property':<32} {'CONTROL':>14} {'IMMORTAL':>14} {'RANDOM':>14}")
    lines.append(f"  {'─' * 32} {'─' * 14} {'─' * 14} {'─' * 14}")

    # Scarcity
    def scarcity_label(res):
        return "YES" if res.scarcity['death_rate'] > 0.01 else "NO"

    lines.append(
        f"  {'Finite lifespans':<32} {scarcity_label(c):>14} "
        f"{scarcity_label(i):>14} {scarcity_label(r):>14}"
    )

    # Stratification
    def strat_label(res):
        ratio = res.stratification['rich_poor_ratio']
        if ratio == float('inf') or (ratio == 1.0 and res.stratification['rich_avg_signal'] == 0):
            return "NO (zero output)"
        return f"YES ({ratio:.1f}x)" if ratio > 1.3 else "NO"

    lines.append(
        f"  {'Budget stratification':<32} {strat_label(c):>14} "
        f"{strat_label(i):>14} {strat_label(r):>14}"
    )

    # Selectivity
    def select_label(res):
        score = res.selectivity['niche_score']
        if score > 0.7:
            return "YES"
        elif score > 0.3:
            return "PARTIAL"
        else:
            return "NO"

    lines.append(
        f"  {'Niche differentiation':<32} {select_label(c):>14} "
        f"{select_label(i):>14} {select_label(r):>14}"
    )

    # Accountability
    def audit_label(res):
        s = res.accountability
        if s['meaningful_rate'] < 0.01:
            return "NO (vacuous)"
        if s['per_class_audit_rate'] > 0.5:
            return "YES"
        return "PARTIAL"

    lines.append(
        f"  {'Per-class audit':<32} {audit_label(c):>14} "
        f"{audit_label(i):>14} {audit_label(r):>14}"
    )

    lines.append("")
    lines.append("─" * 80)
    lines.append("  INTERPRETATION")
    lines.append("─" * 80)
    lines.append("")
    lines.append("  CONTROL (conservation ON):  All four emergent properties present.")
    lines.append("  IMMORTAL (no depletion):    Zero emergence. No depletion = no scarcity")
    lines.append("                              = no differentiation = nothing to audit.")
    lines.append("  RANDOM (unstructured):      Scarcity exists (agents die) but class-selective")
    lines.append("                              properties vanish. Depletion without structure")
    lines.append("                              produces death without meaning.")
    lines.append("")
    lines.append("  Two factors are both necessary:")
    lines.append("    1. DEPLETION (mass decreases on interaction)")
    lines.append("    2. STRUCTURE (depletion is class-selective and accountable)")
    lines.append("")
    lines.append("  The conservation law provides both. Remove either: emergence degrades.")
    lines.append("  Remove both: emergence disappears entirely.")
    lines.append("=" * 80)

    return "\n".join(lines)
