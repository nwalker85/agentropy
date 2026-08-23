import os, sys, copy
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
from amt_core import AgentFactory
from amt_token_economy import ToolGateway, STANDARD_TOOL_CLASSES
from amt_marketplace import ResourcePool
from amt_physical_iot import ResourceBudget, RESOURCE_MAP

secrets = {k: os.urandom(32) for k in ["alpha","beta","gamma","delta","epsilon"]}
factory = AgentFactory(secrets)

print("== 1. COPY-REPLAY against a 3-layer price")
llm = STANDARD_TOOL_CLASSES["llm_inference"]
gw = ToolGateway(gateway_id="gw1", name="gpt4", tool_class=llm, tool_name="gpt-4")
gw.initialize(secrets)
a = factory.build_agent([("beta", b"x"*32)])
b = copy.deepcopy(a)
r1 = gw.process_tool_call(a); r2 = gw.process_tool_call(b)
print(f"  declared base_cost={llm.base_cost}  agent had 1 beta layer")
print(f"  copy A -> outcome={r1['outcome']} success={r1['success']}")
print(f"  copy B -> outcome={r2['outcome']} success={r2['success']}")

print("== 1b. OVERCHARGE: 12 beta layers, one visit")
c = factory.build_agent([("beta", b"x"*32)]*12)
r3 = gw.process_tool_call(c)
print(f"  layers before=12 after={c.layer_count} outcome={r3['outcome']}")

print("== 2. REGEN CLOCK (sim-time ticks vs wall-clock last_tick default)")
pool = ResourcePool(capacity=100.0, current=0.0, regeneration_rate=10.0)
for t in [0.5, 1.0, 1.5, 2.0]:
    pool.regenerate(t)
    print(f"  tick sim_time={t}: current={pool.current}")

print("== 3. IoT ROUND TRIP")
bud = ResourceBudget(battery_wh=50, bandwidth_mb=100, storage_ops=500, cpu_seconds=30, sensor_reads=50)
ag = factory.build_agent(bud.to_layer_specs())
back = ResourceBudget.interpret_agent_mass(ag)
for k, v in back.items():
    print(f"  {k:10s} requested={getattr(bud, {'battery':'battery_wh','bandwidth':'bandwidth_mb','storage':'storage_ops','cpu':'cpu_seconds','sensor':'sensor_reads'}[k])}  decoded={v:.3f}")
