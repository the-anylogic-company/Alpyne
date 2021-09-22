import itertools

from alpyne.client.alpyne_client import AlpyneClient
from alpyne.client.utils import histogram_outputs_to_fake_dataset, limit
from alpyne.data.constants import RunStatus
from alpyne.data.spaces import Number, Observation


def get_fixed_order_rate() -> Number:
    rate = 25
    return rate


def get_heuristic_order_rate(obs: Observation) -> Number:
    """
    Use a simple heuristic to keep the order rate as close to 50% (5k) as possible.
    :param obs: the current sim observation
    :return: a number representing the order rate to execute the next step with
    """
    rate = obs.last_order_rate  # start with last value
    if obs.stock_amount > 7000:
        # avoid reaching max by decreasing amount ordered
        rate = rate - 15
    elif obs.stock_amount < 3000:
        # avoid reaching min by increasing amount ordered
        rate = rate + 5
    # keep within [0,50] range (not technically enforced)
    rate = limit(0, rate, 50)
    return rate


if __name__ == "__main__":
    client = AlpyneClient(r"Exported\StockManagementGame\model.jar", blocking=False, verbose=False)

    print(client.configuration_template)
    print(client.observation_template)
    print(client.action_template)
    print(client.output_names)

    config = client.create_default_rl_inputs()  # == configuration_template
    config.acquisition_lag_days = 1

    incrementer = itertools.count(start=1, step=1)
    config.engine_seed = lambda: next(incrementer) # increment seed, for multiruns


    sims = [client.create_reinforcement_learning(config) for _ in range(4)]
    [sim.run() for sim in sims]

    while not all([sim.is_terminal() for sim in sims]):
        for i, sim in enumerate(sims):
            status, info = sim.get_state()
            if status == RunStatus.PAUSED:
                print(f"[#{i}] Current sim status/info = {status} | {info}")

                observation = sim.get_observation()
                print(f"[#{i}] Observation = {observation}", end="\n\n")

                # query order rate based on function chosen
                action = client.action_template
                action.order_rate = get_fixed_order_rate()
                sim.take_action(action)

    multi_outputs = [sim.get_outputs() for sim in sims]

    try:
        from matplotlib import pyplot as plt
        mean_sold = sum([output.amountSold for output in multi_outputs]) / len(multi_outputs)
        mean_wasted = sum([output.amountWasted for output in multi_outputs]) / len(multi_outputs)
        plt.suptitle(f"Sold (μ): {mean_sold:7.2f} | Wasted (μ): {mean_wasted:7.2f}")

        plt.subplot(3, 2, 1)
        for i, output in enumerate(multi_outputs):
            plt.plot(output.stockValueDS['dataX'], output.stockValueDS['dataY'], label=f"Sim{i}")
        plt.title("Stock values", weight="bold")
        plt.xlabel("seconds", style="italic")

        plt.subplot(3, 2, 3)
        for i, output in enumerate(multi_outputs):
            plt.plot(output.orderRateDS['dataX'], output.orderRateDS['dataY'], label=f"Sim{i}")
        plt.title("Order rates", weight="bold")
        plt.xlabel("seconds", style="italic")

        plt.subplot(3, 2, 5)
        for i, output in enumerate(multi_outputs):
            plt.plot(output.demandRateDS['dataX'], output.demandRateDS['dataY'], label=f"Sim{i}")
        plt.title("Demands", weight="bold")
        plt.xlabel("seconds", style="italic")

        plt.subplot(3, 2, (2, 6))
        datasets = [histogram_outputs_to_fake_dataset(output.fullnessDistribution['lowerBound'],
                                                      output.fullnessDistribution['intervalWidth'],
                                                      output.fullnessDistribution['hits']) for output in multi_outputs]
        plt.hist([ds[0] for ds in datasets], bins=datasets[0][1],
                 rwidth=1.25, label=[f"Sim{i}" for i in range(len(datasets))])
        plt.title("Stock fullness distribution", weight="bold")
        plt.legend(loc='upper left')

        plt.tight_layout(h_pad=1.8)
        plt.show()
    except ModuleNotFoundError:
        # just print stats if user doesn't have matplotlib
        print(f"Stock fullness statistics: {[output.fullnessDistribution['statistics'] for output in multi_outputs]}")
        print(f"Amount sold: {[output.amountSold for output in multi_outputs]}")
        print(f"Amount wasted: {[output.amountWasted for output in multi_outputs]}")



