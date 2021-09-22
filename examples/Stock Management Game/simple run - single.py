from logging import DEBUG

from alpyne.client import alpyne_client
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
    client = AlpyneClient(r"Exported\StockManagementGame\model.jar", blocking=True, verbose=True)

    print(client.configuration_template)
    print(client.observation_template)
    print(client.action_template)
    print(client.output_names)

    config = client.create_default_rl_inputs()  # == configuration_template
    config.acquisition_lag_days = 1
    config.engine_seed = 1 # fixed seed

    sim = client.create_reinforcement_learning(config)\
                .run()

    while not sim.is_terminal():
        status, info = sim.last_state  # updated when status is polled (automatically done thx to `blocking=True`)
        print(f"Current sim status/info = {status} | {info}")

        observation = sim.get_observation()
        print(f"Observation = {observation}", end="\n\n")

        # query order rate based on function chosen
        action = client.action_template
        action.order_rate = get_fixed_order_rate()
        sim.take_action(action)

    print(f"Finished! Final state = {sim.last_state}.")
    print(f"Final observation = {sim.get_observation()}")

    outputs = sim.get_outputs()

    try:
        from matplotlib import pyplot as plt
        plt.suptitle(f"Sold: {outputs.amountSold:7.2f} | Wasted: {outputs.amountWasted:7.2f}")

        plt.subplot(3, 2, 1)
        plt.plot(outputs.stockValueDS['dataX'], outputs.stockValueDS['dataY'])
        plt.title("Stock values", weight="bold")
        plt.xlabel("seconds", style="italic")

        plt.subplot(3, 2, 3)
        plt.plot(outputs.orderRateDS['dataX'], outputs.orderRateDS['dataY'])
        plt.title("Order rates", weight="bold")
        plt.xlabel("seconds", style="italic")

        plt.subplot(3, 2, 5)
        plt.plot(outputs.demandRateDS['dataX'], outputs.demandRateDS['dataY'])
        plt.title("Demands", weight="bold")
        plt.xlabel("seconds", style="italic")

        plt.subplot(3, 2, (2, 6))
        data, bins = histogram_outputs_to_fake_dataset(outputs.fullnessDistribution['lowerBound'],
                                                       outputs.fullnessDistribution['intervalWidth'],
                                                       outputs.fullnessDistribution['hits'])
        plt.hist(data, bins=bins, rwidth=0.9)
        plt.title("Stock fullness distribution", weight="bold")

        plt.tight_layout(h_pad=1.8)
        plt.show()
    except ModuleNotFoundError:
        # just print some stats if user doesn't have matplotlib
        print(f"Amount sold: {outputs.amountSold}")
        print(f"Amount wasted: {outputs.amountWasted}")
        print(f"Stock fullness statistics: {outputs.fullnessDistribution['statistics']}")

