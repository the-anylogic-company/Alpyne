
High-level walkthrough
======================

.. note:: The following explains the general workflow in a way that doesn't require (extensive) referencing to the API documentation; the final sub-section contains some sample code. Explanations assume you have an exported model and are generally familiar with Python programming.


Creating the AnyLogicSim object
---------------------------------

The ``AnyLogicSim`` object serves as the connection to a single instance of your model. If you want to run multiple, parallel runs, you will need to create multiple instances of the ``AnyLogicSim`` object.

The constructor of the sim object requires, at minimum, the path to your AnyLogic model exported from the RL Experiment.
There are several others for configuring logging, behavioral handling of the model, definitions of overrides and default values, and more.
A list of all options can be seen in the constructor's signature. The following sub-sections also explain the concepts in further detail; note that some examples reference functions or concepts explored by the subsequent sections.

model path argument
~~~~~~~~~~~~~~~~~~~

When you export from the RL experiment, it saves as a zip file. You have two choices regarding how to reference it:

1. Pass a path to the zip file. Alpyne will extract the contents to a temporary directory which should self-delete on the termination of your Python script. The specific location will depend on your system setup and the logic of the tempfile module; when logging is set to INFO, the log file will contain the specific path used.

- Pros: Less time consuming to set up (as the extraction is automated)
- Cons: Potential for temporary directory to not self-delete if the process is forcibly quit; no access to model's input/output files

2. Extract the contents of the zip file, then pass a path to the "model.jar" file.

- Pros: Gives you access to any input/output files your model may utilize
- Cons: Requires an extra step after exporting the model

.. important:: Option #1 is **required** when your model has *both* an internal database and your are running multiple parallel instances of the ``AnyLogicSim`` object. This is because the database has a lock whenever one process (i.e., the running model) is using it.

logging
~~~~~~~

You can customize the log level for output from Python (in the terminal of your Python script) and from Java (from the underlying Alpyne executable used to run your model) via the ``py_log_level`` and ``java_log_level`` arguments, respectively.
Each take either a value from Python's built-in logging module or a boolean (with True providing basic info logs and False providing only warnings or errors).

- The Python log level controls how verbose the output is in your terminal when you run your Python script. This mostly relates to the requests sent and received to the underlying Alpyne server.

- The Java log level controls how verbose the output is to the file "alpyne.log" which includes information about the control, status, and timing of the execution of your sim.

Regardless of the option you set, you will also see a "model.log" file which has any and all text from your model's standard output and error (e.g., ``traceln`` calls, model error tracebacks).

Both log files are by default overridden each time a new ``AnyLogicSim`` object is created. If you want to prevent this, or are running multiple parallel instances, set a value for the ``log_id``; this will append a separator and your ID to the log names.

locking
~~~~~~~

For monitoring the state of your model in its execution, the state of the AnyLogic engine (the object actually executing the events in the simulation model) is used. Alpyne has replicated the same set of states in its ``EngineState`` flag-typed enum (it being a flag means bitwise operators are supported when wanting to specify multiple options - the usefulness of which will be apparent shortly).

For waiting until the completion of time consuming requests (namely the ``reset`` and ``take_action`` functions), the AnyLogicSim has ``lock`` function which two inputs: a flag for engine state(s) and a timeout. The function will wait up to the number of seconds expressed by the timeout for the underlying sim to be in the state(s) specified by the flag. It will return the sim's status if the flag is met, otherwise it'll throw an error.

.. code-block:: python

    # will wait up to 30 seconds for the engine to be PAUSED *or* FINISHED *or* ERROR state
    # note: this example is also showing the default values used if you call `lock` without arguments
    status = sim.lock(flag=EngineState.PAUSED|EngineState.FINISHED|EngineState.ERROR, timeout=30)

.. tip:: The ``EngineState.ready()`` function is a shorthand for any of the three states that require some user/code action (i.e., PAUSED, FINISHED, ERROR)

.. note:: The returned status has a "state" attribute you can use to see which specific state the engine is currently in

If you want to change the default values used by the lock function, the AnyLogicSim's ``lock_defaults`` constructor argument allows you to pass a dictionary with keys matching the keyword names of the lock function and the desired default value.

.. code-block:: python

    # note: some notable kwargs are missing from this constructor for brevity
    sim = AnyLogicSim("export.zip", lock_defaults=dict(flag=EngineState.PAUSED, timeout=10), ...)
    sim.reset()
    # will wait up to 10 seconds for the engine to be in the PAUSED state
    status = sim.lock()
    # ...
    sim.take_action(...)
    # will wait up to 10 seconds for the engine to be in either the PAUSED, FINISHED, or ERROR state
    status = sim.lock(flag=EngineState.ready())


