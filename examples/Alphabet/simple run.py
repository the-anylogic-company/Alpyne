from logging import DEBUG
import random
random.seed(1)

from alpyne.client import alpyne_client
from alpyne.client.alpyne_client import AlpyneClient
from alpyne.client.utils import histogram_outputs_to_fake_dataset, limit
from alpyne.data.constants import RunStatus
from alpyne.data.spaces import Number, Observation

if __name__ == "__main__":
    client = AlpyneClient(r"Exported\Alphabet\model.jar", blocking=True, verbose=True)

    print(client.configuration_template)
    print(client.observation_template)
    print(client.action_template)
    print(client.output_names)

    config = client.create_default_rl_inputs()  # == configuration_template
    config.start = "a"
    config.finish = "c"
    config.verbose = True
    config.engine_seed = 1

    sim = client.create_reinforcement_learning(config)\
                .run()

    # episode 1
    while not sim.is_terminal():
        status, info = sim.last_state  # updated when status is polled (automatically done thx to `blocking=True`)
        print(f"[1] Current sim status/info = {status} | {info}")

        observation = sim.get_observation()
        print(f"[1] Observation = {observation}", end="\n\n")

        # query order rate based on function chosen
        action = client.action_template
        action.step = 3
        sim.take_action(action)

    print(f"[1] Finished! Final state = {sim.last_state}.")
    print(f"[1] Final observation = {sim.get_observation()}")

    outputs = sim.get_outputs()
    print("[1]", outputs)

    print("-------------------------------------")

    # episode 2
    sim.reset()
    while not sim.is_terminal():
        status, info = sim.last_state  # updated when status is polled (automatically done thx to `blocking=True`)
        print(f"[2] Current sim status/info = {status} | {info}")

        observation = sim.get_observation()
        print(f"[2] Observation = {observation}", end="\n\n")

        # query order rate based on function chosen
        action = client.action_template
        action.step = 1
        sim.take_action(action)

    print(f"[2] Finished! Final state = {sim.last_state}.")
    print(f"[2] Final observation = {sim.get_observation()}")

    outputs = sim.get_outputs()
    print("[2]", outputs)

    print("-------------------------------------")

    # episode 3
    sim.reset()
    do_valid_step = True
    while not sim.is_terminal():
        status, info = sim.last_state  # updated when status is polled (automatically done thx to `blocking=True`)
        print(f"Current sim status/info = {status} | {info}")

        observation = sim.get_observation()
        print(f"Observation = {observation}", end="\n\n")

        # query order rate based on function chosen
        action = client.action_template
        action.step = 1 if do_valid_step else 27
        do_valid_step = not do_valid_step
        print(f"Taking action {action.step}")
        sim.take_action(action)

    print(f"Finished! Final state = {sim.last_state}.")
    print(f"Final observation = {sim.get_observation()}")

    outputs = sim.get_outputs()
    print(outputs)

