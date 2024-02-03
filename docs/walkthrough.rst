
High-level walkthrough
======================

.. note:: The following explains the general workflow in a way that doesn't require (extensive) referencing to the API documentation; the final sub-section contains some sample code. Explanations assume you have an exported model and are generally familiar with Python programming.


Creating the AnyLogicSim object
---------------------------------

The ``AnyLogicSim`` object serves as the connection to a single instance of your model. If you want to run multiple, parallel runs, you will need to create multiple instances of the ``AnyLogicSim`` object (however, this is not covered in this walkthrough).

The constructor of the sim object takes the following arguments, some of which are explained further below:

- The path to your exported model
- The port to run the app on; this should be unique per instance of the AnyLogicSim (default 0, auto-detect a free port)
- How detailed the logging should be set to on both the Python side (writes to the terminal) and Java side (writes to log files)
- Settings for the AnyLogic engine for time units, start/stop time/date, and RNG seed (default None, which uses the RL experiment's settings)

model path argument
~~~~~~~~~~~~~~~~~~~

When you export from the RL experiment, it saves as a zip file. You have two choices regarding this:

1. Pass a path to the zip file

- Alpyne will extract the contents to a temporary directory.

- For a list of candidates, see: https://github.com/python/cpython/blob/3.9/Lib/tempfile.py#L157

2. Extract the contents of the zip file, then pass a path to the "model.jar" file

Option #1 is only recommended for testing your model. Option #2 requires another step after exporting, but gives you convenient access to any input/output files your model might use or to the the Alpyne log (when enabled), and will write to the hard drive less.

logging
~~~~~~~

You can customize log levels on both the Python side and the Java side.

The Python log level controls how verbose the output is in your terminal when you run your Python script. This mostly relates to the requests sent and received to the underlying Alpyne server.

The Java log level controls how verbose the output is to the file "alpyne.log" which includes information about the control, status, and timing of the execution of your sim.

Two other files are also created: "model.log", which contains any and all text from the standard output and error from your model (e.g., calling ``traceln`` from the AnyLogic model, error tracebacks).

locking
~~~~~~~

The constructor argument ``auto_lock`` determines whether potentially time consuming requests - via the ``reset`` and ``take_action`` functions - automatically call the locking endpoint - via the ``lock`` function, which returns the sim status after some engine state condition is met or throwing an error if the given timeout elapses.

The default is to automatically lock, waiting for up to 30 seconds for the engine state to be in PAUSED, FINISHED, or ERROR.

.. tip:: The returned status has the "state" attribute you can use to see which specific state the engine is currently in

When ``auto_lock`` is false, the ``reset`` and ``take_action`` functions will return None, requiring you to manually call the ``lock`` function. When true, it will use the default arguments (overridable via the ``lock_defaults`` constructor argument) and return the status. Examples (all assume the timeout never elapses):

.. code-block:: python

    # Using partial argument defaults
    sim = AnyLogicSim("model.jar", lock_defaults=dict(timeout=5))
    status = sim.reset(dummyParamVal=1.23)
    while status.state in EngineState.PAUSED:
        status = sim.take_action(dummyChoice=status['dummySize']>50)

    # Using argument defaults, without automatic locking
    sim = AnyLogicSim("model.jar", auto_lock=False)
    sim.reset()
    status = sim.lock(timeout=10)  # uses the default flag (`EngineState.ready()`)
    sim.take_action(dummy=1)
    status = sim.lock(flag=EngineState.ready())  # uses the default timeout (30)

.. note:: See the relevant section in the appendix for more detailed information

engine settings
~~~~~~~~~~~~~~~

If you do not pass any specific settings, the model will execute each run based on the settings you designated in your RL experiment.
You can optionally pass a dictionary to the ``engine_overrides`` constructor argument with settings to override, the keys for which are the names in snake case (e.g., start_time, seed) and are defined in ``alpyne.typing.EngineSettingKeys``.

Generally, Alpyne will attempt to dynamically update the properties in a natural way (i.e., if you pass a stop time only, the stop date will be inferred from this).

Note that any of the values can be set to a no-argument function which returns the expected type.
This is particularly useful for the "seed", in case you want each run to be unique. Examples:

.. code-block:: python

    # each call to reset now uses a random seed in the specified range
    sim = AnyLogicSim("model.jar", engine_overrides=dict(seed=lambda: random.randint(-1e9, 1e9)))

    # each call to reset now starts the seed at 0 and increments by one each time,
    #   using the provided helper function (alpyne.utils.next_num)
    sim = AnyLogicSim("model.jar", engine_overrides=dict(seed=next_num)


Resetting the run
-----------------
When creating a new model run, you'll pass in the initial inputs (i.e., configuration) to execute the first episode with.
This is done by the sim's ``reset`` function which takes keyword arguments for the configuration space.

For example, say your model has the following configuration space:

============= ========
 Name          Type
============= ========
num_workers   int
rate_per_sec  double
machine_types String[]
============= ========

The Python code would look like:

.. code-block:: python

    sim = AnyLogicSim(...)
    sim.reset(num_workers=10, rate_per_sec=3.14, machine_types=["A", "A", "B"])

	
.. warning:: If you do not set explicit values of your defined configuration fields, they will be set to their Java defaults (0 for number types, null for object types). This may cause model errors if your Configuration code does not account for this or if you do not pass the desired defaults as part of the ``config_defaults`` constructor argument in the AlpyneSim object's creation.

.. tip:: In addition to setting fixed values, you can also no-argument callables; these will retrieve the next value every time they're accessed.

Submitting actions
------------------
Whenever the model is in a PAUSED state, you can submit requests to take some action based on your action space definition. When Alpyne consumes your request, it will apply it to the simulation and allow it to continue running.
In practice, this works exactly the same way as resetting with the configuration does, but using the ``take_action`` function with your action space. This function takes keyword arguments for the action space and returns a boolean for if the action was accepted (i.e., passed validation check).

For example, say your model has the following action space:

====================== ========
 Name                    Type
====================== ========
machine_speeds         double[]
====================== ========

The Python code could look like:

.. code-block:: python

    sim.take_action(machine_speeds=[0.1, 0.85, 0.9])

.. warning:: If you do not set explicit values of your defined action fields, they will be set to their Java defaults (0 for number types, null for object types). This may cause model errors if your Action code does not account for this.

Experiment status + observation
-------------------------------
The ``SimStatus`` object contains a variety of information about your sim, including the current time (in model units), date, progress (decimal percent, if a stop time/date was specified), value of the sim engine's state, observation (as a dictionary-like object), and counters.

This object is returned by an explicit call to the AnyLogicSim object's ``status()`` function and also by the ``reset(...)`` and ``take_action(...)`` functions when the ``auto_lock`` constructor argument is set to True (the default).

.. important:: By manually controlling the locking behavior (i.e., ``auto_lock=False``), it is possible to get the status while the simulation is in a RUNNING state

When you see the 'state' being reported from Alpyne, it's referring to the state of the underlying AnyLogic engine. There are 6 different states it can be in:

- IDLE: Just started, waiting for the configuration

- PAUSED = Mid-run, waiting for action and open to observation and output querying

- RUNNING = The model is being actively executed

- FINISHED = The model execution has reached a stopping point and will no longer advance simulated time

- ERROR = Some internal model error has occurred

- PLEASE_WAIT = The model is in the process of executing an uninterruptible command (calling `pause()`, `stop()`, `step()` from the AnyLogic model)

Alpyne has a flag-based enum class that allows you to pass one or more of these states to pass to the ``lock`` function or the ``lock_defaults`` constructor argument in addition to the maximum amount of time you want to wait for the condition to be fulfilled (after which an error will be thrown).

For example, ``sim.lock(EngineState.PAUSED | EngineState.FINISHED | EngineState.ERROR, 30)`` will submit a request to wait until the engine is in PAUSED or FINISHED for up to 5 seconds. The default timeout is 10 seconds if you do not provide anything.

.. tip:: The State enum has a `ready()` function which is a shorthand for the above code (i.e., `sim.lock(State.ready(), 30)`) -- "ready" as in, "ready for some interaction". This is also the default for the function.

The AnyLogicSim object also has a ``observation()`` function which is a shorthand for getting the RL status and referencing the observation attribute.

For example, say your model has the following observation space:

====================== ========
 Name                    Type
====================== ========
mean_service_time      double
per_worker_utilization double[]
====================== ========

Code to retrieve these could look like:

.. code-block:: python

    status = sim.lock()  # paused, finished, or error; up to 30 seconds
    print(status.observation['mean_service_time'], status.observation['per_worker_utilization'])


Retrieving outputs
------------------

Alpyne also allows you to query the current status of any analysis or Output objects on your top-level agent via the ``outputs`` function.

This function takes as input the variable names you want to request (passing nothing retrieves them all) and returns a dictionary mapping names to parsed values. The type of the value differs - anything that has a Python-typed equivalent (e.g., Output object whose type is int) are as such; Alpyne has specialized types for any of the AnyLogic-specific classes (e.g., DataSet) whose attributes follow the same structure as the AnyLogic equivalent.

For example, say you had the following objects in your top-level agent:

====================== ===================
 Name                    Type
====================== ===================
productsSold           Output(type=int)
productsTISStats       StatisticsDiscrete
====================== ===================

Your code could look like this following:

.. code-block:: python

    outputs = sim.outputs()
    for name, value in outputs.items():
        print(name, type(value).__name__, value)
    # productsSold int 75779
    # productsTISStats StatisticsDiscrete StatisticsDiscrete(count=75779, mean=19.981, confidence=0.03, min=6.062, max=29.981, deviation=0.036, sum=1514107.338)

Training an AI policy
---------------------

How you decide to train some kind of AI - from a Bayesian optimization to an RL policy or anything else - is entirely dependent on the desired libraries and use case.

In general, it's recommended to only construct the ``AnyLogicSim`` object once per script, then make use of its ability to run indefinite episodes throughout your code.
For example, if you want to run an episode of the simulation within a function, create the ``AnyLogicSim`` object first, passing it as input to the function, which then may be called by some optimizer library.

Testing a policy within the AnyLogic model
------------------------------------------

Just as the "training" instructions were ambiguous, the "testing" ones will be as well. To embed the results of your training process back into the AnyLogic model will be entirely dependent on your approach to training or specific use case.

For example, if using Bayesian Optimization, you only need to open AnyLogic and use the values returned by the optimization to the model.

Due to numerous RL libraries, each with their own specific framework and rules for saving/loading policies, it's extremely difficult to create some sort of general-purpose connector.
For this reason, it's recommended to make use of the Pypeline library, which you can use to interact with Python code dynamically over the simulation run.
Additionally, if your RL library supports exporting to the ONNX framework, you can make use of the ONNX Helper Library for AnyLogic; with this, you can run inferences on the policy with minimal code.

As of AnyLogic 8.8, you can also call each of the RL Experiment's functions from within the simulation model. This means that if you choose to host your RL policy on some HTTP endpoint, you can use the jetty library (shipped with AnyLogic) and the ObjectMapper object from the Jackson library (also shipped with AnyLogic) to get and apply these actions to your model.

Complete sample code
--------------------

The following code uses the spaces defined in the sections above and is meant for demo purposes only.

.. code-block:: python

    import numpy as np

    from alpyne.constants import EngineState
    from alpyne.outputs import StatisticsDiscrete
    from alpyne.sim import AnyLogicSim
    from alpyne.utils import next_num

    sim = AnyLogicSim("model.jar",
                      auto_finish=True,  # sets engine to FINISHED if stop condition is met
                      engine_overrides=dict(stop_time=1000, seed=next_num),
                      config_defaults=dict(rate_per_sec=1.5, machine_types=["A", "A", "A"]))

    # test doing random machine speeds using a varying number of workers;
    num_workers_trials = list(range(1, 11))

    # track mean time in system stats and whether it prematurely ended
    # (due to stop condition) per num workers
    results: dict[int, (StatisticsDiscrete, bool)] = dict()
    for num_workers in num_workers_trials:
        # start a new episode and continue running it until hitting the end
        status = sim.reset(num_workers=num_workers)  # omitted values use the defaults above
        while EngineState.FINISHED not in status.state:
            status = sim.take_action(
                machine_speeds=np.random.random((3,))*10  # setting per machine, range [0, 10]
            )

        # put the outputs in the dictionary describing the outcome
        tis_stats = sim.outputs()['productsTISStats']
        results[num_workers] = (tis_stats, status.stop)

    # visualize the results (e.g., colored bar with range intervals)
    # ...

