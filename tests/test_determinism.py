"""v1.0.1: seeded runs are identical across processes with different PYTHONHASHSEED (review item 24)."""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCRIPT = r"""
import random, os, sys
sys.path.insert(0, __ROOT__)
from amt_core import AgentFactory
from amt_extensions import Node, Topology, AgentBehavior
secrets = {k: bytes([i]) * 32 for i, k in enumerate(["alpha", "beta", "gamma", "delta"])}
factory = AgentFactory(secrets)
topo = Topology()
topo.add_node(Node(node_id="hub", name="hub", _key_secrets={}))
for k in ["alpha", "beta", "gamma", "delta"]:
    topo.add_node(Node(node_id=k, name=k, _key_secrets={k: secrets[k]}))
    topo.connect("hub", k)
topo.connect("alpha", "beta"); topo.connect("beta", "gamma"); topo.connect("gamma", "delta")
random.seed(7)
visits = []
for i in range(40):
    agent = factory.build_agent([(k, bytes(8)) for k in ["alpha", "beta", "gamma", "delta"] for _ in range(3)])
    behavior = AgentBehavior(risk_baseline=0.4, desperation_curve=2.0)
    behavior.observe(agent)
    cur = "hub"
    for step in range(15):
        node = topo.nodes[cur]
        node.process(agent, factory)
        behavior.observe(agent)
        if not agent.alive:
            break
        nxt = behavior.choose_node(topo.reachable_from(cur), agent)
        if nxt is None:
            break
        cur = nxt.node_id
        visits.append(cur)
print(len(visits), ",".join(visits))
"""


def _run(hash_seed: str) -> str:
    env = dict(os.environ, PYTHONHASHSEED=hash_seed)
    out = subprocess.run(
        [sys.executable, "-c", SCRIPT.replace("__ROOT__", repr(ROOT))],
        capture_output=True, text=True, check=True, env=env, cwd=ROOT,
    )
    return out.stdout.strip()


@pytest.mark.parametrize("a,b", [("0", "1"), ("1", "2"), ("0", "12345")])
def test_behavioral_traversal_is_hash_seed_independent(a, b):
    assert _run(a) == _run(b)


def test_reachable_from_is_sorted():
    from amt_extensions import Node, Topology
    topo = Topology()
    for nid in ["zeta", "alpha", "mid"]:
        topo.add_node(Node(node_id=nid, name=nid, _key_secrets={}))
    topo.add_node(Node(node_id="hub", name="hub", _key_secrets={}))
    for nid in ["zeta", "alpha", "mid"]:
        topo.connect("hub", nid)
    assert [n.node_id for n in topo.reachable_from("hub")] == ["alpha", "mid", "zeta"]
