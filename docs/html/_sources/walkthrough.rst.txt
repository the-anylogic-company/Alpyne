
High-level walkthrough
======================

The following explains the general workflow in a way that doesn't require (extensive) referencing to the API documentation. It assumes you have an exported model and are generally familiar with Python programming.

Creating the Alpyne Client object
---------------------------------

The ``AlpyneClient`` object serves as the parent object which individual runs spawn from and which has general model-level information. Except in advanced use cases, you only need to have a single instance of it.

The constructor of the client object takes the following arguments, some of which are explained further below:

- The path to your exported model
- Whether to enable blocking (default False)
- The port to run the app on (default 51150)
- Whether to enable verbose logging for the server (default False)

**model path argument**

When you export from the RL experiment, it saves as a zip file. You have two choices regarding this:

1. Pass a path to the zip file

- Alpyne will extract the contents to a temporary directory.

- For a list of candidates, see: https://github.com/python/cpython/blob/3.9/Lib/tempfile.py#L157

2. Extract the contents of the zip file, then pass a path to the ``model.jar`` file

Option #1 is only recommended for testing your model. Option #2 requires another step after exporting, but gives you convenient access to any input/output files your model might use or to the the Alpyne log (when enabled), and will write to the hard drive less.

**blocking**

Some simple operations - such as querying a run's status or getting input/output templates - execute so quickly that the app provide a near instantaneous response. Other more complex operations, however, are potentially time consuming - such as advancing a run to the next step. While the run is processing, you cannot query the observation or submit further actions until the run gets to the next event. Here you have a choice:

1. If ``blocking`` is ``True``, the app will consume your request and not allow the active thread to continue until the request is completed (i.e., when the model is ready for the next request).

2. If ``blocking`` is ``False``, the app will consume your request and immediately return. You then need to manually setup a periodic query of the run's status (calling ``wait_for_completion`` or ``get_state`` with a delay in a loop).

Option #1 is only recommended when you're executing a single run at a time (since there are no other threads having their time wasted while waiting). Option #2 is generally recommended for most usage.

To see how this effects the way you communicate with runs, the examples have both usages of this argument.
  
**server logging**

Regardless of what you set this to, the app will create a ``alpyne.log`` file in your exported model's directory with at least basic information (e.g., the process ID, any errors encountered, or trace statements from your model). If verbose is set to ``True``, it will also include many debug statements.
  
Creating model runs from the client
-----------------------------------
When creating a new model run, you'll pass in the initial inputs (i.e., configuration) to execute the first episode with. A template for the inputs can be obtained with the ``create_default_rl_inputs`` method or the ``configuration_template`` attribute of the client object (they are synonymous with one another). This will return a Configuration object which allows you to directly set the values of both your configuration fields and engine-level settings.

For example, say your model has the following configuration space:

============= ========
 Name          Type
============= ========
num_workers   int
rate_per_sec  double
machine_types String[]
============= ========

The Python code could look like:

::

	app = AlpyneClient(...)
	
	config = app.configuration_template
	config.num_workers = 10
	config.rate_per_sec = 3.14
	config.machine_types = ["A", "A", "B"]
	config.engine_seed = 1 # fixed seed
	config.engine_stop_time = 1000 # override value in the RL exp.
	
**Warning**: If you do not set explicit values of your defined configuration fields, they will be set to their Java defaults (0 for number types, null for object types). This may cause model errors if your Configuration code does not account for this.

- Note: In contrast, the engine settings will default to whatever value you set in the RL experiment.

**Warning**: To avoid conflict, do not name your configuration fields the same as any of the ``engine_`` settings.

**Tip**: In addition to setting fixed values, you can also pass tuples consisting of (start, stop, step) or no-argument callables; these will retrieve the next value every time they're accessed.

After building the configuration object, pass it into a call to the ``create_reinforcement_learning`` method of the client object. The returned value is an instance of a ``ModelRun`` object.

Interacting with model runs
---------------------------
After creating a new model run object, you will need to call its ``run`` method to begin execution. Depending on what you set ``block`` to, the thread will either be locked until the run reaches its first step (= True) or return immediately (= False). 

