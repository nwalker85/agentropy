"""KNOWN LIMITATIONS of the v1.0.x reference implementation, made executable.

These tests PASS when the limitation is PRESENT. They exist so that the limitation
is stated in code, next to the code, and so that whoever removes it in a later
version has to change a test on purpose. None of these is a bug fixed by v1.0.1;
each is scoped out of a patch release and belongs to a v2 design record.

Source: Overmier open technical review of v1.0.0 (2026-08-22) and
docs/reviews/2026-08-22-overmier-v1.0.0/VERIFICATION-NOTES.md.
"""
import copy
import os

import pytest

from amt_core import AgentFactory, Environment, interact
from amt_extensions import PublicLedger
from amt_token_economy import STANDARD_TOOL_CLASSES, ToolGateway

CLASSES = ["alpha", "beta", "gamma", "delta", "epsilon"]


@pytest.fixture
def secrets():
    return {k: os.urandom(32) for k in CLASSES}


@pytest.fixture
def factory(secrets):
    return AgentFactory(secrets)


def test_known_limitation_copied_agent_pays_twice(factory, secrets):
    """Review item 8. Consumption is a list reassignment inside one process; ciphertext
    bytes copy like any bytes. Price enforcement (v1.0.1) does not change this: a
    copy that holds the full price still pays. Uniqueness across copies requires an
    authority outside the scheme (ledger, settlement, hardware) — v2."""
    gw = ToolGateway("llm", "LLM", STANDARD_TOOL_CLASSES["llm_inference"], "model")
    gw.initialize(secrets)
    original = factory.build_agent([("beta", b"p")] * 3 + [("alpha", b"ballast")])
    clone = copy.deepcopy(original)
    a = gw.process_tool_call(original)
    b = gw.process_tool_call(clone)
    assert a["outcome"] == "success" and b["outcome"] == "success"
    assert a["layers_charged"] == b["layers_charged"] == 3


def test_known_limitation_key_class_is_plaintext_metadata(factory, secrets):
    """Review item 2. An environment without the beta secret can still see that beta
    layers exist; only their contents are hidden. cross_org_accountability.md:94
    said otherwise in v1.0.0 (corrected in the v1.0.1 errata)."""
    agent = factory.build_agent([("alpha", b"a"), ("beta", b"b")])
    alpha_only = Environment("alpha", {"alpha": secrets["alpha"]})
    visible_classes = {layer.key_class for layer in agent.layers}
    assert "beta" in visible_classes
    result = interact(agent, alpha_only)
    assert result.layers_stripped == 1
    assert [l.key_class for l in agent.layers] == ["beta"]


def test_known_limitation_public_ledger_is_a_mutable_list():
    """Review item 10. The reference 'public append-only ledger' is an in-memory
    Python list; commitments are unsigned and unanchored. Anchoring/signing is v2."""
    ledger = PublicLedger()
    assert isinstance(ledger.commitments, list)
    ledger.commitments.clear()  # nothing prevents this
    assert ledger.commitments == []


def test_known_limitation_physical_budget_round_trip_is_lossy(factory):
    """Review item 12. GCM overhead and 256-B layer quantisation make encode/decode
    non-invertible. The demo now prints the error table; the paper no longer says
    'bidirectional' without qualification."""
    from amt_physical_iot import ResourceBudget
    b = ResourceBudget(battery_wh=50, bandwidth_mb=100, storage_ops=500, cpu_seconds=30, sensor_reads=50)
    back = ResourceBudget.interpret_agent_mass(factory.build_agent(b.to_layer_specs()))
    assert round(back["battery"], 3) == 45.396
    assert back["bandwidth"] == 128.0
    assert round(back["storage"], 2) == 453.96
    assert round(back["cpu"], 3) == 26.984
    assert round(back["sensor"], 2) == 43.82
