"""v1.0.1 ablation controls (review items 20, 21): matched depletion rate, honest signal/loss."""
import os
import random

from amt_core import AgentFactory, Environment, LAYER_OVERHEAD
from amt_ablation import interact_random, interact_random_matched


def _setup():
    secrets = {k: os.urandom(32) for k in ["alpha", "beta", "gamma"]}
    return secrets, AgentFactory(secrets)


def test_random_matched_removes_exactly_what_control_would():
    secrets, factory = _setup()
    env = Environment("alpha", {"alpha": secrets["alpha"]})
    random.seed(3)
    agent = factory.build_agent([("alpha", b"a" * 10)] * 4 + [("beta", b"b" * 10)] * 6)
    result = interact_random_matched(agent, env)
    assert result.layers_stripped == 4
    assert agent.layer_count == 6


def test_random_signal_and_loss_follow_layer_geometry():
    secrets, factory = _setup()
    env = Environment("alpha", {"alpha": secrets["alpha"]})
    random.seed(5)
    agent = factory.build_agent([("alpha", b"a" * 50), ("beta", b""), ("gamma", b"g" * 20)])
    before = agent.mass
    result = interact_random_matched(agent, env)  # removes 1 layer, class-blind
    assert result.layers_stripped == 1
    removed_mass = before - agent.mass
    expected_signal = max(0, removed_mass - LAYER_OVERHEAD)
    assert result.total_signal == expected_signal
    assert result.total_loss == removed_mass - expected_signal
    assert result.mass_before == result.mass_after + result.total_signal + result.total_loss


def test_unmatched_random_keeps_v1_rate_of_one_layer_per_key():
    secrets, factory = _setup()
    env = Environment("alpha", {"alpha": secrets["alpha"]})
    random.seed(9)
    agent = factory.build_agent([("alpha", b"a")] * 8)
    result = interact_random(agent, env)
    assert result.layers_stripped == 1


def test_random_matched_is_control_for_pure_class_agents():
    """Documented consequence: the selectivity fixture cannot separate structure from depletion."""
    secrets, factory = _setup()
    env = Environment("alpha", {"alpha": secrets["alpha"]})
    random.seed(11)
    agent = factory.build_agent([("alpha", b"a" * 8)] * 6)
    result = interact_random_matched(agent, env)
    assert result.layers_stripped == 6 and not agent.alive
