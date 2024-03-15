import os

import numpy as np
from stable_baselines3 import SAC
from tabulate import tabulate

from alpyne.sim import AnyLogicSim


def test_and_print(files: list[str]):
    """
    Test a series of previously trained policies on a range of arrival rates.

    Prints a table showing the rates tried and the resulting predictions and results for all provided policies.

    :param files: A list of zip files containing trained SAC policies.
    """
    policies = [SAC.load(f) for f in files]

    # We can just use a single AnyLogicSim object to test the different policy runs;
    # we use fixed seed to ensure similar results between policies and rates
    sim = AnyLogicSim("ModelExported/model.jar", engine_overrides=dict(seed=1),
                      config_defaults=dict(sizeBufferQueues=100))
    table = []
    # Presumably trained on rates from 0-2; try a bigger range to test how well it extrapolates
    for rate in np.arange(0.25, 5.1, 0.25):
        row = [str(rate)]
        for i, name in enumerate(files):
            # Get the action based on the observation
            # Note: this assumes all observation shapes are the same
            policy = policies[i]
            act, _ = policy.predict(np.array([rate]))  # `predict` returns (action, None)
            a, b, d, s = act
            a, b = int(a.round()), int(b.round())
            d, s = float(d), float(s)

            # Try a run with the provided rate and action values to see how well it performs
            _ = sim.reset(arrivalRate=rate)
            status = sim.take_action(numResourceA=a, numResourceB=b, processDelay=d, conveyorSpeed=s)
            cpp = status.observation['costPerProduct']

            row.append(f"({a:2d}, {b:2d}, {d:5.2f}, {s:5.2f} | {cpp:6.1f})")

        table.append(row)
    print(tabulate(table, headers=["rate"] + files))


if __name__ == '__main__':
    assert os.path.exists(
        r"ModelExported/model.jar"), r"Missing file 'ModelExported/model.jar'. To fix, create the folder if it does not exist and export/unzip in-place."

    # Insert one or more zip files to test
    files = ["ABCA_SAC.zip"]

    test_and_print(files)
