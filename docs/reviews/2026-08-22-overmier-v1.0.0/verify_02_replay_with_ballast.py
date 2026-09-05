import os, sys, copy
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
from amt_core import AgentFactory
from amt_token_economy import ToolGateway, STANDARD_TOOL_CLASSES
from amt_marketplace import ResourcePool, MarketplaceNode, MarketplaceTopology
secrets = {k: os.urandom(32) for k in ["alpha","beta","gamma","delta","epsilon"]}
factory = AgentFactory(secrets)
llm = STANDARD_TOOL_CLASSES["llm_inference"]
gw = ToolGateway(gateway_id="gw1", name="gpt4", tool_class=llm, tool_name="gpt-4"); gw.initialize(secrets)

print("== 1. COPY-REPLAY (1 beta + alpha ballast) vs base_cost=3")
a = factory.build_agent([("beta", b"x"*32), ("alpha", b"y"*64)])
b = copy.deepcopy(a)
for tag, ag in (("copy A", a), ("copy B", b)):
    r = gw.process_tool_call(ag)
    print(f"  {tag}: outcome={r['outcome']} success={r['success']} layers_charged={r['layers_charged']}")

print("== 1b. OVERCHARGE: 12 beta + ballast, one visit")
c = factory.build_agent([("beta", b"x"*32)]*12 + [("alpha", b"y"*64)])
r = gw.process_tool_call(c)
print(f"  beta layers before=12 after={c.mass_profile().get('beta',0)//1 and c.layer_count-1} outcome={r['outcome']} success={r['success']}")

print("== 2. REGEN via MarketplaceTopology.tick()")
import inspect
sig = inspect.signature(MarketplaceNode.__init__); print("  MarketplaceNode args:", list(sig.parameters)[1:])
