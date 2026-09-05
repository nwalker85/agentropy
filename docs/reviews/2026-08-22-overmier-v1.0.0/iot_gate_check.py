"""Can the IoT mass gate ever bind in the configured demo?

Computes the heaviest agent ``demo_6_scale`` can build (top of every draw range at
``amt_physical_iot_demo.py:391-395``) and compares it with the tightest gate
(``amt_physical_iot.py:161-162``, ``500 * 1024`` bytes). Run from anywhere; by
default it imports the repo this file lives in. Pass a directory as ``argv[1]`` to
test another tree (e.g. an extracted Zenodo archive).
"""
import os
import pathlib
import sys

ART = sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parents[3])
sys.path.insert(0, ART)

from amt_core import AgentFactory  # noqa: E402
from amt_physical_iot import ResourceBudget  # noqa: E402

secrets = {k: os.urandom(32) for k in ["alpha", "beta", "gamma", "delta", "epsilon"]}
f = AgentFactory(secrets)

# demo_6 draws: battery U(5,60), bandwidth U(1,80), storage U(10,300), cpu U(1,25), sensors randint(2,40)
b = ResourceBudget(battery_wh=60.0, bandwidth_mb=80.0, storage_ops=300.0, cpu_seconds=25.0, sensor_reads=40)
a = f.build_agent(b.to_layer_specs())
print("tree:", ART)
print("max-budget demo agent mass (bytes):", a.mass)
print("gate floor at <20% battery (bytes):", 500 * 1024)
print("gate can bind in demo_6:", a.mass > 500 * 1024)

# the paper's §5.1 agent
b2 = ResourceBudget(battery_wh=50, bandwidth_mb=100, storage_ops=500, cpu_seconds=30, sensor_reads=50)
a2 = f.build_agent(b2.to_layer_specs())
print("paper §5.1 agent mass (bytes):", a2.mass, "layers:", a2.layer_count)
