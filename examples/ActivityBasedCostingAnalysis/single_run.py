import os
from argparse import ArgumentParser, Namespace

from alpyne.outputs import UnitValue
from alpyne.sim import AnyLogicSim


def run(args: Namespace):
    """
    Execute a single run of the ABCA model, printing relevant information.

    Note that there is no argument validation (i.e., it assumes all values are of the correct type/in acceptable range)
    """
    sim = AnyLogicSim("ModelExported/model.jar",
                      engine_overrides=dict(seed=args.seed, stop_time=UnitValue(args.stop_time, "DAY")),
                      config_defaults=dict(sizeBufferQueues=args.queue)
                      )
    if not args.no_schema:
        print(sim.schema)
    if args.no_run:
        return

    status = sim.reset(arrivalRate=args.rate)
    print(status)

    status = sim.take_action(numResourceA=args.num_a, numResourceB=args.num_b, processDelay=args.delay,
                             conveyorSpeed=args.speed)
    print(status)

    print(sim.outputs())


if __name__ == '__main__':
    assert os.path.exists(r"ModelExported/model.jar"), r"Missing file 'ModelExported/model.jar'. To fix, create the folder if it does not exist and export/unzip in-place."

    parser = ArgumentParser(prog="ABCA-SingleRun",
                            description="Execute a single run of the ABCA model, printing at least the before/after run status and outputs to the console.")
    parser.add_argument("-s", "--seed", default=1,
                        help="RNG seed")
    parser.add_argument("-r", "--rate", default=1.0,
                        help="Arrival rate (per day); typical range [0.1, 2]")
    parser.add_argument("-a", "--num-a", default=10,
                        help="Number of Resource A agents; typical range [1, 20]")
    parser.add_argument("-b", "--num-b", default=10,
                        help="Number of Resource B agents; typical range [1, 20]")
    parser.add_argument("-d", "--delay", default=1.0,
                        help="Delay (seconds) of machine; typical range [1, 12]")
    parser.add_argument("-c", "--speed", default=0.001,
                        help="Speed (m/s) of conveyor; typical range [1e-6, 15]")
    parser.add_argument("-q", "--queue", default=90,
                        help="Size of auxiliary queues before each resource's seize block; typical size [1, 90]")
    parser.add_argument("-t", "--stop-time", default=180,
                        help="Stop time (days)")

    prevent_group = parser.add_mutually_exclusive_group()
    prevent_group.add_argument("--no-run", action="store_true",
                               help="Do not execute a simulation run (i.e., only print schema and quit)")
    prevent_group.add_argument("--no-schema", action="store_true",
                               help="Suppress schema from being printed")

    args = parser.parse_args()
    run(args)
