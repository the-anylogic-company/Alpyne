import itertools
from typing import NoReturn

from alpyne.client.alpyne_client import AlpyneClient
from alpyne.client.model_run import ModelRun
from alpyne.client.abstract import BaseMultiRun
from alpyne.client.utils import histogram_outputs_to_fake_dataset, limit
from alpyne.data.constants import RunStatus
from alpyne.data.single_run_outputs import SingleRunOutputs
from alpyne.data.spaces import Number, Observation, Action, Configuration


class MyMultiRun(BaseMultiRun):
    def __init__(self, client: AlpyneClient, n_workers: int, verbose: bool = False):
        super().__init__(client, n_workers, verbose)
        self.counter = itertools.count(start=1, step=1)
        self.last_outputs = [SingleRunOutputs()]*n_workers  # initialize to empty outputs

    def get_configuration(self, template: Configuration) -> Configuration:
        """ Overridden abstract method """

        template.acquisition_lag_days = 1
        template.engine_seed = next(self.counter)
        return template

    def get_action(self, observation: Observation, template: Action) -> Action:
        """ Overridden abstract method """

        # You will typically use this space for testing trained RL policies in your model.
        # For simplicity, the pre-defined action is used.

        # Heuristic-based action
        # rate = observation.last_order_rate  # start with last value
        # if observation.stock_amount > 7000:
        #     # avoid reaching max by decreasing amount ordered
        #     rate = rate - 15
        # elif observation.stock_amount < 3000:
        #     # avoid reaching min by increasing amount ordered
        #     rate = rate + 5
        # # keep within [0,50] range (not technically enforced)
        # rate = limit(0, rate, 50)

        # # Fixed action
        rate = 25

        template.order_rate = rate
        return template

    def on_episode_finish(self, sim: ModelRun) -> NoReturn:
        """ Overridden optional method """

        # Update the last outputs of the sim at their index
        # If we didn't have this, the stats would be lost after it resets at episode complete
        #   (something that happens due to the automated logic of the base class)
        self.last_outputs[sim.id-1] = sim.get_outputs()


if __name__ == "__main__":
    client = AlpyneClient(r"Exported\StockManagementGame\model.jar")

    print(client.configuration_template)
    print(client.observation_template)
    print(client.action_template)
    print(client.output_names)

    N_WORKERS = N_EPISODES = 8
    multi_sim = MyMultiRun(client, N_WORKERS, verbose=True)  # enable simple logging
    multi_sim.run(N_EPISODES)

    multi_outputs = multi_sim.last_outputs

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
        # just print the stats if user doesn't have matplotlib
        print(f"Stock fullness statistics: {[output.fullnessDistribution['statistics'] for output in multi_outputs]}")
        print(f"Amount sold: {[output.amountSold for output in multi_outputs]}")
        print(f"Amount wasted: {[output.amountWasted for output in multi_outputs]}")



