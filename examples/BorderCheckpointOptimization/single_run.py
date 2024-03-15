"""
Execute a single run, printing useful information along the way.
"""
import os
from datetime import datetime
from pprint import pprint
from alpyne.sim import AnyLogicSim


if __name__ == '__main__':
    assert os.path.exists(r"ModelExported/BorderCheckpointOptimization.zip"), r"Missing file 'ModelExported/BorderCheckpointOptimization.zip'. To fix, create the folder if it does not exist and export with the specified name."

    sim = AnyLogicSim(r"ModelExported/BorderCheckpointOptimization.zip",
                      engine_overrides=dict(start_date=datetime(2024, 1, 1),
                                            stop_date=datetime(2024, 1, 2),
                                            seed=1),
                      lock_defaults=dict(timeout=60))
    print(sim.schema)
    print(sim.engine_settings)

    print("***")

    status = sim.reset(numCarInspectors=4, numBusInspectors=2)
    print(status.state, status.time, status.date)
    print(status.observation)

    print("***")

    pprint(sim.outputs())