If the app was not setup with blocking, you'll need to call either ``wait_for_completion`` or ``get_state`` until the run is waiting for input.

Note: ``get_state`` returns two values - A constant representing the engine status (one of the ``RunStatus`` values) and a dictionary with more detailed information.

You can take observations, check if the terminal condition is true, or get outputs if the status is one of the following: ``PAUSED``, ``COMPLETED``, ``STOPPED``, ``FAILED``. Actions can only be taken while the run holds the ``PAUSED`` status.

To get an observation, you can call the run's ``get_observation`` method. This will return an Observation object where you can retrieve specific field values by either accessing the name directly or via the ``get_input`` method. 

For example, say your model has the following observation space:

====================== ========
 Name                    Type
====================== ========
mean_service_time      double
per_worker_utilization double[]
====================== ========

Printing out information about the current observation in your Python code may look like:

::

	obs = run1.get_observation()
	print(f"Mean service time = {obs.mean_service_time}")
	n_workers = len(obs.per_worker_utilization)
	print(f"Mean worker utilization = {sum(obs.per_worker_utilization) / n_workers}")
	
The ``is_terminal`` method of the run will return a boolean value based on a combination of the "done" condition in the RL experiment and the assigned stop time/date.
	
Taking an action in the run involves creating an Action object from the client's ``action_template`` attribute, filling it as desired, then passing it to the ``take_action`` method. 

After calling ``take_action``, your model will apply the action and then continue until the next step. 

Lastly, whenever your model is not actively processing, you can get any (analytical) outputs present in your top-level agent. 

**Tip**: You can check the names of the objects available from the ``output_names`` attirubte of the client object. 

To retrieve the values, call the ``get_outputs`` method of the run. You can pass names of specific objects, or pass no arguments if you'd like them all. This will return a ``SingleRunOutputs`` object which operates similarly to the other objects: you can retrieve values by directly passing names as attributes or by ``value`` method.

For example, if your model had an Output object named "amount_sold" and a DataSet named "demand_log", your Python code could look like the following:

::

	outputs = run1.get_outputs()
	print(f"Amount sold = {outputs.amount_sold}")
	print(f"Demand Xs = {outputs.demand_log['dataX']}")
	print(f"Demand Ys = {outputs.demand_log['dataY']}")

Note that the values of complex output types, such as HistogramData and DataSet, work exactly like they do on AnyLogic Cloud. 

For more details about all of these objects and what attributes/methods they possess, see the relevant API pages.

Multi-runs and RL training
---------------------------

Alpyne has two "base" (abstract) classes which you can extend depending on your desired uses:

1. ``BaseMultiRun``
	- Used to easily execute batches of multiple simultaneous model runs
	- Desirable when testing trained policies or pre-defined heuristics
	- Requires functions to be implemented for getting configuration and actions for a given run
	- Has additional callbacks for extra logic on step events and at the end of a run
	
2. ``BaseAlpyneEnv``
	- Follows the OpenAI Gym interface
	- Desirable when using RL libraries that support custom Gym environments (e.g., stable baselines, tensorflow)
	- Requires functions to be implemented for defining your observation and action space, and for converting Alpyne types to/from typical Python types.
	- Has an additional, optinonal method for defining any alternative terminal conditions.
	
To extend the classes, define a new class and pass the base class as the desired superclass. Required methods can be implemented - and optional methods overridden or extended - by defining them with the same name/arguments/return type. 

Most Python IDEs should provide an option to easily perform either of these tasks too. Examples of the simplicity of this can be seen using PyCharm in the images below.

.. list-table::

	* - .. figure:: _static/py_base_method_implement.png
		   :scale: 70 %
		   :alt: PyCharm with builtin ability to implement methods
   
	  - .. figure:: _static/py_base_method_override.png
		   :scale: 50 %
		   :alt: PyCharm with builtin ability to override methods
		   
	* - Easily implement missing abstract methods
	
	  - Simple dialog to override base methods

	   
.. note:: Optional methods can be *extended* by calling ``super().METHOD_NAME(METHOD_ARGS)`` anywhere desirable in the body of the overriden method.