"""v1.0.1 marketplace fixes: regeneration clock (item 16) and nutrient accounting (items 17, 18)."""
import os

import pytest

from amt_core import AgentFactory, LAYER_OVERHEAD
from amt_marketplace import MarketplaceNode, MarketplaceTopology, NutrientCycler, ResourcePool


def test_first_simulation_tick_regenerates():
    pool = ResourcePool(capacity=100.0, current=0.0, regeneration_rate=10.0)
    node = MarketplaceNode("n", "n", {"alpha": os.urandom(32)}, pool, NutrientCycler())
    topo = MarketplaceTopology()
    topo.add_node(node)
    seen = []
    for _ in range(4):
        topo.tick(0.5)
        seen.append(pool.current)
    assert seen == [5.0, 10.0, 15.0, 20.0]


def test_reviewers_single_tick_of_ten_seconds_regenerates_to_capacity():
    """The reviewer's harness ticked once and read 0; v1.0.1 reads 100."""
    pool = ResourcePool(capacity=100, current=0, regeneration_rate=10)
    node = MarketplaceNode("n", "N", {"alpha": os.urandom(32)}, pool)
    topo = MarketplaceTopology()
    topo.add_node(node)
    topo.tick(10)
    assert pool.current == 100


def test_explicit_zero_time_is_a_valid_clock_value():
    pool = ResourcePool(capacity=100.0, current=0.0, regeneration_rate=10.0, last_tick=0.0)
    pool.regenerate(0.0)
    assert pool.current == 0.0 and pool.last_tick == 0.0
    pool.regenerate(2.0)
    assert pool.current == 20.0


def test_standalone_pool_first_call_only_sets_the_basis():
    pool = ResourcePool(capacity=100.0, current=0.0, regeneration_rate=10.0)
    pool.regenerate(0.5)
    assert pool.current == 0.0
    pool.regenerate(1.0)
    assert pool.current == 5.0


@pytest.fixture
def factory():
    return AgentFactory({k: os.urandom(32) for k in ["alpha", "beta", "gamma", "delta", "epsilon"]})


def test_cycled_counts_only_what_is_returned(factory):
    cycler = NutrientCycler(cycle_threshold=200)
    cycler.deposit(signal=1000, loss=0)  # 30 % retention -> 300 B budget
    assert cycler.accumulated == 300
    specs = cycler.cycle(factory, ["alpha", "beta"], max_layers=3)
    used = sum(len(p) for _, p in specs)
    assert len(specs) <= 3
    assert cycler._total_cycled == used
    assert cycler.accumulated == 300 - used
    assert cycler._total_overhead_created == LAYER_OVERHEAD * len(specs)
    assert cycler.total_ciphertext_created == used + LAYER_OVERHEAD * len(specs)


def test_minted_ciphertext_exceeds_nutrient_budget_by_overhead(factory):
    """The reviewer's 300 B -> 356 B (two classes) figure, now labelled for what it is."""
    cycler = NutrientCycler(cycle_threshold=200)
    cycler.deposit(signal=1000, loss=0)
    specs = cycler.cycle(factory, ["alpha", "beta"])
    layers = [factory.create_layer(k, p) for k, p in specs]
    minted = sum(l.mass for l in layers)
    assert minted == cycler.total_ciphertext_created
    assert minted - cycler._total_cycled == LAYER_OVERHEAD * len(layers)