As, for common usage, you will always want to call ``lock`` to wait for some time consuming action to finish, there is the AnyLogicSim's ``auto_lock`` constructor argument. Having this enabled - the default - will automatically call the lock function whenever you call reset or take_action; having this enabled also causes the aforementioned functions to return the status object given from the lock call.

.. code-block:: python

    # specifying `auto_lock=True` here is redundant but shown for demo purposes
    sim = AnyLogicSim("export.zip", auto_lock=True)
    # will use the `lock_default` values when internally calling lock
    status = sim.reset()
    # ...
    status = sim.take_action(...)

.. note::
    You'll typically only disable the auto lock when wanting to run multiple parallel AnyLogicSim objects in a single process.

    .. code-block:: python

        sims = [AnyLogicSim("export.zip", auto_lock=False) for _ in range(3)]
        # the following will execute nearly instantly,
        #   as each call to reset will return once the request is accepted
        for sim in sims:
            sim.reset()
        # now synchronize the runs, getting all their statuses
        statuses = [sim.lock() for sim in sims]


engine settings
~~~~~~~~~~~~~~~

If you do not pass any specific settings, the model will execute each run based on the time/date/seed settings you designated in your RL experiment.
You can optionally pass a dictionary to the ``engine_overrides`` constructor argument with settings to override, the keys for which are the names in snake case (e.g., start_time, seed) and are defined in ``alpyne.typing.EngineSettingKeys``.

Some important behaviors to be aware of:

- Setting a stop time or date will override the last stop value that was set; passing both will use whichever is processed last

- The numeric value for start or stop time uses whatever the model's time units are set to. To allow setting times agnostic of this, Alpyne also allows you to pass a ``UnitValue`` object - the class typically used by Outputs which stores a numeric value and a unit. Alpyne has enum classes for each of the units used by AnyLogic which all share the same names (e.g., alpyne.outputs.TimeUnits.MINUTE); you can also pass the time units as an appropriate string name.

- Any of the values can be set to a no-argument function which returns the expected type. This is particularly useful for the "seed", in case you want each run to be unique but use known values.

