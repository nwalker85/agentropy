import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
from amt_marketplace import ResourcePool, MarketplaceNode, MarketplaceTopology, NutrientCycler
secrets = {"alpha": os.urandom(32)}
pool = ResourcePool(capacity=100.0, current=0.0, regeneration_rate=10.0)
node = MarketplaceNode(node_id="n1", name="n1", key_secrets=secrets, resource_pool=pool, nutrient_cycler=NutrientCycler())
topo = MarketplaceTopology(); topo.add_node(node)
for i in range(4):
    topo.tick(0.5)
    print(f"  tick {i+1} (sim_time={topo._sim_time}): pool.current={pool.current}")
