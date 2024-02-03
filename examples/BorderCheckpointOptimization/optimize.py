from math import sqrt
from typing import Union
import time

from alpyne.sim import AnyLogicSim
from alpyne.constants import EngineState

from bayes_opt import BayesianOptimization
from bayes_opt import UtilityFunction

# Parameters to optimize for (feel free to change, within limits where they exist)
car_rate = 22.0  # (0,30]
bus_rate = 2.0  # (0, 2.5]
round_values = True  # whether to round values before checking it against the history cache
num_iterations = 10  # how many distinct parameter sets to try (6 and 4 options for the two discrete parameters = 24 total options; i.e., setting above 24 does nothing more)
num_replications = 3  # how many times to rerun the same set to give the optimizer the mean value of (set to 1 if used a fixed seed!)
seed = None  # set to None for a random seed each sim run; if using a fixed seed, `num_replications` should be 1
hours_to_sim = 3  # takes ~4sec to sim each hour
verbose = True  # include print logging

# Setup optimizer (only change if you are experimenting / know what you're doing)
optimizer = BayesianOptimization(
    f=None,
    pbounds={'c': (1, 6), 'b': (1, 4)},  # allowed ranges for number of car and bus inspectors (as defined by the model logic)
    random_state=1,
)
optimizer.set_gp_params(alpha=1e-3)  # reduced from 1e-6 to better solve for discrete nature, as per BO docs
utility = UtilityFunction(kind="ucb", kappa=2.5, xi=0.0)  # reference: https://github.com/bayesian-optimization/BayesianOptimization/blob/master/bayes_opt/util.py#L124

# Setup script-related objects
sim = AnyLogicSim("ModelExported\model.jar",
                  engine_overrides=dict(stop_time=hours_to_sim*60, seed=seed),
                  lock_defaults=dict(flag=EngineState.FINISHED, timeout=hours_to_sim*4*2)  # ~4 sec per sim hour, doubled for added buffer
                  )
history = dict()  # recorded parameter set to objective function value

def objective(c: Union[int, float], b: Union[int, float]) -> float:
    """
    Tests the provided inputs on the sim, returning an objective that it sought to be maximized.

    :param c: Desired number of car inspections; will be rounded to an int
    :param b: Desired number of bus inspections; will be rounded to an int
    :return: The negative mean squared time in systems for cars and buses
    """
    rc, rb = int(round(c)), int(round(b))
    key = (rc, rb) if round_values else (c, b)
    score = history.get(key)
    if verbose:
        print(f"[{len(history)+1} / {num_iterations}] Attempting ({c:.2f}, {b:.2f}) == ({rc}, {rb}) ... cached score: {score}")
    if score is None:  # not yet recorded
        score = 0
        for i in range(num_replications):
            start = time.time()

            status = sim.reset(carRate=car_rate, busRate=bus_rate, nCarInspectors=rc, nBusInspectors=rb)
            # setup metric to greatly prefer significant reduces in TIS (smaller differences don't matter)
            #           and slightly prefer those with less workers,
            #           with both TIS values are weighted equally.
            # (smaller values = better)
            this_score = (status.observation['carTISMean'] + status.observation['busTISMean'])**2 * (rc + rb)
            score += this_score

            dur = time.time() - start
            if verbose:
                print(f"\t[{i+1} / {num_replications}] {key}  ->  {this_score:.2f}  (took: {dur:.2f})")
        # get the average value across all replications
        score /= num_replications
        # and finally negative it since this library is looking to maximum the objective
        score *= -1
        if verbose:
            print(f"\t= {score:.2f}")
        # store in the history in case this trial gets repeated
        history[key] = score
    return score


if __name__ == "__main__":
    print(sim.schema)

    start = time.time()
    while len(history) < num_iterations:
        next_suggestion = optimizer.suggest(utility)
        target = objective(**next_suggestion)
        optimizer.register(params=next_suggestion, target=target)

    print("\nOPTIMIZER MAX:", optimizer.max)
    print(f"TRANSLATION: For the input arrival rates (car={car_rate}, bus={bus_rate}), "
          f"\n\tthe found optimums for inspectors are: car={int(round(optimizer.max['params']['c']))}, bus={int(round(optimizer.max['params']['b']))},"
          f"\n\tresulting in a mean TIS of {sqrt(abs(optimizer.max['target']))/60.0:.2f} hours"
          )
    print(f"EXPERIMENT DURATION: {time.time()-start:.3f} seconds")
