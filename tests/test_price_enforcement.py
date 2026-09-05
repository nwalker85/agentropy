"""v1.0.1: the token gateway enforces its declared price (review items 3, 5, 6, 7, 9)."""
import os

import pytest

from amt_core import AgentFactory
from amt_token_economy import STANDARD_TOOL_CLASSES, ToolGateway

CLASSES = ["alpha", "beta", "gamma", "delta", "epsilon"]


@pytest.fixture
def secrets():
    return {k: os.urandom(32) for k in CLASSES}


@pytest.fixture
def factory(secrets):
    return AgentFactory(secrets)


@pytest.fixture
def llm_gateway(secrets):
    gw = ToolGateway("llm", "LLM", STANDARD_TOOL_CLASSES["llm_inference"], "model")
    gw.initialize(secrets)
    return gw


def test_declared_price_is_three_layers(llm_gateway):
    assert llm_gateway.tool_class.base_cost == 3


def test_underfunded_payment_is_rejected_before_any_consumption(factory, llm_gateway):
    agent = factory.build_agent([("beta", b"payment"), ("alpha", b"survival")])
    before = agent.mass
    call = llm_gateway.process_tool_call(agent)
    assert call["outcome"] == "insufficient_funds"
    assert call["success"] is False
    assert call["layers_charged"] == 0
    assert call["mass_charged"] == 0
    assert agent.mass == before
    assert call["layers_held"] == 1 and call["declared_cost"] == 3


def test_exact_price_is_charged_and_surplus_survives(factory, llm_gateway):
    agent = factory.build_agent([("beta", f"p{i}".encode()) for i in range(12)] + [("alpha", b"s")])
    call = llm_gateway.process_tool_call(agent)
    assert call["outcome"] == "success"
    assert call["layers_charged"] == 3
    assert sum(1 for l in agent.layers if l.key_class == "beta") == 9


def test_twelve_layers_buy_exactly_four_calls(factory, llm_gateway):
    """The paper's sentence 'an agent with 12 beta layers has exactly 4 LLM calls' (token_economy.md §8.5)."""
    agent = factory.build_agent([("beta", b"p")] * 12 + [("alpha", b"s")])
    outcomes = [llm_gateway.process_tool_call(agent)["outcome"] for _ in range(5)]
    assert outcomes == ["success"] * 4 + ["no_affinity"]


def test_no_affinity_charges_nothing(factory, llm_gateway):
    agent = factory.build_agent([("alpha", b"only-alpha")])
    before = agent.mass
    call = llm_gateway.process_tool_call(agent)
    assert call["outcome"] == "no_affinity" and call["layers_charged"] == 0
    assert agent.mass == before


def test_paying_the_exact_price_with_nothing_else_is_died_paying(factory, llm_gateway):
    agent = factory.build_agent([("beta", b"p")] * 3)
    call = llm_gateway.process_tool_call(agent)
    assert call["outcome"] == "died_paying"
    assert call["success"] is False
    assert call["layers_charged"] == 3
    assert not agent.alive


def test_conservation_holds_on_every_recorded_call(factory, llm_gateway):
    for spec in ([("beta", b"p")] * 5 + [("alpha", b"s")], [("beta", b"p")], [("gamma", b"g")]):
        agent = factory.build_agent(spec)
        call = llm_gateway.process_tool_call(agent)
        assert call["mass_before"] == call["mass_after"] + call["signal"] + call["loss"]