.. code-block:: python

    # each call to reset now uses a random seed in the specified range and run the sim for 8 hours (assuming the default start time is 0)
    sim = AnyLogicSim("model.jar", engine_overrides=dict(stop_time=UnitValue(8, "HOUR"), seed=lambda: random.randint(-1e9, 1e9)))

    # each call to reset now starts the seed at 0 and increments by one each time,
    #   using the provided helper function (alpyne.utils.next_num)
    sim = AnyLogicSim("model.jar", engine_overrides=dict(seed=next_num)

automatic finish
~~~~~~~~~~~~~~~~

The status object (containing a set of information about the current status of your simulation model) has an attribute called "stop" - a boolean evaluated from the RL Experiment's "Simulation run stop condition". When it is true, it's meant to indicate the simulation has reached some terminal condition and the model should be reset.

However, this is intended as merely an *indicator* and thus does not inherently force the simulation model to stop executing, preventing further actions from taking place. To allow control over this, there is the AnyLogicSim's ``auto_finish`` constructor argument.

By default, it's set to False, causing only conditions internal to the model to set the engine to its FINISHED state (namely, when it reaches a stop time/date or the model logic calls the ``finish`` function. When set to True, the stop attribute will also set the engine to be set to FINISHED.

Resetting the run
-----------------

When creating a new model run, you'll pass in the initial inputs (i.e., configuration) to execute the first episode with. This is done by the sim's ``reset`` function which takes keyword arguments for the configuration space.

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

    sim = AnyLogicSim("export.zip")
    sim.reset(num_workers=10, rate_per_sec=3.14, machine_types=["A", "A", "B"])

	
.. warning:: If you do not set explicit values of your defined configuration fields, they will be set to their Java defaults (0 for number types, null for object types). This may cause model errors if your Configuration code does not account for this or if you do not pass the desired defaults as part of the ``config_defaults`` constructor argument in the AlpyneSim object's creation.

.. tip:: In addition to setting fixed values, you can also no-argument callables; these will retrieve the next value every time they're accessed.

.. code-block:: python

    sim = AnyLogicSim("export.zip", config_defaults=dict(num_workers=10))
    # for 'num_workers' passes 10 (as defined by the defaults above)
    # for 'rate_per_sec' and 'machine_types' passes 0 and None/null, respectively (not defined above; the Java defaults)
    sim.reset()

Submitting actions
------------------
Whenever the model is in a PAUSED state, you can submit requests to take some action based on your action space definition. When Alpyne consumes your request, it will apply it to the simulation and allow it to continue running.
In practice, this works exactly the same way as resetting with the configuration does, but using the ``take_action`` function with your action space. This function takes a dictionary or keyword arguments matching the action space.

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

.. important:: By manually controlling the locking behavior (i.e., ``auto_lock=False``), it is possible to get the status while the simulation is in a RUNNING state. Assume the information you receive in this case is transient; don't rely on it for getting reproducible snapshots, but this may be useful for monitoring progress or debugging models.

When you see the 'state' being reported from Alpyne, it's referring to the state of the underlying AnyLogic engine. There are 6 different states it can be in:

- IDLE: Just started, waiting for the configuration

- PAUSED = Mid-run, waiting for action and open to observation and output querying

- RUNNING = The model is being actively executed

- FINISHED = The model execution has reached a stopping point and will no longer advance simulated time

- ERROR = Some internal model error has occurred

- PLEASE_WAIT = The model is in the process of executing an uninterruptible command (calling `pause()`, `stop()`, `step()` from the AnyLogic model)

Alpyne has a flag-based enum class -- ``EngineState`` -- that allows you to pass one or more of these states to pass to the ``lock`` function or the ``lock_defaults`` constructor argument, in addition to the maximum amount of time you want to wait for the condition to be fulfilled (after which a Python error will be thrown).

For example, ``sim.lock(EngineState.PAUSED | EngineState.FINISHED | EngineState.ERROR, 30)`` will submit a request to wait up to 30 seconds for the engine to be in the PAUSED or FINISHED or ERROR state. As this is the default, you can also just do ``sim.lock()``.

.. tip:: The EngineState enum has a ``ready()`` function which is a shorthand for the above code (i.e., ``sim.lock(EngineState.ready(), 30)``) -- "ready" as in, "ready for some interaction". This is the default for the function.

The AnyLogicSim object also has a ``observation()`` function which is a shorthand for getting the RL status and referencing the observation attribute (i.e., ``sim.status().observation``).

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

Passing no arguments will return a dictionary mapping all output names to their values. Passing one or more strings corresponding to output names will return a tuple of those values in the order you list them.

The types of the values will be the natural Python type when relevant (e.g., Output object whose type is int); for other types, Alpyne has AnyLogic-specific classes (e.g., DataSet) whose attributes follow the same structure as the AnyLogic equivalent.

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

    # ALTERNATIVE:
    products_sold, tis_stats = sim.outputs("productsSold", "productsTISStats")

Training an AI policy
---------------------

How you decide to train some kind of AI - from a Bayesian optimization to an RL policy or anything else - is entirely dependent on the desired libraries and use case.

Alpyne does not contain any inherent logic that restricts it to one library versus another. For this reason, the examples provided are designed to cover a wide range of different libraries.

In general, it's recommended to only construct the ``AnyLogicSim`` object once per script (assuming non-parallel scenarios), then make use of its ability to run indefinite episodes throughout your code.
For example, if you want to run an episode of the simulation within a function, create the ``AnyLogicSim`` object first, passing it as input to the function, which then may be called by some optimizer library.

Testing a policy within the AnyLogic model
------------------------------------------

Just as the "training" instructions were ambiguous, these "testing" ones will be as well. To embed the results of your training process back into the AnyLogic model will be entirely dependent on your approach to training or the specific use case.

For example, if using Bayesian Optimization, you only need to open AnyLogic and use the values returned by the optimization to the model.

Due to numerous RL libraries, each with their own specific framework and rules for saving/loading policies, it's extremely difficult to create some sort of general-purpose connector.
For this reason, it's recommended to make use of the Pypeline library, which you can use to interact with Python code dynamically over the simulation run.
Additionally, if your RL library supports exporting to the ONNX framework, you can make use of the ONNX Helper Library for AnyLogic; with this, you can run inferences on the policy with minimal code.

The provided examples also make use of a variety of ways of querying the trained models. Some may require you to add libraries to your AnyLogic environment (e.g., Pypeline, ONNX Helper) and/or adjust various properties for it to work on your specific system. These are specified further in each example's README.

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

    sim = AnyLogicSim("Exported/model.jar",
                      auto_finish=True,  # sets engine to FINISHED if stop condition is met
                      engine_overrides=dict(stop_time=1000, seed=next_num),
                      config_defaults=dict(rate_per_sec=1.5, machine_types=["A", "A", "A"]))

    # test doing random machine speeds using a varying number of workers
    # ("workers" as in, worker agents in the simulation model)
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

        # specifying the output name(s) returns an iterable of values
        (tis_stats, ) = sim.outputs("productsTISStats")
        # put the outputs in the dictionary describing the outcome
        results[num_workers] = (tis_stats, status.stop)

    # visualize the results (e.g., colored bar with range intervals)
    # ...

