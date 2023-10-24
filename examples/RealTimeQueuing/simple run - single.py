from logging import DEBUG
import random
random.seed(1)
import time
from alpyne.client import alpyne_client
from alpyne.client.alpyne_client import AlpyneClient
from alpyne.client.utils import histogram_outputs_to_fake_dataset, limit
from alpyne.data.constants import RunStatus
from alpyne.data.spaces import Number, Observation

if __name__ == "__main__":
    client = AlpyneClient(r"Exported\RealTimeQueuing\model.jar", blocking=False, verbose=True)

    print(client.configuration_template)
    print(client.observation_template)
    print(client.action_template)
    print(client.output_names)

    config = client.create_default_rl_inputs()  # == configuration_template
    config.verbose = True
    config.trigger_on_exit = False
    config.trigger_frequency = 0
    config.engine_seed = 1

    sim = client.create_reinforcement_learning(config)\
                .run()

    status, info = sim.last_state  # updated when status is polled (automatically done thx to `blocking=True`)
    print(f"Current sim status/info = {status} | {info}")

    observation = sim.get_observation()
    print(f"Observation = {observation}", end="\n\n")

    # query order rate based on function chosen
    action = client.action_template
    action.delay_seconds = 10
    sim.take_action(action)

    status, info = sim.get_state()
    ts = time.time()
    while status not in (RunStatus.STOPPED, RunStatus.COMPLETED):
        elapsed = round(time.time()-ts, 2)
        print(f"[{elapsed:4.2f}] {status} | {info}: ", end="")
        print(sim.get_observation())
        time.sleep(0.5)
        status, info = sim.get_state()

    print(f"Finished! Final state = {sim.last_state}.")
    print(f"Final observation = {sim.get_observation()}")

    outputs = sim.get_outputs()
    print(outputs)
