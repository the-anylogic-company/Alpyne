import logging

from alpyne.client import alpyne_client
from alpyne.client.alpyne_client import AlpyneClient
from alpyne.data.spaces import Action

if __name__ == "__main__":
    alpyne_client.LOG_LEVEL = logging.DEBUG
    client = AlpyneClient(r"Exported\Traffic Light RL\model.jar", blocking=True, verbose=True)

    print(client.configuration_template)
    print(client.observation_template)
    print(client.action_template)
    print(client.output_names)

    cfg = client.configuration_template
    cfg.secs_per_phase = 300
    cfg.secs_between_actions = 300
    cfg.schedule_ns = "none_all_day"
    cfg.schedule_ew = "constant_heavy"
    cfg.engine_seed = 1  # reproducible runs
    cfg.engine_stop_time = 20 # minutes

    sim = client.create_reinforcement_learning(cfg)\
                .run()

    while not sim.is_terminal():
        print(sim.get_observation())
        sim.take_action(Action(do_next_phase=0))

    ops = sim.get_outputs(["totalPassed", "meanTIS"])
    print(ops)