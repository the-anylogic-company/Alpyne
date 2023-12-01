import os
import sys
from random import randint

from alpyne.client.utils import AlpyneJSONEncoder
from alpyne.data.model_data import EngineSettings
from alpyne.data.spaces import Configuration, Action
from alpyne.client.alpyne_client import AlpyneClient
from alpyne.data.constants import PyLogLevel, JavaLogLevel, State

if __name__ == "__main__":
    client = AlpyneClient(r"Exported\Alphabet\model.jar",
                          py_log_level=PyLogLevel.INFO,
                          java_log_level=JavaLogLevel.CONFIG,
                          alpyne_path=os.environ.get('ALPYNE_SERVER_PATH'))
    print(client.version)

    client.reset(
        Configuration(start="a", finish="z", verbose=True),
        EngineSettings(stopTime=100, seed=1)  # overrides default engine settings
    )

    rl_status = client.wait_for(State.PAUSED, 5)  # wait until first call to `takeAction` is made
    while not rl_status.done and rl_status.state not in State.FINISHED|State.ERROR:
        engine_status = client.engine_status()
        model_time, model_units = engine_status.time, engine_status.settings.units.name

        a = Action(step=randint(1, 3))  # action to take
        print(f"[EPISODE {rl_status.episodeNum} STEP {rl_status.stepNum} @ {model_time} {model_units}] Taking action: {a}")

        client.step(a)
        rl_status = client.wait_for(State.PAUSED|State.FINISHED|State.ERROR, 5)  # wait til in next stopped state
        print(f"[{rl_status.state.name}] New letter = {rl_status.observation.letter}\n")

    print("OUTPUTS")
    print(client.template.outputs)
    outputs = client.outputs(client.template.outputs)
    print(outputs)
