"""The conservation identity and the layer geometry it rests on (paper Appendix B).

These tests make the paper's own statement executable: the identity holds because
`loss` is defined as `mass - signal`, and every layer carries exactly LAYER_OVERHEAD
bytes of nonce + tag.
"""
import os
import random

import pytest

from amt_core import Agent, AgentFactory, Environment, LAYER_OVERHEAD, interact

CLASSES = ["alpha", "beta", "gamma", "delta", "epsilon"]


@pytest.fixture
def secrets():
    return {k: os.urandom(32) for k in CLASSES}


@pytest.fixture
def factory(secrets):
    return AgentFactory(secrets)


def test_layer_geometry_is_overhead_plus_plaintext(factory):
    for n in (0, 1, 17, 256, 1024):
        layer = factory.create_layer("alpha", os.urandom(n))
        assert layer.mass == LAYER_OVERHEAD + n


def test_conservation_identity_holds_for_random_agents(factory, secrets):
    rng = random.Random(1)
    for _ in range(50):
        specs = [
            (rng.choice(CLASSES), os.urandom(rng.choice([0, 0, 8, 64, 300])))
            for _ in range(rng.randint(1, 20))
        ]
        agent = factory.build_agent(specs)
        held = rng.sample(CLASSES, rng.randint(0, 5))
        env = Environment("e", {k: secrets[k] for k in held})
        before = agent.mass
        result = interact(agent, env)
        assert result.mass_before == before
        assert result.mass_before == result.mass_after + result.total_signal + result.total_loss
        # every stripped layer was of a class the environment holds
        assert all(k in held for k in result.delta_L)
        # and no surviving layer is of a held class
        assert all(layer.key_class not in held for layer in agent.layers)


def test_signal_and_loss_match_geometry(factory, secrets):
    agent = factory.build_agent([("alpha", b"x" * 40), ("alpha", b""), ("beta", b"y" * 10)])
    env = Environment("alpha-only", {"alpha": secrets["alpha"]})
    result = interact(agent, env)
    assert result.layers_stripped == 2
    assert result.total_signal == 40
    assert result.total_loss == 2 * LAYER_OVERHEAD
    assert agent.layer_count == 1 and agent.layers[0].key_class == "beta"


def test_max_layers_bounds_consumption_and_preserves_identity(factory, secrets):
    agent = factory.build_agent([("beta", b"p" * 16)] * 12 + [("alpha", b"ballast")])
    env = Environment("beta", {"beta": secrets["beta"]})
    before = agent.mass
    result = interact(agent, env, max_layers=3)
    assert result.layers_stripped == 3
    assert sum(1 for l in agent.layers if l.key_class == "beta") == 9
    assert before == result.mass_after + result.total_signal + result.total_loss


def test_max_layers_none_strips_everything_matching(factory, secrets):
    agent = factory.build_agent([("beta", b"p")] * 12)
    env = Environment("beta", {"beta": secrets["beta"]})
    result = interact(agent, env, max_layers=None)
    assert result.layers_stripped == 12
    assert not agent.alive


def test_mass_gate_blocks_without_consuming(factory, secrets):
    agent = factory.build_agent([("alpha", b"x" * 100)])
    env = Environment("tiny", {"alpha": secrets["alpha"]}, mass_threshold=(0, 10))
    before = agent.mass
    result = interact(agent, env)
    assert not result.agent_could_enter
    assert agent.mass == before
